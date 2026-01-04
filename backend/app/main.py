"""Forseti Emblem RAG Backend - Main Application Entry Point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import check_db_connection, init_db, pgvector_available
from .docs_auth import setup_docs_auth
from .routes import chat, wiki


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Runs on startup and shutdown.
    """
    # Startup
    logger.info(f"Starting Forseti Emblem RAG Backend in {settings.environment} mode")
    logger.info(f"Debug mode: {settings.debug}")

    # Check database connection
    if check_db_connection():
        logger.info("Database connection successful")
        # Initialize database tables (will skip if pgvector is missing)
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Database initialization skipped/failed: {e}")
    else:
        logger.warning("Database connection failed - some features may not work")

    yield

    # Shutdown
    logger.info("Shutting down Forseti Emblem RAG Backend")


app = FastAPI(
    title="Forseti Emblem RAG Backend",
    description="RAG-powered API for Fire Emblem game knowledge",
    version="0.1.0",
    lifespan=lifespan,
)

docs_auth_enabled, docs_auth_mode = setup_docs_auth(app, logger=logger)

# CORS configuration for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local frontend dev
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://localhost:8000",  # Same-origin requests
        # Production URLs will be added via environment or here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health() -> dict:
    """Health check endpoint."""
    db_status = "connected" if check_db_connection() else "disconnected"
    vector_status = (
        "available"
        if (db_status == "connected" and pgvector_available())
        else "missing"
    )
    return {
        "status": "ok",
        "environment": settings.environment,
        "database": db_status,
        "pgvector": vector_status,
    }


@app.get("/config", tags=["system"])
def get_config() -> dict:
    """
    Get current configuration (non-sensitive values only).

    Useful for debugging configuration issues.
    """
    return {
        "environment": settings.environment,
        "database_host": settings.database_host,
        "database_port": settings.database_port,
        "database_name": settings.database_name,
        "openai_embedding_model": settings.openai_embedding_model,
        "openai_chat_model": settings.openai_chat_model,
        "openai_api_key_set": bool(settings.openai_api_key),
        "debug": settings.debug,
        "log_level": settings.log_level,
        "docs_auth_enabled": docs_auth_enabled,
        "docs_auth_mode": docs_auth_mode,
    }


app.include_router(wiki.router)
app.include_router(chat.router)
