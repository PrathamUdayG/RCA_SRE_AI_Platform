"""
Purpose
-------
Package exports for the Operational Recommendation Domain.

Responsibilities
----------------
- Provide public module exports for recommendation domain models, exceptions, and provider interfaces.

Does NOT
---------
- Execute commands or modify infrastructure.
- Tightly couple business logic to a specific AI vendor.
"""

from .exceptions import (
    InvalidRCAResultError,
    RecommendationError,
    RecommendationProviderError,
)
from .llm_interface import RecommendationProviderInterface
from .models import (
    MonitoringRecommendation,
    PreventionRecommendation,
    Recommendation,
    RecommendationCategory,
    RecommendationMetadata,
    RecommendationPriority,
    RecommendationReport,
    RiskLevel,
    RollbackPlan,
    ValidationStep,
)

__all__ = [
    "RecommendationError",
    "InvalidRCAResultError",
    "RecommendationProviderError",
    "RecommendationProviderInterface",
    "RecommendationCategory",
    "RecommendationPriority",
    "RiskLevel",
    "Recommendation",
    "ValidationStep",
    "RollbackPlan",
    "MonitoringRecommendation",
    "PreventionRecommendation",
    "RecommendationMetadata",
    "RecommendationReport",
]
