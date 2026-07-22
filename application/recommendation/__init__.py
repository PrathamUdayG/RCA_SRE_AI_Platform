"""
Purpose
-------
Package exports for the Recommendation Application Layer services.

Responsibilities
----------------
- Expose RecommendationService.

Does NOT
---------
- Depend on specific LLM vendor SDKs.
"""

from .recommendation_service import RecommendationService

__all__ = [
    "RecommendationService",
]
