"""
Purpose
-------
Domain models representing operational recommendations, risk levels, validation steps, and rollback plans.

Responsibilities
----------------
- Store prioritized operational action items (Immediate, Short-Term, Long-Term, Preventive).
- Store validation criteria, rollback plans, risk assessments, and monitoring suggestions.
- Represent complete RecommendationReport payload passed to Phase 6 (Policy / Autonomous Remediation Engine).

Does NOT
---------
- Execute commands or modify remote infrastructure.
- Perform Root Cause Analysis or data correlation directly.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class RecommendationCategory(str, Enum):
    """Operational focus category for recommendations."""
    IMMEDIATE = "IMMEDIATE"
    SHORT_TERM = "SHORT_TERM"
    LONG_TERM = "LONG_TERM"
    PREVENTIVE = "PREVENTIVE"
    CAPACITY_PLANNING = "CAPACITY_PLANNING"
    SECURITY = "SECURITY"
    RUNBOOK = "RUNBOOK"


class RecommendationPriority(str, Enum):
    """Execution priority level for operational recommendations."""
    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH = "P2_HIGH"
    P3_MEDIUM = "P3_MEDIUM"
    P4_LOW = "P4_LOW"


class RiskLevel(str, Enum):
    """Risk severity assessment associated with executing a recommendation."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ValidationStep(BaseModel):
    """
    Step required to verify system health before or after applying a recommendation.
    """

    step_number: int = Field(..., ge=1, description="Sequence order for validation.")
    command_or_metric: str = Field(..., description="Linux command or metric to check.")
    expected_outcome: str = Field(..., description="Expected healthy result or state.")


class RollbackPlan(BaseModel):
    """
    Instructions for reverting changes if a recommendation causes unexpected issues.
    """

    rollback_steps: List[str] = Field(default_factory=list, description="Ordered steps to revert changes.")
    estimated_rollback_time_minutes: int = Field(default=5, ge=1, description="Estimated time required to revert.")
    risk_summary: str = Field(default="Low risk rollback.", description="Summary of rollback risks.")


class Recommendation(BaseModel):
    """
    Single structured operational action recommended by the AI SRE engine.
    """

    recommendation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this recommendation."
    )

    title: str = Field(..., description="Short action title (e.g. 'Restart Memory Leaking Worker').")
    description: str = Field(..., description="Detailed instructions for performing the action.")
    reason: str = Field(..., description="Operational justification tied to the Root Cause Analysis.")
    category: RecommendationCategory = Field(..., description="Category classification.")
    priority: RecommendationPriority = Field(..., description="Assigned priority.")
    risk_level: RiskLevel = Field(..., description="Associated risk level.")
    expected_benefit: str = Field(..., description="Benefit of completing this action.")
    estimated_impact: str = Field(..., description="Impact on system performance or availability.")
    required_skill_level: str = Field(default="Senior SRE", description="Required engineering expertise level.")
    requires_human_approval: bool = Field(default=True, description="True if human approval is required.")
    target_resource: str = Field(..., description="Target service, process, or mount point.")


class MonitoringRecommendation(BaseModel):
    """
    Alerting or telemetry metric recommendation to prevent incident recurrence.
    """

    metric_or_alert: str = Field(..., description="Metric name or alert condition.")
    suggested_threshold: str = Field(..., description="Recommended alert threshold.")
    rationale: str = Field(..., description="Why this monitoring guardrail should be added.")


class PreventionRecommendation(BaseModel):
    """
    Long-term architectural or configuration safeguard.
    """

    preventive_action: str = Field(..., description="Action to prevent future occurrences.")
    target_system: str = Field(..., description="System or service target.")
    benefit: str = Field(..., description="Long-term benefit.")


class RecommendationMetadata(BaseModel):
    """
    Metadata about the recommendation generation execution.
    """

    provider_used: str = Field(default="Gemini", description="AI Provider used for recommendation generation.")
    model_name: str = Field(default="gemini-2.5-flash", description="Model identifier.")
    generation_duration_seconds: float = Field(default=0.0, ge=0.0)
    total_recommendations_count: int = Field(default=0, ge=0)


class RecommendationReport(BaseModel):
    """
    Standardized payload produced by Phase 5 containing operational recommendations.
    This payload is passed to Phase 6 (Policy / Autonomous Remediation Engine).
    """

    report_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this recommendation report."
    )

    analysis_id: str = Field(..., description="ID of the source Phase 4 RootCauseAnalysis.")
    investigation_id: str = Field(..., description="ID of the original Phase 1 InvestigationPlan.")
    user_question: str = Field(..., description="Original user natural language query.")

    executive_summary: str = Field(..., description="Executive summary of guidance.")
    primary_root_cause_ref: str = Field(..., description="Reference statement of the primary root cause.")

    recommended_actions: List[Recommendation] = Field(
        default_factory=list,
        description="Ordered list of recommended action items."
    )

    validation_steps: List[ValidationStep] = Field(
        default_factory=list,
        description="Validation checks before/after applying guidance."
    )

    rollback_plan: RollbackPlan = Field(
        default_factory=RollbackPlan,
        description="Rollback procedure if guidance fails."
    )

    monitoring_recommendations: List[MonitoringRecommendation] = Field(
        default_factory=list,
        description="Telemetry and monitoring guardrails."
    )

    preventive_recommendations: List[PreventionRecommendation] = Field(
        default_factory=list,
        description="Long-term architectural safeguards."
    )

    additional_investigations: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up investigation questions."
    )

    metadata: RecommendationMetadata = Field(
        default_factory=RecommendationMetadata,
        description="Generation metadata."
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC creation timestamp."
    )
