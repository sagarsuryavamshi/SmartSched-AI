from fastapi import APIRouter, HTTPException, Query, Response
from typing import List, Dict, Any, Optional
import io
import csv

from backend.app.core.config import settings
from src.database.timetable_repository import load_saved_timetable

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

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Assignment ID", "Run ID", "Course Code", "Course Title",
        "Faculty Name", "Student Group", "Classroom", "Room Type",
        "Day", "Start Time", "End Time", "Duration (min)"
    ])
    for r in records:
        writer.writerow([
            r.get("id"),
            r.get("assignment_id"),
            r.get("generation_run_id"),
            r.get("course_code"),
            r.get("course_title"),
            r.get("faculty_name"),
            r.get("group_name"),
            r.get("room_name"),
            r.get("room_type"),
            r.get("day"),
            r.get("start_time"),
            r.get("end_time"),
            r.get("duration_minutes")
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=smartsched_timetable_{run_id or 'latest'}.csv"}
    )
