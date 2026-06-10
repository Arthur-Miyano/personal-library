from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


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
