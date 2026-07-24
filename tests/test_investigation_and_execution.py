"""
Unit tests for Investigation Planner, StepExecutor, and Execution Layer (Phases A & B).
"""

import unittest
from domain.investigation import InvestigationPlanner
from domain.investigation.template_registry import TemplateRegistry
from domain.execution.models import ExecutionStatus, StepExecutionResult
from application.execution import ExecutionService, StepExecutor, SequentialRunner
from domain.investigation.models import InvestigationStep
from infrastructure.registry.command_registry import LinuxCommandRegistry
from infrastructure.registry.parser_registry import LinuxParserRegistry


class MockSSHClient:
    """Mock ISSHClient for deterministic unit testing without SSH host dependency."""
    def execute_command(self, command: str):
        if "cat /proc/loadavg" in command:
            return {"host": "mock-host", "output": "0.15 0.20 0.18 1/450 12345", "error": ""}
        if "free -m" in command:
            return {"host": "mock-host", "output": "              total        used        free      shared  buff/cache   available\nMem:           8000        2000        1000         100        5000        5500\nSwap:          2000           0        2000", "error": ""}
        if "df -h" in command:
            return {"host": "mock-host", "output": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        100G   40G   60G  40% /", "error": ""}
        return {"host": "mock-host", "output": "mock_stdout_ok", "error": ""}


class MockAuditRepository:
    """Mock PostgresAuditRepository for unit testing."""
    def save_audit_log(self, host: str, command: str, output: str, error: str) -> None:
        pass


class TestInvestigationAndExecution(unittest.TestCase):

    def test_planner_creates_valid_plan(self):
        planner = InvestigationPlanner()
        plan = planner.create_plan("Why is my server slow and unresponsive?")
        self.assertIsNotNone(plan.investigation_id)
        self.assertEqual(plan.metadata["matched_template"], "slow_server")
        self.assertGreater(len(plan.steps), 0)

        # Verify step consistency
        for step in plan.steps:
            self.assertIsNotNone(step.command_id)
            self.assertIsNotNone(step.parser_name)

    def test_step_executor_with_mock_ssh(self):
        mock_ssh = MockSSHClient()
        mock_audit = MockAuditRepository()
        executor = StepExecutor(ssh_client=mock_ssh, audit_repository=mock_audit)

        step = InvestigationStep(
            order=1,
            command_id="cpu_load",
            description="Check CPU load",
            parser_name="parse_cpu_load",
        )

        res: StepExecutionResult = executor.execute_step(step)
        self.assertEqual(res.status, ExecutionStatus.SUCCESS)
        self.assertEqual(res.parsed_output["load_average_1m"], 0.15)
        self.assertEqual(res.parsed_output["load_average_5m"], 0.20)

    def test_execution_service_end_to_end(self):
        planner = InvestigationPlanner()
        plan = planner.create_plan("Check RAM availability")

        mock_ssh = MockSSHClient()
        mock_audit = MockAuditRepository()
        step_exec = StepExecutor(ssh_client=mock_ssh, audit_repository=mock_audit)
        seq_runner = SequentialRunner(step_executor=step_exec)
        exec_service = ExecutionService(sequential_runner=seq_runner)

        exec_res = exec_service.execute_plan(plan)
        self.assertEqual(exec_res.status, ExecutionStatus.SUCCESS)
        self.assertEqual(exec_res.metrics.total_steps, len(plan.steps))
        self.assertEqual(exec_res.metrics.successful_steps, len(plan.steps))


if __name__ == "__main__":
    unittest.main()
