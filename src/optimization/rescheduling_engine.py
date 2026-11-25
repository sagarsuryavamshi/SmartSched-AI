"""What-If Rescheduling Engine.

Allows administrators to propose alternative timeslots and classrooms for existing sessions,
evaluates candidate schedules against the full H1-H8 and S1-S4 constraint suite,
computes penalty deltas, and prevents invalid or conflicting timetable modifications.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.csp_engine.domain_types import (
    ConstraintViolation,
    SchedulingAssignmentValue,
    SchedulingVariable,
    TimetableStatus,
    ValidationReport,
)
from src.csp_engine.model import CSPModel
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.optimization.rescheduling")


@dataclass
class WhatIfProposal:
    """Represents a proposed rescheduling change for a single variable."""
    variable_id: str
    new_room_id: str
    new_day: str
    new_start_time: str
    new_end_time: str
    new_slot_ids: List[str]
    reason: str = "Administrator What-If Adjustment"


@dataclass
class WhatIfEvaluationResult:
    """Detailed evaluation result comparing an original timetable against a proposed change."""
    is_valid: bool
    is_hard_conflict_free: bool
    original_soft_penalty: float
    proposed_soft_penalty: float
    soft_penalty_delta: float  # Negative is improvement, positive is deterioration
    status: TimetableStatus
    hard_violations: List[ConstraintViolation] = field(default_factory=list)
    soft_violations: List[ConstraintViolation] = field(default_factory=list)
    summary_by_constraint: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    old_assignment: Optional[SchedulingAssignmentValue] = None
    new_assignment: Optional[SchedulingAssignmentValue] = None
    validation_report: Optional[ValidationReport] = None
    message: str = ""


def evaluate_what_if_reschedule(
    current_assignment: Dict[str, SchedulingAssignmentValue],
    variable_id: str,
    new_room_id: str,
    new_slot_ids: List[str],
    model: CSPModel,
    reason: str = "What-If Adjustment",
) -> WhatIfEvaluationResult:
    """Evaluates a proposed assignment change against all CSP hard and soft constraints.

    Does NOT modify the database or mutate the current assignment in-place.
    """
    if variable_id not in current_assignment:
        return WhatIfEvaluationResult(
            is_valid=False,
            is_hard_conflict_free=False,
            original_soft_penalty=0.0,
            proposed_soft_penalty=0.0,
            soft_penalty_delta=0.0,
            status=TimetableStatus.INVALID,
            message=f"Variable '{variable_id}' is not in the current schedule assignment.",
        )

    var = model.variables_map.get(variable_id)
    if not var:
        return WhatIfEvaluationResult(
            is_valid=False,
            is_hard_conflict_free=False,
            original_soft_penalty=0.0,
            proposed_soft_penalty=0.0,
            soft_penalty_delta=0.0,
            status=TimetableStatus.INVALID,
            message=f"Variable '{variable_id}' is not registered in the CSP Model.",
        )

    old_val = current_assignment[variable_id]

    # Validate that new slots exist in model timeslot details
    if not new_slot_ids:
        return WhatIfEvaluationResult(
            is_valid=False,
            is_hard_conflict_free=False,
            original_soft_penalty=0.0,
            proposed_soft_penalty=0.0,
            soft_penalty_delta=0.0,
            status=TimetableStatus.INVALID,
            message="No target timeslots specified for proposal.",
        )

    first_slot_meta = model.timeslot_details.get(new_slot_ids[0])
    last_slot_meta = model.timeslot_details.get(new_slot_ids[-1])
    if not first_slot_meta or not last_slot_meta:
        return WhatIfEvaluationResult(
            is_valid=False,
            is_hard_conflict_free=False,
            original_soft_penalty=0.0,
            proposed_soft_penalty=0.0,
            soft_penalty_delta=0.0,
            status=TimetableStatus.INVALID,
            message=f"Invalid timeslot IDs: {new_slot_ids}",
        )

    new_day = first_slot_meta["day"]
    new_start_time = first_slot_meta["start_time"]
    new_end_time = last_slot_meta["end_time"]

    # Construct the candidate proposed assignment value
    new_val = SchedulingAssignmentValue(
        slot_id=new_slot_ids[0],
        room_id=new_room_id,
        day=new_day,
        start_time=new_start_time,
        end_time=new_end_time,
        slot_ids=list(new_slot_ids),
        faculty_id=var.faculty_id,
        group_id=var.group_id,
    )

    # 1. Evaluate baseline original schedule
    original_report = model.validate_assignments(current_assignment)
    orig_soft = original_report.soft_penalty_score

    # 2. Construct candidate hypothetical timetable
    candidate_assignment = dict(current_assignment)
    candidate_assignment[variable_id] = new_val

    # 3. Evaluate candidate timetable against full H1-H8 and S1-S4
    candidate_report = model.validate_assignments(candidate_assignment)
    prop_soft = candidate_report.soft_penalty_score
    delta_soft = prop_soft - orig_soft

    is_hard_ok = len(candidate_report.hard_violations) == 0
    is_valid = is_hard_ok and candidate_report.is_valid

    if is_valid:
        if delta_soft < 0:
            msg = f"Proposal is FEASIBLE and IMPROVES soft preferences by {abs(delta_soft):.1f} points."
        elif delta_soft == 0:
            msg = "Proposal is FEASIBLE with identical soft penalty score."
        else:
            msg = f"Proposal is FEASIBLE but increases soft penalty by {delta_soft:.1f} points."
    else:
        num_v = len(candidate_report.hard_violations)
        conflict_types = {v.constraint_id for v in candidate_report.hard_violations}
        msg = f"Proposal REJECTED: {num_v} hard conflict(s) detected ({', '.join(sorted(conflict_types))})."

    return WhatIfEvaluationResult(
        is_valid=is_valid,
        is_hard_conflict_free=is_hard_ok,
        original_soft_penalty=orig_soft,
        proposed_soft_penalty=prop_soft,
        soft_penalty_delta=delta_soft,
        status=candidate_report.status,
        hard_violations=candidate_report.hard_violations,
        soft_violations=candidate_report.soft_violations,
        summary_by_constraint=candidate_report.summary_by_constraint,
        old_assignment=old_val,
        new_assignment=new_val,
        validation_report=candidate_report,
        message=msg,
    )
