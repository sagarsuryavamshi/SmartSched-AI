"""Persistent User Repository for SmartSched AI (SQLite & PostgreSQL)."""

from typing import Any, Dict, List, Optional, Tuple
from src.database.db_manager import DEFAULT_DB_PATH, ensure_runtime_tables, get_db_connection
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.database.users")

VALID_ROLES = {"admin", "viewer"}


def get_user_by_username(username: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetches a user record by username."""
    ensure_runtime_tables(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, full_name, email, hashed_password, role, disabled FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["disabled"] = bool(d.get("disabled", False))
        return d


def list_users(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Lists all users without exposing password hashes."""
    ensure_runtime_tables(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, full_name, email, role, disabled, created_at FROM users ORDER BY id ASC"
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["disabled"] = bool(d.get("disabled", False))
            if d.get("created_at") is not None:
                d["created_at"] = str(d["created_at"])
            result.append(d)
        return result


def count_admins(db_path: str = DEFAULT_DB_PATH) -> int:
    """Returns the number of active administrator accounts."""
    ensure_runtime_tables(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE role = 'admin'")
        row = cursor.fetchone()
        if isinstance(row, dict):
            return int(row["cnt"])
        return int(row[0])


def create_user(
    username: str,
    full_name: str,
    email: str,
    hashed_password: str,
    role: str = "viewer",
    disabled: bool = False,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Creates a new persistent user account."""
    if role not in VALID_ROLES:
        return False, f"Invalid role '{role}'. Must be one of {sorted(VALID_ROLES)}."
    if not username or len(username.strip()) < 3:
        return False, "Username must be at least 3 characters."

    ensure_runtime_tables(db_path)
    clean_username = username.strip()
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (clean_username,))
            if cursor.fetchone():
                return False, f"User '{clean_username}' already exists."
            cursor.execute(
                """
                INSERT INTO users (username, full_name, email, hashed_password, role, disabled)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (clean_username, full_name.strip(), email.strip(), hashed_password, role, bool(disabled)),
            )
        logger.info("Created user '%s' with role '%s'.", clean_username, role)
        return True, f"User '{clean_username}' created successfully."
    except Exception as exc:
        logger.error("Failed to create user '%s': %s", clean_username, exc)
        return False, str(exc)


def update_user_password(
    username: str,
    new_hashed_password: str,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Updates a user's bcrypt password hash."""
    ensure_runtime_tables(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET hashed_password = ? WHERE username = ?",
            (new_hashed_password, username),
        )
    return True, "Password updated successfully."
