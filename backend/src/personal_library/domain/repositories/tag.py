import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.domain.models.tag import Tag, ArticleTag


class TagRepository:
    """标签数据访问层"""

    async def create(
        self,
        db: AsyncSession,
        name: str,
        user_id: uuid.UUID,
        color: str = "#909399",
    ) -> Tag:
        """创建新标签"""
        tag = Tag(name=name, user_id=user_id, color=color)
        db.add(tag)
        await db.flush()
        await db.refresh(tag)
        return tag

    async def list_by_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[Tag]:
        """查询某个用户的所有标签"""
        stmt = select(Tag).where(Tag.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self,
        db: AsyncSession,
        tag_id: uuid.UUID,
    ) -> Tag | None:
        """根据 ID 查询单个标签"""
        stmt = select(Tag).where(Tag.id == tag_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, db: AsyncSession, tag: Tag) -> None:
        """删除标签（中间表的关联会因 ON DELETE CASCADE 自动清理）"""
        await db.delete(tag)
        await db.flush()

    async def add_to_article(
        self,
        db: AsyncSession,
        article_id: uuid.UUID,
        tag_id: uuid.UUID,
    ) -> ArticleTag | None:
        """给文章打标签。如果已存在则直接返回 None，避免重复关联。"""
        stmt = select(ArticleTag).where(
            ArticleTag.article_id == article_id,
            ArticleTag.tag_id == tag_id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return None

        link = ArticleTag(article_id=article_id, tag_id=tag_id)
        db.add(link)
        await db.flush()
        return link

    async def remove_from_article(
        self,
        db: AsyncSession,
        article_id: uuid.UUID,
        tag_id: uuid.UUID,
    ) -> bool:
        """从文章移除标签，返回是否成功移除"""
        stmt = select(ArticleTag).where(
            ArticleTag.article_id == article_id,
            ArticleTag.tag_id == tag_id,
        )
        result = await db.execute(stmt)
        link = result.scalar_one_or_none()
        if link is None:
            return False
        await db.delete(link)
        await db.flush()
        return True

    async def list_tags_for_article(
        self,
        db: AsyncSession,
        article_id: uuid.UUID,
    ) -> list[Tag]:
        """查询某篇文章的所有标签"""
        stmt = (
            select(Tag)
            .join(ArticleTag, Tag.id == ArticleTag.tag_id)
            .where(ArticleTag.article_id == article_id)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def list_articles_by_tag(
        self,
        db: AsyncSession,
        tag_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        """查询某个标签下的所有文章ID"""
        stmt = select(ArticleTag.article_id).where(ArticleTag.tag_id == tag_id)
        result = await db.execute(stmt)
        return result.scalars().all()
