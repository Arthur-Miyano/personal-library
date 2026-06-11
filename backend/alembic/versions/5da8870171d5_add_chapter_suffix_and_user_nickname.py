"""add chapter suffix and user nickname

Revision ID: 5da8870171d5
Revises: b2c3d4e5f6a7
Create Date: 2026-06-10 20:27:53.552189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5da8870171d5'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # chapter.suffix — add with default for existing rows, then alter to NOT NULL
    op.add_column('chapters', sa.Column('suffix', sa.String(length=4), nullable=True))
    op.execute("UPDATE chapters SET suffix = '' WHERE suffix IS NULL")
    op.alter_column('chapters', 'suffix', nullable=False)

    # 替换唯一约束
    op.drop_constraint('uq_chapter_novel_chapter_number', 'chapters', type_='unique')
    op.create_unique_constraint('uq_chapter_novel_chapter_suffix', 'chapters', ['novel_id', 'chapter_number', 'suffix'])

    # user.nickname
    op.add_column('users', sa.Column('nickname', sa.String(length=100), nullable=True))
    op.execute("UPDATE users SET nickname = '' WHERE nickname IS NULL")
    op.alter_column('users', 'nickname', nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'nickname')
    op.drop_constraint('uq_chapter_novel_chapter_suffix', 'chapters', type_='unique')
    op.create_unique_constraint('uq_chapter_novel_chapter_number', 'chapters', ['novel_id', 'chapter_number'])
    op.drop_column('chapters', 'suffix')
    # ### end Alembic commands ###
