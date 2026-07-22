"""
Purpose
-------
Abstract SSH client interface for remote Linux command execution.

Responsibilities
----------------
- Define the contract for SSH connection managers (Paramiko, AsyncSSH, MockSSH).

Does NOT
---------
- Depend on specific SSH vendor libraries.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class ISSHClient(ABC):
    """
    Abstract interface for SSH connection clients.
    """

    @abstractmethod
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Executes a remote Linux command over SSH and returns output dictionary.

        Parameters
        ----------
        command : str
            Linux command string to execute.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing 'host', 'output', and 'error'.
        """
        pass
