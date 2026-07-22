"""
Purpose:
--------
Package initializer for the Investigation Domain. Exposes core models, exceptions,
and the main InvestigationPlanner interface.

Responsibilities:
-----------------
- Expose clean public interface for the domain.

Does NOT:
---------
- Contain business logic.
- Execute SSH or external APIs.
"""

from .exceptions import (
    InvestigationError,
    InvalidQuestionError,
    PlanGenerationError,
    TemplateNotFoundError,
)
from .models import (
    ExecutionStrategy,
    InvestigationPlan,
    InvestigationPriority,
    InvestigationStatus,
    InvestigationStep,
)
from .planner import InvestigationPlanner
from .rule_engine import RuleEngine
from .strategy import StrategyEvaluator
from .template_registry import TemplateRegistry

__all__ = [
    "InvestigationError",
    "InvalidQuestionError",
    "PlanGenerationError",
    "TemplateNotFoundError",
    "ExecutionStrategy",
    "InvestigationPlan",
    "InvestigationPriority",
    "InvestigationStatus",
    "InvestigationStep",
    "InvestigationPlanner",
    "RuleEngine",
    "StrategyEvaluator",
    "TemplateRegistry",
]
