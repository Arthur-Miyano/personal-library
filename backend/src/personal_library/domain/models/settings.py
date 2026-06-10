import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, REAL, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class UserSettings(Base, TimestampMixin):
    """用户设置表：存储阅读器偏好等个性化配置"""
    __tablename__ = "user_settings"

    # 设置属于哪个用户（一对一关系，用户被删设置也删）
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    user: Mapped["User"] = relationship(back_populates="settings")

    # 主题模式
    theme_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="light"
    )

    # 背景颜色（含透明度的 HEX，如 #FFFFFF）
    bg_color: Mapped[str] = mapped_column(
        String(9), nullable=False, default="#FFFFFF"
    )

    # 背景透明度（0.0 ~ 1.0）
    bg_opacity: Mapped[float] = mapped_column(
        REAL, nullable=False, default=1.0
    )

    # 字体族
    font_family: Mapped[str] = mapped_column(
        String(500), nullable=False, default="system-ui"
    )

    # 字体大小（像素）
    font_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=16
    )

    # 行高（倍数，如 1.8）
    line_height: Mapped[float] = mapped_column(
        REAL, nullable=False, default=1.8
    )

    # 段落间距（像素）
    paragraph_spacing: Mapped[int] = mapped_column(
        Integer, nullable=False, default=12
    )

    # 阅读器最大宽度（像素）
    reader_max_width: Mapped[int] = mapped_column(
        Integer, nullable=False, default=800
    )

    # 首行缩进
    first_line_indent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # 默认自动排版
    default_reformat: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
