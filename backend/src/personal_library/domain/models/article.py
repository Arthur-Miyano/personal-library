import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .collection import Collection
    from .tag import Tag


class Article(Base, TimestampMixin):
    """文章表：存储用户导入的每一篇文章"""
    __tablename__ = "articles"

    # 文章标题（必填，最多500字）
    title: Mapped[str] = mapped_column(
        String(500), nullable=False, index=True
    )

    # 文章原始文本（必填）
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    # 字数（默认0）
    word_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # 来源类型：paste（粘贴）、upload（上传）等
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="paste"
    )

    # 来源名称（比如文件名）
    source_name: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    # 状态：草稿 draft、已排版 formatted 等
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )

    # 软删除标记（False=正常，True=已删）
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # 内容 SHA256 哈希（去重用，空串=未计算）
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, default=""
    )

    # 这篇文章属于哪个用户（外键关联到 users 表）
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary="article_tags",
        back_populates="articles",
        lazy="selectin",
    )
    collections: Mapped[List["Collection"]] = relationship(
        "Collection",
        secondary="collection_articles",
        back_populates="articles",
        lazy="selectin",
    )

