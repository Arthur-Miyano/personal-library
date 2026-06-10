from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库连接地址，例如 "postgresql+asyncpg://user:pass@localhost/dbname"
    database_url: str
    secret_key: str
    app_name: str = "personal_library"    # 应用名，有默认值
    app_env: str = "development"          # 运行环境：development / production
    upload_dir: str = "./uploads"         # 小说文件上传目录

    model_config = {
        "env_file": ".env",   # 从项目根目录的 .env 文件读取配置
        "extra": "ignore",    # 忽略 .env 中未定义的其他变量
    }

# 生成一个全局的配置实例，后续用 from ... import settings 直接使用
settings = Settings()