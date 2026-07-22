"""
Purpose
-------
Domain exceptions for the Operational Recommendation Engine.

Responsibilities
----------------
- Define explicit error types for recommendation processing and AI provider failures.

Does NOT
---------
- Catch system errors outside the recommendation domain.
- Execute infrastructure commands.
"""


class RecommendationError(Exception):
    """Base exception for all Recommendation Domain errors."""
    pass


class InvalidRCAResultError(RecommendationError):
    """Raised when the input RootCauseAnalysis object is invalid or empty."""

    def __init__(self, message: str = "Input must be a valid RootCauseAnalysis object."):
        self.message = message
        super().__init__(self.message)


class RecommendationProviderError(RecommendationError):
    """Raised when an external recommendation AI provider fails to generate guidance."""

    def __init__(self, provider_name: str, reason: str):
        self.provider_name = provider_name
        self.reason = reason
        super().__init__(f"Recommendation Provider '{provider_name}' failed: {reason}")
