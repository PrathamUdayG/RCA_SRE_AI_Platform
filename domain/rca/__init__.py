"""
Purpose
-------
Package exports for the Root Cause Analysis (RCA) Domain.

Responsibilities
----------------
- Provide public module exports for RCA domain models, exceptions, and provider interfaces.

Does NOT
---------
- Execute SSH commands or perform infrastructure data correlation.
- Tightly couple logic to a specific AI vendor.
"""

from .exceptions import (
    InvalidCorrelationResultError,
    LLMProviderError,
    RCAError,
)
from .llm_interface import LLMProviderInterface
from .models import (
    AffectedComponent,
    AnalysisMetadata,
    Hypothesis,
    ReasoningTrace,
    RootCauseAnalysis,
    SupportingEvidence,
)

__all__ = [
    "RCAError",
    "InvalidCorrelationResultError",
    "LLMProviderError",
    "LLMProviderInterface",
    "Hypothesis",
    "SupportingEvidence",
    "ReasoningTrace",
    "AffectedComponent",
    "AnalysisMetadata",
    "RootCauseAnalysis",
]
