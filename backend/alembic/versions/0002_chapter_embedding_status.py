from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_chapter_embedding_status"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Every existing chapter starts as ``pending``; already fully-embedded
    # chapters are promoted to ``searchable`` in the same migration so status
    # reflects reality immediately after the deploy.
    op.add_column(
        "chapters",
        sa.Column(
            "embedding_status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
    )

    op.execute(
        """
        UPDATE chapters
        SET embedding_status = 'searchable'
        WHERE EXISTS (
            SELECT 1 FROM chapter_chunks c WHERE c.chapter_id = chapters.id
        )
        AND NOT EXISTS (
            SELECT 1 FROM chapter_chunks c
            WHERE c.chapter_id = chapters.id AND c.embedding IS NULL
        )
        """
    )


def downgrade() -> None:
    op.drop_column("chapters", "embedding_status")
