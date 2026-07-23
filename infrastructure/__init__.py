"""
Purpose
-------
Top-level package exports for the Infrastructure Layer.

Responsibilities
----------------
- Expose SSH clients, LLM providers, Registries, and Repositories.

Does NOT
---------
- Contain business logic.
"""

from .health import (
    AIProviderHealthChecker,
    ApplicationHealthChecker,
    DatabaseHealthChecker,
    GeminiHealthChecker,
    LLMHealthChecker,
    SSHHealthChecker,
)
from .llm import (
    GeminiRCAProvider,
    GeminiRecommendationProvider,
    HuggingFaceRCAProvider,
    HuggingFaceRecommendationProvider,
    LLMProviderFactory,
    get_llm_rca_provider,
    get_llm_recommendation_provider,
)
from .persistence import PostgresAuditRepository
from .registry import LinuxCommandRegistry, LinuxParserRegistry
from .ssh import ISSHClient, ParamikoSSHClient

__all__ = [
    "ISSHClient",
    "ParamikoSSHClient",
    "LLMProviderFactory",
    "HuggingFaceRCAProvider",
    "HuggingFaceRecommendationProvider",
    "GeminiRCAProvider",
    "GeminiRecommendationProvider",
    "get_llm_rca_provider",
    "get_llm_recommendation_provider",
    "LinuxCommandRegistry",
    "LinuxParserRegistry",
    "PostgresAuditRepository",
    "SSHHealthChecker",
    "DatabaseHealthChecker",
    "AIProviderHealthChecker",
    "LLMHealthChecker",
    "GeminiHealthChecker",
    "ApplicationHealthChecker",
]
