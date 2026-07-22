"""
Purpose
-------
Infrastructure service wrapping Linux stdout text parsers.

Responsibilities
----------------
- Delegate raw terminal output string parsing to structured JSON functions.

Does NOT
---------
- Embed parsing regular expressions inside domain business logic.
"""

from typing import Any, Dict
from parsers import parse_output


class LinuxParserRegistry:
    """
    Infrastructure service providing parser resolution for Linux stdout text.
    """

    def parse(self, command: str, raw_output: str) -> Dict[str, Any]:
        """
        Parses raw Linux stdout string into structured JSON output.

        Parameters
        ----------
        command : str
            Linux command executed.
        raw_output : str
            Raw stdout text returned over SSH.

        Returns
        -------
        Dict[str, Any]
            Structured dictionary payload.
        """
        return parse_output(command, raw_output)
