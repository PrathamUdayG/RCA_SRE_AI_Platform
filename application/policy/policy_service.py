"""
Purpose
-------
Primary application service for the Policy Engine & Approval Framework (Phase 6).

Responsibilities
----------------
- Accept RecommendationReport payload from Phase 5.
- Evaluate each recommended action against active PolicyRules via PolicyRegistry.
- Categorize actions into Approved, Rejected, and Human Approval Required.
- Return standardized PolicyDecision object for downstream autonomous remediation engines.

Does NOT
---------
- Execute SSH commands or modify infrastructure directly.
- Call LLM APIs.
"""

from datetime import datetime
import time
from typing import List, Optional

from domain.policy.exceptions import InvalidRecommendationReportError, PolicyRuleEvaluationError
from domain.policy.models import (
    ActionPermission,
    ApprovalRequest,
    ApprovalStatus,
    DecisionMetadata,
    DecisionReason,
    PolicyDecision,
    PolicyViolation,
    RiskLevel,
)
from domain.recommendation.models import RecommendationReport

from .policy_registry import PolicyRegistry


class PolicyService:
    """
    Main Phase 6 Application Service orchestrating policy evaluation and approval decisions.
    """

    def __init__(self, policy_registry: Optional[PolicyRegistry] = None):
        self.policy_registry = policy_registry or PolicyRegistry()

    def evaluate_report(self, report: RecommendationReport) -> PolicyDecision:
        """
        Evaluates an operational RecommendationReport against active security and operational policies.

        Parameters
        ----------
        report : RecommendationReport
            Recommendation report produced by Phase 5 RecommendationService.

        Returns
        -------
        PolicyDecision
            Standardized policy decision output container containing approval statuses and permissions.
        """
        if not report or not isinstance(report, RecommendationReport):
            raise InvalidRecommendationReportError("Input must be a valid RecommendationReport object.")

        start_time = time.time()
        executed_at = datetime.utcnow()

        approved_requests: List[ApprovalRequest] = []
        rejected_requests: List[ApprovalRequest] = []
        all_requests: List[ApprovalRequest] = []
        violations: List[PolicyViolation] = []
        reasons: List[DecisionReason] = []

        rules = self.policy_registry.get_rules()
        highest_risk = RiskLevel.LOW

        for recommendation in report.recommended_actions:
            assigned_status: Optional[ApprovalStatus] = None
            assigned_permission: Optional[ActionPermission] = None
            applied_rule_name = "DefaultPolicy"

            # Track highest risk level observed
            if recommendation.risk_level == RiskLevel.CRITICAL:
                highest_risk = RiskLevel.CRITICAL
            elif recommendation.risk_level == RiskLevel.HIGH and highest_risk != RiskLevel.CRITICAL:
                highest_risk = RiskLevel.HIGH
            elif recommendation.risk_level == RiskLevel.MEDIUM and highest_risk not in (RiskLevel.CRITICAL, RiskLevel.HIGH):
                highest_risk = RiskLevel.MEDIUM

            # Evaluate recommendation against registered policy rules
            for rule in rules:
                try:
                    status, permission, violation = rule.evaluate_action(recommendation)
                    if status is not None:
                        assigned_status = status
                        assigned_permission = permission
                        applied_rule_name = rule.name
                        if violation:
                            violations.append(violation)
                        break
                except Exception as exc:
                    raise PolicyRuleEvaluationError(rule.name, str(exc)) from exc

            # Default fallback if no specific rule matched
            if assigned_status is None:
                if recommendation.requires_human_approval:
                    assigned_status = ApprovalStatus.HUMAN_APPROVAL_REQUIRED
                    assigned_permission = ActionPermission.ALLOWED_MANUAL_ONLY
                else:
                    assigned_status = ApprovalStatus.AUTO_APPROVED
                    assigned_permission = ActionPermission.ALLOWED_AUTOMATED

            role = self._determine_required_role(assigned_status, recommendation.required_skill_level)
            rejection = "Prohibited by safety policy" if assigned_status in (ApprovalStatus.PROHIBITED, ApprovalStatus.REJECTED) else None

            request = ApprovalRequest(
                recommendation_id=recommendation.recommendation_id,
                action_title=recommendation.title,
                target_resource=recommendation.target_resource,
                approval_status=assigned_status,
                permission=assigned_permission,
                required_role=role,
                risk_level=recommendation.risk_level,
                rejection_reason=rejection,
            )

            all_requests.append(request)

            if assigned_status in (ApprovalStatus.PROHIBITED, ApprovalStatus.REJECTED):
                rejected_requests.append(request)
            else:
                approved_requests.append(request)

            reasons.append(
                DecisionReason(
                    recommendation_id=recommendation.recommendation_id,
                    reason_text=f"Assigned status '{assigned_status.value}' with permission '{assigned_permission.value}'.",
                    policy_applied=applied_rule_name,
                )
            )

        duration = round(time.time() - start_time, 4)

        if not all_requests:
            reasons.append(
                DecisionReason(
                    recommendation_id="NONE",
                    reason_text="No actionable recommendations available — investigation evidence was insufficient.",
                    policy_applied="DefaultPolicy",
                )
            )

        # Compute overall decision status
        if any(r.approval_status == ApprovalStatus.PROHIBITED for r in all_requests):
            overall_decision = ApprovalStatus.PROHIBITED
        elif any(r.approval_status in (ApprovalStatus.HUMAN_APPROVAL_REQUIRED, ApprovalStatus.CRITICAL_APPROVAL_REQUIRED, ApprovalStatus.SECURITY_APPROVAL_REQUIRED) for r in all_requests):
            overall_decision = ApprovalStatus.HUMAN_APPROVAL_REQUIRED
        else:
            overall_decision = ApprovalStatus.AUTO_APPROVED

        auto_count = sum(1 for r in all_requests if r.approval_status == ApprovalStatus.AUTO_APPROVED)
        human_count = sum(1 for r in all_requests if r.approval_status in (ApprovalStatus.HUMAN_APPROVAL_REQUIRED, ApprovalStatus.CRITICAL_APPROVAL_REQUIRED, ApprovalStatus.SECURITY_APPROVAL_REQUIRED))
        prohibited_count = sum(1 for r in all_requests if r.approval_status in (ApprovalStatus.PROHIBITED, ApprovalStatus.REJECTED))

        metadata = DecisionMetadata(
            total_recommendations_evaluated=len(report.recommended_actions),
            auto_approved_count=auto_count,
            human_approval_count=human_count,
            prohibited_count=prohibited_count,
            evaluation_duration_seconds=duration,
            policy_rules_applied_count=len(rules),
        )

        return PolicyDecision(
            report_id=report.report_id,
            investigation_id=report.investigation_id,
            overall_decision=overall_decision,
            approved_actions=approved_requests,
            rejected_actions=rejected_requests,
            approval_requests=all_requests,
            policy_violations=violations,
            decision_reasons=reasons,
            risk_classification=highest_risk,
            metadata=metadata,
            created_at=executed_at,
        )

    def _determine_required_role(self, status: ApprovalStatus, requested_skill: str) -> str:
        """Determines the required authorized role based on approval status."""
        if status == ApprovalStatus.AUTO_APPROVED:
            return "Automated SRE System"
        if status == ApprovalStatus.SECURITY_APPROVAL_REQUIRED:
            return "Security Administrator"
        if status == ApprovalStatus.CRITICAL_APPROVAL_REQUIRED:
            return "Principal SRE / Tech Lead"
        if status == ApprovalStatus.PROHIBITED:
            return "Blocked (No Authorized Role)"
        return requested_skill or "Senior SRE"
