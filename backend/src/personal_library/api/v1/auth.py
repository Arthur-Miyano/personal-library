from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.core.security import hash_password, create_access_token, verify_password
from personal_library.domain.models.user import User
from personal_library.infrastructure.schemas.auth import (
    RegisterRequest, TokenResponse, UserResponse
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册新用户，注册成功直接返回token（注册即登录）"""
    user_exists = await db.scalar(
        select(exists().where(
            (User.username == body.username) | (User.email == body.email)
        ))
    )

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名或邮箱已被注册"
        )

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password)
    )
    db.add(user)
    await db.flush()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        token_type="bearer"
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """用户登录，支持 JSON 和 Form 两种格式"""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        login_username = body.get("username")
        login_password = body.get("password")
    else:
        form = await request.form()
        login_username = form.get("username")
        login_password = form.get("password")

    if not login_username or not login_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="请提供用户名和密码"
        )

    # 支持用户名或邮箱登录
    user = await db.scalar(
        select(User).where(
            (User.username == login_username) | (User.email == login_username)
        )
    )

    if not user or not verify_password(login_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的详细信息"""
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh(current_user: User = Depends(get_current_user)):
    """刷新访问令牌，延长登录有效期"""
    return TokenResponse(
        access_token=create_access_token(str(current_user.id)),
        token_type="bearer"
    )


@router.post("/token", response_model=TokenResponse)
async def token_for_swagger(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2 表单登录 —— 供 Swagger Authorize 按钮"""
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        token_type="bearer",
    )
