"""Synthetic data generator and database seeder for SmartSched AI."""

import json
from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection, init_db
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.data_management")


def seed_synthetic_data(db_path: str = DEFAULT_DB_PATH, overwrite: bool = False) -> None:
    """Populates the database with realistic academic scheduling data.

    Args:
        db_path: Path to target SQLite database.
        overwrite: If True, clears existing tables before insertion.
    """
    init_db(db_path)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        if overwrite:
            cursor.executescript("""
                DELETE FROM scheduled_assignments;
                DELETE FROM courses;
                DELETE FROM faculty;
                DELETE FROM student_groups;
                DELETE FROM classrooms;
                DELETE FROM timeslots;
            """)

        # Check if already populated
        cursor.execute("SELECT COUNT(*) FROM classrooms")
        if cursor.fetchone()[0] > 0 and not overwrite:
            logger.info("Database already contains data; skipping synthetic seeding.")
            return

        # 1. Timeslots (Mon-Fri, 4 daily lecture slots: 9-10, 10-11, 11-12, 14-15; 1 lunch break: 12-14)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        hours = [
            ("09:00", "10:00", 60, 0),
            ("10:00", "11:00", 60, 0),
            ("11:00", "12:00", 60, 0),
            ("12:00", "13:00", 60, 1),  # Lunch break
            ("14:00", "15:00", 60, 0),
        ]
        slots = []
        for d_idx, day in enumerate(days):
            for h_idx, (start, end, duration, is_brk) in enumerate(hours):
                slot_id = f"TS_{day[:3].upper()}_{h_idx+1}"
                slots.append((slot_id, day, start, end, duration, is_brk))

        cursor.executemany(
            """INSERT OR REPLACE INTO timeslots
               (slot_id, day, start_time, end_time, duration_minutes, is_break)
               VALUES (?, ?, ?, ?, ?, ?)""",
            slots,
        )

        # 2. Classrooms & Labs
        classrooms = [
            ("CR_LH101", "Lecture Hall 101", 80, "LECTURE_HALL", "Projector, Audio System"),
            ("CR_LH102", "Lecture Hall 102", 70, "LECTURE_HALL", "Smart Board, Projector"),
            ("CR_LH103", "Lecture Hall 103", 50, "LECTURE_HALL", "Projector"),
            ("CR_LAB201", "AI & Robotics Lab", 60, "LAB", "High-End GPUs, Linux Workstations"),
            ("CR_LAB202", "Software Systems Lab", 60, "LAB", "Dual Monitors, Dev Environments"),
            ("CR_SEM301", "Seminar Room A", 40, "SEMINAR_ROOM", "Video Conferencing, Display"),
        ]
        cursor.executemany(
            "INSERT OR REPLACE INTO classrooms (room_id, name, capacity, room_type, features) VALUES (?, ?, ?, ?, ?)",
            classrooms,
        )

        # 3. Student Groups
        groups = [
            ("GRP_CS_SEM4", "CS Batch 2024 (Semester 4)", "Computer Science", 55, "B.Tech Computer Science", 4),
            ("GRP_CS_SEM6", "CS Batch 2023 (Semester 6)", "Computer Science", 48, "B.Tech Computer Science", 6),
            ("GRP_AI_SEM2", "AI & Data Science (Semester 2)", "Artificial Intelligence", 38, "M.Tech AI & DS", 2),
        ]
        cursor.executemany(
            """INSERT OR REPLACE INTO student_groups
               (group_id, name, department, size, program, semester)
               VALUES (?, ?, ?, ?, ?, ?)""",
            groups,
        )

        # 4. Faculty with qualified subjects and availability constraints
        faculty_data = [
            ("FAC_ALAN", "Prof. Alan Turing", "a.turing@university.edu", "Computer Science", 14,
             json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
             json.dumps(["CS201", "CS401"]),
             json.dumps(["TS_FRI_5"])),
            ("FAC_GRACE", "Prof. Grace Hopper", "g.hopper@university.edu", "Computer Science", 16,
             json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday"]),
             json.dumps(["CS202", "CS302"]),
             json.dumps(["TS_MON_1"])),
            ("FAC_JOHN", "Prof. John von Neumann", "j.vonneumann@university.edu", "Computer Science", 14,
             json.dumps(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
             json.dumps(["CS203", "AI501"]),
             json.dumps([])),
            ("FAC_ADA", "Prof. Ada Lovelace", "a.lovelace@university.edu", "Computer Science", 16,
             json.dumps(["Tuesday", "Wednesday", "Thursday", "Friday"]),
             json.dumps(["CS204", "AI502"]),
             json.dumps(["TS_WED_5"])),
            ("FAC_CLAUDE", "Prof. Claude Shannon", "c.shannon@university.edu", "Artificial Intelligence", 14,
             json.dumps(["Monday", "Wednesday", "Friday"]),
             json.dumps(["CS305", "AI503"]),
             json.dumps([])),
        ]
        cursor.executemany(
            """INSERT OR REPLACE INTO faculty
               (faculty_id, name, email, department, max_weekly_hours, available_days, qualified_courses, unavailable_slots)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            faculty_data,
        )

        # 5. Courses linked to groups and designated faculty
        courses = [
            # CS Sem 4 courses
            ("CRS_CS201", "CS201", "Data Structures & Algorithms", 3, "LECTURE_HALL", "Theory", 0, "FAC_ALAN", "GRP_CS_SEM4"),
            ("CRS_CS202", "CS202", "Computer Organization & Architecture", 3, "LECTURE_HALL", "Theory", 0, "FAC_GRACE", "GRP_CS_SEM4"),
            ("CRS_CS203", "CS203", "Operating Systems", 3, "LECTURE_HALL", "Theory", 0, "FAC_JOHN", "GRP_CS_SEM4"),
            ("CRS_CS204", "CS204", "Operating Systems Practical Lab", 2, "LAB", "Practical", 1, "FAC_ADA", "GRP_CS_SEM4"),

            # CS Sem 6 courses
            ("CRS_CS302", "CS302", "Compiler Design", 3, "LECTURE_HALL", "Theory", 0, "FAC_GRACE", "GRP_CS_SEM6"),
            ("CRS_CS305", "CS305", "Information & Coding Theory", 3, "LECTURE_HALL", "Theory", 0, "FAC_CLAUDE", "GRP_CS_SEM6"),
            ("CRS_CS401", "CS401", "Distributed Computing Lab", 2, "LAB", "Practical", 1, "FAC_ALAN", "GRP_CS_SEM6"),

            # M.Tech AI Sem 2 courses
            ("CRS_AI501", "AI501", "Advanced Machine Learning", 3, "LECTURE_HALL", "Theory", 0, "FAC_JOHN", "GRP_AI_SEM2"),
            ("CRS_AI502", "AI502", "Natural Language Processing Lab", 2, "LAB", "Practical", 1, "FAC_ADA", "GRP_AI_SEM2"),
            ("CRS_AI503", "AI503", "Probabilistic Graphical Models", 3, "LECTURE_HALL", "Theory", 0, "FAC_CLAUDE", "GRP_AI_SEM2"),
        ]
        cursor.executemany(
            """INSERT OR REPLACE INTO courses
               (course_id, code, title, weekly_hours, required_room_type, category, is_lab, assigned_faculty_id, target_group_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            courses,
        )

    logger.info("Successfully populated synthetic academic data in %s", db_path)


def load_dataset_summary(db_path: str = DEFAULT_DB_PATH) -> dict:
    """Returns total counts of each entity type from the database."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        counts = {}
        for table in ["classrooms", "faculty", "student_groups", "courses", "timeslots", "scheduled_assignments"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
    return counts
