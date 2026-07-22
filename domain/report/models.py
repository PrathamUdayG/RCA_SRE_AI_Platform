"""
Purpose
-------
Unified platform InvestigationReport domain model synthesizing outputs from all Phase 1-6 engines.

Responsibilities
----------------
- Aggregate Phase 1 InvestigationPlan, Phase 2 InvestigationExecutionResult, Phase 3 CorrelationResult,
  Phase 4 RootCauseAnalysis, Phase 5 RecommendationReport, and Phase 6 PolicyDecision into a single payload.

Does NOT
---------
- Execute SSH commands or perform LLM calls.
- Modify infrastructure.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from domain.correlation.models import CorrelationResult
from domain.execution.models import InvestigationExecutionResult
from domain.investigation.models import InvestigationPlan
from domain.policy.models import PolicyDecision
from domain.rca.models import RootCauseAnalysis
from domain.recommendation.models import RecommendationReport


class InvestigationReport(BaseModel):
    """
    Unified end-to-end investigation report payload returned by the AI SRE Platform.
    """

    report_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this unified investigation report."
    )

    user_question: str = Field(
        ...,
        description="Original user natural language query."
    )

    status: str = Field(
        default="SUCCESS",
        description="Overall platform execution status ('SUCCESS', 'PARTIAL_SUCCESS', 'FAILED')."
    )

    total_execution_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total duration taken to run the complete end-to-end workflow."
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC creation timestamp."
    )

    plan: Optional[InvestigationPlan] = Field(
        default=None,
        description="Phase 1: Investigation Plan."
    )

    execution: Optional[InvestigationExecutionResult] = Field(
        default=None,
        description="Phase 2: Multi-Command Execution Results."
    )

    correlation: Optional[CorrelationResult] = Field(
        default=None,
        description="Phase 3: Data Correlation Findings."
    )

    rca: Optional[RootCauseAnalysis] = Field(
        default=None,
        description="Phase 4: AI Root Cause Analysis."
    )

    recommendation: Optional[RecommendationReport] = Field(
        default=None,
        description="Phase 5: Operational Recommendation Guidance."
    )

    policy_decision: Optional[PolicyDecision] = Field(
        default=None,
        description="Phase 6: Policy Engine & Approval Decision."
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Platform execution metadata and audit correlation keys."
    )
