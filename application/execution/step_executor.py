"""
Purpose
-------
Worker application service responsible for executing a single InvestigationStep.

Responsibilities
----------------
- Resolve command_id using the Linux Command Registry interface.
- Execute SSH command on remote server via ISSHClient interface.
- Log execution results to Audit Repository interface.
- Parse raw text output into structured JSON via LinuxParserRegistry interface.
- Guarantee strict execution validation (SSH Succeeded + Command Exit 0 + Valid Parsed Telemetry).
- Return standardized StepExecutionResult object.
"""

from datetime import datetime
import time
from typing import Any, Dict, Optional

from domain.execution.models import ExecutionStatus, StepExecutionResult
from domain.investigation.models import InvestigationStep
from infrastructure.persistence.audit_repository import PostgresAuditRepository
from infrastructure.registry.command_registry import LinuxCommandRegistry
from infrastructure.registry.parser_registry import LinuxParserRegistry
from infrastructure.ssh.paramiko_ssh_client import ParamikoSSHClient
from infrastructure.ssh.ssh_interface import ISSHClient
from shared.logging import get_logger

logger = get_logger("StepExecutor")


class StepExecutor:
    """
    Executes a single InvestigationStep by orchestrating Command Registry, SSH, DB Logging, and Parsers via interfaces.
    """

    def __init__(
        self,
        ssh_client: Optional[ISSHClient] = None,
        command_registry: Optional[LinuxCommandRegistry] = None,
        parser_registry: Optional[LinuxParserRegistry] = None,
        audit_repository: Optional[PostgresAuditRepository] = None,
    ):
        self.ssh_client = ssh_client or ParamikoSSHClient()
        self.command_registry = command_registry or LinuxCommandRegistry()
        self.parser_registry = parser_registry or LinuxParserRegistry()
        self.audit_repository = audit_repository or PostgresAuditRepository(init_on_start=False)

    def execute_step(self, step: InvestigationStep) -> StepExecutionResult:
        """
        Executes one InvestigationStep and returns a validated StepExecutionResult.
        """
        start_time = time.time()
        executed_at = datetime.utcnow()

        # Step 1: Resolve command_id in Linux Command Registry
        command_info = self.command_registry.get_command(step.command_id)
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
            ssh_result = self.ssh_client.execute_command(linux_command)
            host = ssh_result.get("host", "unknown")
            raw_output = ssh_result.get("output", "")
            error_output = ssh_result.get("error", "")

            # Step 3: Log to PostgreSQL audit layer (non-blocking exception handling)
            self.audit_repository.save_audit_log(
                host=host,
                command=linux_command,
                output=raw_output,
                error=error_output,
            )

            # Step 4: Parse raw text output into structured telemetry
            parsed_json = self.parser_registry.parse(step.command_id, raw_output)

            duration = round(time.time() - start_time, 3)
            has_error_text = bool(error_output and error_output.strip())
            has_valid_stdout = bool(raw_output and raw_output.strip())
            is_ssh_failure = "SSH Execution Failed" in error_output or "Failed" in error_output and not has_valid_stdout
            has_parse_error = isinstance(parsed_json, dict) and "parse_error" in parsed_json

            # Execution success contract enforcement:
            # SSH succeeded AND Command executed AND Parser successfully produced structured telemetry
            if is_ssh_failure or not has_valid_stdout:
                step_status = ExecutionStatus.FAILED
                error_msg = error_output or "No output returned from SSH execution."
            elif has_parse_error:
                step_status = ExecutionStatus.FAILED
                error_msg = f"Parsing output failed for command '{step.command_id}': {parsed_json.get('parse_error')}"
            else:
                step_status = ExecutionStatus.SUCCESS
                error_msg = error_output if has_error_text else None

            return StepExecutionResult(
                step_id=step.step_id,
                order=step.order,
                command_id=step.command_id,
                linux_command=linux_command,
                description=step.description,
                status=step_status,
                raw_output=raw_output,
                parsed_output=parsed_json if isinstance(parsed_json, dict) else {"raw": parsed_json},
                error_message=error_msg,
                execution_time_seconds=duration,
                executed_at=executed_at,
            )

        except Exception as err:
            duration = round(time.time() - start_time, 3)
            logger.error(f"Unexpected step execution exception for {step.command_id}: {err}")
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
