"""Database connection, schema migration, and transaction management for SmartSched AI."""

import os
import re
import sqlite3
from contextlib import contextmanager
from typing import Any, Generator, Optional
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.database")

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "smartsched.db",
)


def is_postgres_active(db_path: str = DEFAULT_DB_PATH) -> bool:
    """Returns True when DATABASE_URL is PostgreSQL and caller targets the default production DB."""
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        return False
    return os.path.abspath(db_path) == os.path.abspath(DEFAULT_DB_PATH)


def _translate_sql_for_pg(sql: str) -> str:
    """Translates SQLite '?' parameter placeholders to PostgreSQL '%s' outside string literals."""
    out = []
    in_single = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        if ch == "'" and (i == 0 or sql[i - 1] != "\\"):
            in_single = not in_single
            out.append(ch)
        elif ch == "?" and not in_single:
            out.append("%s")
        else:
            out.append(ch)
        i += 1
    translated = "".join(out)
    # Handle SQLite INSERT OR REPLACE INTO scheduled_assignments when saving
    if "INSERT OR REPLACE INTO scheduled_assignments" in translated:
        translated = translated.replace("INSERT OR REPLACE INTO scheduled_assignments", "INSERT INTO scheduled_assignments")
    return translated


class _PgCursorWrapper:
    """Wraps a psycopg2 RealDictCursor so SQLite-style '?' queries work transparently."""

    def __init__(self, cursor: Any):
        self._cursor = cursor

    def execute(self, sql: str, params: Optional[Any] = None) -> Any:
        pg_sql = _translate_sql_for_pg(sql)
        if params is not None:
            return self._cursor.execute(pg_sql, params)
        return self._cursor.execute(pg_sql)

    def executemany(self, sql: str, seq_of_params: Any) -> Any:
        pg_sql = _translate_sql_for_pg(sql)
        return self._cursor.executemany(pg_sql, seq_of_params)

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> Any:
        return self._cursor.fetchall()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)


class _PgConnectionWrapper:
    """Wraps a psycopg2 connection so it supports SQLite-style cursor() and pandas read_sql_query."""

    def __init__(self, conn: Any):
        self._conn = conn

    def cursor(self) -> _PgCursorWrapper:
        from psycopg2.extras import RealDictCursor
        return _PgCursorWrapper(self._conn.cursor(cursor_factory=RealDictCursor))

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)


@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> Generator[Any, None, None]:
    """Yields a PostgreSQL connection (when DATABASE_URL is configured for default DB) or SQLite connection."""
    if is_postgres_active(db_path):
        import psycopg2
        database_url = os.getenv("DATABASE_URL", "")
        raw_conn = psycopg2.connect(database_url)
        conn = _PgConnectionWrapper(raw_conn)
        try:
            yield conn
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.error("PostgreSQL transaction rolled back due to error: %s", exc)
            raise
        finally:
            conn.close()
        return

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints at SQLite connection level
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("Database transaction rolled back due to error: %s", exc)
        raise
    finally:
        conn.close()


def _ensure_column_exists(conn: sqlite3.Connection, table_name: str, column_name: str, column_def: str) -> None:
    """Checks if a column exists in a table, and adds it if missing."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    existing_columns = [row["name"] for row in cursor.fetchall()]
    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def};")
        logger.info("Migrated table '%s': added column '%s %s'", table_name, column_name, column_def)


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes the database schema and performs non-destructive migrations."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS classrooms (
        room_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        room_type TEXT NOT NULL DEFAULT 'LECTURE_HALL',
        features TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS faculty (
        faculty_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        department TEXT DEFAULT 'Computer Science',
        max_weekly_hours INTEGER DEFAULT 18,
        available_days TEXT DEFAULT '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]',
        qualified_courses TEXT DEFAULT '[]',
        unavailable_slots TEXT DEFAULT '[]'
    );

    CREATE TABLE IF NOT EXISTS student_groups (
        group_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT DEFAULT 'Computer Science',
        size INTEGER NOT NULL,
        program TEXT NOT NULL,
        semester INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS timeslots (
        slot_id TEXT PRIMARY KEY,
        day TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        duration_minutes INTEGER DEFAULT 60,
        is_break INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS courses (
        course_id TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        title TEXT NOT NULL,
        weekly_hours INTEGER NOT NULL,
        required_room_type TEXT DEFAULT 'LECTURE_HALL',
        category TEXT DEFAULT 'Theory',
        is_lab INTEGER DEFAULT 0,
        assigned_faculty_id TEXT,
        target_group_id TEXT,
        FOREIGN KEY (assigned_faculty_id) REFERENCES faculty (faculty_id) ON DELETE RESTRICT,
        FOREIGN KEY (target_group_id) REFERENCES student_groups (group_id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS scheduled_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assignment_id TEXT UNIQUE,
        course_id TEXT NOT NULL,
        group_id TEXT NOT NULL,
        faculty_id TEXT NOT NULL,
        room_id TEXT NOT NULL,
        slot_id TEXT NOT NULL,
        generation_run_id TEXT,
        FOREIGN KEY (course_id) REFERENCES courses (course_id) ON DELETE RESTRICT,
        FOREIGN KEY (group_id) REFERENCES student_groups (group_id) ON DELETE RESTRICT,
        FOREIGN KEY (faculty_id) REFERENCES faculty (faculty_id) ON DELETE RESTRICT,
        FOREIGN KEY (room_id) REFERENCES classrooms (room_id) ON DELETE RESTRICT,
        FOREIGN KEY (slot_id) REFERENCES timeslots (slot_id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS rescheduling_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        change_id TEXT UNIQUE NOT NULL,
        session_id TEXT NOT NULL,
        course_code TEXT NOT NULL,
        group_id TEXT NOT NULL,
        faculty_id TEXT NOT NULL,
        old_room_id TEXT NOT NULL,
        old_slot_id TEXT NOT NULL,
        old_day TEXT NOT NULL,
        old_start_time TEXT NOT NULL,
        new_room_id TEXT NOT NULL,
        new_slot_id TEXT NOT NULL,
        new_day TEXT NOT NULL,
        new_start_time TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'COMMITTED',
        reason TEXT
    );
    """
    with get_db_connection(db_path) as conn:
        conn.executescript(schema_sql)

        # Migration safeguards for existing databases from Phase 1
        _ensure_column_exists(conn, "faculty", "department", "TEXT DEFAULT 'Computer Science'")
        _ensure_column_exists(conn, "faculty", "available_days", "TEXT DEFAULT '[\"Monday\", \"Tuesday\", \"Wednesday\", \"Thursday\", \"Friday\"]'")
        _ensure_column_exists(conn, "student_groups", "department", "TEXT DEFAULT 'Computer Science'")
        _ensure_column_exists(conn, "courses", "category", "TEXT DEFAULT 'Theory'")
        _ensure_column_exists(conn, "timeslots", "duration_minutes", "INTEGER DEFAULT 60")
        _ensure_column_exists(conn, "timeslots", "is_break", "INTEGER DEFAULT 0")

    logger.info("Database schema initialized and migrated successfully at %s", db_path)
