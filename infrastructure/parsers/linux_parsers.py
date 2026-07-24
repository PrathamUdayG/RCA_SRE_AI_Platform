"""
Purpose
-------
Deterministic Linux stdout text parsers for all 47+ read-only diagnostic commands.

Responsibilities
----------------
- Parse raw terminal stdout text returned over SSH into structured JSON dictionaries matching domain telemetry schemas.
- Guarantee 100% deterministic outputs with graceful fallback parsing.
- Provide comprehensive parser mapping for every whitelisted Linux command.
"""

import re
from typing import Any, Dict, List


def parse_hostname(raw_output: str) -> Dict[str, Any]:
    return {"hostname": raw_output.strip()}


def parse_whoami(raw_output: str) -> Dict[str, Any]:
    return {"current_user": raw_output.strip()}


def parse_os_version(raw_output: str) -> Dict[str, Any]:
    raw_release = {}
    os_name = "Unknown"
    version_id = "Unknown"
    pretty_name = ""

    for line in raw_output.strip().splitlines():
        if "=" in line:
            key, val = line.strip().split("=", 1)
            val = val.strip('"\'')
            raw_release[key] = val
            if key == "NAME":
                os_name = val
            elif key == "VERSION_ID":
                version_id = val
            elif key == "PRETTY_NAME":
                pretty_name = val

    return {
        "os_name": os_name,
        "version_id": version_id,
        "pretty_name": pretty_name or os_name,
        "raw_release": raw_release,
    }


def parse_kernel_version(raw_output: str) -> Dict[str, Any]:
    return {"kernel_version": raw_output.strip()}


def parse_architecture(raw_output: str) -> Dict[str, Any]:
    return {"architecture": raw_output.strip()}


def parse_uname_a(raw_output: str) -> Dict[str, Any]:
    parts = raw_output.strip().split()
    return {
        "kernel_name": parts[0] if len(parts) > 0 else "",
        "nodename": parts[1] if len(parts) > 1 else "",
        "kernel_release": parts[2] if len(parts) > 2 else "",
        "kernel_version": " ".join(parts[3:-2]) if len(parts) > 5 else "",
        "machine": parts[-2] if len(parts) > 2 else "",
        "processor": parts[-1] if len(parts) > 1 else "",
        "raw_uname": raw_output.strip(),
    }


def parse_server_time(raw_output: str) -> Dict[str, Any]:
    return {"server_time": raw_output.strip()}


def parse_timedatectl(raw_output: str) -> Dict[str, Any]:
    result = {"raw_output": raw_output.strip(), "timezone": "UTC", "clock_synchronized": False}
    for line in raw_output.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip().lower()
            v = v.strip()
            if "time zone" in k:
                result["timezone"] = v.split()[0] if v else "UTC"
            elif "system clock synchronized" in k or "ntp service" in k:
                result["clock_synchronized"] = "yes" in v.lower() or "active" in v.lower()
    return result


def parse_uptime(raw_output: str) -> Dict[str, Any]:
    output = raw_output.strip()
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


def parse_lscpu(raw_output: str) -> Dict[str, Any]:
    info = {}
    for line in raw_output.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()

    return {
        "model_name": info.get("Model name", "Unknown CPU"),
        "cpu_cores": int(info.get("CPU(s)", 1)),
        "threads_per_core": int(info.get("Thread(s) per core", 1)),
        "sockets": int(info.get("Socket(s)", 1)),
        "mhz": float(info.get("CPU MHz", 0.0)) if info.get("CPU MHz") else 0.0,
        "raw_lscpu": info,
    }


def parse_top_cpu(raw_output: str) -> Dict[str, Any]:
    user_pct = 0.0
    sys_pct = 0.0
    idle_pct = 100.0
    iowait_pct = 0.0

    match = re.search(r"%Cpu\(s\):\s*([\d\.]+)\s*us,\s*([\d\.]+)\s*sy,.*?([\d\.]+)\s*id,\s*([\d\.]+)\s*wa", raw_output)
    if match:
        user_pct = float(match.group(1))
        sys_pct = float(match.group(2))
        idle_pct = float(match.group(3))
        iowait_pct = float(match.group(4))

    return {
        "user_pct": user_pct,
        "system_pct": sys_pct,
        "idle_pct": idle_pct,
        "iowait_pct": iowait_pct,
        "steal_pct": 0.0,
    }


def parse_cpu_load(raw_output: str) -> Dict[str, Any]:
    parts = raw_output.strip().split()
    load_1m = float(parts[0]) if len(parts) > 0 else 0.0
    load_5m = float(parts[1]) if len(parts) > 1 else 0.0
    load_15m = float(parts[2]) if len(parts) > 2 else 0.0

    runnable_tasks = 0
    total_tasks = 0
    if len(parts) > 3 and "/" in parts[3]:
        r, t = parts[3].split("/", 1)
        runnable_tasks = int(r)
        total_tasks = int(t)

    last_pid = int(parts[4]) if len(parts) > 4 else 0

    return {
        "load_average_1m": load_1m,
        "load_average_5m": load_5m,
        "load_average_15m": load_15m,
        "runnable_tasks": runnable_tasks,
        "total_tasks": total_tasks,
        "last_pid": last_pid,
    }


def parse_free_m(raw_output: str) -> Dict[str, Any]:
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


def parse_proc_meminfo(raw_output: str) -> Dict[str, Any]:
    data = {}
    for line in raw_output.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v_val = v.strip().split()[0]
            if v_val.isdigit():
                data[k.strip()] = int(v_val)

    return {
        "mem_total_kb": data.get("MemTotal", 0),
        "mem_free_kb": data.get("MemFree", 0),
        "mem_available_kb": data.get("MemAvailable", 0),
        "buffers_kb": data.get("Buffers", 0),
        "cached_kb": data.get("Cached", 0),
        "swap_total_kb": data.get("SwapTotal", 0),
        "swap_free_kb": data.get("SwapFree", 0),
    }


def parse_df_h(raw_output: str) -> Dict[str, Any]:
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


def parse_df_i(raw_output: str) -> Dict[str, Any]:
    inodes = []
    lines = raw_output.strip().splitlines()

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or cleaned_line.startswith("Filesystem"):
            continue

        parts = cleaned_line.split(maxsplit=5)
        if len(parts) >= 6:
            inodes.append({
                "filesystem": parts[0],
                "inodes": parts[1],
                "iused": parts[2],
                "ifree": parts[3],
                "iuse_percent": parts[4],
                "mounted_on": parts[5],
            })

    return {"inodes": inodes}


def parse_lsblk(raw_output: str) -> Dict[str, Any]:
    devices = []
    lines = raw_output.strip().splitlines()
    if not lines:
        return {"devices": devices}

    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) >= 4:
            devices.append({
                "name": parts[0].replace("└─", "").replace("├─", ""),
                "size": parts[3] if len(parts) > 3 else "0",
                "type": parts[5] if len(parts) > 5 else "disk",
                "mountpoint": parts[6] if len(parts) > 6 else None,
            })

    return {"devices": devices}


def parse_mount(raw_output: str) -> Dict[str, Any]:
    mounts = []
    for line in raw_output.strip().splitlines():
        match = re.match(r"(\S+)\s+on\s+(\S+)\s+type\s+(\S+)\s+\((.*?)\)", line)
        if match:
            mounts.append({
                "device": match.group(1),
                "mountpoint": match.group(2),
                "fstype": match.group(3),
                "options": match.group(4),
            })
    return {"mounts": mounts}


def parse_ip_addr(raw_output: str) -> Dict[str, Any]:
    interfaces = []
    current_iface = None

    for line in raw_output.strip().splitlines():
        if line and line[0].isdigit():
            parts = line.split(":", 2)
            if len(parts) >= 2:
                if current_iface:
                    interfaces.append(current_iface)
                iface_name = parts[1].strip()
                flags = re.findall(r"<([^>]+)>", line)
                flag_list = flags[0].split(",") if flags else []
                state_match = re.search(r"state\s+(\S+)", line)
                state = state_match.group(1) if state_match else "UNKNOWN"
                current_iface = {
                    "name": iface_name,
                    "flags": flag_list,
                    "state": state,
                    "mac": None,
                    "ip_addresses": [],
                }
        elif current_iface:
            if "inet " in line or "inet6 " in line:
                ip_match = re.search(r"inet6?\s+(\S+)", line)
                if ip_match:
                    current_iface["ip_addresses"].append(ip_match.group(1))
            elif "link/ether" in line:
                mac_match = re.search(r"link/ether\s+(\S+)", line)
                if mac_match:
                    current_iface["mac"] = mac_match.group(1)

    if current_iface:
        interfaces.append(current_iface)

    return {"interfaces": interfaces}


def parse_ip_route(raw_output: str) -> Dict[str, Any]:
    routes = []
    for line in raw_output.strip().splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        dest = parts[0]
        gw = "0.0.0.0"
        if "via" in parts:
            gw_idx = parts.index("via")
            if len(parts) > gw_idx + 1:
                gw = parts[gw_idx + 1]
        iface = ""
        if "dev" in parts:
            dev_idx = parts.index("dev")
            if len(parts) > dev_idx + 1:
                iface = parts[dev_idx + 1]
        routes.append({
            "destination": dest,
            "gateway": gw,
            "genmask": None,
            "flags": "",
            "metric": 0,
            "iface": iface,
        })
    return {"routes": routes}


def parse_ip_link(raw_output: str) -> Dict[str, Any]:
    return parse_ip_addr(raw_output)


def parse_resolv_conf(raw_output: str) -> Dict[str, Any]:
    nameservers = []
    search = []
    options = []
    for line in raw_output.strip().splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        parts = line.split()
        if parts[0] == "nameserver" and len(parts) > 1:
            nameservers.append(parts[1])
        elif parts[0] == "search":
            search.extend(parts[1:])
        elif parts[0] == "options":
            options.extend(parts[1:])
    return {
        "nameservers": nameservers,
        "search_domains": search,
        "options": options,
    }


def parse_ss_tuln(raw_output: str) -> Dict[str, Any]:
    ports = []
    lines = raw_output.strip().splitlines()
    for line in lines:
        if line.startswith("Netid") or line.startswith("State") or not line.strip():
            continue
        parts = line.strip().split()
        if len(parts) >= 5:
            proto = parts[0]
            rq = int(parts[1]) if parts[1].isdigit() else 0
            sq = int(parts[2]) if parts[2].isdigit() else 0
            local = parts[3]
            peer = parts[4]

            local_addr = local
            local_port = 0
            if ":" in local:
                local_addr, port_str = local.rsplit(":", 1)
                local_port = int(port_str) if port_str.isdigit() else 0

            ports.append({
                "protocol": proto,
                "receive_q": rq,
                "send_q": sq,
                "local_address": local_addr,
                "local_port": local_port,
                "peer_address": peer,
                "peer_port": "*",
                "process": parts[5] if len(parts) > 5 else None,
            })
    return {"ports": ports}


def parse_ss_s(raw_output: str) -> Dict[str, Any]:
    summary = {}
    total_sockets = 0
    tcp_sockets = 0
    udp_sockets = 0

    for line in raw_output.strip().splitlines():
        if "Total:" in line:
            match = re.search(r"Total:\s*(\d+)", line)
            if match:
                total_sockets = int(match.group(1))
        elif "TCP:" in line:
            match = re.search(r"TCP:\s*(\d+)", line)
            if match:
                tcp_sockets = int(match.group(1))
        elif "UDP:" in line:
            match = re.search(r"UDP:\s*(\d+)", line)
            if match:
                udp_sockets = int(match.group(1))
        summary[line.split(":")[0].strip()] = line.split(":", 1)[1].strip() if ":" in line else line

    return {
        "total_sockets": total_sockets,
        "tcp_sockets": tcp_sockets,
        "udp_sockets": udp_sockets,
        "summary": summary,
    }


def parse_ps_aux(raw_output: str) -> Dict[str, Any]:
    processes = []
    lines = raw_output.strip().splitlines()
    for line in lines:
        if line.startswith("USER") or not line.strip():
            continue
        parts = line.strip().split(maxsplit=10)
        if len(parts) >= 11:
            try:
                processes.append({
                    "user": parts[0],
                    "pid": int(parts[1]),
                    "cpu_pct": float(parts[2]),
                    "mem_pct": float(parts[3]),
                    "vsz": int(parts[4]),
                    "rss": int(parts[5]),
                    "tty": parts[6],
                    "stat": parts[7],
                    "start": parts[8],
                    "time": parts[9],
                    "command": parts[10],
                })
            except ValueError:
                continue

    return {
        "total_processes": len(processes),
        "processes": processes,
    }


def parse_pstree(raw_output: str) -> Dict[str, Any]:
    return {
        "raw_tree": raw_output.strip(),
        "process_count": len(raw_output.strip().splitlines()),
    }


def parse_top_cpu_processes(raw_output: str) -> Dict[str, Any]:
    processes = []
    lines = raw_output.strip().splitlines()
    for line in lines:
        if "PID" in line or not line.strip():
            continue
        parts = line.strip().split()
        if len(parts) >= 3:
            try:
                processes.append({
                    "pid": int(parts[0]),
                    "command": parts[1],
                    "usage_value": float(parts[2]),
                })
            except ValueError:
                continue
    return {"processes": processes}


def parse_top_memory_processes(raw_output: str) -> Dict[str, Any]:
    return parse_top_cpu_processes(raw_output)


def parse_running_services(raw_output: str) -> Dict[str, Any]:
    services = []
    lines = raw_output.strip().splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("UNIT") or "loaded units listed" in line_clean:
            continue
        parts = line_clean.split(maxsplit=4)
        if len(parts) >= 5:
            services.append({
                "unit": parts[0],
                "load": parts[1],
                "active": parts[2],
                "sub": parts[3],
                "description": parts[4],
            })
    return {"services": services}


def parse_failed_services(raw_output: str) -> Dict[str, Any]:
    services = []
    lines = raw_output.strip().splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("UNIT") or "loaded units listed" in line_clean:
            continue
        parts = line_clean.split(maxsplit=4)
        if len(parts) >= 5 and parts[2] == "failed":
            services.append({
                "unit": parts[0],
                "load": parts[1],
                "active": parts[2],
                "sub": parts[3],
                "description": parts[4],
            })
    return {
        "failed_services": services,
        "total_failed": len(services),
    }


def parse_who(raw_output: str) -> Dict[str, Any]:
    sessions = []
    for line in raw_output.strip().splitlines():
        parts = line.strip().split()
        if len(parts) >= 3:
            sessions.append({
                "username": parts[0],
                "tty": parts[1],
                "login_time": " ".join(parts[2:]),
                "from_host": parts[2] if len(parts) > 2 else "local",
            })
    return {"sessions": sessions}


def parse_last(raw_output: str) -> Dict[str, Any]:
    entries = []
    for line in raw_output.strip().splitlines()[:20]:
        parts = line.strip().split()
        if len(parts) >= 4 and not line.startswith("wtmp begins"):
            entries.append({
                "user": parts[0],
                "tty": parts[1],
                "host": parts[2],
                "timestamp": " ".join(parts[3:]),
            })
    return {"login_history": entries}


def parse_pwd(raw_output: str) -> Dict[str, Any]:
    return {"current_directory": raw_output.strip()}


def parse_lsblk_f(raw_output: str) -> Dict[str, Any]:
    return parse_lsblk(raw_output)


def parse_printenv(raw_output: str) -> Dict[str, Any]:
    env_vars = {}
    for line in raw_output.strip().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env_vars[k.strip()] = v.strip()
    return {"environment": env_vars}


def parse_path(raw_output: str) -> Dict[str, Any]:
    return {"path": raw_output.strip().split(":")}


def parse_docker_ps(raw_output: str) -> Dict[str, Any]:
    containers = []
    lines = raw_output.strip().splitlines()
    if not lines:
        return {"containers": containers, "total_containers": 0, "running_count": 0, "exited_count": 0}

    for line in lines[1:]:
        parts = line.strip().split(maxsplit=6)
        if len(parts) >= 7:
            status = parts[4]
            containers.append({
                "container_id": parts[0],
                "image": parts[1],
                "command": parts[2],
                "created": parts[3],
                "status": status,
                "ports": parts[5],
                "names": parts[6],
            })

    running = sum(1 for c in containers if "Up" in c["status"])
    exited = sum(1 for c in containers if "Exited" in c["status"])

    return {
        "containers": containers,
        "total_containers": len(containers),
        "running_count": running,
        "exited_count": exited,
    }


def parse_docker_images(raw_output: str) -> Dict[str, Any]:
    images = []
    lines = raw_output.strip().splitlines()
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) >= 3:
            images.append({
                "repository": parts[0],
                "tag": parts[1],
                "image_id": parts[2],
                "size": parts[-1],
            })
    return {"images": images}


def parse_docker_info(raw_output: str) -> Dict[str, Any]:
    info = {}
    for line in raw_output.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()
    return {"docker_info": info}


def parse_history(raw_output: str) -> Dict[str, Any]:
    return {"last_command": raw_output.strip()}


def parse_jobs(raw_output: str) -> Dict[str, Any]:
    return {"jobs": raw_output.strip().splitlines()}


def parse_lastlog(raw_output: str) -> Dict[str, Any]:
    lines = raw_output.strip().splitlines()
    return {"lastlog": lines[-1] if lines else "No login record."}


def parse_kubectl_nodes(raw_output: str) -> Dict[str, Any]:
    nodes = []
    lines = raw_output.strip().splitlines()
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) >= 5:
            nodes.append({
                "name": parts[0],
                "status": parts[1],
                "roles": parts[2],
                "age": parts[3],
                "version": parts[4],
            })
    return {"nodes": nodes}


def parse_kubectl_pods(raw_output: str) -> Dict[str, Any]:
    pods = []
    unhealthy = []
    lines = raw_output.strip().splitlines()
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) >= 6:
            pod_data = {
                "namespace": parts[0],
                "name": parts[1],
                "ready": parts[2],
                "status": parts[3],
                "restarts": int(parts[4]) if parts[4].isdigit() else 0,
                "age": parts[5],
            }
            pods.append(pod_data)
            if parts[3].lower() not in ("running", "completed"):
                unhealthy.append(pod_data)
    return {
        "pods": pods,
        "total_pods": len(pods),
        "unhealthy_pods": unhealthy,
    }


def parse_kubectl_services(raw_output: str) -> Dict[str, Any]:
    services = []
    lines = raw_output.strip().splitlines()
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) >= 6:
            services.append({
                "namespace": parts[0],
                "name": parts[1],
                "type": parts[2],
                "cluster_ip": parts[3],
                "external_ip": parts[4],
                "ports": parts[5],
                "age": parts[6] if len(parts) > 6 else "",
            })
    return {"services": services}


def parse_w(raw_output: str) -> Dict[str, Any]:
    return parse_who(raw_output)


def parse_sudo_version(raw_output: str) -> Dict[str, Any]:
    lines = raw_output.strip().splitlines()
    version = lines[0] if lines else "Unknown Sudo Version"
    return {"sudo_version": version}


# ───────────────────────────────────────────────────────────────────────
# Master Command -> Parser Resolution Map
# ───────────────────────────────────────────────────────────────────────

COMMAND_PARSER_MAP: Dict[str, Any] = {
    # System Information
    "hostname": parse_hostname,
    "current_user": parse_whoami,
    "os_version": parse_os_version,
    "kernel_version": parse_kernel_version,
    "system_architecture": parse_architecture,
    "system_information": parse_uname_a,
    "server_time": parse_server_time,
    "server_timezone": parse_timedatectl,
    "uptime": parse_uptime,
    # CPU
    "cpu_information": parse_lscpu,
    "cpu_usage": parse_top_cpu,
    "cpu_load": parse_cpu_load,
    # Memory
    "memory_usage": parse_free_m,
    "memory_details": parse_proc_meminfo,
    # Disk
    "disk_usage": parse_df_h,
    "disk_inodes": parse_df_i,
    "block_devices": parse_lsblk,
    "mounted_filesystems": parse_mount,
    # Network
    "ip_address": parse_ip_addr,
    "routing_table": parse_ip_route,
    "network_interfaces": parse_ip_link,
    "dns_configuration": parse_resolv_conf,
    "listening_ports": parse_ss_tuln,
    "network_statistics": parse_ss_s,
    # Processes & Services
    "running_processes": parse_ps_aux,
    "process_tree": parse_pstree,
    "top_cpu_processes": parse_top_cpu_processes,
    "top_memory_processes": parse_top_memory_processes,
    "running_services": parse_running_services,
    "failed_services": parse_failed_services,
    # Logged-in Users & Environment
    "logged_in_users": parse_who,
    "user_login_history": parse_last,
    "current_directory": parse_pwd,
    "disk_partitions": parse_lsblk_f,
    "environment_variables": parse_printenv,
    "path_variable": parse_path,
    # Docker
    "docker_containers": parse_docker_ps,
    "docker_images": parse_docker_images,
    "docker_system_info": parse_docker_info,
    # History & Jobs
    "last_command": parse_history,
    "background_jobs": parse_jobs,
    "last_login": parse_lastlog,
    # Kubernetes
    "kubectl_nodes": parse_kubectl_nodes,
    "kubectl_pods": parse_kubectl_pods,
    "kubectl_services": parse_kubectl_services,
    # Security
    "logged_in_sessions": parse_w,
    "sudo_version": parse_sudo_version,
}

# Raw Command String Fallback Map
RAW_COMMAND_PARSER_MAP: Dict[str, Any] = {
    "hostname": parse_hostname,
    "whoami": parse_whoami,
    "cat /etc/os-release": parse_os_version,
    "uname -r": parse_kernel_version,
    "uname -m": parse_architecture,
    "uname -a": parse_uname_a,
    "date": parse_server_time,
    "timedatectl": parse_timedatectl,
    "uptime": parse_uptime,
    "lscpu": parse_lscpu,
    "top -bn1": parse_top_cpu,
    "cat /proc/loadavg": parse_cpu_load,
    "free -m": parse_free_m,
    "cat /proc/meminfo": parse_proc_meminfo,
    "df -h": parse_df_h,
    "df -i": parse_df_i,
    "lsblk": parse_lsblk,
    "mount": parse_mount,
    "ip addr": parse_ip_addr,
    "ip route": parse_ip_route,
    "ip link": parse_ip_link,
    "cat /etc/resolv.conf": parse_resolv_conf,
    "ss -tuln": parse_ss_tuln,
    "ss -s": parse_ss_s,
    "ps aux": parse_ps_aux,
    "pstree": parse_pstree,
    "ps -eo pid,comm,%cpu --sort=-%cpu | head": parse_top_cpu_processes,
    "ps -eo pid,comm,%mem --sort=-%mem | head": parse_top_memory_processes,
    "systemctl list-units --type=service --state=running": parse_running_services,
    "systemctl --failed": parse_failed_services,
    "who": parse_who,
    "last": parse_last,
    "pwd": parse_pwd,
    "lsblk -f": parse_lsblk_f,
    "printenv": parse_printenv,
    "echo $PATH": parse_path,
    "docker ps -a": parse_docker_ps,
    "docker images": parse_docker_images,
    "docker info": parse_docker_info,
    "history 1": parse_history,
    "jobs": parse_jobs,
    "lastlog -u $(whoami)": parse_lastlog,
    "kubectl get nodes": parse_kubectl_nodes,
    "kubectl get pods -A": parse_kubectl_pods,
    "kubectl get svc -A": parse_kubectl_services,
    "w": parse_w,
    "sudo -V": parse_sudo_version,
}


def parse_command_output(command_identifier: str, raw_output: str) -> Dict[str, Any]:
    """
    Parses raw stdout text using command key or raw Linux command string.
    Guarantees structured dictionary payload.
    """
    cmd_key = command_identifier.strip()
    parser = COMMAND_PARSER_MAP.get(cmd_key) or RAW_COMMAND_PARSER_MAP.get(cmd_key)

    if parser is None:
        return {"raw_output": raw_output.strip()}

    try:
        parsed = parser(raw_output)
        if isinstance(parsed, dict):
            return parsed
        return {"parsed_result": parsed}
    except Exception as err:
        return {
            "raw_output": raw_output.strip(),
            "parse_error": str(err),
        }
