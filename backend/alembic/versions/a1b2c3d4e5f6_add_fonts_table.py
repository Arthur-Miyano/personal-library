"""add fonts table

Revision ID: a1b2c3d4e5f6
Revises: f8a9b0c1d2e3
Create Date: 2026-06-09

"""
from typing import Sequence, Union
import uuid as uuid_lib
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fonts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.String(500), nullable=False),
        sa.Column("font_family", sa.String(200), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fonts_user_id", "fonts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_fonts_user_id")
    op.drop_table("fonts")
