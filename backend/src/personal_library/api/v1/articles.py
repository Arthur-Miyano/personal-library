from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Form
from pydantic import BaseModel
from sqlalchemy import insert, select
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
    q: str | None = Query(None, description="搜索关键词，匹配标题和正文"),
    collection_id: UUID | None = Query(None, description="按合集ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=200, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询当前用户所有的文章，可选按标签/关键词/合集筛选，支持分页"""
    articles = await repo.list_by_user(
        db=db,
        user_id=current_user.id,
        tag_id=tag_id,
        q=q,
        collection_id=collection_id,
        page=page,
        size=size,
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


# ===================== 批量导入 =====================

from fastapi import UploadFile, File
from personal_library.core.file_extractor import (
    extract_text, ALLOWED_EXTENSIONS, get_title_from_filename, VALID_ENCODINGS, cleanup_text,
)


class BatchImportItem(BaseModel):
    filename: str
    status: str
    title: str | None = None
    article_id: UUID | None = None
    detail: str | None = None


class BatchImportResponse(BaseModel):
    total: int
    success: int
    duplicate: int
    failed: int
    results: list[BatchImportItem]


@router.post("/batch-import", response_model=BatchImportResponse)
async def batch_import_articles(
    files: list[UploadFile] = File(...),
    encoding: str = Form("auto"),
    cleanup: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量导入文章，每个文件生成一篇独立文章（支持 EPUB/PDF/DOCX/TXT/HTML/MD）。"""
    import hashlib

    results: list[BatchImportItem] = []
    success = 0
    duplicate = 0
    failed = 0

    for file in files:
        filename = file.filename or "未命名文件"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        ext = f".{ext}" if ext else ""

        if ext not in ALLOWED_EXTENSIONS:
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail=f"不支持的格式 {ext}"))
            failed += 1
            continue

        if encoding not in VALID_ENCODINGS:
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail=f"不支持的编码: {encoding}"))
            failed += 1
            continue

        try:
            content = await file.read()
        except Exception:
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail="读取文件失败"))
            failed += 1
            continue

        if len(content) == 0:
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail="文件为空"))
            failed += 1
            continue

        if len(content) > 50 * 1024 * 1024:
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail="文件超过 50MB 限制"))
            failed += 1
            continue

        # 魔数检测
        _magic_checks = {
            ".pdf": [lambda b: b[:5] == b"%PDF-"],
            ".epub": [lambda b: b[:4] == b"PK\x03\x04"],
            ".docx": [lambda b: b[:4] == b"PK\x03\x04"],
        }
        checks = _magic_checks.get(ext)
        if checks and not any(c(content) for c in checks):
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail="文件内容不符合声明的类型"))
            failed += 1
            continue
        if ext in (".txt", ".md", ".html") and b"\x00" in content[:8192]:
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail="文件包含空字节，可能是二进制文件"))
            failed += 1
            continue

        try:
            raw_text = extract_text(content, filename, encoding_hint=encoding, errors="replace")
        except ValueError as e:
            results.append(BatchImportItem(filename=filename, status="failed", detail=str(e)))
            failed += 1
            continue
        except UnicodeDecodeError:
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail="编码错误，请尝试手动选择编码"))
            failed += 1
            continue

        if cleanup:
            raw_text = cleanup_text(raw_text)

        if not raw_text.strip():
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail="文件内容为空"))
            failed += 1
            continue

        h = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        existing = await repo.find_duplicate(db, current_user.id, h)
        if existing:
            results.append(BatchImportItem(filename=filename, status="duplicate",
                                           title=existing.title,
                                           detail=f"文件已存在: {existing.title}"))
            duplicate += 1
            continue

        title = get_title_from_filename(filename)
        try:
            article = await repo.create(
                db=db, title=title, raw_text=raw_text, user_id=current_user.id,
                source_type="upload", source_name=filename, content_hash=h,
            )
            results.append(BatchImportItem(filename=filename, status="success",
                                           title=title, article_id=article.id))
            success += 1
        except Exception as e:
            results.append(BatchImportItem(filename=filename, status="failed",
                                           detail=f"数据库写入失败: {str(e)[:200]}"))
            failed += 1

    return BatchImportResponse(
        total=len(files), success=success, duplicate=duplicate, failed=failed, results=results,
    )


# ===================== 批量操作 =====================

class BatchTagRequest(BaseModel):
    article_ids: list[UUID]
    tag_id: UUID


@router.post("/batch-tag", status_code=status.HTTP_204_NO_CONTENT)
async def batch_add_tag(
    body: BatchTagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """多篇文章批量关联同一个标签"""
    tag = await tag_repo.get_by_id(db=db, tag_id=body.tag_id)
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")

    from personal_library.domain.models.tag import ArticleTag
    for aid in body.article_ids:
        article = await repo.get_by_id(db=db, article_id=aid)
        if not article or article.user_id != current_user.id:
            continue  # 跳过无权文章
        stmt = select(ArticleTag).where(
            ArticleTag.article_id == aid, ArticleTag.tag_id == body.tag_id
        )
        if not (await db.scalar(stmt)):
            db.add(ArticleTag(article_id=aid, tag_id=body.tag_id))
    await db.flush()
    return Response(status_code=204)


class BatchSetTagsRequest(BaseModel):
    tag_ids: list[UUID]


@router.post("/{article_id}/tags/batch", status_code=status.HTTP_204_NO_CONTENT)
async def batch_set_tags(
    article_id: UUID,
    body: BatchSetTagsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """单篇文章批量设置标签（替换式：移除旧的，添加新的）"""
    article = await repo.get_by_id(db=db, article_id=article_id)
    if not article or article.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    from personal_library.domain.models.tag import ArticleTag
    from sqlalchemy import delete as sqla_delete

    # 移除现有标签关联
    await db.execute(
        sqla_delete(ArticleTag).where(ArticleTag.article_id == article_id)
    )
    # 添加新标签
    for tid in body.tag_ids:
        tag = await tag_repo.get_by_id(db=db, tag_id=tid)
        if tag and tag.user_id == current_user.id:
            db.add(ArticleTag(article_id=article_id, tag_id=tid))
    await db.flush()
    return Response(status_code=204)
