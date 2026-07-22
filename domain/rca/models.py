"""
Purpose
-------
Domain models representing Root Cause Analysis outputs, hypotheses, and evidence reasoning traces.

Responsibilities
----------------
- Store structured root cause determinations, confidence scores, and hypothesis rankings.
- Store step-by-step reasoning traces and affected infrastructure component impacts.
- Represent complete RootCauseAnalysis payload passed to Phase 5 (Recommendation Engine).

Does NOT
---------
- Call LLM APIs or execute SSH commands directly.
- Correlate raw infrastructure data.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class SupportingEvidence(BaseModel):
    """
    Empirical metric observation supporting a hypothesis.
    """

    evidence_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this supporting evidence item."
    )

    metric_name: str = Field(
        ...,
        description="Name of the observed metric."
    )

    observed_value: Any = Field(
        ...,
        description="Observed empirical metric value."
    )

    finding_title: str = Field(
        ...,
        description="Title of the source operational finding from Phase 3."
    )

    relevance_explanation: str = Field(
        ...,
        description="Explanation of why this evidence supports the hypothesis."
    )


class Hypothesis(BaseModel):
    """
    RCA hypothesis representing a potential cause of the operational incident.
    """

    hypothesis_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this hypothesis."
    )

    title: str = Field(
        ...,
        description="Concise hypothesis title (e.g. 'Memory Exhaustion caused by Process Leak')."
    )

    description: str = Field(
        ...,
        description="Detailed description of the hypothesis mechanism."
    )

    likelihood_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability score between 0.0 and 1.0."
    )

    is_primary: bool = Field(
        default=False,
        description="True if this is selected as the primary root cause."
    )

    supporting_evidences: List[SupportingEvidence] = Field(
        default_factory=list,
        description="Evidences supporting this hypothesis."
    )


class ReasoningTrace(BaseModel):
    """
    Step in the logical reasoning process leading to the root cause determination.
    """

    step_number: int = Field(..., ge=1)
    observation: str = Field(..., description="Observed operational symptom or metric relationship.")
    deduction: str = Field(..., description="Logical conclusion derived from the observation.")


class AffectedComponent(BaseModel):
    """
    Resource or component impacted by the operational incident.
    """

    component_type: str = Field(..., description="Resource category (e.g. 'MEMORY', 'CPU', 'SERVICE', 'DISK').")
    name: str = Field(..., description="Name of the affected component or mount point.")
    impact_level: str = Field(default="MEDIUM", description="Impact severity ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW').")


class AnalysisMetadata(BaseModel):
    """
    Metadata about the AI RCA reasoning execution run.
    """

    provider_used: str = Field(default="Gemini", description="AI Provider used for analysis.")
    model_name: str = Field(default="gemini-2.5-flash", description="Model name identifier.")
    analysis_duration_seconds: float = Field(default=0.0, ge=0.0)
    total_findings_analyzed: int = Field(default=0, ge=0)


class RootCauseAnalysis(BaseModel):
    """
    Complete Root Cause Analysis payload produced by Phase 4.
    This object is passed to Phase 5 for Recommendation & Action Generation.
    """

    analysis_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this RCA payload."
    )

    correlation_id: str = Field(
        ...,
        description="ID of the source Phase 3 CorrelationResult."
    )

    investigation_id: str = Field(
        ...,
        description="ID of the source Phase 1 InvestigationPlan."
    )

    user_question: str = Field(
        ...,
        description="Original user natural language query."
    )

    primary_root_cause: str = Field(
        ...,
        description="Clear, authoritative statement of the primary root cause."
    )

    overall_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence score in the diagnosis."
    )

    summary: str = Field(
        ...,
        description="Executive summary of the incident diagnosis."
    )

    primary_hypothesis: Hypothesis = Field(
        ...,
        description="Primary hypothesis selected by the AI SRE engine."
    )

    alternative_hypotheses: List[Hypothesis] = Field(
        default_factory=list,
        description="Alternative hypotheses evaluated during analysis."
    )

    reasoning_trace: List[ReasoningTrace] = Field(
        default_factory=list,
        description="Step-by-step reasoning trace explaining the conclusion."
    )

    affected_components: List[AffectedComponent] = Field(
        default_factory=list,
        description="List of impacted infrastructure components and services."
    )

    metadata: AnalysisMetadata = Field(
        default_factory=AnalysisMetadata,
        description="Analysis run metadata and timing metrics."
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC creation timestamp."
    )
