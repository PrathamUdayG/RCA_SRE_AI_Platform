"""
Purpose
-------
Policy rule for evaluating critical infrastructure, database, and firewall modifications.

Responsibilities
----------------
- Require CRITICAL_APPROVAL_REQUIRED for database restarts or schema mutations.
- Require SECURITY_APPROVAL_REQUIRED for firewall, iptables, or network security modifications.

Does NOT
---------
- Execute commands or modify network configurations.
"""

from typing import Optional, Tuple

from domain.policy.models import ActionPermission, ApprovalStatus, PolicyViolation
from domain.recommendation.models import Recommendation
from .base_policy_rule import BasePolicyRule


class CriticalInfrastructureRule(BasePolicyRule):
    """
    Enforces specialized Critical or Security approval for database and network firewall changes.
    """

    @property
    def name(self) -> str:
        return "CriticalInfrastructureRule"

    @property
    def description(self) -> str:
        return "Requires Critical or Security approval for database, firewall, and security policy changes."

    def evaluate_action(
        self, recommendation: Recommendation
    ) -> Tuple[Optional[ApprovalStatus], Optional[ActionPermission], Optional[PolicyViolation]]:
        text = f"{recommendation.title} {recommendation.description} {recommendation.target_resource}".lower()

        # Security & Firewall modifications
        if any(term in text for term in ["firewall", "iptables", "ufw", "security group", "port block"]):
            return (
                ApprovalStatus.SECURITY_APPROVAL_REQUIRED,
                ActionPermission.ALLOWED_MANUAL_ONLY,
                None,
            )

        # Database restarts or schema mutations
        if any(term in text for term in ["database", "postgres", "mysql", "mongodb", "redis restart"]):
            return (
                ApprovalStatus.CRITICAL_APPROVAL_REQUIRED,
                ActionPermission.ALLOWED_MANUAL_ONLY,
                None,
            )

        return None, None, None
