"""
Purpose
-------
Abstract base class defining the contract for all domain correlation rules.

Responsibilities
----------------
- Define the evaluate method interface for correlation rules.
- Enforce clean separation of independent rule implementations.

Does NOT
---------
- Implement specific domain heuristics or execute network calls.
"""

from abc import ABC, abstractmethod
from typing import List

from domain.execution.models import StepExecutionResult
from domain.correlation.models import Finding


class BaseCorrelationRule(ABC):
    """
    Abstract Base Class for all domain correlation rules.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name identifier of the rule."""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Domain category of the rule (e.g. CPU, MEMORY, DISK)."""
        pass

    @abstractmethod
    def evaluate(self, step_results: List[StepExecutionResult]) -> List[Finding]:
        """
        Evaluates step execution results and returns a list of operational Findings.

        Parameters
        ----------
        step_results : List[StepExecutionResult]
            Execution step results from Phase 2.

        Returns
        -------
        List[Finding]
            Zero or more correlated operational findings.
        """
        pass
