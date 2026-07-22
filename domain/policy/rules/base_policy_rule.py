"""
Purpose
-------
Abstract base class defining the contract for all policy rules in the Policy Engine.

Responsibilities
----------------
- Define the evaluate_action method interface for policy rules.
- Enforce decoupled and extensible policy rule implementations.

Does NOT
---------
- Hardcode business logic or execute remote commands.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from domain.policy.models import ActionPermission, ApprovalStatus, PolicyViolation
from domain.recommendation.models import Recommendation


class BasePolicyRule(ABC):
    """
    Abstract Base Class for all policy evaluation rules.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the policy rule."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable explanation of rule intent."""
        pass

    @abstractmethod
    def evaluate_action(
        self, recommendation: Recommendation
    ) -> Tuple[Optional[ApprovalStatus], Optional[ActionPermission], Optional[PolicyViolation]]:
        """
        Evaluates a single recommendation action against policy criteria.

        Parameters
        ----------
        recommendation : Recommendation
            Recommended action item from Phase 5.

        Returns
        -------
        Tuple[Optional[ApprovalStatus], Optional[ActionPermission], Optional[PolicyViolation]]
            Assigned status, permission, and optional policy violation.
        """
        pass
