"""
Purpose
-------
Primary orchestration workflow for the AI SRE Platform.

Responsibilities
----------------
- Execute end-to-end investigation pipeline across all Phase 1-6 engines:
  User Request -> Planner (P1) -> Execution Engine (P2) -> Correlation Engine (P3)
  -> AI RCA Engine (P4) -> Recommendation Engine (P5) -> Policy Engine (P6) -> Unified InvestigationReport.

Does NOT
---------
- Implement low-level infrastructure code directly.
"""

import time
from typing import Optional

from application.correlation import CorrelationService
from application.execution import ExecutionService
from application.policy import PolicyService
from application.rca import RCAService
from application.recommendation import RecommendationService
from domain.investigation import InvestigationPlanner
from domain.report.models import InvestigationReport
from shared.logging import get_logger

logger = get_logger("InvestigationWorkflow")


class InvestigationWorkflow:
    """
    Main Orchestration Workflow for end-to-end AI SRE Incident Investigations.
    """

    def __init__(
        self,
        planner: Optional[InvestigationPlanner] = None,
        execution_service: Optional[ExecutionService] = None,
        correlation_service: Optional[CorrelationService] = None,
        rca_service: Optional[RCAService] = None,
        recommendation_service: Optional[RecommendationService] = None,
        policy_service: Optional[PolicyService] = None,
    ):
        self.planner = planner or InvestigationPlanner()
        self.execution_service = execution_service or ExecutionService()
        self.correlation_service = correlation_service or CorrelationService()
        self.rca_service = rca_service or RCAService()
        self.recommendation_service = recommendation_service or RecommendationService()
        self.policy_service = policy_service or PolicyService()

    def execute_investigation(self, user_question: str) -> InvestigationReport:
        """
        Executes complete end-to-end investigation pipeline for a natural language user query.

        Parameters
        ----------
        user_question : str
            Natural language user query (e.g. "Why is my server slow?")

        Returns
        -------
        InvestigationReport
            Unified report payload containing plan, execution metrics, correlated findings,
            root cause analysis, operational guidance, and policy decisions.
        """
        start_time = time.time()
        logger.info(f"Starting end-to-end investigation workflow for query: '{user_question}'")

        # Step 1: Phase 1 Investigation Planning
        logger.info("[Stage 1/6] Generating Investigation Plan...")
        plan = self.planner.create_plan(user_question)

        # Step 2: Phase 2 Multi-Command Execution
        logger.info(f"[Stage 2/6] Executing {len(plan.steps)} investigation step(s)...")
        execution = self.execution_service.execute_plan(plan)

        # Step 3: Phase 3 Data Correlation
        logger.info("[Stage 3/6] Correlating diagnostic step observations...")
        correlation = self.correlation_service.correlate(execution)

        # Step 4: Phase 4 AI Root Cause Analysis
        logger.info("[Stage 4/6] Performing AI Root Cause Analysis...")
        rca = self.rca_service.analyze_root_cause(correlation)

        # Step 5: Phase 5 Operational Recommendation Engine
        logger.info("[Stage 5/6] Generating operational recommendations...")
        recommendation = self.recommendation_service.generate_report(rca)

        # Step 6: Phase 6 Policy Engine & Approval Framework
        logger.info("[Stage 6/6] Evaluating recommendations against policy framework...")
        policy_decision = self.policy_service.evaluate_report(recommendation)

        total_duration = round(time.time() - start_time, 3)
        logger.info(f"Completed investigation workflow in {total_duration}s.")

        overall_status = "SUCCESS"
        if execution.status.value in ("FAILED", "PARTIAL_SUCCESS"):
            overall_status = execution.status.value

        return InvestigationReport(
            user_question=user_question,
            status=overall_status,
            total_execution_time_seconds=total_duration,
            plan=plan,
            execution=execution,
            correlation=correlation,
            rca=rca,
            recommendation=recommendation,
            policy_decision=policy_decision,
            metadata={
                "workflow_version": "1.0.0",
                "total_stages_completed": 6,
            },
        )
