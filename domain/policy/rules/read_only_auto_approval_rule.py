"""
Purpose
-------
Policy rule for automatically approving read-only diagnostic and inspection recommendations.

Responsibilities
----------------
- Evaluate read-only, inspection, or telemetry action items.
- Assign AUTO_APPROVED status and ALLOWED_AUTOMATED permission to safe read-only actions.

Does NOT
---------
- Approve state-changing or destructive actions.
"""

from typing import Optional, Tuple

from domain.policy.models import ActionPermission, ApprovalStatus, PolicyViolation
from domain.recommendation.models import Recommendation, RecommendationCategory
from .base_policy_rule import BasePolicyRule


class ReadOnlyAutoApprovalRule(BasePolicyRule):
    """
    Auto-approves safe read-only, diagnostic, and telemetry inspection recommendations.
    """

    @property
    def name(self) -> str:
        return "ReadOnlyAutoApprovalRule"

    @property
    def description(self) -> str:
        return "Automatically approves safe read-only diagnostic and telemetry inspection actions."

    def evaluate_action(
        self, recommendation: Recommendation
    ) -> Tuple[Optional[ApprovalStatus], Optional[ActionPermission], Optional[PolicyViolation]]:
        text = f"{recommendation.title} {recommendation.description}".lower()

        # Check for explicitly read-only keywords
        read_only_keywords = ["inspect", "check", "view", "monitor", "gather", "collect", "read", "verify"]
        is_read_only = any(kw in text for kw in read_only_keywords)
        is_safe_category = recommendation.category in (RecommendationCategory.RUNBOOK, RecommendationCategory.PREVENTIVE)

        if is_read_only or is_safe_category:
            return (
                ApprovalStatus.AUTO_APPROVED,
                ActionPermission.ALLOWED_AUTOMATED,
                None,
            )

        return None, None, None
