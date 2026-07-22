"""
Purpose
-------
Container and Kubernetes domain correlation rules for analyzing Docker containers and K8s pod health.

Responsibilities
----------------
- Evaluate Docker container states and Kubernetes pod statuses.
- Produce structured Container operational Findings.

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


class ContainerHealthRule(BaseCorrelationRule):
    """
    Evaluates Docker container list and K8s pod statuses to detect crashed or exited containers.
    """

    @property
    def name(self) -> str:
        return "ContainerHealthRule"

    @property
    def category(self) -> str:
        return FindingCategory.CONTAINER.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []

        docker_step = next((s for s in step_results if s.command_id in ("docker_containers", "kubectl_pods")), None)
        if not docker_step or not docker_step.raw_output:
            return findings

        output = docker_step.raw_output.strip()

        # Check for exited containers or crashloop pods
        exited_lines = [
            line.strip()
            for line in output.splitlines()
            if any(term in line.lower() for term in ["exited", "crashloopbackoff", "error", "failed"])
        ]

        if exited_lines:
            evidence = Evidence(
                metric_name="container_failure_count",
                observed_value=len(exited_lines),
                source_command=docker_step.linux_command,
                context={"unhealthy_containers": exited_lines[:5]},
            )

            findings.append(
                Finding(
                    title="Container Instance Failure Detected",
                    category=FindingCategory.CONTAINER,
                    severity=Severity.HIGH,
                    confidence_score=0.91,
                    summary=f"Detected {len(exited_lines)} container/pod instance(s) in non-running error state.",
                    evidences=[evidence],
                    related_metrics=["container_failure_count"],
                    affected_resources=["Docker / Kubernetes Runtime"],
                )
            )

        return findings
