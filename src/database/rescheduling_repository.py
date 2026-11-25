"""Rescheduling and Transactional Rollback Repository.

Provides atomic, transaction-safe operations to modify scheduled assignments,
log every change into `rescheduling_history`, and roll back previous changes
without corrupting relational integrity.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional, Tuple
from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.database.rescheduling")


def record_rescheduling_event(
    session_id: str,
    course_code: str,
    group_id: str,
    faculty_id: str,
    old_room_id: str,
    old_slot_id: str,
    old_day: str,
    old_start_time: str,
    new_room_id: str,
    new_slot_id: str,
    new_day: str,
    new_start_time: str,
    reason: str = "Administrator What-If Reschedule",
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str, str]:
    """Records a single committed rescheduling event into `rescheduling_history`."""
    change_id = f"CHG_{uuid.uuid4().hex[:8].upper()}"
    query = """
        INSERT INTO rescheduling_history (
            change_id, session_id, course_code, group_id, faculty_id,
            old_room_id, old_slot_id, old_day, old_start_time,
            new_room_id, new_slot_id, new_day, new_start_time,
            status, reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMMITTED', ?)
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    change_id, session_id, course_code, group_id, faculty_id,
                    old_room_id, old_slot_id, old_day, old_start_time,
                    new_room_id, new_slot_id, new_day, new_start_time,
                    reason,
                ),
            )
        return True, change_id, f"Reschedule change {change_id} recorded successfully."
    except Exception as exc:
        logger.error("Failed to record rescheduling history: %s", exc)
        return False, "", str(exc)


def apply_reschedule_transaction(
    assignment_ids: List[str],
    new_room_id: str,
    new_slot_ids: List[str],
    reason: str = "Admin Manual Adjustment",
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str, str]:
    """Applies a session reschedule atomically in SQLite.

    Handles single-slot theory sessions and multi-slot lab sessions.
    Updates `scheduled_assignments` and records the transition in `rescheduling_history`.
    If any step fails, the entire transaction is rolled back automatically.
    """
    if len(assignment_ids) != len(new_slot_ids):
        return False, "", "Mismatch between old assignment IDs count and new slot IDs count."

    change_id = f"CHG_{uuid.uuid4().hex[:8].upper()}"

    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # 1. Fetch current assignment and slot metadata
            old_records = []
            for a_id in assignment_ids:
                cursor.execute(
                    """
                    SELECT sa.id, sa.assignment_id, sa.course_id, c.code, sa.group_id, sa.faculty_id,
                           sa.room_id, sa.slot_id, ts.day, ts.start_time
                    FROM scheduled_assignments sa
                    JOIN courses c ON sa.course_id = c.course_id
                    JOIN timeslots ts ON sa.slot_id = ts.slot_id
                    WHERE sa.assignment_id = ?
                    """,
                    (a_id,),
                )
                row = cursor.fetchone()
                if not row:
                    return False, "", f"Assignment record '{a_id}' not found in database."
                old_records.append(row)

            # 2. Fetch new slot metadata
            new_slots_meta = []
            for s_id in new_slot_ids:
                cursor.execute(
                    "SELECT slot_id, day, start_time FROM timeslots WHERE slot_id = ?",
                    (s_id,),
                )
                s_row = cursor.fetchone()
                if not s_row:
                    return False, "", f"Target timeslot '{s_id}' does not exist."
                new_slots_meta.append(s_row)

            # 3. Update scheduled_assignments atomically
            for (old_row, new_slot) in zip(old_records, new_slots_meta):
                sa_id = old_row["assignment_id"]
                cursor.execute(
                    """
                    UPDATE scheduled_assignments
                    SET room_id = ?, slot_id = ?
                    WHERE assignment_id = ?
                    """,
                    (new_room_id, new_slot["slot_id"], sa_id),
                )

            # 4. Insert into rescheduling_history
            primary_old = old_records[0]
            primary_new = new_slots_meta[0]
            cursor.execute(
                """
                INSERT INTO rescheduling_history (
                    change_id, session_id, course_code, group_id, faculty_id,
                    old_room_id, old_slot_id, old_day, old_start_time,
                    new_room_id, new_slot_id, new_day, new_start_time,
                    status, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMMITTED', ?)
                """,
                (
                    change_id,
                    primary_old["assignment_id"],
                    primary_old["code"],
                    primary_old["group_id"],
                    primary_old["faculty_id"],
                    primary_old["room_id"],
                    ",".join(r["slot_id"] for r in old_records),
                    primary_old["day"],
                    primary_old["start_time"],
                    new_room_id,
                    ",".join(new_slot_ids),
                    primary_new["day"],
                    primary_new["start_time"],
                    reason,
                ),
            )

        logger.info("Successfully executed atomic reschedule %s for %s", change_id, primary_old["code"])
        return True, change_id, f"Reschedule committed successfully under Change ID: {change_id}."

    except Exception as exc:
        logger.error("Atomic reschedule failed and rolled back: %s", exc)
        return False, "", f"Transaction error: {str(exc)}"


def rollback_reschedule_transaction(
    change_id: str,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Atomically rolls back a committed reschedule change, restoring the previous assignment."""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Retrieve change record
            cursor.execute(
                "SELECT * FROM rescheduling_history WHERE change_id = ?",
                (change_id,),
            )
            chg = cursor.fetchone()
            if not chg:
                return False, f"Reschedule record '{change_id}' not found."

            if chg["status"] == "ROLLED_BACK":
                return False, f"Change '{change_id}' has already been rolled back."

            session_id = chg["session_id"]
            old_room_id = chg["old_room_id"]
            old_slot_ids = chg["old_slot_id"].split(",")
            new_slot_ids = chg["new_slot_id"].split(",")

            # Revert the scheduled assignments
            # Find the assignments corresponding to the session
            cursor.execute(
                """
                SELECT sa.assignment_id, sa.slot_id
                FROM scheduled_assignments sa
                WHERE sa.room_id = ? AND sa.slot_id IN ({})
                """.format(",".join("?" * len(new_slot_ids))),
                [chg["new_room_id"]] + new_slot_ids,
            )
            current_rows = cursor.fetchall()

            for old_s_id, new_s_id in zip(old_slot_ids, new_slot_ids):
                cursor.execute(
                    """
                    UPDATE scheduled_assignments
                    SET room_id = ?, slot_id = ?
                    WHERE room_id = ? AND slot_id = ?
                    """,
                    (old_room_id, old_s_id, chg["new_room_id"], new_s_id),
                )

            # Mark change as rolled back
            cursor.execute(
                "UPDATE rescheduling_history SET status = 'ROLLED_BACK' WHERE change_id = ?",
                (change_id,),
            )

        logger.info("Successfully rolled back reschedule %s", change_id)
        return True, f"Change '{change_id}' was successfully rolled back to original slots."

    except Exception as exc:
        logger.error("Rollback of %s failed: %s", change_id, exc)
        return False, f"Rollback error: {str(exc)}"


def get_rescheduling_history(
    limit: int = 50,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """Retrieves all recorded rescheduling changes in reverse chronological order."""
    query = """
        SELECT
            id, change_id, session_id, course_code, group_id, faculty_id,
            old_room_id, old_slot_id, old_day, old_start_time,
            new_room_id, new_slot_id, new_day, new_start_time,
            timestamp, status, reason
        FROM rescheduling_history
        ORDER BY id DESC
        LIMIT ?
    """
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to fetch rescheduling history: %s", exc)
        return []
