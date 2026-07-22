"""
Purpose
-------
Policy rule protecting production services and preventing dangerous or destructive operations.

Responsibilities
----------------
- Enforce human approval for service restarts, process terminations, or storage modifications.
- Prohibit destructive actions (e.g., deleting root filesystems or unvalidated purges).

Does NOT
---------
- Execute commands on remote servers.
"""

from typing import Optional, Tuple

from domain.policy.models import ActionPermission, ApprovalStatus, PolicyViolation
from domain.recommendation.models import Recommendation, RecommendationPriority, RiskLevel
from .base_policy_rule import BasePolicyRule


class ProductionProtectionRule(BasePolicyRule):
    """
    Enforces human approval for production service modifications and prohibits destructive actions.
    """

    @property
    def name(self) -> str:
        return "ProductionProtectionRule"

    @property
    def description(self) -> str:
        return "Requires human approval for production mutations and prohibits destructive actions."

    def evaluate_action(
        self, recommendation: Recommendation
    ) -> Tuple[Optional[ApprovalStatus], Optional[ActionPermission], Optional[PolicyViolation]]:
        text = f"{recommendation.title} {recommendation.description}".lower()

        # Prohibit destructive actions
        if any(term in text for term in ["rm -rf /", "delete root", "drop database", "format disk"]):
            violation = PolicyViolation(
                rule_name=self.name,
                severity="BLOCKING",
                message="Destructive system operation prohibited by production safety policy.",
                recommendation_id=recommendation.recommendation_id,
            )
            return (
                ApprovalStatus.PROHIBITED,
                ActionPermission.BLOCKED,
                violation,
            )

        # Enforce human approval for high risk or critical priority actions
        if recommendation.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) or recommendation.priority == RecommendationPriority.P1_CRITICAL:
            return (
                ApprovalStatus.HUMAN_APPROVAL_REQUIRED,
                ActionPermission.ALLOWED_MANUAL_ONLY,
                None,
            )

        # Enforce human approval for service restarts
        if any(term in text for term in ["restart", "stop", "terminate", "kill", "purge"]):
            return (
                ApprovalStatus.HUMAN_APPROVAL_REQUIRED,
                ActionPermission.ALLOWED_MANUAL_ONLY,
                None,
            )

        return None, None, None
