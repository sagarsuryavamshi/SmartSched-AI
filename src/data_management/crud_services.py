"""CRUD database operations with validation and relational safety for SmartSched AI."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.crud_services")


# ============================================================================
# 1. CLASSROOM CRUD
# ============================================================================

def get_all_classrooms(search_term: str = "", db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all classrooms with optional search filtering."""
    query = "SELECT * FROM classrooms"
    params: List[Any] = []
    if search_term.strip():
        query += " WHERE room_id LIKE ? OR name LIKE ? OR room_type LIKE ? OR features LIKE ?"
        like_pat = f"%{search_term.strip()}%"
        params.extend([like_pat, like_pat, like_pat, like_pat])
    query += " ORDER BY room_id ASC"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_classroom_by_id(room_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single classroom by room_id."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM classrooms WHERE room_id = ?", (room_id.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_classroom(
    room_id: str,
    name: str,
    capacity: int,
    room_type: str,
    features: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Creates a new classroom with validation."""
    room_id = room_id.strip().upper()
    name = name.strip()
    if not room_id or not name:
        return False, "Room ID and Room Name cannot be empty."
    if capacity <= 0:
        return False, "Capacity must be a positive integer."
    if room_type not in ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"]:
        return False, "Invalid room type. Must be LECTURE_HALL, LAB, or SEMINAR_ROOM."

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM classrooms WHERE room_id = ?", (room_id,))
        if cursor.fetchone():
            return False, f"Classroom with ID '{room_id}' already exists."

        cursor.execute(
            "INSERT INTO classrooms (room_id, name, capacity, room_type, features) VALUES (?, ?, ?, ?, ?)",
            (room_id, name, capacity, room_type, features.strip()),
        )
    logger.info("Created classroom: %s (%s)", room_id, name)
    return True, f"Classroom '{name}' ({room_id}) created successfully."


def update_classroom(
    room_id: str,
    name: str,
    capacity: int,
    room_type: str,
    features: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Updates an existing classroom."""
    name = name.strip()
    if not name:
        return False, "Room Name cannot be empty."
    if capacity <= 0:
        return False, "Capacity must be a positive integer."
    if room_type not in ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"]:
        return False, "Invalid room type."

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM classrooms WHERE room_id = ?", (room_id,))
        if not cursor.fetchone():
            return False, f"Classroom '{room_id}' does not exist."

        cursor.execute(
            "UPDATE classrooms SET name = ?, capacity = ?, room_type = ?, features = ? WHERE room_id = ?",
            (name, capacity, room_type, features.strip(), room_id),
        )
    logger.info("Updated classroom: %s", room_id)
    return True, f"Classroom '{room_id}' updated successfully."


def delete_classroom(room_id: str, db_path: str = DEFAULT_DB_PATH) -> Tuple[bool, str]:
    """Safely deletes a classroom if not referenced by existing scheduled assignments."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scheduled_assignments WHERE room_id = ?", (room_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            return False, f"Cannot delete classroom '{room_id}' because it is referenced by {count} scheduled timetable assignment(s)."

        cursor.execute("DELETE FROM classrooms WHERE room_id = ?", (room_id,))
        if cursor.rowcount == 0:
            return False, f"Classroom '{room_id}' was not found."

    logger.info("Deleted classroom: %s", room_id)
    return True, f"Classroom '{room_id}' deleted successfully."


# ============================================================================
# 2. FACULTY CRUD
# ============================================================================

def get_all_faculty(search_term: str = "", db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all faculty members with optional search filtering."""
    query = "SELECT * FROM faculty"
    params: List[Any] = []
    if search_term.strip():
        query += " WHERE faculty_id LIKE ? OR name LIKE ? OR email LIKE ? OR department LIKE ?"
        like_pat = f"%{search_term.strip()}%"
        params.extend([like_pat, like_pat, like_pat, like_pat])
    query += " ORDER BY faculty_id ASC"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            # Parse JSON structures
            try:
                d["available_days_list"] = json.loads(d.get("available_days") or "[]")
            except Exception:
                d["available_days_list"] = []
            try:
                d["qualified_courses_list"] = json.loads(d.get("qualified_courses") or "[]")
            except Exception:
                d["qualified_courses_list"] = []
            try:
                d["unavailable_slots_list"] = json.loads(d.get("unavailable_slots") or "[]")
            except Exception:
                d["unavailable_slots_list"] = []
            result.append(d)
        return result


def get_faculty_by_id(faculty_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single faculty by faculty_id."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM faculty WHERE faculty_id = ?", (faculty_id.strip(),))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["available_days_list"] = json.loads(d.get("available_days") or "[]")
        d["qualified_courses_list"] = json.loads(d.get("qualified_courses") or "[]")
        d["unavailable_slots_list"] = json.loads(d.get("unavailable_slots") or "[]")
        return d


def create_faculty(
    faculty_id: str,
    name: str,
    email: str,
    department: str = "Computer Science",
    max_weekly_hours: int = 18,
    available_days: Optional[List[str]] = None,
    qualified_courses: Optional[List[str]] = None,
    unavailable_slots: Optional[List[str]] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Creates a new faculty member with validation."""
    faculty_id = faculty_id.strip().upper()
    name = name.strip()
    email = email.strip()
    if not faculty_id or not name or not email:
        return False, "Faculty ID, Name, and Email are mandatory."
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Invalid email address format."
    if max_weekly_hours <= 0:
        return False, "Maximum weekly hours must be positive."

    avail_days_json = json.dumps(available_days or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    qual_courses_json = json.dumps(qualified_courses or [])
    unavail_slots_json = json.dumps(unavailable_slots or [])

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM faculty WHERE faculty_id = ?", (faculty_id,))
        if cursor.fetchone():
            return False, f"Faculty member with ID '{faculty_id}' already exists."

        cursor.execute(
            """INSERT INTO faculty
               (faculty_id, name, email, department, max_weekly_hours, available_days, qualified_courses, unavailable_slots)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (faculty_id, name, email, department.strip(), max_weekly_hours, avail_days_json, qual_courses_json, unavail_slots_json),
        )
    logger.info("Created faculty: %s (%s)", faculty_id, name)
    return True, f"Faculty member '{name}' ({faculty_id}) registered successfully."


def update_faculty(
    faculty_id: str,
    name: str,
    email: str,
    department: str = "Computer Science",
    max_weekly_hours: int = 18,
    available_days: Optional[List[str]] = None,
    qualified_courses: Optional[List[str]] = None,
    unavailable_slots: Optional[List[str]] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Updates an existing faculty member."""
    name = name.strip()
    email = email.strip()
    if not name or not email:
        return False, "Faculty Name and Email cannot be empty."
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Invalid email format."
    if max_weekly_hours <= 0:
        return False, "Max weekly hours must be a positive integer."

    avail_days_json = json.dumps(available_days or [])
    qual_courses_json = json.dumps(qualified_courses or [])
    unavail_slots_json = json.dumps(unavailable_slots or [])

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM faculty WHERE faculty_id = ?", (faculty_id,))
        if not cursor.fetchone():
            return False, f"Faculty with ID '{faculty_id}' not found."

        cursor.execute(
            """UPDATE faculty
               SET name = ?, email = ?, department = ?, max_weekly_hours = ?, available_days = ?, qualified_courses = ?, unavailable_slots = ?
               WHERE faculty_id = ?""",
            (name, email, department.strip(), max_weekly_hours, avail_days_json, qual_courses_json, unavail_slots_json, faculty_id),
        )
    logger.info("Updated faculty: %s", faculty_id)
    return True, f"Faculty member '{faculty_id}' updated successfully."


def delete_faculty(faculty_id: str, db_path: str = DEFAULT_DB_PATH) -> Tuple[bool, str]:
    """Safely deletes faculty with foreign key reference protection."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Check course references
        cursor.execute("SELECT code, title FROM courses WHERE assigned_faculty_id = ?", (faculty_id,))
        referenced_courses = cursor.fetchall()
        if referenced_courses:
            course_list = ", ".join([r["code"] for r in referenced_courses])
            return False, f"Cannot delete faculty '{faculty_id}' because they are assigned to course(s): {course_list}. Reassign or remove courses first."

        # Check schedule assignments
        cursor.execute("SELECT COUNT(*) FROM scheduled_assignments WHERE faculty_id = ?", (faculty_id,))
        assignment_count = cursor.fetchone()[0]
        if assignment_count > 0:
            return False, f"Cannot delete faculty '{faculty_id}' because they have {assignment_count} scheduled timetable assignment(s)."

        cursor.execute("DELETE FROM faculty WHERE faculty_id = ?", (faculty_id,))
        if cursor.rowcount == 0:
            return False, f"Faculty '{faculty_id}' not found."

    logger.info("Deleted faculty: %s", faculty_id)
    return True, f"Faculty member '{faculty_id}' deleted successfully."


# ============================================================================
# 3. STUDENT GROUP CRUD
# ============================================================================

def get_all_student_groups(search_term: str = "", db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all student cohorts with optional search."""
    query = "SELECT * FROM student_groups"
    params: List[Any] = []
    if search_term.strip():
        query += " WHERE group_id LIKE ? OR name LIKE ? OR program LIKE ? OR department LIKE ?"
        like_pat = f"%{search_term.strip()}%"
        params.extend([like_pat, like_pat, like_pat, like_pat])
    query += " ORDER BY group_id ASC"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_student_group_by_id(group_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single student group by group_id."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student_groups WHERE group_id = ?", (group_id.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_student_group(
    group_id: str,
    name: str,
    department: str = "Computer Science",
    size: int = 50,
    program: str = "B.Tech",
    semester: int = 1,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Creates a new student cohort."""
    group_id = group_id.strip().upper()
    name = name.strip()
    if not group_id or not name:
        return False, "Group ID and Name are mandatory."
    if size <= 0:
        return False, "Student count (size) must be a positive integer."
    if semester < 1 or semester > 12:
        return False, "Semester must be between 1 and 12."

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM student_groups WHERE group_id = ?", (group_id,))
        if cursor.fetchone():
            return False, f"Student group with ID '{group_id}' already exists."

        cursor.execute(
            """INSERT INTO student_groups (group_id, name, department, size, program, semester)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (group_id, name, department.strip(), size, program.strip(), semester),
        )
    logger.info("Created student group: %s (%s)", group_id, name)
    return True, f"Student group '{name}' ({group_id}) created successfully."


def update_student_group(
    group_id: str,
    name: str,
    department: str = "Computer Science",
    size: int = 50,
    program: str = "B.Tech",
    semester: int = 1,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Updates an existing student group."""
    name = name.strip()
    if not name:
        return False, "Group Name cannot be empty."
    if size <= 0:
        return False, "Student count (size) must be positive."
    if semester < 1 or semester > 12:
        return False, "Semester must be between 1 and 12."

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM student_groups WHERE group_id = ?", (group_id,))
        if not cursor.fetchone():
            return False, f"Student group '{group_id}' not found."

        cursor.execute(
            """UPDATE student_groups
               SET name = ?, department = ?, size = ?, program = ?, semester = ?
               WHERE group_id = ?""",
            (name, department.strip(), size, program.strip(), semester, group_id),
        )
    logger.info("Updated student group: %s", group_id)
    return True, f"Student group '{group_id}' updated successfully."


def delete_student_group(group_id: str, db_path: str = DEFAULT_DB_PATH) -> Tuple[bool, str]:
    """Safely deletes student group with foreign key protection."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT code, title FROM courses WHERE target_group_id = ?", (group_id,))
        courses = cursor.fetchall()
        if courses:
            c_codes = ", ".join([c["code"] for c in courses])
            return False, f"Cannot delete group '{group_id}' because it is target of course(s): {c_codes}. Reassign or remove courses first."

        cursor.execute("SELECT COUNT(*) FROM scheduled_assignments WHERE group_id = ?", (group_id,))
        assign_count = cursor.fetchone()[0]
        if assign_count > 0:
            return False, f"Cannot delete group '{group_id}' because it has {assign_count} scheduled timetable assignment(s)."

        cursor.execute("DELETE FROM student_groups WHERE group_id = ?", (group_id,))
        if cursor.rowcount == 0:
            return False, f"Student group '{group_id}' not found."

    logger.info("Deleted student group: %s", group_id)
    return True, f"Student group '{group_id}' deleted successfully."


# ============================================================================
# 4. COURSES CRUD
# ============================================================================

def get_all_courses(search_term: str = "", db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all courses with joined faculty and student group details."""
    query = """
        SELECT c.*,
               f.name AS assigned_faculty_name,
               g.name AS target_group_name
        FROM courses c
        LEFT JOIN faculty f ON c.assigned_faculty_id = f.faculty_id
        LEFT JOIN student_groups g ON c.target_group_id = g.group_id
    """
    params: List[Any] = []
    if search_term.strip():
        query += " WHERE c.course_id LIKE ? OR c.code LIKE ? OR c.title LIKE ? OR c.category LIKE ? OR f.name LIKE ? OR g.name LIKE ?"
        like_pat = f"%{search_term.strip()}%"
        params.extend([like_pat, like_pat, like_pat, like_pat, like_pat, like_pat])
    query += " ORDER BY c.code ASC"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_course_by_id(course_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single course by course_id."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_course(
    course_id: str,
    code: str,
    title: str,
    weekly_hours: int,
    required_room_type: str = "LECTURE_HALL",
    category: str = "Theory",
    is_lab: bool = False,
    assigned_faculty_id: Optional[str] = None,
    target_group_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Creates a new academic course with validation and foreign key verification."""
    course_id = course_id.strip().upper()
    code = code.strip().upper()
    title = title.strip()
    if not course_id or not code or not title:
        return False, "Course ID, Code, and Title are mandatory."
    if weekly_hours <= 0:
        return False, "Weekly teaching hours must be positive."
    if required_room_type not in ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"]:
        return False, "Invalid required room type."
    if category not in ["Theory", "Practical"]:
        return False, "Category must be 'Theory' or 'Practical'."

    # If is_lab or practical, ensure room type or category aligns
    if category == "Practical":
        is_lab = True

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        # Unique check
        cursor.execute("SELECT 1 FROM courses WHERE course_id = ? OR code = ?", (course_id, code))
        if cursor.fetchone():
            return False, f"Course with ID '{course_id}' or code '{code}' already exists."

        # Verify assigned faculty exists
        if assigned_faculty_id:
            cursor.execute("SELECT 1 FROM faculty WHERE faculty_id = ?", (assigned_faculty_id,))
            if not cursor.fetchone():
                return False, f"Assigned faculty ID '{assigned_faculty_id}' does not exist in the database."

        # Verify target group exists
        if target_group_id:
            cursor.execute("SELECT 1 FROM student_groups WHERE group_id = ?", (target_group_id,))
            if not cursor.fetchone():
                return False, f"Target student group ID '{target_group_id}' does not exist in the database."

        cursor.execute(
            """INSERT INTO courses
               (course_id, code, title, weekly_hours, required_room_type, category, is_lab, assigned_faculty_id, target_group_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (course_id, code, title, weekly_hours, required_room_type, category, 1 if is_lab else 0, assigned_faculty_id, target_group_id),
        )
    logger.info("Created course: %s - %s", code, title)
    return True, f"Course '{code}: {title}' created successfully."


def update_course(
    course_id: str,
    code: str,
    title: str,
    weekly_hours: int,
    required_room_type: str = "LECTURE_HALL",
    category: str = "Theory",
    is_lab: bool = False,
    assigned_faculty_id: Optional[str] = None,
    target_group_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Updates an existing course."""
    code = code.strip().upper()
    title = title.strip()
    if not code or not title:
        return False, "Course Code and Title cannot be empty."
    if weekly_hours <= 0:
        return False, "Weekly teaching hours must be positive."
    if category == "Practical":
        is_lab = True

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM courses WHERE course_id = ?", (course_id,))
        if not cursor.fetchone():
            return False, f"Course '{course_id}' not found."

        # Verify unique code against other courses
        cursor.execute("SELECT 1 FROM courses WHERE code = ? AND course_id != ?", (code, course_id))
        if cursor.fetchone():
            return False, f"Course code '{code}' is already used by another course."

        if assigned_faculty_id:
            cursor.execute("SELECT 1 FROM faculty WHERE faculty_id = ?", (assigned_faculty_id,))
            if not cursor.fetchone():
                return False, f"Faculty '{assigned_faculty_id}' does not exist."

        if target_group_id:
            cursor.execute("SELECT 1 FROM student_groups WHERE group_id = ?", (target_group_id,))
            if not cursor.fetchone():
                return False, f"Student group '{target_group_id}' does not exist."

        cursor.execute(
            """UPDATE courses
               SET code = ?, title = ?, weekly_hours = ?, required_room_type = ?, category = ?, is_lab = ?, assigned_faculty_id = ?, target_group_id = ?
               WHERE course_id = ?""",
            (code, title, weekly_hours, required_room_type, category, 1 if is_lab else 0, assigned_faculty_id, target_group_id, course_id),
        )
    logger.info("Updated course: %s", course_id)
    return True, f"Course '{code}' updated successfully."


def delete_course(course_id: str, db_path: str = DEFAULT_DB_PATH) -> Tuple[bool, str]:
    """Safely deletes course with scheduled assignments reference check."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scheduled_assignments WHERE course_id = ?", (course_id,))
        assign_count = cursor.fetchone()[0]
        if assign_count > 0:
            return False, f"Cannot delete course '{course_id}' because it has {assign_count} scheduled timetable assignment(s)."

        cursor.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
        if cursor.rowcount == 0:
            return False, f"Course '{course_id}' not found."

    logger.info("Deleted course: %s", course_id)
    return True, f"Course '{course_id}' deleted successfully."


# ============================================================================
# 5. TIME SLOTS CRUD & GENERATOR
# ============================================================================

def get_all_timeslots(search_term: str = "", db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Fetches all timeslots with day and time ordering."""
    query = "SELECT * FROM timeslots"
    params: List[Any] = []
    if search_term.strip():
        query += " WHERE slot_id LIKE ? OR day LIKE ? OR start_time LIKE ? OR end_time LIKE ?"
        like_pat = f"%{search_term.strip()}%"
        params.extend([like_pat, like_pat, like_pat, like_pat])

    # Custom order by day of week then start time
    query += """
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
    """

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_timeslot_by_id(slot_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single timeslot by slot_id."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM timeslots WHERE slot_id = ?", (slot_id.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_timeslot(
    slot_id: str,
    day: str,
    start_time: str,
    end_time: str,
    duration_minutes: int = 60,
    is_break: bool = False,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Creates a new timeslot with validation."""
    slot_id = slot_id.strip().upper()
    day = day.strip()
    start_time = start_time.strip()
    end_time = end_time.strip()

    if not slot_id or not day or not start_time or not end_time:
        return False, "Slot ID, Day, Start Time, and End Time are required."
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    if day not in valid_days:
        return False, f"Invalid day of week. Must be one of: {', '.join(valid_days)}"
    if duration_minutes <= 0:
        return False, "Duration must be greater than 0 minutes."

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM timeslots WHERE slot_id = ?", (slot_id,))
        if cursor.fetchone():
            return False, f"Timeslot with ID '{slot_id}' already exists."

        # Check for duplicate same day + same start time
        cursor.execute("SELECT slot_id FROM timeslots WHERE day = ? AND start_time = ?", (day, start_time))
        existing_dup = cursor.fetchone()
        if existing_dup:
            return False, f"A timeslot already exists on {day} starting at {start_time} (ID: {existing_dup['slot_id']})."

        cursor.execute(
            """INSERT INTO timeslots (slot_id, day, start_time, end_time, duration_minutes, is_break)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (slot_id, day, start_time, end_time, duration_minutes, 1 if is_break else 0),
        )
    logger.info("Created timeslot: %s (%s %s-%s)", slot_id, day, start_time, end_time)
    return True, f"Timeslot '{slot_id}' ({day} {start_time}-{end_time}) created successfully."


def update_timeslot(
    slot_id: str,
    day: str,
    start_time: str,
    end_time: str,
    duration_minutes: int = 60,
    is_break: bool = False,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[bool, str]:
    """Updates an existing timeslot."""
    day = day.strip()
    start_time = start_time.strip()
    end_time = end_time.strip()
    if not day or not start_time or not end_time:
        return False, "Day, Start Time, and End Time are required."

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM timeslots WHERE slot_id = ?", (slot_id,))
        if not cursor.fetchone():
            return False, f"Timeslot '{slot_id}' not found."

        cursor.execute(
            """UPDATE timeslots
               SET day = ?, start_time = ?, end_time = ?, duration_minutes = ?, is_break = ?
               WHERE slot_id = ?""",
            (day, start_time, end_time, duration_minutes, 1 if is_break else 0, slot_id),
        )
    logger.info("Updated timeslot: %s", slot_id)
    return True, f"Timeslot '{slot_id}' updated successfully."


def delete_timeslot(slot_id: str, db_path: str = DEFAULT_DB_PATH) -> Tuple[bool, str]:
    """Safely deletes a timeslot with scheduled assignment check."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scheduled_assignments WHERE slot_id = ?", (slot_id,))
        assign_count = cursor.fetchone()[0]
        if assign_count > 0:
            return False, f"Cannot delete timeslot '{slot_id}' because it has {assign_count} scheduled timetable assignment(s)."

        cursor.execute("DELETE FROM timeslots WHERE slot_id = ?", (slot_id,))
        if cursor.rowcount == 0:
            return False, f"Timeslot '{slot_id}' not found."

    logger.info("Deleted timeslot: %s", slot_id)
    return True, f"Timeslot '{slot_id}' deleted successfully."
