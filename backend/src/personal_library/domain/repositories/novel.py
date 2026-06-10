import uuid
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from personal_library.core.chapter_parser import ChapterData
from personal_library.domain.models.novel import Novel
from personal_library.domain.models.chapter import Chapter


class NovelRepository:

    async def create_with_chapters(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str,
        file_path: str,
        file_name: str,
        file_size: int,
        file_type: str,
        author: str | None = None,
        cover_path: str | None = None,
        chapters_data: list[ChapterData] | None = None,
    ) -> Novel:
        novel = Novel(
            title=title,
            author=author,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            cover_path=cover_path,
            user_id=user_id,
        )
        db.add(novel)
        await db.flush()

        if chapters_data:
            total_words = 0
            for cd in chapters_data:
                chapter = Chapter(
                    novel_id=novel.id,
                    chapter_number=cd.chapter_number,
                    title=cd.title,
                    content=cd.content,
                    word_count=cd.word_count,
                    start_position=cd.start_position,
                    end_position=cd.end_position,
                    is_prologue=cd.is_prologue,
                    content_hash=cd.content_hash,
                    needs_review=cd.needs_review,
                )
                db.add(chapter)
                total_words += cd.word_count

            novel.total_chapters = sum(1 for c in chapters_data if not c.is_prologue)
            novel.total_words = total_words

        await db.flush()
        await db.refresh(novel)
        return novel

    async def list_by_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Novel], int]:
        base = select(Novel).where(Novel.user_id == user_id, Novel.is_deleted == False)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = await db.scalar(count_stmt)

        stmt = (
            base
            .order_by(Novel.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(stmt)
        return result.scalars().all(), total or 0

    async def get_by_id(
        self,
        db: AsyncSession,
        novel_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Novel | None:
        stmt = select(Novel).where(Novel.id == novel_id)
        if not include_deleted:
            stmt = stmt.where(Novel.is_deleted == False)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        novel: Novel,
        title: str | None = None,
        author: str | None = None,
        is_read: bool | None = None,
    ) -> None:
        if title is not None:
            novel.title = title
        if author is not None:
            novel.author = author
        if is_read is not None:
            novel.is_read = is_read
        await db.flush()

    async def soft_delete(self, db: AsyncSession, novel: Novel) -> None:
        novel.is_deleted = True
        await db.flush()

    async def hard_delete(self, db: AsyncSession, novel: Novel) -> None:
        """彻底删除，DB 级联删 chapters 和 reading_progress"""
        await db.delete(novel)
        await db.flush()

    async def update_cover(
        self,
        db: AsyncSession,
        novel: Novel,
        cover_path: str,
    ) -> None:
        novel.cover_path = cover_path
        await db.flush()

    async def list_trash_by_user(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[Novel]:
        stmt = (
            select(Novel)
            .where(Novel.user_id == user_id, Novel.is_deleted == True)
            .order_by(Novel.updated_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_chapter_by_id(
        self,
        db: AsyncSession,
        chapter_id: uuid.UUID,
        novel_id: uuid.UUID,
    ) -> Chapter | None:
        stmt = select(Chapter).where(
            Chapter.id == chapter_id,
            Chapter.novel_id == novel_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_chapter(
        self,
        db: AsyncSession,
        chapter: Chapter,
        title: str | None = None,
        chapter_number: int | None = None,
        content: str | None = None,
    ) -> None:
        if title is not None:
            chapter.title = title
        if chapter_number is not None:
            chapter.chapter_number = chapter_number
            chapter.needs_review = False
        if content is not None:
            import hashlib
            from personal_library.core.xss import sanitize_html
            chapter.content = sanitize_html(content)
            chapter.word_count = len(chapter.content)
            chapter.content_hash = hashlib.sha256(
                chapter.content.encode("utf-8")
            ).hexdigest()
        await db.flush()
