"""
Purpose
-------
Abstract provider interface decoupling RCA business logic from concrete LLM vendor SDKs.

Responsibilities
----------------
- Define the contract for AI RCA reasoning providers (Gemini, OpenAI, Claude, Local LLMs).

Does NOT
---------
- Depend on specific LLM vendor SDKs or environment variables.
"""

from abc import ABC, abstractmethod

from domain.correlation.models import CorrelationResult
from .models import RootCauseAnalysis


class LLMProviderInterface(ABC):
    """
    Abstract AI Gateway Interface for Root Cause Analysis providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name identifier of the LLM Provider (e.g. 'Gemini', 'OpenAI', 'Claude')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier (e.g. 'gemini-2.5-flash', 'gpt-4o')."""
        pass

    @abstractmethod
    def analyze_correlation(self, correlation_result: CorrelationResult) -> RootCauseAnalysis:
        """
        Analyzes a CorrelationResult object and returns a structured RootCauseAnalysis.

        Parameters
        ----------
        correlation_result : CorrelationResult
            Correlated operational findings and evidence from Phase 3.

        Returns
        -------
        RootCauseAnalysis
            Fully constructed and validated Root Cause Analysis payload.
        """
        pass
