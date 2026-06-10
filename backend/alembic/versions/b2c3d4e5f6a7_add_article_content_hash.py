"""add article content_hash with partial unique index

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-10

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("content_hash", sa.String(64), nullable=False, server_default=sa.text("''")))
    op.execute("CREATE UNIQUE INDEX ix_articles_user_content_hash ON articles(user_id, content_hash) WHERE content_hash != ''")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_articles_user_content_hash")
    op.drop_column("articles", "content_hash")
