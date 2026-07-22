# parsers.py

"""
Parser module for converting raw Linux command output strings into structured
Python dictionaries (JSON-serializable).
"""

import re
from typing import Any, Dict, List


def parse_hostname(raw_output: str) -> Dict[str, str]:
    """Parse output of 'hostname' command."""
    return {"hostname": raw_output.strip()}


def parse_whoami(raw_output: str) -> Dict[str, str]:
    """Parse output of 'whoami' command."""
    return {"current_user": raw_output.strip()}


def parse_uptime(raw_output: str) -> Dict[str, Any]:
    """
    Parse output of 'uptime' command.

    Example input:
    04:53:33 up 29 days, 18:41, 1 user, load average: 0.07, 0.07, 0.08
    """
    output = raw_output.strip()

    # Extract uptime and user count using regex
    uptime_match = re.search(r"up\s+(.*?),\s*(\d+)\s+users?,", output)
    load_match = re.search(r"load average:\s*([\d\.]+),\s*([\d\.]+),\s*([\d\.]+)", output)

    uptime_val = uptime_match.group(1).strip() if uptime_match else output
    users_val = int(uptime_match.group(2)) if uptime_match else 0

    load_1m = float(load_match.group(1)) if load_match else 0.0
    load_5m = float(load_match.group(2)) if load_match else 0.0
    load_15m = float(load_match.group(3)) if load_match else 0.0

    return {
        "uptime": uptime_val,
        "users_logged_in": users_val,
        "load_average_1m": load_1m,
        "load_average_5m": load_5m,
        "load_average_15m": load_15m,
    }


def parse_free_m(raw_output: str) -> Dict[str, Any]:
    """
    Parse output of 'free -m' command.

    Example input:
                   total        used        free      shared  buff/cache   available
    Mem:            7940        2807         394         110        5156        5133
    Swap:           2047           0        2047
    """
    mem_match = re.search(r"Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", raw_output)
    swap_match = re.search(r"Swap:\s+(\d+)\s+(\d+)\s+(\d+)", raw_output)

    memory_data = {
        "total_mb": int(mem_match.group(1)) if mem_match else 0,
        "used_mb": int(mem_match.group(2)) if mem_match else 0,
        "free_mb": int(mem_match.group(3)) if mem_match else 0,
        "shared_mb": int(mem_match.group(4)) if mem_match else 0,
        "buff_cache_mb": int(mem_match.group(5)) if mem_match else 0,
        "available_mb": int(mem_match.group(6)) if mem_match else 0,
    }

    swap_data = {
        "total_mb": int(swap_match.group(1)) if swap_match else 0,
        "used_mb": int(swap_match.group(2)) if swap_match else 0,
        "free_mb": int(swap_match.group(3)) if swap_match else 0,
    }

    return {
        "memory": memory_data,
        "swap": swap_data,
    }


def parse_df_h(raw_output: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Parse output of 'df -h' command.

    Example input:
    Filesystem      Size  Used Avail Use% Mounted on
    tmpfs           795M  2.4M  792M   1% /run
    /dev/sda1        96G   41G   56G  43% /
    """
    filesystems = []
    lines = raw_output.strip().splitlines()

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or cleaned_line.startswith("Filesystem"):
            continue

        parts = cleaned_line.split(maxsplit=5)
        if len(parts) >= 6:
            filesystems.append({
                "filesystem": parts[0],
                "size": parts[1],
                "used": parts[2],
                "available": parts[3],
                "usage_percent": parts[4],
                "mounted_on": parts[5],
            })

    return {"filesystems": filesystems}


# Dispatcher map connecting command strings to parser functions
PARSERS = {
    "hostname": parse_hostname,
    "whoami": parse_whoami,
    "uptime": parse_uptime,
    "free -m": parse_free_m,
    "df -h": parse_df_h,
}


def parse_output(command: str, raw_output: str) -> Dict[str, Any]:
    """
    Automatically selects and runs the correct parser based on command.
    Returns a fallback dictionary containing raw_output if no parser exists.
    """
    cmd_key = command.strip()
    parser = PARSERS.get(cmd_key)

    if parser is None:
        return {"raw_output": raw_output}

    try:
        return parser(raw_output)
    except Exception:
        return {"raw_output": raw_output}
