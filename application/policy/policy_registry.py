"""
Purpose
-------
Registry for managing and dynamically loading policy evaluation rules.

Responsibilities
----------------
- Maintain registered policy rules.
- Provide default policy rule set initialization.

Does NOT
---------
- Evaluate rules or execute SSH commands.
"""

from typing import List

from domain.policy.rules import (
    BasePolicyRule,
    ContainerK8sPolicyRule,
    CriticalInfrastructureRule,
    ProductionProtectionRule,
    ReadOnlyAutoApprovalRule,
)


class PolicyRegistry:
    """
    Registry maintaining active domain policy rules for evaluation.
    """

    def __init__(self, register_defaults: bool = True):
        self._rules: List[BasePolicyRule] = []
        if register_defaults:
            self._register_default_rules()

    def register_rule(self, rule: BasePolicyRule) -> None:
        """Registers a single policy rule."""
        self._rules.append(rule)

    def get_rules(self) -> List[BasePolicyRule]:
        """Returns list of registered policy rules."""
        return list(self._rules)

    def _register_default_rules(self) -> None:
        """Registers default domain policy evaluation rules."""
        self.register_rule(ReadOnlyAutoApprovalRule())
        self.register_rule(ProductionProtectionRule())
        self.register_rule(CriticalInfrastructureRule())
        self.register_rule(ContainerK8sPolicyRule())
