import re
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


class CollectionCreate(BaseModel):
    """创建收藏夹请求模型"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    color: str = Field(default="#409EFF")
    icon: str = Field(default="folder", max_length=50)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not HEX_COLOR_PATTERN.match(v):
            raise ValueError("颜色必须是 #RRGGBB 格式的 HEX 字符串")
        return v


class CollectionUpdate(BaseModel):
    """更新收藏夹请求模型（所有字段可选）"""
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    color: str | None = None
    icon: str | None = Field(None, max_length=50)
    sort_order: float | None = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is not None and not HEX_COLOR_PATTERN.match(v):
            raise ValueError("颜色必须是 #RRGGBB 格式的 HEX 字符串")
        return v


class CollectionResponse(BaseModel):
    """收藏夹响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    color: str
    icon: str
    sort_order: float
    articles: list = []
