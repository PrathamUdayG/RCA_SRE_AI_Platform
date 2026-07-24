"""
Purpose
-------
LLM Provider Factory for instantiating concrete AI reasoning providers based on LLM_PROVIDER settings.

Responsibilities
----------------
- Inspect LLM_PROVIDER configuration ("huggingface", "gemini", "openai", "ollama", "azure", etc.).
- Return concrete implementations of unified LLMProviderInterface.
- Decouple Application, Domain, and Observability layers from concrete vendor implementations.

Does NOT
---------
- Implement LLM prompt formatting or API calls directly.
"""

from domain.llm import LLMProviderInterface
from .provider_manager import LLMProviderManager


class LLMProviderFactory:
    """
    Factory class providing static methods to return the centralized LLMProviderManager instance.
    """

    @staticmethod
    def get_provider() -> LLMProviderInterface:
        """
        Returns the authoritative centralized LLMProviderManager instance.
        """
        return LLMProviderManager()

    @staticmethod
    def create_rca_provider() -> LLMProviderInterface:
        return LLMProviderFactory.get_provider()

    @staticmethod
    def create_recommendation_provider() -> LLMProviderInterface:
        return LLMProviderFactory.get_provider()


def get_provider() -> LLMProviderInterface:
    """Convenience function retrieving configured active LLM provider."""
    return LLMProviderFactory.get_provider()


def get_llm_rca_provider() -> LLMProviderInterface:
    """Convenience function retrieving configured active LLM provider for RCA."""
    return LLMProviderFactory.get_provider()


def get_llm_recommendation_provider() -> LLMProviderInterface:
    """Convenience function retrieving configured active LLM provider for Recommendations."""
    return LLMProviderFactory.get_provider()
