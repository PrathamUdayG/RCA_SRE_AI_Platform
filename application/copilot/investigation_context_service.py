"""Capture completed reports as safe, reusable Copilot context."""

from domain.copilot import InvestigationContext, InvestigationContextRepository
from domain.report.models import InvestigationReport

from .follow_up_question_service import FollowUpQuestionService


class InvestigationContextService:
    """Creates a context only from completed investigation artifacts."""

    def __init__(self, repository: InvestigationContextRepository, follow_up_service: FollowUpQuestionService | None = None):
        self._repository = repository
        self._follow_up_service = follow_up_service or FollowUpQuestionService()

    def capture(self, report: InvestigationReport) -> InvestigationContext:
        investigation_id = report.plan.investigation_id if report.plan else report.report_id
        context = InvestigationContext(
            investigation_id=investigation_id,
            report_id=report.report_id,
            report=report,
            suggested_questions=self._follow_up_service.generate(report),
        )
        self._repository.save_context(context)
        return context
