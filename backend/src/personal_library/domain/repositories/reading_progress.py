import uuid
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql import func
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
        """原子 upsert：使用 PostgreSQL INSERT ... ON CONFLICT 消除 TOCTOU 竞态。
        依赖 reading_progresses 表的 (user_id, novel_id) 唯一约束。
        """
        stmt = (
            pg_insert(ReadingProgress)
            .values(
                user_id=user_id,
                novel_id=novel_id,
                chapter_id=chapter_id,
                percentage=percentage,
            )
            .on_conflict_do_update(
                index_elements=["user_id", "novel_id"],
                set_={
                    "chapter_id": chapter_id,
                    "percentage": percentage,
                    "updated_at": func.now(),
                },
            )
        )
        await db.execute(stmt)
        await db.flush()

        result = await db.scalar(
            select(ReadingProgress).where(
                ReadingProgress.user_id == user_id,
                ReadingProgress.novel_id == novel_id,
            )
        )
        return result

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
        from sqlalchemy.orm import joinedload
        stmt = (
            select(ReadingProgress)
            .options(joinedload(ReadingProgress.chapter))
            .where(ReadingProgress.user_id == user_id, ReadingProgress.novel_id == novel_id)
        )
        result = await db.execute(stmt)
        progress = result.scalar_one_or_none()
        if progress is None:
            return None, None
        return progress, progress.chapter
