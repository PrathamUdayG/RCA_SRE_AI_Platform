"""
Purpose
-------
Application service for synthesizing Phase 1-6 investigation outputs into a unified ExecutiveSummary.

Responsibilities
----------------
- Consume Phase 1 InvestigationPlan, Phase 2 ExecutionResults, Phase 3 CorrelationResults,
  Phase 4 RootCauseAnalysis, Phase 5 Recommendations, Phase 6 PolicyDecisions, and total duration.
- Synthesize a clear, 1-2 paragraph executive direct answer to the user's natural language question.
- Determine overall investigation status ('SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'INCONCLUSIVE', 'NO_DATA').
- Extract empirical evidence metrics, top process observations, and command execution quality metrics.
- Perform 100% deterministic synthesis without executing additional SSH commands or LLM prompts.

Does NOT
---------
- Make network, SSH, or LLM API calls.
- Modify Phase 1-6 business logic or domain models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from domain.correlation.models import CorrelationResult
from domain.execution.models import InvestigationExecutionResult
from domain.investigation.models import InvestigationPlan
from domain.llm import LLMProviderInterface
from domain.policy.models import PolicyDecision
from domain.rca.models import RootCauseAnalysis
from domain.recommendation.models import RecommendationReport
from domain.report.models import ExecutiveSummary
from infrastructure.llm.provider_factory import LLMProviderFactory
from shared.logging import get_logger

logger = get_logger("ExecutiveSummaryService")


class ExecutiveSummaryService:
    """
    Dedicated application service that synthesizes the outputs of Phase 1-6
    into an ExecutiveSummary DTO using the centralized LLMProviderManager.
    """

    def __init__(self, provider: Optional[LLMProviderInterface] = None):
        self.provider = provider or LLMProviderFactory.get_provider()

    def generate_summary(
        self,
        user_question: str,
        plan: Optional[InvestigationPlan] = None,
        execution: Optional[InvestigationExecutionResult] = None,
        correlation: Optional[CorrelationResult] = None,
        rca: Optional[RootCauseAnalysis] = None,
        recommendation: Optional[RecommendationReport] = None,
        policy_decision: Optional[PolicyDecision] = None,
        total_duration: float = 0.0,
    ) -> ExecutiveSummary:
        """
        Synthesizes all completed phase outputs into an ExecutiveSummary.
        """
        logger.info(f"Synthesizing Executive Investigation Summary for query: '{user_question}'")
        executed_at = datetime.utcnow()

        # Step 1: Analyze Execution Quality & SSH Failures
        total_steps = len(execution.step_results) if execution else 0
        failed_steps = sum(1 for s in execution.step_results if s.status.value == "FAILED") if execution else 0
        succeeded_steps = total_steps - failed_steps
        data_quality_val = round((succeeded_steps / total_steps) * 100, 1) if total_steps > 0 else 0.0

        target_server = "testserv.ortusolis.in:22"
        if execution and execution.step_results:
            first_step = execution.step_results[0]
            if hasattr(first_step, "hostname") and first_step.hostname:
                target_server = f"{first_step.hostname}:22"

        # Step 2: Classify Query Intent (Historical vs Real-time)
        q_lower = user_question.lower()
        is_historical_query = any(kw in q_lower for kw in ["when", "past", "history", "historical", "last week", "yesterday", "earlier", "spike last"])

        # Step 3: Synthesize Direct Answer and Status
        if execution and execution.status.value == "FAILED":
            status = "FAILED"
            confidence = 0.0
            primary_rc = "Evidence Collection Failed"
            direct_answer = (
                f"The platform could not determine the answer to '{user_question}' because evidence collection "
                f"failed over SSH during diagnostic command execution. No operational conclusion can be made."
            )
            rec_summary = "Verify SSH credentials, network routing, and target host availability, then rerun the investigation."
        elif is_historical_query:
            status = "INCONCLUSIVE"
            confidence = 0.12
            primary_rc = "Historical Metrics Unavailable"
            direct_answer = (
                f"The platform cannot determine when historical events occurred for '{user_question}' because "
                f"historical time-series metrics are unavailable. Only real-time Linux diagnostics were executed. "
                f"Current real-time system status: {rca.summary if rca else 'No current anomaly detected.'}"
            )
            rec_summary = "Integrate historical time-series monitoring (Prometheus, SAR, Grafana) for past trend analysis."
        elif rca and rca.overall_confidence >= 0.3:
            status = execution.status.value if execution else "SUCCESS"
            confidence = rca.overall_confidence
            primary_rc = rca.primary_root_cause
            direct_answer = self._build_direct_answer(
                user_question=user_question,
                correlation=correlation,
                rca=rca,
                recommendation=recommendation,
            )
            rec_summary = recommendation.executive_summary if recommendation else "No immediate action required."
        else:
            status = "INCONCLUSIVE"
            confidence = rca.overall_confidence if rca else 0.1
            primary_rc = rca.primary_root_cause if rca else "Investigation Inconclusive"
            direct_answer = (
                f"Diagnostic evidence was collected from {target_server}, but evidence was insufficient to "
                f"conclusively isolate a root cause for '{user_question}'."
            )
            rec_summary = recommendation.executive_summary if recommendation else "Perform manual diagnostic inspection."

        # Step 4: Extract Key Findings & Evidence Metrics
        key_findings = [f.title for f in correlation.findings] if correlation else []
        key_evidence: List[Dict[str, Any]] = []

        if correlation and correlation.findings:
            for f in correlation.findings:
                for ev in f.evidences:
                    key_evidence.append({
                        "finding_title": f.title,
                        "category": f.category.value,
                        "severity": f.severity.value,
                        "metric_name": ev.metric_name,
                        "observed_value": str(ev.observed_value),
                        "threshold": str(ev.threshold),
                    })

        # Step 5: Format Policy Evaluation Summary
        policy_sum = "N/A"
        if policy_decision:
            policy_sum = f"Decision: {policy_decision.overall_decision.value} ({len(policy_decision.approval_requests)} action(s) evaluated)"

        # Step 6: Package Investigation Metadata
        metadata = {
            "investigation_id": str(uuid4()),
            "target_server": target_server,
            "start_time_utc": executed_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "duration_seconds": total_duration,
            "commands_executed": total_steps,
            "commands_succeeded": succeeded_steps,
            "commands_failed": failed_steps,
            "data_quality_pct": f"{data_quality_val}%",
            "ai_provider": self.provider.provider_name,
            "llm_model": self.provider.model_name,
        }

        return ExecutiveSummary(
            user_question=user_question,
            direct_answer=direct_answer,
            investigation_status=status,
            confidence_score=confidence,
            primary_root_cause=primary_rc,
            key_findings=key_findings,
            key_evidence=key_evidence,
            recommendations_summary=rec_summary,
            policy_summary=policy_sum,
            investigation_metadata=metadata,
        )

    @staticmethod
    def _build_direct_answer(
        user_question: str,
        correlation: Optional[CorrelationResult],
        rca: Optional[RootCauseAnalysis],
        recommendation: Optional[RecommendationReport],
    ) -> str:
        """Build a plain-language answer before exposing investigation detail.

        This card is the user's answer, not an internal RCA or audit record. It is
        deliberately deterministic so its wording remains grounded in the completed
        investigation and does not depend on an LLM response format.
        """
        findings = correlation.findings if correlation else []
        target_label, target_categories = ExecutiveSummaryService._question_target(user_question)
        relevant_findings = [
            finding for finding in findings
            if not target_categories or finding.category.value in target_categories
        ]
        if not relevant_findings:
            relevant_findings = findings

        if not relevant_findings:
            return (
                f"I could not confirm the {target_label.lower()} from the collected evidence. "
                "No verified operational conclusion should be made yet."
            )

        unhealthy_severities = {"MEDIUM", "HIGH", "CRITICAL"}
        needs_attention = any(finding.severity.value in unhealthy_severities for finding in relevant_findings)
        lead = (
            f"Your {target_label.lower()} needs attention."
            if needs_attention
            else f"Your {target_label.lower()} is healthy."
        )
        finding = relevant_findings[0]
        evidence_sentence = ExecutiveSummaryService._plain_evidence(finding)

        answer_parts = [lead, finding.summary.rstrip(".") + "."]
        if evidence_sentence:
            answer_parts.append(evidence_sentence)
        if needs_attention and rca and rca.summary:
            answer_parts.append(f"The investigation indicates that {rca.summary.rstrip('.') }.")

        if recommendation and recommendation.recommended_actions:
            next_action = recommendation.recommended_actions[0].title.rstrip(".")
            answer_parts.append(f"Recommended next step: {next_action}.")
        elif not needs_attention:
            answer_parts.append("No immediate action is required based on this investigation.")

        return " ".join(answer_parts)

    @staticmethod
    def _question_target(user_question: str) -> tuple[str, set[str]]:
        """Map a natural-language question to a simple user-facing system target."""
        question = user_question.lower()
        if any(term in question for term in ("cpu", "processor", "load")):
            return "CPU status", {"CPU", "PROCESS"}
        if any(term in question for term in ("memory", "ram", "swap")):
            return "memory status", {"MEMORY", "PROCESS"}
        if any(term in question for term in ("disk", "storage", "filesystem", "inode")):
            return "disk status", {"DISK"}
        if any(term in question for term in ("network", "connection", "dns", "port")):
            return "network status", {"NETWORK"}
        if any(term in question for term in ("service", "daemon", "systemd")):
            return "service status", {"SERVICE"}
        return "system status", set()

    @staticmethod
    def _plain_evidence(finding) -> str:
        """Express the first verified metric in operator-friendly language."""
        if not finding.evidences:
            return ""
        evidence = finding.evidences[0]
        metric_labels = {
            "load_average_1m": "1-minute load average",
            "load_average_5m": "5-minute load average",
            "memory_used_percent": "memory usage",
            "swap_used_percent": "swap usage",
            "disk_usage_percent": "disk usage",
        }
        metric = metric_labels.get(evidence.metric_name, evidence.metric_name.replace("_", " "))
        value = evidence.observed_value
        if evidence.threshold is None:
            return f"Observed {metric}: {value}."
        comparison = "above" if finding.severity.value in {"MEDIUM", "HIGH", "CRITICAL"} else "within"
        return f"The {metric} is {value}, {comparison} the reference threshold of {evidence.threshold}."
