"""Tests for the artifact-backed Copilot workspace; no SSH, DB, or LLM calls."""

import unittest

from application.copilot import ConversationService, InvestigationContextService
from domain.correlation.models import CorrelationResult, Evidence, Finding, FindingCategory, Severity
from domain.rca.models import AnalysisMetadata, Hypothesis, RootCauseAnalysis
from domain.report.models import ExecutiveSummary, InvestigationReport
from infrastructure.persistence.in_memory_investigation_context_repository import InMemoryInvestigationContextRepository


class TestCopilotWorkspace(unittest.TestCase):
    def setUp(self):
        evidence = Evidence(
            metric_name="load_average_1m",
            observed_value=4.5,
            threshold=1.0,
            source_command="cat /proc/loadavg",
        )
        finding = Finding(
            title="CPU Saturation Detected",
            category=FindingCategory.CPU,
            severity=Severity.HIGH,
            confidence_score=0.9,
            summary="Load average is above the configured threshold.",
            evidences=[evidence],
        )
        correlation = CorrelationResult(
            execution_id="execution-1",
            investigation_id="investigation-1",
            user_question="Why is CPU high?",
            findings=[finding],
        )
        rca = RootCauseAnalysis(
            correlation_id=correlation.correlation_id,
            investigation_id="investigation-1",
            user_question="Why is CPU high?",
            primary_root_cause="A CPU-bound process saturated available compute capacity.",
            overall_confidence=0.9,
            summary="High load was correlated with CPU saturation.",
            primary_hypothesis=Hypothesis(
                title="CPU saturation",
                description="A process is consuming the available CPU capacity.",
                likelihood_score=0.9,
                is_primary=True,
            ),
            metadata=AnalysisMetadata(provider_used="test"),
        )
        self.report = InvestigationReport(
            report_id="report-1",
            user_question="Why is CPU high?",
            executive_summary=ExecutiveSummary(
                user_question="Why is CPU high?",
                direct_answer="CPU demand is currently high.",
                confidence_score=0.9,
                primary_root_cause=rca.primary_root_cause,
            ),
            correlation=correlation,
            rca=rca,
        )
        self.repository = InMemoryInvestigationContextRepository()
        self.context_service = InvestigationContextService(self.repository)
        self.conversation_service = ConversationService(self.repository)

    def test_capture_generates_context_aware_questions(self):
        context = self.context_service.capture(self.report)

        self.assertEqual(context.investigation_id, "report-1")
        self.assertIn("Explain load average.", context.suggested_questions)
        self.assertIs(self.repository.get_context("report-1"), context)

    def test_follow_up_is_grounded_in_saved_evidence(self):
        self.context_service.capture(self.report)

        response = self.conversation_service.answer_follow_up("report-1", "Why is this happening?")

        self.assertIn("CPU-bound process", response.content)
        self.assertEqual(response.citations[0].metric_name, "load_average_1m")
        self.assertEqual(len(self.repository.list_messages("report-1")), 2)

    def test_unknown_context_is_rejected_without_execution(self):
        with self.assertRaises(KeyError):
            self.conversation_service.answer_follow_up("unknown", "Why?")


if __name__ == "__main__":
    unittest.main()
