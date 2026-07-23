"""
Purpose
-------
Primary application service for the Operational Recommendation Engine (Phase 5).

Responsibilities
----------------
- Accept Phase 4 RootCauseAnalysis payload.
- Delegate recommendation generation to an abstract RecommendationProviderInterface (Gemini, OpenAI, Claude).
- Return standardized RecommendationReport domain model for downstream policy or remediation engines.

Does NOT
---------
- Execute SSH commands or modify infrastructure directly.
- Hardcode vendor-specific LLM SDK calls.
"""

from typing import Optional

from domain.llm import RecommendationProviderInterface
from domain.rca.models import RootCauseAnalysis
from domain.recommendation.exceptions import InvalidRCAResultError
from domain.recommendation.models import RecommendationReport
from infrastructure.llm.provider_factory import get_llm_recommendation_provider


class RecommendationService:
    """
    Main Phase 5 Application Service orchestrating Operational Recommendation Reports.
    """

    def __init__(self, provider: Optional[RecommendationProviderInterface] = None):
        self.provider = provider or get_llm_recommendation_provider()

    def generate_report(self, rca: RootCauseAnalysis) -> RecommendationReport:
        """
        Generates an operational RecommendationReport from a RootCauseAnalysis payload.

        Parameters
        ----------
        rca : RootCauseAnalysis
            Root cause analysis payload produced by Phase 4 RCAService.

        Returns
        -------
        RecommendationReport
            Standardized recommendation report payload containing action guidance, risk scoring, and rollback plans.
        """
        if not rca or not isinstance(rca, RootCauseAnalysis):
            raise InvalidRCAResultError("Input must be a valid RootCauseAnalysis object.")

        return self.provider.generate_recommendations(rca)
