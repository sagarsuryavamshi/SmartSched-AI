import psycopg2
from fastapi import APIRouter
from typing import Dict, Any

from backend.app.core.config import settings
from src.database.db_manager import get_db_connection

router = APIRouter()

@router.get("/health")
def get_health() -> Dict[str, Any]:
    db_connected = False
    db_type = "SQLite"
    record_counts = {}
    db_target = str(settings.DB_PATH)

    # 1. If DATABASE_URL is set to a PostgreSQL connection (e.g. Neon or standard Postgres), test it
    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql"):
        db_type = "PostgreSQL"
        db_target = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "configured"
        try:
            conn = psycopg2.connect(settings.DATABASE_URL)
            cursor = conn.cursor()
            for table in ["classrooms", "faculty", "student_groups", "courses", "timeslots", "scheduled_assignments"]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    record_counts[table] = cursor.fetchone()[0]
                except Exception:
                    record_counts[table] = 0
            cursor.close()
            conn.close()
            db_connected = True
        except Exception as e:
            db_connected = False
            record_counts["error"] = str(e)

    # 2. Otherwise fall back to local SQLite database check
    if not db_connected and db_type == "SQLite":
        try:
            with get_db_connection(str(settings.DB_PATH)) as conn:
                cursor = conn.cursor()
                for table in ["classrooms", "faculty", "student_groups", "courses", "timeslots", "scheduled_assignments"]:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        record_counts[table] = cursor.fetchone()[0]
                    except Exception:
                        record_counts[table] = 0
                db_connected = True
        except Exception as e:
            db_connected = False
            record_counts["error"] = str(e)

    return {
        "status": "healthy" if db_connected else "degraded",
        "database": {
            "type": db_type,
            "connected": db_connected,
            "target": db_target,
            "record_counts": record_counts
        },
        "engines": {
            "csp_solver": "ready",
            "genetic_algorithm": "ready",
            "constraint_validator": "ready",
            "rescheduling_engine": "ready"
        },
        "version": settings.VERSION
    }
