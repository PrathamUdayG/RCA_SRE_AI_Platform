"""Application boundary around read-only infrastructure capability discovery."""

from typing import Optional

from domain.capability import ServerCapabilities
from infrastructure.capabilities import CapabilityDiscoveryEngine


class CapabilityDiscoveryService:
    """Produces one reusable capability snapshot for an investigation."""

    def __init__(self, engine: Optional[CapabilityDiscoveryEngine] = None):
        self._engine = engine or CapabilityDiscoveryEngine()

    def discover(self) -> ServerCapabilities:
        return self._engine.discover()
