"""
Purpose
-------
PostgreSQL persistence repository for logging command execution audit records.

Responsibilities
----------------
- Initialize logs table and save audit records into PostgreSQL database.

Does NOT
---------
- Embed raw SQL statements inside domain business logic.
"""

from typing import Any, Dict, Optional
from database import create_logs_table, save_log
from shared.logging import get_logger

logger = get_logger("PostgresAuditRepository")


class PostgresAuditRepository:
    """
    Repository wrapping PostgreSQL audit logging operations.
    """

    def __init__(self, init_on_start: bool = True):
        if init_on_start:
            self.initialize_schema()

    def initialize_schema(self) -> None:
        """Initializes database schema tables safely."""
        try:
            create_logs_table()
        except Exception as err:
            logger.warning(f"Database schema initialization deferred: {err}")

    def save_audit_log(self, host: str, command: str, output: str, error: str) -> None:
        """Saves execution audit record to PostgreSQL."""
        try:
            save_log(host=host, command=command, output=output, error=error)
        except Exception as err:
            logger.warning(f"Failed to log audit record to PostgreSQL: {err}")
