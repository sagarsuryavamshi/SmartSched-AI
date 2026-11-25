from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from backend.app.core.config import settings
from src.database.timetable_repository import load_saved_timetable
from src.csp_engine.model import CSPModel
from src.csp_engine.domain_types import SchedulingAssignmentValue

router = APIRouter()
DB_PATH = str(settings.DB_PATH)

class ValidationRequest(BaseModel):
    run_id: Optional[str] = None

@router.post("/validate")
def validate_timetable(payload: Optional[ValidationRequest] = None):
    r_id = payload.run_id if payload else None
    records = load_saved_timetable(run_id=r_id, db_path=DB_PATH)
    model = CSPModel.build_from_db(DB_PATH)

    assignment_map: Dict[str, SchedulingAssignmentValue] = {}
    for r in records:
        c_code = r.get("course_code")
        matched_var = None
        for v in model.variables:
            if v.course_code == c_code and v.group_id == r.get("group_id"):
                matched_var = v
                break

        if matched_var:
            if matched_var.var_id in assignment_map:
                current_val = assignment_map[matched_var.var_id]
                new_slots = list(current_val.slot_ids)
                if r.get("slot_id") not in new_slots:
                    new_slots.append(r.get("slot_id"))
                    assignment_map[matched_var.var_id] = SchedulingAssignmentValue(
                        slot_id=current_val.slot_id,
                        room_id=current_val.room_id,
                        day=current_val.day,
                        start_time=current_val.start_time,
                        end_time=current_val.end_time,
                        slot_ids=tuple(new_slots),
                        faculty_id=current_val.faculty_id,
                        group_id=current_val.group_id
                    )
            else:
                assignment_map[matched_var.var_id] = SchedulingAssignmentValue(
                    slot_id=r.get("slot_id"),
                    room_id=r.get("room_id"),
                    day=r.get("day"),
                    start_time=r.get("start_time"),
                    end_time=r.get("end_time"),
                    slot_ids=(r.get("slot_id"),),
                    faculty_id=r.get("faculty_id"),
                    group_id=r.get("group_id")
                )

    report = model.validate_assignments(assignment_map)

    return {
        "status": report.status.value if hasattr(report.status, 'value') else str(report.status),
        "is_valid": report.is_valid,
        "assigned_variables": report.assigned_variables,
        "total_variables": report.total_variables,
        "completion_percentage": round((report.assigned_variables / report.total_variables * 100), 1) if report.total_variables else 0.0,
        "hard_violations_count": len(report.hard_violations),
        "hard_violations": [
            {
                "constraint_id": v.constraint_id,
                "constraint_name": v.constraint_name,
                "description": v.explanation,
                "severity": v.severity.value if hasattr(v.severity, 'value') else str(v.severity),
                "entities_involved": v.violating_var_ids
            }
            for v in report.hard_violations
        ],
        "soft_violations_count": len(report.soft_violations),
        "total_soft_penalty": report.soft_penalty_score,
        "summary_by_constraint": report.summary_by_constraint
    }
