"""add chapters fields and novel soft delete

Revision ID: d4e5f6a7b8c9
Revises: e1b42610b358
Create Date: 2026-06-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "e1b42610b358"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chapters", sa.Column("is_prologue", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("chapters", sa.Column("content_hash", sa.String(64), nullable=False, server_default=sa.text("''")))
    op.add_column("chapters", sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("novels", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    op.drop_column("novels", "is_deleted")
    op.drop_column("chapters", "needs_review")
    op.drop_column("chapters", "content_hash")
    op.drop_column("chapters", "is_prologue")
