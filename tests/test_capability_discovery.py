"""Capability discovery and planner-gating tests using only a mock SSH client."""

import unittest

from domain.capability import InvestigationDomain
from domain.investigation import InvestigationPlanner
from infrastructure.capabilities import CapabilityDiscoveryEngine


class DiscoveryMockSSHClient:
    def execute_command(self, command: str):
        self.command = command
        return {
            "host": "mock-host",
            "output": (
                "OS|Ubuntu 24.04 LTS\nDISTRO|ubuntu\nKERNEL|6.8.0\n"
                "TECH|docker|Docker version 27.0.0\nTECH|psql|psql (PostgreSQL) 16.3\n"
                "TECH|systemctl|systemd 255\n"
            ),
            "error": "",
        }


class TestCapabilityDiscovery(unittest.TestCase):
    def test_discovery_creates_structured_capabilities(self):
        client = DiscoveryMockSSHClient()
        capabilities = CapabilityDiscoveryEngine(ssh_client=client).discover()

        self.assertIn("command -v", client.command)
        self.assertTrue(capabilities.technology_installed("Docker"))
        self.assertTrue(capabilities.supports(InvestigationDomain.CONTAINERS))
        self.assertFalse(capabilities.supports(InvestigationDomain.KUBERNETES))
        self.assertTrue(capabilities.supports(InvestigationDomain.POSTGRESQL))

    def test_planner_excludes_kubernetes_commands_when_unavailable(self):
        capabilities = CapabilityDiscoveryEngine(ssh_client=DiscoveryMockSSHClient()).discover()
        plan = InvestigationPlanner().create_plan("Why is Kubernetes unhealthy?", capabilities)

        self.assertEqual(plan.metadata["matched_template"], "container_issues")
        self.assertNotIn("kubectl_pods", [step.command_id for step in plan.steps])
        self.assertIn("not detected", plan.metadata["capability_notice"])

    def test_planner_keeps_docker_commands_when_docker_is_detected(self):
        capabilities = CapabilityDiscoveryEngine(ssh_client=DiscoveryMockSSHClient()).discover()
        plan = InvestigationPlanner().create_plan("Why is my Docker container unhealthy?", capabilities)

        self.assertIn("docker_containers", [step.command_id for step in plan.steps])
        self.assertNotIn("kubectl_pods", [step.command_id for step in plan.steps])


if __name__ == "__main__":
    unittest.main()
