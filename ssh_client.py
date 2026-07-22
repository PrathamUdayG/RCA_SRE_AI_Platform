"""What does this file do?

This file has one job only:

Connect to the server and execute a command.
"""

import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("SSH_HOST", "127.0.0.1")
PORT = int(os.getenv("SSH_PORT", 22))
USERNAME = os.getenv("SSH_USERNAME")
PASSWORD = os.getenv("SSH_PASSWORD")


class SSHClientManager:
    """Manages SSH connections and remote command execution using Paramiko."""

    def __init__(self, host=HOST, port=PORT, username=USERNAME, password=PASSWORD):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        """Connect to the remote SSH server."""
        print(f"Connecting to SSH host: {self.host}:{self.port}...")
        self.client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=10
        )
        print(f"Connected to {self.host} successfully.\n")

    def execute_command(self, command):
        """Execute a remote command and return (stdout, stderr)."""
        stdin, stdout, stderr = self.client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        return output, error

    def close(self):
        """Close the SSH client connection."""
        self.client.close()
        print(f"Closed SSH connection to {self.host}.")


def execute_command(command: str) -> dict:
    """Convenience function to execute a single SSH command on the remote host."""
    mgr = SSHClientManager()
    mgr.connect()
    try:
        output, error = mgr.execute_command(command)
        return {
            "host": mgr.host,
            "output": output,
            "error": error
        }
    finally:
        mgr.close()

