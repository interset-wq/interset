"""FastAPI 应用组装：lifespan 建表、挂载路由、前端托管。"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_db_and_tables
from app.routers import heroes, teams


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时创建数据表（演示用；生产环境建议 Alembic 迁移）。"""
    create_db_and_tables()
    yield


app = FastAPI(
    title="interset API",
    description="FastAPI + SQLModel 演示项目：前后端分离，前端由本应用托管",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    """健康检查接口。"""
    return {"status": "ok"}


# 挂载业务路由（统一 /api 前缀）
app.include_router(heroes.router, prefix="/api")
app.include_router(teams.router, prefix="/api")

# 托管前端构建产物（低优先级路由：API 优先匹配，SPA 客户端路由回退到 index.html）
# 仅当 dist 存在时挂载：本地部署由 .fastapicloudignore 的 !dist/ 保证上传，
# 但基于 git 的部署（如 GitHub 集成，云端不运行前端构建）不会包含 dist，
# 此时跳过挂载可避免应用在导入阶段崩溃，API 仍正常可用。
if os.path.isdir("dist"):
    app.frontend("/", directory="dist")
