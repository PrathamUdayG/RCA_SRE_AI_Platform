"""
Purpose
-------
CPU domain correlation rules for analyzing CPU saturation, load averages, and top CPU processes.

Responsibilities
----------------
- Evaluate load averages against CPU utilization metrics.
- Correlate high CPU load with top CPU consuming processes.
- Produce structured CPU operational Findings.

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


class CPUSaturationRule(BaseCorrelationRule):
    """
    Correlates system load averages with process CPU utilization to detect CPU saturation.
    """

    @property
    def name(self) -> str:
        return "CPUSaturationRule"

    @property
    def category(self) -> str:
        return FindingCategory.CPU.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []

        load_step = next((s for s in step_results if s.command_id in ("cpu_load", "uptime")), None)
        top_proc_step = next((s for s in step_results if s.command_id == "top_cpu_processes"), None)

        if not load_step or not load_step.parsed_output:
            return findings

        load_1m = load_step.parsed_output.get("load_average_1m")
        load_5m = load_step.parsed_output.get("load_average_5m")

        if load_1m is not None and isinstance(load_1m, (int, float)) and load_1m > 1.0:
            evidences = [
                Evidence(
                    metric_name="load_average_1m",
                    observed_value=load_1m,
                    threshold=1.0,
                    source_command=load_step.linux_command,
                    context={"load_average_5m": load_5m},
                )
            ]

            summary = f"1-minute load average is elevated at {load_1m} (threshold: 1.0)."
            affected_procs = []

            if top_proc_step and top_proc_step.raw_output:
                evidences.append(
                    Evidence(
                        metric_name="top_cpu_processes_stdout",
                        observed_value=top_proc_step.raw_output.strip().splitlines()[:5],
                        source_command=top_proc_step.linux_command,
                    )
                )
                summary += " Top CPU consuming processes identified."

            severity = Severity.HIGH if load_1m > 3.0 else Severity.MEDIUM

            findings.append(
                Finding(
                    title="Elevated CPU Load Average",
                    category=FindingCategory.CPU,
                    severity=severity,
                    confidence_score=0.95,
                    summary=summary,
                    evidences=evidences,
                    related_metrics=["load_average_1m", "load_average_5m"],
                    affected_resources=["CPU Core(s)"],
                )
            )

        return findings
