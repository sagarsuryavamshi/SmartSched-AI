"""Database persistence and retrieval services for scheduled academic timetables."""

import uuid
from typing import Any, Dict, List, Optional, Tuple
from src.csp_engine.domain_types import SchedulingAssignmentValue, SchedulingVariable
from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.database.timetable_repo")


def save_timetable_solution(
    assignment: Dict[str, SchedulingAssignmentValue],
    variables_map: Dict[str, SchedulingVariable],
    run_id: Optional[str] = None,
    overwrite_existing: bool = True,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Persists a complete or partial timetable assignment into `scheduled_assignments`.

    Uses a single transaction to prevent partial writes.
    Does not touch or modify the underlying courses, faculty, or classrooms tables.
    """
    if not assignment:
        return False, "Cannot save an empty timetable assignment."

    run_id = run_id or f"RUN_{uuid.uuid4().hex[:8].upper()}"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        if overwrite_existing:
            cursor.execute("DELETE FROM scheduled_assignments")
            logger.info("Cleared previous schedule assignments before saving new run '%s'.", run_id)

        rows_to_insert = []
        for var_id, val in assignment.items():
            var = variables_map.get(var_id)
            if not var:
                continue

            # If session spans multiple consecutive slot_ids (e.g. 2-hour lab),
            # persist an assignment record for each occupied slot_id
            for s_id in val.slot_ids:
                asg_id = f"ASG_{var.course_code}_S{var.session_num}_{s_id}"
                rows_to_insert.append((
                    asg_id,
                    var.course_id,
                    val.group_id,
                    val.faculty_id,
                    val.room_id,
                    s_id,
                    run_id,
                ))

        cursor.executemany(
            """INSERT OR REPLACE INTO scheduled_assignments
               (assignment_id, course_id, group_id, faculty_id, room_id, slot_id, generation_run_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            rows_to_insert,
        )

    logger.info("Successfully persisted %d schedule entries for run '%s'.", len(rows_to_insert), run_id)
    return True, f"Timetable saved successfully ({len(rows_to_insert)} sessions stored under Run ID: {run_id})."


def load_saved_timetable(
    run_id: Optional[str] = None,
    group_id: Optional[str] = None,
    faculty_id: Optional[str] = None,
    room_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """Retrieves saved timetable schedule records with joined course, faculty, room, and timeslot details.
    Supports PostgreSQL if DATABASE_URL is set, otherwise falls back to SQLite db_path.
    """
    database_url = os.getenv("DATABASE_URL")
    is_postgres = database_url and database_url.startswith("postgresql")

    query = """
        SELECT
            sa.id,
            sa.assignment_id,
            sa.generation_run_id,
            c.code AS course_code,
            c.title AS course_title,
            c.category AS course_category,
            f.name AS faculty_name,
            f.faculty_id,
            g.name AS group_name,
            g.group_id,
            cr.name AS room_name,
            cr.room_id,
            cr.room_type,
            ts.slot_id,
            ts.day,
            ts.start_time,
            ts.end_time,
            ts.duration_minutes
        FROM scheduled_assignments sa
        JOIN courses c ON sa.course_id = c.course_id
        JOIN faculty f ON sa.faculty_id = f.faculty_id
        JOIN student_groups g ON sa.group_id = g.group_id
        JOIN classrooms cr ON sa.room_id = cr.room_id
        JOIN timeslots ts ON sa.slot_id = ts.slot_id
        WHERE 1=1
    """
    placeholder = "%s" if is_postgres else "?"
    params: List[Any] = []
    if run_id:
        query += f" AND sa.generation_run_id = {placeholder}"
        params.append(run_id)
    if group_id:
        query += f" AND sa.group_id = {placeholder}"
        params.append(group_id)
    if faculty_id:
        query += f" AND sa.faculty_id = {placeholder}"
        params.append(faculty_id)
    if room_id:
        query += f" AND sa.room_id = {placeholder}"
        params.append(room_id)

    query += """
        ORDER BY
            CASE ts.day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                ELSE 7
            END,
            ts.start_time ASC
    """

    if is_postgres:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        try:
            conn = psycopg2.connect(database_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params)
            rows = cur.fetchall()
            cur.close()
            conn.close()
            if rows:
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error("Error loading timetable from PostgreSQL: %s", e)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
