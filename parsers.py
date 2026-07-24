"""
Purpose
-------
Backward compatible parser facade delegating to infrastructure.parsers.linux_parsers.
"""

from typing import Any, Dict
from infrastructure.parsers.linux_parsers import (
    parse_command_output,
    parse_hostname,
    parse_whoami,
    parse_uptime,
    parse_free_m,
    parse_df_h,
    parse_cpu_load,
    parse_top_cpu,
    parse_lscpu,
    parse_proc_meminfo,
    parse_df_i,
    parse_lsblk,
    parse_mount,
    parse_ip_addr,
    parse_ip_route,
    parse_ss_tuln,
    parse_ss_s,
    parse_ps_aux,
    parse_pstree,
    parse_top_cpu_processes,
    parse_top_memory_processes,
    parse_running_services,
    parse_failed_services,
    parse_who,
    parse_last,
    parse_docker_ps,
    parse_kubectl_pods,
)


def parse_output(command: str, raw_output: str) -> Dict[str, Any]:
    """
    Facade wrapper delegating command parsing to infrastructure.parsers.linux_parsers.
    """
    return parse_command_output(command, raw_output)
