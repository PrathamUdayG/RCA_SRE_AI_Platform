"""
Purpose
-------
Domain schemas representing structured Linux system telemetry using Pydantic.

Responsibilities
----------------
- Define strongly-typed schemas for command execution outputs across all diagnostic categories.
- Enforce data integrity and eliminate raw text string reliance in downstream reasoning engines.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── System & Information Telemetry ────────────────────────────────────

class HostnameTelemetry(BaseModel):
    hostname: str = Field(..., description="Server hostname")


class CurrentUserTelemetry(BaseModel):
    current_user: str = Field(..., description="Logged-in username")


class OSVersionTelemetry(BaseModel):
    os_name: str = Field(default="Unknown", description="Operating system name")
    version_id: str = Field(default="Unknown", description="OS version ID")
    pretty_name: str = Field(default="", description="Human readable OS name")
    raw_release: Dict[str, str] = Field(default_factory=dict, description="Parsed key-value pairs from os-release")


class KernelVersionTelemetry(BaseModel):
    kernel_version: str = Field(..., description="Linux kernel release string")


class ArchitectureTelemetry(BaseModel):
    architecture: str = Field(..., description="Hardware architecture (e.g. x86_64, aarch64)")


class ServerTimeTelemetry(BaseModel):
    server_time: str = Field(..., description="Server system date and time")


class TimezoneTelemetry(BaseModel):
    timezone: str = Field(default="UTC", description="Configured system timezone")
    clock_synchronized: Optional[bool] = Field(default=None, description="NTP synchronization status")


class UptimeTelemetry(BaseModel):
    uptime: str = Field(..., description="Formatted uptime duration")
    users_logged_in: int = Field(default=0, ge=0, description="Count of currently logged in users")
    load_average_1m: float = Field(default=0.0, ge=0.0, description="1-minute system load average")
    load_average_5m: float = Field(default=0.0, ge=0.0, description="5-minute system load average")
    load_average_15m: float = Field(default=0.0, ge=0.0, description="15-minute system load average")


# ── CPU Telemetry ──────────────────────────────────────────────────────

class CPULoadTelemetry(BaseModel):
    load_average_1m: float = Field(default=0.0, ge=0.0)
    load_average_5m: float = Field(default=0.0, ge=0.0)
    load_average_15m: float = Field(default=0.0, ge=0.0)
    runnable_tasks: int = Field(default=0, ge=0)
    total_tasks: int = Field(default=0, ge=0)
    last_pid: int = Field(default=0, ge=0)


class CPUUsageTelemetry(BaseModel):
    user_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    system_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    idle_pct: float = Field(default=100.0, ge=0.0, le=100.0)
    iowait_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    steal_pct: float = Field(default=0.0, ge=0.0, le=100.0)


class CPUInfoTelemetry(BaseModel):
    model_name: str = Field(default="Unknown CPU")
    cpu_cores: int = Field(default=1, ge=1)
    threads_per_core: int = Field(default=1, ge=1)
    sockets: int = Field(default=1, ge=1)
    mhz: float = Field(default=0.0, ge=0.0)


# ── Memory Telemetry ───────────────────────────────────────────────────

class MemoryData(BaseModel):
    total_mb: int = Field(default=0, ge=0)
    used_mb: int = Field(default=0, ge=0)
    free_mb: int = Field(default=0, ge=0)
    shared_mb: int = Field(default=0, ge=0)
    buff_cache_mb: int = Field(default=0, ge=0)
    available_mb: int = Field(default=0, ge=0)


class SwapData(BaseModel):
    total_mb: int = Field(default=0, ge=0)
    used_mb: int = Field(default=0, ge=0)
    free_mb: int = Field(default=0, ge=0)


class MemoryUsageTelemetry(BaseModel):
    memory: MemoryData = Field(default_factory=MemoryData)
    swap: SwapData = Field(default_factory=SwapData)


class MemoryDetailsTelemetry(BaseModel):
    mem_total_kb: int = Field(default=0, ge=0)
    mem_free_kb: int = Field(default=0, ge=0)
    mem_available_kb: int = Field(default=0, ge=0)
    buffers_kb: int = Field(default=0, ge=0)
    cached_kb: int = Field(default=0, ge=0)
    swap_total_kb: int = Field(default=0, ge=0)
    swap_free_kb: int = Field(default=0, ge=0)


# ── Disk Telemetry ─────────────────────────────────────────────────────

class FilesystemUsage(BaseModel):
    filesystem: str
    size: str
    used: str
    available: str
    usage_percent: str
    mounted_on: str


class DiskUsageTelemetry(BaseModel):
    filesystems: List[FilesystemUsage] = Field(default_factory=list)


class InodeUsage(BaseModel):
    filesystem: str
    inodes: str
    iused: str
    ifree: str
    iuse_percent: str
    mounted_on: str


class DiskInodesTelemetry(BaseModel):
    inodes: List[InodeUsage] = Field(default_factory=list)


class BlockDevice(BaseModel):
    name: str
    size: str
    type: str
    mountpoint: Optional[str] = None
    fstype: Optional[str] = None


class BlockDevicesTelemetry(BaseModel):
    devices: List[BlockDevice] = Field(default_factory=list)


class MountEntry(BaseModel):
    device: str
    mountpoint: str
    fstype: str
    options: str


class MountsTelemetry(BaseModel):
    mounts: List[MountEntry] = Field(default_factory=list)


# ── Network Telemetry ──────────────────────────────────────────────────

class IPInterface(BaseModel):
    name: str
    flags: List[str] = Field(default_factory=list)
    state: str = Field(default="UNKNOWN")
    mac: Optional[str] = None
    ip_addresses: List[str] = Field(default_factory=list)


class IPAddressTelemetry(BaseModel):
    interfaces: List[IPInterface] = Field(default_factory=list)


class RouteEntry(BaseModel):
    destination: str
    gateway: str
    genmask: Optional[str] = None
    flags: str = Field(default="")
    metric: int = Field(default=0)
    iface: str = Field(default="")


class RoutingTableTelemetry(BaseModel):
    routes: List[RouteEntry] = Field(default_factory=list)


class ListeningPort(BaseModel):
    protocol: str
    receive_q: int = Field(default=0)
    send_q: int = Field(default=0)
    local_address: str
    local_port: int
    peer_address: str = Field(default="*")
    peer_port: str = Field(default="*")
    process: Optional[str] = None


class ListeningPortsTelemetry(BaseModel):
    ports: List[ListeningPort] = Field(default_factory=list)


class NetworkStatisticsTelemetry(BaseModel):
    total_sockets: int = Field(default=0)
    tcp_sockets: int = Field(default=0)
    udp_sockets: int = Field(default=0)
    summary: Dict[str, Any] = Field(default_factory=dict)


class DNSConfigurationTelemetry(BaseModel):
    nameservers: List[str] = Field(default_factory=list)
    search_domains: List[str] = Field(default_factory=list)
    options: List[str] = Field(default_factory=list)


# ── Process & Service Telemetry ───────────────────────────────────────

class TopProcessEntry(BaseModel):
    pid: int
    command: str
    usage_value: float = Field(..., description="CPU % or Memory %")


class TopProcessesTelemetry(BaseModel):
    processes: List[TopProcessEntry] = Field(default_factory=list)


class ProcessEntry(BaseModel):
    user: str
    pid: int
    cpu_pct: float
    mem_pct: float
    vsz: int
    rss: int
    tty: str
    stat: str
    start: str
    time: str
    command: str


class ProcessListTelemetry(BaseModel):
    total_processes: int = Field(default=0)
    processes: List[ProcessEntry] = Field(default_factory=list)


class SystemdService(BaseModel):
    unit: str
    load: str
    active: str
    sub: str
    description: str


class RunningServicesTelemetry(BaseModel):
    services: List[SystemdService] = Field(default_factory=list)


class FailedServicesTelemetry(BaseModel):
    failed_services: List[SystemdService] = Field(default_factory=list)
    total_failed: int = Field(default=0)


# ── Container & Kubernetes Telemetry ──────────────────────────────────

class DockerContainer(BaseModel):
    container_id: str
    image: str
    command: str
    created: str
    status: str
    ports: str
    names: str


class DockerContainersTelemetry(BaseModel):
    containers: List[DockerContainer] = Field(default_factory=list)
    total_containers: int = Field(default=0)
    running_count: int = Field(default=0)
    exited_count: int = Field(default=0)


class K8sPod(BaseModel):
    namespace: str
    name: str
    ready: str
    status: str
    restarts: int
    age: str


class K8sPodsTelemetry(BaseModel):
    pods: List[K8sPod] = Field(default_factory=list)
    total_pods: int = Field(default=0)
    unhealthy_pods: List[K8sPod] = Field(default_factory=list)


class UserSession(BaseModel):
    username: str
    tty: str
    from_host: str
    login_time: str
    idle_time: Optional[str] = None
    what: Optional[str] = None


class LoggedInUsersTelemetry(BaseModel):
    sessions: List[UserSession] = Field(default_factory=list)
