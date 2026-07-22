"""
Purpose
-------
Package exports for Infrastructure Persistence Repositories.

Responsibilities
----------------
- Expose PostgresAuditRepository.

Does NOT
---------
- Contain business logic.
"""

from .audit_repository import PostgresAuditRepository

__all__ = ["PostgresAuditRepository"]
