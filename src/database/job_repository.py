"""Persistent Optimization Job Repository (SQLite & PostgreSQL)."""

import json
import time
from typing import Any, Dict, Optional
from src.database.db_manager import DEFAULT_DB_PATH, ensure_runtime_tables, get_db_connection
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.database.jobs")


def create_job(
    job_id: str,
    job_type: str,
    status: str = "queued",
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    """Persists a newly queued optimization job."""
    ensure_runtime_tables(db_path)
    now = time.time()
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO optimization_jobs (job_id, job_type, status, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (job_id, job_type, status, now),
        )


def update_job_status(
    job_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    started_at: Optional[float] = None,
    completed_at: Optional[float] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    """Updates an existing optimization job's status, result payload, or error."""
    ensure_runtime_tables(db_path)
    result_json = json.dumps(result) if result is not None else None
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE optimization_jobs
            SET status = ?,
                started_at = COALESCE(?, started_at),
                completed_at = COALESCE(?, completed_at),
                result_json = COALESCE(?, result_json),
                error = COALESCE(?, error)
            WHERE job_id = ?
            """,
            (status, started_at, completed_at, result_json, error, job_id),
        )


def get_job(job_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a persistent optimization job record by ID."""
    ensure_runtime_tables(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT job_id, job_type, status, created_at, started_at, completed_at, result_json, error
            FROM optimization_jobs
            WHERE job_id = ?
            """,
            (job_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        payload: Dict[str, Any] = {
            "job_id": d["job_id"],
            "type": d["job_type"],
            "status": d["status"],
            "created_at": d["created_at"],
        }
        if d.get("started_at") is not None:
            payload["started_at"] = d["started_at"]
        if d.get("completed_at") is not None:
            payload["completed_at"] = d["completed_at"]
        if d.get("result_json"):
            payload["result"] = json.loads(d["result_json"])
        if d.get("error"):
            payload["error"] = d["error"]
        return payload
