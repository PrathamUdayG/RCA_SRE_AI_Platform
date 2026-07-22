"""
Purpose
-------
Package exports for the Correlation Application Layer services.

Responsibilities
----------------
- Expose RuleRegistry and CorrelationService.

Does NOT
---------
- Contain domain models or execute SSH/LLM logic.
"""

from .correlation_service import CorrelationService
from .rule_registry import RuleRegistry

__all__ = [
    "RuleRegistry",
    "CorrelationService",
]
