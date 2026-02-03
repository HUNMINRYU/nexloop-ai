from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./data/auth.db")


def _ensure_sqlite_dir(database_url: str) -> None:
    if not database_url.startswith("sqlite+aiosqlite:///"):
        return
    raw_path = database_url.split("sqlite+aiosqlite:///", 1)[1]
    if not raw_path:
        return
    path = Path(raw_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionFactory = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


def _migrate_users_columns(sync_conn):  # noqa: ANN001
    """기존 users 테이블에 role/role_id/team_id 컬럼이 없으면 추가 (스키마 이전 대응)."""
    try:
        result = sync_conn.execute(text("PRAGMA table_info(users)"))
        rows = result.fetchall()
    except Exception:
        return
    # SQLite table_info: (cid, name, type, notnull, dflt_value, pk)
    names = [row[1] for row in rows] if rows else []
    if "role" not in names:
        sync_conn.execute(
            text("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'editor' NOT NULL")
        )
    if "role_id" not in names:
        sync_conn.execute(
            text("ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id)")
        )
    if "team_id" not in names:
        sync_conn.execute(
            text("ALTER TABLE users ADD COLUMN team_id INTEGER REFERENCES teams(id)")
        )
    if "phone_number" not in names:
        sync_conn.execute(text("ALTER TABLE users ADD COLUMN phone_number TEXT"))
    if "job_title" not in names:
        sync_conn.execute(text("ALTER TABLE users ADD COLUMN job_title TEXT"))


async def _seed_initial_data(async_conn):
    """기본 역할(role) 데이터를 삽입합니다."""
    from datetime import datetime, timezone, timedelta

    # Role 모델은 admin.py나 models.py에 정의되어 있지만,
    # 여기서는 초기화를 위해 직접 SQL 또는 metadata를 사용합니다.
    # Base.metadata.create_all은 이미 테이블을 생성한 상태입니다.

    # 중복 삽입 방지를 위해 INSERT OR IGNORE(SQLite) 패턴 사용
    roles = [
        ("admin", "System Administrator with full access"),
        ("editor", "Content Editor with create/edit access"),
        ("viewer", "Read-only access to analytics and assets"),
    ]
    for name, desc in roles:
        await async_conn.execute(
            text(
                "INSERT OR IGNORE INTO roles (name, description, created_at) VALUES (:name, :desc, :now)"
            ),
            {
                "name": name,
                "desc": desc,
                "now": datetime.now(timezone(timedelta(hours=9))),
            },
        )


async def init_db() -> None:
    from infrastructure.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_users_columns)
        # 기본 데이터 시딩 (Async로 실행)
        await _seed_initial_data(conn)
