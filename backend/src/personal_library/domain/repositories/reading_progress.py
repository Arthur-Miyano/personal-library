import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from personal_library.domain.models.reading_progress import ReadingProgress
from personal_library.domain.models.chapter import Chapter


class ReadingProgressRepository:

    async def upsert(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        novel_id: uuid.UUID,
        chapter_id: uuid.UUID,
        percentage: Decimal,
    ) -> ReadingProgress:
        existing = await db.scalar(
            select(ReadingProgress).where(
                ReadingProgress.user_id == user_id,
                ReadingProgress.novel_id == novel_id,
            )
        )
        if existing:
            await db.execute(
                update(ReadingProgress)
                .where(ReadingProgress.id == existing.id)
                .values(chapter_id=chapter_id, percentage=percentage)
            )
            await db.flush()
            await db.refresh(existing)
            return existing
        else:
            progress = ReadingProgress(
                user_id=user_id, novel_id=novel_id,
                chapter_id=chapter_id, percentage=percentage,
            )
            db.add(progress)
            await db.flush()
            await db.refresh(progress)
            return progress

    async def get(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        novel_id: uuid.UUID,
    ) -> ReadingProgress | None:
        stmt = select(ReadingProgress).where(
            ReadingProgress.user_id == user_id,
            ReadingProgress.novel_id == novel_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_chapter(self, db, user_id, novel_id):
        progress = await self.get(db, user_id, novel_id)
        if progress is None:
            return None, None
        chapter = None
        if progress.chapter_id:
            stmt = select(Chapter).where(Chapter.id == progress.chapter_id)
            result = await db.execute(stmt)
            chapter = result.scalar_one_or_none()
        return progress, chapter
