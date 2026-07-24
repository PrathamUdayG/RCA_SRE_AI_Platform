"""Answer follow-ups using existing investigation artifacts only."""

from typing import List

from domain.copilot import (
    ConversationMessage,
    ConversationRole,
    EvidenceCitation,
    InvestigationContext,
    InvestigationContextRepository,
)


class ConversationService:
    """Evidence-grounded conversation engine with no execution capability."""

    def __init__(self, repository: InvestigationContextRepository):
        self._repository = repository

    def answer_follow_up(self, investigation_id: str, question: str) -> ConversationMessage:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Follow-up question must be non-empty.")

        context = self._repository.get_context(investigation_id)
        if context is None:
            raise KeyError(f"No investigation context exists for '{investigation_id}'.")

        self._repository.append_message(ConversationMessage(
            investigation_id=investigation_id,
            role=ConversationRole.USER,
            content=clean_question,
        ))
        answer, citations = self._build_answer(context, clean_question)
        response = ConversationMessage(
            investigation_id=investigation_id,
            role=ConversationRole.ASSISTANT,
            content=answer,
            citations=citations,
        )
        self._repository.append_message(response)
        return response

    @staticmethod
    def _citations(context: InvestigationContext) -> List[EvidenceCitation]:
        citations: List[EvidenceCitation] = []
        for finding in context.report.correlation.findings if context.report.correlation else []:
            for evidence in finding.evidences:
                citations.append(EvidenceCitation(
                    finding_title=finding.title,
                    metric_name=evidence.metric_name,
                    observed_value=str(evidence.observed_value),
                    threshold=str(evidence.threshold) if evidence.threshold is not None else "N/A",
                    source_command=evidence.source_command,
                ))
        return citations

    def _build_answer(self, context: InvestigationContext, question: str) -> tuple[str, List[EvidenceCitation]]:
        report = context.report
        rca = report.rca
        recommendation = report.recommendation
        lower_question = question.lower()
        citations = self._citations(context)

        if any(term in lower_question for term in ("what should", "how do i fix", "what do i do", "prevent")):
            actions = recommendation.recommended_actions if recommendation else []
            if not actions:
                return (
                    "The investigation did not produce a verified remediation action. "
                    "Review the evidence and escalate for a human SRE decision; no action has been performed.",
                    citations,
                )
            action_text = " ".join(
                f"{index}. {action.title}: {action.description}"
                for index, action in enumerate(actions[:3], start=1)
            )
            return (
                f"The evidence-backed recommendations are: {action_text} "
                "These are advisory only; the Copilot has not executed any command or change.",
                citations,
            )

        if any(term in lower_question for term in ("why", "cause", "happening")):
            if rca:
                return (
                    f"The recorded root-cause assessment is: {rca.primary_root_cause}. "
                    f"{rca.summary} This conclusion has confidence {rca.overall_confidence:.0%} "
                    "and is supported by the cited investigation evidence.",
                    citations,
                )

        if any(term in lower_question for term in ("evidence", "show", "process", "load", "memory", "cpu", "service", "container")):
            if citations:
                evidence_text = "; ".join(
                    f"{citation.metric_name}={citation.observed_value} (source: {citation.source_command})"
                    for citation in citations[:5]
                )
                return f"The investigation recorded: {evidence_text}.", citations
            return "No concrete evidence items were recorded for this investigation, so I cannot make a stronger claim.", []

        if any(term in lower_question for term in ("beginner", "explain")) and rca:
            return (
                f"In plain language: {rca.summary} The system collected measurements, found the pattern described in the "
                "root-cause assessment, and then produced recommendations for a human operator to review.",
                citations,
            )

        summary = report.executive_summary.direct_answer if report.executive_summary else "No executive summary is available."
        return (
            f"This follow-up is anchored to the completed investigation of '{report.user_question}'. {summary} "
            "Ask about the cause, evidence, recommended next steps, or a simpler explanation for a grounded answer.",
            citations,
        )
