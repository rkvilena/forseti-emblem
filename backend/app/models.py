from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pageid: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    infobox_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    game: Mapped[str | None] = mapped_column(String(255), nullable=True)
    objective: Mapped[str | None] = mapped_column(String(255), nullable=True)
    units_allowed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    units_gained: Mapped[str | None] = mapped_column(Text, nullable=True)
    boss: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_infobox: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    chunks: Mapped[list["ChapterChunk"]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan"
    )


class ChapterChunk(Base):
    __tablename__ = "chapter_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    chapter: Mapped["Chapter"] = relationship(back_populates="chunks")

    __table_args__ = (
        UniqueConstraint(
            "chapter_id", "kind", "chunk_index", name="uix_chapter_chunk_order"
        ),
    )
