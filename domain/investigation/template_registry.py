"""
Purpose:
--------
Registry of pre-configured diagnostic investigation templates.

Responsibilities:
-----------------
- Provide template definitions for common SRE incident scenarios.
- Expose lookup mechanisms for template matching.
- Enforce 100% 1-to-1 consistency between command keys and dedicated parser names.
"""

from typing import Dict, List, Optional
from .exceptions import TemplateNotFoundError
from .models import InvestigationStep


class TemplateRegistry:
    """
    Registry providing standardized sets of investigation steps for incident patterns.
    """

    def __init__(self):
        self._templates: Dict[str, List[Dict[str, str]]] = {
            "slow_server": [
                {
                    "command_id": "cpu_load",
                    "description": "Check system load averages for CPU saturation.",
                    "parser_name": "parse_cpu_load",
                },
                {
                    "command_id": "cpu_usage",
                    "description": "Check current CPU utilization percentages.",
                    "parser_name": "parse_top_cpu",
                },
                {
                    "command_id": "top_cpu_processes",
                    "description": "Identify top processes consuming CPU resources.",
                    "parser_name": "parse_top_cpu_processes",
                },
                {
                    "command_id": "memory_usage",
                    "description": "Check RAM usage and swap memory saturation.",
                    "parser_name": "parse_free_m",
                },
                {
                    "command_id": "top_memory_processes",
                    "description": "Identify top memory-consuming processes.",
                    "parser_name": "parse_top_memory_processes",
                },
                {
                    "command_id": "disk_usage",
                    "description": "Verify filesystem storage availability.",
                    "parser_name": "parse_df_h",
                },
            ],
            "high_memory": [
                {
                    "command_id": "memory_usage",
                    "description": "Check total RAM and swap space utilization.",
                    "parser_name": "parse_free_m",
                },
                {
                    "command_id": "memory_details",
                    "description": "Inspect detailed buffer and cached memory breakdown.",
                    "parser_name": "parse_proc_meminfo",
                },
                {
                    "command_id": "top_memory_processes",
                    "description": "Identify processes causing memory pressure.",
                    "parser_name": "parse_top_memory_processes",
                },
            ],
            "high_cpu": [
                {
                    "command_id": "cpu_usage",
                    "description": "Measure overall CPU activity.",
                    "parser_name": "parse_top_cpu",
                },
                {
                    "command_id": "cpu_load",
                    "description": "Retrieve 1m, 5m, and 15m load averages.",
                    "parser_name": "parse_cpu_load",
                },
                {
                    "command_id": "top_cpu_processes",
                    "description": "Locate top processes driving CPU usage.",
                    "parser_name": "parse_top_cpu_processes",
                },
            ],
            "disk_space": [
                {
                    "command_id": "disk_usage",
                    "description": "Inspect mounted disk usage percentages.",
                    "parser_name": "parse_df_h",
                },
                {
                    "command_id": "disk_inodes",
                    "description": "Check inode capacity and usage.",
                    "parser_name": "parse_df_i",
                },
                {
                    "command_id": "block_devices",
                    "description": "List attached block storage devices.",
                    "parser_name": "parse_lsblk",
                },
            ],
            "network_connectivity": [
                {
                    "command_id": "ip_address",
                    "description": "Retrieve network interface IP configurations.",
                    "parser_name": "parse_ip_addr",
                },
                {
                    "command_id": "listening_ports",
                    "description": "Inspect open listening TCP and UDP sockets.",
                    "parser_name": "parse_ss_tuln",
                },
                {
                    "command_id": "routing_table",
                    "description": "Check IP routing gateway configuration.",
                    "parser_name": "parse_ip_route",
                },
            ],
            "general_health": [
                {
                    "command_id": "hostname",
                    "description": "Get server hostname.",
                    "parser_name": "parse_hostname",
                },
                {
                    "command_id": "uptime",
                    "description": "Check server uptime and user count.",
                    "parser_name": "parse_uptime",
                },
                {
                    "command_id": "memory_usage",
                    "description": "Check memory availability.",
                    "parser_name": "parse_free_m",
                },
                {
                    "command_id": "disk_usage",
                    "description": "Verify disk space availability.",
                    "parser_name": "parse_df_h",
                },
            ],
            "failed_services": [
                {
                    "command_id": "failed_services",
                    "description": "Check for systemd units in failed state.",
                    "parser_name": "parse_failed_services",
                },
                {
                    "command_id": "running_services",
                    "description": "List currently active systemd services.",
                    "parser_name": "parse_running_services",
                },
            ],
            "container_issues": [
                {
                    "command_id": "docker_containers",
                    "description": "List Docker containers and exit codes.",
                    "parser_name": "parse_docker_ps",
                },
                {
                    "command_id": "kubectl_pods",
                    "description": "List Kubernetes pods and status.",
                    "parser_name": "parse_kubectl_pods",
                },
            ],
        }

    def get_template(self, template_name: str) -> List[InvestigationStep]:
        """
        Retrieves instantiated InvestigationStep list for a given template name.
        """
        if template_name not in self._templates:
            raise TemplateNotFoundError(template_name)

        raw_steps = self._templates[template_name]
        steps = []
        for idx, item in enumerate(raw_steps, start=1):
            steps.append(
                InvestigationStep(
                    order=idx,
                    command_id=item["command_id"],
                    description=item["description"],
                    parser_name=item["parser_name"],
                    timeout_seconds=30,
                    depends_on=[],
                )
            )
        return steps

    def list_templates(self) -> List[str]:
        """Returns list of registered template names."""
        return list(self._templates.keys())
