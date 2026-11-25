"""PostgreSQL Schema Migration and Data Transfer Script for SmartSched AI.

Preserves:
  - SQLite source data (read-only verification).
  - Primary keys, foreign keys, unique constraints, and check constraints.
  - Full relational integrity across classrooms, faculty, student groups, courses, timeslots,
    scheduled_assignments, and rescheduling_history.
"""

import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SQLITE_DB_PATH = BASE_DIR / "data" / "smartsched.db"
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://sagarsukhadev@localhost:5432/smartsched")

CREATE_TABLES_SQL = """
-- Drop existing tables in dependency order
DROP TABLE IF EXISTS rescheduling_history CASCADE;
DROP TABLE IF EXISTS scheduled_assignments CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS student_groups CASCADE;
DROP TABLE IF EXISTS faculty CASCADE;
DROP TABLE IF EXISTS classrooms CASCADE;
DROP TABLE IF EXISTS timeslots CASCADE;

-- 1. Classrooms
CREATE TABLE classrooms (
    room_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    room_type VARCHAR(50) NOT NULL DEFAULT 'Classroom',
    features TEXT DEFAULT ''
);

-- 2. Faculty
CREATE TABLE faculty (
    faculty_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    max_weekly_hours INTEGER NOT NULL DEFAULT 18 CHECK (max_weekly_hours > 0),
    qualified_courses TEXT DEFAULT '[]',
    unavailable_slots TEXT DEFAULT '[]',
    department VARCHAR(100) NOT NULL DEFAULT 'Computer Science',
    available_days TEXT DEFAULT '["Monday","Tuesday","Wednesday","Thursday","Friday"]'
);

-- 3. Student Groups
CREATE TABLE student_groups (
    group_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    size INTEGER NOT NULL CHECK (size > 0),
    program VARCHAR(100) NOT NULL DEFAULT 'B.Tech',
    semester INTEGER NOT NULL CHECK (semester >= 1),
    department VARCHAR(100) NOT NULL DEFAULT 'Computer Science'
);

-- 4. Courses
CREATE TABLE courses (
    course_id VARCHAR(50) PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    weekly_hours INTEGER NOT NULL CHECK (weekly_hours > 0),
    required_room_type VARCHAR(50) NOT NULL DEFAULT 'Classroom',
    is_lab BOOLEAN NOT NULL DEFAULT FALSE,
    assigned_faculty_id VARCHAR(50) REFERENCES faculty(faculty_id) ON DELETE SET NULL,
    target_group_id VARCHAR(50) REFERENCES student_groups(group_id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL DEFAULT 'Core'
);

-- 5. Timeslots
CREATE TABLE timeslots (
    slot_id VARCHAR(50) PRIMARY KEY,
    day VARCHAR(20) NOT NULL,
    start_time VARCHAR(20) NOT NULL,
    end_time VARCHAR(20) NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 60 CHECK (duration_minutes > 0),
    is_break BOOLEAN NOT NULL DEFAULT FALSE
);

-- 6. Scheduled Assignments (Active Timetables)
CREATE TABLE scheduled_assignments (
    id SERIAL PRIMARY KEY,
    assignment_id VARCHAR(100) NOT NULL,
    course_id VARCHAR(50) NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    group_id VARCHAR(50) NOT NULL REFERENCES student_groups(group_id) ON DELETE CASCADE,
    faculty_id VARCHAR(50) NOT NULL REFERENCES faculty(faculty_id) ON DELETE CASCADE,
    room_id VARCHAR(50) NOT NULL REFERENCES classrooms(room_id) ON DELETE CASCADE,
    slot_id VARCHAR(50) NOT NULL REFERENCES timeslots(slot_id) ON DELETE CASCADE,
    generation_run_id VARCHAR(50) NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_sa_run_id ON scheduled_assignments(generation_run_id);
CREATE INDEX idx_sa_course ON scheduled_assignments(course_id);
CREATE INDEX idx_sa_faculty ON scheduled_assignments(faculty_id);
CREATE INDEX idx_sa_group ON scheduled_assignments(group_id);
CREATE INDEX idx_sa_room ON scheduled_assignments(room_id);
CREATE INDEX idx_sa_slot ON scheduled_assignments(slot_id);

-- 7. Rescheduling History (Audit Trail)
CREATE TABLE rescheduling_history (
    id SERIAL PRIMARY KEY,
    change_id VARCHAR(50) NOT NULL UNIQUE,
    session_id VARCHAR(100) NOT NULL,
    course_code VARCHAR(50) NOT NULL,
    group_id VARCHAR(50) NOT NULL,
    faculty_id VARCHAR(50) NOT NULL,
    old_room_id VARCHAR(50) NOT NULL,
    old_slot_id VARCHAR(50) NOT NULL,
    old_day VARCHAR(20) NOT NULL,
    old_start_time VARCHAR(20) NOT NULL,
    new_room_id VARCHAR(50) NOT NULL,
    new_slot_id VARCHAR(50) NOT NULL,
    new_day VARCHAR(20) NOT NULL,
    new_start_time VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'COMMITTED',
    reason TEXT NOT NULL
);

CREATE INDEX idx_rh_change_id ON rescheduling_history(change_id);
"""

def migrate():
    print(f"Connecting to source SQLite: {SQLITE_DB_PATH}")
    sqlite_conn = sqlite3.connect(str(SQLITE_DB_PATH))
    sqlite_conn.row_factory = sqlite3.Row
    sq_cur = sqlite_conn.cursor()

    print(f"Connecting to target PostgreSQL: {POSTGRES_URL}")
    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cur = pg_conn.cursor()

    # 1. Execute DDL
    print("Creating PostgreSQL tables and indexes...")
    pg_cur.execute(CREATE_TABLES_SQL)
    pg_conn.commit()

    # 2. Transfer Classrooms
    sq_cur.execute("SELECT room_id, name, capacity, room_type, features FROM classrooms")
    rooms = [tuple(r) for r in sq_cur.fetchall()]
    execute_values(pg_cur, "INSERT INTO classrooms (room_id, name, capacity, room_type, features) VALUES %s", rooms)
    print(f"Migrated {len(rooms)} classrooms.")

    # 3. Transfer Faculty
    sq_cur.execute("SELECT faculty_id, name, email, max_weekly_hours, qualified_courses, unavailable_slots, department, available_days FROM faculty")
    fac = [tuple(r) for r in sq_cur.fetchall()]
    execute_values(pg_cur, "INSERT INTO faculty (faculty_id, name, email, max_weekly_hours, qualified_courses, unavailable_slots, department, available_days) VALUES %s", fac)
    print(f"Migrated {len(fac)} faculty members.")

    # 4. Transfer Student Groups
    sq_cur.execute("SELECT group_id, name, size, program, semester, department FROM student_groups")
    groups = [tuple(r) for r in sq_cur.fetchall()]
    execute_values(pg_cur, "INSERT INTO student_groups (group_id, name, size, program, semester, department) VALUES %s", groups)
    print(f"Migrated {len(groups)} student groups.")

    # 5. Transfer Courses
    sq_cur.execute("SELECT course_id, code, title, weekly_hours, required_room_type, is_lab, assigned_faculty_id, target_group_id, category FROM courses")
    courses = []
    for r in sq_cur.fetchall():
        d = list(r)
        d[5] = bool(d[5])  # SQLite 0/1 to boolean
        courses.append(tuple(d))
    execute_values(pg_cur, "INSERT INTO courses (course_id, code, title, weekly_hours, required_room_type, is_lab, assigned_faculty_id, target_group_id, category) VALUES %s", courses)
    print(f"Migrated {len(courses)} courses.")

    # 6. Transfer Timeslots
    sq_cur.execute("SELECT slot_id, day, start_time, end_time, duration_minutes, is_break FROM timeslots")
    slots = []
    for r in sq_cur.fetchall():
        d = list(r)
        d[5] = bool(d[5])
        slots.append(tuple(d))
    execute_values(pg_cur, "INSERT INTO timeslots (slot_id, day, start_time, end_time, duration_minutes, is_break) VALUES %s", slots)
    print(f"Migrated {len(slots)} timeslots.")

    # 7. Transfer Scheduled Assignments
    sq_cur.execute("SELECT assignment_id, course_id, group_id, faculty_id, room_id, slot_id, generation_run_id FROM scheduled_assignments")
    assignments = [tuple(r) for r in sq_cur.fetchall()]
    if assignments:
        execute_values(pg_cur, "INSERT INTO scheduled_assignments (assignment_id, course_id, group_id, faculty_id, room_id, slot_id, generation_run_id) VALUES %s", assignments)
    print(f"Migrated {len(assignments)} scheduled assignments.")

    # 8. Transfer Rescheduling History
    sq_cur.execute("SELECT change_id, session_id, course_code, group_id, faculty_id, old_room_id, old_slot_id, old_day, old_start_time, new_room_id, new_slot_id, new_day, new_start_time, status, reason FROM rescheduling_history")
    history = [tuple(r) for r in sq_cur.fetchall()]
    if history:
        execute_values(pg_cur, "INSERT INTO rescheduling_history (change_id, session_id, course_code, group_id, faculty_id, old_room_id, old_slot_id, old_day, old_start_time, new_room_id, new_slot_id, new_day, new_start_time, status, reason) VALUES %s", history)
    print(f"Migrated {len(history)} rescheduling history records.")

    pg_conn.commit()

    # Verification counts
    print("\n--- Migration Verification ---")
    for tbl in ["classrooms", "faculty", "student_groups", "courses", "timeslots", "scheduled_assignments", "rescheduling_history"]:
        sq_cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        sq_count = sq_cur.fetchone()[0]
        pg_cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        pg_count = pg_cur.fetchone()[0]
        match = "MATCH [OK]" if sq_count == pg_count else "MISMATCH [FAIL]"
        print(f"Table '{tbl}': SQLite={sq_count} -> PostgreSQL={pg_count} | {match}")
        assert sq_count == pg_count, f"Record count mismatch in {tbl}"

    sqlite_conn.close()
    pg_conn.close()
    print("\nPostgreSQL Database Migration successfully executed and verified!")

if __name__ == "__main__":
    migrate()
