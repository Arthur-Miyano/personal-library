from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.domain.models.user import User
from personal_library.domain.repositories.tag import TagRepository
from personal_library.infrastructure.schemas.tag import TagCreate, TagResponse

router = APIRouter(prefix="/tags", tags=["tags"])
repo = TagRepository()


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tag(
    body: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新标签"""
    tag = await repo.create(
        db=db,
        name=body.name,
        user_id=current_user.id,
        color=body.color,
    )
    return tag


@router.get(
    "",
    response_model=List[TagResponse],
)
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有标签"""
    tags = await repo.list_by_user(db=db, user_id=current_user.id)
    return tags


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除标签（会同时移除该标签与所有文章的关联）"""
    tag = await repo.get_by_id(db=db, tag_id=tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标签不存在"
        )
    if tag.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该标签"
        )

    await repo.delete(db=db, tag=tag)
    return None
