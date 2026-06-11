from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.domain.models.user import User
from personal_library.domain.repositories.article import ArticleRepository
from personal_library.domain.repositories.collection import CollectionRepository
from personal_library.infrastructure.schemas.collection import (
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse,
)

router = APIRouter(prefix="/collections", tags=["collections"])
repo = CollectionRepository()
article_repo = ArticleRepository()


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    body: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新收藏夹"""
    collection = await repo.create(
        db=db,
        name=body.name,
        user_id=current_user.id,
        description=body.description,
        color=body.color,
        icon=body.icon,
    )
    return collection


@router.get(
    "",
    response_model=List[CollectionResponse],
)
async def list_collections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有收藏夹"""
    collections = await repo.list_by_user(
        db=db,
        user_id=current_user.id,
    )
    return collections


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
)
async def get_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个收藏夹详情"""
    collection = await repo.get_by_id(db=db, collection_id=collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏夹不存在"
        )
    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该收藏夹"
        )
    return collection


@router.post(
    "/{collection_id}/articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_article_to_collection(
    collection_id: UUID,
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """把文章加入收藏夹"""
    # 先确认收藏夹存在且属于当前用户
    collection = await repo.get_by_id(db=db, collection_id=collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏夹不存在"
        )
    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该收藏夹"
        )

    # 再确认文章存在且属于当前用户
    article = await article_repo.get_by_id(db=db, article_id=article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    if article.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该文章"
        )

    await repo.add_article(
        db=db,
        collection_id=collection_id,
        article_id=article_id,
    )
    return None


@router.delete(
    "/{collection_id}/articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_article_from_collection(
    collection_id: UUID,
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从收藏夹移除文章"""
    # 先确认收藏夹存在且属于当前用户
    collection = await repo.get_by_id(db=db, collection_id=collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏夹不存在"
        )
    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该收藏夹"
        )

    removed = await repo.remove_article(
        db=db,
        collection_id=collection_id,
        article_id=article_id,
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该文章不在此收藏夹中"
        )
    return None


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
)
async def update_collection(
    collection_id: UUID,
    body: CollectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改收藏夹信息（包括排序）"""
    collection = await repo.get_by_id(db=db, collection_id=collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏夹不存在"
        )
    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该收藏夹"
        )

    await repo.update(
        db=db,
        collection=collection,
        name=body.name,
        description=body.description,
        color=body.color,
        icon=body.icon,
        sort_order=body.sort_order,
    )
    await db.refresh(collection)
    return collection


@router.patch(
    "/{collection_id}/articles/{article_id}/sort",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_article_sort_in_collection(
    collection_id: UUID,
    article_id: UUID,
    sort_order: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """调整收藏夹内文章的排序位置"""
    collection = await repo.get_by_id(db=db, collection_id=collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="收藏夹不存在"
        )
    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作该收藏夹"
        )

    updated = await repo.update_article_sort(
        db=db,
        collection_id=collection_id,
        article_id=article_id,
        sort_order=sort_order,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该文章不在此收藏夹中"
        )
    return None


@router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除收藏夹"""
    collection = await repo.get_by_id(db=db, collection_id=collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收藏夹不存在")
    if collection.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")
    await repo.delete(db=db, collection=collection)
    return None


# ===================== 批量操作 =====================

class BatchArticleRequest(BaseModel):
    article_ids: list[UUID]


@router.post("/{collection_id}/articles/batch", status_code=status.HTTP_204_NO_CONTENT)
async def batch_add_articles(
    collection_id: UUID,
    body: BatchArticleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量添加文章到合集"""
    collection = await repo.get_by_id(db=db, collection_id=collection_id)
    if not collection or collection.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合集不存在")

    # 批量查询文章所有权，避免 N+1
    if body.article_ids:
        from sqlalchemy import select as sqla_select
        articles_stmt = sqla_select(Article).where(
            Article.id.in_(body.article_ids),
            Article.user_id == current_user.id,
        )
        result = await db.execute(articles_stmt)
        valid_ids = {a.id for a in result.scalars().all()}
    else:
        valid_ids = set()

    for aid in body.article_ids:
        if aid in valid_ids:
            await repo.add_article(db=db, collection_id=collection_id, article_id=aid)
    await db.flush()
    return Response(status_code=204)


class MoveArticleRequest(BaseModel):
    direction: str  # "up" | "down"


@router.post("/{collection_id}/articles/{article_id}/move", status_code=status.HTTP_204_NO_CONTENT)
async def move_article(
    collection_id: UUID,
    article_id: UUID,
    body: MoveArticleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """移动合集内文章排序（与相邻文章交换位置）"""
    from personal_library.domain.models.collection import CollectionArticle, Collection

    # 先校验合集所有权
    collection = await db.scalar(
        select(Collection).where(Collection.id == collection_id)
    )
    if not collection or collection.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合集不存在")

    current = await db.scalar(
        select(CollectionArticle).where(
            CollectionArticle.collection_id == collection_id,
            CollectionArticle.article_id == article_id,
        )
    )
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不在此合集中")

    if body.direction == "up":
        neighbor = await db.scalar(
            select(CollectionArticle).where(
                CollectionArticle.collection_id == collection_id,
                CollectionArticle.sort_order < current.sort_order,
            ).order_by(CollectionArticle.sort_order.desc()).limit(1)
        )
    else:
        neighbor = await db.scalar(
            select(CollectionArticle).where(
                CollectionArticle.collection_id == collection_id,
                CollectionArticle.sort_order > current.sort_order,
            ).order_by(CollectionArticle.sort_order.asc()).limit(1)
        )

    if not neighbor:
        return Response(status_code=204)  # 已在边界

    tmp = current.sort_order
    current.sort_order = neighbor.sort_order
    neighbor.sort_order = tmp
    await db.flush()
    return Response(status_code=204)
