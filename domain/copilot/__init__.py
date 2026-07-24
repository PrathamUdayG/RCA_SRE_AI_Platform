"""Domain contracts and models for evidence-grounded Copilot conversations."""

from .models import (
    ConversationMessage,
    ConversationRole,
    EvidenceCitation,
    InvestigationContext,
)
from .repository import InvestigationContextRepository

__all__ = [
    "ConversationMessage",
    "ConversationRole",
    "EvidenceCitation",
    "InvestigationContext",
    "InvestigationContextRepository",
]
