import pytest

TEST_USER = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword123"
}
# 专门用于登录接口的请求体（没有email字段）
LOGIN_USER = {
    "username": "testuser",
    "password": "testpassword123"
     }


# 测试1：用户注册成功
@pytest.mark.asyncio
async def test_register_success(client):
    # 发送注册请求
    response = await client.post(
        "/api/v1/auth/register",
        json=TEST_USER
    )

    # 断言状态码是201（创建成功）
    assert response.status_code == 201
    # 断言响应中包含access_token
    assert "access_token" in response.json()
    # 断言token类型是bearer
    assert response.json()["token_type"] == "bearer"


# 测试2：用户登录成功
@pytest.mark.asyncio
async def test_login_success(client):
    # 第一步：先注册一个用户
    await client.post(
        "/api/v1/auth/register",
        json=TEST_USER
    )

    # 第二步：用刚才注册的用户登录
    response = await client.post(
        "/api/v1/auth/login",
        data=LOGIN_USER  
    )

    # 断言状态码是200（成功）
    assert response.status_code == 200
    # 断言响应中包含access_token
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


# 测试3：JSON格式登录成功
@pytest.mark.asyncio
async def test_login_json(client):
    """用 JSON 格式登录（测试 body 路径）"""
    await client.post("/api/v1/auth/register", json=TEST_USER)

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


# 测试4：未登录访问个人信息接口返回401
@pytest.mark.asyncio
async def test_me_unauthorized(client):
    # 不携带任何token，直接访问个人信息接口
    response = await client.get("/api/v1/auth/me")

    # 断言状态码是401（未授权）
    assert response.status_code == 401



