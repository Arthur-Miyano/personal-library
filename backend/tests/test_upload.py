import io
import pytest

TEST_USER = {
    "username": "uploaduser",
    "email": "uploaduser@example.com",
    "password": "TestPass123!"
}


async def register_and_login(client):
    await client.post("/api/v1/auth/register", json=TEST_USER)
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_upload_txt_file(client):
    """上传 .txt 文件创建文章"""
    token = await register_and_login(client)

    # 构造一个内存中的文本文件
    file_content = "这是上传的测试文本内容。\n第二行内容。".encode("utf-8")
    files = {
        "file": ("测试文档.txt", io.BytesIO(file_content), "text/plain")
    }

    response = await client.post(
        "/api/v1/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "测试文档"  # 去掉了 .txt 扩展名
    assert data["raw_text"] == file_content.decode("utf-8")


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_type(client):
    """上传不支持的文件类型应被拒绝"""
    token = await register_and_login(client)

    files = {
        "file": ("恶意.exe", io.BytesIO(b"binary data"), "application/octet-stream")
    }

    response = await client.post(
        "/api/v1/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_xss_filter(client):
    """上传内容中包含 script 标签应被过滤"""
    token = await register_and_login(client)

    file_content = "正常内容<script>alert('xss')</script>结尾".encode("utf-8")
    files = {
        "file": ("xss_test.txt", io.BytesIO(file_content), "text/plain")
    }

    response = await client.post(
        "/api/v1/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert "<script>" not in data["raw_text"]
    assert "正常内容" in data["raw_text"]
    assert "结尾" in data["raw_text"]
