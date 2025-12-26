"""Application configuration using Pydantic Settings.

Loads environment variables and dotenv files.

Important: when running locally, you might execute `uvicorn` from the repo root.
To keep config deterministic, we always prefer `backend/.env`.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    _BACKEND_DIR = Path(__file__).resolve().parents[1]

    model_config = SettingsConfigDict(
        # Prefer the backend folder env files regardless of current working directory.
        # Note: pydantic-settings expects a string/path or a LIST (not a tuple).
        env_file=[
            _BACKEND_DIR / ".env",
            _BACKEND_DIR / ".env.local",
            ".env",
        ],
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Environment
    environment: Literal["local", "development", "staging", "production"] = Field(
        default="local",
        description="Runtime environment",
    )

    # Database
    database_host: str = Field(default="localhost", description="PostgreSQL host")
    database_port: int = Field(default=5432, description="PostgreSQL port")
    database_user: str = Field(default="postgres", description="PostgreSQL user")
    database_password: str = Field(default="postgres", description="PostgreSQL password")
    database_name: str = Field(default="forsetiemblem", description="PostgreSQL database name")
    database_url: str | None = Field(
        default=None,
        description="Full database URL (overrides individual settings if provided)",
    )

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key for embeddings")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model name",
    )
    openai_chat_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI chat model for RAG responses",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload (local dev only)")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    @computed_field
    @property
    def database_url_computed(self) -> str:
        """Construct database URL from components or use provided URL."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @computed_field
    @property
    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.environment == "local"

    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience export
settings = get_settings()
