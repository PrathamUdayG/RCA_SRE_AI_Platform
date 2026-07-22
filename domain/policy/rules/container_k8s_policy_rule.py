"""
Purpose
-------
Policy rule for evaluating Docker container restarts and Kubernetes pod scaling operations.

Responsibilities
----------------
- Evaluate container runtime and Kubernetes cluster recommendations.
- Require human approval for pod scaling or container restarts.

Does NOT
---------
- Call Docker or Kubernetes APIs directly.
"""

from typing import Optional, Tuple

from domain.policy.models import ActionPermission, ApprovalStatus, PolicyViolation
from domain.recommendation.models import Recommendation
from .base_policy_rule import BasePolicyRule


class ContainerK8sPolicyRule(BasePolicyRule):
    """
    Enforces approval workflows for Docker container restarts and Kubernetes deployment scaling.
    """

    @property
    def name(self) -> str:
        return "ContainerK8sPolicyRule"

    @property
    def description(self) -> str:
        return "Requires approval for container restarts, image updates, and Kubernetes scaling."

    def evaluate_action(
        self, recommendation: Recommendation
    ) -> Tuple[Optional[ApprovalStatus], Optional[ActionPermission], Optional[PolicyViolation]]:
        text = f"{recommendation.title} {recommendation.description} {recommendation.target_resource}".lower()

        if any(term in text for term in ["docker", "kubernetes", "kubectl", "pod scale", "container restart"]):
            return (
                ApprovalStatus.HUMAN_APPROVAL_REQUIRED,
                ActionPermission.ALLOWED_MANUAL_ONLY,
                None,
            )

        return None, None, None
