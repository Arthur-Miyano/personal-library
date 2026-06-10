import pytest

TEST_USER = {
    "username": "updateuser",
    "email": "updateuser@example.com",
    "password": "testpassword123"
}

TEST_ARTICLE = {
    "title": "原标题",
    "raw_text": "原文内容"
}


async def register_and_login(client):
    await client.post("/api/v1/auth/register", json=TEST_USER)
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_update_article_title(client):
    """只修改文章标题"""
    token = await register_and_login(client)

    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]

    # 只改标题
    response = await client.patch(
        f"/api/v1/articles/{article_id}",
        json={"title": "新标题"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "新标题"
    assert data["raw_text"] == "原文内容"  # 内容没变


@pytest.mark.asyncio
async def test_update_article_content(client):
    """只修改文章内容"""
    token = await register_and_login(client)

    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]

    # 只改内容
    response = await client.patch(
        f"/api/v1/articles/{article_id}",
        json={"raw_text": "新内容"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "原标题"  # 标题没变
    assert data["raw_text"] == "新内容"


@pytest.mark.asyncio
async def test_cannot_update_others_article(client):
    """不能修改别人的文章"""
    # 用户A 创建文章
    token_a = await register_and_login(client)
    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token_a}"}
    )
    article_id = article_resp.json()["id"]

    # 用户B 尝试修改
    user_b = {
        "username": "updateuserb",
        "email": "updateuserb@example.com",
        "password": "testpassword123"
    }
    await client.post("/api/v1/auth/register", json=user_b)
    login_b = await client.post(
        "/api/v1/auth/login",
        data={"username": user_b["username"], "password": user_b["password"]}
    )
    token_b = login_b.json()["access_token"]

    response = await client.patch(
        f"/api/v1/articles/{article_id}",
        json={"title": "恶意修改"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 403
