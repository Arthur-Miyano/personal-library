"""fix cover_path to URL format

Revision ID: f8a9b0c1d2e3
Revises: d4e5f6a7b8c9
Create Date: 2026-06-09

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE novels
        SET cover_path = REPLACE(cover_path, './uploads/', '/uploads/')
        WHERE cover_path LIKE './uploads/%'
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE novels
        SET cover_path = REPLACE(cover_path, '/uploads/', './uploads/')
        WHERE cover_path LIKE '/uploads/%'
    """)
