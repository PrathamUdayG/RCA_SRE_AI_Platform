"""
Purpose
-------
Package exports for shared platform modules.

Responsibilities
----------------
- Provide top-level exports for shared config, logging, and exceptions.

Does NOT
---------
- Contain business logic.
"""

from .config import get_settings
from .exceptions import PlatformBaseException
from .logging import get_logger

__all__ = ["get_settings", "get_logger", "PlatformBaseException"]
