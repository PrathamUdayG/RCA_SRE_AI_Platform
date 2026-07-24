"""Models for a Copilot conversation anchored to one investigation."""

from datetime import datetime
from enum import Enum
from typing import List
from uuid import uuid4

from pydantic import BaseModel, Field

from domain.report.models import InvestigationReport


class ConversationRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class EvidenceCitation(BaseModel):
    """A traceable reference to evidence already collected by an investigation."""

    finding_title: str
    metric_name: str
    observed_value: str
    threshold: str = "N/A"
    source_command: str


class ConversationMessage(BaseModel):
    """A single message in an investigation-scoped conversation."""

    message_id: str = Field(default_factory=lambda: str(uuid4()))
    investigation_id: str
    role: ConversationRole
    content: str
    citations: List[EvidenceCitation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvestigationContext(BaseModel):
    """The immutable investigation artifact bundle used by the Copilot.

    The report is captured after an investigation completes. Conversation services only
    read this artifact; they do not invoke SSH, command execution, or remediation.
    """

    investigation_id: str
    report_id: str
    report: InvestigationReport
    suggested_questions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
