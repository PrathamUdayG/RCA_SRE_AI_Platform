"""
Unit tests for safe read-only Command Registry and Parser Framework (Phase A).
"""

import unittest
from commands import COMMANDS, get_command
from infrastructure.parsers.linux_parsers import parse_command_output, COMMAND_PARSER_MAP
from infrastructure.registry.command_registry import LinuxCommandRegistry
from infrastructure.registry.parser_registry import LinuxParserRegistry


class TestCommandRegistryAndParsers(unittest.TestCase):

    def test_all_commands_have_descriptions_and_categories(self):
        registry = LinuxCommandRegistry()
        all_cmds = registry.get_all_commands()
        self.assertGreaterEqual(len(all_cmds), 40)

        for key, info in all_cmds.items():
            self.assertIn("description", info, f"Command '{key}' missing description")
            self.assertIn("command", info, f"Command '{key}' missing linux command string")
            self.assertIn("category", info, f"Command '{key}' missing category")

    def test_all_commands_are_read_only(self):
        """Ensure no command mutates system state (rm, kill, systemctl stop, apt, etc.)."""
        registry = LinuxCommandRegistry()
        for key, info in registry.get_all_commands().items():
            cmd_str = info["command"].lower()
            self.assertNotIn("rm ", cmd_str)
            self.assertNotIn("kill ", cmd_str)
            self.assertNotIn("reboot", cmd_str)
            self.assertNotIn("shutdown", cmd_str)
            self.assertNotIn("systemctl stop", cmd_str)
            self.assertNotIn("systemctl restart", cmd_str)
            self.assertNotIn("apt ", cmd_str)
            self.assertNotIn("yum ", cmd_str)

    def test_every_command_has_a_registered_parser(self):
        registry = LinuxCommandRegistry()
        for key in registry.list_command_keys():
            self.assertIn(key, COMMAND_PARSER_MAP, f"Command key '{key}' has no registered parser in COMMAND_PARSER_MAP")

    def test_parser_returns_structured_dict(self):
        parser_reg = LinuxParserRegistry()

        # Test uptime parser
        uptime_sample = "10:15:30 up 5 days, 4:20, 2 users, load average: 0.15, 0.25, 0.30"
        res = parser_reg.parse("uptime", uptime_sample)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["users_logged_in"], 2)
        self.assertEqual(res["load_average_1m"], 0.15)

        # Test memory parser
        free_sample = "              total        used        free      shared  buff/cache   available\nMem:           8000        2000        1000         100        5000        5500\nSwap:          2000         100        1900"
        res_mem = parser_reg.parse("memory_usage", free_sample)
        self.assertEqual(res_mem["memory"]["total_mb"], 8000)
        self.assertEqual(res_mem["memory"]["used_mb"], 2000)

        # Test df -h parser
        df_sample = "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        100G   40G   60G  40% /"
        res_df = parser_reg.parse("disk_usage", df_sample)
        self.assertEqual(len(res_df["filesystems"]), 1)
        self.assertEqual(res_df["filesystems"][0]["usage_percent"], "40%")


if __name__ == "__main__":
    unittest.main()
