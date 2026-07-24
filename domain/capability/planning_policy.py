"""Pure domain policy that removes steps requiring unavailable technology."""

from typing import Dict, List, Tuple

from domain.investigation.models import InvestigationStep

from .models import InvestigationDomain, ServerCapabilities


class CapabilityAwarePlanPolicy:
    """Maps technology-specific command steps to investigation-domain support."""

    _STEP_REQUIREMENTS: Dict[str, InvestigationDomain] = {
        "docker_containers": InvestigationDomain.CONTAINERS,
        "docker_images": InvestigationDomain.CONTAINERS,
        "docker_system_info": InvestigationDomain.CONTAINERS,
        "kubectl_nodes": InvestigationDomain.KUBERNETES,
        "kubectl_pods": InvestigationDomain.KUBERNETES,
        "kubectl_services": InvestigationDomain.KUBERNETES,
    }

    def filter_steps(
        self, steps: List[InvestigationStep], capabilities: ServerCapabilities
    ) -> Tuple[List[InvestigationStep], List[str]]:
        allowed: List[InvestigationStep] = []
        skipped: List[str] = []
        for step in steps:
            required_domain = self._STEP_REQUIREMENTS.get(step.command_id)
            if required_domain and not capabilities.supports(required_domain):
                skipped.append(step.command_id)
                continue
            allowed.append(step)
        return allowed, skipped
