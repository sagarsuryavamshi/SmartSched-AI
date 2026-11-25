from fastapi import APIRouter
from typing import Dict, Any

from backend.app.core.config import settings
from src.database.db_manager import get_db_connection

router = APIRouter()

@router.get("/health")
def get_health() -> Dict[str, Any]:
    db_connected = False
    record_counts = {}
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
            "type": "SQLite",
            "connected": db_connected,
            "path": str(settings.DB_PATH),
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
