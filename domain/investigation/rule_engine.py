"""
Purpose:
--------
Rule matcher engine for analyzing user questions and selecting investigation rules.

Responsibilities:
-----------------
- Match user natural language keywords to investigation templates and priority levels.

Does NOT:
---------
- Call LLM APIs.
- Execute SSH commands.
"""

from typing import List, Tuple

from .models import InvestigationPriority, InvestigationStep
from .template_registry import TemplateRegistry


class RuleEngine:
    """
    Engine matching natural language questions to templates and priority levels using rule patterns.
    """

    def __init__(self, template_registry: TemplateRegistry = None):
        self.registry = template_registry or TemplateRegistry()

    def match_rules(self, question: str) -> Tuple[List[InvestigationStep], InvestigationPriority, str]:
        """
        Analyzes the user question and returns (steps, priority, matched_template_name).
        """
        q_lower = question.lower()

        if any(term in q_lower for term in ["slow", "lag", "unresponsive", "performance", "freeze"]):
            return (
                self.registry.get_template("slow_server"),
                InvestigationPriority.HIGH,
                "slow_server",
            )

        if any(term in q_lower for term in ["ram", "memory", "swap", "oom"]):
            return (
                self.registry.get_template("high_memory"),
                InvestigationPriority.MEDIUM,
                "high_memory",
            )

        if any(term in q_lower for term in ["cpu", "processor", "load"]):
            return (
                self.registry.get_template("high_cpu"),
                InvestigationPriority.MEDIUM,
                "high_cpu",
            )

        if any(term in q_lower for term in ["disk", "space", "full", "filesystem", "inode", "partition"]):
            return (
                self.registry.get_template("disk_space"),
                InvestigationPriority.MEDIUM,
                "disk_space",
            )

        if any(term in q_lower for term in ["network", "ip", "port", "connection", "socket", "dns"]):
            return (
                self.registry.get_template("network_connectivity"),
                InvestigationPriority.MEDIUM,
                "network_connectivity",
            )

        # Fallback to general health investigation
        return (
            self.registry.get_template("general_health"),
            InvestigationPriority.LOW,
            "general_health",
        )
