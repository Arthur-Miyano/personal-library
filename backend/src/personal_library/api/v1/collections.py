from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
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
