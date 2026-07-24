"""
Unit tests for Correlation Engine and End-to-End Investigation Workflow (Phases C & D).
"""

import unittest
from domain.execution.models import ExecutionMetrics, ExecutionStatus, InvestigationExecutionResult, StepExecutionResult
from domain.correlation.models import FindingCategory, Severity
from application.correlation import CorrelationService
from application.workflow import InvestigationWorkflow
from domain.report.models import InvestigationReport


class TestCorrelationAndFullPipeline(unittest.TestCase):

    def test_correlation_rules_with_high_memory_telemetry(self):
        step_res = StepExecutionResult(
            step_id="step-1",
            order=1,
            command_id="memory_usage",
            linux_command="free -m",
            description="Check RAM",
            status=ExecutionStatus.SUCCESS,
            raw_output="Mem: 8000 7500 500 100 500 500\nSwap: 2000 600 1400",
            parsed_output={
                "memory": {"total_mb": 8000, "used_mb": 7500, "free_mb": 500, "available_mb": 500},
                "swap": {"total_mb": 2000, "used_mb": 600, "free_mb": 1400},
            },
        )

        exec_payload = InvestigationExecutionResult(
            investigation_id="inv-123",
            user_question="Why is RAM high?",
            status=ExecutionStatus.SUCCESS,
            metrics=ExecutionMetrics(total_steps=1, successful_steps=1),
            step_results=[step_res],
        )

        corr_service = CorrelationService()
        corr_result = corr_service.correlate(exec_payload)

        self.assertGreater(len(corr_result.findings), 0)
        mem_finding = next((f for f in corr_result.findings if f.category == FindingCategory.MEMORY), None)
        self.assertIsNotNone(mem_finding)
        self.assertIn(mem_finding.severity, (Severity.HIGH, Severity.CRITICAL))

    def test_healthy_system_correlation(self):
        step_res = StepExecutionResult(
            step_id="step-1",
            order=1,
            command_id="cpu_load",
            linux_command="cat /proc/loadavg",
            description="Check load",
            status=ExecutionStatus.SUCCESS,
            raw_output="0.10 0.15 0.12 1/400 1234",
            parsed_output={"load_average_1m": 0.10, "load_average_5m": 0.15, "load_average_15m": 0.12},
        )

        exec_payload = InvestigationExecutionResult(
            investigation_id="inv-123",
            user_question="Is CPU healthy?",
            status=ExecutionStatus.SUCCESS,
            metrics=ExecutionMetrics(total_steps=1, successful_steps=1),
            step_results=[step_res],
        )

        corr_service = CorrelationService()
        corr_result = corr_service.correlate(exec_payload)

        info_finding = next((f for f in corr_result.findings if f.severity == Severity.INFO), None)
        self.assertIsNotNone(info_finding)
        self.assertEqual(info_finding.title, "CPU Load Within Normal Parameters")

    def test_full_investigation_workflow(self):
        workflow = InvestigationWorkflow()
        report: InvestigationReport = workflow.execute_investigation("Why is my server slow and unresponsive?")

        self.assertIsNotNone(report.report_id)
        self.assertIsNotNone(report.executive_summary)
        self.assertIsNotNone(report.plan)
        self.assertIsNotNone(report.execution)
        self.assertIsNotNone(report.correlation)
        self.assertIsNotNone(report.rca)
        self.assertIsNotNone(report.recommendation)
        self.assertIsNotNone(report.policy_decision)

        # Verify executive summary structure
        self.assertTrue(len(report.executive_summary.direct_answer) > 0)
        self.assertIn(report.executive_summary.investigation_status, ("SUCCESS", "PARTIAL_SUCCESS", "FAILED", "INCONCLUSIVE"))


if __name__ == "__main__":
    unittest.main()
