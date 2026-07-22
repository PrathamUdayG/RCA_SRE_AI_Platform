"""
Purpose:
--------
Strategy evaluator for determining execution mode and duration estimates for investigation plans.

Responsibilities:
-----------------
- Analyze dependencies between investigation steps.
- Assign SEQUENTIAL vs PARALLEL ExecutionStrategy.
- Calculate total estimated execution time.

Does NOT:
---------
- Execute steps or manage threads/async loops.
"""

from typing import List, Tuple

from .models import ExecutionStrategy, InvestigationStep


class StrategyEvaluator:
    """
    Evaluates step dependencies to select optimal execution strategy and compute duration bounds.
    """

    def evaluate(self, steps: List[InvestigationStep]) -> Tuple[ExecutionStrategy, int]:
        """
        Evaluates list of steps and returns (ExecutionStrategy, estimated_duration_seconds).
        """
        if not steps:
            return ExecutionStrategy.SEQUENTIAL, 0

        # Check if any step has explicit prerequisites
        has_dependencies = any(len(step.depends_on) > 0 for step in steps)

        if has_dependencies:
            strategy = ExecutionStrategy.SEQUENTIAL
            estimated_duration = sum(step.timeout_seconds for step in steps)
        else:
            # Independent diagnostic steps can be safely executed in parallel
            strategy = ExecutionStrategy.PARALLEL
            max_timeout = max(step.timeout_seconds for step in steps)
            # Add small 2-second communication overhead buffer
            estimated_duration = max_timeout + 2

        return strategy, estimated_duration
