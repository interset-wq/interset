"""数据库连接与会话管理（SQLModel）。

支持两种数据库，通过环境变量 `DATABASE_URL` 切换：
- 未设置：本地 SQLite（database.db），适合开发
- 已设置：PostgreSQL（如 Neon 云数据库），适合部署
"""

import os
import threading
from collections import deque
from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine


def _resolve_database_url() -> str:
    """解析数据库连接串：优先使用 DATABASE_URL 环境变量，否则回退到本地 SQLite。"""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return "sqlite:///database.db"
    # Neon 提供的连接串形如 postgresql://user:pass@host/db?sslmode=require
    # 显式指定 psycopg v3 驱动（SQLAlchemy 对 postgresql:// 默认用的 psycopg2 已废弃）
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


database_url = _resolve_database_url()

if database_url.startswith("sqlite"):
    # SQLite：FastAPI 的同步路由在线程池中运行，需要允许跨线程使用连接
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL（Neon）：实例会因空闲而挂起（scale-to-zero），
    # pool_pre_ping 在取连接时先探测存活，pool_recycle 定期回收连接，避免 SSL EOF 错误
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
    )


# ---- SQL 执行日志（供前端面板展示）----
# 线程安全：FastAPI 同步路由在线程池中执行，多个线程可能同时写日志
_sql_log_lock = threading.Lock()
_sql_logs: deque[dict] = deque(maxlen=100)


def _on_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """SQLAlchemy 事件：记录每次实际执行的 SQL 语句（含参数），新记录在前。"""
    sql = " ".join(str(statement).split())  # 压缩空白，便于展示
    if not sql.strip():
        return
    try:
        params = repr(tuple(parameters)) if isinstance(parameters, (list, tuple)) else repr(parameters)
    except Exception:
        params = ""
    with _sql_log_lock:
        _sql_logs.appendleft(
            {
                "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "sql": sql,
                "params": params,
            }
        )


event.listen(engine, "before_cursor_execute", _on_before_cursor_execute)


def get_sql_logs(limit: int = 50) -> list[dict]:
    """返回最近执行的 SQL 日志（新→旧），供 API/前端展示。"""
    with _sql_log_lock:
        return list(_sql_logs)[:limit]


def create_db_and_tables() -> None:
    """根据 SQLModel 元数据创建所有表（仅用于演示，生产环境建议用 Alembic 迁移）。"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI 依赖：为每个请求提供一个数据库会话，请求结束后自动关闭。"""
    with Session(engine) as session:
        yield session
