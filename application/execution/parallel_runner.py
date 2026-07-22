"""
Purpose
-------
Runner service executing independent investigation steps in parallel using thread pools.

Responsibilities
----------------
- Execute independent steps concurrently via ThreadPoolExecutor.
- Enforce per-step timeout limits.
- Sort and return results by original step order.

Does NOT
---------
- Perform RCA or LLM reasoning.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from domain.execution.models import ExecutionStatus, StepExecutionResult
from domain.investigation.models import InvestigationStep

from .step_executor import StepExecutor


class ParallelRunner:
    """
    Executes independent investigation steps concurrently using a worker thread pool.
    """

    def __init__(
        self,
        max_workers: int = 5,
        step_executor: Optional[StepExecutor] = None,
    ):
        self.max_workers = max_workers
        self.step_executor = step_executor or StepExecutor()

    def run(self, steps: List[InvestigationStep]) -> List[StepExecutionResult]:
        """
        Executes a list of independent investigation steps in parallel.

        Parameters
        ----------
        steps : List[InvestigationStep]
            List of diagnostic steps to execute concurrently.

        Returns
        -------
        List[StepExecutionResult]
            Ordered list of results matching step sequence order.
        """
        if not steps:
            return []

        results: List[StepExecutionResult] = []

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(steps))) as executor:
            future_to_step = {
                executor.submit(self.step_executor.execute_step, step): step
                for step in steps
            }

            for future in as_completed(future_to_step):
                step = future_to_step[future]
                try:
                    res = future.result(timeout=step.timeout_seconds + 5)
                    results.append(res)
                except Exception as exc:
                    results.append(
                        StepExecutionResult(
                            step_id=step.step_id,
                            order=step.order,
                            command_id=step.command_id,
                            linux_command=step.command_id,
                            description=step.description,
                            status=ExecutionStatus.TIMEOUT if "timeout" in str(exc).lower() else ExecutionStatus.FAILED,
                            raw_output="",
                            parsed_output={},
                            error_message=f"Parallel worker exception: {exc}",
                            execution_time_seconds=float(step.timeout_seconds),
                        )
                    )

        # Sort results back into step order
        return sorted(results, key=lambda r: r.order)
