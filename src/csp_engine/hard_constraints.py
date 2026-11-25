"""Hard Constraint definitions and validation functions (H1 through H8)."""

from typing import Any, Dict, List, Optional, Set, Tuple
from src.csp_engine.domain_types import (
    ConstraintViolation,
    SchedulingAssignmentValue,
    SchedulingVariable,
    SessionType,
)


def _slots_overlap(val1: SchedulingAssignmentValue, val2: SchedulingAssignmentValue) -> bool:
    """Returns True if two assignments share any timeslot on the same day."""
    if val1.day != val2.day:
        return False
    # Check intersection of occupied slot_ids
    return bool(set(val1.slot_ids) & set(val2.slot_ids))


def _var_display(var_id: str, variables_map: Dict[str, SchedulingVariable]) -> str:
    """Returns a readable identifier combining course code, session num, and unique variable ID."""
    var = variables_map.get(var_id)
    if var:
        return f"{var.course_code}-S{var.session_num} ({var_id})"
    return var_id


# ============================================================================
# H1: Faculty Overlap Constraint
# ============================================================================
def check_h1_faculty_overlap(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
) -> List[ConstraintViolation]:
    """H1: An instructor cannot be scheduled for two concurrent sessions at the same timeslot.
    Ensures:
      - Variable is never compared with itself (var_id1 != var_id2).
      - Each distinct unordered pair {var_id1, var_id2} is evaluated exactly once.
      - Both unique variable IDs and session numbers are clearly identified.
    """
    violations: List[ConstraintViolation] = []
    assigned_items = list(assignments.items())

    for i in range(len(assigned_items)):
        var_id1, val1 = assigned_items[i]
        for j in range(i + 1, len(assigned_items)):
            var_id2, val2 = assigned_items[j]
            if var_id1 == var_id2:
                continue

            if val1.faculty_id == val2.faculty_id and _slots_overlap(val1, val2):
                overlap = sorted(list(set(val1.slot_ids) & set(val2.slot_ids)))
                v1_label = _var_display(var_id1, variables_map)
                v2_label = _var_display(var_id2, variables_map)
                violations.append(
                    ConstraintViolation(
                        constraint_id="H1",
                        constraint_name="Faculty Double-Booking",
                        violating_var_ids=[var_id1, var_id2],
                        explanation=(
                            f"Faculty '{val1.faculty_id}' is double-booked on {val1.day} "
                            f"at slot(s) {overlap} between {v1_label} and {v2_label}."
                        ),
                        severity="HARD",
                    )
                )
    return violations


# ============================================================================
# H2: Classroom Overlap Constraint
# ============================================================================
def check_h2_classroom_overlap(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
) -> List[ConstraintViolation]:
    """H2: A physical classroom or laboratory cannot host two sessions at the same timeslot.
    Ensures:
      - Variable is never compared with itself (var_id1 != var_id2).
      - Each pair evaluated exactly once.
    """
    violations: List[ConstraintViolation] = []
    assigned_items = list(assignments.items())

    for i in range(len(assigned_items)):
        var_id1, val1 = assigned_items[i]
        for j in range(i + 1, len(assigned_items)):
            var_id2, val2 = assigned_items[j]
            if var_id1 == var_id2:
                continue

            if val1.room_id == val2.room_id and _slots_overlap(val1, val2):
                overlap = sorted(list(set(val1.slot_ids) & set(val2.slot_ids)))
                v1_label = _var_display(var_id1, variables_map)
                v2_label = _var_display(var_id2, variables_map)
                violations.append(
                    ConstraintViolation(
                        constraint_id="H2",
                        constraint_name="Classroom Double-Booking",
                        violating_var_ids=[var_id1, var_id2],
                        explanation=(
                            f"Room '{val1.room_id}' is occupied by multiple sessions on {val1.day} "
                            f"at slot(s) {overlap} between {v1_label} and {v2_label}."
                        ),
                        severity="HARD",
                    )
                )
    return violations


# ============================================================================
# H3: Student Group Overlap Constraint
# ============================================================================
def check_h3_student_group_overlap(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
) -> List[ConstraintViolation]:
    """H3: A student cohort cannot attend two sessions simultaneously.
    Ensures:
      - Variable is never compared with itself.
      - Each pair evaluated exactly once.
    """
    violations: List[ConstraintViolation] = []
    assigned_items = list(assignments.items())

    for i in range(len(assigned_items)):
        var_id1, val1 = assigned_items[i]
        for j in range(i + 1, len(assigned_items)):
            var_id2, val2 = assigned_items[j]
            if var_id1 == var_id2:
                continue

            if val1.group_id == val2.group_id and _slots_overlap(val1, val2):
                overlap = sorted(list(set(val1.slot_ids) & set(val2.slot_ids)))
                v1_label = _var_display(var_id1, variables_map)
                v2_label = _var_display(var_id2, variables_map)
                violations.append(
                    ConstraintViolation(
                        constraint_id="H3",
                        constraint_name="Student Cohort Clash",
                        violating_var_ids=[var_id1, var_id2],
                        explanation=(
                            f"Student group '{val1.group_id}' has conflicting sessions on {val1.day} "
                            f"at slot(s) {overlap} between {v1_label} and {v2_label}."
                        ),
                        severity="HARD",
                    )
                )
    return violations


# ============================================================================
# H4: Room Capacity Constraint
# ============================================================================
def check_h4_room_capacity(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
    room_capacities: Dict[str, int],
    group_sizes: Dict[str, int],
) -> List[ConstraintViolation]:
    """H4: Room capacity must be greater than or equal to the student cohort size."""
    violations: List[ConstraintViolation] = []

    for var_id, val in assignments.items():
        cap = room_capacities.get(val.room_id, 0)
        req_size = group_sizes.get(val.group_id, 0)
        if cap < req_size:
            v_label = _var_display(var_id, variables_map)
            violations.append(
                ConstraintViolation(
                    constraint_id="H4",
                    constraint_name="Insufficient Room Capacity",
                    violating_var_ids=[var_id],
                    explanation=(
                        f"Room '{val.room_id}' has capacity {cap}, which cannot accommodate "
                        f"group '{val.group_id}' of size {req_size} for {v_label}."
                    ),
                    severity="HARD",
                )
            )
    return violations


# ============================================================================
# H5: Faculty Availability Constraint
# ============================================================================
def check_h5_faculty_availability(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
    faculty_unavailability: Dict[str, Set[str]],
    faculty_working_days: Dict[str, Set[str]],
) -> List[ConstraintViolation]:
    """H5: Instructor must be available at the assigned timeslot and day."""
    violations: List[ConstraintViolation] = []

    for var_id, val in assignments.items():
        v_label = _var_display(var_id, variables_map)
        unavail = faculty_unavailability.get(val.faculty_id, set())
        allowed_days = faculty_working_days.get(val.faculty_id, set())

        # Day check
        if allowed_days and val.day not in allowed_days:
            violations.append(
                ConstraintViolation(
                    constraint_id="H5",
                    constraint_name="Faculty Unavailable Day",
                    violating_var_ids=[var_id],
                    explanation=(
                        f"Faculty '{val.faculty_id}' is not available on {val.day} "
                        f"for session {v_label}."
                    ),
                    severity="HARD",
                )
            )

        # Slot check
        conflicting_slots = sorted(list(set(val.slot_ids) & unavail))
        if conflicting_slots:
            violations.append(
                ConstraintViolation(
                    constraint_id="H5",
                    constraint_name="Faculty Unavailable Slot",
                    violating_var_ids=[var_id],
                    explanation=(
                        f"Faculty '{val.faculty_id}' is marked unavailable during slot(s) {conflicting_slots} "
                        f"for session {v_label}."
                    ),
                    severity="HARD",
                )
            )
    return violations


# ============================================================================
# H6: Room Type Matching Constraint
# ============================================================================
def check_h6_room_type(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
    room_types: Dict[str, str],
) -> List[ConstraintViolation]:
    """H6: The assigned room type must match the course requirement (e.g. Lab requires LAB)."""
    violations: List[ConstraintViolation] = []

    for var_id, val in assignments.items():
        var = variables_map[var_id]
        assigned_room_type = room_types.get(val.room_id, "")
        if assigned_room_type != var.required_room_type:
            v_label = _var_display(var_id, variables_map)
            violations.append(
                ConstraintViolation(
                    constraint_id="H6",
                    constraint_name="Incompatible Room Type",
                    violating_var_ids=[var_id],
                    explanation=(
                        f"Session {v_label} requires '{var.required_room_type}' but is assigned "
                        f"to '{val.room_id}' which is of type '{assigned_room_type}'."
                    ),
                    severity="HARD",
                )
            )
    return violations


# ============================================================================
# H7: Laboratory Continuity Constraint
# ============================================================================
def check_h7_lab_continuity(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
    timeslot_details: Dict[str, Dict[str, Any]],
) -> List[ConstraintViolation]:
    """H7: Multi-hour practical/lab sessions must be assigned to continuous timeslots."""
    violations: List[ConstraintViolation] = []

    for var_id, val in assignments.items():
        var = variables_map[var_id]
        if var.session_type == SessionType.LAB and var.duration_hours > 1:
            slots = val.slot_ids
            v_label = _var_display(var_id, variables_map)
            if len(slots) != var.duration_hours:
                violations.append(
                    ConstraintViolation(
                        constraint_id="H7",
                        constraint_name="Insufficient Lab Duration",
                        violating_var_ids=[var_id],
                        explanation=(
                            f"Lab session {v_label} requires {var.duration_hours} consecutive slots, "
                            f"but has {len(slots)} slots assigned."
                        ),
                        severity="HARD",
                    )
                )
                continue

            # Check that each consecutive pair is contiguous in time
            for k in range(len(slots) - 1):
                slot_a = timeslot_details.get(slots[k])
                slot_b = timeslot_details.get(slots[k + 1])
                if not slot_a or not slot_b or slot_a["end_time"] != slot_b["start_time"] or slot_a["day"] != slot_b["day"]:
                    violations.append(
                        ConstraintViolation(
                            constraint_id="H7",
                            constraint_name="Discontinuous Lab Slots",
                            violating_var_ids=[var_id],
                            explanation=(
                                f"Lab session {v_label} has broken continuity between slots "
                                f"'{slots[k]}' ({slot_a.get('end_time') if slot_a else '?'}) and "
                                f"'{slots[k+1]}' ({slot_b.get('start_time') if slot_b else '?'})."
                            ),
                            severity="HARD",
                        )
                    )
                    break
    return violations


# ============================================================================
# H8: Working Hours and Recess Periods Constraint
# ============================================================================
def check_h8_working_hours(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
    timeslot_details: Dict[str, Dict[str, Any]],
) -> List[ConstraintViolation]:
    """H8: Sessions must only be scheduled within standard working timeslots and not during breaks."""
    violations: List[ConstraintViolation] = []

    for var_id, val in assignments.items():
        v_label = _var_display(var_id, variables_map)
        for s_id in val.slot_ids:
            slot = timeslot_details.get(s_id)
            if not slot:
                violations.append(
                    ConstraintViolation(
                        constraint_id="H8",
                        constraint_name="Invalid Timeslot",
                        violating_var_ids=[var_id],
                        explanation=f"Session {v_label} assigned to unrecognized slot '{s_id}'.",
                        severity="HARD",
                    )
                )
            elif slot.get("is_break", 0) == 1:
                violations.append(
                    ConstraintViolation(
                        constraint_id="H8",
                        constraint_name="Scheduled on Institutional Break",
                        violating_var_ids=[var_id],
                        explanation=(
                            f"Session {v_label} is scheduled during institutional "
                            f"break period at slot '{s_id}' ({slot['day']} {slot['start_time']}-{slot['end_time']})."
                        ),
                        severity="HARD",
                    )
                )
    return violations
