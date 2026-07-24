"""
Purpose
-------
Disk domain correlation rules consuming structured telemetry for filesystem storage capacity and inode exhaustion.

Responsibilities
----------------
- Evaluate mounted filesystem storage utilization and inode capacity percentages.
- Cross-correlate disk usage % with inode utilization.
- Produce structured Disk operational Findings.
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


class DiskCapacityRule(BaseCorrelationRule):
    """
    Evaluates mounted filesystem space and inode utilization telemetry.
    """

    @property
    def name(self) -> str:
        return "DiskCapacityRule"

    @property
    def category(self) -> str:
        return FindingCategory.DISK.value

    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        findings: List[Finding] = []

        disk_step = next((s for s in step_results if s.command_id == "disk_usage"), None)
        inode_step = next((s for s in step_results if s.command_id == "disk_inodes"), None)

        if not disk_step or not disk_step.parsed_output:
            return findings

        filesystems = disk_step.parsed_output.get("filesystems", [])
        high_usage_fs = []

        for fs in filesystems:
            usage_str = fs.get("usage_percent", "0%").rstrip("%")
            try:
                usage_val = int(usage_str)
                if usage_val >= 80:
                    high_usage_fs.append((fs.get("mounted_on", "unknown"), usage_val, fs))
            except ValueError:
                continue

        # Inode cross-correlation
        inode_data = {}
        if inode_step and inode_step.parsed_output:
            for inode in inode_step.parsed_output.get("inodes", []):
                inode_data[inode.get("mounted_on", "")] = inode.get("iuse_percent", "0%")

        if high_usage_fs:
            evidences = []
            affected_mounts = []

            for mount, pct, fs_data in high_usage_fs:
                affected_mounts.append(mount)
                ctx = dict(fs_data)
                if mount in inode_data:
                    ctx["inode_usage_percent"] = inode_data[mount]

                evidences.append(
                    Evidence(
                        metric_name=f"disk_usage_{mount}",
                        observed_value=f"{pct}%",
                        threshold="80%",
                        source_command=disk_step.linux_command,
                        context=ctx,
                    )
                )

            max_pct = max(pct for _, pct, _ in high_usage_fs)
            severity = Severity.CRITICAL if max_pct >= 95 else (Severity.HIGH if max_pct >= 90 else Severity.MEDIUM)

            summary = f"Filesystem storage usage exceeded safety threshold on mount(s): {', '.join(affected_mounts)} (highest usage: {max_pct}%)."

            findings.append(
                Finding(
                    title="High Disk Capacity Usage Warning",
                    category=FindingCategory.DISK,
                    severity=severity,
                    confidence_score=0.98,
                    summary=summary,
                    evidences=evidences,
                    related_metrics=["disk_usage_percent", "inode_usage_percent"],
                    affected_resources=affected_mounts,
                )
            )

        return findings
