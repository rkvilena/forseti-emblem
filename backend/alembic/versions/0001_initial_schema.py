from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pageid", sa.Integer(), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("infobox_title", sa.String(length=255), nullable=True),
        sa.Column("game", sa.String(length=255), nullable=True),
        sa.Column("objective", sa.String(length=255), nullable=True),
        sa.Column("units_allowed", sa.Integer(), nullable=True),
        sa.Column("units_gained", sa.Text(), nullable=True),
        sa.Column("boss", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("raw_infobox", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index("ix_chapters_id", "chapters", ["id"], unique=False)
    op.create_index("ix_chapters_pageid", "chapters", ["pageid"], unique=True)
    op.create_index("ix_chapters_title", "chapters", ["title"], unique=False)
    op.create_index("ix_chapters_game", "chapters", ["game"], unique=False)

    op.create_table(
        "chapter_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "chapter_id", "kind", "chunk_index", name="uix_chapter_chunk_order"
        ),
    )

    op.create_index("ix_chapter_chunks_id", "chapter_chunks", ["id"], unique=False)
    op.create_index(
        "ix_chapter_chunks_chapter_id",
        "chapter_chunks",
        ["chapter_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_chapter_chunks_chapter_id", table_name="chapter_chunks")
    op.drop_index("ix_chapter_chunks_id", table_name="chapter_chunks")
    op.drop_table("chapter_chunks")

    op.drop_index("ix_chapters_game", table_name="chapters")
    op.drop_index("ix_chapters_title", table_name="chapters")
    op.drop_index("ix_chapters_pageid", table_name="chapters")
    op.drop_index("ix_chapters_id", table_name="chapters")
    op.drop_table("chapters")
