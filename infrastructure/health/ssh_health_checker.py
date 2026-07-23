"""
Purpose
-------
SSH Server health checker for the AI SRE Platform.

Responsibilities
----------------
- Establish a lightweight Paramiko SSH connection to the configured target server.
- Execute minimal diagnostic commands (hostname, hostname -I) to verify connectivity.
- Measure round-trip connection latency.
- Return a structured ComponentHealthResult with connection metadata.

Does NOT
---------
- Execute investigation commands or modify remote server state.
- Implement business logic or domain rules.
"""

import time
from datetime import datetime
from typing import Optional

import paramiko

from domain.health.models import ComponentHealthResult, ComponentStatus
from shared.config import get_settings
from shared.logging import get_logger

logger = get_logger("SSHHealthChecker")


class SSHHealthChecker:
    """
    Infrastructure health checker that probes SSH server connectivity.

    Uses Paramiko to establish a test connection and collect server metadata
    (hostname, IP address, authentication status, round-trip latency).

    Parameters
    ----------
    host : Optional[str]
        SSH server hostname. Defaults to platform settings.
    port : Optional[int]
        SSH server port. Defaults to platform settings.
    username : Optional[str]
        SSH username. Defaults to platform settings.
    password : Optional[str]
        SSH password. Defaults to platform settings.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        settings = get_settings()
        self._host = host or settings.ssh.host
        self._port = port or settings.ssh.port
        self._username = username or settings.ssh.username
        self._password = password or settings.ssh.password

    def check(self) -> ComponentHealthResult:
        """
        Performs a lightweight SSH connectivity health check.

        Returns
        -------
        ComponentHealthResult
            Health result containing connection metadata or error details.
        """
        checked_at = datetime.utcnow()
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        start_time = time.time()
        try:
            client.connect(
                hostname=self._host,
                port=self._port,
                username=self._username,
                password=self._password,
                timeout=10,
            )
            connection_time_ms = round((time.time() - start_time) * 1000, 2)

            # Collect server hostname
            _, stdout_host, _ = client.exec_command("hostname")
            server_hostname = stdout_host.read().decode().strip()

            # Collect server IP address
            _, stdout_ip, _ = client.exec_command("hostname -I")
            server_ip = stdout_ip.read().decode().strip().split()[0] if stdout_ip else "N/A"

            # Measure round-trip latency with a trivial command
            rtt_start = time.time()
            _, stdout_echo, _ = client.exec_command("echo ok")
            stdout_echo.read()
            rtt_ms = round((time.time() - rtt_start) * 1000, 2)

            client.close()

            logger.info(f"SSH health check passed: {self._host}:{self._port} ({connection_time_ms}ms)")

            return ComponentHealthResult(
                component_name="SSH Server",
                status=ComponentStatus.HEALTHY,
                details={
                    "hostname": server_hostname,
                    "ip_address": server_ip,
                    "connection_target": f"{self._host}:{self._port}",
                    "connection_time_ms": connection_time_ms,
                    "authentication_status": "Authenticated",
                    "round_trip_time_ms": rtt_ms,
                },
                checked_at=checked_at,
                latency_ms=connection_time_ms,
            )

        except Exception as exc:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            error_msg = f"Unable to connect to SSH server at {self._host}:{self._port} — {type(exc).__name__}: {exc}"
            logger.warning(f"SSH health check failed: {error_msg}")

            try:
                client.close()
            except Exception:
                pass

            return ComponentHealthResult(
                component_name="SSH Server",
                status=ComponentStatus.UNHEALTHY,
                details={
                    "connection_target": f"{self._host}:{self._port}",
                    "authentication_status": "Failed",
                },
                error_message=error_msg,
                recommendation=(
                    "Verify that the SSH server is running and reachable. "
                    "Check SSH_HOST, SSH_PORT, SSH_USERNAME, and SSH_PASSWORD in your .env file."
                ),
                checked_at=checked_at,
                latency_ms=elapsed_ms,
            )
