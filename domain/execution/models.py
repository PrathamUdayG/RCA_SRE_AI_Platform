"""
Purpose
-------
Domain models representing execution results, step outputs, and execution metrics.

Responsibilities
----------------
- Store single-step execution results (command, raw output, parsed output, duration).
- Store aggregated metrics for an entire investigation execution.
- Represent complete InvestigationExecutionResult payload for downstream correlation.

Does NOT
---------
- Execute commands or call SSH/PostgreSQL directly.
- Perform RCA or LLM reasoning.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Status outcome of a step or full investigation execution."""
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"


class StepExecutionResult(BaseModel):
    """
    Result model for an individual investigation step execution.
    """

    step_id: str = Field(
        ...,
        description="ID of the InvestigationStep executed."
    )

    order: int = Field(
        ...,
        description="Sequence order of the step."
    )

    command_id: str = Field(
        ...,
        description="Command registry key."
    )

    linux_command: str = Field(
        ...,
        description="Actual Linux command executed on remote server."
    )

    description: str = Field(
        ...,
        description="Step purpose description."
    )

    status: ExecutionStatus = Field(
        default=ExecutionStatus.SUCCESS,
        description="Outcome status of the step execution."
    )

    raw_output: str = Field(
        default="",
        description="Raw terminal stdout string returned from SSH."
    )

    parsed_output: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured JSON output produced by the output parser."
    )

    error_message: Optional[str] = Field(
        default=None,
        description="Error description if step failed or stderr was returned."
    )

    execution_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Time taken to execute this individual step."
    )

    executed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the step finished."
    )


class ExecutionMetrics(BaseModel):
    """
    Aggregated metrics for an entire investigation plan execution.
    """

    total_steps: int = Field(default=0, ge=0)
    successful_steps: int = Field(default=0, ge=0)
    failed_steps: int = Field(default=0, ge=0)
    skipped_steps: int = Field(default=0, ge=0)
    total_duration_seconds: float = Field(default=0.0, ge=0.0)
    strategy_used: str = Field(default="SEQUENTIAL")


class InvestigationExecutionResult(BaseModel):
    """
    Complete standardized execution result produced after executing an InvestigationPlan.
    This object is passed to Phase 3 for Root Cause Analysis.
    """

    execution_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this execution run."
    )

    investigation_id: str = Field(
        ...,
        description="ID of the source InvestigationPlan."
    )

    user_question: str = Field(
        ...,
        description="Original user natural language question."
    )

    status: ExecutionStatus = Field(
        default=ExecutionStatus.SUCCESS,
        description="Overall execution status."
    )

    metrics: ExecutionMetrics = Field(
        default_factory=ExecutionMetrics,
        description="Summary statistics of step executions."
    )

    step_results: List[StepExecutionResult] = Field(
        default_factory=list,
        description="Ordered list of results for each executed step."
    )

    executed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC completion timestamp."
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context, host info, or tags."
    )
