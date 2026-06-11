import os
import uuid as uuid_lib

import aiofiles
from aiofiles import os as async_os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.config import settings
from personal_library.core.file_extractor import sanitize_filename
from personal_library.domain.models.user import User
from personal_library.domain.repositories.font import FontRepository
from personal_library.infrastructure.schemas.font import FontResponse

router = APIRouter(prefix="/fonts", tags=["fonts"])
repo = FontRepository()

ALLOWED_EXTENSIONS = {".ttf", ".otf"}
MAX_SIZE = 10 * 1024 * 1024


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _parse_font_family(file_bytes: bytes) -> str:
    from fontTools.ttLib import TTFont
    from io import BytesIO
    try:
        font = TTFont(BytesIO(file_bytes))
        name_records = font["name"].names
        for record in name_records:
            if record.nameID == 1:  # Font Family
                try:
                    return record.toUnicode()
                except Exception:
                    pass
        return "Unknown"
    except Exception:
        raise ValueError("无法解析字体文件")


@router.post("", response_model=FontResponse, status_code=status.HTTP_201_CREATED)
async def upload_font(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filename = sanitize_filename(file.filename or "font.ttf")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail=f"不支持的文件类型，仅支持 {', '.join(ALLOWED_EXTENSIONS)}")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="字体文件超过 10MB 限制")

    try:
        font_family = _parse_font_family(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    fonts_dir = os.path.join(settings.upload_dir, "fonts")
    _ensure_dir(fonts_dir)
    uid = uuid_lib.uuid4()
    local_path = os.path.join(fonts_dir, f"{uid}{ext}")
    async with aiofiles.open(local_path, "wb") as f:
        await f.write(data)

    stored_path = f"/uploads/fonts/{uid}{ext}"

    try:
        font = await repo.create(
            db=db, user_id=current_user.id, filename=filename,
            stored_path=stored_path, font_family=font_family, file_size=len(data),
        )
    except Exception as e:
        import traceback, logging
        logging.getLogger(__name__).error(f"字体入库失败: {traceback.format_exc()}")
        # 文件已保存，不删除
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"数据库写入失败: {str(e)[:200]}")

    return font


@router.get("", response_model=list[FontResponse])
async def list_fonts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await repo.list_by_user(db=db, user_id=current_user.id)


@router.delete("/{font_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_font(
    font_id: uuid_lib.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    font = await repo.get_by_id(db=db, font_id=font_id)
    if not font or font.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="字体不存在")

    await repo.delete(db=db, font=font)

    # 安全路径校验：确保解析后的路径在 upload_dir 内，防止路径遍历攻击
    fonts_dir = os.path.join(settings.upload_dir, "fonts")
    stored_subpath = font.stored_path.replace("/uploads/", "", 1)
    local_path = os.path.realpath(os.path.join(fonts_dir, stored_subpath))
    expected_prefix = os.path.realpath(fonts_dir) + os.sep
    if not local_path.startswith(expected_prefix):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非法文件路径")
    try:
        if await async_os.path.exists(local_path):
            await async_os.unlink(local_path)
    except OSError:
        pass
    return None
