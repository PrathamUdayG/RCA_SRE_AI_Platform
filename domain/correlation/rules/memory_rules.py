"""
Purpose
-------
Memory domain correlation rules consuming structured telemetry for RAM, swap, and top memory processes.

Responsibilities
----------------
- Correlate RAM utilization, active swap memory usage, and top process telemetry to detect memory pressure.
- Produce structured Memory operational Findings.
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


class MemoryPressureRule(BaseCorrelationRule):
    """
    Correlates RAM utilization, active swap memory usage, and top memory process telemetry.
    """

    @property
    def name(self) -> str:
        return "MemoryPressureRule"

    @property
    def category(self) -> str:
        return FindingCategory.MEMORY.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []

        mem_step = next((s for s in step_results if s.command_id == "memory_usage"), None)
        top_mem_step = next((s for s in step_results if s.command_id == "top_memory_processes"), None)

        if not mem_step or not mem_step.parsed_output:
            return findings

        mem_data = mem_step.parsed_output.get("memory", {})
        swap_data = mem_step.parsed_output.get("swap", {})

        total_mb = mem_data.get("total_mb", 0)
        used_mb = mem_data.get("used_mb", 0)
        free_mb = mem_data.get("free_mb", 0)
        available_mb = mem_data.get("available_mb", free_mb)

        swap_used_mb = swap_data.get("used_mb", 0)

        if total_mb > 0:
            usage_pct = (used_mb / total_mb) * 100.0

            if usage_pct > 80.0 or swap_used_mb > 100:
                evidences = [
                    Evidence(
                        metric_name="memory_used_pct",
                        observed_value=round(usage_pct, 1),
                        threshold=80.0,
                        source_command=mem_step.linux_command,
                        context={"used_mb": used_mb, "total_mb": total_mb, "available_mb": available_mb},
                    )
                ]

                if swap_used_mb > 0:
                    evidences.append(
                        Evidence(
                            metric_name="swap_used_mb",
                            observed_value=swap_used_mb,
                            threshold=0,
                            source_command=mem_step.linux_command,
                        )
                    )

                top_processes = []
                if top_mem_step and top_mem_step.parsed_output:
                    top_processes = top_mem_step.parsed_output.get("processes", [])

                summary = f"System memory usage is elevated at {round(usage_pct, 1)}% ({used_mb}MB / {total_mb}MB used). "
                if swap_used_mb > 0:
                    summary += f"Swap memory is actively being used ({swap_used_mb}MB used)."

                if top_processes:
                    top_3 = top_processes[:3]
                    proc_str = ", ".join([f"{p.get('command', 'proc')} (PID {p.get('pid')}, {p.get('usage_value')}%)" for p in top_3])
                    summary += f" Top memory processes: {proc_str}."
                    evidences.append(
                        Evidence(
                            metric_name="top_memory_processes",
                            observed_value=top_3,
                            source_command=top_mem_step.linux_command if top_mem_step else "ps",
                        )
                    )

                severity = Severity.CRITICAL if (usage_pct > 95.0 or swap_used_mb > 1000) else (
                    Severity.HIGH if (usage_pct > 85.0 or swap_used_mb > 500) else Severity.MEDIUM
                )

                findings.append(
                    Finding(
                        title="High Memory Pressure Detected",
                        category=FindingCategory.MEMORY,
                        severity=severity,
                        confidence_score=0.95,
                        summary=summary,
                        evidences=evidences,
                        related_metrics=["memory_used_pct", "swap_used_mb", "available_mb"],
                        affected_resources=["System Memory (RAM)", "Swap Partition"],
                    )
                )

        return findings
