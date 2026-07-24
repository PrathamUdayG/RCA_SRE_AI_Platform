"""
Purpose
-------
Streamlit Web Dashboard Presentation Layer for the AI SRE Platform.

Responsibilities
----------------
- Render interactive web dashboard UI for natural language incident investigations.
- Render Executive Investigation Summary providing a direct answer to user queries first.
- Render Platform Health Dashboard displaying real-time status of all platform dependencies.
- Render expandable 6-phase technical audit trail with defensive rendering boundaries.

Does NOT
--------
- Implement business logic or direct SSH/database calls.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import streamlit as st

from application.health import HealthService
from application.workflow import InvestigationWorkflow
from domain.health.models import ComponentStatus
from domain.report.models import InvestigationReport


# ─────────────────────────────────────────────────────────────────────
# Defensive Helper Functions
# ─────────────────────────────────────────────────────────────────────

def safe_get(obj: Any, attr_path: str, default: Any = "N/A") -> Any:
    """
    Safely retrieves a nested attribute or dictionary key path from an object or dictionary.
    Unpacks Enum values (.value) and formats None/empty values cleanly.
    """
    if obj is None:
        return default

    curr = obj
    for part in attr_path.split("."):
        if curr is None:
            return default
        if isinstance(curr, dict):
            curr = curr.get(part)
        elif hasattr(curr, part):
            curr = getattr(curr, part)
        else:
            return default

    if curr is None or curr == "":
        return default

    if isinstance(curr, Enum):
        return curr.value

    return curr


_STATUS_BADGES = {
    ComponentStatus.HEALTHY: "🟢",
    ComponentStatus.UNHEALTHY: "🔴",
    ComponentStatus.DEGRADED: "🟡",
    ComponentStatus.NOT_CONFIGURED: "⚪",
}

_STATUS_LABELS = {
    ComponentStatus.HEALTHY: "Healthy",
    ComponentStatus.UNHEALTHY: "Unhealthy",
    ComponentStatus.DEGRADED: "Partially Available",
    ComponentStatus.NOT_CONFIGURED: "Not Configured",
}

_FUTURE_PLACEHOLDERS = [
    "Docker Engine",
    "Kubernetes Cluster",
    "Redis",
    "Vector Database",
    "Knowledge Base",
    "Monitoring System",
]


# ─────────────────────────────────────────────────────────────────────
# Health Dashboard Rendering
# ─────────────────────────────────────────────────────────────────────

def _render_health_dashboard():
    """
    Renders the Platform Health Dashboard section defensively.
    """
    st.header("🏥 Platform Health")

    try:
        if "health_report" not in st.session_state:
            with st.spinner("Checking platform health..."):
                health_service = HealthService()
                st.session_state["health_report"] = health_service.check_all()

        report = st.session_state.get("health_report")
        if not report:
            st.info("Health status information unavailable.")
            return

        overall_status = getattr(report, "overall_status", ComponentStatus.NOT_CONFIGURED)
        overall_badge = _STATUS_BADGES.get(overall_status, "⚪")
        overall_label = _STATUS_LABELS.get(overall_status, "Unknown")

        status_color_map = {
            ComponentStatus.HEALTHY: "green",
            ComponentStatus.DEGRADED: "orange",
            ComponentStatus.UNHEALTHY: "red",
        }
        border_color = status_color_map.get(overall_status, "gray")
        checked_time_str = report.checked_at.strftime('%Y-%m-%d %H:%M:%S UTC') if hasattr(report, "checked_at") and report.checked_at else "N/A"

        st.markdown(
            f"""
            <div style="
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 16px 24px;
                margin-bottom: 16px;
                background: linear-gradient(135deg, rgba(0,0,0,0.02), rgba(0,0,0,0.06));
            ">
                <h3 style="margin: 0;">Platform Status: {overall_badge} {overall_label}</h3>
                <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9em;">
                    Last checked: {checked_time_str} &nbsp;|&nbsp;
                    Version: {getattr(report, "application_version", "1.0.0")} &nbsp;|&nbsp;
                    Python: {getattr(report, "python_version", "3.x")}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        components = getattr(report, "component_results", [])
        if components:
            col_pairs = [components[i:i + 2] for i in range(0, len(components), 2)]
            for pair in col_pairs:
                cols = st.columns(len(pair))
                for col, result in zip(cols, pair):
                    with col:
                        c_status = getattr(result, "status", ComponentStatus.NOT_CONFIGURED)
                        badge = _STATUS_BADGES.get(c_status, "⚪")
                        label = _STATUS_LABELS.get(c_status, "Unknown")
                        c_name = getattr(result, "component_name", "Component")
                        header_text = f"{badge} {c_name} — {label}"

                        with st.expander(header_text, expanded=(c_status != ComponentStatus.HEALTHY)):
                            if c_status == ComponentStatus.HEALTHY:
                                st.success(f"{c_name} is operational.")
                            elif c_status == ComponentStatus.DEGRADED:
                                st.warning(f"{c_name} is experiencing issues.")
                            else:
                                st.error(f"{c_name} is unavailable.")

                            details = getattr(result, "details", {})
                            if details:
                                st.markdown("**Connection Details:**")
                                for key, value in details.items():
                                    display_key = key.replace("_", " ").title()
                                    st.markdown(f"- **{display_key}**: `{value}`")

                            latency = getattr(result, "latency_ms", None)
                            if latency is not None:
                                st.markdown(f"- **Latency**: `{latency} ms`")

                            error_msg = getattr(result, "error_message", None)
                            if error_msg:
                                st.markdown("---")
                                st.markdown(f"**⚠️ Error**: {error_msg}")

                            rec = getattr(result, "recommendation", None)
                            if rec:
                                st.markdown(f"**💡 Recommendation**: {rec}")

                            c_time = result.checked_at.strftime('%Y-%m-%d %H:%M:%S UTC') if getattr(result, "checked_at", None) else "N/A"
                            st.caption(f"Checked at: {c_time}")

    except Exception as err:
        st.warning(f"Unable to render platform health dashboard: {err}")

    st.markdown("##### Future Services")
    placeholder_cols = st.columns(3)
    for idx, service_name in enumerate(_FUTURE_PLACEHOLDERS):
        with placeholder_cols[idx % 3]:
            st.markdown(
                f"""
                <div style="
                    border: 1px dashed gray;
                    border-radius: 8px;
                    padding: 10px 14px;
                    margin-bottom: 8px;
                    opacity: 0.5;
                    text-align: center;
                ">
                    ⚪ {service_name}<br/>
                    <small>Not Configured</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.button("🔄 Refresh Health Status", key="refresh_health_btn", use_container_width=True):
        with st.spinner("Re-checking platform health..."):
            health_service = HealthService()
            st.session_state["health_report"] = health_service.check_all()
        st.rerun()


# ─────────────────────────────────────────────────────────────────────
# Executive Investigation Summary Rendering (PRIMARY DISPLAY)
# ─────────────────────────────────────────────────────────────────────

def _render_executive_summary(report: InvestigationReport):
    """
    Renders the Executive Investigation Summary section consuming ExecutiveSummary DTO.
    """
    st.header("📊 Executive Investigation Summary")

    summary = getattr(report, "executive_summary", None)
    if not summary:
        st.info("No executive summary DTO available.")
        return

    inv_status = safe_get(summary, "investigation_status", "INCONCLUSIVE")
    if inv_status == "SUCCESS":
        status_badge_str = "🟢 SUCCESS"
    elif inv_status == "PARTIAL_SUCCESS":
        status_badge_str = "🟡 PARTIAL SUCCESS"
    elif inv_status == "FAILED":
        status_badge_str = "🔴 FAILED"
    else:
        status_badge_str = "⚪ INCONCLUSIVE"

    user_q = safe_get(summary, "user_question", "Diagnostic Question")
    direct_ans = safe_get(summary, "direct_answer", "Investigation complete.")

    # ── Executive Direct Answer Box ────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            border: 2px solid #1E88E5;
            border-radius: 12px;
            padding: 20px 24px;
            background: linear-gradient(135deg, rgba(30,136,229,0.06), rgba(30,136,229,0.02));
            margin-bottom: 24px;
        ">
            <div style="font-size: 0.85em; text-transform: uppercase; letter-spacing: 1px; color: #1565C0; font-weight: bold; margin-bottom: 4px;">
                Direct Investigation Answer
            </div>
            <h4 style="margin: 0 0 12px 0; color: #0D47A1;">Question: "{user_q}"</h4>
            <p style="font-size: 1.1em; line-height: 1.6; margin: 0; color: #1A237E;">
                {direct_ans}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Executive Key Metric Row (4 KPI Cards) ────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    conf_score = safe_get(summary, "confidence_score", 0.0)
    confidence_pct = f"{round(float(conf_score) * 100, 1)}%" if isinstance(conf_score, (int, float)) else "0%"
    primary_rc = safe_get(summary, "primary_root_cause", "N/A")
    top_recommendation = safe_get(summary, "recommendations_summary", "N/A")

    with col1:
        st.metric("Investigation Status", inv_status, delta=status_badge_str)
    with col2:
        st.metric("Overall Confidence", confidence_pct)
    with col3:
        st.metric("Primary Root Cause", primary_rc[:35] + "..." if len(primary_rc) > 35 else primary_rc)
    with col4:
        st.metric("Top Recommendation", top_recommendation[:35] + "..." if len(top_recommendation) > 35 else top_recommendation)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Key Supporting Evidence Grid ──────────────────────────────────
    st.subheader("🔑 Key Supporting Evidence")
    key_evidence = getattr(summary, "key_evidence", [])
    key_findings = getattr(summary, "key_findings", [])

    if key_evidence:
        st.dataframe(key_evidence, use_container_width=True)
    elif key_findings:
        for finding_title in key_findings:
            st.markdown(f"- 📌 **Finding**: {finding_title}")
    else:
        st.info("No specific empirical metric violations recorded.")

    # ── Primary Recommended Next Action ──────────────────────────────
    rec_report = getattr(report, "recommendation", None)
    rec_actions = getattr(rec_report, "recommended_actions", []) if rec_report else []

    if rec_actions:
        st.subheader("💡 Recommended Next Action")
        action = rec_actions[0]
        act_title = safe_get(action, "title", "Action")
        act_prio = safe_get(action, "priority", "N/A")
        act_risk = safe_get(action, "risk_level", "N/A")
        act_skill = safe_get(action, "required_skill_level", "Senior SRE")
        act_reason = safe_get(action, "reason", "N/A")
        act_desc = safe_get(action, "description", "N/A")

        st.warning(
            f"**Action**: {act_title}\n\n"
            f"**Priority**: `{act_prio}` | **Risk Level**: `{act_risk}` | **Skill Level**: `{act_skill}`\n\n"
            f"**Reasoning**: {act_reason}\n\n"
            f"**Description**: {act_desc}"
        )

    # ── Investigation Metadata Panel ─────────────────────────────────
    st.subheader("ℹ️ Investigation Metadata & Data Quality")
    meta = getattr(summary, "investigation_metadata", {}) or {}

    meta_c1, meta_c2, meta_c3, meta_c4 = st.columns(4)
    with meta_c1:
        inv_id = meta.get("investigation_id", getattr(report, "report_id", "N/A"))
        st.markdown(f"**Investigation ID**:\n`{str(inv_id)[:8]}...`")
        st.markdown(f"**Target Server**:\n`{meta.get('target_server', 'testserv.ortusolis.in:22')}`")
    with meta_c2:
        c_time_str = report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if hasattr(report, "created_at") and report.created_at else "N/A"
        st.markdown(f"**Start Time (UTC)**:\n`{meta.get('start_time_utc', c_time_str)}`")
        st.markdown(f"**Total Duration**:\n`{meta.get('duration_seconds', getattr(report, 'total_execution_time_seconds', 0.0))}s`")
    with meta_c3:
        st.markdown(f"**Commands Executed**:\n`{meta.get('commands_executed', 0)}` total (`{meta.get('commands_succeeded', 0)}` ok, `{meta.get('commands_failed', 0)}` failed)")
        st.markdown(f"**Data Quality**:\n`{meta.get('data_quality_pct', '100%')}`")
    with meta_c4:
        st.markdown(f"**AI Provider**:\n`{meta.get('ai_provider', 'N/A')}`")
        st.markdown(f"**LLM Model**:\n`{meta.get('llm_model', 'N/A')}`")


# ─────────────────────────────────────────────────────────────────────
# Technical Pipeline Tab Renderers (DEFENSIVE ISOLATED COMPONENTS)
# ─────────────────────────────────────────────────────────────────────

def _render_tab_rca(rca):
    """Renders Phase 4 Root Cause Analysis tab."""
    if not rca:
        st.info("No RCA available.")
        return

    st.subheader("🎯 Primary Root Cause")
    st.error(safe_get(rca, "primary_root_cause", "No primary root cause identified."))

    st.subheader("📝 Executive Summary")
    st.info(safe_get(rca, "summary", "Analysis completed."))

    st.subheader("💡 Hypotheses & Evidence")
    prim_hyp = getattr(rca, "primary_hypothesis", None)
    hyp_title = safe_get(prim_hyp, "title", "Primary Hypothesis")
    hyp_score = safe_get(prim_hyp, "likelihood_score", "N/A")
    hyp_desc = safe_get(prim_hyp, "description", "N/A")

    st.markdown(f"**Primary Hypothesis**: {hyp_title} (Likelihood: `{hyp_score}`)")
    st.write(hyp_desc)

    st.subheader("🔍 Reasoning Trace")
    traces = getattr(rca, "reasoning_trace", [])
    if traces:
        for rt in traces:
            step_num = safe_get(rt, "step_number", 1)
            obs = safe_get(rt, "observation", "")
            ded = safe_get(rt, "deduction", "")
            st.write(f"**Step #{step_num}**: Observation: *{obs}* ➔ Deduction: `{ded}`")
    else:
        st.caption("No reasoning trace steps recorded.")


def _render_tab_guidance(recommendation, policy_decision):
    """Renders Phase 5 & 6 Guidance & Policy permissions tab."""
    if not recommendation:
        st.info("No recommendations available.")
        return

    st.subheader("📋 Operational Recommendations & Policy Permissions")
    rec_actions = getattr(recommendation, "recommended_actions", [])
    requests = getattr(policy_decision, "approval_requests", []) if policy_decision else []

    if rec_actions:
        for idx, action in enumerate(rec_actions, start=1):
            act_id = getattr(action, "recommendation_id", None)
            req = next((r for r in requests if getattr(r, "recommendation_id", None) == act_id), None)
            perm_badge = safe_get(req, "approval_status", "PENDING")

            title = safe_get(action, "title", "Recommended Action")
            cat = safe_get(action, "category", "IMMEDIATE")
            prio = safe_get(action, "priority", "P2_HIGH")
            risk = safe_get(action, "risk_level", "MEDIUM")
            reason = safe_get(action, "reason", "N/A")
            desc = safe_get(action, "description", "N/A")

            st.markdown(f"### Action #{idx}: {title}  `[{perm_badge}]`")
            st.write(f"**Category**: {cat} | **Priority**: {prio} | **Risk**: {risk}")
            st.write(f"**Reason**: {reason}")
            st.write(f"**Description**: {desc}")
            st.divider()
    else:
        st.caption("No actionable recommendations recorded.")


def _render_tab_findings(correlation):
    """Renders Phase 3 Correlated Findings tab."""
    if not correlation:
        st.info("No findings available.")
        return

    st.subheader("🔗 Correlated Operational Findings")
    findings = getattr(correlation, "findings", [])

    if findings:
        for f in findings:
            sev = safe_get(f, "severity", "INFO")
            title = safe_get(f, "title", "Finding")
            cat = safe_get(f, "category", "SYSTEM")
            summary = safe_get(f, "summary", "N/A")
            conf = safe_get(f, "confidence_score", 0.0)
            res = safe_get(f, "affected_resources", [])

            with st.expander(f"[{sev}] {title} ({cat})"):
                st.write(f"**Summary**: {summary}")
                st.write(f"**Confidence**: {conf}")
                st.write(f"**Affected Resources**: {res}")
    else:
        st.caption("Zero correlated findings recorded.")


def _render_tab_executions(execution):
    """Renders Phase 2 Step Executions tab."""
    if not execution:
        st.info("No step executions available.")
        return

    st.subheader("⚡ Multi-Command Execution Details")
    step_results = getattr(execution, "step_results", [])

    if step_results:
        for res in step_results:
            order = safe_get(res, "order", 1)
            cmd_id = safe_get(res, "command_id", "command")
            l_cmd = safe_get(res, "linux_command", "command")
            status = safe_get(res, "status", "SUCCESS")
            raw_out = safe_get(res, "raw_output", "")

            with st.expander(f"Order #{order}: {cmd_id} (`{l_cmd}`) - Status: {status}"):
                if raw_out:
                    st.code(raw_out, language="bash")
                else:
                    st.caption("No raw terminal output recorded.")
    else:
        st.caption("No step results recorded.")


def _render_tab_plan(plan):
    """Renders Phase 1 Investigation Plan tab."""
    if not plan:
        st.info("No plan available.")
        return

    st.subheader("🗺️ Phase 1 Investigation Plan Blueprint")
    prio = safe_get(plan, "priority", "MEDIUM")
    strat = safe_get(plan, "execution_strategy", "SEQUENTIAL")
    st.write(f"**Priority**: {prio} | **Strategy**: {strat}")

    steps = getattr(plan, "steps", [])
    if steps:
        for s in steps:
            order = safe_get(s, "order", 1)
            cmd_id = safe_get(s, "command_id", "command")
            desc = safe_get(s, "description", "N/A")
            st.write(f"**Step #{order}**: `{cmd_id}` - {desc}")
    else:
        st.caption("No plan steps recorded.")


def _render_tab_policy(policy_decision):
    """Renders Phase 6 Policy Decisions tab."""
    if not policy_decision:
        st.info("No policy decisions available.")
        return

    st.subheader("🛡️ Phase 6 Policy Engine Evaluation")
    overall_dec = safe_get(policy_decision, "overall_decision", "AUTO_APPROVED")
    summary_text = safe_get(policy_decision, "summary", "Policy evaluation completed.")

    st.write(f"**Overall Policy Decision**: `{overall_dec}`")
    st.write(f"**Evaluation Summary**: {summary_text}")

    requests = getattr(policy_decision, "approval_requests", [])
    if requests:
        for req in requests:
            # Defensive field extraction for recommendation title / action title and risk level
            title = safe_get(req, "action_title", safe_get(req, "recommendation_title", "Action"))
            status = safe_get(req, "approval_status", "PENDING")
            risk = safe_get(req, "risk_level", "MEDIUM")
            st.markdown(f"- **{title}**: `{status}` (Risk: `{risk}`)")
    else:
        st.caption("No policy approval requests recorded.")


def _render_technical_pipeline(report: InvestigationReport):
    """
    Renders the secondary 6-phase technical investigation pipeline with isolated error boundaries per tab.
    """
    st.divider()
    with st.expander("🔍 Technical Investigation Pipeline & Audit Trail (Phases 1–6)", expanded=False):
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🧠 Root Cause Analysis (Phase 4)",
            "📋 Guidance & Policy (Phases 5 & 6)",
            "🔗 Correlated Findings (Phase 3)",
            "⚡ Step Executions (Phase 2)",
            "🗺️ Investigation Plan (Phase 1)",
            "🛡️ Policy Decisions (Phase 6)",
        ])

        with tab1:
            try:
                _render_tab_rca(getattr(report, "rca", None))
            except Exception as err:
                st.warning(f"Unable to render Root Cause Analysis tab: {err}")

        with tab2:
            try:
                _render_tab_guidance(getattr(report, "recommendation", None), getattr(report, "policy_decision", None))
            except Exception as err:
                st.warning(f"Unable to render Guidance & Policy tab: {err}")

        with tab3:
            try:
                _render_tab_findings(getattr(report, "correlation", None))
            except Exception as err:
                st.warning(f"Unable to render Correlated Findings tab: {err}")

        with tab4:
            try:
                _render_tab_executions(getattr(report, "execution", None))
            except Exception as err:
                st.warning(f"Unable to render Step Executions tab: {err}")

        with tab5:
            try:
                _render_tab_plan(getattr(report, "plan", None))
            except Exception as err:
                st.warning(f"Unable to render Investigation Plan tab: {err}")

        with tab6:
            try:
                _render_tab_policy(getattr(report, "policy_decision", None))
            except Exception as err:
                st.warning(f"Unable to render Policy Decisions tab: {err}")


# ─────────────────────────────────────────────────────────────────────
# Main Dashboard Entry Point
# ─────────────────────────────────────────────────────────────────────

def render_streamlit_dashboard():
    """Renders the Streamlit AI SRE Platform Web Dashboard."""
    st.set_page_config(
        page_title="AI SRE Platform for Autonomous Operations",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🛡️ AI SRE Platform for Autonomous Operations")
    st.caption("Enterprise Autonomous Incident Investigation, Correlation, RCA, Recommendation & Policy Engine")

    with st.sidebar:
        st.header("⚙️ Platform Architecture")
        st.markdown("""
        **Pipeline Stages**:
        1. 📋 **Phase 1**: Investigation Planner
        2. ⚡ **Phase 2**: Execution Engine
        3. 🔗 **Phase 3**: Correlation Engine
        4. 🧠 **Phase 4**: AI RCA Engine
        5. 📋 **Phase 5**: Recommendation Engine
        6. 🛡️ **Phase 6**: Policy Engine
        7. 📊 **Synthesis**: Executive Summary Service
        """)
        st.divider()
        st.info("Target Server: `testserv.ortusolis.in:22`")

    # ── Platform Health Dashboard ────────────────────────────────────
    _render_health_dashboard()

    st.divider()
    st.subheader("🔍 Autonomous Incident Investigation")

    # Natural Language Question Input
    query = st.text_input(
        "Ask a diagnostic question about your infrastructure:",
        placeholder="e.g., Why is my server slow and unresponsive?",
        key="user_query_input",
    )

    if st.button("Run Autonomous Investigation", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a valid natural language question.")
            return

        with st.spinner("Executing end-to-end investigation pipeline (Phases 1-6 + Executive Synthesis)..."):
            workflow = InvestigationWorkflow()
            report: InvestigationReport = workflow.execute_investigation(query.strip())
            st.session_state["last_investigation_report"] = report

    # ── Render Executive Summary & Pipeline if report exists ─────────
    if "last_investigation_report" in st.session_state:
        report = st.session_state["last_investigation_report"]

        # 1. PRIMARY DISPLAY: Executive Investigation Summary (Answers user question first)
        try:
            _render_executive_summary(report)
        except Exception as err:
            st.error(f"Error rendering Executive Summary: {err}")

        # 2. SECONDARY DISPLAY: Technical Pipeline & Audit Trail (Phases 1–6)
        try:
            _render_technical_pipeline(report)
        except Exception as err:
            st.error(f"Error rendering Technical Pipeline: {err}")


if __name__ == "__main__":
    render_streamlit_dashboard()
