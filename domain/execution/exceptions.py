"""
Purpose
-------
Domain exceptions for the Multi-Command Execution Engine.

Responsibilities
----------------
- Define explicit error types for step failures, timeouts, and missing command registrations.

Does NOT
---------
- Catch system errors outside the execution domain.
- Perform SSH or database logic.
"""


class ExecutionError(Exception):
    """Base exception for all Execution Domain errors."""
    pass


class CommandNotFoundError(ExecutionError):
    """Raised when a step's command_id is not found in the Linux Command Registry."""

    def __init__(self, command_id: str):
        self.command_id = command_id
        super().__init__(f"Command key '{command_id}' not found in registry.")


class StepExecutionError(ExecutionError):
    """Raised when an individual investigation step fails during execution."""

    def __init__(self, step_id: str, command_id: str, reason: str):
        self.step_id = step_id
        self.command_id = command_id
        self.reason = reason
        super().__init__(f"Step '{step_id}' ({command_id}) failed: {reason}")


class TimeoutExecutionError(ExecutionError):
    """Raised when an investigation step exceeds its maximum timeout budget."""

    def __init__(self, step_id: str, timeout_seconds: int):
        self.step_id = step_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Step '{step_id}' timed out after {timeout_seconds}s.")
