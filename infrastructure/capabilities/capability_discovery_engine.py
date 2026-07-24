"""Read-only, registry-driven discovery of host technologies and investigation domains."""

import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from domain.capability import (
    DetectedTechnology, InvestigationCapability, InvestigationDomain,
    ServerCapabilities, TechnologyCategory,
)
from infrastructure.ssh.ssh_interface import ISSHClient
from infrastructure.ssh.paramiko_ssh_client import ParamikoSSHClient
from shared.logging import get_logger

logger = get_logger("CapabilityDiscoveryEngine")


@dataclass(frozen=True)
class TechnologyDefinition:
    name: str
    executable: str
    category: TechnologyCategory


class CapabilityDiscoveryEngine:
    """Executes one allowlisted shell probe and converts it into domain capabilities."""

    _TECHNOLOGIES: List[TechnologyDefinition] = [
        TechnologyDefinition("Docker", "docker", TechnologyCategory.CONTAINER),
        TechnologyDefinition("Docker Compose", "docker-compose", TechnologyCategory.CONTAINER),
        TechnologyDefinition("Podman", "podman", TechnologyCategory.CONTAINER),
        TechnologyDefinition("containerd", "containerd", TechnologyCategory.CONTAINER),
        TechnologyDefinition("kubectl", "kubectl", TechnologyCategory.ORCHESTRATION),
        TechnologyDefinition("kubelet", "kubelet", TechnologyCategory.ORCHESTRATION),
        TechnologyDefinition("k3s", "k3s", TechnologyCategory.ORCHESTRATION),
        TechnologyDefinition("microk8s", "microk8s", TechnologyCategory.ORCHESTRATION),
        TechnologyDefinition("PostgreSQL", "psql", TechnologyCategory.DATABASE),
        TechnologyDefinition("MySQL", "mysql", TechnologyCategory.DATABASE),
        TechnologyDefinition("MariaDB", "mariadb", TechnologyCategory.DATABASE),
        TechnologyDefinition("MongoDB", "mongod", TechnologyCategory.DATABASE),
        TechnologyDefinition("Redis", "redis-server", TechnologyCategory.DATABASE),
        TechnologyDefinition("Nginx", "nginx", TechnologyCategory.WEB_SERVER),
        TechnologyDefinition("Apache", "apache2", TechnologyCategory.WEB_SERVER),
        TechnologyDefinition("Java", "java", TechnologyCategory.RUNTIME),
        TechnologyDefinition("Python", "python3", TechnologyCategory.RUNTIME),
        TechnologyDefinition("NodeJS", "node", TechnologyCategory.RUNTIME),
        TechnologyDefinition("RabbitMQ", "rabbitmqctl", TechnologyCategory.MESSAGE_BROKER),
        TechnologyDefinition("Kafka", "kafka-topics.sh", TechnologyCategory.MESSAGE_BROKER),
        TechnologyDefinition("AWS CLI", "aws", TechnologyCategory.CLOUD_CLI),
        TechnologyDefinition("Azure CLI", "az", TechnologyCategory.CLOUD_CLI),
        TechnologyDefinition("Google Cloud CLI", "gcloud", TechnologyCategory.CLOUD_CLI),
        TechnologyDefinition("systemd", "systemctl", TechnologyCategory.SYSTEM),
        TechnologyDefinition("journalctl", "journalctl", TechnologyCategory.SYSTEM),
        TechnologyDefinition("cron", "crontab", TechnologyCategory.SYSTEM),
        TechnologyDefinition("LVM", "lvs", TechnologyCategory.STORAGE),
        TechnologyDefinition("RAID", "mdadm", TechnologyCategory.STORAGE),
        TechnologyDefinition("NFS tools", "findmnt", TechnologyCategory.STORAGE),
    ]

    def __init__(self, ssh_client: Optional[ISSHClient] = None):
        self._ssh_client = ssh_client or ParamikoSSHClient()

    def discover(self) -> ServerCapabilities:
        """Discover all registered technologies through a single read-only probe."""
        started = time.time()
        logger.info("Capability discovery started")
        result = self._ssh_client.execute_command(self._build_probe_command())
        output = result.get("output", "")
        host = result.get("host", "unknown")
        detected = self._parse_probe_output(output)
        technologies = [
            DetectedTechnology(
                name=definition.name,
                category=definition.category,
                installed=definition.name in detected,
                version=detected.get(definition.name),
                detection_method="allowlisted command availability and version probe",
                confidence=1.0 if definition.name in detected else 0.95,
            )
            for definition in self._TECHNOLOGIES
        ]
        capabilities = ServerCapabilities(
            host=host,
            operating_system=self._field(output, "OS"),
            linux_distribution=self._field(output, "DISTRO"),
            kernel_version=self._field(output, "KERNEL"),
            detected_at=datetime.utcnow(),
            discovery_duration_seconds=round(time.time() - started, 3),
            technologies=technologies,
            investigation_capabilities=self._build_investigation_capabilities(technologies),
        )
        logger.info(
            "Capability discovery complete: host=%s technologies=%s duration=%ss",
            host, sum(technology.installed for technology in technologies), capabilities.discovery_duration_seconds,
        )
        return capabilities

    @classmethod
    def _build_probe_command(cls) -> str:
        executables = " ".join(definition.executable for definition in cls._TECHNOLOGIES)
        return (
            "sh -c '"
            "if [ -r /etc/os-release ]; then . /etc/os-release; printf \"OS|%s\\nDISTRO|%s\\n\" \"${PRETTY_NAME:-Linux}\" \"${ID:-unknown}\"; fi; "
            "printf \"KERNEL|%s\\n\" \"$(uname -r)\"; "
            f"for command_name in {executables}; do "
            "if command -v \"$command_name\" >/dev/null 2>&1; then "
            "version=$(\"$command_name\" --version 2>&1 | head -n 1); "
            "printf \"TECH|%s|%s\\n\" \"$command_name\" \"${version:-installed}\"; fi; "
            "done'"
        )

    @classmethod
    def _parse_probe_output(cls, output: str) -> Dict[str, str]:
        executable_to_name = {item.executable: item.name for item in cls._TECHNOLOGIES}
        detected: Dict[str, str] = {}
        for line in output.splitlines():
            if not line.startswith("TECH|"):
                continue
            _, executable, version = (line.split("|", 2) + ["", ""])[:3]
            name = executable_to_name.get(executable)
            if name:
                detected[name] = version.strip() or "installed"
                logger.info("Technology detected: %s version=%s", name, detected[name])
        return detected

    @staticmethod
    def _field(output: str, name: str) -> Optional[str]:
        match = re.search(rf"^{name}\\|(.+)$", output, re.MULTILINE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _build_investigation_capabilities(technologies: List[DetectedTechnology]) -> List[InvestigationCapability]:
        installed = {technology.name for technology in technologies if technology.installed}
        definitions = [
            (InvestigationDomain.CPU, True, []), (InvestigationDomain.MEMORY, True, []),
            (InvestigationDomain.DISK, True, []), (InvestigationDomain.NETWORK, True, []),
            (InvestigationDomain.SERVICES, "systemd" in installed, ["systemd"]),
            (InvestigationDomain.CONTAINERS, bool({"Docker", "Podman"} & installed), ["Docker or Podman"]),
            (InvestigationDomain.KUBERNETES, bool({"kubectl", "kubelet", "k3s", "microk8s"} & installed), ["kubectl, kubelet, k3s, or microk8s"]),
            (InvestigationDomain.POSTGRESQL, "PostgreSQL" in installed, ["PostgreSQL"]),
            (InvestigationDomain.MYSQL, bool({"MySQL", "MariaDB"} & installed), ["MySQL or MariaDB"]),
            (InvestigationDomain.REDIS, "Redis" in installed, ["Redis"]),
        ]
        return [
            InvestigationCapability(
                domain=domain, supported=supported,
                reason="Supported by detected host capability." if supported else "Required technology was not detected on this server.",
                required_technologies=requirements,
            )
            for domain, supported, requirements in definitions
        ]
