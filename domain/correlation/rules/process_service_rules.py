"""
Purpose
-------
Service and Process domain correlation rules consuming structured telemetry for failed systemd services.

Responsibilities
----------------
- Evaluate system service states to detect failed units from structured telemetry.
- Produce structured Service operational Findings.
"""

from typing import List

from domain.execution.models import StepExecutionResult
from domain.correlation.models import (
    Evidence,
    Finding,
    FindingCategory,
    Severity,
)
from .base_rule import BaseCorrelationRule


class ServiceFailureRule(BaseCorrelationRule):
    """
    Evaluates systemd unit states to detect failed services using structured telemetry.
    """

    @property
    def name(self) -> str:
        return "ServiceFailureRule"

    @property
    def category(self) -> str:
        return FindingCategory.SERVICE.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []

        svc_step = next((s for s in step_results if s.command_id == "failed_services"), None)
        if not svc_step or not svc_step.parsed_output:
            return findings

        failed_units = svc_step.parsed_output.get("failed_services", [])
        total_failed = svc_step.parsed_output.get("total_failed", len(failed_units))

        if total_failed > 0 or failed_units:
            unit_names = [f.get("unit", "service") for f in failed_units]
            evidence = Evidence(
                metric_name="failed_systemd_units_count",
                observed_value=total_failed,
                threshold=0,
                source_command=svc_step.linux_command,
                context={"failed_units": unit_names},
            )

            severity = Severity.CRITICAL if total_failed > 3 else Severity.HIGH

            findings.append(
                Finding(
                    title="Failed Systemd Service Units Detected",
                    category=FindingCategory.SERVICE,
                    severity=severity,
                    confidence_score=0.98,
                    summary=f"Found {total_failed} systemd unit(s) in failed operational state: {', '.join(unit_names[:5])}.",
                    evidences=[evidence],
                    related_metrics=["failed_systemd_units_count"],
                    affected_resources=unit_names or ["Systemd Service Manager"],
                )
            )

        return findings
