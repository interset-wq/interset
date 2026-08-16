# interset

前后端分离的 FastAPI 演示项目：FastAPI + SQLModel 提供后端 API，前端（Vue 3 + Vite）构建为静态文件，由 FastAPI 统一托管。

## 技术栈

- Python >= 3.14，uv 管理依赖
- FastAPI（含 uvicorn）
- SQLModel（SQLAlchemy + Pydantic）
- 数据库：SQLite（开发默认）/ PostgreSQL（生产，支持 Neon 云数据库，psycopg 驱动）
- 前端：Vue 3 + Vite（pnpm 管理），构建产物为 `dist/`

## 本地开发

```bash
# 1. 安装后端依赖
uv sync

# 2. （可选）本地连接 PostgreSQL/Neon：设置连接串；未设置则默认本地 SQLite
#    部署时无需手动设置——FastAPI Cloud 内置 Neon 集成会自动注入 DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"

# 3. 构建前端（首次或前端代码变更后）
cd frontend && pnpm install && pnpm build && cd ..

# 4. 启动服务（监听 0.0.0.0:8000，启动时自动建表）
uv run python main.py
# 或：uv run uvicorn app.main:app --reload
```

访问 http://127.0.0.1:8000 查看前端页面，API 文档在 http://127.0.0.1:8000/docs。

前端单独开发时可用 `cd frontend && pnpm dev`（Vite 会把 `/api` 代理到 8000 端口）。

## API 概览

所有列表接口均支持分页：`?offset=0&limit=10`，响应为 `{"items": [...], "total": n}`。

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |

### Hero（英雄，Team 1:N Hero）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/heroes?offset=0&limit=5` | 分页查询英雄 |
| GET | `/api/heroes/{id}` | 查询单个英雄 |
| POST | `/api/heroes` | 创建英雄（id 由数据库生成） |
| PATCH | `/api/heroes/{id}` | 部分更新英雄 |
| DELETE | `/api/heroes/{id}` | 删除英雄 |

### Team（团队）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/teams?offset=0&limit=5` | 分页查询团队（含成员） |
| GET | `/api/teams/{id}` | 查询单个团队 |
| POST | `/api/teams` | 创建团队（重名返回 409） |
| PATCH | `/api/teams/{id}` | 部分更新团队 |
| DELETE | `/api/teams/{id}` | 删除团队 |

### Mission（任务，Hero M2M，经中间表 `mission_hero`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/missions?offset=0&limit=5` | 分页查询任务（含关联英雄） |
| GET | `/api/missions/{id}` | 查询单个任务 |
| POST | `/api/missions` | 创建任务（`hero_ids` 关联英雄） |
| PATCH | `/api/missions/{id}` | 部分更新任务 |
| DELETE | `/api/missions/{id}` | 删除任务 |

### mission_hero（M2M 中间表）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/missions/links?offset=0&limit=5` | 分页查询中间表实际行（附名称） |
| POST | `/api/missions/links` | 创建关联（mission_id + hero_id + role） |
| PATCH | `/api/missions/links/{mission_id}/{hero_id}` | 更新中间表行（role） |
| DELETE | `/api/missions/links/{mission_id}/{hero_id}` | 取消关联 |

### 日志与表结构

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/sql-logs?limit=5` | 最近执行的 SQL 日志（仅写操作，参数内联） |
| GET | `/api/tables` | 表结构信息（列名/类型/可空/默认值/主键） |

## UI 说明（Neon/Supabase 风格 Table Editor）

- **左侧 sidebar**：表列表（hero / team / mission / mission_hero）+ Views（schema）
- **右侧可编辑数据网格**：点击单元格直接编辑（PATCH）、`Insert row` 创建（主键 id 不在表单中）、🗑 删除行
- **schema 视图**：psql `\d` 风格，每张表一个表格（Column / Type / Nullable / Default + Indexes）
- **分页**：所有表每页 5 条（固定，不可调整），`← Prev / Page x / y（n rows）/ Next →`
- **SQL 日志面板**：页面底部独立 section，显示最近 5 条用户写操作的 SQL（参数内联）
- **移动端适配**：≤768px 时 sidebar 变横排 chip，表格横向滚动

## 演示数据（seed）

```bash
uv run python seed.py   # 幂等：插入 ~20 条英雄 + 团队/任务/中间表数据，重复运行不重复
```

## 前端模块结构

```
frontend/src/
├── main.js                        # 入口
├── api.js                         # fetch 请求封装
├── composables/
│   └── useTableData.js            # 表数据/分页/CRUD/编辑逻辑
├── components/
│   ├── TableSidebar.vue           # 左侧表列表 + schema 入口
│   ├── SchemaView.vue             # psql \d 风格表结构视图
│   ├── DataGrid.vue               # 可编辑数据网格（单元格编辑/删除）
│   ├── InsertRowForm.vue          # 插入行表单（过滤主键列）
│   ├── PaginationBar.vue          # 分页控件（固定每页 5 条）
│   └── SqlLogPanel.vue            # SQL 日志面板
└── App.vue                        # 根组件：组装子组件 + 全局样式
```

## 部署（FastAPI Cloud，前后端分离方案）

按官方文档 [Deploy a Full-Stack App](https://fastapicloud.com/docs/builds-and-deployments/frontend/) 处理。

### 方式一：CI 自动部署（推荐，已配置 workflow）

仓库已含 `.github/workflows/deploy.yml`：push 到 `main` 时自动构建前端并部署到 FastAPI Cloud。

需要在 GitHub 仓库配置两个 secrets（参见 [Deploy Tokens](https://fastapicloud.com/docs/advanced-features/deploy-tokens)）：

| Secret | 说明 |
|--------|------|
| `FASTAPI_CLOUD_TOKEN` | FastAPI Cloud 部署令牌 |
| `FASTAPI_CLOUD_APP_ID` | FastAPI Cloud 应用 ID |

workflow 流程：`pnpm install --frozen-lockfile && pnpm build`（生成 `dist/`）→ `uv run fastapi deploy`。

### 方式二：本地部署

```bash
# 1. 本地先构建前端（FastAPI Cloud 不会自动运行前端构建）
cd frontend && pnpm build && cd ..

# 2. 部署
uv run fastapi deploy
```

### 部署要点

- `dist/` 被 `.gitignore` 忽略（构建产物不入库），但 `.fastapicloudignore` 中的 `!dist/` 会确保部署时上传
- **连接 Neon 数据库**（可选）：在 FastAPI Cloud 的 Integrations 中连接 Neon 账户并选择数据库，平台会自动创建 `DATABASE_URL` 环境变量（以加密 secret 存储），应用启动时读取该变量连接 PostgreSQL；未连接则使用本地 SQLite

## 项目结构

```
├── main.py              # 本地启动入口（uv run python main.py）
├── seed.py              # 演示数据填充脚本（幂等，uv run python seed.py）
├── app/
│   ├── main.py          # FastAPI 应用：lifespan 建表、挂载路由、app.frontend 托管前端
│   ├── database.py      # 数据库引擎、会话依赖、SQL 执行日志（写操作参数内联）
│   ├── models.py        # SQLModel 表模型（Team 1:N Hero；Hero M2M Mission，中间表 mission_hero）
│   ├── schemas.py       # 请求/响应模型（含 Paginated* 分页响应）
│   └── routers/         # API 路由（heroes / teams / missions）
├── frontend/            # Vue 3 + Vite 前端源码（模块化结构，见上文）
├── dist/                # 前端构建产物（git 忽略，部署时上传）
├── .fastapicloudignore  # 部署时取消忽略 dist/
└── pyproject.toml       # 依赖 + [tool.fastapi] entrypoint
```
