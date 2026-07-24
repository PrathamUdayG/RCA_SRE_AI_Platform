"""
Purpose
-------
Domain correlation rule for detecting missing telemetry or unparseable diagnostic output.

Responsibilities
----------------
- Evaluate execution step results for missing telemetry data.
- Produce structured WARNING operational Findings when expected command telemetry is absent.
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


class MissingTelemetryRule(BaseCorrelationRule):
    """
    Evaluates step executions for missing telemetry data and produces WARNING findings.
    """

    @property
    def name(self) -> str:
        return "MissingTelemetryRule"

    @property
    def category(self) -> str:
        return FindingCategory.SYSTEM.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []

        for step in step_results:
            if not step.parsed_output or "raw_output" in step.parsed_output or "parse_error" in step.parsed_output:
                findings.append(
                    Finding(
                        title=f"Missing Structured Telemetry: {step.command_id}",
                        category=FindingCategory.SYSTEM,
                        severity=Severity.WARNING,
                        confidence_score=0.85,
                        summary=f"Diagnostic command '{step.command_id}' did not yield validated structured telemetry.",
                        evidences=[
                            Evidence(
                                metric_name="telemetry_parsed_status",
                                observed_value="MISSING_OR_UNPARSED",
                                threshold="PARSED_JSON",
                                source_command=step.linux_command,
                                context={"error": step.error_message},
                            )
                        ],
                        related_metrics=["telemetry_parsed_status"],
                        affected_resources=[f"Command: {step.command_id}"],
                    )
                )

        return findings
