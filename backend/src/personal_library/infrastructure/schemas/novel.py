from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ===== 章节 =====
class ChapterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chapter_number: int
    title: str
    word_count: int
    is_prologue: bool
    content_hash: str
    needs_review: bool


class ChapterDetailResponse(ChapterResponse):
    """含正文的单章详情（仅在 GET /chapters/{id} 时返回）"""
    content: str


class ChapterUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    chapter_number: int | None = Field(None, ge=0)
    content: str | None = None


# ===== 小说 =====
class NovelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    author: str | None
    file_name: str
    file_size: int
    file_type: str
    cover_path: str | None
    total_chapters: int | None
    total_words: int | None
    is_read: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    chapters: list[ChapterResponse] = []


class NovelListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    author: str | None
    cover_path: str | None
    total_chapters: int | None
    total_words: int | None
    is_read: bool
    created_at: datetime
    updated_at: datetime


class NovelUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    author: str | None = Field(None, max_length=200)
    is_read: bool | None = None

    @model_validator(mode="after")
    def check_not_empty(self):
        if self.title is None and self.author is None and self.is_read is None:
            raise ValueError("至少需要提供一个要修改的字段")
        return self


class PaginatedNovels(BaseModel):
    items: list[NovelListResponse]
    total: int
    page: int
    size: int


# ===== 阅读进度 =====
class ProgressUpdate(BaseModel):
    chapter_id: UUID
    percentage: Decimal = Field(..., ge=0, le=100, max_digits=5, decimal_places=2)
    updated_at: datetime | None = None


class ProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chapter_id: UUID | None
    chapter_number: int | None = None
    chapter_title: str | None = None
    percentage: Decimal | None
    content_hash: str | None = None
    updated_at: datetime


# ===== 封面 =====
class CoverResponse(BaseModel):
    cover_path: str
