"""
Purpose
-------
Main backend entrypoint for the AI SRE Platform.
Maintains backward compatibility with ask_server(question) while delegating to the InvestigationWorkflow orchestrator.

Responsibilities
----------------
- Initialize platform dependencies and execute end-to-end investigation workflow.

Does NOT
---------
- Implement business logic or infrastructure network calls directly.
"""

from typing import Any, Dict

from application.workflow import InvestigationWorkflow
from domain.report.models import InvestigationReport
from shared.logging import get_logger

logger = get_logger("AppBackend")


def initialize_backend() -> None:
    """Initialize backend platform services and repository schemas."""
    logger.info("Initializing AI SRE Platform backend services...")


def ask_server(question: str) -> Dict[str, Any]:
    """
    Orchestrates the complete investigation workflow across Phases 1-6.

    Parameters
    ----------
    question : str
        Natural language user question.

    Returns
    -------
    Dict[str, Any]
        Structured dictionary payload for backward compatibility with frontend.py.
    """
    workflow = InvestigationWorkflow()
    report: InvestigationReport = workflow.execute_investigation(question)

    # Legacy response key mapping
    primary_cause = report.rca.primary_root_cause if report.rca else "Investigation complete."
    exec_summary = report.rca.summary if report.rca else "Metrics collected."

    return {
        "success": report.status in ("SUCCESS", "PARTIAL_SUCCESS"),
        "question": question,
        "report_id": report.report_id,
        "answer": f"**Primary Root Cause**: {primary_cause}\n\n**Summary**: {exec_summary}",
        "execution_time_seconds": report.total_execution_time_seconds,
        "timestamp": str(report.created_at),
        "raw_report": report,
    }


def main():
    """Main execution function."""
    initialize_backend()
    res = ask_server("Why is my server slow?")
    print(res["answer"])


if __name__ == "__main__":
    main()