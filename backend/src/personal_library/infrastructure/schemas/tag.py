import re
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


class TagCreate(BaseModel):
    """创建标签请求模型"""
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#909399")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not HEX_COLOR_PATTERN.match(v):
            raise ValueError("颜色必须是 #RRGGBB 格式的 HEX 字符串")
        return v


class TagResponse(BaseModel):
    """标签响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    color: str
