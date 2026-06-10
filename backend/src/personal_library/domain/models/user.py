from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .novel import Novel
    from .reading_progress import ReadingProgress
    from .settings import UserSettings


class User(Base, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
        nullable=False,
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )

    novels: Mapped[List["Novel"]] = relationship(
        "Novel", back_populates="user", lazy="selectin"
    )
    reading_progresses: Mapped[List["ReadingProgress"]] = relationship(
        "ReadingProgress", back_populates="user"
    )
    settings: Mapped["UserSettings"] = relationship(
        "UserSettings", back_populates="user", uselist=False
    )