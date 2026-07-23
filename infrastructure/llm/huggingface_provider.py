"""
Purpose
-------
Unified Hugging Face Inference API implementation of LLMProviderInterface
using Qwen/Qwen2.5-72B-Instruct.

Responsibilities
----------------
- Perform AI Provider Health Checks probing Qwen on Hugging Face Inference API.
- Synthesize correlated operational findings into structured RootCauseAnalysis payloads.
- Formulate prioritized operational recommendations into structured RecommendationReport payloads.
- Handle API retries, timeouts, and structured error responses.
- Provide deterministic rule-based fallbacks if network endpoints or API tokens are unavailable.

Does NOT
---------
- Accept raw unparsed terminal text directly.
- Hardcode vendor references in application or presentation layers.
"""

from datetime import datetime
import json
import os
import re
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import requests

from domain.correlation.models import CorrelationResult
from domain.health.models import ComponentHealthResult, ComponentStatus
from domain.llm import LLMProviderInterface
from domain.rca.models import (
    AffectedComponent,
    AnalysisMetadata,
    Hypothesis,
    ReasoningTrace,
    RootCauseAnalysis,
    SupportingEvidence,
)
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
from shared.config import get_settings
from shared.logging import get_logger

load_dotenv()

logger = get_logger("HuggingFaceProvider")


class HuggingFaceProvider(LLMProviderInterface):
    """
    Unified concrete Hugging Face LLM Provider implementing LLMProviderInterface
    using Qwen/Qwen2.5-72B-Instruct.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        settings = get_settings()
        self._api_key = api_key or settings.llm.api_key
        self._model_name = model_name or settings.llm.model or "Qwen/Qwen2.5-72B-Instruct"

    @property
    def provider_name(self) -> str:
        return "Hugging Face"

    @property
    def model_name(self) -> str:
        return self._model_name

    def health_check(self) -> ComponentHealthResult:
        """
        Performs a lightweight probe against Hugging Face Inference API.
        """
        checked_at = datetime.utcnow()
        provider_display = "Hugging Face"

        if not self._api_key:
            logger.warning("AI Provider health check skipped: LLM_API_KEY is not configured.")
            return ComponentHealthResult(
                component_name="AI Provider",
                category="AI",
                status=ComponentStatus.UNHEALTHY,
                details={
                    "provider": provider_display,
                    "model": self._model_name,
                    "provider_type": "Remote Inference API",
                    "api_connectivity": "No API Key Configured",
                },
                error_message="LLM_API_KEY is not configured in the environment.",
                recommendation="Set the LLM_API_KEY environment variable in your .env file.",
                checked_at=checked_at,
            )

        start_time = time.time()
        url = f"https://api-inference.huggingface.co/models/{self._model_name}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": "Health probe: respond OK",
            "parameters": {"max_new_tokens": 10},
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            if resp.status_code == 200:
                logger.info(f"AI Provider health check passed ({provider_display} {self._model_name}, {latency_ms}ms)")
                return ComponentHealthResult(
                    component_name="AI Provider",
                    category="AI",
                    status=ComponentStatus.HEALTHY,
                    details={
                        "provider": provider_display,
                        "model": self._model_name,
                        "provider_type": "Remote Inference API",
                        "api_connectivity": "Connected",
                        "last_successful_check": checked_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        "response_latency_ms": latency_ms,
                    },
                    checked_at=checked_at,
                    latency_ms=latency_ms,
                )
            else:
                error_msg = f"API returned HTTP {resp.status_code}: {resp.text[:200]}"
                logger.warning(f"AI Provider health check failed: {error_msg}")
                return ComponentHealthResult(
                    component_name="AI Provider",
                    category="AI",
                    status=ComponentStatus.UNHEALTHY,
                    details={
                        "provider": provider_display,
                        "model": self._model_name,
                        "provider_type": "Remote Inference API",
                        "api_connectivity": "Failed",
                        "http_status": resp.status_code,
                    },
                    error_message=error_msg,
                    recommendation="Verify LLM_API_KEY is valid and Hugging Face model endpoint is active.",
                    checked_at=checked_at,
                    latency_ms=latency_ms,
                )

        except Exception as exc:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            error_msg = f"AI Provider health check failed — {type(exc).__name__}: {exc}"
            logger.warning(f"AI Provider health check failed: {error_msg}")
            return ComponentHealthResult(
                component_name="AI Provider",
                category="AI",
                status=ComponentStatus.UNHEALTHY,
                details={
                    "provider": provider_display,
                    "model": self._model_name,
                    "provider_type": "Remote Inference API",
                    "api_connectivity": "Failed",
                },
                error_message=error_msg,
                recommendation="Check network connectivity to Hugging Face API and verify LLM_API_KEY.",
                checked_at=checked_at,
                latency_ms=elapsed_ms,
            )

    def analyze_correlation(self, correlation_result: CorrelationResult) -> RootCauseAnalysis:
        """
        Synthesizes correlated operational findings into a structured RootCauseAnalysis object.
        """
        start_time = time.time()
        executed_at = datetime.utcnow()

        if not self._api_key:
            logger.warning("LLM API key not configured. Using deterministic fallback synthesis.")
            return self._fallback_rca_synthesis(correlation_result, start_time, executed_at, error_reason="No LLM_API_KEY configured")

        prompt = self._build_rca_prompt(correlation_result)
        response_text = self._call_hf_api(prompt)

        if not response_text:
            return self._fallback_rca_synthesis(correlation_result, start_time, executed_at, error_reason="Empty response from Hugging Face API")

        try:
            clean_json_str = self._clean_json(response_text)
            data = json.loads(clean_json_str)

            duration = round(time.time() - start_time, 3)
            logger.info(f"RCA completed via Hugging Face model {self.model_name} in {duration}s")
            return self._parse_rca_model(data, correlation_result, duration, executed_at)

        except Exception as exc:
            logger.warning(f"Failed to parse Hugging Face RCA JSON output: {exc}")
            return self._fallback_rca_synthesis(correlation_result, start_time, executed_at, error_reason=str(exc))

    def generate_recommendations(self, rca: RootCauseAnalysis) -> RecommendationReport:
        """
        Generates operational RecommendationReport from a RootCauseAnalysis payload.
        """
        start_time = time.time()
        executed_at = datetime.utcnow()

        if not self._api_key:
            return self._fallback_recommendations_guidance(rca, start_time, executed_at, error_reason="No LLM_API_KEY configured")

        prompt = self._build_recommendations_prompt(rca)
        response_text = self._call_hf_api(prompt)

        if not response_text:
            return self._fallback_recommendations_guidance(rca, start_time, executed_at, error_reason="Empty response from Hugging Face API")

        try:
            clean_json_str = self._clean_json(response_text)
            data = json.loads(clean_json_str)

            duration = round(time.time() - start_time, 3)
            logger.info(f"Recommendation report generated via Hugging Face model {self.model_name} in {duration}s")
            return self._parse_recommendation_model(data, rca, duration, executed_at)

        except Exception as exc:
            logger.warning(f"Failed to parse Hugging Face Recommendation JSON output: {exc}")
            return self._fallback_recommendations_guidance(rca, start_time, executed_at, error_reason=str(exc))

    def _call_hf_api(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Executes API request to Hugging Face Router / Inference API with retries."""
        url = f"https://api-inference.huggingface.co/models/{self._model_name}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1500,
                "temperature": 0.1,
                "return_full_text": False,
            },
        }

        for attempt in range(1, max_retries + 1):
            try:
                start_call = time.time()
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                call_duration = round(time.time() - start_call, 2)

                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        gen_text = data[0].get("generated_text", "")
                        logger.info(f"HF API call succeeded ({call_duration}s)")
                        return gen_text
                    elif isinstance(data, dict) and "generated_text" in data:
                        return data["generated_text"]
                    return resp.text

                logger.warning(f"HF API HTTP {resp.status_code} (attempt {attempt}/{max_retries}): {resp.text[:200]}")
                time.sleep(1)

            except Exception as err:
                logger.warning(f"HF API exception (attempt {attempt}/{max_retries}): {err}")
                time.sleep(1)

        return None

    def _build_rca_prompt(self, correlation_result: CorrelationResult) -> str:
        """Builds a strict JSON system prompt from structured correlation findings."""
        findings_summary = []
        for f in correlation_result.findings:
            ev_list = [
                {"metric": ev.metric_name, "value": str(ev.observed_value), "threshold": str(ev.threshold)}
                for ev in f.evidences
            ]
            findings_summary.append({
                "title": f.title,
                "category": f.category.value,
                "severity": f.severity.value,
                "summary": f.summary,
                "evidences": ev_list,
                "affected_resources": f.affected_resources,
            })

        return f"""You are a Principal Site Reliability Engineer (SRE) performing an autonomous incident investigation.

User Question: "{correlation_result.user_question}"

Structured Operational Findings:
{json.dumps(findings_summary, indent=2)}

Instructions:
1. Analyze the structured findings and empirical evidences above.
2. Determine the Primary Root Cause.
3. Formulate the Primary Hypothesis and any Alternative Hypotheses.
4. Output a step-by-step Reasoning Trace.
5. Identify Affected Components.
6. Respond ONLY in valid JSON format matching this exact schema:

{{
  "primary_root_cause": "Authoritative root cause statement",
  "overall_confidence": 0.95,
  "summary": "Executive incident diagnosis summary",
  "primary_hypothesis": {{
    "title": "Primary hypothesis title",
    "description": "Detailed explanation of mechanism",
    "likelihood_score": 0.95,
    "supporting_evidences": [
      {{
        "metric_name": "metric_name",
        "observed_value": "observed_value",
        "finding_title": "finding_title",
        "relevance_explanation": "relevance_explanation"
      }}
    ]
  }},
  "alternative_hypotheses": [],
  "reasoning_trace": [
    {{
      "step_number": 1,
      "observation": "Observed symptom",
      "deduction": "Logical deduction"
    }}
  ],
  "affected_components": [
    {{
      "component_type": "MEMORY",
      "name": "RAM",
      "impact_level": "HIGH"
    }}
  ]
}}
"""

    def _build_recommendations_prompt(self, rca: RootCauseAnalysis) -> str:
        """Builds prompt instructing Qwen to output structured RecommendationReport JSON."""
        return f"""You are a Principal SRE formulating operational action guidance.

Primary Root Cause: "{rca.primary_root_cause}"
Summary: "{rca.summary}"

Formulate prioritized operational recommendations in valid JSON format:
{{
  "executive_summary": "Executive operational guidance summary",
  "primary_root_cause_ref": "{rca.primary_root_cause}",
  "recommended_actions": [
    {{
      "title": "Action title",
      "description": "Step details",
      "reason": "Operational justification",
      "category": "IMMEDIATE",
      "priority": "P1_CRITICAL",
      "risk_level": "LOW",
      "expected_benefit": "Benefit",
      "estimated_impact": "Impact",
      "required_skill_level": "Senior SRE",
      "requires_human_approval": true,
      "target_resource": "System Resources"
    }}
  ]
}}
"""

    def _clean_json(self, text: str) -> str:
        """Strips markdown code fences from LLM output."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        return cleaned.strip()

    def _safe_enum(self, enum_cls: Any, value: str, default: Any) -> Any:
        """Safely parses string values into enum members with fallback."""
        if not value:
            return default
        try:
            return enum_cls(value.upper())
        except ValueError:
            return default

    def _parse_rca_model(
        self,
        data: Dict[str, Any],
        corr: CorrelationResult,
        duration: float,
        executed_at: datetime
    ) -> RootCauseAnalysis:
        """Transforms parsed dictionary into RootCauseAnalysis domain object."""
        prim_hyp_data = data.get("primary_hypothesis", {})
        supp_evidences = [
            SupportingEvidence(
                metric_name=ev.get("metric_name", "unknown"),
                observed_value=ev.get("observed_value", "unknown"),
                finding_title=ev.get("finding_title", "finding"),
                relevance_explanation=ev.get("relevance_explanation", "Supports hypothesis"),
            )
            for ev in prim_hyp_data.get("supporting_evidences", [])
        ]

        primary_hypothesis = Hypothesis(
            title=prim_hyp_data.get("title", "Primary Operational Finding"),
            description=prim_hyp_data.get("description", "Analyzed from correlated findings."),
            likelihood_score=float(prim_hyp_data.get("likelihood_score", 0.9)),
            is_primary=True,
            supporting_evidences=supp_evidences,
        )

        alt_hypotheses = [
            Hypothesis(
                title=alt.get("title", "Alternative Hypothesis"),
                description=alt.get("description", ""),
                likelihood_score=float(alt.get("likelihood_score", 0.3)),
                is_primary=False,
            )
            for alt in data.get("alternative_hypotheses", [])
        ]

        reasoning_traces = [
            ReasoningTrace(
                step_number=rt.get("step_number", idx + 1),
                observation=rt.get("observation", ""),
                deduction=rt.get("deduction", ""),
            )
            for idx, rt in enumerate(data.get("reasoning_trace", []))
        ]

        affected_comps = [
            AffectedComponent(
                component_type=ac.get("component_type", "SYSTEM"),
                name=ac.get("name", "Host"),
                impact_level=ac.get("impact_level", "MEDIUM"),
            )
            for ac in data.get("affected_components", [])
        ]

        metadata = AnalysisMetadata(
            provider_used=self.provider_name,
            model_name=self.model_name,
            analysis_duration_seconds=duration,
            total_findings_analyzed=len(corr.findings),
        )

        return RootCauseAnalysis(
            correlation_id=corr.correlation_id,
            investigation_id=corr.investigation_id,
            user_question=corr.user_question,
            primary_root_cause=data.get("primary_root_cause", "No primary root cause identified."),
            overall_confidence=float(data.get("overall_confidence", 0.9)),
            summary=data.get("summary", "Analysis completed."),
            primary_hypothesis=primary_hypothesis,
            alternative_hypotheses=alt_hypotheses,
            reasoning_trace=reasoning_traces,
            affected_components=affected_comps,
            metadata=metadata,
            created_at=executed_at,
        )

    def _parse_recommendation_model(
        self,
        data: Dict[str, Any],
        rca: RootCauseAnalysis,
        duration: float,
        executed_at: datetime
    ) -> RecommendationReport:
        """Transforms parsed dictionary into RecommendationReport domain object."""
        rec_actions = [
            Recommendation(
                title=act.get("title", "Operational Action"),
                description=act.get("description", "Inspect system state."),
                reason=act.get("reason", rca.primary_root_cause),
                category=self._safe_enum(RecommendationCategory, act.get("category", ""), RecommendationCategory.IMMEDIATE),
                priority=self._safe_enum(RecommendationPriority, act.get("priority", ""), RecommendationPriority.P1_CRITICAL),
                risk_level=self._safe_enum(RiskLevel, act.get("risk_level", ""), RiskLevel.LOW),
                expected_benefit=act.get("expected_benefit", "Mitigates operational issue."),
                estimated_impact=act.get("estimated_impact", "Minimal risk read-only operational check."),
                required_skill_level=act.get("required_skill_level", "Senior SRE"),
                requires_human_approval=bool(act.get("requires_human_approval", True)),
                target_resource=act.get("target_resource", "System Resources"),
            )
            for act in data.get("recommended_actions", [])
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
            metadata=metadata,
            created_at=executed_at,
        )

    def _fallback_rca_synthesis(
        self,
        corr: CorrelationResult,
        start_time: float,
        executed_at: datetime,
        error_reason: str = None
    ) -> RootCauseAnalysis:
        """Deterministic rule-based fallback when Hugging Face API is unconfigured or unreachable."""
        duration = round(time.time() - start_time, 3)
        has_execution_failures = any("Execution Failed" in f.title or "Failure" in f.title for f in corr.findings)

        if not corr.findings:
            primary_rc = "Investigation Inconclusive — insufficient evidence collected from host."
            summary = "No diagnostic metric findings could be extracted. Unable to verify system health."
            confidence = 0.1
            primary_hyp = Hypothesis(
                title="Investigation Inconclusive",
                description="No operational evidence was retrieved from server diagnostics.",
                likelihood_score=0.1,
                is_primary=True,
            )
            reasoning = [
                ReasoningTrace(step_number=1, observation="Zero correlated findings retrieved.", deduction="Cannot establish root cause without empirical evidence.")
            ]
            affected = [AffectedComponent(component_type="SYSTEM", name="Server Host", impact_level="HIGH")]
        elif has_execution_failures and len(corr.findings) == sum(1 for f in corr.findings if "Execution Failed" in f.title or "Failure" in f.title):
            primary_rc = "Investigation Inconclusive — Diagnostic SSH command execution failed."
            summary = "Remote diagnostic commands failed to execute. Infrastructure telemetry could not be gathered."
            confidence = 0.1
            primary_hyp = Hypothesis(
                title="Diagnostic Execution Failure",
                description="Commands executed over SSH failed or returned no output.",
                likelihood_score=0.1,
                is_primary=True,
            )
            reasoning = [
                ReasoningTrace(step_number=idx + 1, observation=f.title, deduction=f.summary)
                for idx, f in enumerate(corr.findings)
            ]
            affected = [AffectedComponent(component_type="SYSTEM", name="SSH Connectivity", impact_level="CRITICAL")]
        else:
            top_finding = max(corr.findings, key=lambda f: f.confidence_score)
            primary_rc = f"Primary cause associated with {top_finding.title}: {top_finding.summary}"
            summary = f"Synthesized diagnosis based on {len(corr.findings)} correlated findings."
            confidence = top_finding.confidence_score

            supp_evs = [
                SupportingEvidence(
                    metric_name=ev.metric_name,
                    observed_value=ev.observed_value,
                    finding_title=top_finding.title,
                    relevance_explanation="Direct empirical metric violation.",
                )
                for ev in top_finding.evidences
            ]

            primary_hyp = Hypothesis(
                title=top_finding.title,
                description=top_finding.summary,
                likelihood_score=confidence,
                is_primary=True,
                supporting_evidences=supp_evs,
            )

            reasoning = [
                ReasoningTrace(
                    step_number=idx + 1,
                    observation=f.title,
                    deduction=f.summary,
                )
                for idx, f in enumerate(corr.findings)
            ]

            affected = [
                AffectedComponent(component_type=f.category.value, name=res, impact_level=f.severity.value)
                for f in corr.findings
                for res in f.affected_resources
            ]

        metadata = AnalysisMetadata(
            provider_used="Hugging Face (Fallback Engine)" if error_reason else "Deterministic Synthesizer",
            model_name=self.model_name,
            analysis_duration_seconds=duration,
            total_findings_analyzed=len(corr.findings),
        )

        return RootCauseAnalysis(
            correlation_id=corr.correlation_id,
            investigation_id=corr.investigation_id,
            user_question=corr.user_question,
            primary_root_cause=primary_rc,
            overall_confidence=confidence,
            summary=summary,
            primary_hypothesis=primary_hyp,
            alternative_hypotheses=[],
            reasoning_trace=reasoning,
            affected_components=affected,
            metadata=metadata,
            created_at=executed_at,
        )

    def _fallback_recommendations_guidance(
        self,
        rca: RootCauseAnalysis,
        start_time: float,
        executed_at: datetime,
        error_reason: str = None
    ) -> RecommendationReport:
        """Deterministic rule-based fallback when Hugging Face API is unconfigured or unreachable."""
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
                    description="Ensure whitelisted diagnostic commands (e.g. top, free, df) are installed on remote host.",
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

        metadata = RecommendationMetadata(
            provider_used="Hugging Face (Fallback Engine)" if error_reason else "Deterministic Advisory Synthesizer",
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
            metadata=metadata,
            created_at=executed_at,
        )


# Backward compatibility aliases
HuggingFaceRCAProvider = HuggingFaceProvider
HuggingFaceRecommendationProvider = HuggingFaceProvider
