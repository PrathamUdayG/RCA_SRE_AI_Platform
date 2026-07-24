"""
Purpose
-------
Domain models representing policy decisions, approval statuses, action permissions, and policy violations.

Responsibilities
----------------
- Store policy evaluation decisions (Auto-Approved, Human Approval Required, Prohibited).
- Store approval requests, permission classifications, and explicit policy violations.
- Represent complete PolicyDecision payload passed to Phase 7 (Autonomous Remediation Engine).

Does NOT
---------
- Execute commands or modify remote infrastructure.
- Perform AI reasoning or LLM calls.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Approval classification assigned to a recommended action."""
    AUTO_APPROVED = "AUTO_APPROVED"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
    CRITICAL_APPROVAL_REQUIRED = "CRITICAL_APPROVAL_REQUIRED"
    SECURITY_APPROVAL_REQUIRED = "SECURITY_APPROVAL_REQUIRED"
    PROHIBITED = "PROHIBITED"
    REJECTED = "REJECTED"


class ActionPermission(str, Enum):
    """Execution permission granted to an action."""
    ALLOWED_AUTOMATED = "ALLOWED_AUTOMATED"
    ALLOWED_MANUAL_ONLY = "ALLOWED_MANUAL_ONLY"
    BLOCKED = "BLOCKED"


class RiskLevel(str, Enum):
    """Risk classification assigned during policy evaluation."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PolicyViolation(BaseModel):
    """
    Policy violation detected during recommendation evaluation.
    """

    violation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this violation."
    )

    rule_name: str = Field(..., description="Name of the policy rule violated.")
    severity: str = Field(default="BLOCKING", description="Severity ('BLOCKING' or 'WARNING').")
    message: str = Field(..., description="Detailed explanation of the policy violation.")
    recommendation_id: str = Field(..., description="ID of the recommendation violating policy.")


class PolicyRule(BaseModel):
    """
    Configurable policy rule definition.
    """

    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    rule_name: str = Field(..., description="Unique rule identifier.")
    description: str = Field(..., description="Rule intent description.")
    is_active: bool = Field(default=True, description="True if rule is active.")


class DecisionReason(BaseModel):
    """
    Justification for a policy approval decision.
    """

    recommendation_id: str = Field(..., description="ID of the evaluated recommendation.")
    reason_text: str = Field(..., description="Explanation of why this decision was reached.")
    policy_applied: str = Field(..., description="Name of the policy rule applied.")


class ApprovalRequest(BaseModel):
    """
    Approval request generated for a specific action item.
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this approval request."
    )

    recommendation_id: str = Field(..., description="Source recommendation ID.")
    action_title: str = Field(..., description="Title of the recommended action.")
    target_resource: str = Field(..., description="Target system or service.")
    approval_status: ApprovalStatus = Field(..., description="Assigned approval status.")
    permission: ActionPermission = Field(..., description="Granted execution permission.")
    required_role: str = Field(default="Senior SRE", description="Role authorized to approve or execute.")
    risk_level: Optional[RiskLevel] = Field(default=None, description="Assigned risk level of the target action.")
    rejection_reason: Optional[str] = Field(default=None, description="Reason if action is rejected/prohibited.")

    @property
    def recommendation_title(self) -> str:
        """Alias property for backward compatibility with UI components expecting recommendation_title."""
        return self.action_title



class DecisionMetadata(BaseModel):
    """
    Metadata summarizing a policy evaluation run.
    """

    total_recommendations_evaluated: int = Field(default=0, ge=0)
    auto_approved_count: int = Field(default=0, ge=0)
    human_approval_count: int = Field(default=0, ge=0)
    prohibited_count: int = Field(default=0, ge=0)
    evaluation_duration_seconds: float = Field(default=0.0, ge=0.0)
    policy_rules_applied_count: int = Field(default=0, ge=0)


class PolicyDecision(BaseModel):
    """
    Standardized policy decision output payload produced by Phase 6.
    This payload is consumed by Phase 7 for Autonomous Remediation.
    """

    decision_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this policy decision."
    )

    report_id: str = Field(..., description="ID of the source Phase 5 RecommendationReport.")
    investigation_id: str = Field(..., description="ID of the original Phase 1 InvestigationPlan.")
    overall_decision: ApprovalStatus = Field(..., description="Summary decision status for the entire report.")

    approved_actions: List[ApprovalRequest] = Field(
        default_factory=list,
        description="Actions approved for automated or manual execution."
    )

    rejected_actions: List[ApprovalRequest] = Field(
        default_factory=list,
        description="Actions rejected or prohibited by policy."
    )

    approval_requests: List[ApprovalRequest] = Field(
        default_factory=list,
        description="All approval requests generated."
    )

    policy_violations: List[PolicyViolation] = Field(
        default_factory=list,
        description="List of detected policy violations."
    )

    decision_reasons: List[DecisionReason] = Field(
        default_factory=list,
        description="Detailed decision reasons per action item."
    )

    risk_classification: RiskLevel = Field(
        default=RiskLevel.MEDIUM,
        description="Highest risk level across evaluated recommendations."
    )

    metadata: DecisionMetadata = Field(
        default_factory=DecisionMetadata,
        description="Evaluation metadata and counters."
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC creation timestamp."
    )

    @property
    def summary(self) -> str:
        """Returns a human-readable summary of the policy evaluation decision."""
        return (
            f"Overall Decision: {self.overall_decision.value} | "
            f"Evaluated: {self.metadata.total_recommendations_evaluated} action(s) | "
            f"Auto-Approved: {self.metadata.auto_approved_count} | "
            f"Human Approval Required: {self.metadata.human_approval_count} | "
            f"Prohibited: {self.metadata.prohibited_count}"
        )


