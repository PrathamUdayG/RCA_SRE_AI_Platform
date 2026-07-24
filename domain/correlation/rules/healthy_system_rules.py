"""
Purpose
-------
Domain correlation rule for identifying nominal system health states.

Responsibilities
----------------
- Evaluate telemetry against baseline healthy metrics.
- Produce structured INFO operational Findings when infrastructure component states are healthy.
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


class HealthySystemRule(BaseCorrelationRule):
    """
    Evaluates execution results for healthy metric patterns and produces INFO findings.
    """

    @property
    def name(self) -> str:
        return "HealthySystemRule"

    @property
    def category(self) -> str:
        return FindingCategory.SYSTEM.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []

        load_step = next((s for s in step_results if s.command_id in ("cpu_load", "uptime")), None)
        mem_step = next((s for s in step_results if s.command_id == "memory_usage"), None)
        disk_step = next((s for s in step_results if s.command_id == "disk_usage"), None)

        # 1. Healthy CPU Load
        if load_step and load_step.parsed_output:
            load_1m = load_step.parsed_output.get("load_average_1m", 0.0)
            if isinstance(load_1m, (int, float)) and load_1m <= 1.0:
                findings.append(
                    Finding(
                        title="CPU Load Within Normal Parameters",
                        category=FindingCategory.CPU,
                        severity=Severity.INFO,
                        confidence_score=0.99,
                        summary=f"1-minute load average is nominal at {load_1m} (under threshold of 1.0).",
                        evidences=[
                            Evidence(
                                metric_name="load_average_1m",
                                observed_value=load_1m,
                                threshold=1.0,
                                source_command=load_step.linux_command,
                            )
                        ],
                        related_metrics=["load_average_1m"],
                        affected_resources=["System CPU"],
                    )
                )

        # 2. Healthy Memory Availability
        if mem_step and mem_step.parsed_output:
            mem_data = mem_step.parsed_output.get("memory", {})
            total_mb = mem_data.get("total_mb", 0)
            used_mb = mem_data.get("used_mb", 0)
            if total_mb > 0:
                usage_pct = (used_mb / total_mb) * 100.0
                if usage_pct <= 80.0:
                    findings.append(
                        Finding(
                            title="Memory Capacity Healthy",
                            category=FindingCategory.MEMORY,
                            severity=Severity.INFO,
                            confidence_score=0.99,
                            summary=f"System RAM utilization is optimal at {round(usage_pct, 1)}% ({used_mb}MB / {total_mb}MB used).",
                            evidences=[
                                Evidence(
                                    metric_name="memory_used_pct",
                                    observed_value=round(usage_pct, 1),
                                    threshold=80.0,
                                    source_command=mem_step.linux_command,
                                )
                            ],
                            related_metrics=["memory_used_pct"],
                            affected_resources=["System Memory (RAM)"],
                        )
                    )

        # 3. Healthy Disk Space
        if disk_step and disk_step.parsed_output:
            filesystems = disk_step.parsed_output.get("filesystems", [])
            high_fs = [fs for fs in filesystems if int(fs.get("usage_percent", "0%").rstrip("%") or "0") >= 80]
            if filesystems and not high_fs:
                findings.append(
                    Finding(
                        title="Disk Capacity Healthy",
                        category=FindingCategory.DISK,
                        severity=Severity.INFO,
                        confidence_score=0.99,
                        summary=f"All mounted filesystems have sufficient free storage space.",
                        evidences=[
                            Evidence(
                                metric_name="max_disk_usage_percent",
                                observed_value="<80%",
                                threshold="80%",
                                source_command=disk_step.linux_command,
                            )
                        ],
                        related_metrics=["disk_usage_percent"],
                        affected_resources=["Storage Filesystems"],
                    )
                )

        return findings
