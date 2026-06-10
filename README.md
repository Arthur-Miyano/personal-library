# 个人图书馆（Personal Library）

一个前后端分离的个人数字图书馆系统，支持文章导入、小说阅读、字体管理。

## 功能

### 文章管理
- 支持导入 .txt / .md / .html / .epub / .pdf / .docx 文件
- 自动提取 EPUB、PDF、DOCX 正文
- 标签管理（自定义颜色）
- 合集/收藏夹管理（拖拽排序）
- 软删除 + 回收站
- 查找替换（阅读页内弹窗）

### 小说阅读
- 上传 .txt / .epub / .pdf，自动识别中文章节标题（第X章）
- 章节目录导航
- 阅读进度追踪（乐观锁防多设备冲突）
- 章节内容编辑 + 查找替换
- 封面图上传

### 阅读器设置
- 字体大小、行高、阅读宽度
- 背景色自定义
- 首行缩进开关
- 自定义字体上传（.ttf / .otf）

### 用户系统
- JWT 认证（注册即登录）
- 用户名或邮箱登录
- 深色模式

## 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | FastAPI (Python 3.11+) |
| ORM | SQLAlchemy 2.0 (async) |
| 数据库 | PostgreSQL 16 |
| 迁移 | Alembic |
| 前端框架 | Vue 3 + TypeScript |
| UI 库 | Element Plus |
| 构建 | Vite |
| 状态管理 | Pinia |

## 项目结构

```
personal_library/
├── backend/                     # 后端（FastAPI）
│   ├── src/personal_library/
│   │   ├── api/v1/              # API 路由
│   │   │   ├── auth.py          #   认证（注册/登录/刷新）
│   │   │   ├── articles.py      #   文章 CRUD + 标签关联 + 回收站
│   │   │   ├── collections.py   #   合集管理
│   │   │   ├── tags.py          #   标签管理
│   │   │   ├── settings.py      #   阅读器设置
│   │   │   ├── upload.py        #   文章文件上传
│   │   │   ├── novels.py        #   小说上传/阅读/进度
│   │   │   └── fonts.py         #   字体上传/管理
│   │   ├── core/                # 核心工具
│   │   │   ├── security.py      #   JWT + bcrypt
│   │   │   ├── chapter_parser.py#   小说章节检测
│   │   │   ├── file_extractor.py#   多格式文本提取
│   │   │   └── xss.py           #   XSS 过滤
│   │   ├── domain/
│   │   │   ├── models/          # ORM 模型（10个表）
│   │   │   └── repositories/    # 数据访问层
│   │   ├── infrastructure/
│   │   │   └── schemas/         # Pydantic 请求/响应模型
│   │   ├── config.py            # 配置（pydantic-settings）
│   │   ├── database.py          # 数据库引擎
│   │   └── main.py              # FastAPI 入口
│   ├── alembic/                 # 数据库迁移
│   ├── tests/                   # 测试（50 用例）
│   ├── docker-compose.yml       # PostgreSQL 容器
│   └── pyproject.toml
│
├── frontend/                    # 前端（Vue 3）
│   ├── src/
│   │   ├── api/index.ts         # API 接口层
│   │   ├── router/index.ts      # 路由配置
│   │   ├── stores/app.ts        # 全局状态（Pinia）
│   │   ├── pages/               # 页面组件（15 个）
│   │   ├── components/          # 通用组件
│   │   ├── styles/              # 全局样式 + LOFTER 主题
│   │   └── types/index.ts       # TypeScript 类型
│   └── vite.config.ts
│
└── README.md
```

## 快速开始

### 1. 启动数据库

```bash
cd backend
docker-compose up -d
```

### 2. 配置环境变量

在 `backend/` 目录下创建 `.env` 文件：

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/personal_library
SECRET_KEY=your-secret-key-change-in-production
APP_ENV=development
UPLOAD_DIR=./uploads
```

### 3. 启动后端

```bash
cd backend
pip install -e .
alembic upgrade head
uvicorn personal_library.main:app --host 0.0.0.0 --port 8000 --reload
```

API 文档：http://localhost:8000/docs

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

## 数据库表

| 表名 | 说明 |
|------|------|
| users | 用户 |
| articles | 文章（支持软删除） |
| tags | 标签 |
| article_tags | 文章-标签 多对多 |
| collections | 合集/收藏夹 |
| collection_articles | 合集-文章 多对多 |
| novels | 小说 |
| chapters | 章节（含序言标记、内容哈希） |
| reading_progresses | 阅读进度 |
| user_settings | 阅读器偏好设置 |
| fonts | 用户上传的字体 |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/register | 注册 |
| POST | /api/v1/auth/login | 登录（支持 JSON 和 Form） |
| GET | /api/v1/auth/me | 当前用户信息 |
| POST | /api/v1/auth/refresh | 刷新 token |
| GET | /api/v1/articles | 文章列表（支持标签筛选） |
| POST | /api/v1/articles | 创建文章 |
| GET | /api/v1/articles/{id} | 文章详情 |
| PATCH | /api/v1/articles/{id} | 修改文章 |
| DELETE | /api/v1/articles/{id} | 软删除 |
| GET | /api/v1/articles/trash/list | 回收站列表 |
| PATCH | /api/v1/articles/{id}/restore | 恢复文章 |
| DELETE | /api/v1/articles/{id}/permanent | 彻底删除 |
| POST | /api/v1/upload | 上传文件创建文章 |
| GET/POST/DELETE | /api/v1/tags | 标签 CRUD |
| POST/DELETE | /api/v1/articles/{id}/tags/{id} | 文章标签关联 |
| GET/POST/PATCH | /api/v1/collections | 合集 CRUD |
| POST/DELETE | /api/v1/collections/{id}/articles/{id} | 合集文章关联 |
| GET/PATCH | /api/v1/settings | 阅读器设置 |
| GET/POST/PATCH/DELETE | /api/v1/novels/** | 小说管理（11 个端点） |
| GET/PUT | /api/v1/novels/{id}/progress | 阅读进度 |
| GET/POST/DELETE | /api/v1/fonts | 字体管理 |

## 许可证

MIT
