"""
Purpose
-------
Unified abstract domain interface decoupling all AI/LLM operations (Root Cause Analysis,
Recommendation Generation, and Health Checks) from concrete infrastructure providers.

Responsibilities
----------------
- Define unified contract for AI LLM providers (Hugging Face, OpenAI, Claude, Ollama, Gemini).
- Require every provider to implement health_check(), analyze_correlation(), and generate_recommendations().
- Ensure Domain and Application layers remain 100% provider-agnostic.

Does NOT
---------
- Depend on external LLM vendor SDKs or environment variables.
- Execute network calls or parse raw text strings directly.
"""

from abc import ABC, abstractmethod

from domain.correlation.models import CorrelationResult
from domain.health.models import ComponentHealthResult
from domain.rca.models import RootCauseAnalysis
from domain.recommendation.models import RecommendationReport


class LLMProviderInterface(ABC):
    """
    Unified Abstract AI Gateway Interface for all platform LLM capabilities.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name identifier of the LLM Provider (e.g. 'Hugging Face', 'OpenAI', 'Claude')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier (e.g. 'Qwen/Qwen2.5-72B-Instruct', 'gpt-4o')."""
        pass

    @abstractmethod
    def health_check(self) -> ComponentHealthResult:
        """
        Performs a lightweight provider connectivity health check and returns a ComponentHealthResult.
        """
        pass

    @abstractmethod
    def analyze_correlation(self, correlation_result: CorrelationResult) -> RootCauseAnalysis:
        """
        Analyzes a CorrelationResult object and returns a structured RootCauseAnalysis payload.
        """
        pass

    @abstractmethod
    def generate_recommendations(self, rca: RootCauseAnalysis) -> RecommendationReport:
        """
        Generates an operational RecommendationReport from a RootCauseAnalysis payload.
        """
        pass

    @abstractmethod
    def generate_executive_summary(
        self,
        user_question: str,
        correlation_result: CorrelationResult = None,
        rca: RootCauseAnalysis = None,
        recommendation: RecommendationReport = None,
    ) -> str:
        """
        Synthesizes a clear, direct executive answer to the user's natural language question
        based on correlation findings, RCA hypotheses, and operational recommendations.
        """
        pass


# Aliases for clean backward compatibility
LLMProvider = LLMProviderInterface
RecommendationProviderInterface = LLMProviderInterface
