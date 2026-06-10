import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.domain.models.settings import UserSettings


class SettingsRepository:
    """用户设置数据访问层"""

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> UserSettings | None:
        """查询某个用户的设置"""
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_default(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> UserSettings:
        """为新建用户创建默认设置"""
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
        return settings

    async def update(
        self,
        db: AsyncSession,
        settings: UserSettings,
        theme_mode: str | None = None,
        bg_color: str | None = None,
        bg_opacity: float | None = None,
        font_family: str | None = None,
        font_size: int | None = None,
        line_height: float | None = None,
        paragraph_spacing: int | None = None,
        reader_max_width: int | None = None,
        first_line_indent: bool | None = None,
        default_reformat: bool | None = None,
    ) -> None:
        """更新设置字段（只改传进来的非 None 值）"""
        if theme_mode is not None:
            settings.theme_mode = theme_mode
        if bg_color is not None:
            settings.bg_color = bg_color
        if bg_opacity is not None:
            settings.bg_opacity = bg_opacity
        if font_family is not None:
            settings.font_family = font_family
        if font_size is not None:
            settings.font_size = font_size
        if line_height is not None:
            settings.line_height = line_height
        if paragraph_spacing is not None:
            settings.paragraph_spacing = paragraph_spacing
        if reader_max_width is not None:
            settings.reader_max_width = reader_max_width
        if first_line_indent is not None:
            settings.first_line_indent = first_line_indent
        if default_reformat is not None:
            settings.default_reformat = default_reformat
        await db.flush()
