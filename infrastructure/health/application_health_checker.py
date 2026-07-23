"""
Purpose
-------
Application self-health checker for the AI SRE Platform.

Responsibilities
----------------
- Report application runtime metadata: version, Python version, environment, startup time, uptime.
- Always return HEALTHY status (if this code executes, the application is running).

Does NOT
---------
- Perform any external infrastructure calls.
- Implement business logic or domain rules.
"""

import sys
import time
from datetime import datetime
from typing import Optional

from domain.health.models import ComponentHealthResult, ComponentStatus
from shared.logging import get_logger

logger = get_logger("ApplicationHealthChecker")

# Module-level startup timestamp — captured once when the module is first imported.
_APPLICATION_STARTUP_TIME: datetime = datetime.utcnow()
_APPLICATION_STARTUP_MONOTONIC: float = time.monotonic()

APPLICATION_VERSION = "1.0.0"


class ApplicationHealthChecker:
    """
    Infrastructure health checker that reports application self-health metadata.

    This checker always returns HEALTHY status because if this code is executing,
    the application process is alive. Its primary purpose is to surface runtime
    metadata (version, Python version, startup time, uptime).

    Parameters
    ----------
    version : Optional[str]
        Application version string. Defaults to "1.0.0".
    environment : Optional[str]
        Runtime environment name. Defaults to "production".
    """

    def __init__(
        self,
        version: Optional[str] = None,
        environment: Optional[str] = None,
    ):
        self._version = version or APPLICATION_VERSION
        self._environment = environment or "production"

    def check(self) -> ComponentHealthResult:
        """
        Reports application runtime health and metadata.

        Returns
        -------
        ComponentHealthResult
            Health result containing application version, Python version,
            environment, startup time, and uptime.
        """
        checked_at = datetime.utcnow()
        uptime_seconds = round(time.monotonic() - _APPLICATION_STARTUP_MONOTONIC, 2)

        # Format uptime as human-readable string
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_display = f"{hours}h {minutes}m {seconds}s"

        logger.info(f"Application health check: version={self._version}, uptime={uptime_display}")

        return ComponentHealthResult(
            component_name="Application",
            status=ComponentStatus.HEALTHY,
            details={
                "application_version": self._version,
                "python_version": sys.version.split()[0],
                "python_full_version": sys.version,
                "environment": self._environment,
                "startup_time": _APPLICATION_STARTUP_TIME.isoformat(),
                "uptime_seconds": uptime_seconds,
                "uptime_display": uptime_display,
            },
            checked_at=checked_at,
        )
