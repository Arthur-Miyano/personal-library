import uuid
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin


class Font(Base, TimestampMixin):
    __tablename__ = "fonts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    font_family: Mapped[str] = mapped_column(String(200), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
