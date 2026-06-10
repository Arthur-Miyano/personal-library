import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
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
        client_updated_at: datetime | None = None,
    ) -> ReadingProgress | None:
        """返回进度对象；乐观锁冲突时返回 None"""
        if client_updated_at is None:
            progress = ReadingProgress(
                user_id=user_id,
                novel_id=novel_id,
                chapter_id=chapter_id,
                percentage=percentage,
            )
            db.add(progress)
            try:
                await db.flush()
                await db.refresh(progress)
                return progress
            except Exception:
                await db.rollback()
                return None
        else:
            from sqlalchemy import update
            stmt = (
                update(ReadingProgress)
                .where(
                    ReadingProgress.user_id == user_id,
                    ReadingProgress.novel_id == novel_id,
                    ReadingProgress.updated_at == client_updated_at,
                )
                .values(chapter_id=chapter_id, percentage=percentage)
            )
            result = await db.execute(stmt)
            if result.rowcount == 0:
                return None
            return await self.get(db, user_id, novel_id)

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

    async def get_with_chapter(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        novel_id: uuid.UUID,
    ):
        """返回 (ReadingProgress, Chapter | None)"""
        progress = await self.get(db, user_id, novel_id)
        if progress is None:
            return None, None
        chapter = None
        if progress.chapter_id:
            stmt = select(Chapter).where(Chapter.id == progress.chapter_id)
            result = await db.execute(stmt)
            chapter = result.scalar_one_or_none()
        return progress, chapter
