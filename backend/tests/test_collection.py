import pytest

TEST_USER = {
    "username": "collectionuser",
    "email": "collectionuser@example.com",
    "password": "TestPass123!"
}

TEST_ARTICLE = {
    "title": "测试文章",
    "raw_text": "测试内容"
}

TEST_COLLECTION = {
    "name": "我的收藏夹",
    "description": "这是一个测试收藏夹",
    "color": "#FF0000",
    "icon": "star"
}


async def register_and_login(client):
    """注册并登录，返回 access_token"""
    await client.post("/api/v1/auth/register", json=TEST_USER)
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_collection_success(client):
    """登录后创建收藏夹"""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/collections",
        json=TEST_COLLECTION,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == TEST_COLLECTION["name"]
    assert data["description"] == TEST_COLLECTION["description"]
    assert data["color"] == TEST_COLLECTION["color"]
    assert data["icon"] == TEST_COLLECTION["icon"]
    assert "id" in data


@pytest.mark.asyncio
async def test_list_collections(client):
    """创建收藏夹后，列表里应该能看到"""
    token = await register_and_login(client)

    # 创建两个收藏夹（显式设置不同 sort_order 避免排序不确定性）
    await client.post(
        "/api/v1/collections",
        json={"name": "收藏夹A", "sort_order": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    await client.post(
        "/api/v1/collections",
        json={"name": "收藏夹B", "sort_order": 2},
        headers={"Authorization": f"Bearer {token}"}
    )

    # 获取列表
    response = await client.get(
        "/api/v1/collections",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "收藏夹A"
    assert data[1]["name"] == "收藏夹B"


@pytest.mark.asyncio
async def test_add_article_to_collection(client):
    """把文章加入收藏夹"""
    token = await register_and_login(client)

    # 先创建一篇文章
    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]

    # 再创建一个收藏夹
    collection_resp = await client.post(
        "/api/v1/collections",
        json={"name": "技术文章"},
        headers={"Authorization": f"Bearer {token}"}
    )
    collection_id = collection_resp.json()["id"]

    # 把文章加入收藏夹
    response = await client.post(
        f"/api/v1/collections/{collection_id}/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_article_from_collection(client):
    """从收藏夹移除文章"""
    token = await register_and_login(client)

    # 创建文章和收藏夹
    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]

    collection_resp = await client.post(
        "/api/v1/collections",
        json={"name": "待读清单"},
        headers={"Authorization": f"Bearer {token}"}
    )
    collection_id = collection_resp.json()["id"]

    # 先加入
    await client.post(
        f"/api/v1/collections/{collection_id}/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # 再移除
    response = await client.delete(
        f"/api/v1/collections/{collection_id}/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_cannot_access_others_collection(client):
    """不能查看别人的收藏夹（权限隔离）"""
    # 用户A 创建收藏夹
    token_a = await register_and_login(client)
    collection_resp = await client.post(
        "/api/v1/collections",
        json={"name": "A的私密收藏"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    collection_id = collection_resp.json()["id"]

    # 用户B 注册并尝试访问
    user_b = {
        "username": "userb",
        "email": "userb@example.com",
        "password": "TestPass123!"
    }
    await client.post("/api/v1/auth/register", json=user_b)
    login_b = await client.post(
        "/api/v1/auth/login",
        data={"username": user_b["username"], "password": user_b["password"]}
    )
    token_b = login_b.json()["access_token"]

    # 用户B 获取用户A的收藏夹 → 应该 403
    response = await client.get(
        f"/api/v1/collections/{collection_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )

    assert response.status_code == 403
