import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .chapter import Chapter
    from .novel import Novel
    from .user import User


class ReadingProgress(Base, TimestampMixin):
    """阅读进度表：记录用户每本书的阅读位置。"""
    __tablename__ = "reading_progresses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    novel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("novels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    position: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="reading_progresses")
    novel: Mapped["Novel"] = relationship(back_populates="reading_progresses")
    chapter: Mapped[Optional["Chapter"]] = relationship(
        back_populates="reading_progresses"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "novel_id", name="uq_reading_progress_user_novel"
        ),
        CheckConstraint(
            "percentage >= 0 AND percentage <= 100",
            name="ck_reading_progress_percentage_range",
        ),
        Index("ix_reading_progress_user_novel", "user_id", "novel_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ReadingProgress(user={self.user_id!s}, novel={self.novel_id!s}, "
            f"percentage={self.percentage})>"
        )