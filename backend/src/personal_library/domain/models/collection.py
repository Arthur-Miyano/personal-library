import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    DECIMAL,
    ForeignKey,
    Integer,
    String,
    Text,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .article import Article


class Collection(Base, TimestampMixin):
    """合集/收藏夹表：用户可以创建多个收藏夹来组织文章"""
    __tablename__ = "collections"

    # 收藏夹属于哪个用户
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 收藏夹名称（必填）
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 描述（可选，默认空字符串）
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # 颜色（前端展示用，默认 Element Plus 主色）
    color: Mapped[str] = mapped_column(String(9), nullable=False, default="#409EFF")

    # 图标（前端展示用，默认文件夹图标）
    icon: Mapped[str] = mapped_column(String(50), nullable=False, default="folder")

    # 排序权重（数字越小越靠前）
    sort_order: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 5), nullable=False, default=Decimal("0")
    )

    articles: Mapped[List["Article"]] = relationship(
        "Article",
        secondary="collection_articles",
        back_populates="collections",
        lazy="selectin",
    )


class CollectionArticle(Base):
    """中间表：收藏夹与文章的多对多关联"""
    __tablename__ = "collection_articles"

    # 联合主键：收藏夹ID + 文章ID
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("collections.id", ondelete="CASCADE"),
        primary_key=True,
    )

    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # 在收藏夹内的排序（数字越小越靠前）
    sort_order: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 5), nullable=False, default=Decimal("0")
    )

    # 版本号（乐观锁，后续可能用到）
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 加入收藏夹的时间
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
