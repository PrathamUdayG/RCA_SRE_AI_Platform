"""
Purpose
-------
Paramiko implementation of ISSHClient interface.

Responsibilities
----------------
- Manage SSH client connections and execute remote commands using Paramiko.

Does NOT
---------
- Implement business logic or command selection.
"""

from typing import Any, Dict, Optional

from shared.config import get_settings
from shared.logging import get_logger
from infrastructure.ssh.ssh_client import execute_command as legacy_ssh_execute

from .ssh_interface import ISSHClient

logger = get_logger("ParamikoSSHClient")


class ParamikoSSHClient(ISSHClient):
    """
    Paramiko SSH client implementation of ISSHClient interface.
    """

    def __init__(self, host: str = None, port: int = None, username: str = None, password: str = None):
        settings = get_settings()
        self.host = host or settings.ssh.host
        self.port = port or settings.ssh.port
        self.username = username or settings.ssh.username
        self.password = password or settings.ssh.password

    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Executes remote Linux command via Paramiko SSH Client.
        """
        logger.info(f"Executing remote command: '{command}' on {self.host}:{self.port}")
        return legacy_ssh_execute(command)
