"""
Purpose
-------
Runner service executing investigation steps sequentially in strict sequence order.

Responsibilities
----------------
- Sort investigation steps by execution order.
- Invoke StepExecutor sequentially for each step.
- Support partial failure handling (continue executing independent steps).
- Collect ordered list of StepExecutionResult objects.

Does NOT
---------
- Use multi-threading or parallel tasks.
- Perform RCA or LLM reasoning.
"""

from typing import List, Optional

from domain.execution.models import StepExecutionResult
from domain.investigation.models import InvestigationStep

from .step_executor import StepExecutor


class SequentialRunner:
    """
    Executes investigation steps sequentially in order.
    """

    def __init__(self, step_executor: Optional[StepExecutor] = None):
        self.step_executor = step_executor or StepExecutor()

    def run(self, steps: List[InvestigationStep]) -> List[StepExecutionResult]:
        """
        Executes a list of investigation steps sequentially.

        Parameters
        ----------
        steps : List[InvestigationStep]
            List of diagnostic steps to execute.

        Returns
        -------
        List[StepExecutionResult]
            Ordered list of results for each executed step.
        """
        if not steps:
            return []

        sorted_steps = sorted(steps, key=lambda s: s.order)
        results: List[StepExecutionResult] = []

        for step in sorted_steps:
            result = self.step_executor.execute_step(step)
            results.append(result)

        return results
