"""
Purpose:
--------
Domain-specific exceptions for the Investigation Planning Engine.

Responsibilities:
-----------------
- Define explicit error types for investigation domain failures.

Does NOT:
---------
- Catch system errors outside the investigation domain.
- Execute any logic or handle SSH/Database operations.
"""


class InvestigationError(Exception):
    """Base exception for all Investigation Domain errors."""
    pass


class InvalidQuestionError(InvestigationError):
    """Raised when the provided user question is empty, invalid, or malformed."""

    def __init__(self, message: str = "User question must be a non-empty string."):
        self.message = message
        super().__init__(self.message)


class PlanGenerationError(InvestigationError):
    """Raised when the InvestigationPlanner fails to generate a valid plan."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Failed to generate investigation plan: {reason}")


class TemplateNotFoundError(InvestigationError):
    """Raised when a requested investigation template key does not exist."""

    def __init__(self, template_name: str):
        self.template_name = template_name
        super().__init__(f"Investigation template '{template_name}' was not found.")
