from contextlib import asynccontextmanager

import os

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from personal_library.api.v1.router import router as v1_router
from personal_library.config import settings
from personal_library.database import close_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    yield
    await close_engine()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(v1_router)

# 静态文件服务（上传的封面、字体等）
if settings.upload_dir:
    os.makedirs(settings.upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/health", tags=["health"])
async def health_check():
    """服务健康检查端点"""
    return {"status": "ok"}


# ========== 全局异常处理器 ==========

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """数据库唯一约束冲突等异常"""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "数据冲突，请检查唯一性约束"},
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Pydantic 校验失败（非请求参数类）"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(include_url=False)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """兜底异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "服务器内部错误"},
    )
