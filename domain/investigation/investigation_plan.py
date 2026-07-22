"""
Domain Model:
Investigation Plan

This module defines the core domain objects representing a planned
investigation. These models are shared across the AI SRE Platform and
contain no business logic.

Responsibilities:
- Represent an investigation
- Represent investigation steps
- Represent execution strategy
- Represent investigation status

This module must remain independent of:
- SSH
- LLMs
- Databases
- APIs
- Streamlit
- Parsers
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ==========================================================
# ENUMS
# ==========================================================

class InvestigationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InvestigationStatus(str, Enum):
    PENDING = "PENDING"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExecutionStrategy(str, Enum):
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"


# ==========================================================
# INVESTIGATION STEP
# ==========================================================

class InvestigationStep(BaseModel):
    """
    Represents one observation required during an investigation.

    Example:
        Check CPU Usage
        Check Memory Usage
        Check Disk Usage
    """

    step_id: str = Field(default_factory=lambda: str(uuid4()))

    order: int = Field(
        ...,
        description="Execution order within the investigation."
    )

    command_name: str = Field(
        ...,
        description="Whitelisted command identifier."
    )

    description: str = Field(
        ...,
        description="Human-readable explanation of this step."
    )

    parser_name: str = Field(
        ...,
        description="Parser responsible for interpreting command output."
    )

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        description="Maximum execution time."
    )

    depends_on: List[str] = Field(
        default_factory=list,
        description="IDs of prerequisite steps."
    )


# ==========================================================
# INVESTIGATION PLAN
# ==========================================================

class InvestigationPlan(BaseModel):
    """
    Complete execution plan generated before any command is executed.
    """

    investigation_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    user_question: str

    priority: InvestigationPriority = InvestigationPriority.MEDIUM

    status: InvestigationStatus = InvestigationStatus.PENDING

    execution_strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL

    created_at: datetime = Field(default_factory=datetime.utcnow)

    estimated_duration_seconds: Optional[int] = None

    steps: List[InvestigationStep] = Field(default_factory=list)

    metadata: dict = Field(default_factory=dict)

    """
Phase 1 — Investigation Planning Engine

Goal

Transform a user's request into an investigation plan instead of a single command.

Input

"Why is my server slow?"

Output

InvestigationPlan
    Step 1
        CPU

    Step 2
        Memory

    Step 3
        Disk

    Step 4
        Network

    Step 5
        Load Average

Execution Strategy

Parallel

Priority

High

No SSH execution occurs yet.

This phase only produces the plan.
    """