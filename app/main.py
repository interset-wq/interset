"""FastAPI 应用组装：lifespan 建表、挂载路由、前端托管。"""

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query
from sqlalchemy import inspect

from app.database import create_db_and_tables, engine, get_sql_logs
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


@app.get("/api/sql-logs", tags=["logs"])
def sql_logs(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[dict]:
    """返回最近执行的 SQL 日志（新→旧），供前端日志面板展示。"""
    return get_sql_logs(limit)


@app.get("/api/tables", tags=["schema"])
def tables() -> list[dict]:
    """列出所有表的表结构（类似 psql \\d：表名、字段名、数据类型、可空、主键）。"""
    inspector = inspect(engine)
    rows: list[dict] = []
    for table_name in inspector.get_table_names():
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = set(pk_constraint.get("constrained_columns") or [])
        for col in inspector.get_columns(table_name):
            rows.append(
                {
                    "table": table_name,
                    "column": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "primary_key": col["name"] in pk_columns,
                }
            )
    return rows


# 挂载业务路由（统一 /api 前缀）
app.include_router(heroes.router, prefix="/api")
app.include_router(teams.router, prefix="/api")

# 托管前端构建产物（低优先级路由：API 优先匹配，SPA 客户端路由回退到 index.html）
# 按 FastAPI Cloud 前端部署文档：部署前须本地先构建前端（pnpm build），
# dist/ 由 .fastapicloudignore 的 !dist/ 随部署上传。
app.frontend("/", directory="dist")
