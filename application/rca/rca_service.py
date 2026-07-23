"""
Purpose
-------
Primary application service for the AI Root Cause Analysis Engine (Phase 4).

Responsibilities
----------------
- Accept Phase 3 CorrelationResult payload.
- Delegate AI reasoning to an abstract LLMProviderInterface (Gemini, OpenAI, Claude).
- Return standardized RootCauseAnalysis domain model for downstream recommendation engines.

Does NOT
---------
- Execute SSH commands or correlate raw infrastructure metrics.
- Hardcode vendor-specific LLM SDK calls.
"""

from typing import Optional

from domain.correlation.models import CorrelationResult
from domain.llm import LLMProviderInterface
from domain.rca.exceptions import InvalidCorrelationResultError
from domain.rca.models import RootCauseAnalysis
from infrastructure.llm.provider_factory import get_llm_rca_provider


class RCAService:
    """
    Main Phase 4 Application Service orchestrating AI Root Cause Analysis.
    """

    def __init__(self, provider: Optional[LLMProviderInterface] = None):
        self.provider = provider or get_llm_rca_provider()

    def analyze_root_cause(self, correlation_result: CorrelationResult) -> RootCauseAnalysis:
        """
        Analyzes correlated findings and returns a structured RootCauseAnalysis.

        Parameters
        ----------
        correlation_result : CorrelationResult
            Correlated operational findings produced by Phase 3 CorrelationEngine.

        Returns
        -------
        RootCauseAnalysis
            Standardized RCA payload containing primary root cause, hypotheses, and evidence links.
        """
        if not correlation_result or not isinstance(correlation_result, CorrelationResult):
            raise InvalidCorrelationResultError("Input must be a valid CorrelationResult object.")

        return self.provider.analyze_correlation(correlation_result)
