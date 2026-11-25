from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional

from backend.app.core.config import settings
from src.database.timetable_repository import load_saved_timetable
from src.evaluation.metrics import calculate_timetable_analytics
from src.csp_engine.model import CSPModel

router = APIRouter()
DB_PATH = str(settings.DB_PATH)

@router.get("/summary")
def get_analytics_summary(run_id: Optional[str] = None):
    records = load_saved_timetable(run_id=run_id, db_path=DB_PATH)
    model = CSPModel.build_from_db(DB_PATH)

    analytics = calculate_timetable_analytics(records, model=model, db_path=DB_PATH)
    return {
        "status": "success",
        "run_id": run_id or (records[0]["generation_run_id"] if records else None),
        "total_sessions": len(records),
        "analytics": analytics
    }

@router.get("/faculty-workload")
def get_faculty_workload(run_id: Optional[str] = None):
    records = load_saved_timetable(run_id=run_id, db_path=DB_PATH)
    model = CSPModel.build_from_db(DB_PATH)
    analytics = calculate_timetable_analytics(records, model=model, db_path=DB_PATH)
    return analytics.get("faculty_analytics", {})

@router.get("/room-utilization")
def get_room_utilization(run_id: Optional[str] = None):
    records = load_saved_timetable(run_id=run_id, db_path=DB_PATH)
    model = CSPModel.build_from_db(DB_PATH)
    analytics = calculate_timetable_analytics(records, model=model, db_path=DB_PATH)
    return analytics.get("room_analytics", {})

@router.get("/soft-objectives")
def get_soft_objectives(run_id: Optional[str] = None):
    records = load_saved_timetable(run_id=run_id, db_path=DB_PATH)
    model = CSPModel.build_from_db(DB_PATH)
    analytics = calculate_timetable_analytics(records, model=model, db_path=DB_PATH)
    return analytics.get("soft_penalties", {})
