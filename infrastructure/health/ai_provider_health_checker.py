"""
Purpose
-------
Provider-agnostic AI Provider health checker for the AI SRE Platform.

Responsibilities
----------------
- Delegate health check probing directly to the active LLMProvider instance via LLMProviderFactory.
- Return structured ComponentHealthResult DTOs.
- Ensure 100% single-path execution for all AI capabilities (RCA, Recommendations, and Health Checks).

Does NOT
---------
- Implement duplicate API client calls or health probe logic separate from LLMProvider.
- Hardcode vendor references.
"""

from typing import Optional

from domain.health.models import ComponentHealthResult
from domain.llm import LLMProviderInterface
from infrastructure.llm.provider_factory import LLMProviderFactory
from shared.logging import get_logger

logger = get_logger("AIProviderHealthChecker")


class AIProviderHealthChecker:
    """
    Provider-agnostic health checker delegating directly to active LLMProvider instance.
    """

    def __init__(self, provider: Optional[LLMProviderInterface] = None):
        self._provider = provider or LLMProviderFactory.get_provider()

    def check(self) -> ComponentHealthResult:
        """
        Delegates health check execution directly to the active LLMProvider instance.
        """
        return self._provider.health_check()


# Backward compatibility aliases
LLMHealthChecker = AIProviderHealthChecker
GeminiHealthChecker = AIProviderHealthChecker
