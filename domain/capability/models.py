"""Strongly typed capability-discovery results used by planning and presentation."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TechnologyCategory(str, Enum):
    CONTAINER = "CONTAINER"
    ORCHESTRATION = "ORCHESTRATION"
    DATABASE = "DATABASE"
    WEB_SERVER = "WEB_SERVER"
    RUNTIME = "RUNTIME"
    MESSAGE_BROKER = "MESSAGE_BROKER"
    CLOUD_CLI = "CLOUD_CLI"
    SYSTEM = "SYSTEM"
    STORAGE = "STORAGE"


class InvestigationDomain(str, Enum):
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK = "NETWORK"
    SERVICES = "SERVICES"
    CONTAINERS = "CONTAINERS"
    KUBERNETES = "KUBERNETES"
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    REDIS = "REDIS"


class DetectedTechnology(BaseModel):
    name: str
    category: TechnologyCategory
    installed: bool
    version: Optional[str] = None
    detection_method: str
    confidence: float = Field(ge=0.0, le=1.0)


class InvestigationCapability(BaseModel):
    domain: InvestigationDomain
    supported: bool
    reason: str
    required_technologies: List[str] = Field(default_factory=list)


class ServerCapabilities(BaseModel):
    host: str = "unknown"
    operating_system: Optional[str] = None
    linux_distribution: Optional[str] = None
    kernel_version: Optional[str] = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    discovery_duration_seconds: float = Field(default=0.0, ge=0.0)
    technologies: List[DetectedTechnology] = Field(default_factory=list)
    investigation_capabilities: List[InvestigationCapability] = Field(default_factory=list)

    def supports(self, domain: InvestigationDomain) -> bool:
        return any(item.domain == domain and item.supported for item in self.investigation_capabilities)

    def technology_installed(self, name: str) -> bool:
        return any(item.name == name and item.installed for item in self.technologies)
