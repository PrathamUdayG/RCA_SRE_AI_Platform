"""
Purpose
-------
CLI Presentation Layer for running autonomous incident investigations from the terminal.

Responsibilities
----------------
- Parse CLI arguments, invoke InvestigationWorkflow, and print formatted investigation reports.

Does NOT
---------
- Implement business logic or direct SSH calls.
"""

import sys
from application.workflow import InvestigationWorkflow


def main():
    """CLI Entrypoint for AI SRE Platform."""
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Why is my server slow and unresponsive?"

    print(f"=== AI SRE Platform CLI ===")
    print(f"Query: '{query}'\n")

    workflow = InvestigationWorkflow()
    report = workflow.execute_investigation(query)

    print("\n=======================================================")
    print(f"INVESTIGATION REPORT [{report.report_id}]")
    print("=======================================================")
    print(f"Status: {report.status}")
    print(f"Execution Time: {report.total_execution_time_seconds}s")
    if report.rca:
        print(f"\nPrimary Root Cause: {report.rca.primary_root_cause}")
        print(f"Executive Summary: {report.rca.summary}")
    if report.policy_decision:
        print(f"\nOverall Policy Decision: {report.policy_decision.overall_decision.value}")
        print(f"Approved Actions Count: {len(report.policy_decision.approved_actions)}")
        print(f"Rejected Actions Count: {len(report.policy_decision.rejected_actions)}")


if __name__ == "__main__":
    main()
