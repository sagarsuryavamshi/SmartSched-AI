"""Soft Constraint definitions and objective penalty scoring functions (S1 through S4)."""

from typing import Any, Dict, List, Optional, Set, Tuple
from src.csp_engine.domain_types import (
    ConstraintViolation,
    SchedulingAssignmentValue,
    SchedulingVariable,
    SessionType,
)


def _time_str_to_minutes(time_str: str) -> int:
    """Converts 'HH:MM' string to minutes from midnight."""
    try:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0


# ============================================================================
# S1: Faculty Preferred Timeslots
# ============================================================================
def score_s1_faculty_preferences(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
    faculty_preferred_slots: Optional[Dict[str, Set[str]]] = None,
) -> Tuple[float, List[ConstraintViolation]]:
    """S1: Penalizes sessions scheduled outside instructor preferred time intervals (or non-morning slots).

    Baseline: If preferred slots are not explicitly set, 09:00 - 13:00 morning slots are considered preferred,
    and afternoon slots (>14:00) incur a soft penalty of 5.0 points per session.
    """
    violations: List[ConstraintViolation] = []
    penalty = 0.0

    for var_id, val in assignments.items():
        var = variables_map[var_id]
        preferred = (faculty_preferred_slots or {}).get(val.faculty_id)

        if preferred is not None:
            # Explicit preferred set check
            non_pref = set(val.slot_ids) - preferred
            if non_pref:
                p = 10.0 * len(non_pref)
                penalty += p
                violations.append(
                    ConstraintViolation(
                        constraint_id="S1",
                        constraint_name="Non-Preferred Faculty Timeslot",
                        violating_var_ids=[var_id],
                        explanation=f"Session {var.course_code} for {val.faculty_id} scheduled in non-preferred slot(s) {non_pref}.",
                        severity="SOFT",
                    )
                )
        else:
            # Default preference heuristic: morning vs late afternoon
            start_min = _time_str_to_minutes(val.start_time)
            if start_min >= 14 * 60:  # 2 PM or later
                penalty += 5.0
                violations.append(
                    ConstraintViolation(
                        constraint_id="S1",
                        constraint_name="Afternoon Slot Allocation",
                        violating_var_ids=[var_id],
                        explanation=f"Session {var.course_code} for {val.faculty_id} assigned to afternoon slot ({val.start_time}).",
                        severity="SOFT",
                    )
                )

    return penalty, violations


# ============================================================================
# S2: Minimizing Faculty Idle Gaps
# ============================================================================
def score_s2_faculty_idle_gaps(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
) -> Tuple[float, List[ConstraintViolation]]:
    """S2: Penalizes long idle window gaps (> 60 minutes) between sessions for an instructor on the same day."""
    violations: List[ConstraintViolation] = []
    penalty = 0.0

    # Group assignments by (faculty_id, day)
    fac_day_sessions: Dict[Tuple[str, str], List[Tuple[str, SchedulingAssignmentValue]]] = {}
    for var_id, val in assignments.items():
        fac_day_sessions.setdefault((val.faculty_id, val.day), []).append((var_id, val))

    for (fac_id, day), sessions in fac_day_sessions.items():
        if len(sessions) < 2:
            continue
        # Sort chronologically by start_time
        sorted_s = sorted(sessions, key=lambda x: _time_str_to_minutes(x[1].start_time))

        for k in range(len(sorted_s) - 1):
            prev_end = _time_str_to_minutes(sorted_s[k][1].end_time)
            next_start = _time_str_to_minutes(sorted_s[k + 1][1].start_time)
            gap = next_start - prev_end
            if gap > 60:  # Greater than 1 hour gap
                p = float(gap // 30) * 8.0  # 8 points per 30m idle gap
                penalty += p
                violations.append(
                    ConstraintViolation(
                        constraint_id="S2",
                        constraint_name="Faculty Idle Schedule Gap",
                        violating_var_ids=[sorted_s[k][0], sorted_s[k + 1][0]],
                        explanation=(
                            f"Faculty '{fac_id}' has an idle gap of {gap} mins on {day} "
                            f"between {variables_map[sorted_s[k][0]].course_code} and {variables_map[sorted_s[k+1][0]].course_code}."
                        ),
                        severity="SOFT",
                    )
                )

    return penalty, violations


# ============================================================================
# S3: Avoiding Consecutive Heavy Theory Sessions
# ============================================================================
def score_s3_consecutive_theory_sessions(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
) -> Tuple[float, List[ConstraintViolation]]:
    """S3: Penalizes more than 2 back-to-back heavy theory lecture hours for the same student group."""
    violations: List[ConstraintViolation] = []
    penalty = 0.0

    # Group by (group_id, day)
    group_day_sessions: Dict[Tuple[str, str], List[Tuple[str, SchedulingAssignmentValue]]] = {}
    for var_id, val in assignments.items():
        group_day_sessions.setdefault((val.group_id, val.day), []).append((var_id, val))

    for (grp_id, day), sessions in group_day_sessions.items():
        if len(sessions) < 3:
            continue
        sorted_s = sorted(sessions, key=lambda x: _time_str_to_minutes(x[1].start_time))

        consecutive_theory_run = 0
        run_vars: List[str] = []

        for i in range(len(sorted_s)):
            var_id, val = sorted_s[i]
            var = variables_map[var_id]
            if var.session_type == SessionType.THEORY:
                if consecutive_theory_run == 0:
                    consecutive_theory_run = 1
                    run_vars = [var_id]
                else:
                    prev_end = _time_str_to_minutes(sorted_s[i - 1][1].end_time)
                    curr_start = _time_str_to_minutes(val.start_time)
                    if prev_end == curr_start:
                        consecutive_theory_run += 1
                        run_vars.append(var_id)
                        if consecutive_theory_run >= 3:
                            p = 15.0 * (consecutive_theory_run - 2)
                            penalty += p
                            violations.append(
                                ConstraintViolation(
                                    constraint_id="S3",
                                    constraint_name="Fatiguing Consecutive Theory Lectures",
                                    violating_var_ids=list(run_vars),
                                    explanation=(
                                        f"Student group '{grp_id}' has {consecutive_theory_run} consecutive "
                                        f"theory hours on {day} without a mental break."
                                    ),
                                    severity="SOFT",
                                )
                            )
                    else:
                        consecutive_theory_run = 1
                        run_vars = [var_id]
            else:
                consecutive_theory_run = 0
                run_vars = []

    return penalty, violations


# ============================================================================
# S4: Balanced Daily Workload Distribution
# ============================================================================
def score_s4_balanced_daily_workload(
    assignments: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
) -> Tuple[float, List[ConstraintViolation]]:
    """S4: Penalizes unbalanced student schedules (e.g. days with > 4 hours or days with only 1 hour)."""
    violations: List[ConstraintViolation] = []
    penalty = 0.0

    # Group daily hours by (group_id, day)
    group_day_hours: Dict[Tuple[str, str], int] = {}
    group_day_vars: Dict[Tuple[str, str], List[str]] = {}

    for var_id, val in assignments.items():
        var = variables_map[var_id]
        key = (val.group_id, val.day)
        group_day_hours[key] = group_day_hours.get(key, 0) + var.duration_hours
        group_day_vars.setdefault(key, []).append(var_id)

    for (grp_id, day), total_hrs in group_day_hours.items():
        if total_hrs > 4:
            overload = total_hrs - 4
            p = float(overload) * 12.0
            penalty += p
            violations.append(
                ConstraintViolation(
                    constraint_id="S4",
                    constraint_name="Daily Student Overload",
                    violating_var_ids=group_day_vars.get((grp_id, day), []),
                    explanation=f"Group '{grp_id}' is overloaded with {total_hrs} scheduled hours on {day} (>4h limit).",
                    severity="SOFT",
                )
            )
        elif total_hrs == 1:
            penalty += 6.0
            violations.append(
                ConstraintViolation(
                    constraint_id="S4",
                    constraint_name="Under-utilized Academic Day",
                    violating_var_ids=group_day_vars.get((grp_id, day), []),
                    explanation=f"Group '{grp_id}' has only 1 scheduled lecture on {day}.",
                    severity="SOFT",
                )
            )

    return penalty, violations
