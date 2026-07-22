# frontend.py

"""
Streamlit Web Frontend for Linux Server AI Assistant.
Provides a modern dashboard UI to interact with remote server diagnostic AI backend.
"""

import streamlit as st
from app import ask_server

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Linux Server AI Assistant",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich aesthetics and modern layout
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        font-size: 2.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .sub-header {
        font-size: 1rem;
        color: #9CA3AF;
        margin-bottom: 1.5rem;
    }

    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-label {
        font-size: 0.75rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #F8FAFC;
    }

    .ai-response-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #3B82F6;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.1);
    }
    .ai-response-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #60A5FA;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .ai-response-content {
        font-size: 1.05rem;
        line-height: 1.6;
        color: #E2E8F0;
    }

    .history-card {
        background-color: #1E293B;
        border-left: 4px solid #8B5CF6;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .history-q {
        font-weight: 600;
        color: #F1F5F9;
        font-size: 1rem;
        margin-bottom: 6px;
    }
    .history-a {
        color: #CBD5E1;
        font-size: 0.95rem;
        line-height: 1.5;
        margin-bottom: 8px;
    }
    .history-meta {
        font-size: 0.8rem;
        color: #64748B;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State for Chat History
if "history" not in st.session_state:
    st.session_state["history"] = []

if "latest_result" not in st.session_state:
    st.session_state["latest_result"] = None

# -----------------------------------------------------------------------------
# 2. Header Section
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">🖥️ Linux Server AI Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Ask questions about your remote Linux server using natural language.</div>',
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 3. Sidebar Quick Commands & Information
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("💡 Example Questions")
    st.markdown("- *How much RAM is available?*")
    st.markdown("- *What is the server uptime?*")
    st.markdown("- *Show me the disk space usage.*")
    st.markdown("- *What is the server hostname?*")
    st.markdown("- *Who is the current user?*")
    st.divider()

    st.markdown("### ⚙️ System Status")
    st.success("SSH Connection: Configured")
    st.success("PostgreSQL Log: Active")
    st.info("LLM Model: gemini-2.5-flash")

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["history"] = []
        st.session_state["latest_result"] = None
        st.rerun()

from commands import COMMANDS

# Group commands by category
categories = {}
for key, cmd in COMMANDS.items():
    cat = cmd.get("category", "General")
    if cat not in categories:
        categories[cat] = []
    examples = cmd.get("examples", [])
    for ex in examples:
        categories[cat].append((ex, key))

# -----------------------------------------------------------------------------
# 4. Examples & Question Input Section
# -----------------------------------------------------------------------------
st.markdown("### Examples you can ask:")

cat_cols = st.columns(2)
cat_items = list(categories.items())

for idx, (cat_name, ex_list) in enumerate(cat_items):
    with cat_cols[idx % 2]:
        with st.expander(f"▼ {cat_name}", expanded=False):
            for example_text, _ in ex_list:
                st.markdown(f"• {example_text}")

st.markdown("<br>", unsafe_allow_html=True)

with st.container():
    with st.form(key="question_form", clear_on_submit=False):
        user_input = st.text_input(
            label="Ask your question:",
            placeholder="e.g. How much RAM is available?",
            key="user_question_input",
        )
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            submit_button = st.form_submit_button(
                label="🚀 Ask",
                use_container_width=True,
            )

# -----------------------------------------------------------------------------
# 5. Question Processing Workflow
# -----------------------------------------------------------------------------
if submit_button and user_input.strip():
    with st.spinner("Connecting to server & executing command..."):
        # Execute ask_server backend pipeline
        res = ask_server(user_input.strip())

    st.session_state["latest_result"] = res

    # Append to history
    st.session_state["history"].insert(0, res)

# -----------------------------------------------------------------------------
# 6. Display Current Result (if available)
# -----------------------------------------------------------------------------
latest_res = st.session_state["latest_result"]

if latest_res:
    st.divider()

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)

    status_str = "Success" if latest_res["success"] else "Failed"
    status_color = "#22C55E" if latest_res["success"] else "#EF4444"

    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Command Selected</div>
                <div class="metric-value">{latest_res.get("command_key") or "N/A"}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Execution Time</div>
                <div class="metric-value">{latest_res.get("execution_time_seconds", 0.0)} s</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Status</div>
                <div class="metric-value" style="color: {status_color};">{status_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Timestamp</div>
                <div class="metric-value">{latest_res.get("timestamp", "N/A")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # AI Answer Card or Error Notification
    if latest_res["success"]:
        st.markdown(
            f"""
            <div class="ai-response-box">
                <div class="ai-response-header">✨ AI Response</div>
                <div class="ai-response-content">{latest_res["answer"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Expandable Sections
        with st.expander("🔍 Executed Linux Command", expanded=False):
            st.code(latest_res["linux_command"] or "None", language="bash")

        with st.expander("📄 Raw Command Output", expanded=False):
            st.code(latest_res["raw_output"] or "No output returned.", language="text")

        with st.expander("📊 Parsed JSON Output", expanded=False):
            if latest_res["parsed_output"]:
                st.json(latest_res["parsed_output"])
            else:
                st.write("No parsed data available.")

    else:
        st.error(f"**Error:** {latest_res.get('answer', 'Execution failed.')}")
        if latest_res.get("error"):
            st.warning(f"**Details:** {latest_res['error']}")

# -----------------------------------------------------------------------------
# 7. Conversation History Section
# -----------------------------------------------------------------------------
if st.session_state["history"]:
    st.divider()
    st.subheader("📜 Conversation History")

    for idx, item in enumerate(st.session_state["history"]):
        st.markdown(
            f"""
            <div class="history-card">
                <div class="history-q">❓ {item['question']}</div>
                <div class="history-a">{item['answer']}</div>
                <div class="history-meta">
                    ⏱️ {item.get('timestamp', '')} | Command: <code>{item.get('command_key', 'N/A')}</code> | Time: {item.get('execution_time_seconds', 0.0)}s
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
