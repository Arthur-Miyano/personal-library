import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .novel import Novel
    from .reading_progress import ReadingProgress


class Chapter(Base, TimestampMixin):
    """章节表：存储每本小说的章节内容及在原文中的字节偏移位置。"""
    __tablename__ = "chapters"

    novel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("novels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    start_position: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_position: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_prologue: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, default=""
    )
    needs_review: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    novel: Mapped["Novel"] = relationship(back_populates="chapters")
    reading_progresses: Mapped[List["ReadingProgress"]] = relationship(
        back_populates="chapter"
    )

    __table_args__ = (
        UniqueConstraint(
            "novel_id", "chapter_number", name="uq_chapter_novel_chapter_number"
        ),
        CheckConstraint(
            "start_position >= 0", name="ck_chapter_start_position_positive"
        ),
        CheckConstraint(
            "end_position > start_position", name="ck_chapter_end_position_greater"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Chapter(id={self.id!s}, novel_id={self.novel_id!s}, "
            f"number={self.chapter_number}, title={self.title!r})>"
        )