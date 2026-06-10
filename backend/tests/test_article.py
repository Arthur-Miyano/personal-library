import pytest

# ========== 测试用的固定数据 ==========
TEST_USER = {
    "username": "articleuser",
    "email": "articleuser@example.com",
    "password": "testpassword123"
}

TEST_ARTICLE = {
    "title": "测试文章标题",
    "raw_text": "这是测试文章的原文内容。"
}


# ========== 辅助函数：快速注册并登录，返回 token ==========
async def register_and_login(client):
    """
    先注册一个新用户，然后用这个用户登录，返回 access_token。
    几乎每个文章接口都需要登录，所以我们把这个重复逻辑抽成函数。
    """
    # 第一步：注册
    await client.post("/api/v1/auth/register", json=TEST_USER)
    # 第二步：登录（注意：登录接口用 form-data，不是 json）
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )
    return response.json()["access_token"]


# ========== 测试 1：未登录时创建文章，返回 401 ==========
@pytest.mark.asyncio
async def test_create_article_without_auth(client):
    """没 token 的人不能创建文章"""
    response = await client.post("/api/v1/articles", json=TEST_ARTICLE)
    assert response.status_code == 401


# ========== 测试 2：登录后成功创建文章 ==========
@pytest.mark.asyncio
async def test_create_article_success(client):
    """登录用户可以正常创建文章"""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == TEST_ARTICLE["title"]
    assert data["raw_text"] == TEST_ARTICLE["raw_text"]
    assert "id" in data  # 创建成功后必须返回文章的 UUID


# ========== 测试 3：获取文章列表 ==========
@pytest.mark.asyncio
async def test_list_articles(client):
    """创建文章后，列表里应该能看到它"""
    token = await register_and_login(client)

    # 先创建一篇文章
    await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )

    # 再获取列表
    response = await client.get(
        "/api/v1/articles",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == TEST_ARTICLE["title"]


# ========== 测试 4：获取单篇文章详情 ==========
@pytest.mark.asyncio
async def test_get_article_detail(client):
    """能根据 ID 获取单篇文章的详情"""
    token = await register_and_login(client)

    # 创建文章
    create_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = create_resp.json()["id"]

    # 获取详情
    response = await client.get(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == article_id
    assert data["title"] == TEST_ARTICLE["title"]


# ========== 测试 5：删除文章后再次获取，返回 404 ==========
@pytest.mark.asyncio
async def test_delete_article_then_get_404(client):
    """软删除：删除成功后，再次获取应该返回 404"""
    token = await register_and_login(client)

    # 创建文章
    create_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = create_resp.json()["id"]

    # 删除文章
    delete_resp = await client.delete(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_resp.status_code == 204

    # 再次获取，应该 404
    get_resp = await client.get(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_resp.status_code == 404
