"""
Database Connection Manager for AI Control Center.
Provides clean abstraction over SQLite with parameterized queries,
thread safety, and support for future migration to PostgreSQL / Supabase.
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Any, List, Tuple, Dict, Optional


# Resolve database path relative to repository root or via environment variable
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "ai_control_center.db"
DB_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))


def get_db_path() -> Path:
    """Return the resolved database file path and ensure directory exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for obtaining a thread-safe SQLite connection."""
    db_file = get_db_path()
    conn = sqlite3.connect(str(db_file), timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    """Initialize database schema from schema.sql."""
    schema_file = Path(__file__).resolve().parent / "schema.sql"
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_file}")

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db_connection() as conn:
        conn.executescript(schema_sql)


def execute_query(query: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
    """Execute a parameterized SELECT query and return rows."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_write(query: str, params: Tuple[Any, ...] = ()) -> int:
    """Execute a parameterized INSERT/UPDATE/DELETE query and return affected rows."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount
