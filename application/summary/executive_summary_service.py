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
from domain.policy.models import PolicyDecision
from domain.rca.models import RootCauseAnalysis
from domain.recommendation.models import RecommendationReport
from domain.report.models import ExecutiveSummary
from shared.logging import get_logger

logger = get_logger("ExecutiveSummaryService")


class ExecutiveSummaryService:
    """
    Dedicated application service that synthesizes the outputs of Phase 1-6
    into an ExecutiveSummary DTO.
    """

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
            direct_answer = rca.summary
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
            "ai_provider": rca.metadata.provider_used if rca else "N/A",
            "llm_model": rca.metadata.model_name if rca else "N/A",
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
