"""
Purpose
-------
Registry for managing and dynamically loading domain correlation rules.

Responsibilities
----------------
- Maintain registered correlation rules.
- Provide default rule set initialization.

Does NOT
---------
- Evaluate rules or execute SSH commands.
"""

from typing import List

from domain.correlation.rules import (
    BaseCorrelationRule,
    CPUSaturationRule,
    ContainerHealthRule,
    DiskCapacityRule,
    MemoryPressureRule,
    NetworkSocketsRule,
    ServiceFailureRule,
)


class RuleRegistry:
    """
    Registry maintaining active domain correlation rules for evaluation.
    """

    def __init__(self, register_defaults: bool = True):
        self._rules: List[BaseCorrelationRule] = []
        if register_defaults:
            self._register_default_rules()

    def register_rule(self, rule: BaseCorrelationRule) -> None:
        """Registers a single domain correlation rule."""
        self._rules.append(rule)

    def get_rules(self) -> List[BaseCorrelationRule]:
        """Returns list of all registered correlation rules."""
        return list(self._rules)

    def _register_default_rules(self) -> None:
        """Registers default domain correlation rules."""
        self.register_rule(CPUSaturationRule())
        self.register_rule(MemoryPressureRule())
        self.register_rule(DiskCapacityRule())
        self.register_rule(NetworkSocketsRule())
        self.register_rule(ServiceFailureRule())
        self.register_rule(ContainerHealthRule())
