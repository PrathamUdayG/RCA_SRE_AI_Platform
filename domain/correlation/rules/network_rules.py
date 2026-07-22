"""
Purpose
-------
Network domain correlation rules for analyzing listening ports, routing, and socket activity.

Responsibilities
----------------
- Evaluate open socket count and listening port availability.
- Produce structured Network operational Findings.

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


class NetworkSocketsRule(BaseCorrelationRule):
    """
    Evaluates listening ports and active sockets to report open network services.
    """

    @property
    def name(self) -> str:
        return "NetworkSocketsRule"

    @property
    def category(self) -> str:
        return FindingCategory.NETWORK.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []

        net_step = next((s for s in step_results if s.command_id in ("listening_ports", "network_statistics")), None)
        if not net_step or not net_step.raw_output:
            return findings

        lines = net_step.raw_output.strip().splitlines()
        socket_count = len(lines)

        if socket_count > 0:
            evidence = Evidence(
                metric_name="listening_socket_count",
                observed_value=socket_count,
                source_command=net_step.linux_command,
                context={"sample_ports": lines[:5]},
            )

            findings.append(
                Finding(
                    title="Active Network Services Detected",
                    category=FindingCategory.NETWORK,
                    severity=Severity.INFO,
                    confidence_score=0.90,
                    summary=f"Detected {socket_count} active listening socket entry/entries.",
                    evidences=[evidence],
                    related_metrics=["listening_socket_count"],
                    affected_resources=["Network Stack"],
                )
            )

        return findings
