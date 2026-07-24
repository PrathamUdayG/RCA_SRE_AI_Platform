"""
Purpose
-------
Unified platform InvestigationReport domain model synthesizing outputs from all Phase 1-6 engines,
plus the ExecutiveSummary presentation synthesis layer.

Responsibilities
----------------
- Define ExecutiveSummary domain model holding executive direct answers, KPI metrics, supporting evidence,
  recommendations summary, policy summary, and investigation metadata.
- Aggregate Phase 1 InvestigationPlan, Phase 2 InvestigationExecutionResult, Phase 3 CorrelationResult,
  Phase 4 RootCauseAnalysis, Phase 5 RecommendationReport, Phase 6 PolicyDecision, and ExecutiveSummary into a single payload.

Does NOT
---------
- Execute SSH commands or perform LLM calls.
- Modify infrastructure.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from domain.correlation.models import CorrelationResult
from domain.capability.models import ServerCapabilities
from domain.execution.models import InvestigationExecutionResult
from domain.investigation.models import InvestigationPlan
from domain.policy.models import PolicyDecision
from domain.rca.models import RootCauseAnalysis
from domain.recommendation.models import RecommendationReport


class ExecutiveSummary(BaseModel):
    """
    Synthesized executive investigation summary payload presented to human operators and executives first.
    """

    user_question: str = Field(
        ...,
        description="Original user natural language query."
    )

    direct_answer: str = Field(
        ...,
        description="Concise 1-2 paragraph executive response directly answering the user query."
    )

    investigation_status: str = Field(
        default="SUCCESS",
        description="Investigation status ('SUCCESS', 'PARTIAL_SUCCESS', 'FAILED', 'INCONCLUSIVE', 'NO_DATA')."
    )

    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence score (0.0 to 1.0)."
    )

    primary_root_cause: str = Field(
        default="Investigation Inconclusive",
        description="Primary root cause title or status explanation."
    )

    key_findings: List[str] = Field(
        default_factory=list,
        description="High-level bulleted operational findings."
    )

    key_evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Empirical metric violations and key diagnostic observations."
    )

    recommendations_summary: str = Field(
        default="No immediate action required.",
        description="Concise executive summary of operational recommendations."
    )

    policy_summary: str = Field(
        default="N/A",
        description="Summary of policy evaluation and approval status."
    )

    investigation_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata including investigation_id, target_server, timestamps, duration, commands executed/failed, data quality %."
    )


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

    executive_summary: Optional[ExecutiveSummary] = Field(
        default=None,
        description="Executive Investigation Summary presentation synthesis layer."
    )

    capabilities: Optional[ServerCapabilities] = Field(
        default=None,
        description="Read-only pre-planning infrastructure capability discovery result.",
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
