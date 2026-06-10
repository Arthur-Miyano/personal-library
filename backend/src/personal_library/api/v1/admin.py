import asyncio
import hashlib
import time
import uuid as uuid_lib
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from personal_library.api.deps import get_current_user, get_db
from personal_library.config import settings
from personal_library.core.file_extractor import (
    ALLOWED_EXTENSIONS, VALID_ENCODINGS, extract_text, get_title_from_filename, sanitize_filename,
)
from personal_library.core.xss import sanitize_html
from personal_library.domain.models.user import User
from personal_library.domain.repositories.article import ArticleRepository
from personal_library.domain.repositories.collection import CollectionRepository

router = APIRouter(prefix="/admin", tags=["admin"])
article_repo = ArticleRepository()
coll_repo = CollectionRepository()

_user_locks: dict[str, asyncio.Lock] = {}


@dataclass
class ProcessResult:
    text: str = ""
    hash: str = ""
    filename: str = ""
    title: str = ""
    error: str = ""


@dataclass
class ImportTask:
    status: str = "running"
    total: int = 0
    success: int = 0
    failed: int = 0
    duplicate: int = 0
    current: str = ""
    failures: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


_import_tasks: dict[str, ImportTask] = {}


class ImportPathRequest(BaseModel):
    subpath: str = Field(..., min_length=1, description="相对于 import_root 的子路径")
    collection_name: str | None = Field(None, description="导入后归入的合集名，不存在则自动创建")
    encoding: str = Field("auto", description="编码: auto|utf-8|gbk|gb18030")
    encoding_errors: str = Field("strict", description="strict|replace|ignore")


@router.post("/import-path")
async def start_import(
    body: ImportPathRequest,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可用")
    if not settings.import_root:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="服务器导入功能未启用")
    if body.encoding not in VALID_ENCODINGS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的编码: {body.encoding}")

    subpath = body.subpath.lstrip("/\\")
    if ".." in Path(subpath).parts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="路径不允许 ..")

    resolved_root = Path(settings.import_root).resolve()
    target = (resolved_root / subpath).resolve()
    if not str(target).startswith(str(resolved_root)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="路径越权")
    if not target.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"路径不存在: {subpath}")
    if not target.is_dir():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="路径不是目录")

    files = sorted([f for f in target.iterdir() if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS])
    if len(files) > settings.import_max_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"文件数量 {len(files)} 超过上限 {settings.import_max_files}")
    if len(files) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="目录中没有可导入的文件")

    lock_key = str(current_user.id)
    if lock_key not in _user_locks:
        _user_locks[lock_key] = asyncio.Lock()
    lock = _user_locks[lock_key]
    if lock.locked():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已有导入任务正在运行")

    task_id = str(uuid_lib.uuid4())
    _import_tasks[task_id] = ImportTask(total=len(files))
    asyncio.create_task(_run_import(task_id, files, body, current_user.id, lock))
    return {"task_id": task_id, "total": len(files)}


@router.get("/import-path/{task_id}")
async def get_import_progress(task_id: str):
    task = _import_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在或已过期")
    return {
        "status": task.status, "total": task.total,
        "success": task.success, "failed": task.failed,
        "duplicate": task.duplicate, "current": task.current,
        "failures": task.failures,
    }


async def _run_import(task_id, files, body, user_id, lock):
    task = _import_tasks[task_id]
    async with lock:
        from personal_library.database import async_session
        try:
            async with async_session() as db:
                coll_id = None
                if body.collection_name:
                    coll = await _find_or_create_collection(db, user_id, body.collection_name)
                    coll_id = coll.id

                for i, f in enumerate(files):
                    try:
                        result = await asyncio.to_thread(_process_one_file, f, body)
                        if result.error:
                            task.failed += 1
                            task.failures.append({"file": f.name, "reason": result.error})
                        else:
                            created, article = await article_repo.create_dedup(
                                db, user_id,
                                title=result.title, raw_text=result.text,
                                content_hash=result.hash,
                                source_type="import", source_name=result.filename,
                            )
                            if created and coll_id:
                                await coll_repo.add_article(db, coll_id, article.id)
                            if created:
                                task.success += 1
                            else:
                                task.duplicate += 1
                    except Exception as e:
                        task.failed += 1
                        task.failures.append({"file": f.name, "reason": str(e)})

                    task.current = f.name
                    if (i + 1) % 50 == 0:
                        await db.commit()
                await db.commit()
            task.status = "done"
        except Exception as e:
            task.status = "failed"
            task.failures.append({"file": "__system__", "reason": str(e)})


def _process_one_file(f: Path, body) -> ProcessResult:
    try:
        st = f.stat()
        if st.st_size == 0:
            return ProcessResult(error="文件为空")
        max_bytes = settings.import_max_file_size_mb * 1024 * 1024
        if st.st_size > max_bytes:
            return ProcessResult(error=f"文件超过 {settings.import_max_file_size_mb}MB 限制")
        content = f.read_bytes()
        text = extract_text(content, f.name, body.encoding, body.encoding_errors)
        text = sanitize_html(text)
        if not text.strip():
            return ProcessResult(error="文件内容为空")
        h = hashlib.sha256(text.encode()).hexdigest()
        return ProcessResult(text=text, hash=h, filename=f.name,
                             title=get_title_from_filename(f.name))
    except OSError as e:
        return ProcessResult(error=f"文件读取错误: {e}")
    except ValueError as e:
        return ProcessResult(error=str(e))
    except UnicodeDecodeError:
        return ProcessResult(error="编码错误，请尝试手动选择编码")


async def _find_or_create_collection(db, user_id, name):
    from sqlalchemy import select
    from personal_library.domain.models.collection import Collection
    existing = await db.scalar(
        select(Collection).where(Collection.user_id == user_id, Collection.name == name)
    )
    if existing:
        return existing
    coll = Collection(name=name, user_id=user_id)
    db.add(coll)
    await db.flush()
    return coll


async def _cleanup_tasks():
    while True:
        try:
            await asyncio.sleep(600)
            now = time.time()
            expired = [k for k, v in _import_tasks.items() if now - v.created_at > 1800]
            for k in expired:
                del _import_tasks[k]
        except Exception:
            continue

_cleanup_started = False
def start_cleanup():
    global _cleanup_started
    if not _cleanup_started:
        _cleanup_started = True
        asyncio.create_task(_cleanup_tasks())
