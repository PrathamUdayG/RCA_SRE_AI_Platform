"""Repository contract for investigation-scoped Copilot state."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import ConversationMessage, InvestigationContext


class InvestigationContextRepository(ABC):
    """Persistence boundary for contexts and their conversation messages."""

    @abstractmethod
    def save_context(self, context: InvestigationContext) -> None:
        """Store or replace a completed investigation context."""

    @abstractmethod
    def get_context(self, investigation_id: str) -> Optional[InvestigationContext]:
        """Return a context by its stable investigation identifier."""

    @abstractmethod
    def append_message(self, message: ConversationMessage) -> None:
        """Append a conversation message for an existing investigation."""

    @abstractmethod
    def list_messages(self, investigation_id: str) -> List[ConversationMessage]:
        """Return conversation history in insertion order."""
