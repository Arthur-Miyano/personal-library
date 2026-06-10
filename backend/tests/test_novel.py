import io
import pytest

TEST_USER = {
    "username": "noveltestuser",
    "email": "noveltest@example.com",
    "password": "testpassword123"
}

SAMPLE_TXT = (
    "序言内容：这是一本测试小说。\n"
    "第一章 开始\n"
    "这是第一章的内容。主角踏上了旅程。\n"
    "第二章 途中\n"
    "第二章的内容。主角遇到了困难。\n"
    "第三章 结局\n"
    "第三章的内容。故事结束了。\n"
)

SAMPLE_TXT_NO_CHAPTERS = (
    "这是一段没有任何章节标题的纯文本内容。\n"
    "第二行。第三行。\n"
)


async def register_and_login(client):
    await client.post("/api/v1/auth/register", json=TEST_USER)
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )
    return response.json()["access_token"]


# ===== 上传 =====

@pytest.mark.asyncio
async def test_upload_novel_success(client):
    """上传标准小说 → 正确分章"""
    token = await register_and_login(client)
    files = {"file": ("test_novel.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    response = await client.post(
        "/api/v1/novels/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "test_novel"
    assert data["total_chapters"] == 3


@pytest.mark.asyncio
async def test_upload_novel_has_prologue(client):
    """上传带序言的小说 → 序言标记正确且不计入章节数"""
    token = await register_and_login(client)
    files = {"file": ("prologue.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    response = await client.post(
        "/api/v1/novels/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_chapters"] == 3  # 序言不计入
    assert len(data["chapters"]) == 4   # 但列表中包含序言
    assert data["chapters"][0]["is_prologue"] is True
    assert data["chapters"][0]["chapter_number"] == 0


@pytest.mark.asyncio
async def test_upload_no_chapters(client):
    """上传无章节标题的纯文本 → 单章"""
    token = await register_and_login(client)
    files = {"file": ("plain.txt", io.BytesIO(SAMPLE_TXT_NO_CHAPTERS.encode("utf-8")), "text/plain")}
    response = await client.post(
        "/api/v1/novels/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_chapters"] == 1


@pytest.mark.asyncio
async def test_upload_rejects_non_txt(client):
    """拒绝不支持的文件格式"""
    token = await register_and_login(client)
    files = {"file": ("test.exe", io.BytesIO(b"binary"), "application/octet-stream")}
    response = await client.post(
        "/api/v1/novels/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_empty_file(client):
    """拒绝空文件"""
    token = await register_and_login(client)
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    response = await client.post(
        "/api/v1/novels/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


# ===== 列表 =====

@pytest.mark.asyncio
async def test_list_novels_paginated(client):
    """分页列表"""
    token = await register_and_login(client)

    files = {"file": ("a.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token}"})

    response = await client.get("/api/v1/novels?page=1&size=10", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["page"] == 1


# ===== 详情 =====

@pytest.mark.asyncio
async def test_get_novel_detail(client):
    """获取小说详情，含章节目录"""
    token = await register_and_login(client)

    files = {"file": ("detail.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    resp = await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    novel_id = resp.json()["id"]

    response = await client.get(f"/api/v1/novels/{novel_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["chapters"]) == 4  # 1 序言 + 3 章
    assert data["chapters"][1]["title"] == "第一章 开始"


# ===== 章节内容 =====

@pytest.mark.asyncio
async def test_get_chapter_content(client):
    """获取单章正文"""
    token = await register_and_login(client)

    files = {"file": ("chap.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    resp = await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    novel_id = resp.json()["id"]
    chapters = resp.json()["chapters"]
    chapter_id = chapters[1]["id"]  # chapters[0] is prologue

    response = await client.get(
        f"/api/v1/novels/{novel_id}/chapters/{chapter_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "第一章 开始" in data["title"]
    assert len(data["content"]) > 0


# ===== 修改元数据 =====

@pytest.mark.asyncio
async def test_update_novel_metadata(client):
    """修改小说标题和作者"""
    token = await register_and_login(client)

    files = {"file": ("meta.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    resp = await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    novel_id = resp.json()["id"]

    response = await client.patch(
        f"/api/v1/novels/{novel_id}",
        json={"title": "新书名", "author": "新作者"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "新书名"
    assert data["author"] == "新作者"


@pytest.mark.asyncio
async def test_update_novel_empty_body(client):
    """空请求体返回 422"""
    token = await register_and_login(client)

    files = {"file": ("emptybody.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    resp = await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    novel_id = resp.json()["id"]

    response = await client.patch(
        f"/api/v1/novels/{novel_id}",
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


# ===== 修正章节 =====

@pytest.mark.asyncio
async def test_update_chapter_title(client):
    """手动修正章节标题"""
    token = await register_and_login(client)

    files = {"file": ("fix.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    resp = await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    novel_id = resp.json()["id"]
    chapter_id = resp.json()["chapters"][1]["id"]

    response = await client.patch(
        f"/api/v1/novels/{novel_id}/chapters/{chapter_id}",
        json={"title": "修正后的标题"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "修正后的标题"


# ===== 阅读进度 =====

@pytest.mark.asyncio
async def test_reading_progress_create_and_get(client):
    """创建进度后获取验证"""
    token = await register_and_login(client)

    files = {"file": ("prog.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    resp = await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    novel_id = resp.json()["id"]
    chapter_id = resp.json()["chapters"][1]["id"]

    put_resp = await client.put(
        f"/api/v1/novels/{novel_id}/progress",
        json={"chapter_id": chapter_id, "percentage": 45.5},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert put_resp.status_code == 200

    get_resp = await client.get(
        f"/api/v1/novels/{novel_id}/progress",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert float(data["percentage"]) == pytest.approx(45.5)


@pytest.mark.asyncio
async def test_reading_progress_conflict(client):
    """进度冲突（旧 updated_at）→ 409"""
    token = await register_and_login(client)

    files = {"file": ("conflict.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    resp = await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    novel_id = resp.json()["id"]
    chapter_id = resp.json()["chapters"][1]["id"]

    # 首次创建
    await client.put(
        f"/api/v1/novels/{novel_id}/progress",
        json={"chapter_id": chapter_id, "percentage": 10},
        headers={"Authorization": f"Bearer {token}"}
    )

    # 用旧的 updated_at 更新
    response = await client.put(
        f"/api/v1/novels/{novel_id}/progress",
        json={"chapter_id": chapter_id, "percentage": 20, "updated_at": "2000-01-01T00:00:00"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 409


# ===== 权限隔离 =====

@pytest.mark.asyncio
async def test_cannot_access_others_novel(client):
    """用户A的小说用户B看不到"""
    token_a = await register_and_login(client)

    files = {"file": ("mine.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    resp = await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token_a}"})
    novel_id = resp.json()["id"]

    user_b = {"username": "noveluserb", "email": "novelb@example.com", "password": "testpassword123"}
    await client.post("/api/v1/auth/register", json=user_b)
    login_b = await client.post(
        "/api/v1/auth/login",
        data={"username": user_b["username"], "password": user_b["password"]}
    )
    token_b = login_b.json()["access_token"]

    response = await client.get(f"/api/v1/novels/{novel_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert response.status_code == 404


# ===== 软删除 =====

@pytest.mark.asyncio
async def test_soft_delete_novel(client):
    """软删除后列表中消失"""
    token = await register_and_login(client)

    files = {"file": ("delme.txt", io.BytesIO(SAMPLE_TXT.encode("utf-8")), "text/plain")}
    resp = await client.post("/api/v1/novels/upload", files=files, headers={"Authorization": f"Bearer {token}"})
    novel_id = resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/novels/{novel_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_resp.status_code == 204

    list_resp = await client.get("/api/v1/novels", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.json()["total"] == 0
