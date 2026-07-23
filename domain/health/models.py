"""
Purpose
-------
Pure domain models for Platform Health observability.

Responsibilities
----------------
- Define ComponentStatus enum representing the health state of a platform component.
- Define ComponentHealthResult dataclass for individual component health check results.
- Define PlatformHealthReport dataclass aggregating all component health results.

Does NOT
---------
- Perform any infrastructure calls (SSH, database, API, network).
- Depend on external libraries beyond Pydantic and Python stdlib.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComponentStatus(str, Enum):
    """
    Enumeration of possible health states for a platform component.

    Values
    ------
    HEALTHY : str
        Component is fully operational and responsive.
    UNHEALTHY : str
        Component is unreachable or returning errors.
    DEGRADED : str
        Component is reachable but exhibiting performance issues.
    NOT_CONFIGURED : str
        Component has not been set up or configured on this platform instance.
    """

    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    DEGRADED = "DEGRADED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class ComponentHealthResult(BaseModel):
    """
    Health check result for a single platform component.

    Attributes
    ----------
    component_name : str
        Human-readable name of the component (e.g., "SSH Server", "PostgreSQL Database").
    status : ComponentStatus
        Current health status of the component.
    details : Dict[str, Any]
        Key-value metadata about the component (hostname, version, latency, etc.).
    error_message : Optional[str]
        Human-readable error description if the component is unhealthy.
    recommendation : Optional[str]
        Suggested remediation action if the component is unhealthy.
    checked_at : datetime
        Timestamp when the health check was performed.
    latency_ms : Optional[float]
        Round-trip probe latency in milliseconds, if measurable.
    """

    component_name: str
    category: str = Field(default="Infrastructure")
    status: ComponentStatus
    details: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    recommendation: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: Optional[float] = None


class PlatformHealthReport(BaseModel):
    """
    Aggregated health report for the entire AI SRE Platform.

    Attributes
    ----------
    overall_status : ComponentStatus
        Derived overall platform health status.
    component_results : List[ComponentHealthResult]
        Individual health check results for each platform component.
    checked_at : datetime
        Timestamp when the aggregate health check was performed.
    application_version : str
        Current platform application version string.
    python_version : str
        Python interpreter version.
    environment : str
        Current runtime environment identifier.
    startup_time : Optional[datetime]
        Timestamp when the application was started.
    uptime_seconds : Optional[float]
        Number of seconds the application has been running.
    """

    overall_status: ComponentStatus
    component_results: List[ComponentHealthResult] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    application_version: str = "1.0.0"
    python_version: str = ""
    environment: str = "production"
    startup_time: Optional[datetime] = None
    uptime_seconds: Optional[float] = None
