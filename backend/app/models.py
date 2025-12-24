from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .db import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    pageid = Column(Integer, unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    infobox_title = Column(String(255), nullable=True)
    game = Column(String(255), nullable=True)
    objective = Column(String(255), nullable=True)
    units_allowed = Column(Integer, nullable=True)
    units_gained = Column(Text, nullable=True)
    boss = Column(Text, nullable=True)
    raw_infobox = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chunks = relationship("ChapterChunk", back_populates="chapter", cascade="all, delete-orphan")


class ChapterChunk(Base):
    __tablename__ = "chapter_chunks"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    section_title = Column(String(255), nullable=True)
    kind = Column(String(50), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chapter = relationship("Chapter", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("chapter_id", "kind", "chunk_index", name="uix_chapter_chunk_order"),
    )
