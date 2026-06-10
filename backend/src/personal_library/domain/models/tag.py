import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .article import Article


class Tag(Base, TimestampMixin):
    """标签表：用户可以给文章打标签"""
    __tablename__ = "tags"

    # 标签属于哪个用户
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 标签名称（必填）
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 颜色（前端展示用，默认灰色）
    color: Mapped[str] = mapped_column(String(9), nullable=False, default="#909399")

    # 同一个用户下标签名不能重复
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
    )

    articles: Mapped[List["Article"]] = relationship(
        "Article",
        secondary="article_tags",
        back_populates="tags",
        lazy="selectin",
    )


class ArticleTag(Base):
    """中间表：文章与标签的多对多关联"""
    __tablename__ = "article_tags"

    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
