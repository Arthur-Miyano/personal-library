import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt
from personal_library.config import settings

# 密码哈希
def hash_password(password: str) -> str:
    """
    对密码进行哈希处理
    :param password:
    :return:
    """
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

#密码验证
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    bcrypt.checkpw 需 bytes 类型，且参数顺序是「明文→哈希」
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),# 明文转 bytes
        hashed_password.encode('utf-8')# 哈希串转 bytes
    )
def create_access_token(subject: str) -> str:
    """创建 JWT access token，subject 为用户 ID (UUID 字符串)"""
    expire_time = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {
        "sub": subject,
        "exp": expire_time,
    }
    token = jwt.encode(
        payload,
        settings.secret_key,  # 从配置文件读取密钥（需确保 settings 有该属性）
        algorithm="HS256"     # 签名算法
    )
    return token