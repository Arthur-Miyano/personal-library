from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from .tag import TagResponse

# ===== 前端传给后端的数据格式 =====
class ArticleCreate(BaseModel):
    """创建文章请求模型（接收前端参数）"""
    title: str = Field(..., min_length=1, max_length=500)
    raw_text: str = Field(..., min_length=1)


class ArticleUpdate(BaseModel):
    """更新文章请求模型（所有字段可选，只传要改的）"""
    title: str | None = Field(None, min_length=1, max_length=500)
    raw_text: str | None = Field(None, min_length=1)


# ===== 后端返回给前端的数据格式 =====
class ArticleResponse(BaseModel):
    """文章响应模型（返回给前端数据）"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    raw_text: str
    word_count: int
    source_type: str
    source_name: str | None
    status: str
    is_deleted: bool
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    content_hash: str = ""
    tags: list[TagResponse] = []
