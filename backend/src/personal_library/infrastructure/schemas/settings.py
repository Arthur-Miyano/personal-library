from pydantic import BaseModel, ConfigDict, Field, field_validator


class SettingsUpdate(BaseModel):
    """更新设置请求模型（所有字段可选）"""
    theme_mode: str | None = Field(None, max_length=20)
    bg_color: str | None = Field(None, max_length=9)
    bg_opacity: float | None = Field(None, ge=0.0, le=1.0)
    font_family: str | None = Field(None, max_length=500)
    font_size: int | None = Field(None, ge=8, le=128)
    line_height: float | None = Field(None, ge=0.5, le=5.0)
    paragraph_spacing: int | None = Field(None, ge=0, le=256)
    reader_max_width: int | None = Field(None, ge=100, le=3840)
    first_line_indent: bool | None = None
    default_reformat: bool | None = None

    @field_validator("bg_color")
    @classmethod
    def validate_bg_color(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) not in (7, 9) or not v.startswith("#"):
                raise ValueError("背景颜色必须是 #RRGGBB 或 #RRGGBBAA 格式")
            if not all(c in "0123456789ABCDEFabcdef" for c in v[1:]):
                raise ValueError("背景颜色包含非法字符")
        return v


class SettingsResponse(BaseModel):
    """设置响应模型"""
    model_config = ConfigDict(from_attributes=True)

    theme_mode: str
    bg_color: str
    bg_opacity: float
    font_family: str
    font_size: int
    line_height: float
    paragraph_spacing: int
    reader_max_width: int
    first_line_indent: bool
    default_reformat: bool
