"""ESP APM PostgreSQL database connection manager (Server 184).

STRICT SAFETY CONTRACT:
This module connects exclusively in READ-ONLY mode.
Any attempt to execute INSERT, UPDATE, DELETE, or DDL will be physically rejected by PostgreSQL.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager, suppress
from typing import Generator
import psycopg2
from psycopg2 import pool
from psycopg2.extensions import cursor as PgCursor

from app.core.config import settings

logger = logging.getLogger("agent.esp_db")

_pool: pool.ThreadedConnectionPool | None = None


def get_esp_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        logger.info(f"Initializing read-only connection pool to ESP APM DB: {settings.ESP_APM_DB_URL}")
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.ESP_APM_DB_URL,
            connect_timeout=5,
        )
    return _pool


@contextmanager
def get_esp_cursor() -> Generator[PgCursor, None, None]:
    """Yields a database cursor with strict read-only session enforcement."""
    p = get_esp_pool()
    conn = p.getconn()
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            yield cur
        p.putconn(conn)
    except Exception:
        with suppress(Exception):
            p.putconn(conn, close=True)
        raise


def check_esp_db_health() -> bool:
    try:
        with get_esp_cursor() as cur:
            cur.execute("SELECT 1;")
            row = cur.fetchone()
            return bool(row and row[0] == 1)
    except Exception as e:
        logger.error(f"ESP APM DB health check failed: {e}")
        return False
