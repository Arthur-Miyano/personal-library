import pytest

TEST_USER = {
    "username": "sortuser",
    "email": "sortuser@example.com",
    "password": "TestPass123!"
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
async def test_update_collection_sort_order(client):
    """修改收藏夹的排序权重"""
    token = await register_and_login(client)

    # 创建收藏夹
    resp = await client.post(
        "/api/v1/collections",
        json={"name": "A收藏夹"},
        headers={"Authorization": f"Bearer {token}"}
    )
    collection_id = resp.json()["id"]

    # 修改排序为 100
    patch_resp = await client.patch(
        f"/api/v1/collections/{collection_id}",
        json={"sort_order": 100},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert patch_resp.status_code == 200
    assert patch_resp.json()["sort_order"] == 100


@pytest.mark.asyncio
async def test_collection_list_sorted_by_sort_order(client):
    """收藏夹列表按 sort_order 升序排列"""
    token = await register_and_login(client)

    # 创建两个收藏夹，先创建的默认 sort_order=0
    await client.post(
        "/api/v1/collections",
        json={"name": "Z收藏夹"},
        headers={"Authorization": f"Bearer {token}"}
    )
    resp_b = await client.post(
        "/api/v1/collections",
        json={"name": "A收藏夹"},
        headers={"Authorization": f"Bearer {token}"}
    )
    collection_b_id = resp_b.json()["id"]

    # 把 B 的 sort_order 设为 -1（让它排在前面）
    await client.patch(
        f"/api/v1/collections/{collection_b_id}",
        json={"sort_order": -1},
        headers={"Authorization": f"Bearer {token}"}
    )

    # 获取列表，验证顺序
    list_resp = await client.get(
        "/api/v1/collections",
        headers={"Authorization": f"Bearer {token}"}
    )
    collections = list_resp.json()
    assert collections[0]["name"] == "A收藏夹"  # sort_order=-1 排第一
    assert collections[1]["name"] == "Z收藏夹"  # sort_order=0 排第二


@pytest.mark.asyncio
async def test_update_article_sort_in_collection(client):
    """调整收藏夹内文章的排序"""
    token = await register_and_login(client)

    # 创建收藏夹和文章
    coll_resp = await client.post(
        "/api/v1/collections",
        json={"name": "测试收藏夹"},
        headers={"Authorization": f"Bearer {token}"}
    )
    collection_id = coll_resp.json()["id"]

    article_resp = await client.post(
        "/api/v1/articles",
        json=TEST_ARTICLE,
        headers={"Authorization": f"Bearer {token}"}
    )
    article_id = article_resp.json()["id"]

    # 加入收藏夹
    await client.post(
        f"/api/v1/collections/{collection_id}/articles/{article_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # 修改排序
    patch_resp = await client.patch(
        f"/api/v1/collections/{collection_id}/articles/{article_id}/sort?sort_order=99",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert patch_resp.status_code == 204
