"""SQLAlchemy-backed persistence adapters.

The only place that builds SQLAlchemy queries for chapters/chunks. Use cases and
pipeline components depend on the repository's domain operations instead of ORM
mechanics.
"""

from .repository import ChapterRepository

__all__ = ["ChapterRepository"]
