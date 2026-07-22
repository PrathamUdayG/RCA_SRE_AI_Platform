"""
Purpose
-------
Abstract provider interface decoupling Recommendation business logic from concrete LLM vendor SDKs.

Responsibilities
----------------
- Define the contract for AI Recommendation providers (Gemini, OpenAI, Claude, Local LLMs).

Does NOT
---------
- Depend on specific LLM vendor SDKs or environment variables.
"""

from abc import ABC, abstractmethod

from domain.rca.models import RootCauseAnalysis
from .models import RecommendationReport


class RecommendationProviderInterface(ABC):
    """
    Abstract AI Gateway Interface for Operational Recommendation providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name identifier of the Recommendation Provider (e.g. 'Gemini', 'OpenAI', 'Claude')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier (e.g. 'gemini-2.5-flash', 'gpt-4o')."""
        pass

    @abstractmethod
    def generate_recommendations(self, rca: RootCauseAnalysis) -> RecommendationReport:
        """
        Generates an operational RecommendationReport from a RootCauseAnalysis object.

        Parameters
        ----------
        rca : RootCauseAnalysis
            Structured Root Cause Analysis payload from Phase 4.

        Returns
        -------
        RecommendationReport
            Fully constructed and validated RecommendationReport payload.
        """
        pass
