from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from personal_library.config import settings
from personal_library.database import async_session
from personal_library.domain.models.user import User


# ========== 数据库会话依赖（供所有路由共享）==========
async def get_db() -> AsyncSession:
    """获取数据库会话，请求结束后自动 commit/rollback/close。"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ========== JWT 认证依赖 ==========
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT 中解析当前用户。任何需要登录的接口依赖此函数即可。
    1. 解码 JWT，拿到 payload
    2. 从 payload 取 "sub" → 用户ID（UUID）
    3. 用用户ID查数据库
    4. 找不到或已停用则 401
    """
    #捕获Token无效或过期的异常
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. 解码 JWT，拿到 payload
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id_str: str = payload.get("sub")
        #如果payload里没有用户ID，抛出异常
        if user_id_str is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 3. 用用户ID查数据库（使用 get_db 提供的 session，保证测试时能被 override）
    user_id = uuid.UUID(user_id_str)
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()
    # 4. 找不到或被停用则 401
    if user is None or not user.is_active:
        raise credentials_exception
    return user

