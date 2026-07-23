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
from shared.config import get_settings

from .gemini_provider import GeminiRCAProvider
from .huggingface_provider import HuggingFaceProvider


class LLMProviderFactory:
    """
    Factory class providing static methods to create the active LLM Provider instance.
    """

    @staticmethod
    def get_provider() -> LLMProviderInterface:
        """
        Instantiates and returns the configured active LLM provider.
        """
        settings = get_settings()
        provider_name = (settings.llm.provider or "huggingface").lower().strip()

        if provider_name in ("huggingface", "hf", "qwen"):
            return HuggingFaceProvider()
        elif provider_name == "gemini":
            return GeminiRCAProvider()
        else:
            # Default fallback to Hugging Face
            return HuggingFaceProvider()

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
