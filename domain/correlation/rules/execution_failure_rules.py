"""
Purpose
-------
Domain correlation rule for detecting execution step failures, timeouts, and missing metrics.

Responsibilities
----------------
- Evaluate step execution results for FAILED, TIMEOUT, or missing output states.
- Generate structured SYSTEM operational Findings for failed command executions.
- Ensure execution failures are never silently swallowed as empty findings.

Does NOT
---------
- Call LLM APIs or execute SSH commands.
"""

from typing import List

from domain.execution.models import ExecutionStatus, StepExecutionResult
from domain.correlation.models import (
    Evidence,
    Finding,
    FindingCategory,
    Severity,
)
from .base_rule import BaseCorrelationRule


class ExecutionFailureRule(BaseCorrelationRule):
    """
    Correlates step execution failures and missing evidence to produce operational findings.
    """

    @property
    def name(self) -> str:
        return "ExecutionFailureRule"

    @property
    def category(self) -> str:
        return FindingCategory.SYSTEM.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []
        failed_steps = [
            s for s in step_results
            if s.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT)
            or (s.error_message and not s.raw_output)
        ]

        if not failed_steps:
            return findings

        total_steps = len(step_results)
        failed_count = len(failed_steps)

        for step in failed_steps:
            error_reason = step.error_message or "No output returned or command timed out."
            evidences = [
                Evidence(
                    metric_name="execution_status",
                    observed_value=step.status.value,
                    threshold="SUCCESS",
                    source_command=step.linux_command,
                    context={"error_message": error_reason, "command_id": step.command_id},
                )
            ]

            severity = Severity.HIGH if failed_count == total_steps else Severity.MEDIUM

            findings.append(
                Finding(
                    title=f"Command Execution Failed: {step.command_id}",
                    category=FindingCategory.SYSTEM,
                    severity=severity,
                    confidence_score=1.0,
                    summary=f"Diagnostic command '{step.linux_command}' failed to execute: {error_reason}",
                    evidences=evidences,
                    related_metrics=["execution_status", "step_error"],
                    affected_resources=[f"Command: {step.command_id}"],
                )
            )

        # Aggregate summary finding if multiple or all commands failed
        if failed_count == total_steps and total_steps > 0:
            findings.append(
                Finding(
                    title="Complete Investigation Execution Failure",
                    category=FindingCategory.SYSTEM,
                    severity=Severity.CRITICAL,
                    confidence_score=1.0,
                    summary=f"All {total_steps} diagnostic investigation step(s) failed to execute over SSH. Infrastructure evidence could not be collected.",
                    evidences=[
                        Evidence(
                            metric_name="failed_step_count",
                            observed_value=failed_count,
                            threshold=0,
                            source_command="SSH Runner",
                            context={"total_steps": total_steps},
                        )
                    ],
                    related_metrics=["failed_step_count"],
                    affected_resources=["SSH Infrastructure Connectivity"],
                )
            )

        return findings
