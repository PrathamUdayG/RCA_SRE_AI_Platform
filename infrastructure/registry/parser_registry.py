"""
Purpose
-------
Infrastructure service wrapping Linux stdout text parsers.

Responsibilities
----------------
- Delegate raw terminal output string parsing to structured JSON functions.
"""

from typing import Any, Dict
from infrastructure.parsers.linux_parsers import parse_command_output


class LinuxParserRegistry:
    """
    Infrastructure service providing parser resolution for Linux stdout text.
    """

    def parse(self, command_identifier: str, raw_output: str) -> Dict[str, Any]:
        """
        Parses raw Linux stdout string into structured JSON output.

        Parameters
        ----------
        command_identifier : str
            Command key (e.g. 'cpu_load') or raw Linux command string.
        raw_output : str
            Raw stdout text returned over SSH.

        Returns
        -------
        Dict[str, Any]
            Structured telemetry dictionary payload.
        """
        return parse_command_output(command_identifier, raw_output)
