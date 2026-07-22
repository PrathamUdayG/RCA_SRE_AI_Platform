"""
Purpose
-------
Prompt builder application service for constructing structured SRE prompts from CorrelationResults.

Responsibilities
----------------
- Format Phase 3 findings, evidences, and affected resources into structured prompt payloads.

Does NOT
---------
- Include raw unparsed stdout or SSH terminal logs.
- Call LLM APIs directly.
"""

from typing import Any, Dict

from domain.correlation.models import CorrelationResult


class RCAPromptBuilder:
    """
    Constructs structured prompts for LLM RCA providers.
    """

    def build_payload(self, correlation_result: CorrelationResult) -> Dict[str, Any]:
        """
        Transforms a CorrelationResult into a structured dictionary for AI reasoning.
        """
        findings_payload = []
        for finding in correlation_result.findings:
            evidences = [
                {
                    "metric": ev.metric_name,
                    "observed_value": str(ev.observed_value),
                    "threshold": str(ev.threshold) if ev.threshold is not None else "None",
                    "command": ev.source_command,
                }
                for ev in finding.evidences
            ]
            findings_payload.append({
                "title": finding.title,
                "category": finding.category.value,
                "severity": finding.severity.value,
                "confidence_score": finding.confidence_score,
                "summary": finding.summary,
                "evidences": evidences,
                "affected_resources": finding.affected_resources,
            })

        return {
            "user_question": correlation_result.user_question,
            "investigation_id": correlation_result.investigation_id,
            "correlation_id": correlation_result.correlation_id,
            "findings_count": len(correlation_result.findings),
            "findings": findings_payload,
        }
