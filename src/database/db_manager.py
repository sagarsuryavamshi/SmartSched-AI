"""Database connection, schema migration, and transaction management for SmartSched AI."""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.database")

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "smartsched.db",
)


@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Yields a SQLite connection with row factory and foreign key enforcement enabled."""
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
