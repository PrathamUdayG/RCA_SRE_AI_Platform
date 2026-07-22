"""
Purpose
-------
Package exports for the Workflow Application Layer.

Responsibilities
----------------
- Expose InvestigationWorkflow orchestrator.

Does NOT
---------
- Contain low-level infrastructure.
"""

from .investigation_workflow import InvestigationWorkflow

__all__ = ["InvestigationWorkflow"]
