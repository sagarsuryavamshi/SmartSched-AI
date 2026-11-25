"""CSP Variable and Domain Generator from SQLite Academic Database."""

import json
from typing import Any, Dict, List, Optional, Set, Tuple
from src.csp_engine.domain_types import (
    SchedulingAssignmentValue,
    SchedulingVariable,
    SessionType,
)
from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.csp_engine.generator")


def generate_variables_from_db(db_path: str = DEFAULT_DB_PATH) -> List[SchedulingVariable]:
    """Extracts academic courses from SQLite and decomposes them into atomic scheduling variables.

    Decomposition rules:
      - If course is_lab is True or category is 'Practical':
        Creates laboratory sessions of 2 hours duration (or weekly_hours if < 2).
      - If course is Theory:
        Creates weekly_hours individual 1-hour lecture sessions.
    """
    variables: List[SchedulingVariable] = []

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT course_id, code, title, weekly_hours, required_room_type,
                   category, is_lab, assigned_faculty_id, target_group_id
            FROM courses
            ORDER BY code ASC
        """)
        courses = cursor.fetchall()

        for c in courses:
            c_id = c["course_id"]
            code = c["code"]
            weekly_hrs = int(c["weekly_hours"])
            room_type = c["required_room_type"] or "LECTURE_HALL"
            is_lab = bool(c["is_lab"] or c["category"] == "Practical")
            faculty_id = c["assigned_faculty_id"] or "FAC_UNASSIGNED"
            group_id = c["target_group_id"] or "GRP_UNASSIGNED"

            if is_lab:
                # Group lab hours into consecutive 2-hour lab blocks (or remainder)
                session_len = 2
                num_sessions = max(1, weekly_hrs // session_len)
                for s_idx in range(1, num_sessions + 1):
                    var_id = f"VAR_{code}_LAB_S{s_idx}"
                    variables.append(
                        SchedulingVariable(
                            var_id=var_id,
                            course_id=c_id,
                            course_code=code,
                            session_num=s_idx,
                            total_sessions=num_sessions,
                            session_type=SessionType.LAB,
                            duration_hours=session_len,
                            faculty_id=faculty_id,
                            group_id=group_id,
                            required_room_type=room_type if room_type != "LECTURE_HALL" else "LAB",
                        )
                    )
            else:
                # Theory courses: 1 hour per lecture session
                for s_idx in range(1, weekly_hrs + 1):
                    var_id = f"VAR_{code}_LEC_S{s_idx}"
                    variables.append(
                        SchedulingVariable(
                            var_id=var_id,
                            course_id=c_id,
                            course_code=code,
                            session_num=s_idx,
                            total_sessions=weekly_hrs,
                            session_type=SessionType.THEORY,
                            duration_hours=1,
                            faculty_id=faculty_id,
                            group_id=group_id,
                            required_room_type=room_type,
                        )
                    )

    logger.info("Generated %d scheduling variables from database.", len(variables))
    return variables


def _get_consecutive_slots(
    slots_by_day: Dict[str, List[Dict[str, Any]]],
    day: str,
    start_idx: int,
    num_slots: int,
) -> Optional[List[Dict[str, Any]]]:
    """Validates and retrieves consecutive timeslots without intervening breaks."""
    day_slots = slots_by_day.get(day, [])
    if start_idx + num_slots > len(day_slots):
        return None

    candidate_sequence = day_slots[start_idx : start_idx + num_slots]

    # Verify none of the slots in candidate sequence is a designated break period
    for s in candidate_sequence:
        if s.get("is_break", 0) == 1:
            return None

    # Check temporal continuity: end_time of slot[i] == start_time of slot[i+1]
    for i in range(len(candidate_sequence) - 1):
        if candidate_sequence[i]["end_time"] != candidate_sequence[i + 1]["start_time"]:
            return None

    return candidate_sequence


def generate_domains_from_db(
    variables: List[SchedulingVariable],
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, List[SchedulingAssignmentValue]]:
    """Generates initial domains for each variable, pre-filtering impossible assignments.

    Filters applied:
      1. Working hours & break periods (H8 & institutional recesses)
      2. Consecutive slot availability for multi-hour labs (H7)
      3. Faculty unavailable timeslots and available days (H5)
      4. Room capacity >= student cohort size (H4)
      5. Required room type matching (H6)
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Fetch classrooms
        cursor.execute("SELECT room_id, name, capacity, room_type FROM classrooms")
        classrooms = {r["room_id"]: dict(r) for r in cursor.fetchall()}

        # 2. Fetch student groups (for capacity check)
        cursor.execute("SELECT group_id, size FROM student_groups")
        group_sizes = {g["group_id"]: g["size"] for g in cursor.fetchall()}

        # 3. Fetch faculty (for availability check)
        cursor.execute("SELECT faculty_id, available_days, unavailable_slots FROM faculty")
        faculty_meta: Dict[str, Dict[str, Any]] = {}
        for row in cursor.fetchall():
            f_id = row["faculty_id"]
            avail_days = set(json.loads(row["available_days"] or "[]"))
            unavail_slots = set(json.loads(row["unavailable_slots"] or "[]"))
            faculty_meta[f_id] = {
                "available_days": avail_days,
                "unavailable_slots": unavail_slots,
            }

        # 4. Fetch timeslots ordered chronologically by day & start_time
        cursor.execute("""
            SELECT slot_id, day, start_time, end_time, duration_minutes, is_break
            FROM timeslots
            ORDER BY
                CASE day
                    WHEN 'Monday' THEN 1
                    WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3
                    WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5
                    WHEN 'Saturday' THEN 6
                    ELSE 7
                END,
                start_time ASC
        """)
        all_slots = [dict(s) for s in cursor.fetchall()]

    # Group timeslots by day
    slots_by_day: Dict[str, List[Dict[str, Any]]] = {}
    for s in all_slots:
        day = s["day"]
        slots_by_day.setdefault(day, []).append(s)

    domains: Dict[str, List[SchedulingAssignmentValue]] = {}

    for var in variables:
        var_domain: List[SchedulingAssignmentValue] = []
        required_duration_hours = var.duration_hours
        required_room_type = var.required_room_type
        group_size = group_sizes.get(var.group_id, 0)
        fac_info = faculty_meta.get(var.faculty_id, {"available_days": set(), "unavailable_slots": set()})

        # Pre-filter compatible rooms (H4: Capacity & H6: Room Type)
        compatible_rooms = [
            r for r in classrooms.values()
            if r["room_type"] == required_room_type and r["capacity"] >= group_size
        ]

        # Scan each day's slots
        for day, day_slots in slots_by_day.items():
            # Check if faculty works on this day (if defined)
            if fac_info["available_days"] and day not in fac_info["available_days"]:
                continue

            for idx in range(len(day_slots)):
                # Continuous block check (H7 & H8)
                consecutive_sequence = _get_consecutive_slots(
                    slots_by_day, day, idx, required_duration_hours
                )
                if not consecutive_sequence:
                    continue

                slot_ids_tuple = tuple(s["slot_id"] for s in consecutive_sequence)
                first_slot = consecutive_sequence[0]
                last_slot = consecutive_sequence[-1]

                # Check faculty unavailable slots (H5)
                has_fac_conflict = any(s_id in fac_info["unavailable_slots"] for s_id in slot_ids_tuple)
                if has_fac_conflict:
                    continue

                # Combine with compatible rooms
                for room in compatible_rooms:
                    val = SchedulingAssignmentValue(
                        slot_id=first_slot["slot_id"],
                        room_id=room["room_id"],
                        day=day,
                        start_time=first_slot["start_time"],
                        end_time=last_slot["end_time"],
                        slot_ids=slot_ids_tuple,
                        faculty_id=var.faculty_id,
                        group_id=var.group_id,
                    )
                    var_domain.append(val)

        domains[var.var_id] = var_domain

    total_possibilities = sum(len(d) for d in domains.values())
    logger.info("Constructed domains for %d variables: Total possibilities = %d", len(variables), total_possibilities)
    return domains
