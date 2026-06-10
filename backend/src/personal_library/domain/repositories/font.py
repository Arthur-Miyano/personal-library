import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from personal_library.domain.models.font import Font


class FontRepository:
    async def create(
        self, db: AsyncSession,
        user_id: uuid.UUID, filename: str, stored_path: str,
        font_family: str, file_size: int,
    ) -> Font:
        font = Font(
            user_id=user_id, filename=filename,
            stored_path=stored_path, font_family=font_family,
            file_size=file_size,
        )
        db.add(font)
        await db.flush()
        await db.refresh(font)
        return font

    async def list_by_user(self, db: AsyncSession, user_id: uuid.UUID) -> list[Font]:
        stmt = select(Font).where(Font.user_id == user_id).order_by(Font.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, font_id: uuid.UUID) -> Font | None:
        stmt = select(Font).where(Font.id == font_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, db: AsyncSession, font: Font) -> None:
        await db.delete(font)
        await db.flush()
