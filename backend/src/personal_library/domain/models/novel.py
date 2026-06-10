import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .chapter import Chapter
    from .reading_progress import ReadingProgress
    from .user import User


class Novel(Base, TimestampMixin):
    """小说主表：存储用户上传的每一本小说元数据。"""
    __tablename__ = "novels"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cover_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    total_chapters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_words: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False, default=False
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(back_populates="novels")
    chapters: Mapped[List["Chapter"]] = relationship(
        back_populates="novel",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Chapter.chapter_number",
    )
    reading_progresses: Mapped[List["ReadingProgress"]] = relationship(
        back_populates="novel",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "file_path", name="uq_novel_user_file_path"),
    )

    def __repr__(self) -> str:
        return (
            f"<Novel(id={self.id!s}, title={self.title!r}, "
            f"author={self.author!r}, file_type={self.file_type})>"
        )