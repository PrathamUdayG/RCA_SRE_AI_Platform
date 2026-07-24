"""
Unit tests for Presentation Layer rendering functions and defensive property helpers.
"""

import unittest
from presentation.streamlit.app import safe_get, _render_executive_summary, _render_tab_policy, _render_tab_guidance
from domain.policy.models import ApprovalRequest, ApprovalStatus, ActionPermission, DecisionMetadata, PolicyDecision, RiskLevel
from domain.report.models import ExecutiveSummary, InvestigationReport


class TestPresentationLayer(unittest.TestCase):

    def test_safe_get_helper(self):
        """Test safe_get dereferencing nested objects, dicts, enums, and None values."""
        self.assertEqual(safe_get(None, "attr"), "N/A")
        self.assertEqual(safe_get(ApprovalStatus.AUTO_APPROVED, "value"), "AUTO_APPROVED")

        req = ApprovalRequest(
            recommendation_id="rec-1",
            action_title="Restart Service",
            target_resource="nginx",
            approval_status=ApprovalStatus.AUTO_APPROVED,
            permission=ActionPermission.ALLOWED_AUTOMATED,
            required_role="Senior SRE",
            risk_level=RiskLevel.LOW,
        )

        self.assertEqual(safe_get(req, "action_title"), "Restart Service")
        self.assertEqual(safe_get(req, "recommendation_title"), "Restart Service")
        self.assertEqual(safe_get(req, "approval_status"), "AUTO_APPROVED")
        self.assertEqual(safe_get(req, "risk_level"), "LOW")
        self.assertEqual(safe_get(req, "non_existent_field", "fallback"), "fallback")

    def test_policy_decision_summary_and_rendering(self):
        """Test PolicyDecision summary property and defensive rendering."""
        decision = PolicyDecision(
            report_id="rep-1",
            investigation_id="inv-1",
            overall_decision=ApprovalStatus.AUTO_APPROVED,
            approved_actions=[],
            rejected_actions=[],
            approval_requests=[],
            policy_violations=[],
            decision_reasons=[],
            risk_classification=RiskLevel.LOW,
            metadata=DecisionMetadata(
                total_recommendations_evaluated=2,
                auto_approved_count=2,
                human_approval_count=0,
                prohibited_count=0,
            ),
        )

        self.assertIn("AUTO_APPROVED", decision.summary)
        self.assertEqual(safe_get(decision, "summary"), decision.summary)


if __name__ == "__main__":
    unittest.main()
