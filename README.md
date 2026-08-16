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

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/heroes?offset=0&limit=10` | 分页查询英雄 |
| POST | `/api/heroes` | 创建英雄 |
| GET | `/api/heroes/{id}` | 查询单个英雄 |
| PATCH | `/api/heroes/{id}` | 部分更新英雄 |
| DELETE | `/api/heroes/{id}` | 删除英雄 |
| GET | `/api/teams` | 查询团队（含成员） |
| GET | `/api/teams/{id}` | 查询单个团队 |
| POST | `/api/teams` | 创建团队 |

## 部署（FastAPI Cloud，前后端分离方案）

按官方文档 [Deploy a Full-Stack App](https://fastapicloud.com/docs/builds-and-deployments/frontend/) 处理：

1. **本地先构建前端**：`cd frontend && pnpm build`（FastAPI Cloud 不会自动运行前端构建）
2. 确认 `dist/` 存在；它被 `.gitignore` 忽略，但 `.fastapicloudignore` 中的 `!dist/` 会确保部署时上传
3. **连接 Neon 数据库**（可选）：在 FastAPI Cloud 的 Integrations 中连接 Neon 账户并选择数据库，平台会自动创建 `DATABASE_URL` 环境变量（以加密 secret 存储），应用启动时读取该变量连接 PostgreSQL；未连接则使用本地 SQLite
4. 部署：`uv run fastapi deploy`

CI 部署时同样需要在 workflow 中先执行 `pnpm install && pnpm build`，再运行 `uv run fastapi deploy`。

## 项目结构

```
├── main.py              # 本地启动入口（uv run python main.py）
├── app/
│   ├── main.py          # FastAPI 应用：lifespan 建表、挂载路由、app.frontend 托管前端
│   ├── database.py      # 数据库引擎与会话依赖
│   ├── models.py        # SQLModel 表模型（Team / Hero 一对多）
│   ├── schemas.py       # 请求/响应模型
│   └── routers/         # API 路由（heroes / teams）
├── frontend/            # Vue 3 + Vite 前端源码
├── dist/                # 前端构建产物（git 忽略，部署时上传）
├── .fastapicloudignore  # 部署时取消忽略 dist/
└── pyproject.toml       # 依赖 + [tool.fastapi] entrypoint
```
