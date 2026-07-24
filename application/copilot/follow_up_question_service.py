"""Generate bounded, context-aware follow-up questions without an LLM call."""

from typing import List

from domain.report.models import InvestigationReport


class FollowUpQuestionService:
    """Derives useful next questions exclusively from completed report artifacts."""

    _MAX_QUESTIONS = 8

    def generate(self, report: InvestigationReport) -> List[str]:
        questions: List[str] = ["Why is this happening?", "Explain this like I'm new to Linux."]
        findings = report.correlation.findings if report.correlation else []
        categories = {finding.category.value for finding in findings}

        if "CPU" in categories:
            questions.extend(["Explain load average.", "Show the CPU evidence."])
        if "MEMORY" in categories:
            questions.extend(["Is memory contributing to this?", "Show the memory evidence."])
        if "PROCESS" in categories or "CPU" in categories:
            questions.append("Which processes are relevant to this finding?")
        if "SERVICE" in categories or "CONTAINER" in categories:
            questions.append("Which services or containers are affected?")

        if report.recommendation and report.recommendation.recommended_actions:
            questions.extend(["What should I do next?", "How can I prevent this from happening again?"])

        unique_questions: List[str] = []
        for question in questions:
            if question not in unique_questions:
                unique_questions.append(question)
        return unique_questions[: self._MAX_QUESTIONS]
