"""
Purpose
-------
Service and Process domain correlation rules for analyzing failed systemd services and process state issues.

Responsibilities
----------------
- Evaluate system service states to detect failed units.
- Produce structured Service and Process operational Findings.

Does NOT
---------
- Call LLM APIs or execute SSH commands.
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
    Evaluates systemd unit states to detect failed services.
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
        if not svc_step or not svc_step.raw_output:
            return findings

        output = svc_step.raw_output.strip()

        # Check if failed services output contains active failed units
        if "0 loaded units listed" not in output and "loaded units listed" in output:
            failed_lines = [line.strip() for line in output.splitlines() if "failed" in line.lower()]

            if failed_lines:
                evidence = Evidence(
                    metric_name="failed_systemd_units",
                    observed_value=failed_lines,
                    threshold="0 failed units",
                    source_command=svc_step.linux_command,
                )

                findings.append(
                    Finding(
                        title="Failed Systemd Service Detected",
                        category=FindingCategory.SERVICE,
                        severity=Severity.HIGH,
                        confidence_score=0.95,
                        summary=f"Found {len(failed_lines)} systemd unit(s) in failed state.",
                        evidences=[evidence],
                        related_metrics=["failed_systemd_units"],
                        affected_resources=["Systemd Service Manager"],
                    )
                )

        return findings
