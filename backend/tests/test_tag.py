import pytest

TEST_USER = {
    "username": "taguser",
    "email": "taguser@example.com",
    "password": "testpassword123"
}

TEST_ARTICLE = {
    "title": "测试文章",
    "raw_text": "测试内容"
}


async def register_and_login(client):
    await client.post("/api/v1/auth/register", json=TEST_USER)
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_tag_success(client):
    """创建标签"""
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/tags",
        json={"name": "技术", "color": "#409EFF"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "技术"
    assert data["color"] == "#409EFF"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_tags(client):
    """获取标签列表"""
    token = await register_and_login(client)

    await client.post(
        "/api/v1/tags",
        json={"name": "技术"},
        headers={"Authorization": f"Bearer {token}"}
    )
    await client.post(
        "/api/v1/tags",
        json={"name": "小说"},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = await client.get(
        "/api/v1/tags",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_add_tag_to_article(client):
    """给文章打标签"""
    token = await register_and_login(client)

    # 创建文章
    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]

    # 创建标签
    tag_resp = await client.post(
        "/api/v1/tags",
        json={"name": "待读"},
        headers={"Authorization": f"Bearer {token}"}
    )
    tag_id = tag_resp.json()["id"]

    # 打标签
    response = await client.post(
        f"/api/v1/articles/{article_id}/tags/{tag_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204

    # 按标签筛选文章
    list_resp = await client.get(
        f"/api/v1/articles?tag_id={tag_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert list_resp.status_code == 200
    articles = list_resp.json()
    assert len(articles) == 1
    assert articles[0]["id"] == str(article_id)


@pytest.mark.asyncio
async def test_remove_tag_from_article(client):
    """从文章移除标签"""
    token = await register_and_login(client)

    # 创建文章和标签
    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]

    tag_resp = await client.post(
        "/api/v1/tags",
        json={"name": "临时"},
        headers={"Authorization": f"Bearer {token}"}
    )
    tag_id = tag_resp.json()["id"]

    # 先打标签
    await client.post(
        f"/api/v1/articles/{article_id}/tags/{tag_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # 再移除
    response = await client.delete(
        f"/api/v1/articles/{article_id}/tags/{tag_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204

    # 确认筛选不到这篇文章了
    list_resp = await client.get(
        f"/api/v1/articles?tag_id={tag_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_delete_tag(client):
    """删除标签"""
    token = await register_and_login(client)

    tag_resp = await client.post(
        "/api/v1/tags",
        json={"name": "废弃标签"},
        headers={"Authorization": f"Bearer {token}"}
    )
    tag_id = tag_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/tags/{tag_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204

    # 确认列表里没有了
    list_resp = await client.get(
        "/api/v1/tags",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(list_resp.json()) == 0
