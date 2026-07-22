"""
Purpose
-------
Package exports for shared logging utilities.

Responsibilities
----------------
- Expose get_logger helper function.

Does NOT
---------
- Contain business or infrastructure logic.
"""

from .logger import get_logger

__all__ = ["get_logger"]
