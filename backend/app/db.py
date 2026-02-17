"""
Database configuration and session management.

Uses settings from config module for connection parameters.
Supports both local development and production deployments.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings


logger = logging.getLogger(__name__)

# Create engine with settings from config
engine = create_engine(
    settings.database_url_computed,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,  # Check connection health before using
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.

    Yields a database session and ensures it's closed after use.

    Usage:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session outside of FastAPI dependencies.

    Usage:
        with get_db_context() as db:
            db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database extensions only.

    Schema changes are managed via Alembic migrations.
    """
    pgvector_ok = ensure_pgvector_extension()
    if not pgvector_ok:
        logger.warning(
            "pgvector extension is not available on the connected PostgreSQL instance. "
            "Install pgvector on the database server and run again."
        )
    else:
        logger.info("pgvector extension available")


def pgvector_available() -> bool:
    """Return True if the 'vector' extension is installed on the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
            ).scalar_one()
            return bool(result)
    except SQLAlchemyError as e:
        logger.error(f"Failed to check pgvector extension: {e}")
        return False


def ensure_pgvector_extension() -> bool:
    """
    Try to enable pgvector extension.

    Returns True if pgvector is available (already installed or successfully enabled).
    Returns False if pgvector is missing on the server.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    except SQLAlchemyError as e:
        # Common when pgvector is not installed on the server.
        logger.warning(
            "Could not enable pgvector extension (CREATE EXTENSION vector failed). "
            f"Reason: {e}"
        )
    return pgvector_available()


def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
