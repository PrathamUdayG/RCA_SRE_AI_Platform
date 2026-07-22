"""
Purpose
-------
Streamlit Web Dashboard Presentation Layer for the AI SRE Platform.

Responsibilities
----------------
- Render interactive web dashboard UI for natural language incident investigations.
- Render multi-stage tabs for Investigation Reports, AI RCA, Recommendations, and Policy Decisions.

Does NOT
---------
- Implement business logic or direct SSH/database calls.
"""

import streamlit as st
from application.workflow import InvestigationWorkflow
from domain.report.models import InvestigationReport


def render_streamlit_dashboard():
    """Renders the Streamlit AI SRE Platform Web Dashboard."""
    st.set_page_config(
        page_title="AI SRE Platform for Autonomous Operations",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🛡️ AI SRE Platform for Autonomous Operations")
    st.caption("End-to-End Autonomous Incident Investigation, Correlation, RCA, Recommendation & Policy Engine")

    # Sidebar Information
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

        st.success(f"Investigation completed in {report.total_execution_time_seconds}s!")

        # Key Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Overall Status", report.status)
        with col2:
            st.metric("Duration", f"{report.total_execution_time_seconds}s")
        with col3:
            findings_count = len(report.correlation.findings) if report.correlation else 0
            st.metric("Correlated Findings", findings_count)
        with col4:
            policy_status = report.policy_decision.overall_decision.value if report.policy_decision else "N/A"
            st.metric("Policy Status", policy_status)

        st.divider()

        # Multi-Stage Tab Views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🧠 Root Cause Analysis (Phase 4)",
            "📋 Guidance & Policy (Phases 5 & 6)",
            "🔗 Correlated Findings (Phase 3)",
            "⚡ Step Executions (Phase 2)",
            "🗺️ Investigation Plan (Phase 1)",
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
                st.write("No recommendations or policy decisions available.")

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


if __name__ == "__main__":
    render_streamlit_dashboard()
