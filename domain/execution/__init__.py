"""
Purpose
-------
Package initializer for the Execution Domain. Exposes execution domain models,
enums, and domain exceptions.

Responsibilities
----------------
- Provide public module exports for execution domain entities.

Does NOT
---------
- Execute SSH commands.
- Perform RCA or LLM reasoning.
"""

from .exceptions import (
    CommandNotFoundError,
    ExecutionError,
    StepExecutionError,
    TimeoutExecutionError,
)
from .models import (
    ExecutionMetrics,
    ExecutionStatus,
    InvestigationExecutionResult,
    StepExecutionResult,
)

__all__ = [
    "ExecutionError",
    "StepExecutionError",
    "CommandNotFoundError",
    "TimeoutExecutionError",
    "ExecutionStatus",
    "StepExecutionResult",
    "ExecutionMetrics",
    "InvestigationExecutionResult",
]
