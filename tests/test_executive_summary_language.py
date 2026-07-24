"""Tests for question-first executive summary wording; no external services."""

import unittest

from application.summary.executive_summary_service import ExecutiveSummaryService
from domain.correlation.models import Evidence, Finding, FindingCategory, Severity


class TestExecutiveSummaryLanguage(unittest.TestCase):
    def test_healthy_cpu_answer_leads_with_cpu_status(self):
        finding = Finding(
            title="CPU Load Within Normal Parameters",
            category=FindingCategory.CPU,
            severity=Severity.INFO,
            confidence_score=0.99,
            summary="1-minute load average is nominal at 0.21.",
            evidences=[
                Evidence(
                    metric_name="load_average_1m",
                    observed_value=0.21,
                    threshold=1.0,
                    source_command="cat /proc/loadavg",
                )
            ],
        )

        answer = ExecutiveSummaryService._build_direct_answer(
            user_question="What is my CPU status?",
            correlation=type("Correlation", (), {"findings": [finding]})(),
            rca=None,
            recommendation=None,
        )

        self.assertTrue(answer.startswith("Your cpu status is healthy."))
        self.assertIn("1-minute load average", answer)
        self.assertNotIn("Primary Cause:", answer)

    def test_unhealthy_cpu_answer_leads_with_attention_status(self):
        finding = Finding(
            title="CPU Saturation Detected",
            category=FindingCategory.CPU,
            severity=Severity.HIGH,
            confidence_score=0.9,
            summary="1-minute load average is elevated at 4.5.",
            evidences=[
                Evidence(
                    metric_name="load_average_1m",
                    observed_value=4.5,
                    threshold=1.0,
                    source_command="cat /proc/loadavg",
                )
            ],
        )

        answer = ExecutiveSummaryService._build_direct_answer(
            user_question="What is my CPU status?",
            correlation=type("Correlation", (), {"findings": [finding]})(),
            rca=None,
            recommendation=None,
        )

        self.assertTrue(answer.startswith("Your cpu status needs attention."))
        self.assertIn("above the reference threshold", answer)


if __name__ == "__main__":
    unittest.main()
