"""
Purpose
-------
Package exports for the Unified Investigation Report domain module.

Responsibilities
----------------
- Expose InvestigationReport model.

Does NOT
---------
- Contain infrastructure code.
"""

from .models import InvestigationReport

__all__ = ["InvestigationReport"]
