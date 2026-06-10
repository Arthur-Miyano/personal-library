from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)
from personal_library.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
)
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def close_engine() -> None:
    """优雅关闭数据库连接池"""
    await engine.dispose()
