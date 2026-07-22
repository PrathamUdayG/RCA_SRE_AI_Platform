"""
Purpose
-------
Package exports for the Correlation Domain. Exposes domain models, exceptions,
and base rule interfaces.

Responsibilities
----------------
- Provide public module exports for correlation domain entities.

Does NOT
---------
- Call LLM APIs or execute SSH commands.
- Perform Root Cause Analysis.
"""

from .exceptions import (
    CorrelationError,
    InvalidExecutionResultError,
    RuleEvaluationError,
)
from .models import (
    CorrelationMetadata,
    CorrelationResult,
    Evidence,
    Finding,
    FindingCategory,
    Severity,
)

__all__ = [
    "CorrelationError",
    "InvalidExecutionResultError",
    "RuleEvaluationError",
    "Severity",
    "FindingCategory",
    "Evidence",
    "Finding",
    "CorrelationMetadata",
    "CorrelationResult",
]
