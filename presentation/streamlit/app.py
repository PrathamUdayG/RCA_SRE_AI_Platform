"""
Purpose
-------
Streamlit Web Dashboard Presentation Layer for the AI SRE Platform.

Responsibilities
----------------
- Render interactive web dashboard UI for natural language incident investigations.
- Render Executive Investigation Summary providing a direct answer to user queries first.
- Render Platform Health Dashboard displaying real-time status of all platform dependencies.
- Render expandable technical audit trail for Phases 1-6.

Does NOT
---------
- Implement business logic or direct SSH/database calls.
"""

from datetime import datetime
import streamlit as st

from application.health import HealthService
from application.workflow import InvestigationWorkflow
from domain.health.models import ComponentStatus
from domain.report.models import InvestigationReport


# ─────────────────────────────────────────────────────────────────────
# Status Badge Helpers
# ─────────────────────────────────────────────────────────────────────

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
    Renders the Platform Health Dashboard section.
    """
    st.header("🏥 Platform Health")

    if "health_report" not in st.session_state:
        with st.spinner("Checking platform health..."):
            health_service = HealthService()
            st.session_state["health_report"] = health_service.check_all()

    report = st.session_state["health_report"]

    overall_badge = _STATUS_BADGES.get(report.overall_status, "⚪")
    overall_label = _STATUS_LABELS.get(report.overall_status, "Unknown")

    status_color_map = {
        ComponentStatus.HEALTHY: "green",
        ComponentStatus.DEGRADED: "orange",
        ComponentStatus.UNHEALTHY: "red",
    }
    border_color = status_color_map.get(report.overall_status, "gray")

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
                Last checked: {report.checked_at.strftime('%Y-%m-%d %H:%M:%S UTC')} &nbsp;|&nbsp;
                Version: {report.application_version} &nbsp;|&nbsp;
                Python: {report.python_version}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    components = report.component_results
    col_pairs = [components[i:i + 2] for i in range(0, len(components), 2)]

    for pair in col_pairs:
        cols = st.columns(len(pair))
        for col, result in zip(cols, pair):
            with col:
                badge = _STATUS_BADGES.get(result.status, "⚪")
                label = _STATUS_LABELS.get(result.status, "Unknown")
                header_text = f"{badge} {result.component_name} — {label}"

                with st.expander(header_text, expanded=(result.status != ComponentStatus.HEALTHY)):
                    if result.status == ComponentStatus.HEALTHY:
                        st.success(f"{result.component_name} is operational.")
                    elif result.status == ComponentStatus.DEGRADED:
                        st.warning(f"{result.component_name} is experiencing issues.")
                    else:
                        st.error(f"{result.component_name} is unavailable.")

                    if result.details:
                        st.markdown("**Connection Details:**")
                        for key, value in result.details.items():
                            display_key = key.replace("_", " ").title()
                            st.markdown(f"- **{display_key}**: `{value}`")

                    if result.latency_ms is not None:
                        st.markdown(f"- **Latency**: `{result.latency_ms} ms`")

                    if result.error_message:
                        st.markdown("---")
                        st.markdown(f"**⚠️ Error**: {result.error_message}")

                    if result.recommendation:
                        st.markdown(f"**💡 Recommendation**: {result.recommendation}")

                    st.caption(f"Checked at: {result.checked_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")

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
    Renders the Executive Investigation Summary section.
    Synthesizes the direct answer, KPI metrics, supporting evidence,
    recommendation, and investigation metadata.
    """
    st.header("📊 Executive Investigation Summary")

    # Synthesize Direct Answer to User Question
    q_lower = report.user_question.lower()
    is_historical = any(k in q_lower for k in ["when", "past", "history", "historical", "last week", "yesterday", "earlier", "spike last"])

    if is_historical:
        answer_text = (
            f"The platform executed real-time diagnostic probes via SSH over target host `testserv.ortusolis.in:22`. "
            f"However, it could not determine historical metric trends because historical telemetry (e.g. from Prometheus, Grafana, SAR, "
            f"or previously stored investigation metrics) is not currently configured on this host. "
            f"Current real-time diagnostic status: {report.rca.summary if report.rca else 'No real-time anomalies detected.'}"
        )
        inv_status = "INCONCLUSIVE"
        status_badge_str = "⚪ INCONCLUSIVE"
    elif report.status == "FAILED":
        answer_text = (
            "The platform could not determine the root cause because evidence collection failed during the SSH investigation. "
            "Verify SSH credentials and network connectivity to the target host."
        )
        inv_status = "FAILED"
        status_badge_str = "🔴 FAILED"
    elif report.rca and report.rca.overall_confidence >= 0.3:
        answer_text = report.rca.summary
        inv_status = report.status
        status_badge_str = f"🟢 {report.status}" if report.status == "SUCCESS" else f"🟡 {report.status}"
    else:
        answer_text = (
            f"Diagnostic metrics were collected, but evidence was inconclusive to confidently isolate a primary root cause. "
            f"{report.rca.summary if report.rca else ''}"
        )
        inv_status = "INCONCLUSIVE"
        status_badge_str = "⚪ INCONCLUSIVE"

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
            <h4 style="margin: 0 0 12px 0; color: #0D47A1;">Question: "{report.user_question}"</h4>
            <p style="font-size: 1.1em; line-height: 1.6; margin: 0; color: #1A237E;">
                {answer_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Executive Key Metric Row (4 KPI Cards) ────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    confidence_score = report.rca.overall_confidence if report.rca else 0.0
    confidence_pct = f"{round(confidence_score * 100, 1)}%"
    primary_rc = report.rca.primary_root_cause if (report.rca and confidence_score >= 0.3) else "Investigation Inconclusive"
    top_recommendation = report.recommendation.recommended_actions[0].title if (report.recommendation and report.recommendation.recommended_actions) else "N/A"

    with col1:
        st.metric("Investigation Status", inv_status, delta=status_badge_str)
    with col2:
        st.metric("Overall Confidence", confidence_pct)
    with col3:
        st.metric("Primary Root Cause", primary_rc[:35] + "..." if len(primary_rc) > 35 else primary_rc)
    with col4:
        st.metric("Top Recommended Action", top_recommendation[:35] + "..." if len(top_recommendation) > 35 else top_recommendation)

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Key Supporting Evidence Grid ──────────────────────────────────
    st.subheader("🔑 Key Supporting Evidence")
    if report.correlation and report.correlation.findings:
        evidence_data = []
        for f in report.correlation.findings:
            for ev in f.evidences:
                evidence_data.append({
                    "Finding Title": f.title,
                    "Category": f.category.value,
                    "Severity": f.severity.value,
                    "Metric": ev.metric_name,
                    "Observed Value": str(ev.observed_value),
                    "Threshold": str(ev.threshold),
                })
        if evidence_data:
            st.dataframe(evidence_data, use_container_width=True)
        else:
            st.info("No numeric metric thresholds breached during diagnostic execution.")
    else:
        st.info("No correlated findings recorded.")

    # ── Primary Recommended Next Action ──────────────────────────────
    if report.recommendation and report.recommendation.recommended_actions:
        st.subheader("💡 Recommended Next Action")
        action = report.recommendation.recommended_actions[0]
        st.warning(
            f"**Action**: {action.title}\n\n"
            f"**Priority**: `{action.priority.value}` | **Risk Level**: `{action.risk_level.value}` | **Skill Level**: `{action.required_skill_level}`\n\n"
            f"**Reasoning**: {action.reason}\n\n"
            f"**Description**: {action.description}"
        )

    # ── Investigation Metadata Panel ─────────────────────────────────
    st.subheader("ℹ️ Investigation Metadata & Data Quality")
    total_steps = len(report.execution.step_results) if report.execution else 0
    failed_steps = sum(1 for s in report.execution.step_results if s.status.value == "FAILED") if report.execution else 0
    succeeded_steps = total_steps - failed_steps
    data_quality_pct = f"{round((succeeded_steps / total_steps) * 100, 1)}%" if total_steps > 0 else "0%"

    meta_c1, meta_c2, meta_c3, meta_c4 = st.columns(4)
    with meta_c1:
        st.markdown(f"**Investigation ID**:\n`{report.report_id}`")
        st.markdown(f"**Target Server**:\n`testserv.ortusolis.in:22`")
    with meta_c2:
        st.markdown(f"**Start Time (UTC)**:\n`{report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}`")
        st.markdown(f"**Total Duration**:\n`{report.total_execution_time_seconds}s`")
    with meta_c3:
        st.markdown(f"**Commands Executed**:\n`{total_steps}` total (`{succeeded_steps}` ok, `{failed_steps}` failed)")
        st.markdown(f"**Data Quality**:\n`{data_quality_pct}`")
    with meta_c4:
        st.markdown(f"**AI Provider**:\n`{report.rca.metadata.provider_used if report.rca else 'N/A'}`")
        st.markdown(f"**LLM Model**:\n`{report.rca.metadata.model_name if report.rca else 'N/A'}`")


# ─────────────────────────────────────────────────────────────────────
# Technical Pipeline & Audit Trail Rendering (SECONDARY DISPLAY)
# ─────────────────────────────────────────────────────────────────────

def _render_technical_pipeline(report: InvestigationReport):
    """
    Renders the secondary 6-phase technical investigation pipeline and audit trail.
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
            if report.rca:
                st.subheader("🎯 Primary Root Cause")
                st.error(report.rca.primary_root_cause)

                st.subheader("📝 Executive Summary")
                st.info(report.rca.summary)

                st.subheader("💡 Hypotheses & Evidence")
                st.markdown(f"**Primary Hypothesis**: {report.rca.primary_hypothesis.title} (Likelihood: `{report.rca.primary_hypothesis.likelihood_score}`)")
                st.write(report.rca.primary_hypothesis.description)

                st.subheader("🔍 Reasoning Trace")
                for rt in report.rca.reasoning_trace:
                    st.write(f"**Step #{rt.step_number}**: Observation: *{rt.observation}* ➔ Deduction: `{rt.deduction}`")
            else:
                st.write("No RCA available.")

        with tab2:
            if report.recommendation and report.policy_decision:
                st.subheader("📋 Operational Recommendations & Policy Permissions")
                for idx, action in enumerate(report.recommendation.recommended_actions, start=1):
                    req = next((r for r in report.policy_decision.approval_requests if r.recommendation_id == action.recommendation_id), None)
                    perm_badge = req.approval_status.value if req else "PENDING"
                    st.markdown(f"### Action #{idx}: {action.title}  `[{perm_badge}]`")
                    st.write(f"**Category**: {action.category.value} | **Priority**: {action.priority.value} | **Risk**: {action.risk_level.value}")
                    st.write(f"**Reason**: {action.reason}")
                    st.write(f"**Description**: {action.description}")
                    st.divider()
            else:
                st.write("No recommendations available.")

        with tab3:
            if report.correlation:
                st.subheader("🔗 Correlated Operational Findings")
                for f in report.correlation.findings:
                    with st.expander(f"[{f.severity.value}] {f.title} ({f.category.value})"):
                        st.write(f"**Summary**: {f.summary}")
                        st.write(f"**Confidence**: {f.confidence_score}")
                        st.write(f"**Affected Resources**: {f.affected_resources}")
            else:
                st.write("No findings available.")

        with tab4:
            if report.execution:
                st.subheader("⚡ Multi-Command Execution Details")
                for res in report.execution.step_results:
                    with st.expander(f"Order #{res.order}: {res.command_id} (`{res.linux_command}`) - Status: {res.status.value}"):
                        st.code(res.raw_output, language="bash")
            else:
                st.write("No step executions available.")

        with tab5:
            if report.plan:
                st.subheader("🗺️ Phase 1 Investigation Plan Blueprint")
                st.write(f"**Priority**: {report.plan.priority.value} | **Strategy**: {report.plan.execution_strategy.value}")
                for s in report.plan.steps:
                    st.write(f"**Step #{s.order}**: `{s.command_id}` - {s.description}")
            else:
                st.write("No plan available.")

        with tab6:
            if report.policy_decision:
                st.subheader("🛡️ Phase 6 Policy Engine Evaluation")
                st.write(f"**Overall Policy Decision**: `{report.policy_decision.overall_decision.value}`")
                st.write(f"**Evaluation Summary**: {report.policy_decision.summary}")
                for req in report.policy_decision.approval_requests:
                    st.markdown(f"- **{req.recommendation_title}**: `{req.approval_status.value}` (Risk: `{req.risk_level.value}`)")
            else:
                st.write("No policy decisions available.")


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

        with st.spinner("Executing end-to-end investigation pipeline (Phases 1-6)..."):
            workflow = InvestigationWorkflow()
            report: InvestigationReport = workflow.execute_investigation(query.strip())
            st.session_state["last_investigation_report"] = report

    # ── Render Executive Summary & Pipeline if report exists ─────────
    if "last_investigation_report" in st.session_state:
        report = st.session_state["last_investigation_report"]

        # 1. PRIMARY DISPLAY: Executive Investigation Summary (Answers user question first)
        _render_executive_summary(report)

        # 2. SECONDARY DISPLAY: Technical Pipeline & Audit Trail (Phases 1–6)
        _render_technical_pipeline(report)


if __name__ == "__main__":
    render_streamlit_dashboard()
