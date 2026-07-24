"""
Purpose
-------
CPU domain correlation rules consuming structured telemetry for load averages, CPU usage, and top CPU processes.

Responsibilities
----------------
- Evaluate load averages against CPU utilization and top processes telemetry.
- Cross-correlate CPU load, utilization %, and process details without raw text regex.
- Produce structured CPU operational Findings.
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
    Correlates system load averages, top CPU processes, and CPU utilization telemetry.
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
        cpu_usage_step = next((s for s in step_results if s.command_id == "cpu_usage"), None)
        top_proc_step = next((s for s in step_results if s.command_id == "top_cpu_processes"), None)

        if not load_step or not load_step.parsed_output:
            return findings

        load_1m = load_step.parsed_output.get("load_average_1m", 0.0)
        load_5m = load_step.parsed_output.get("load_average_5m", 0.0)

        # Cross-correlate with top CPU processes telemetry
        top_processes = []
        if top_proc_step and top_proc_step.parsed_output:
            top_processes = top_proc_step.parsed_output.get("processes", [])

        # Cross-correlate with top -bn1 CPU usage telemetry
        user_pct = 0.0
        sys_pct = 0.0
        if cpu_usage_step and cpu_usage_step.parsed_output:
            user_pct = cpu_usage_step.parsed_output.get("user_pct", 0.0)
            sys_pct = cpu_usage_step.parsed_output.get("system_pct", 0.0)

        if isinstance(load_1m, (int, float)) and load_1m > 1.0:
            evidences = [
                Evidence(
                    metric_name="load_average_1m",
                    observed_value=load_1m,
                    threshold=1.0,
                    source_command=load_step.linux_command,
                    context={"load_average_5m": load_5m, "user_pct": user_pct, "system_pct": sys_pct},
                )
            ]

            summary = f"1-minute system load average is elevated at {load_1m} (threshold: 1.0)."

            if top_processes:
                top_3 = top_processes[:3]
                proc_str = ", ".join([f"{p.get('command', 'proc')} (PID {p.get('pid')}, {p.get('usage_value')}%)" for p in top_3])
                summary += f" Top CPU processes: {proc_str}."
                evidences.append(
                    Evidence(
                        metric_name="top_cpu_processes",
                        observed_value=top_3,
                        source_command=top_proc_step.linux_command if top_proc_step else "ps",
                    )
                )

            severity = Severity.CRITICAL if load_1m > 5.0 else (Severity.HIGH if load_1m > 2.5 else Severity.MEDIUM)

            findings.append(
                Finding(
                    title="Elevated CPU Load Saturation",
                    category=FindingCategory.CPU,
                    severity=severity,
                    confidence_score=0.95,
                    summary=summary,
                    evidences=evidences,
                    related_metrics=["load_average_1m", "load_average_5m", "user_pct", "system_pct"],
                    affected_resources=["CPU Core(s)"],
                )
            )

        return findings
