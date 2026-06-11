import re
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """密码至少12位，包含大写字母、小写字母、数字、特殊字符中的至少3种"""
        categories = sum([
            bool(re.search(r"[A-Z]", v)),
            bool(re.search(r"[a-z]", v)),
            bool(re.search(r"\d", v)),
            bool(re.search(r"[^A-Za-z0-9]", v)),
        ])
        if categories < 3:
            raise ValueError("密码必须至少包含大写字母、小写字母、数字、特殊字符中的3种")
        return v


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """用户信息响应 (me 接口用)"""
    id: UUID
    username: str
    email: str
    is_active: bool
    is_superuser: bool
