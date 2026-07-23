"""
Purpose
-------
PostgreSQL Database health checker for the AI SRE Platform.

Responsibilities
----------------
- Establish a lightweight psycopg2 connection to the configured PostgreSQL instance.
- Execute minimal diagnostic queries (SELECT version(), SELECT current_user).
- Measure connection latency.
- Return a structured ComponentHealthResult with database metadata.

Does NOT
---------
- Modify database state, create tables, or insert records.
- Implement business logic or domain rules.
"""

import time
from datetime import datetime
from typing import Optional

import psycopg2

from domain.health.models import ComponentHealthResult, ComponentStatus
from shared.config import get_settings
from shared.logging import get_logger

logger = get_logger("DatabaseHealthChecker")


class DatabaseHealthChecker:
    """
    Infrastructure health checker that probes PostgreSQL database connectivity.

    Uses psycopg2 to establish a test connection and collect database metadata
    (host, port, database name, current user, version, connection latency).

    Parameters
    ----------
    host : Optional[str]
        Database hostname. Defaults to platform settings.
    port : Optional[int]
        Database port. Defaults to platform settings.
    name : Optional[str]
        Database name. Defaults to platform settings.
    user : Optional[str]
        Database user. Defaults to platform settings.
    password : Optional[str]
        Database password. Defaults to platform settings.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        name: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        settings = get_settings()
        self._host = host or settings.db.host
        self._port = port or settings.db.port
        self._name = name or settings.db.name
        self._user = user or settings.db.user
        self._password = password or settings.db.password

    def check(self) -> ComponentHealthResult:
        """
        Performs a lightweight PostgreSQL connectivity health check.

        Returns
        -------
        ComponentHealthResult
            Health result containing database metadata or error details.
        """
        checked_at = datetime.utcnow()
        start_time = time.time()

        try:
            conn = psycopg2.connect(
                host=self._host,
                port=self._port,
                database=self._name,
                user=self._user,
                password=self._password,
                connect_timeout=10,
            )
            connection_time_ms = round((time.time() - start_time) * 1000, 2)

            cursor = conn.cursor()

            # Collect database version
            cursor.execute("SELECT version();")
            db_version_full = cursor.fetchone()[0]
            # Extract concise version string (e.g., "PostgreSQL 16.3")
            db_version = db_version_full.split(",")[0].strip() if db_version_full else "Unknown"

            # Collect current user
            cursor.execute("SELECT current_user;")
            current_user = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            logger.info(f"Database health check passed: {self._host}:{self._port}/{self._name} ({connection_time_ms}ms)")

            return ComponentHealthResult(
                component_name="PostgreSQL Database",
                status=ComponentStatus.HEALTHY,
                details={
                    "host": self._host,
                    "port": self._port,
                    "database_name": self._name,
                    "current_user": current_user,
                    "database_version": db_version,
                    "connection_latency_ms": connection_time_ms,
                },
                checked_at=checked_at,
                latency_ms=connection_time_ms,
            )

        except Exception as exc:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            error_msg = f"Unable to connect to PostgreSQL at {self._host}:{self._port}/{self._name} — {type(exc).__name__}: {exc}"
            logger.warning(f"Database health check failed: {error_msg}")

            return ComponentHealthResult(
                component_name="PostgreSQL Database",
                status=ComponentStatus.UNHEALTHY,
                details={
                    "host": self._host,
                    "port": self._port,
                    "database_name": self._name,
                },
                error_message=error_msg,
                recommendation=(
                    "Verify that PostgreSQL service is running and database credentials are correct. "
                    "Check DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD in your .env file."
                ),
                checked_at=checked_at,
                latency_ms=elapsed_ms,
            )
