"""
Purpose
-------
Infrastructure service wrapping the whitelisted Linux Command Registry.

Responsibilities
----------------
- Provide lookup mechanisms for whitelisted Linux command definitions.

Does NOT
---------
- Hardcode Linux commands inside application use cases.
"""

from typing import Any, Dict, List, Optional
from commands import COMMANDS, get_command


class LinuxCommandRegistry:
    """
    Infrastructure service wrapping the Linux Command Registry.
    """

    def __init__(self, commands_data: Dict[str, Any] = None):
        self._commands = commands_data or COMMANDS

    def get_command(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves whitelisted command info dictionary by identifier."""
        return get_command(command_id)

    def list_command_keys(self) -> List[str]:
        """Returns list of registered command identifiers."""
        return list(self._commands.keys())

    def get_all_commands(self) -> Dict[str, Any]:
        """Returns complete command registry dictionary."""
        return self._commands
