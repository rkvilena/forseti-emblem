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
    database_password: str = Field(
        default="postgres", description="PostgreSQL password"
    )
    database_name: str = Field(
        default="forsetiemblem", description="PostgreSQL database name"
    )
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

    # Cloudflare Turnstile
    turnstile_secret_key: str = Field(
        default="",
        description="Cloudflare Turnstile secret key",
    )
    turnstile_enabled: bool = Field(
        default=True,
        description="Enable Cloudflare Turnstile verification",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(
        default=False, description="Enable auto-reload (local dev only)"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Redis / Rate limiting
    redis_url: str | None = Field(
        default=None,
        description="Redis connection URL for caching and rate limiting",
    )
    rate_limit_short_window_seconds: int = Field(
        default=60,
        description="Short-window size in seconds for IP rate limiting",
    )
    rate_limit_short_ip_requests: int = Field(
        default=3,
        description="Max number of requests per IP within the short window",
    )
    rate_limit_long_window_seconds: int = Field(
        default=86400,
        description="Long-window size in seconds for IP rate limiting",
    )
    rate_limit_long_ip_requests: int = Field(
        default=25,
        description="Max number of requests per IP within the long window",
    )
    session_rate_limit_long_ip_requests: int = Field(
        default=15,
        description="Max number of requests per anonymous session within the long window",
    )
    session_cookie_name: str = Field(
        default="fe_anon_session",
        description="Cookie name for anonymous chat sessions",
    )
    session_cookie_ttl_seconds: int = Field(
        default=86400,
        description="TTL for anonymous session cookie (seconds)",
    )

    # Cost controls
    request_max_chars: int = Field(
        default=300,
        description="Maximum allowed message length in characters for chat endpoints",
    )
    rag_top_k_max: int = Field(
        default=8,
        description="Maximum allowed top_k for RAG retrieval",
    )
    session_cooldown_threshold: int = Field(
        default=3,
        description="Number of rapid requests per session before cooldown applies",
    )
    session_cooldown_window_seconds: int = Field(
        default=60,
        description="Window size in seconds to measure cooldown threshold",
    )
    session_cooldown_duration_seconds: int = Field(
        default=30,
        description="Cooldown duration in seconds after threshold is exceeded",
    )

    # API Docs (Swagger/ReDoc)
    docs_auth_enabled: bool = Field(
        default=False,
        description="Require HTTP Basic Auth for /docs, /redoc, and /openapi.json",
    )
    docs_auth_mode: Literal["basic", "session"] = Field(
        default="basic",
        description="Docs auth mode: 'basic' uses browser Basic Auth; 'session' uses a signed cookie via /docs-login",
    )
    docs_username: str = Field(
        default="",
        description="HTTP Basic Auth username for API docs",
    )
    docs_password: str = Field(
        default="",
        description="HTTP Basic Auth password for API docs",
    )
    docs_session_ttl_seconds: int = Field(
        default=10,
        description="Docs session cookie TTL in seconds (session auth mode)",
    )
    docs_session_secret: str = Field(
        default="",
        description="Secret used to sign docs session cookies (required for session auth mode)",
    )

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
