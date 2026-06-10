import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import asyncpg

from personal_library.main import app
from personal_library.api.v1.auth import get_db
from personal_library.domain.models.base import Base

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/personal_library_test"
TEST_DATABASE_NAME = "personal_library_test"
POSTGRES_SYSTEM_URL = "postgresql://postgres:postgres@localhost:5432/postgres"


async def ensure_test_database():
    """如果测试数据库不存在，自动创建"""
    conn = await asyncpg.connect(POSTGRES_SYSTEM_URL)
    try:
        await conn.execute(f"CREATE DATABASE {TEST_DATABASE_NAME}")
    except asyncpg.exceptions.DuplicateDatabaseError:
        pass
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    await ensure_test_database()
    eng = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(scope="session")
async def setup_database(engine):
    """整个测试会话只建表一次"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(engine, setup_database):
    """
    每个测试在连接级别开启嵌套事务（保存点），测试结束后回滚。
    即使测试代码中调用 session.commit()，也只会提交保存点，外层真实事务仍可回滚。
    """
    async with engine.connect() as conn:
        trans = await conn.begin_nested()  # 关键：使用嵌套事务/保存点
        session_factory = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with session_factory() as session:
            yield session
        await trans.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    # 每次请求结束后 commit savepoint，让同一测试内的后续请求能读到之前的数据
    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # 只清理我们添加的依赖重写，不影响其他 fixture 或测试的设置
    app.dependency_overrides.pop(get_db, None)