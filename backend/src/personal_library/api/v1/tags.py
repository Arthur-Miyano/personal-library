from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.domain.models.user import User
from personal_library.domain.models.tag import Tag
from personal_library.domain.repositories.tag import TagRepository
from personal_library.infrastructure.schemas.tag import TagCreate, TagResponse

router = APIRouter(prefix="/tags", tags=["tags"])
repo = TagRepository()


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_or_get_tag(
    body: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建标签，已存在则返回已有标签 (upsert)"""
    name = body.name.strip()
    color = body.color or "#C85D5D"

    # 大小写不敏感查找已有标签
    existing = await db.scalar(
        select(Tag).where(
            Tag.user_id == current_user.id,
            func.lower(Tag.name) == name.lower(),
        )
    )
    if existing:
        return existing  # 200 OK

    try:
        tag = await repo.create(db=db, name=name, user_id=current_user.id, color=color)
        return tag
    except IntegrityError:
        await db.rollback()
        # 并发窗口：另一个请求刚好创建了同名标签，重新查找
        existing = await db.scalar(
            select(Tag).where(
                Tag.user_id == current_user.id,
                func.lower(Tag.name) == name.lower(),
            )
        )
        if existing:
            return existing
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="标签创建冲突")


@router.get("", response_model=List[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的所有标签"""
    tags = await repo.list_by_user(db=db, user_id=current_user.id)
    return tags


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除标签（会同时移除该标签与所有文章的关联）"""
    tag = await repo.get_by_id(db=db, tag_id=tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")
    if tag.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除该标签")

    await repo.delete(db=db, tag=tag)
    return None
