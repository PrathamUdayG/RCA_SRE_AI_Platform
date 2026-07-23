"""
Purpose
-------
Application-layer health service orchestrator for the AI SRE Platform.

Responsibilities
----------------
- Orchestrate all infrastructure health checkers (SSH, Database, Gemini, Application).
- Aggregate individual ComponentHealthResult objects into a unified PlatformHealthReport.
- Derive overall platform health status from individual component statuses.

Does NOT
---------
- Perform infrastructure calls directly (delegates to health checker classes).
- Implement Streamlit UI rendering or presentation logic.
"""

import sys
import time
from datetime import datetime
from typing import List, Optional

from domain.health.models import (
    ComponentHealthResult,
    ComponentStatus,
    PlatformHealthReport,
)
from infrastructure.health import (
    AIProviderHealthChecker,
    ApplicationHealthChecker,
    DatabaseHealthChecker,
    SSHHealthChecker,
)
from shared.logging import get_logger

logger = get_logger("HealthService")


class HealthService:
    """
    Application-layer orchestrator that runs all platform health checks
    and aggregates results into a unified PlatformHealthReport.
    """

    def __init__(
        self,
        ssh_checker: Optional[SSHHealthChecker] = None,
        database_checker: Optional[DatabaseHealthChecker] = None,
        ai_provider_checker: Optional[AIProviderHealthChecker] = None,
        application_checker: Optional[ApplicationHealthChecker] = None,
        llm_checker: Optional[AIProviderHealthChecker] = None,
        gemini_checker: Optional[AIProviderHealthChecker] = None,
    ):
        self._ssh_checker = ssh_checker or SSHHealthChecker()
        self._database_checker = database_checker or DatabaseHealthChecker()
        self._ai_provider_checker = ai_provider_checker or llm_checker or gemini_checker or AIProviderHealthChecker()
        self._application_checker = application_checker or ApplicationHealthChecker()

    def check_all(self) -> PlatformHealthReport:
        """
        Runs all platform health checks and returns an aggregated report.
        """
        logger.info("Starting platform-wide health check...")
        checked_at = datetime.utcnow()

        results: List[ComponentHealthResult] = []

        # Run each checker safely — a single checker failure must not prevent others
        for checker_name, checker in [
            ("SSH Server", self._ssh_checker),
            ("PostgreSQL Database", self._database_checker),
            ("AI Provider", self._ai_provider_checker),
            ("Application", self._application_checker),
        ]:
            try:
                result = checker.check()
                results.append(result)
            except Exception as exc:
                logger.error(f"Unexpected error in {checker_name} health checker: {exc}")
                results.append(
                    ComponentHealthResult(
                        component_name=checker_name,
                        status=ComponentStatus.UNHEALTHY,
                        error_message=f"Health checker crashed: {type(exc).__name__}: {exc}",
                        recommendation=f"Review the {checker_name} health checker implementation for bugs.",
                        checked_at=checked_at,
                    )
                )

        # Derive overall status from active (non-NOT_CONFIGURED) components
        overall_status = self._derive_overall_status(results)

        # Extract application metadata from the Application checker result
        app_result = next((r for r in results if r.component_name == "Application"), None)
        app_version = app_result.details.get("application_version", "1.0.0") if app_result else "1.0.0"
        python_version = app_result.details.get("python_version", sys.version.split()[0]) if app_result else sys.version.split()[0]
        environment = app_result.details.get("environment", "production") if app_result else "production"
        startup_time_str = app_result.details.get("startup_time") if app_result else None
        startup_time = datetime.fromisoformat(startup_time_str) if startup_time_str else None
        uptime_seconds = app_result.details.get("uptime_seconds") if app_result else None

        logger.info(f"Platform health check completed: overall_status={overall_status.value}")

        return PlatformHealthReport(
            overall_status=overall_status,
            component_results=results,
            checked_at=checked_at,
            application_version=app_version,
            python_version=python_version,
            environment=environment,
            startup_time=startup_time,
            uptime_seconds=uptime_seconds,
        )

    def check_component(self, component_name: str) -> ComponentHealthResult:
        """
        Runs a health check for a single named component.

        Parameters
        ----------
        component_name : str
            Name of the component to check. Must be one of:
            "ssh", "database", "gemini", "application".

        Returns
        -------
        ComponentHealthResult
            Health result for the specified component.

        Raises
        ------
        ValueError
            If the component name is not recognized.
        """
        checkers = {
            "ssh": self._ssh_checker,
            "database": self._database_checker,
            "gemini": self._gemini_checker,
            "application": self._application_checker,
        }

        checker = checkers.get(component_name.lower())
        if not checker:
            raise ValueError(
                f"Unknown component: '{component_name}'. "
                f"Valid components: {list(checkers.keys())}"
            )

        return checker.check()

    @staticmethod
    def _derive_overall_status(results: List[ComponentHealthResult]) -> ComponentStatus:
        """
        Derives the overall platform health status from individual component results.

        Parameters
        ----------
        results : List[ComponentHealthResult]
            Individual component health check results.

        Returns
        -------
        ComponentStatus
            Derived overall platform status.
        """
        # Filter out NOT_CONFIGURED components for status derivation
        active_results = [r for r in results if r.status != ComponentStatus.NOT_CONFIGURED]

        if not active_results:
            return ComponentStatus.HEALTHY

        statuses = {r.status for r in active_results}

        if statuses == {ComponentStatus.HEALTHY}:
            return ComponentStatus.HEALTHY
        elif ComponentStatus.UNHEALTHY in statuses and ComponentStatus.HEALTHY in statuses:
            return ComponentStatus.DEGRADED
        elif statuses == {ComponentStatus.UNHEALTHY}:
            return ComponentStatus.UNHEALTHY
        elif ComponentStatus.DEGRADED in statuses:
            return ComponentStatus.DEGRADED
        else:
            return ComponentStatus.DEGRADED
