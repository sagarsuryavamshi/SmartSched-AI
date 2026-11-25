"""Comprehensive test suite for SmartSched AI CRUD operations and foreign key safeguards."""

import os
import shutil
import tempfile
import unittest

from src.database.db_manager import init_db, get_db_connection
from src.data_management.crud_services import (
    create_classroom,
    create_course,
    create_faculty,
    create_student_group,
    create_timeslot,
    delete_classroom,
    delete_course,
    delete_faculty,
    delete_student_group,
    delete_timeslot,
    get_all_classrooms,
    get_all_courses,
    get_all_faculty,
    get_all_student_groups,
    get_all_timeslots,
    get_classroom_by_id,
    get_course_by_id,
    get_faculty_by_id,
    get_student_group_by_id,
    get_timeslot_by_id,
    update_classroom,
    update_course,
    update_faculty,
    update_student_group,
    update_timeslot,
)
from src.data_management.loader import seed_synthetic_data


class TestDataManagementCRUD(unittest.TestCase):
    """Unit tests for CRUD services, persistence, validations, and relational integrity."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_smartsched.db")
        init_db(self.test_db)
        seed_synthetic_data(self.test_db, overwrite=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ------------------------------------------------------------------------
    # 1. CLASSROOM TESTS
    # ------------------------------------------------------------------------
    def test_classroom_crud_lifecycle(self) -> None:
        # Create
        ok, msg = create_classroom("CR_TEST1", "Auditorium X", 150, "LECTURE_HALL", "Stage, Mic", db_path=self.test_db)
        self.assertTrue(ok)
        room = get_classroom_by_id("CR_TEST1", db_path=self.test_db)
        self.assertIsNotNone(room)
        self.assertEqual(room["capacity"], 150)

        # Duplicate ID rejection
        ok, msg = create_classroom("CR_TEST1", "Duplicate Room", 100, "LAB", db_path=self.test_db)
        self.assertFalse(ok)
        self.assertIn("already exists", msg)

        # Invalid capacity
        ok, msg = create_classroom("CR_BAD", "Bad Capacity", -10, "LECTURE_HALL", db_path=self.test_db)
        self.assertFalse(ok)

        # Update
        ok, msg = update_classroom("CR_TEST1", "Auditorium Prime", 200, "LECTURE_HALL", "Upgraded AV", db_path=self.test_db)
        self.assertTrue(ok)
        room_updated = get_classroom_by_id("CR_TEST1", db_path=self.test_db)
        self.assertEqual(room_updated["name"], "Auditorium Prime")
        self.assertEqual(room_updated["capacity"], 200)

        # Delete
        ok, msg = delete_classroom("CR_TEST1", db_path=self.test_db)
        self.assertTrue(ok)
        self.assertIsNone(get_classroom_by_id("CR_TEST1", db_path=self.test_db))

    def test_classroom_foreign_key_protection(self) -> None:
        # Inject an assignment referencing CR_LH101
        with get_db_connection(self.test_db) as conn:
            conn.execute(
                """INSERT INTO scheduled_assignments
                   (assignment_id, course_id, group_id, faculty_id, room_id, slot_id)
                   VALUES ('ASG_1', 'CRS_CS201', 'GRP_CS_SEM4', 'FAC_ALAN', 'CR_LH101', 'TS_MON_1')"""
            )
        # Attempt delete should fail safely
        ok, msg = delete_classroom("CR_LH101", db_path=self.test_db)
        self.assertFalse(ok)
        self.assertIn("referenced by", msg)

    # ------------------------------------------------------------------------
    # 2. FACULTY TESTS
    # ------------------------------------------------------------------------
    def test_faculty_crud_lifecycle(self) -> None:
        # Create
        ok, msg = create_faculty(
            faculty_id="FAC_TEST",
            name="Dr. Richard Feynman",
            email="feynman@university.edu",
            department="Physics",
            max_weekly_hours=12,
            available_days=["Monday", "Wednesday"],
            qualified_courses=["CS201"],
            unavailable_slots=["TS_MON_1"],
            db_path=self.test_db,
        )
        self.assertTrue(ok)
        fac = get_faculty_by_id("FAC_TEST", db_path=self.test_db)
        self.assertIsNotNone(fac)
        self.assertEqual(fac["department"], "Physics")
        self.assertEqual(fac["available_days_list"], ["Monday", "Wednesday"])
        self.assertEqual(fac["unavailable_slots_list"], ["TS_MON_1"])

        # Invalid Email
        ok, msg = create_faculty("FAC_BAD", "Bad", "bad-email-format", db_path=self.test_db)
        self.assertFalse(ok)
        self.assertIn("email", msg.lower())

        # Update
        ok, msg = update_faculty(
            faculty_id="FAC_TEST",
            name="Prof. Richard Feynman",
            email="r.feynman@university.edu",
            department="Quantum Computing",
            max_weekly_hours=14,
            available_days=["Tuesday", "Thursday"],
            qualified_courses=["CS201", "CS202"],
            unavailable_slots=[],
            db_path=self.test_db,
        )
        self.assertTrue(ok)
        fac_up = get_faculty_by_id("FAC_TEST", db_path=self.test_db)
        self.assertEqual(fac_up["department"], "Quantum Computing")
        self.assertEqual(fac_up["max_weekly_hours"], 14)

        # Delete unreferenced faculty
        ok, msg = delete_faculty("FAC_TEST", db_path=self.test_db)
        self.assertTrue(ok)
        self.assertIsNone(get_faculty_by_id("FAC_TEST", db_path=self.test_db))

    def test_faculty_foreign_key_protection(self) -> None:
        # FAC_ALAN is assigned to courses in seed data (CRS_CS201)
        ok, msg = delete_faculty("FAC_ALAN", db_path=self.test_db)
        self.assertFalse(ok)
        self.assertIn("assigned to course", msg)

    # ------------------------------------------------------------------------
    # 3. STUDENT GROUP TESTS
    # ------------------------------------------------------------------------
    def test_student_group_crud_lifecycle(self) -> None:
        # Create
        ok, msg = create_student_group(
            group_id="GRP_CYBER_SEM1",
            name="Cybersecurity Batch 2026",
            department="Information Security",
            size=45,
            program="M.Tech Cybersecurity",
            semester=1,
            db_path=self.test_db,
        )
        self.assertTrue(ok)
        grp = get_student_group_by_id("GRP_CYBER_SEM1", db_path=self.test_db)
        self.assertIsNotNone(grp)
        self.assertEqual(grp["size"], 45)

        # Update
        ok, msg = update_student_group(
            group_id="GRP_CYBER_SEM1",
            name="Cybersecurity Batch 2026 (Updated)",
            department="Information Security",
            size=52,
            program="M.Tech Cybersecurity",
            semester=2,
            db_path=self.test_db,
        )
        self.assertTrue(ok)
        grp_up = get_student_group_by_id("GRP_CYBER_SEM1", db_path=self.test_db)
        self.assertEqual(grp_up["size"], 52)
        self.assertEqual(grp_up["semester"], 2)

        # Delete
        ok, msg = delete_student_group("GRP_CYBER_SEM1", db_path=self.test_db)
        self.assertTrue(ok)
        self.assertIsNone(get_student_group_by_id("GRP_CYBER_SEM1", db_path=self.test_db))

    def test_student_group_foreign_key_protection(self) -> None:
        # GRP_CS_SEM4 has courses assigned
        ok, msg = delete_student_group("GRP_CS_SEM4", db_path=self.test_db)
        self.assertFalse(ok)
        self.assertIn("target of course", msg)

    # ------------------------------------------------------------------------
    # 4. COURSES TESTS
    # ------------------------------------------------------------------------
    def test_course_crud_lifecycle(self) -> None:
        # Create
        ok, msg = create_course(
            course_id="CRS_CS999",
            code="CS999",
            title="Quantum Information Theory",
            weekly_hours=4,
            required_room_type="LECTURE_HALL",
            category="Theory",
            assigned_faculty_id="FAC_CLAUDE",
            target_group_id="GRP_CS_SEM6",
            db_path=self.test_db,
        )
        self.assertTrue(ok)
        crs = get_course_by_id("CRS_CS999", db_path=self.test_db)
        self.assertIsNotNone(crs)
        self.assertEqual(crs["weekly_hours"], 4)

        # Invalid faculty reference
        ok, msg = create_course(
            course_id="CRS_BAD",
            code="CS888",
            title="Bad Faculty Test",
            weekly_hours=3,
            assigned_faculty_id="FAC_NON_EXISTENT",
            db_path=self.test_db,
        )
        self.assertFalse(ok)
        self.assertIn("does not exist", msg)

        # Update
        ok, msg = update_course(
            course_id="CRS_CS999",
            code="CS999",
            title="Advanced Quantum Information Theory",
            weekly_hours=5,
            required_room_type="SEMINAR_ROOM",
            category="Theory",
            assigned_faculty_id="FAC_CLAUDE",
            target_group_id="GRP_CS_SEM6",
            db_path=self.test_db,
        )
        self.assertTrue(ok)
        crs_up = get_course_by_id("CRS_CS999", db_path=self.test_db)
        self.assertEqual(crs_up["weekly_hours"], 5)
        self.assertEqual(crs_up["required_room_type"], "SEMINAR_ROOM")

        # Delete
        ok, msg = delete_course("CRS_CS999", db_path=self.test_db)
        self.assertTrue(ok)
        self.assertIsNone(get_course_by_id("CRS_CS999", db_path=self.test_db))

    # ------------------------------------------------------------------------
    # 5. TIMESLOT TESTS
    # ------------------------------------------------------------------------
    def test_timeslot_crud_lifecycle(self) -> None:
        # Create
        ok, msg = create_timeslot(
            slot_id="TS_SAT_1",
            day="Saturday",
            start_time="09:00",
            end_time="10:00",
            duration_minutes=60,
            is_break=False,
            db_path=self.test_db,
        )
        self.assertTrue(ok)
        slot = get_timeslot_by_id("TS_SAT_1", db_path=self.test_db)
        self.assertIsNotNone(slot)
        self.assertEqual(slot["day"], "Saturday")

        # Duplicate same day + start time check
        ok, msg = create_timeslot(
            slot_id="TS_SAT_DUP",
            day="Saturday",
            start_time="09:00",
            end_time="10:30",
            db_path=self.test_db,
        )
        self.assertFalse(ok)
        self.assertIn("already exists", msg)

        # Update
        ok, msg = update_timeslot(
            slot_id="TS_SAT_1",
            day="Saturday",
            start_time="09:30",
            end_time="10:30",
            duration_minutes=60,
            is_break=True,
            db_path=self.test_db,
        )
        self.assertTrue(ok)
        slot_up = get_timeslot_by_id("TS_SAT_1", db_path=self.test_db)
        self.assertEqual(slot_up["start_time"], "09:30")
        self.assertEqual(slot_up["is_break"], 1)

        # Delete
        ok, msg = delete_timeslot("TS_SAT_1", db_path=self.test_db)
        self.assertTrue(ok)
        self.assertIsNone(get_timeslot_by_id("TS_SAT_1", db_path=self.test_db))


if __name__ == "__main__":
    unittest.main()
