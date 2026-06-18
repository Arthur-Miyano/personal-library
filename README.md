# 藏卷小筑 v1.4

个人数字图书馆系统 — 文章管理、小说阅读、标签合集、字体管理，四位一体。

**12,668 行** · FastAPI + Vue 3 全栈 · PostgreSQL 16

---

## 技术栈

| 层 | 技术 | 版本 |
|------|------|------|
| **运行时** | Python / Node.js | 3.13 / 22 |
| **后端框架** | FastAPI (async) | 0.110 |
| **ORM** | SQLAlchemy 2.0 (async) | 2.0 |
| **数据库** | PostgreSQL + Alembic | 16 |
| **前端框架** | Vue 3 Composition API | 3.5 |
| **语言** | TypeScript | 5.x |
| **构建** | Vite | 8 |
| **UI 库** | Element Plus | 2.14 |
| **动画** | GSAP | 3.15 |
| **状态管理** | Pinia | 3.0 |

### 关键依赖

| 包 | 用途 |
|------|------|
| `bcrypt` | 密码哈希 |
| `python-jose` | JWT 令牌签发/验证 |
| `aiofiles` | 异步文件 IO (非阻塞) |
| `chardet` + `fonttools` + `Pillow` | 编码检测 / 字体解析 / 图片验证 |
| `ebooklib` + `PyPDF2` + `python-docx` | EPUB/PDF/DOCX 文本提取 |
| `dompurify` | 前端 XSS 二次净化 |
| `lucide-vue-next` + `vuedraggable` | 图标库 / 拖拽排序 |

---

## 项目结构

```
personal_library/
│
├── README.md
├── .gitignore
│
├── backend/
│   ├── pyproject.toml              # 依赖与工具配置 (ruff/mypy/black)
│   ├── alembic.ini
│   ├── docker-compose.yml          # PostgreSQL 容器
│   │
│   ├── alembic/
│   │   ├── env.py                  # 迁移引擎 (从 config.py 读取 DB URL)
│   │   └── versions/               # 12 个迁移脚本
│   │       ├── c2c75098a151        # 创建 users 表
│   │       ├── a511d67503be        # 创建 articles 表
│   │       ├── b2c3d4e5f6a7        # articles 添加 content_hash 去重
│   │       ├── 2c65267e41e3        # 创建 tags / article_tags 表
│   │       ├── 81b158d0502b        # 创建 novels / chapters / reading_progresses 表
│   │       ├── d4e5f6a7b8c9        # chapters 字段扩展 + novel 软删除
│   │       ├── f8a9b0c1d2e3        # 修复 cover_path URL 格式
│   │       ├── 94e733fd9f33        # 创建 collections / collection_articles 表
│   │       ├── a1b2c3d4e5f6        # 创建 fonts 表
│   │       ├── e1b42610b358        # 创建 user_settings 表
│   │       └── 5da8870171d5        # chapter 添加 suffix + user 添加 nickname
│   │
│   ├── src/personal_library/
│   │   ├── main.py                 # FastAPI 应用入口 + CORS + 异常处理
│   │   ├── config.py               # pydantic-settings 配置 (从 .env 读取)
│   │   ├── database.py             # async engine + session 工厂
│   │   │
│   │   ├── api/
│   │   │   ├── deps.py             # 依赖注入: get_db / get_current_user
│   │   │   └── v1/
│   │   │       ├── router.py       # 路由聚合 (prefix=/api/v1)
│   │   │       ├── auth.py         # POST register / login / me / profile / refresh / token
│   │   │       ├── articles.py     # CRUD + batch-tag / batch-set-tags / trash / search
│   │   │       ├── tags.py         # upsert 创建 / 列表 / 删除
│   │   │       ├── collections.py  # CRUD + batch-add / move / sort
│   │   │       ├── novels.py       # upload / CRUD / chapters / progress / restore
│   │   │       ├── upload.py       # 文章文件上传 + 去重 + 文本清洗
│   │   │       ├── fonts.py        # upload / list / delete (路径遍历防护)
│   │   │       ├── settings.py     # GET / PATCH 用户排版设置
│   │   │       └── admin.py        # 服务器批量导入
│   │   │
│   │   ├── core/
│   │   │   ├── security.py         # bcrypt 哈希 + JWT 签发 (可配置过期时间)
│   │   │   ├── xss.py              # HTML 净化 (script/iframe/event/handler 正则)
│   │   │   ├── file_extractor.py   # 多格式文本提取 (TXT/EPUB/PDF/DOCX/MD/HTML)
│   │   │   └── chapter_parser.py   # 小说章节自动拆分 + suffix 分配
│   │   │
│   │   ├── domain/
│   │   │   ├── models/             # 11 个 ORM 模型
│   │   │   │   ├── base.py         # Base + TimestampMixin
│   │   │   │   ├── user.py         # (id, username, email, password, nickname)
│   │   │   │   ├── article.py      # (title, raw_text, content_hash, source_type, …)
│   │   │   │   ├── tag.py          # Tag + ArticleTag 关联表
│   │   │   │   ├── novel.py        # (title, author, cover_path, file_path, …)
│   │   │   │   ├── chapter.py      # (chapter_number, suffix, title, content, …)
│   │   │   │   ├── reading_progress.py  # (user_id, novel_id, chapter_id, percentage)
│   │   │   │   ├── collection.py   # Collection + CollectionArticle 关联表
│   │   │   │   ├── font.py         # (filename, font_family, stored_path, …)
│   │   │   │   └── settings.py     # UserSettings (字体/排版/主题偏好)
│   │   │   │
│   │   │   └── repositories/       # 7 个数据访问层
│   │   │       ├── article.py      # CRUD + 列表(分页/搜索/标签筛选) + 去重 + 软删除
│   │   │       ├── tag.py          # 按用户列表
│   │   │       ├── novel.py        # CRUD + 章节管理 + 恢复
│   │   │       ├── collection.py   # CRUD + 文章增删 + 排序
│   │   │       ├── reading_progress.py  # 原子 upsert (ON CONFLICT)
│   │   │       ├── font.py         # CRUD
│   │   │       └── settings.py     # GET / UPSERT
│   │   │
│   │   └── infrastructure/
│   │       └── schemas/            # 6 个 Pydantic v2 schema
│   │           ├── auth.py         # RegisterRequest(密码 ≥12 + 3 种字符)
│   │           ├── article.py      # ArticleResponse / ArticleCreate
│   │           ├── tag.py          # TagResponse / TagCreate
│   │           ├── novel.py        # NovelResponse + 分页
│   │           ├── collection.py   # CollectionResponse
│   │           ├── font.py         # FontResponse
│   │           └── settings.py     # SettingsResponse / SettingsUpdate
│   │
│   └── tests/                      # 11 个测试文件 (pytest + httpx)
│       ├── conftest.py             # async client + DB fixture
│       ├── test_auth.py            # 注册 / 登录 / me
│       ├── test_article.py         # CRUD
│       ├── test_article_update.py  # 更新
│       ├── test_tag.py             # 标签 CRUD
│       ├── test_collection.py      # 合集 CRUD + 排序
│       ├── test_novel.py           # 小说 CRUD + 章节
│       ├── test_upload.py          # 文件上传 + XSS 过滤
│       ├── test_settings.py        # 设置读写
│       ├── test_sort.py            # 排序
│       └── test_trash.py           # 软删除 + 恢复 + 彻底删除
│
└── frontend/
    ├── package.json                # Vue 3 + Element Plus + GSAP + Pinia
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html                  # SPA 入口
    │
    └── src/
        ├── main.ts                 # createApp + Pinia + Router
        ├── App.vue                 # 根组件 (CSS 开屏动画 + 主题切换)
        │
        ├── api/
        │   └── index.ts            # Axios 实例 + 拦截器 (Token 注入/401 刷新锁)
        │       # 导出 8 个 API 模块:
        │       # authApi / articlesApi / tagsApi / collectionsApi
        │       # settingsApi / novelsApi / fontsApi / adminApi
        │
        ├── router/
        │   └── index.ts            # 19 条路由 (懒加载) + beforeEach 守卫
        │
        ├── stores/
        │   ├── app.ts              # token / username / nickname / theme
        │   └── article.ts          # articles / tags / 标签筛选
        │
        ├── types/
        │   └── index.ts            # Article / Tag / Collection / Novel
        │       # Chapter / ReadingProgress / UserSettings / PaginatedResponse
        │
        ├── styles/
        │   ├── var.scss            # CSS 变量: 4 套主题 (朱砂/青瓷/墨玉/素笺)
        │   └── global.scss         # 全局样式: 字体 / 纹理 / 动画
        │
        ├── utils/
        │   ├── design.ts           # 文章封面 procedural 生成 (1024 bucket)
        │   └── procedural.ts       # 遗留辅助 (保留未引用)
        │
        ├── hooks/
        │   └── useLongpress.ts     # 长按事件 composable
        │
        ├── layouts/
        │   └── DefaultLayout.vue   # 主布局: 侧栏导航 + FAB 菜单 + 上传模态框
        │
        ├── components/
        │   ├── BookCard.vue        # 文章卡片 (水印首字/标题/摘要/标签栏)
        │   ├── ArticleCard.vue     # 合集详情用卡片
        │   ├── FailureList.vue     # 上传失败列表展示
        │   ├── FindReplaceDialog.vue  # 小说阅读器查找替换
        │   ├── LofterTabbar.vue    # 底部 Tab 导航
        │   ├── ProgressPanel.vue   # 阅读进度面板
        │   └── shared/
        │       └── BookCard.vue    # BookCard 别名导出
        │
        └── pages/                  # 19 个页面组件
            ├── HomePage.vue        # 文章列表 + 多选 + 批量操作
            ├── LoginPage.vue       # 登录 (3D 视差卡片)
            ├── RegisterPage.vue    # 注册
            ├── EditorPage.vue      # 编辑器 (标签暂存 + 文件导入)
            ├── ReaderPage.vue      # 沉浸式阅读器 (读取排版设置)
            ├── SettingsPage.vue    # 字号/行高/段间距/字体/主题
            ├── TagsPage.vue        # 标签管理 (新建/删除)
            ├── TrashPage.vue       # 回收站 (文章/小说双 Tab)
            ├── MinePage.vue        # 个人中心 (书架/设置/回收站入口)
            ├── BookGroupPage.vue   # 合集列表
            ├── CollectionsPage.vue # 合集管理
            ├── CollectionDetailPage.vue  # 合集详情 + 文章列表
            ├── BatchUploadPage.vue # 批量导入 (孤儿文章补加)
            ├── UploadPage.vue      # 单文件上传
            ├── NovelListPage.vue   # 小说书架 (搜索+删除)
            ├── NovelUploadPage.vue # 小说上传 (作者/封面)
            ├── NovelReaderPage.vue # 小说阅读器 (目录/进度/编辑)
            ├── FontManagePage.vue  # 字体上传/管理
            └── UploadPage.vue      # 文章上传
```

---

## 数据模型关系

```
User (1) ────< (N) Article         (文章)
User (1) ────< (N) Tag             (标签)
User (1) ────< (N) Novel           (小说)
User (1) ────< (N) Collection      (合集)
User (1) ────< (N) Font            (字体)
User (1) ──── (1) UserSettings     (排版偏好)

Article  <───> Tag          via ArticleTag         (多对多)
Article  <───> Collection   via CollectionArticle  (多对多)
Novel    <───< Chapter       (1 对多)
Novel    <───< ReadingProgress  (1 对多，按用户)
```

---

## API 端点 (52 个)

| 模块 | 方法 | 端点 | 说明 |
|------|------|------|------|
| **auth** | POST | `/auth/register` | 注册 (密码 ≥12 位 + 3 种字符) |
| | POST | `/auth/login` | 登录 (JSON + Form 双模式) |
| | GET | `/auth/me` | 当前用户信息 |
| | GET | `/auth/profile` | 用户档案 (昵称 + 统计) |
| | PATCH | `/auth/profile` | 更新昵称 |
| | POST | `/auth/refresh` | 刷新 JWT |
| | POST | `/auth/token` | Swagger OAuth2 登录 |
| **articles** | GET | `/articles` | 列表 (支持 q/search/collection_id/page/size) |
| | POST | `/articles` | 创建 |
| | GET | `/articles/{id}` | 详情 |
| | PATCH | `/articles/{id}` | 更新 |
| | DELETE | `/articles/{id}` | 软删除 |
| | POST | `/articles/batch-tag` | 批量打标签 |
| | POST | `/articles/{id}/tags/batch` | 批量设置标签 (替换式) |
| | POST | `/articles/{id}/tags/{tag_id}` | 添加单个标签 |
| | DELETE | `/articles/{id}/tags/{tag_id}` | 移除单个标签 |
| | GET | `/articles/trash/list` | 回收站列表 |
| | PATCH | `/articles/{id}/restore` | 恢复 |
| | DELETE | `/articles/{id}/permanent` | 彻底删除 |
| **tags** | GET | `/tags` | 列表 |
| | POST | `/tags` | upsert 创建 |
| | DELETE | `/tags/{id}` | 删除 |
| **collections** | GET | `/collections` | 列表 (预加载 articles) |
| | POST | `/collections` | 创建 |
| | GET | `/collections/{id}` | 详情 |
| | PATCH | `/collections/{id}` | 更新元数据 |
| | DELETE | `/collections/{id}` | 删除 (级联清理关联) |
| | POST | `/collections/{id}/articles/{aid}` | 添加文章 |
| | DELETE | `/collections/{id}/articles/{aid}` | 移除文章 |
| | POST | `/collections/{id}/articles/batch` | 批量添加 (IN 查询) |
| | POST | `/collections/{id}/articles/{aid}/move` | 上移/下移排序 |
| | PATCH | `/collections/{id}/articles/{aid}/sort` | 设 sort_order |
| **novels** | GET | `/novels` | 列表 (分页) |
| | POST | `/novels/upload` | 上传 + 自动分章 |
| | GET | `/novels/{id}` | 详情 |
| | PATCH | `/novels/{id}` | 更新 |
| | DELETE | `/novels/{id}` | 软删除 |
| | PATCH | `/novels/{id}/restore` | 恢复 |
| | DELETE | `/novels/{id}/permanent` | 彻底删除 |
| | GET | `/novels/{id}/chapters/{cid}` | 章节内容 |
| | PATCH | `/novels/{id}/chapters/{cid}` | 编辑章节 |
| | GET | `/novels/{id}/progress` | 阅读进度 |
| | PUT | `/novels/{id}/progress` | 更新进度 (ON CONFLICT) |
| | GET | `/novels/trash` | 回收站 |
| **upload** | POST | `/upload` | 文章文件上传 (编码检测 + 去重 + 清洗) |
| **fonts** | GET | `/fonts` | 列表 |
| | POST | `/fonts` | 上传 (TTF/OTF 解析) |
| | DELETE | `/fonts/{id}` | 删除 (路径遍历防护) |
| **settings** | GET | `/settings` | 获取设置 |
| | PATCH | `/settings` | 更新设置 |
| **admin** | POST | `/admin/import-path` | 服务器批量导入 |
| | GET | `/admin/import-path/{task_id}` | 导入进度 |

---

## 安全措施

| 层级 | 措施 |
|------|------|
| **密码** | bcrypt + 随机盐, 强度校验 (≥12 位, 大写/小写/数字/特殊 ≥3 种) |
| **认证** | JWT HS256, access token (30min 可配) + refresh (7 天可配) |
| **XSS** | 后端 `sanitize_html()` 去 script/iframe/embed/on* 事件, 前端 DOMPurify 二次净化 |
| **路径遍历** | 字体删除 `realpath` 前缀校验; admin 导入路径解析校验 |
| **SQL 注入** | SQLAlchemy 参数化查询, 无裸 SQL 拼接 |
| **权限** | 所有端点 `get_current_user` 校验所有权, 合集排序/批量操作均校验 |
| **并发** | ReadingProgress upsert 使用 `INSERT ON CONFLICT`, tags upsert 捕捉 IntegrityError |
| **文件** | 扩展名白名单, 文件大小限制 (10MB 文章 / 50MB 小说 / 5MB 封面 / 10MB 字体) |

---

## 快速开始

### 环境要求

- Python ≥ 3.11 + Node.js ≥ 18
- PostgreSQL ≥ 15 (或 `docker compose up -d`)

### 后端

```bash
cd backend
cp .env.example .env          # 编辑 DATABASE_URL + SECRET_KEY
pip install -e ".[test]"
alembic upgrade head
uvicorn personal_library.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

### 测试

```bash
cd backend
pytest tests/ -v              # 11 个测试文件
```

### API 文档

`http://localhost:8000/docs` (Swagger UI, 仅开发环境)
