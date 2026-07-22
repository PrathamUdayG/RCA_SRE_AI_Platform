"""
Purpose
-------
Worker application service responsible for executing a single InvestigationStep.

Responsibilities
----------------
- Resolve command_id using the Linux Command Registry (commands.py).
- Execute SSH command on remote server via SSH Client (ssh_client.py).
- Log execution results to PostgreSQL Audit Layer (database.py).
- Parse raw text output into structured JSON via Parser Engine (parsers.py).
- Return standardized StepExecutionResult object.

Does NOT
---------
- Manage multi-step execution order or parallel threads.
- Perform RCA or call LLM APIs.
"""

from datetime import datetime
import time
from typing import Any, Dict

from commands import get_command
from database import save_log
from domain.execution.exceptions import CommandNotFoundError
from domain.execution.models import ExecutionStatus, StepExecutionResult
from domain.investigation.models import InvestigationStep
from parsers import parse_output
from ssh_client import execute_command as ssh_execute_command


class StepExecutor:
    """
    Executes a single InvestigationStep by orchestrating Command Registry, SSH, DB Logging, and Parsers.
    """

    def execute_step(self, step: InvestigationStep) -> StepExecutionResult:
        """
        Executes one InvestigationStep and returns a StepExecutionResult.

        Parameters
        ----------
        step : InvestigationStep
            Diagnostic step definition to execute.

        Returns
        -------
        StepExecutionResult
            Result container with raw output, parsed JSON, execution time, and status.
        """
        start_time = time.time()
        executed_at = datetime.utcnow()

        # Step 1: Resolve command_id in Linux Command Registry
        command_info = get_command(step.command_id)
        if command_info is None:
            duration = round(time.time() - start_time, 3)
            return StepExecutionResult(
                step_id=step.step_id,
                order=step.order,
                command_id=step.command_id,
                linux_command=step.command_id,
                description=step.description,
                status=ExecutionStatus.FAILED,
                raw_output="",
                parsed_output={},
                error_message=f"Command key '{step.command_id}' not found in command registry.",
                execution_time_seconds=duration,
                executed_at=executed_at,
            )

        linux_command = command_info["command"]

        try:
            # Step 2: Execute command over SSH
            ssh_result = ssh_execute_command(linux_command)
            host = ssh_result.get("host", "unknown")
            raw_output = ssh_result.get("output", "")
            error_output = ssh_result.get("error", "")

            # Step 3: Log to PostgreSQL audit table (non-blocking exception handling)
            try:
                save_log(
                    host=host,
                    command=linux_command,
                    output=raw_output,
                    error=error_output,
                )
            except Exception as db_err:
                print(f"[Warning] PostgreSQL logging failed for step {step.step_id}: {db_err}")

            # Step 4: Parse raw text output into structured JSON
            parsed_json = parse_output(linux_command, raw_output)

            duration = round(time.time() - start_time, 3)
            has_error = bool(error_output and error_output.strip())

            return StepExecutionResult(
                step_id=step.step_id,
                order=step.order,
                command_id=step.command_id,
                linux_command=linux_command,
                description=step.description,
                status=ExecutionStatus.FAILED if has_error else ExecutionStatus.SUCCESS,
                raw_output=raw_output,
                parsed_output=parsed_json if isinstance(parsed_json, dict) else {"raw": parsed_json},
                error_message=error_output if has_error else None,
                execution_time_seconds=duration,
                executed_at=executed_at,
            )

        except Exception as err:
            duration = round(time.time() - start_time, 3)
            return StepExecutionResult(
                step_id=step.step_id,
                order=step.order,
                command_id=step.command_id,
                linux_command=linux_command,
                description=step.description,
                status=ExecutionStatus.FAILED,
                raw_output="",
                parsed_output={},
                error_message=str(err),
                execution_time_seconds=duration,
                executed_at=executed_at,
            )
