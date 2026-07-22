"""
Purpose
-------
Centralized configuration manager for the AI SRE Platform.

Responsibilities
----------------
- Load and validate environment variables for SSH, DB, LLM, and Platform timeouts.
- Provide strongly-typed settings objects.

Does NOT
---------
- Hardcode credentials or execute infrastructure operations.
"""

import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class SSHSettings(BaseModel):
    """SSH connection settings."""
    host: str = Field(default_factory=lambda: os.getenv("SSH_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("SSH_PORT", "22")))
    username: str = Field(default_factory=lambda: os.getenv("SSH_USERNAME", ""))
    password: str = Field(default_factory=lambda: os.getenv("SSH_PASSWORD", ""))
    timeout: int = Field(default=10)


class DatabaseSettings(BaseModel):
    """PostgreSQL database connection settings."""
    host: str = Field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = Field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    name: str = Field(default_factory=lambda: os.getenv("DB_NAME", "postgres"))
    user: str = Field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))


class LLMSettings(BaseModel):
    """AI LLM provider settings."""
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    default_model: str = Field(default="gemini-2.5-flash")


class PlatformSettings(BaseModel):
    """Global AI SRE Platform settings."""
    ssh: SSHSettings = Field(default_factory=SSHSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    log_level: str = Field(default="INFO")
    default_step_timeout_seconds: int = Field(default=30)


_settings_instance = None


def get_settings() -> PlatformSettings:
    """Returns singleton instance of PlatformSettings."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = PlatformSettings()
    return _settings_instance
