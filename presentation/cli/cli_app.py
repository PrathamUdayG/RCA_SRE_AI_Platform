"""
Purpose
-------
CLI Presentation Layer for running autonomous incident investigations from the terminal.

Responsibilities
----------------
- Parse CLI arguments, invoke InvestigationWorkflow, and print formatted investigation reports defensively.

Does NOT
--------
- Implement business logic or direct SSH calls.
"""

from enum import Enum
import sys
from typing import Any
from application.workflow import InvestigationWorkflow


def safe_get(obj: Any, attr_path: str, default: Any = "N/A") -> Any:
    """Safely retrieves a nested attribute path from an object, handling None and Enums."""
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
    if curr is None:
        return default
    if isinstance(curr, Enum):
        return curr.value
    return curr


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

    rep_id = getattr(report, "report_id", "UNKNOWN")
    rep_status = safe_get(report, "status", "UNKNOWN")
    exec_time = getattr(report, "total_execution_time_seconds", 0.0)

    print("\n=======================================================")
    print(f"INVESTIGATION REPORT [{rep_id}]")
    print("=======================================================")
    print(f"Status: {rep_status}")
    print(f"Execution Time: {exec_time}s")

    rca = getattr(report, "rca", None)
    if rca:
        print(f"\nPrimary Root Cause: {safe_get(rca, 'primary_root_cause', 'N/A')}")
        print(f"Executive Summary: {safe_get(rca, 'summary', 'N/A')}")

    policy_decision = getattr(report, "policy_decision", None)
    if policy_decision:
        dec = safe_get(policy_decision, "overall_decision", "N/A")
        app_count = len(getattr(policy_decision, "approved_actions", []))
        rej_count = len(getattr(policy_decision, "rejected_actions", []))
        print(f"\nOverall Policy Decision: {dec}")
        print(f"Approved Actions Count: {app_count}")
        print(f"Rejected Actions Count: {rej_count}")


if __name__ == "__main__":
    main()
