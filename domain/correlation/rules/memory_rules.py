"""
Purpose
-------
Memory domain correlation rules for analyzing RAM utilization, swap memory activity, and top memory processes.

Responsibilities
----------------
- Correlate RAM utilization with swap memory activity to detect memory pressure.
- Produce structured Memory operational Findings.

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


class MemoryPressureRule(BaseCorrelationRule):
    """
    Correlates RAM utilization and active swap memory usage to detect system memory pressure.
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

                if top_mem_step and top_mem_step.raw_output:
                    evidences.append(
                        Evidence(
                            metric_name="top_memory_processes_stdout",
                            observed_value=top_mem_step.raw_output.strip().splitlines()[:5],
                            source_command=top_mem_step.linux_command,
                        )
                    )

                severity = Severity.HIGH if (usage_pct > 90.0 or swap_used_mb > 500) else Severity.MEDIUM

                summary = (
                    f"System memory usage is at {round(usage_pct, 1)}% ({used_mb}MB / {total_mb}MB used). "
                )
                if swap_used_mb > 0:
                    summary += f"Swap memory is actively being used ({swap_used_mb}MB used)."

                findings.append(
                    Finding(
                        title="High Memory Pressure Detected",
                        category=FindingCategory.MEMORY,
                        severity=severity,
                        confidence_score=0.92,
                        summary=summary,
                        evidences=evidences,
                        related_metrics=["memory_used_pct", "swap_used_mb", "available_mb"],
                        affected_resources=["System Memory (RAM)", "Swap File/Partition"],
                    )
                )

        return findings
