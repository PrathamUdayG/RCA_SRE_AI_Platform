"""
Purpose
-------
Primary application orchestrator for the Data Correlation Engine (Phase 3).

Responsibilities
----------------
- Accept InvestigationExecutionResult payload from Phase 2.
- Execute registered domain correlation rules via RuleRegistry.
- Synthesize findings, evidence, severity counts, and metadata.
- Return standardized CorrelationResult object passed to Phase 4.

Does NOT
---------
- Execute SSH commands or call LLM APIs.
- Perform Root Cause Analysis or generate recommendations.
"""

from datetime import datetime
import time
from typing import List, Optional

from domain.correlation.exceptions import InvalidExecutionResultError, RuleEvaluationError
from domain.correlation.models import (
    CorrelationMetadata,
    CorrelationResult,
    Finding,
    Severity,
)
from domain.execution.models import InvestigationExecutionResult

from .rule_registry import RuleRegistry


class CorrelationService:
    """
    Main Phase 3 Application Service orchestrating data correlation and finding synthesis.
    """

    def __init__(self, rule_registry: Optional[RuleRegistry] = None):
        self.rule_registry = rule_registry or RuleRegistry()

    def correlate(self, execution_result: InvestigationExecutionResult) -> CorrelationResult:
        """
        Correlates execution step results into structured operational findings.

        Parameters
        ----------
        execution_result : InvestigationExecutionResult
            Execution results container produced by Phase 2 Multi-Command Execution Engine.

        Returns
        -------
        CorrelationResult
            Standardized correlation result payload containing operational findings and evidence.
        """
        if not execution_result or not isinstance(execution_result, InvestigationExecutionResult):
            raise InvalidExecutionResultError("Input execution_result must be a valid InvestigationExecutionResult.")

        start_time = time.time()
        executed_at = datetime.utcnow()

        all_findings: List[Finding] = []
        rules = self.rule_registry.get_rules()

        for rule in rules:
            try:
                findings = rule.evaluate(execution_result.step_results)
                if findings:
                    all_findings.extend(findings)
            except Exception as exc:
                raise RuleEvaluationError(rule.name, str(exc)) from exc

        duration = round(time.time() - start_time, 4)

        # Compute metadata statistics
        critical = sum(1 for f in all_findings if f.severity == Severity.CRITICAL)
        high = sum(1 for f in all_findings if f.severity == Severity.HIGH)
        medium = sum(1 for f in all_findings if f.severity == Severity.MEDIUM)
        low = sum(1 for f in all_findings if f.severity == Severity.LOW)
        info = sum(1 for f in all_findings if f.severity == Severity.INFO)

        metadata = CorrelationMetadata(
            total_findings=len(all_findings),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            info_count=info,
            evaluation_time_seconds=duration,
            rules_evaluated=len(rules),
        )

        return CorrelationResult(
            execution_id=execution_result.execution_id,
            investigation_id=execution_result.investigation_id,
            user_question=execution_result.user_question,
            findings=all_findings,
            metadata=metadata,
            created_at=executed_at,
        )
