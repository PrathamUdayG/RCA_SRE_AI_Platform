"""
Purpose
-------
Domain exceptions for the Data Correlation Engine.

Responsibilities
----------------
- Define explicit error types for correlation processing failures.

Does NOT
---------
- Catch system errors outside the correlation domain.
- Execute network or database operations.
"""


class CorrelationError(Exception):
    """Base exception for all Correlation Domain errors."""
    pass


class InvalidExecutionResultError(CorrelationError):
    """Raised when the input InvestigationExecutionResult is invalid or empty."""

    def __init__(self, message: str = "Input execution result must be a valid InvestigationExecutionResult."):
        self.message = message
        super().__init__(self.message)


class RuleEvaluationError(CorrelationError):
    """Raised when an individual correlation rule fails during evaluation."""

    def __init__(self, rule_name: str, reason: str):
        self.rule_name = rule_name
        self.reason = reason
        super().__init__(f"Rule '{rule_name}' evaluation failed: {reason}")
