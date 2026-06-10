from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.domain.models.user import User
from personal_library.domain.repositories.article import ArticleRepository
from personal_library.domain.repositories.tag import TagRepository
from personal_library.infrastructure.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse

router = APIRouter(prefix="/articles", tags=["articles"])
repo = ArticleRepository()
tag_repo = TagRepository()


@router.post(
    "",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_article(
    body: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建一篇新文章"""
    article = await repo.create(
        db=db,
        title=body.title,
        raw_text=body.raw_text,
        user_id=current_user.id,
    )
    return article


@router.get(
    "",
    response_model=List[ArticleResponse],
)
async def list_articles(
    tag_id: UUID | None = Query(None, description="按标签ID筛选文章"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询当前用户所有的文章，可选按标签筛选"""
    articles = await repo.list_by_user(
        db=db,
        user_id=current_user.id,
        tag_id=tag_id,
    )
    return articles


@router.get(
    "/{article_id}",
    response_model=ArticleResponse,
)
async def get_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询单篇文章详情（只能查看自己的文章）"""
    article = await repo.get_by_id(
        db=db,
        article_id=article_id,
    )

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )

    if article.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="你没有权限查看这篇文章"
        )

    return article


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """软删除文章（只能删除自己的）"""
    article = await repo.get_by_id(
        db=db,
        article_id=article_id,
    )

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )

    if article.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该文章"
        )

    await repo.soft_delete(
        db=db,
        article=article,
    )

    return None


@router.post(
    "/{article_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_tag_to_article(
    article_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """给文章打标签"""
    # 确认文章存在且属于当前用户
    article = await repo.get_by_id(db=db, article_id=article_id)
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

    # 确认标签存在且属于当前用户
    tag = await tag_repo.get_by_id(db=db, tag_id=tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标签不存在"
        )
    if tag.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权使用该标签"
        )

    await tag_repo.add_to_article(
        db=db,
        article_id=article_id,
        tag_id=tag_id,
    )
    return None


@router.delete(
    "/{article_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_tag_from_article(
    article_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从文章移除标签"""
    # 确认文章存在且属于当前用户
    article = await repo.get_by_id(db=db, article_id=article_id)
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

    removed = await tag_repo.remove_from_article(
        db=db,
        article_id=article_id,
        tag_id=tag_id,
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该文章没有这个标签"
        )
    return None


@router.get(
    "/trash/list",
    response_model=List[ArticleResponse],
)
async def list_trash_articles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询回收站里的文章（已软删除的）"""
    articles = await repo.list_trash_by_user(
        db=db,
        user_id=current_user.id,
    )
    return articles


@router.patch(
    "/{article_id}/restore",
    response_model=ArticleResponse,
)
async def restore_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从回收站恢复文章"""
    article = await repo.get_by_id(
        db=db,
        article_id=article_id,
        include_deleted=True,
    )

    if not article or not article.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在或不在回收站中"
        )
    if article.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权恢复该文章"
        )

    await repo.restore(db=db, article=article)
    await db.refresh(article)
    return article


@router.delete(
    "/{article_id}/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def permanently_delete_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """彻底删除文章（不可恢复）"""
    article = await repo.get_by_id(
        db=db,
        article_id=article_id,
        include_deleted=True,
    )

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    if article.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该文章"
        )

    await repo.hard_delete(db=db, article=article)
    return None


@router.patch(
    "/{article_id}",
    response_model=ArticleResponse,
)
async def update_article(
    article_id: UUID,
    body: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改文章（只更新传了的字段）"""
    article = await repo.get_by_id(db=db, article_id=article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在"
        )
    if article.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该文章"
        )

    await repo.update(
        db=db,
        article=article,
        title=body.title,
        raw_text=body.raw_text,
    )
    await db.refresh(article)
    return article
