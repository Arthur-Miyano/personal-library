import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, Form
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.core.file_extractor import (
    extract_text, ALLOWED_EXTENSIONS, get_title_from_filename, VALID_ENCODINGS,
)
from personal_library.domain.models.user import User
from personal_library.domain.repositories.article import ArticleRepository
from personal_library.infrastructure.schemas.article import ArticleResponse

router = APIRouter(prefix="/upload", tags=["upload"])
repo = ArticleRepository()
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    encoding: str = Form("auto"),
    encoding_errors: str = Form("strict"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传文件，自动创建文章。支持 encoding 参数覆盖编码检测。"""
    filename = file.filename or "未命名文件"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext = f".{ext}" if ext else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail=f"不支持的文件格式 {ext}，支持: {', '.join(ALLOWED_EXTENSIONS)}")

    if encoding not in VALID_ENCODINGS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"不支持的编码: {encoding}")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件为空")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="文件超过 10MB 限制")

    try:
        raw_text = extract_text(content, filename, encoding_hint=encoding, errors=encoding_errors)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="编码错误，请尝试手动选择编码")

    if not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件内容为空")

    h = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    existing = await repo.find_duplicate(db, current_user.id, h)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"文件已存在: {existing.title}",
        )

    title = get_title_from_filename(filename)
    article = await repo.create(
        db=db, title=title, raw_text=raw_text, user_id=current_user.id,
        source_type="upload", source_name=filename, content_hash=h,
    )
    return article
