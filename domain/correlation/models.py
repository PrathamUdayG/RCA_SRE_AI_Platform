"""
Purpose
-------
Domain models representing correlated operational findings, structured evidence, and metrics.

Responsibilities
----------------
- Store structured operational findings (title, category, severity, confidence).
- Store concrete metric evidence (observed value, source command, thresholds).
- Represent complete CorrelationResult object passed to Phase 4 for Root Cause Analysis.

Does NOT
---------
- Execute SSH commands or call LLM APIs.
- Perform Root Cause Analysis or generate recommendations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Operational severity classification for correlated findings."""
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingCategory(str, Enum):
    """Domain category for operational findings."""
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK = "NETWORK"
    PROCESS = "PROCESS"
    SERVICE = "SERVICE"
    CONTAINER = "CONTAINER"
    SYSTEM = "SYSTEM"


class Evidence(BaseModel):
    """
    Concrete empirical observation supporting a finding.
    """

    metric_name: str = Field(
        ...,
        description="Name of the observed metric (e.g. 'load_average_1m', 'memory_used_percent')."
    )

    observed_value: Any = Field(
        ...,
        description="Actual value observed from parsed execution output."
    )

    threshold: Optional[Any] = Field(
        default=None,
        description="Reference threshold value that triggered the finding."
    )

    source_command: str = Field(
        ...,
        description="Linux command that produced this evidence."
    )

    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional contextual key-value observations."
    )


class Finding(BaseModel):
    """
    Structured operational finding representing a correlated metric relationship or anomaly.
    """

    finding_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this finding."
    )

    title: str = Field(
        ...,
        description="Concise operational title (e.g. 'CPU Saturation Detected')."
    )

    category: FindingCategory = Field(
        ...,
        description="Domain category of the finding."
    )

    severity: Severity = Field(
        ...,
        description="Assigned severity level."
    )

    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Rule-based confidence score between 0.0 and 1.0."
    )

    summary: str = Field(
        ...,
        description="Structured operational summary of the observed pattern."
    )

    evidences: List[Evidence] = Field(
        default_factory=list,
        description="List of empirical metric observations supporting this finding."
    )

    related_metrics: List[str] = Field(
        default_factory=list,
        description="Names of metrics involved in this finding."
    )

    affected_resources: List[str] = Field(
        default_factory=list,
        description="List of affected system resources (e.g. hostnames, filesystems, interface names)."
    )


class CorrelationMetadata(BaseModel):
    """
    Metadata and statistics for a correlation evaluation run.
    """

    total_findings: int = Field(default=0, ge=0)
    critical_count: int = Field(default=0, ge=0)
    high_count: int = Field(default=0, ge=0)
    medium_count: int = Field(default=0, ge=0)
    low_count: int = Field(default=0, ge=0)
    info_count: int = Field(default=0, ge=0)
    evaluation_time_seconds: float = Field(default=0.0, ge=0.0)
    rules_evaluated: int = Field(default=0, ge=0)


class CorrelationResult(BaseModel):
    """
    Standardized payload produced by Phase 3 containing all correlated operational findings.
    This object is passed to Phase 4 for Root Cause Analysis.
    """

    correlation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this correlation result."
    )

    execution_id: str = Field(
        ...,
        description="ID of the source Phase 2 InvestigationExecutionResult."
    )

    investigation_id: str = Field(
        ...,
        description="ID of the original Phase 1 InvestigationPlan."
    )

    user_question: str = Field(
        ...,
        description="Original user natural language query."
    )

    findings: List[Finding] = Field(
        default_factory=list,
        description="List of correlated operational findings."
    )

    metadata: CorrelationMetadata = Field(
        default_factory=CorrelationMetadata,
        description="Summary statistics and execution metrics."
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC creation timestamp."
    )
