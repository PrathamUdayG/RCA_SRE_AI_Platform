"""
Purpose
-------
Package exports for the Policy Engine and Approval Framework Domain.

Responsibilities
----------------
- Provide public module exports for policy domain models, exceptions, and policy rules.

Does NOT
---------
- Execute commands or modify remote infrastructure.
- Perform AI reasoning or LLM calls.
"""

from .exceptions import (
    InvalidRecommendationReportError,
    PolicyError,
    PolicyRuleEvaluationError,
)
from .models import (
    ActionPermission,
    ApprovalRequest,
    ApprovalStatus,
    DecisionMetadata,
    DecisionReason,
    PolicyDecision,
    PolicyRule,
    PolicyViolation,
    RiskLevel,
)

__all__ = [
    "PolicyError",
    "InvalidRecommendationReportError",
    "PolicyRuleEvaluationError",
    "ApprovalStatus",
    "ActionPermission",
    "RiskLevel",
    "PolicyRule",
    "PolicyViolation",
    "ApprovalRequest",
    "DecisionReason",
    "DecisionMetadata",
    "PolicyDecision",
]
