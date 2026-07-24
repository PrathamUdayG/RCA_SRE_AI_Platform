"""Process-local context store for the initial Copilot workspace.

This repository deliberately has no SSH, database, or network dependency. A durable
repository can implement the same domain contract later without changing Copilot use
cases.
"""

from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional

from domain.copilot import ConversationMessage, InvestigationContext, InvestigationContextRepository


class InMemoryInvestigationContextRepository(InvestigationContextRepository):
    """In-memory repository suitable for a Streamlit session or unit tests."""

    def __init__(self):
        self._contexts: Dict[str, InvestigationContext] = {}
        self._messages: DefaultDict[str, List[ConversationMessage]] = defaultdict(list)

    def save_context(self, context: InvestigationContext) -> None:
        self._contexts[context.investigation_id] = context

    def get_context(self, investigation_id: str) -> Optional[InvestigationContext]:
        return self._contexts.get(investigation_id)

    def append_message(self, message: ConversationMessage) -> None:
        if message.investigation_id not in self._contexts:
            raise KeyError(f"No investigation context exists for '{message.investigation_id}'.")
        self._messages[message.investigation_id].append(message)

    def list_messages(self, investigation_id: str) -> List[ConversationMessage]:
        return list(self._messages.get(investigation_id, []))
