"""
Purpose
-------
Domain exceptions for the AI Root Cause Analysis Engine.

Responsibilities
----------------
- Define explicit error types for RCA processing and LLM provider failures.

Does NOT
---------
- Catch system errors outside the RCA domain.
- Execute network or database operations.
"""


class RCAError(Exception):
    """Base exception for all RCA Domain errors."""
    pass


class InvalidCorrelationResultError(RCAError):
    """Raised when the input CorrelationResult is invalid or empty."""

    def __init__(self, message: str = "Input must be a valid CorrelationResult object."):
        self.message = message
        super().__init__(self.message)


class LLMProviderError(RCAError):
    """Raised when an external AI provider fails to generate a structured analysis."""

    def __init__(self, provider_name: str, reason: str):
        self.provider_name = provider_name
        self.reason = reason
        super().__init__(f"LLM Provider '{provider_name}' failed: {reason}")
