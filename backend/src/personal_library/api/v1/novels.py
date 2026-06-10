import logging
import os
import traceback
import uuid as uuid_lib
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.config import settings
from personal_library.core.chapter_parser import parse_chapters
from personal_library.domain.models.user import User
from personal_library.domain.repositories.novel import NovelRepository
from personal_library.domain.repositories.reading_progress import ReadingProgressRepository
from personal_library.infrastructure.schemas.novel import (
    ChapterDetailResponse,
    ChapterResponse,
    ChapterUpdate,
    CoverResponse,
    NovelResponse,
    NovelUpdate,
    PaginatedNovels,
    ProgressResponse,
    ProgressUpdate,
)

router = APIRouter(prefix="/novels", tags=["novels"])
repo = NovelRepository()
progress_repo = ReadingProgressRepository()

ALLOWED_COVER_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_TXT_SIZE = 50 * 1024 * 1024
MAX_COVER_SIZE = 5 * 1024 * 1024


def _ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _validate_image(data: bytes) -> bool:
    """用 Pillow 校验图片完整性"""
    from io import BytesIO
    from PIL import Image
    try:
        img = Image.open(BytesIO(data))
        img.verify()
        return True
    except Exception:
        return False


@router.post("/upload", response_model=NovelResponse, status_code=status.HTTP_201_CREATED)
async def upload_novel(
    file: UploadFile = File(...),
    cover: UploadFile | None = File(None),
    author: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传小说文件（.txt / .epub / .pdf），可选封面图。自动分章。"""
    filename = file.filename or "未命名.txt"
    ext = os.path.splitext(filename)[1].lower()

    from personal_library.core.file_extractor import extract_text, ALLOWED_EXTENSIONS, get_title_from_filename
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持的文件格式 {ext}，支持: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    cover_data: bytes | None = None
    cover_ext: str | None = None
    if cover is not None:
        if cover.content_type not in ALLOWED_COVER_TYPES:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="封面仅支持 JPEG/PNG/WebP")
        cover_data = await cover.read()
        if len(cover_data) > MAX_COVER_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="封面超过 5MB 限制")
        if not _validate_image(cover_data):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="封面图片损坏或格式无效")
        cover_ext = os.path.splitext(cover.filename or "cover.jpg")[1].lower()
        if cover_ext not in (".jpg", ".jpeg", ".png", ".webp"):
            cover_ext = ".jpg"

    # 1. 读取文件内容
    content = await file.read()
    if len(content) > MAX_TXT_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="文件超过 50MB 限制")
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件为空")

    # 2. 提取文本 → 分章
    try:
        text = extract_text(content, filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    chapters_data = parse_chapters(text)
    if not chapters_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="解析章节失败")

    # 3. 保存提取后的文本到磁盘
    novels_dir = os.path.join(settings.upload_dir, "novels")
    _ensure_dir(novels_dir)
    novel_uuid = uuid_lib.uuid4()
    final_path = os.path.join(novels_dir, f"{novel_uuid}.txt")
    try:
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="文件存储失败")

    # 4. 处理封面
    cover_url: str | None = None
    cover_local_path: str | None = None
    if cover_data is not None:
        covers_dir = os.path.join(settings.upload_dir, "covers")
        _ensure_dir(covers_dir)
        cover_local_path = os.path.join(covers_dir, f"{novel_uuid}{cover_ext}")
        with open(cover_local_path, "wb") as f:
            f.write(cover_data)
        cover_url = f"/uploads/covers/{novel_uuid}{cover_ext}"

    # 5. 写数据库
    try:
        title = get_title_from_filename(filename)
        novel = await repo.create_with_chapters(
            db=db, user_id=current_user.id, title=title,
            file_path=final_path, file_name=filename,
            file_size=len(content), file_type=ext.lstrip("."),
            author=author, cover_path=cover_url,
            chapters_data=chapters_data,
        )
    except Exception as e:
        logger.error(f"小说入库失败: {traceback.format_exc()}")
        # 文件已保存成功，不删除；只清理失败的封面
        if cover_local_path and os.path.exists(cover_local_path):
            os.unlink(cover_local_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"数据库写入失败: {str(e)[:200]}")

    return novel


@router.get("", response_model=PaginatedNovels)
async def list_novels(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分页列出当前用户的小说"""
    items, total = await repo.list_by_user(db=db, user_id=current_user.id, page=page, size=size)
    return PaginatedNovels(items=items, total=total, page=page, size=size)


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(
    novel_id: uuid_lib.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """小说详情（含章节目录，不含正文）"""
    novel = await repo.get_by_id(db=db, novel_id=novel_id)
    if not novel or novel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    return novel


@router.patch("/{novel_id}", response_model=NovelResponse)
async def update_novel(
    novel_id: uuid_lib.UUID,
    body: NovelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改小说元数据"""
    novel = await repo.get_by_id(db=db, novel_id=novel_id)
    if not novel or novel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    await repo.update(db=db, novel=novel, title=body.title, author=body.author, is_read=body.is_read)
    await db.refresh(novel)
    return novel


@router.delete("/{novel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_novel(
    novel_id: uuid_lib.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """软删除小说"""
    novel = await repo.get_by_id(db=db, novel_id=novel_id)
    if not novel or novel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")
    await repo.soft_delete(db=db, novel=novel)
    return None


@router.delete("/{novel_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_novel(
    novel_id: uuid_lib.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """彻底删除小说，包括文件和数据库记录"""
    novel = await repo.get_by_id(db=db, novel_id=novel_id, include_deleted=True)
    if not novel or novel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")

    file_path = novel.file_path
    cover_path = novel.cover_path

    await repo.hard_delete(db=db, novel=novel)

    if file_path and os.path.exists(file_path):
        try:
            os.unlink(file_path)
        except OSError:
            pass
    if cover_path:
        local = os.path.join(settings.upload_dir, cover_path.replace("/uploads/", "", 1))
        if os.path.exists(local):
            try:
                os.unlink(local)
            except OSError:
                pass
    return None


@router.post("/{novel_id}/cover", response_model=CoverResponse)
async def upload_cover(
    novel_id: uuid_lib.UUID,
    cover: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传或更换封面图"""
    novel = await repo.get_by_id(db=db, novel_id=novel_id)
    if not novel or novel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")

    if cover.content_type not in ALLOWED_COVER_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="封面仅支持 JPEG/PNG/WebP")

    data = await cover.read()
    if len(data) > MAX_COVER_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="封面超过 5MB 限制")
    if not _validate_image(data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="封面图片损坏或格式无效")

    covers_dir = os.path.join(settings.upload_dir, "covers")
    _ensure_dir(covers_dir)
    ext = os.path.splitext(cover.filename or "cover.jpg")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    filename = f"{novel_id}{ext}"
    local_path = os.path.join(covers_dir, filename)
    with open(local_path, "wb") as f:
        f.write(data)

    # 删除旧封面文件（如果存在且路径可解析）
    if novel.cover_path:
        old_local = os.path.join(settings.upload_dir, novel.cover_path.replace("/uploads/", "", 1))
        if os.path.exists(old_local):
            try:
                os.unlink(old_local)
            except OSError:
                pass

    cover_url = f"/uploads/covers/{filename}"
    await repo.update_cover(db=db, novel=novel, cover_path=cover_url)
    return CoverResponse(cover_path=cover_url)


@router.get("/{novel_id}/chapters/{chapter_id}", response_model=ChapterDetailResponse)
async def get_chapter(
    novel_id: uuid_lib.UUID,
    chapter_id: uuid_lib.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单章正文"""
    novel = await repo.get_by_id(db=db, novel_id=novel_id)
    if not novel or novel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")

    chapter = await repo.get_chapter_by_id(db=db, chapter_id=chapter_id, novel_id=novel_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="章节不存在")
    return chapter


@router.patch("/{novel_id}/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    novel_id: uuid_lib.UUID,
    chapter_id: uuid_lib.UUID,
    body: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修正章节标题或序号"""
    novel = await repo.get_by_id(db=db, novel_id=novel_id)
    if not novel or novel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")

    chapter = await repo.get_chapter_by_id(db=db, chapter_id=chapter_id, novel_id=novel_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="章节不存在")

    await repo.update_chapter(db=db, chapter=chapter, title=body.title, chapter_number=body.chapter_number, content=body.content)
    await db.refresh(chapter)
    return chapter


@router.put("/{novel_id}/progress", response_model=ProgressResponse)
async def update_progress(
    novel_id: uuid_lib.UUID,
    body: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新阅读进度（首次创建不传 updated_at，后续更新必须传）"""
    novel = await repo.get_by_id(db=db, novel_id=novel_id)
    if not novel or novel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")

    result = await progress_repo.upsert(
        db=db, user_id=current_user.id, novel_id=novel_id,
        chapter_id=body.chapter_id, percentage=body.percentage,
    )

    if result is None:
        current, _ = await progress_repo.get_with_chapter(db, current_user.id, novel_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="进度已被其他设备更新，请刷新后重试",
        )

    chapter = None
    if result.chapter_id:
        from sqlalchemy import select
        from personal_library.domain.models.chapter import Chapter
        ch_stmt = select(Chapter).where(Chapter.id == result.chapter_id)
        ch_result = await db.execute(ch_stmt)
        chapter = ch_result.scalar_one_or_none()

    return ProgressResponse(
        chapter_id=result.chapter_id,
        chapter_number=chapter.chapter_number if chapter else None,
        chapter_title=chapter.title if chapter else None,
        percentage=result.percentage,
        content_hash=chapter.content_hash if chapter else None,
        updated_at=result.updated_at,
    )


@router.get("/{novel_id}/progress", response_model=ProgressResponse)
async def get_progress(
    novel_id: uuid_lib.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前阅读进度"""
    novel = await repo.get_by_id(db=db, novel_id=novel_id)
    if not novel or novel.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="小说不存在")

    progress, chapter = await progress_repo.get_with_chapter(db, current_user.id, novel_id)
    if progress is None:
        return ProgressResponse(
            chapter_id=None,
            percentage=None,
            content_hash=None,
            updated_at=None,
        )

    return ProgressResponse(
        chapter_id=progress.chapter_id,
        chapter_number=chapter.chapter_number if chapter else None,
        chapter_title=chapter.title if chapter else None,
        percentage=progress.percentage,
        content_hash=chapter.content_hash if chapter else None,
        updated_at=progress.updated_at,
    )
