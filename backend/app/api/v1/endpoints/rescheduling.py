from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional

from backend.app.core.config import settings
from backend.app.schemas.api_schemas import ReschedulePreviewRequest, RescheduleCommitRequest
from src.database.timetable_repository import load_saved_timetable
from src.csp_engine.model import CSPModel
from src.csp_engine.domain_types import SchedulingAssignmentValue
from src.optimization.rescheduling_engine import evaluate_what_if_reschedule
from src.database.rescheduling_repository import (
    apply_reschedule_transaction,
    get_rescheduling_history,
    rollback_reschedule_transaction
)

router = APIRouter()
DB_PATH = str(settings.DB_PATH)

def get_current_assignment_map(model: CSPModel) -> Dict[str, SchedulingAssignmentValue]:
    records = load_saved_timetable(db_path=DB_PATH)
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
    return assignment_map

@router.post("/preview")
def preview_reschedule(payload: ReschedulePreviewRequest):
    model = CSPModel.build_from_db(DB_PATH)
    assignment_map = get_current_assignment_map(model)

    if not assignment_map:
        raise HTTPException(status_code=404, detail="No active timetable assignments available for rescheduling")

    var_id = payload.variable_id
    if var_id not in assignment_map:
        for vid in assignment_map.keys():
            if var_id in vid or vid in var_id:
                var_id = vid
                break

    eval_res = evaluate_what_if_reschedule(
        current_assignment=assignment_map,
        variable_id=var_id,
        new_room_id=payload.new_room_id,
        new_slot_ids=payload.new_slot_ids,
        model=model,
        reason=payload.reason or "Administrator What-If Adjustment"
    )

    return {
        "is_valid": eval_res.is_valid,
        "is_hard_conflict_free": eval_res.is_hard_conflict_free,
        "status": eval_res.status.value if hasattr(eval_res.status, 'value') else str(eval_res.status),
        "original_soft_penalty": eval_res.original_soft_penalty,
        "proposed_soft_penalty": eval_res.proposed_soft_penalty,
        "soft_penalty_delta": eval_res.soft_penalty_delta,
        "hard_violations": [
            {
                "constraint_id": v.constraint_id,
                "constraint_name": v.constraint_name,
                "description": v.explanation,
                "severity": v.severity.value if hasattr(v.severity, 'value') else str(v.severity),
                "entities_involved": v.violating_var_ids
            }
            for v in eval_res.hard_violations
        ],
        "message": eval_res.message
    }

@router.post("/commit")
def commit_reschedule(payload: RescheduleCommitRequest):
    ok, change_id, msg = apply_reschedule_transaction(
        assignment_ids=payload.assignment_ids,
        new_room_id=payload.new_room_id,
        new_slot_ids=payload.new_slot_ids,
        reason=payload.reason or "Admin Manual Adjustment",
        db_path=DB_PATH
    )

    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "status": "committed",
        "change_id": change_id,
        "message": msg
    }

@router.get("/history")
def list_history(limit: int = 50):
    return get_rescheduling_history(limit=limit, db_path=DB_PATH)

@router.post("/rollback/{change_id}")
def rollback_change(change_id: str):
    ok, msg = rollback_reschedule_transaction(change_id=change_id, db_path=DB_PATH)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "rolled_back", "change_id": change_id, "message": msg}
