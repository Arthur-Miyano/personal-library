# 阅读器个人图书馆/1.0
个人数字图书馆系统 — 文章管理、小说阅读、字体管理，三位一体。

## 技术栈

| 层 | 技术 |
|------|------|
| **后端** | Python 3.13 + FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 16 |
| **前端** | Vue 3 Composition API + TypeScript + Pinia + Vite |
| **认证** | JWT (HS256) + bcrypt 密码哈希 |
| **数据库** | PostgreSQL 16 + Alembic 迁移 |

## 功能

- **文章管理** — 创建/编辑/删除，标签系统，批量操作，全文搜索
- **小说阅读** — TXT/EPUB/PDF 上传，自动分章，阅读进度追踪
- **合集系统** — 自定义合集，文章排序，批量添加
- **字体管理** — 上传 TTF/OTF，自动解析字体族名
- **阅读设置** — 字体/字号/行高/段间距/阅读宽度/首行缩进，实时生效
- **回收站** — 软删除 + 恢复 + 彻底删除
- **多主题** — 朱砂/青瓷/墨玉/素笺 四套配色

## 项目结构

```
backend/
  src/personal_library/
    api/v1/         # REST API 端点 (auth/articles/collections/tags/novels/fonts/settings/upload/admin)
    core/            # 安全/XSS/文件解析/章节分拆
    domain/
      models/        # SQLAlchemy ORM 模型
      repositories/  # 数据访问层
    infrastructure/  # Pydantic schema
  alembic/           # 数据库迁移
  tests/             # pytest + httpx 测试

frontend/
  src/
    api/             # Axios 封装 + 拦截器
    components/      # 通用组件 (BookCard 等)
    layouts/         # 默认布局 (侧栏/导航/FAB)
    pages/           # 18 个页面组件
    stores/          # Pinia 状态管理
    styles/          # CSS 变量 + 全局样式
    types/           # TypeScript 类型定义
```

## 快速开始

### 环境要求
- Python ≥ 3.11
- Node.js ≥ 18
- PostgreSQL ≥ 15

### 后端

```bash
cd backend
cp .env.example .env          # 编辑数据库连接和密钥
pip install -e .
alembic upgrade head
uvicorn personal_library.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev                    # 默认 http://localhost:5173
```

## API 文档

开发环境下访问 `http://localhost:8000/docs` 查看 Swagger UI。

## 测试

```bash
cd backend
pytest tests/ -v
<img width="2549" height="1403" alt="5794e350ac2c152510dbf833773b271b" src="https://github.com/user-attachments/assets/d6294acb-5c43-4477-9f03-ec211176a6fa" />



```

## 许可

MIT
