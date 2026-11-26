from fastapi import APIRouter, HTTPException, Query, Response
from typing import List, Dict, Any, Optional
import io
import csv

from backend.app.core.config import settings
from src.database.timetable_repository import load_saved_timetable
from src.utils.export_service import export_timetable_to_csv, export_timetable_to_pdf

router = APIRouter()
DB_PATH = str(settings.DB_PATH)

@router.get("/active")
def get_active_timetable(
    run_id: Optional[str] = None,
    group_id: Optional[str] = None,
    faculty_id: Optional[str] = None,
    room_id: Optional[str] = None,
    day: Optional[str] = None
):
    records = load_saved_timetable(
        run_id=run_id,
        group_id=group_id,
        faculty_id=faculty_id,
        room_id=room_id,
        db_path=DB_PATH
    )

    if day:
        records = [r for r in records if r.get("day", "").lower() == day.lower()]

    return {
        "status": "success",
        "total_sessions": len(records),
        "run_id": records[0]["generation_run_id"] if records else None,
        "sessions": records
    }

@router.get("/export/csv")
def export_timetable_csv(run_id: Optional[str] = None):
    records = load_saved_timetable(run_id=run_id, db_path=DB_PATH)
    if not records:
        raise HTTPException(status_code=404, detail="No timetable sessions available to export")

    csv_content = export_timetable_to_csv(records)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=smartsched_timetable_{run_id or 'latest'}.csv"}
    )

@router.get("/export/pdf")
def export_timetable_pdf(run_id: Optional[str] = None):
    records = load_saved_timetable(run_id=run_id, db_path=DB_PATH)
    if not records:
        raise HTTPException(status_code=404, detail="No timetable sessions available to export")

    pdf_bytes = export_timetable_to_pdf(
        records,
        title=f"SmartSched AI University Timetable (Run: {run_id or 'Latest'})"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=smartsched_timetable_{run_id or 'latest'}.pdf"}
    )
