import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.domain.models.collection import Collection, CollectionArticle


class CollectionRepository:
    """收藏夹数据访问层"""

    async def create(
        self,
        db: AsyncSession,
        name: str,
        user_id: uuid.UUID,
        description: str = "",
        color: str = "#409EFF",
        icon: str = "folder",
    ) -> Collection:
        """创建新收藏夹"""
        collection = Collection(
            name=name,
            user_id=user_id,
            description=description,
            color=color,
            icon=icon,
        )
        db.add(collection)
        await db.flush()
        await db.refresh(collection)
        return collection

    async def list_by_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[Collection]:
        """查询某个用户的所有收藏夹，按 sort_order 升序排列"""
        stmt = (
            select(Collection)
            .where(Collection.user_id == user_id)
            .order_by(Collection.sort_order.asc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self,
        db: AsyncSession,
        collection_id: uuid.UUID,
    ) -> Collection | None:
        """根据 ID 查询单个收藏夹"""
        stmt = select(Collection).where(Collection.id == collection_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_article(
        self,
        db: AsyncSession,
        collection_id: uuid.UUID,
        article_id: uuid.UUID,
    ) -> CollectionArticle | None:
        """把文章加入收藏夹。如果已存在则返回 None，避免重复关联。"""
        stmt = select(CollectionArticle).where(
            CollectionArticle.collection_id == collection_id,
            CollectionArticle.article_id == article_id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return None

        link = CollectionArticle(
            collection_id=collection_id,
            article_id=article_id,
        )
        db.add(link)
        await db.flush()
        return link

    async def remove_article(
        self,
        db: AsyncSession,
        collection_id: uuid.UUID,
        article_id: uuid.UUID,
    ) -> bool:
        """从收藏夹移除文章，返回是否成功移除"""
        stmt = select(CollectionArticle).where(
            CollectionArticle.collection_id == collection_id,
            CollectionArticle.article_id == article_id,
        )
        result = await db.execute(stmt)
        link = result.scalar_one_or_none()
        if link is None:
            return False
        await db.delete(link)
        await db.flush()
        return True

    async def list_articles_in_collection(
        self,
        db: AsyncSession,
        collection_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        """查询某个收藏夹里的所有文章ID，按 sort_order 升序排列"""
        stmt = (
            select(CollectionArticle.article_id)
            .where(CollectionArticle.collection_id == collection_id)
            .order_by(CollectionArticle.sort_order.asc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update(
        self,
        db: AsyncSession,
        collection: Collection,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        sort_order: float | Decimal | None = None,
    ) -> None:
        """更新收藏夹字段（只改非 None 值）"""
        if name is not None:
            collection.name = name
        if description is not None:
            collection.description = description
        if color is not None:
            collection.color = color
        if icon is not None:
            collection.icon = icon
        if sort_order is not None:
            collection.sort_order = Decimal(str(sort_order))
        await db.flush()

    async def update_article_sort(
        self,
        db: AsyncSession,
        collection_id: uuid.UUID,
        article_id: uuid.UUID,
        sort_order: float,
    ) -> bool:
        """更新收藏夹内文章的排序，返回是否成功"""
        from sqlalchemy import update
        stmt = (
            update(CollectionArticle)
            .where(CollectionArticle.collection_id == collection_id)
            .where(CollectionArticle.article_id == article_id)
            .values(sort_order=Decimal(str(sort_order)))
        )
        result = await db.execute(stmt)
        return result.rowcount > 0
