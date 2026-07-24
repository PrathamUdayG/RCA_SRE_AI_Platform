"""
Purpose
-------
Container and Kubernetes domain correlation rules consuming structured container and pod telemetry.

Responsibilities
----------------
- Evaluate Docker container states and Kubernetes pod statuses from structured telemetry.
- Produce structured Container operational Findings.
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
    Evaluates Docker container list and K8s pod statuses to detect crashed or exited instances.
    """

    @property
    def name(self) -> str:
        return "ContainerHealthRule"

    @property
    def category(self) -> str:
        return FindingCategory.CONTAINER.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []

        docker_step = next((s for s in step_results if s.command_id == "docker_containers"), None)
        k8s_step = next((s for s in step_results if s.command_id == "kubectl_pods"), None)

        # Evaluate Docker container telemetry
        if docker_step and docker_step.parsed_output:
            exited = docker_step.parsed_output.get("exited_count", 0)
            containers = docker_step.parsed_output.get("containers", [])
            exited_containers = [c for c in containers if "Exited" in c.get("status", "")]

            if exited > 0 or exited_containers:
                evidences = [
                    Evidence(
                        metric_name="exited_docker_containers_count",
                        observed_value=exited or len(exited_containers),
                        threshold=0,
                        source_command=docker_step.linux_command,
                        context={"exited_container_names": [c.get("names") for c in exited_containers[:5]]},
                    )
                ]

                findings.append(
                    Finding(
                        title="Exited Docker Container Detected",
                        category=FindingCategory.CONTAINER,
                        severity=Severity.HIGH,
                        confidence_score=0.95,
                        summary=f"Detected {len(exited_containers)} Docker container instance(s) in Exited state.",
                        evidences=evidences,
                        related_metrics=["exited_docker_containers_count"],
                        affected_resources=[c.get("names", "container") for c in exited_containers[:5]],
                    )
                )

        # Evaluate Kubernetes pod telemetry
        if k8s_step and k8s_step.parsed_output:
            unhealthy = k8s_step.parsed_output.get("unhealthy_pods", [])
            if unhealthy:
                evidences = [
                    Evidence(
                        metric_name="unhealthy_k8s_pods_count",
                        observed_value=len(unhealthy),
                        threshold=0,
                        source_command=k8s_step.linux_command,
                        context={"unhealthy_pods": [p.get("name") for p in unhealthy[:5]]},
                    )
                ]

                findings.append(
                    Finding(
                        title="Unhealthy Kubernetes Pod Detected",
                        category=FindingCategory.CONTAINER,
                        severity=Severity.HIGH,
                        confidence_score=0.95,
                        summary=f"Detected {len(unhealthy)} Kubernetes pod(s) in non-Running state.",
                        evidences=evidences,
                        related_metrics=["unhealthy_k8s_pods_count"],
                        affected_resources=[p.get("name", "pod") for p in unhealthy[:5]],
                    )
                )

        return findings
