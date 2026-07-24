"""
Purpose:
--------
Primary application entry point for the Investigation Planning Engine (Phase 1).

Responsibilities:
-----------------
- Validate incoming natural language user questions.
- Orchestrate RuleEngine and StrategyEvaluator to construct an InvestigationPlan.
- Return fully validated InvestigationPlan domain objects.

Does NOT:
---------
- Execute SSH commands or Paramiko logic.
- Call LLM APIs or parse stdout text.
- Save records to database.
"""

from typing import Optional

from domain.capability import CapabilityAwarePlanPolicy, ServerCapabilities
from .exceptions import InvalidQuestionError, PlanGenerationError
from .models import ExecutionStrategy, InvestigationPlan, InvestigationStatus
from .rule_engine import RuleEngine
from .strategy import StrategyEvaluator
from .template_registry import TemplateRegistry


class InvestigationPlanner:
    """
    Main Domain Orchestrator responsible for producing Investigation Plans.
    """

    def __init__(
        self,
        rule_engine: Optional[RuleEngine] = None,
        strategy_evaluator: Optional[StrategyEvaluator] = None,
    ):
        template_registry = TemplateRegistry()
        self.rule_engine = rule_engine or RuleEngine(template_registry)
        self.strategy_evaluator = strategy_evaluator or StrategyEvaluator()
        self.capability_policy = CapabilityAwarePlanPolicy()

    def create_plan(
        self, user_question: str, capabilities: Optional[ServerCapabilities] = None
    ) -> InvestigationPlan:
        """
        Transforms a user's natural language question into an InvestigationPlan object.

        Parameters:
        -----------
        user_question : str
            Natural language query asked by user (e.g. "Why is my server slow?")

        Returns:
        --------
        InvestigationPlan
            A fully constructed, validated investigation plan.
        """
        if not user_question or not isinstance(user_question, str) or not user_question.strip():
            raise InvalidQuestionError("User question must be a non-empty string.")

        clean_question = user_question.strip()

        try:
            # 1. Analyze intent & generate diagnostic steps and priority
            steps, priority, template_name = self.rule_engine.match_rules(clean_question)

            capability_notice = None
            skipped_steps = []
            if capabilities:
                steps, skipped_steps = self.capability_policy.filter_steps(steps, capabilities)
                if skipped_steps:
                    capability_notice = (
                        "Technology-specific diagnostics were excluded because the required "
                        "capability was not detected. The investigation will use supported host diagnostics instead."
                    )
                if not steps:
                    steps = self.rule_engine.registry.get_template("general_health")
                    template_name = "general_health"
                    capability_notice = (
                        "The requested technology was not detected on this server. "
                        "The investigation will use supported host CPU, memory, disk, and service diagnostics instead."
                    )

            # 2. Determine execution strategy and estimated duration
            strategy, estimated_duration = self.strategy_evaluator.evaluate(steps)

            # 3. Assemble and return domain model
            plan = InvestigationPlan(
                user_question=clean_question,
                priority=priority,
                status=InvestigationStatus.PLANNED,
                execution_strategy=strategy,
                estimated_duration_seconds=estimated_duration,
                steps=steps,
                metadata={
                    "matched_template": template_name,
                    "engine_version": "1.0.0",
                    "capability_discovery_used": str(capabilities is not None),
                    "skipped_unsupported_command_ids": ",".join(skipped_steps),
                    "capability_notice": capability_notice or "",
                },
            )
            return plan

        except Exception as e:
            if isinstance(e, InvalidQuestionError):
                raise e
            raise PlanGenerationError(str(e)) from e
