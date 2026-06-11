import pytest

TEST_USER = {
    "username": "settingsuser",
    "email": "settingsuser@example.com",
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
async def test_get_settings_auto_create(client):
    """首次获取设置时，自动创建默认设置"""
    token = await register_and_login(client)

    response = await client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["theme_mode"] == "light"
    assert data["bg_color"] == "#FFFFFF"
    assert data["font_size"] == 16
    assert data["first_line_indent"] is True
    assert data["default_reformat"] is False


@pytest.mark.asyncio
async def test_update_settings(client):
    """修改部分设置字段"""
    token = await register_and_login(client)

    # 先获取默认设置
    await client.get("/api/v1/settings", headers={"Authorization": f"Bearer {token}"})

    # 修改字体大小和主题
    response = await client.patch(
        "/api/v1/settings",
        json={"font_size": 20, "theme_mode": "dark"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["font_size"] == 20
    assert data["theme_mode"] == "dark"
    # 其他字段保持默认值
    assert data["bg_color"] == "#FFFFFF"
    assert data["line_height"] == pytest.approx(1.8)


@pytest.mark.asyncio
async def test_update_settings_partial(client):
    """只修改一个字段，其他不变"""
    token = await register_and_login(client)

    # 先获取默认设置
    await client.get("/api/v1/settings", headers={"Authorization": f"Bearer {token}"})

    # 只改 reader_max_width
    response = await client.patch(
        "/api/v1/settings",
        json={"reader_max_width": 1000},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reader_max_width"] == 1000
    assert data["font_size"] == 16  # 没变
