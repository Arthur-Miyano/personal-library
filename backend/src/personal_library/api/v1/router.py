from fastapi import APIRouter
from .auth import router as auth_router
from .articles import router as articles_router
from .collections import router as collections_router
from .tags import router as tags_router
from .settings import router as settings_router
from .upload import router as upload_router
from .novels import router as novels_router
from .fonts import router as fonts_router

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(articles_router)
router.include_router(collections_router)
router.include_router(tags_router)
router.include_router(settings_router)
router.include_router(upload_router)
router.include_router(novels_router)
router.include_router(fonts_router)
