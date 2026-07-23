"""
Purpose
-------
Gemini implementation of the RecommendationProviderInterface for operational recommendations.

Responsibilities
----------------
- Format structured RootCauseAnalysis into Senior SRE recommendation prompts.
- Call Gemini API to generate structured RecommendationReport payloads.
- Parse JSON output into validated RecommendationReport domain models.
- Provide deterministic fallback guidance if API keys or network endpoints are unavailable.

Does NOT
---------
- Execute commands on remote Linux servers or modify infrastructure.
"""

from datetime import datetime
import json
import os
import re
import time
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai

from domain.rca.models import RootCauseAnalysis
from domain.recommendation.exceptions import RecommendationProviderError
from domain.recommendation.llm_interface import RecommendationProviderInterface
from domain.recommendation.models import (
    MonitoringRecommendation,
    PreventionRecommendation,
    Recommendation,
    RecommendationCategory,
    RecommendationMetadata,
    RecommendationPriority,
    RecommendationReport,
    RiskLevel,
    RollbackPlan,
    ValidationStep,
)

load_dotenv()


class GeminiRecommendationProvider(RecommendationProviderInterface):
    """
    Concrete Gemini AI Provider implementing RecommendationProviderInterface.
    """

    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._model_name = model_name
        self._client = genai.Client(api_key=self._api_key) if self._api_key else None

    @property
    def provider_name(self) -> str:
        return "Gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate_recommendations(self, rca: RootCauseAnalysis) -> RecommendationReport:
        """
        Generates an operational RecommendationReport from a RootCauseAnalysis payload using Gemini.
        """
        start_time = time.time()
        executed_at = datetime.utcnow()

        prompt = self._build_prompt(rca)

        if not self._client:
            return self._fallback_guidance(rca, start_time, executed_at)

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )

            response_text = response.text.strip() if response and response.text else ""
            clean_json_str = self._clean_json(response_text)
            data = json.loads(clean_json_str)

            duration = round(time.time() - start_time, 3)
            return self._parse_report_model(data, rca, duration, executed_at)

        except Exception as exc:
            return self._fallback_guidance(rca, start_time, executed_at, error_reason=str(exc))

    def _build_prompt(self, rca: RootCauseAnalysis) -> str:
        """Builds a strict JSON system prompt from structured RootCauseAnalysis."""
        rca_payload = {
            "primary_root_cause": rca.primary_root_cause,
            "overall_confidence": rca.overall_confidence,
            "summary": rca.summary,
            "primary_hypothesis": {
                "title": rca.primary_hypothesis.title,
                "description": rca.primary_hypothesis.description,
            },
            "affected_components": [
                {"type": ac.component_type, "name": ac.name, "impact": ac.impact_level}
                for ac in rca.affected_components
            ],
        }

        prompt_str = f"""
You are a Principal Site Reliability Engineer (SRE) advising an operations team.

User Incident Query: "{rca.user_question}"

Structured Root Cause Analysis:
{json.dumps(rca_payload, indent=2)}

Instructions:
1. Formulate actionable operational recommendations for Immediate, Short-Term, Long-Term, and Preventive action.
2. Provide Validation Steps to verify system health.
3. Provide a Rollback Plan.
4. Provide Monitoring and Prevention Recommendations.
5. Respond ONLY in valid JSON format matching this exact schema:

{{
  "executive_summary": "Executive guidance summary",
  "primary_root_cause_ref": "Primary root cause statement reference",
  "recommended_actions": [
    {{
      "title": "Action title",
      "description": "Detailed step instructions",
      "reason": "Operational justification",
      "category": "IMMEDIATE",
      "priority": "P1_CRITICAL",
      "risk_level": "MEDIUM",
      "expected_benefit": "Expected benefit",
      "estimated_impact": "Estimated system impact",
      "required_skill_level": "Senior SRE",
      "requires_human_approval": true,
      "target_resource": "Resource name"
    }}
  ],
  "validation_steps": [
    {{
      "step_number": 1,
      "command_or_metric": "free -m",
      "expected_outcome": "Available memory > 20%"
    }}
  ],
  "rollback_plan": {{
    "rollback_steps": ["Step 1 revert"],
    "estimated_rollback_time_minutes": 5,
    "risk_summary": "Low risk rollback"
  }},
  "monitoring_recommendations": [
    {{
      "metric_or_alert": "memory_used_percent",
      "suggested_threshold": "> 85% for 5m",
      "rationale": "Early detection of memory pressure"
    }}
  ],
  "preventive_recommendations": [
    {{
      "preventive_action": "Configure auto-scaling",
      "target_system": "App Pool",
      "benefit": "Prevents RAM exhaustion under load spikes"
    }}
  ],
  "additional_investigations": [
    "Check application process memory leak logs"
  ]
}}
"""
        return prompt_str

    def _clean_json(self, text: str) -> str:
        """Strips markdown code fences from LLM output."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        return cleaned.strip()

    def _parse_report_model(
        self,
        data: Dict[str, Any],
        rca: RootCauseAnalysis,
        duration: float,
        executed_at: datetime
    ) -> RecommendationReport:
        """Transforms parsed dictionary into RecommendationReport domain object."""
        rec_actions = []
        for ra in data.get("recommended_actions", []):
            rec_actions.append(
                Recommendation(
                    title=ra.get("title", "Recommended Action"),
                    description=ra.get("description", ""),
                    reason=ra.get("reason", "Operational improvement."),
                    category=self._safe_enum(RecommendationCategory, ra.get("category"), RecommendationCategory.IMMEDIATE),
                    priority=self._safe_enum(RecommendationPriority, ra.get("priority"), RecommendationPriority.P2_HIGH),
                    risk_level=self._safe_enum(RiskLevel, ra.get("risk_level"), RiskLevel.MEDIUM),
                    expected_benefit=ra.get("expected_benefit", "Resolves incident."),
                    estimated_impact=ra.get("estimated_impact", "Minimal downtime."),
                    required_skill_level=ra.get("required_skill_level", "Senior SRE"),
                    requires_human_approval=bool(ra.get("requires_human_approval", True)),
                    target_resource=ra.get("target_resource", "Target System"),
                )
            )

        val_steps = [
            ValidationStep(
                step_number=vs.get("step_number", idx + 1),
                command_or_metric=vs.get("command_or_metric", "system status check"),
                expected_outcome=vs.get("expected_outcome", "Healthy"),
            )
            for idx, vs in enumerate(data.get("validation_steps", []))
        ]

        rb_data = data.get("rollback_plan", {})
        rollback_plan = RollbackPlan(
            rollback_steps=rb_data.get("rollback_steps", ["Revert previous changes"]),
            estimated_rollback_time_minutes=int(rb_data.get("estimated_rollback_time_minutes", 5)),
            risk_summary=rb_data.get("risk_summary", "Low risk rollback."),
        )

        mon_recs = [
            MonitoringRecommendation(
                metric_or_alert=mr.get("metric_or_alert", "metric"),
                suggested_threshold=mr.get("suggested_threshold", "threshold"),
                rationale=mr.get("rationale", "Rationale"),
            )
            for mr in data.get("monitoring_recommendations", [])
        ]

        prev_recs = [
            PreventionRecommendation(
                preventive_action=pr.get("preventive_action", "Action"),
                target_system=pr.get("target_system", "System"),
                benefit=pr.get("benefit", "Benefit"),
            )
            for pr in data.get("preventive_recommendations", [])
        ]

        metadata = RecommendationMetadata(
            provider_used=self.provider_name,
            model_name=self.model_name,
            generation_duration_seconds=duration,
            total_recommendations_count=len(rec_actions),
        )

        return RecommendationReport(
            analysis_id=rca.analysis_id,
            investigation_id=rca.investigation_id,
            user_question=rca.user_question,
            executive_summary=data.get("executive_summary", "Operational guidance generated."),
            primary_root_cause_ref=data.get("primary_root_cause_ref", rca.primary_root_cause),
            recommended_actions=rec_actions,
            validation_steps=val_steps,
            rollback_plan=rollback_plan,
            monitoring_recommendations=mon_recs,
            preventive_recommendations=prev_recs,
            additional_investigations=data.get("additional_investigations", []),
            metadata=metadata,
            created_at=executed_at,
        )

    def _safe_enum(self, enum_cls: Any, value: str, default: Any) -> Any:
        """Safely parses string values into enum members with fallback."""
        if not value:
            return default
        try:
            return enum_cls(value.upper())
        except ValueError:
            return default

    def _fallback_guidance(
        self,
        rca: RootCauseAnalysis,
        start_time: float,
        executed_at: datetime,
        error_reason: str = None
    ) -> RecommendationReport:
        """Deterministic rule-based fallback when Gemini API is unconfigured or unreachable."""
        duration = round(time.time() - start_time, 3)

        is_inconclusive = rca.overall_confidence < 0.3 or "Inconclusive" in rca.primary_root_cause or "failed" in rca.primary_root_cause.lower()

        if is_inconclusive:
            rec_actions = [
                Recommendation(
                    title="Verify SSH Connectivity & Environment Configuration",
                    description="Verify that SSH_HOST, SSH_PORT, SSH_USERNAME, and SSH_PASSWORD in .env are valid and target host is reachable.",
                    reason=rca.primary_root_cause,
                    category=RecommendationCategory.IMMEDIATE,
                    priority=RecommendationPriority.P1_CRITICAL,
                    risk_level=RiskLevel.LOW,
                    expected_benefit="Restores diagnostic telemetry collection.",
                    estimated_impact="No server downtime.",
                    required_skill_level="Senior SRE",
                    requires_human_approval=False,
                    target_resource="SSH Environment Configuration",
                ),
                Recommendation(
                    title="Verify Linux Command Permissions & Registries",
                    description="Ensure whitelisted diagnostic commands (e.g. top, free, df) are installed on the remote Linux host and accessible.",
                    reason="Prevent command execution failures during automated investigation.",
                    category=RecommendationCategory.SHORT_TERM,
                    priority=RecommendationPriority.P2_HIGH,
                    risk_level=RiskLevel.LOW,
                    expected_benefit="Ensures diagnostic commands complete successfully.",
                    estimated_impact="No server downtime.",
                    required_skill_level="Senior SRE",
                    requires_human_approval=False,
                    target_resource="Linux Host Binaries",
                ),
                Recommendation(
                    title="Re-run Autonomous Investigation",
                    description="Re-run the investigation pipeline after validating SSH connection and permissions.",
                    reason="Collect clean operational telemetry once connection is established.",
                    category=RecommendationCategory.IMMEDIATE,
                    priority=RecommendationPriority.P2_HIGH,
                    risk_level=RiskLevel.LOW,
                    expected_benefit="Produces valid Root Cause Analysis report.",
                    estimated_impact="No server downtime.",
                    required_skill_level="Senior SRE",
                    requires_human_approval=False,
                    target_resource="Platform Pipeline",
                ),
            ]

            val_steps = [
                ValidationStep(step_number=1, command_or_metric="ssh_check", expected_outcome="SSH connection status: CONNECTED"),
                ValidationStep(step_number=2, command_or_metric="uptime", expected_outcome="Command returns exit code 0"),
            ]

            rollback_plan = RollbackPlan(
                rollback_steps=["No remote infrastructure changes executed."],
                estimated_rollback_time_minutes=1,
                risk_summary="Zero risk diagnostic guidance.",
            )

            mon_recs = [
                MonitoringRecommendation(
                    metric_or_alert="ssh_connection_failures",
                    suggested_threshold="> 0",
                    rationale="Alert on platform-to-host connectivity degradation.",
                )
            ]

            prev_recs = [
                PreventionRecommendation(
                    preventive_action="Implement periodic SSH health probes.",
                    target_system="Platform Health Monitoring",
                    benefit="Detects host connectivity drops before incident investigations.",
                )
            ]
        else:
            rec_actions = [
                Recommendation(
                    title="Inspect High Resource Consuming Services",
                    description="Identify and review top memory/CPU process memory consumption patterns.",
                    reason=rca.primary_root_cause,
                    category=RecommendationCategory.IMMEDIATE,
                    priority=RecommendationPriority.P1_CRITICAL,
                    risk_level=RiskLevel.LOW,
                    expected_benefit="Prevents further resource degradation.",
                    estimated_impact="No downtime for read-only inspection.",
                    required_skill_level="Senior SRE",
                    requires_human_approval=True,
                    target_resource="System Resources",
                )
            ]

            val_steps = [
                ValidationStep(step_number=1, command_or_metric="free -m", expected_outcome="RAM usage < 80%"),
                ValidationStep(step_number=2, command_or_metric="uptime", expected_outcome="1m load < 1.5"),
            ]

            rollback_plan = RollbackPlan(
                rollback_steps=["No state-changing commands executed. Revert any manual service changes if applied."],
                estimated_rollback_time_minutes=5,
                risk_summary="Zero risk read-only recommendations.",
            )

            mon_recs = [
                MonitoringRecommendation(
                    metric_or_alert="memory_used_percent",
                    suggested_threshold="> 80%",
                    rationale="Early warning before swap activation.",
                )
            ]

            prev_recs = [
                PreventionRecommendation(
                    preventive_action="Implement memory limits on worker services.",
                    target_system="Systemd / Container Runtime",
                    benefit="Prevents single process OOM from crashing system.",
                )
            ]

        metadata = RecommendationMetadata(
            provider_used="Gemini (Fallback Engine)" if error_reason else "Deterministic Advisory Synthesizer",
            model_name=self.model_name,
            generation_duration_seconds=duration,
            total_recommendations_count=len(rec_actions),
        )

        return RecommendationReport(
            analysis_id=rca.analysis_id,
            investigation_id=rca.investigation_id,
            user_question=rca.user_question,
            executive_summary=f"Operational recommendations formulated for: {rca.primary_root_cause}",
            primary_root_cause_ref=rca.primary_root_cause,
            recommended_actions=rec_actions,
            validation_steps=val_steps,
            rollback_plan=rollback_plan,
            monitoring_recommendations=mon_recs,
            preventive_recommendations=prev_recs,
            additional_investigations=["Re-run investigation once SSH connectivity is verified."],
            metadata=metadata,
            created_at=executed_at,
        )
