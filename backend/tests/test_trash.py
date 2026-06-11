import pytest

TEST_USER = {
    "username": "trashuser",
    "email": "trashuser@example.com",
    "password": "TestPass123!"
}

TEST_ARTICLE = {
    "title": "即将被删除的文章",
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
async def test_trash_list_after_soft_delete(client):
    """软删除后，文章应该出现在回收站列表里"""
    token = await register_and_login(client)

    # 创建文章
    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]

    # 软删除
    await client.delete(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # 正常列表里应该看不到
    normal_list = await client.get(
        "/api/v1/articles",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(normal_list.json()) == 0

    # 回收站里应该能看到
    trash_resp = await client.get(
        "/api/v1/articles/trash/list",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert trash_resp.status_code == 200
    trash_articles = trash_resp.json()
    assert len(trash_articles) == 1
    assert trash_articles[0]["id"] == str(article_id)


@pytest.mark.asyncio
async def test_restore_article(client):
    """恢复回收站里的文章"""
    token = await register_and_login(client)

    # 创建并删除
    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]
    await client.delete(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # 恢复
    restore_resp = await client.patch(
        f"/api/v1/articles/{article_id}/restore",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["id"] == str(article_id)

    # 正常列表里又能看到了
    normal_list = await client.get(
        "/api/v1/articles",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(normal_list.json()) == 1

    # 回收站里看不到了
    trash_resp = await client.get(
        "/api/v1/articles/trash/list",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(trash_resp.json()) == 0


@pytest.mark.asyncio
async def test_permanently_delete_article(client):
    """彻底删除文章后，回收站里也找不到"""
    token = await register_and_login(client)

    # 创建并删除
    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]
    await client.delete(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # 确认在回收站里
    trash_resp = await client.get(
        "/api/v1/articles/trash/list",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(trash_resp.json()) == 1

    # 彻底删除
    del_resp = await client.delete(
        f"/api/v1/articles/{article_id}/permanent",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert del_resp.status_code == 204

    # 回收站里也不存在了
    trash_resp2 = await client.get(
        "/api/v1/articles/trash/list",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert len(trash_resp2.json()) == 0


@pytest.mark.asyncio
async def test_cannot_restore_others_article(client):
    """不能恢复别人的文章"""
    # 用户A 创建并删除文章
    token_a = await register_and_login(client)
    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token_a}"}
    )
    article_id = article_resp.json()["id"]
    await client.delete(
        f"/api/v1/articles/{article_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )

    # 用户B 尝试恢复
    user_b = {
        "username": "trashuserb",
        "email": "trashuserb@example.com",
        "password": "TestPass123!"
    }
    await client.post("/api/v1/auth/register", json=user_b)
    login_b = await client.post(
        "/api/v1/auth/login",
        data={"username": user_b["username"], "password": user_b["password"]}
    )
    token_b = login_b.json()["access_token"]

    response = await client.patch(
        f"/api/v1/articles/{article_id}/restore",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 403
