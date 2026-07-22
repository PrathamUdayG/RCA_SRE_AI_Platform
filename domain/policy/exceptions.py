"""
Purpose
-------
Domain exceptions for the Policy Engine & Approval Framework.

Responsibilities
----------------
- Define explicit error types for policy evaluation and recommendation validation failures.

Does NOT
---------
- Catch system errors outside the policy domain.
- Execute network or database operations.
"""


class PolicyError(Exception):
    """Base exception for all Policy Domain errors."""
    pass


class InvalidRecommendationReportError(PolicyError):
    """Raised when the input RecommendationReport object is invalid or empty."""

    def __init__(self, message: str = "Input must be a valid RecommendationReport object."):
        self.message = message
        super().__init__(self.message)


class PolicyRuleEvaluationError(PolicyError):
    """Raised when a specific policy rule evaluation fails."""

    def __init__(self, rule_name: str, reason: str):
        self.rule_name = rule_name
        self.reason = reason
        super().__init__(f"Policy rule '{rule_name}' evaluation failed: {reason}")
