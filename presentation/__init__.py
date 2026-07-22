"""
Purpose
-------
Package exports for the Presentation Layer.

Responsibilities
----------------
- Provide top-level presentation exports.

Does NOT
---------
- Contain business logic.
"""

from .streamlit.app import render_streamlit_dashboard

__all__ = ["render_streamlit_dashboard"]
