"""
Purpose
-------
Package exports for the Application Health service.

Responsibilities
----------------
- Expose HealthService orchestrator.

Does NOT
---------
- Contain business logic or infrastructure calls.
"""

from .health_service import HealthService

__all__ = ["HealthService"]
