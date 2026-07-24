"""
Unit tests for Centralized LLMProviderManager and LLM Health / Executive Summary hardening.
"""

import unittest
from datetime import datetime

from domain.correlation.models import CorrelationResult, Finding, FindingCategory, Severity
from domain.health.models import ComponentStatus
from domain.rca.models import AnalysisMetadata, Hypothesis, RootCauseAnalysis
from domain.recommendation.models import RecommendationMetadata, RecommendationReport
from infrastructure.llm.provider_manager import DeterministicFallbackProvider, LLMProviderManager


class TestLLMProviderManager(unittest.TestCase):

    def setUp(self):
        self.manager = LLMProviderManager()
        self.manager.reload_providers()

    def test_singleton_instance(self):
        m1 = LLMProviderManager()
        m2 = LLMProviderManager()
        self.assertIs(m1, m2)

    def test_health_check_returns_valid_result(self):
        res = self.manager.health_check()
        self.assertEqual(res.component_name, "AI Provider")
        self.assertIn("active_provider", res.details)
        self.assertIn("active_model", res.details)
        self.assertIn(res.status, (ComponentStatus.HEALTHY, ComponentStatus.DEGRADED))

    def test_fallback_provider_direct(self):
        fallback = DeterministicFallbackProvider()
        self.assertEqual(fallback.provider_name, "Deterministic Fallback Engine")

        corr = CorrelationResult(
            execution_id="exec-1",
            investigation_id="inv-1",
            user_question="How is CPU health?",
            findings=[],
        )
        rca = fallback.analyze_correlation(corr)
        self.assertIsNotNone(rca)
        self.assertIn("Inconclusive", rca.primary_root_cause)

        summary = fallback.generate_executive_summary("How is CPU health?", corr, rca)
        self.assertIn("How is CPU health?", summary)

    def test_executive_summary_generation_via_manager(self):
        corr = CorrelationResult(
            execution_id="exec-2",
            investigation_id="inv-2",
            user_question="Why is my server slow?",
            findings=[
                Finding(
                    finding_id="f-1",
                    category=FindingCategory.CPU,
                    severity=Severity.HIGH,
                    title="High CPU Saturation",
                    summary="CPU load 1m average is 4.5 above threshold 1.0",
                    confidence_score=0.9,
                    affected_resources=["CPU"],
                )
            ],
        )


        rca = RootCauseAnalysis(
            correlation_id="c-1",
            investigation_id="inv-2",
            user_question="Why is my server slow?",
            primary_root_cause="Process cpu_hog consuming 95% CPU",
            overall_confidence=0.9,
            summary="CPU is saturated by rogue process.",
            primary_hypothesis=Hypothesis(title="CPU Saturation", description="Process cpu_hog high CPU", likelihood_score=0.9),
            metadata=AnalysisMetadata(provider_used="LLMProviderManagerTest"),
        )


        rec = RecommendationReport(
            analysis_id="rca-1",
            investigation_id="inv-2",
            user_question="Why is my server slow?",
            primary_root_cause_ref="Process cpu_hog consuming 95% CPU",
            executive_summary="Terminate process cpu_hog (PID 1234).",
            metadata=RecommendationMetadata(provider_used="LLMProviderManagerTest"),
        )


        exec_summary = self.manager.generate_executive_summary(
            user_question="Why is my server slow?",
            correlation_result=corr,
            rca=rca,
            recommendation=rec,
        )

        self.assertIsInstance(exec_summary, str)
        self.assertTrue(len(exec_summary) > 20)
        self.assertIn("Why is my server slow?", exec_summary)


if __name__ == "__main__":
    unittest.main()
