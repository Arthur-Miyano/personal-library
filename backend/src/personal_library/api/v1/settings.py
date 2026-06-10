from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.domain.models.user import User
from personal_library.domain.repositories.settings import SettingsRepository
from personal_library.infrastructure.schemas.settings import (
    SettingsUpdate,
    SettingsResponse,
)

router = APIRouter(prefix="/settings", tags=["settings"])
repo = SettingsRepository()


@router.get(
    "",
    response_model=SettingsResponse,
)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的设置（不存在则自动创建默认设置）"""
    settings = await repo.get_by_user(db=db, user_id=current_user.id)
    if not settings:
        settings = await repo.create_default(db=db, user_id=current_user.id)
    return settings


@router.patch(
    "",
    response_model=SettingsResponse,
)
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新当前用户的设置"""
    settings = await repo.get_by_user(db=db, user_id=current_user.id)
    if not settings:
        settings = await repo.create_default(db=db, user_id=current_user.id)

    await repo.update(
        db=db,
        settings=settings,
        theme_mode=body.theme_mode,
        bg_color=body.bg_color,
        bg_opacity=body.bg_opacity,
        font_family=body.font_family,
        font_size=body.font_size,
        line_height=body.line_height,
        paragraph_spacing=body.paragraph_spacing,
        reader_max_width=body.reader_max_width,
        first_line_indent=body.first_line_indent,
        default_reformat=body.default_reformat,
    )
    await db.refresh(settings)
    return settings
