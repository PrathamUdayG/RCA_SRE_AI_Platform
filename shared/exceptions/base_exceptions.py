"""
Purpose
-------
Global cross-cutting platform exception hierarchy.

Responsibilities
----------------
- Provide base exception classes for platform-wide error handling.

Does NOT
---------
- Implement infrastructure or business logic.
"""


class PlatformBaseException(Exception):
    """Base exception for all AI SRE Platform errors."""
    pass


class ConfigurationException(PlatformBaseException):
    """Raised when environment or settings configuration is invalid."""
    pass


class SSHException(PlatformBaseException):
    """Raised when remote SSH execution encounters an unrecoverable failure."""
    pass


class ExecutionException(PlatformBaseException):
    """Raised when multi-command execution fails."""
    pass


class CorrelationException(PlatformBaseException):
    """Raised when data correlation rules encounter errors."""
    pass


class RCAException(PlatformBaseException):
    """Raised when Root Cause Analysis engine encounters errors."""
    pass


class RecommendationException(PlatformBaseException):
    """Raised when Operational Recommendation engine encounters errors."""
    pass


class PolicyException(PlatformBaseException):
    """Raised when Policy Engine evaluation fails."""
    pass


class ValidationException(PlatformBaseException):
    """Raised when domain object validation fails."""
    pass
