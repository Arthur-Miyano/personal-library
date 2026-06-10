from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.core.file_extractor import extract_text, ALLOWED_EXTENSIONS, get_title_from_filename
from personal_library.domain.models.user import User
from personal_library.domain.repositories.article import ArticleRepository
from personal_library.infrastructure.schemas.article import ArticleResponse

router = APIRouter(prefix="/upload", tags=["upload"])
repo = ArticleRepository()
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传文件（.txt / .md / .html / .epub / .pdf），自动创建文章"""
    filename = file.filename or "未命名文件"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext = f".{ext}" if ext else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"不支持的文件格式 {ext}，支持: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="文件超过 10MB 限制")

    try:
        raw_text = extract_text(content, filename)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件内容为空")

    title = get_title_from_filename(filename)

    article = await repo.create(
        db=db, title=title, raw_text=raw_text,
        user_id=current_user.id, source_type="upload", source_name=filename,
    )
    return article
