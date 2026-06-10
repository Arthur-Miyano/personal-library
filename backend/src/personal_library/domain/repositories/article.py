from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from personal_library.core.xss import sanitize_html
from personal_library.domain.models.article import Article


class ArticleRepository:
    """文章仓库：用于操作数据库中的文章数据存取"""

    async def create(
        self,
        db: AsyncSession,
        title: str,
        raw_text: str,
        user_id: UUID,
        source_type: str = "paste",
        source_name: str | None = None,
        word_count: int | None = None,
        content_hash: str = "",
    ) -> Article:
        """创建一篇文章并保存到数据库"""
        raw_text = sanitize_html(raw_text)

        if word_count is None:
            word_count = len(raw_text)

        article = Article(
            title=title,
            raw_text=raw_text,
            user_id=user_id,
            source_type=source_type,
            source_name=source_name,
            word_count=word_count,
            content_hash=content_hash,
        )
        db.add(article)
        await db.flush()
        await db.refresh(article)
        return article

    async def list_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        tag_id: UUID | None = None,
        q: str | None = None,
        collection_id: UUID | None = None,
    ) -> list[Article]:
        """查询某个用户的所有文章（未删除的），可选按标签/关键词/合集筛选"""
        from sqlalchemy import or_

        stmt = (
            select(Article)
            .where(Article.user_id == user_id)
            .where(Article.is_deleted == False)
            .order_by(Article.created_at.desc())
        )

        if tag_id is not None:
            from personal_library.domain.models.tag import ArticleTag
            stmt = stmt.join(
                ArticleTag, Article.id == ArticleTag.article_id
            ).where(ArticleTag.tag_id == tag_id)

        if q:
            stmt = stmt.where(
                or_(
                    Article.title.ilike(f"%{q}%"),
                    Article.raw_text.ilike(f"%{q}%"),
                )
            )

        if collection_id is not None:
            from personal_library.domain.models.collection import CollectionArticle
            stmt = stmt.join(
                CollectionArticle, Article.id == CollectionArticle.article_id
            ).where(CollectionArticle.collection_id == collection_id)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self,
        db: AsyncSession,
        article_id: UUID,
        include_deleted: bool = False,
    ) -> Article | None:
        """根据 ID 查询单篇文章，找不到返回 None"""
        stmt = select(Article).where(Article.id == article_id)
        if not include_deleted:
            stmt = stmt.where(Article.is_deleted == False)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete(
        self,
        db: AsyncSession,
        article: Article,
    ) -> None:
        """软删除一篇文章（把 is_deleted 改成 True）"""
        article.is_deleted = True
        await db.flush()

    async def restore(
        self,
        db: AsyncSession,
        article: Article,
    ) -> None:
        """恢复已软删除的文章"""
        article.is_deleted = False
        await db.flush()

    async def hard_delete(
        self,
        db: AsyncSession,
        article: Article,
    ) -> None:
        """彻底删除文章（从数据库中移除）"""
        await db.delete(article)
        await db.flush()

    async def list_trash_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Article]:
        """查询回收站里的文章（已软删除的）"""
        stmt = (
            select(Article)
            .where(Article.user_id == user_id)
            .where(Article.is_deleted == True)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update(
        self,
        db: AsyncSession,
        article: Article,
        title: str | None = None,
        raw_text: str | None = None,
    ) -> None:
        """更新文章字段（只改传进来的非 None 值）"""
        if title is not None:
            article.title = title
        if raw_text is not None:
            article.raw_text = sanitize_html(raw_text)
            article.word_count = len(article.raw_text)
        await db.flush()

    async def find_duplicate(
        self, db: AsyncSession, user_id: UUID, content_hash: str,
    ) -> Article | None:
        if not content_hash:
            return None
        stmt = select(Article).where(
            Article.user_id == user_id,
            Article.content_hash == content_hash,
            Article.is_deleted == False,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_dedup(
        self, db: AsyncSession, user_id: UUID,
        title: str, raw_text: str, content_hash: str,
        source_type: str = "import", source_name: str | None = None,
    ) -> tuple[bool, Article]:
        if content_hash:
            existing = await self.find_duplicate(db, user_id, content_hash)
            if existing:
                return (False, existing)
        try:
            article = Article(
                title=title, raw_text=sanitize_html(raw_text), user_id=user_id,
                source_type=source_type, source_name=source_name,
                word_count=len(raw_text), content_hash=content_hash,
            )
            db.add(article)
            await db.flush()
            return (True, article)
        except Exception:
            await db.rollback()
            if content_hash:
                existing = await self.find_duplicate(db, user_id, content_hash)
                if existing:
                    return (False, existing)
            raise
