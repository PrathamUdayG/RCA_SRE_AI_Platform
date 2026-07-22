"""
Purpose
-------
Package exports for shared platform exceptions.

Responsibilities
----------------
- Expose global exception classes cleanly.

Does NOT
---------
- Contain business or infrastructure logic.
"""

from .base_exceptions import (
    ConfigurationException,
    CorrelationException,
    ExecutionException,
    PlatformBaseException,
    PolicyException,
    RCAException,
    RecommendationException,
    SSHException,
    ValidationException,
)

__all__ = [
    "PlatformBaseException",
    "ConfigurationException",
    "SSHException",
    "ExecutionException",
    "CorrelationException",
    "RCAException",
    "RecommendationException",
    "PolicyException",
    "ValidationException",
]
