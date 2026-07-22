"""
Purpose
-------
Root Streamlit entrypoint delegating to presentation.streamlit.app presentation module.

Responsibilities
----------------
- Launch the AI SRE Web Dashboard.

Does NOT
---------
- Implement business logic or direct SSH/database calls.
"""

from presentation.streamlit.app import render_streamlit_dashboard

if __name__ == "__main__":
    render_streamlit_dashboard()
