"""Autonomous QA Audit Test Suite for SmartSched AI Phase 3: Constraint Validation Engine.

Covers:
  - TEST 1: EMPTY TIMETABLE (State, assigned count, 0 hard violations, distinction from complete valid)
  - TEST 2: VALID SAMPLE SCHEDULE (State PARTIAL_VALID, assigned count > 0, 0 hard violations, passes H1-H8, soft penalties computed)
  - TEST 3: INVALID SAMPLE SCHEDULE (State INVALID, H1, H2, H3, H4 detected, identification of variable IDs)
  - TEST 4: DUPLICATE DETECTION (No self-comparison, no duplicate violation records, distinct pair comparison)
  - TEST 5: ALL HARD CONSTRAINTS (H1 to H8 isolated positive and negative test cases)
  - TEST 6: SOFT CONSTRAINTS (S1 to S4 quantitative score triggering verification)
"""

import os
import shutil
import tempfile
import unittest

from src.csp_engine.domain_types import (
    SchedulingAssignmentValue,
    SchedulingVariable,
    SessionType,
    TimetableStatus,
)
from src.csp_engine.hard_constraints import (
    check_h1_faculty_overlap,
    check_h2_classroom_overlap,
    check_h3_student_group_overlap,
    check_h4_room_capacity,
    check_h5_faculty_availability,
    check_h6_room_type,
    check_h7_lab_continuity,
    check_h8_working_hours,
)
from src.csp_engine.model import CSPModel
from src.csp_engine.soft_constraints import (
    score_s1_faculty_preferences,
    score_s2_faculty_idle_gaps,
    score_s3_consecutive_theory_sessions,
    score_s4_balanced_daily_workload,
)
from src.database.db_manager import init_db
from src.data_management.loader import seed_synthetic_data


class TestPhase3ConstraintValidationAudit(unittest.TestCase):
    """Independent technical QA audit for SmartSched AI Phase 3."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "audit_smartsched.db")
        init_db(self.test_db)
        seed_synthetic_data(self.test_db, overwrite=True)
        self.model = CSPModel.build_from_db(self.test_db)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ========================================================================
    # TEST 1: EMPTY TIMETABLE
    # ========================================================================
    def test_audit_1_empty_timetable(self) -> None:
        report = self.model.validate_assignments({})

        # 1. State must strictly be EMPTY
        self.assertEqual(report.status, TimetableStatus.EMPTY)
        # 2. Assigned sessions must be exactly 0
        self.assertEqual(report.assigned_variables, 0)
        # 3. No hard violations
        self.assertEqual(len(report.hard_violations), 0)
        self.assertTrue(report.is_valid)
        # 4. Must NOT be classified as COMPLETE_VALID
        self.assertNotEqual(report.status, TimetableStatus.COMPLETE_VALID)

    # ========================================================================
    # TEST 2: VALID SAMPLE SCHEDULE
    # ========================================================================
    def test_audit_2_valid_sample_schedule(self) -> None:
        sample_assignments = self.model.generate_valid_sample_schedule(num_variables=6)

        # 1. Assigned sessions > 0
        self.assertGreater(len(sample_assignments), 0)
        report = self.model.validate_assignments(sample_assignments)

        # 2. State must be PARTIAL_VALID
        self.assertEqual(report.status, TimetableStatus.PARTIAL_VALID)
        self.assertEqual(report.assigned_variables, len(sample_assignments))

        # 3. Exactly zero hard constraint violations
        self.assertEqual(len(report.hard_violations), 0)
        self.assertTrue(report.is_valid)

        # 4. All H1-H8 checklist entries must report PASS and 0 violations
        for h_id in ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"]:
            h_summary = report.summary_by_constraint.get(h_id)
            self.assertIsNotNone(h_summary, f"Summary missing for {h_id}")
            self.assertEqual(h_summary["violations"], 0, f"{h_id} reported unexpected violations")
            self.assertEqual(h_summary["status"], "PASS")

        # 5. Soft constraint penalties are calculated as numeric float >= 0.0
        self.assertIsInstance(report.soft_penalty_score, float)
        self.assertGreaterEqual(report.soft_penalty_score, 0.0)

    # ========================================================================
    # TEST 3: INVALID SAMPLE SCHEDULE
    # ========================================================================
    def test_audit_3_invalid_sample_schedule(self) -> None:
        invalid_sample = self.model.generate_deliberately_invalid_schedule()
        report = self.model.validate_assignments(invalid_sample)

        # 1. State must be INVALID
        self.assertEqual(report.status, TimetableStatus.INVALID)
        self.assertFalse(report.is_valid)
        self.assertGreater(len(report.hard_violations), 0)

        # 2. H1, H2, H3, H4 must all be detected
        detected_cids = {hv.constraint_id for hv in report.hard_violations}
        self.assertIn("H1", detected_cids, "H1 (Faculty double-booking) was not detected")
        self.assertIn("H2", detected_cids, "H2 (Classroom double-booking) was not detected")
        self.assertIn("H3", detected_cids, "H3 (Student group clash) was not detected")
        self.assertIn("H4", detected_cids, "H4 (Room capacity violation) was not detected")

        # 3. Every pairwise violation (H1, H2, H3) must identify both variable IDs
        for hv in report.hard_violations:
            if hv.constraint_id in ["H1", "H2", "H3"]:
                self.assertEqual(
                    len(hv.violating_var_ids), 2,
                    f"Pairwise conflict {hv.constraint_id} did not identify both variables: {hv.violating_var_ids}",
                )
                self.assertNotEqual(
                    hv.violating_var_ids[0], hv.violating_var_ids[1],
                    "Pairwise violation must identify two distinct variables",
                )

    # ========================================================================
    # TEST 4: DUPLICATE DETECTION AND COMPARISON LOGIC
    # ========================================================================
    def test_audit_4_duplicate_detection_logic(self) -> None:
        invalid_sample = self.model.generate_deliberately_invalid_schedule()
        report = self.model.validate_assignments(invalid_sample)

        # Check for duplicate violation records
        seen_violations = set()
        for hv in report.hard_violations:
            # Unordered variable set key
            v_key = tuple(sorted(hv.violating_var_ids))
            dedup_key = (hv.constraint_id, v_key)
            self.assertNotIn(
                dedup_key, seen_violations,
                f"Duplicate violation report found for constraint {hv.constraint_id} on {v_key}",
            )
            seen_violations.add(dedup_key)

        # Verify that distinct session pairs for the same course are still checked
        # Construct two distinct clashes for same faculty across three sessions
        v1 = SchedulingVariable("VAR_1", "C1", "CS101", 1, 3, SessionType.THEORY, 1, "FAC_CLASH", "GRP_A", "LECTURE_HALL")
        v2 = SchedulingVariable("VAR_2", "C1", "CS101", 2, 3, SessionType.THEORY, 1, "FAC_CLASH", "GRP_B", "LECTURE_HALL")
        v3 = SchedulingVariable("VAR_3", "C1", "CS101", 3, 3, SessionType.THEORY, 1, "FAC_CLASH", "GRP_C", "LECTURE_HALL")
        var_map = {"VAR_1": v1, "VAR_2": v2, "VAR_3": v3}

        val1 = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_CLASH", "GRP_A")
        val2 = SchedulingAssignmentValue("TS_MON_1", "CR_LH102", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_CLASH", "GRP_B")
        val3 = SchedulingAssignmentValue("TS_MON_1", "CR_LH103", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_CLASH", "GRP_C")

        # 3 sessions pairwise = 3 distinct pairs: (1,2), (1,3), (2,3)
        tri_violations = check_h1_faculty_overlap({"VAR_1": val1, "VAR_2": val2, "VAR_3": val3}, var_map)
        self.assertEqual(len(tri_violations), 3)

        reported_pairs = [set(viol.violating_var_ids) for viol in tri_violations]
        self.assertIn({"VAR_1", "VAR_2"}, reported_pairs)
        self.assertIn({"VAR_1", "VAR_3"}, reported_pairs)
        self.assertIn({"VAR_2", "VAR_3"}, reported_pairs)

    # ========================================================================
    # TEST 5: ALL HARD CONSTRAINTS (H1 to H8) INDIVIDUAL ISOLATION
    # ========================================================================
    def test_audit_5_h1_faculty_overlap_isolation(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_A", "LECTURE_HALL")
        v2 = SchedulingVariable("V2", "C2", "CS102", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_B", "LECTURE_HALL")
        var_map = {"V1": v1, "V2": v2}

        # Valid: Different slots
        val1 = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_A")
        val2_ok = SchedulingAssignmentValue("TS_MON_2", "CR_LH102", "Monday", "10:00", "11:00", ("TS_MON_2",), "FAC_A", "GRP_B")
        self.assertEqual(len(check_h1_faculty_overlap({"V1": val1, "V2": val2_ok}, var_map)), 0)

        # Invalid: Same slot
        val2_clash = SchedulingAssignmentValue("TS_MON_1", "CR_LH102", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_B")
        viols = check_h1_faculty_overlap({"V1": val1, "V2": val2_clash}, var_map)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].constraint_id, "H1")

    def test_audit_5_h2_classroom_overlap_isolation(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_A", "LECTURE_HALL")
        v2 = SchedulingVariable("V2", "C2", "CS102", 1, 1, SessionType.THEORY, 1, "FAC_B", "GRP_B", "LECTURE_HALL")
        var_map = {"V1": v1, "V2": v2}

        # Valid: Different slots, same room
        val1 = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_A")
        val2_ok = SchedulingAssignmentValue("TS_MON_2", "CR_LH101", "Monday", "10:00", "11:00", ("TS_MON_2",), "FAC_B", "GRP_B")
        self.assertEqual(len(check_h2_classroom_overlap({"V1": val1, "V2": val2_ok}, var_map)), 0)

        # Invalid: Same room, same slot
        val2_clash = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_B", "GRP_B")
        viols = check_h2_classroom_overlap({"V1": val1, "V2": val2_clash}, var_map)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].constraint_id, "H2")

    def test_audit_5_h3_student_group_overlap_isolation(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_CS4", "LECTURE_HALL")
        v2 = SchedulingVariable("V2", "C2", "CS102", 1, 1, SessionType.THEORY, 1, "FAC_B", "GRP_CS4", "LECTURE_HALL")
        var_map = {"V1": v1, "V2": v2}

        # Valid: Different slots
        val1 = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_CS4")
        val2_ok = SchedulingAssignmentValue("TS_MON_2", "CR_LH102", "Monday", "10:00", "11:00", ("TS_MON_2",), "FAC_B", "GRP_CS4")
        self.assertEqual(len(check_h3_student_group_overlap({"V1": val1, "V2": val2_ok}, var_map)), 0)

        # Invalid: Same group at same slot
        val2_clash = SchedulingAssignmentValue("TS_MON_1", "CR_LH102", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_B", "GRP_CS4")
        viols = check_h3_student_group_overlap({"V1": val1, "V2": val2_clash}, var_map)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].constraint_id, "H3")

    def test_audit_5_h4_room_capacity_isolation(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_CS4", "LECTURE_HALL")
        var_map = {"V1": v1}
        val = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_CS4")

        # Valid: Capacity 60 >= size 50
        self.assertEqual(len(check_h4_room_capacity({"V1": val}, var_map, {"CR_LH101": 60}, {"GRP_CS4": 50})), 0)

        # Invalid: Capacity 40 < size 50
        viols = check_h4_room_capacity({"V1": val}, var_map, {"CR_LH101": 40}, {"GRP_CS4": 50})
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].constraint_id, "H4")

    def test_audit_5_h5_faculty_availability_isolation(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_ALAN", "GRP_CS4", "LECTURE_HALL")
        var_map = {"V1": v1}

        # Valid: Working day Monday, available slot TS_MON_1
        val_ok = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_ALAN", "GRP_CS4")
        unavail = {"FAC_ALAN": {"TS_FRI_5"}}
        days = {"FAC_ALAN": {"Monday", "Tuesday"}}
        self.assertEqual(len(check_h5_faculty_availability({"V1": val_ok}, var_map, unavail, days)), 0)

        # Invalid Day: Wednesday
        val_bad_day = SchedulingAssignmentValue("TS_WED_1", "CR_LH101", "Wednesday", "09:00", "10:00", ("TS_WED_1",), "FAC_ALAN", "GRP_CS4")
        viols_day = check_h5_faculty_availability({"V1": val_bad_day}, var_map, unavail, days)
        self.assertEqual(len(viols_day), 1)

        # Invalid Slot: TS_FRI_5
        days_with_fri = {"FAC_ALAN": {"Monday", "Friday"}}
        val_bad_slot = SchedulingAssignmentValue("TS_FRI_5", "CR_LH101", "Friday", "14:00", "15:00", ("TS_FRI_5",), "FAC_ALAN", "GRP_CS4")
        viols_slot = check_h5_faculty_availability({"V1": val_bad_slot}, var_map, unavail, days_with_fri)
        self.assertEqual(len(viols_slot), 1)

    def test_audit_5_h6_room_type_isolation(self) -> None:
        v_theory = SchedulingVariable("VT", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_A", "LECTURE_HALL")
        v_lab = SchedulingVariable("VL", "C2", "CS102", 1, 1, SessionType.LAB, 2, "FAC_B", "GRP_A", "LAB")
        var_map = {"VT": v_theory, "VL": v_lab}
        room_types = {"CR_LH101": "LECTURE_HALL", "CR_LAB201": "LAB"}

        # Valid assignments
        val_theory = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_A")
        val_lab = SchedulingAssignmentValue("TS_MON_2", "CR_LAB201", "Monday", "10:00", "12:00", ("TS_MON_2", "TS_MON_3"), "FAC_B", "GRP_A")
        self.assertEqual(len(check_h6_room_type({"VT": val_theory, "VL": val_lab}, var_map, room_types)), 0)

        # Invalid assignment: Lab session in Lecture Hall
        val_lab_bad = SchedulingAssignmentValue("TS_MON_2", "CR_LH101", "Monday", "10:00", "12:00", ("TS_MON_2", "TS_MON_3"), "FAC_B", "GRP_A")
        viols = check_h6_room_type({"VL": val_lab_bad}, var_map, room_types)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].constraint_id, "H6")

    def test_audit_5_h7_lab_continuity_isolation(self) -> None:
        v_lab = SchedulingVariable("VL", "C1", "CS204", 1, 1, SessionType.LAB, 2, "FAC_A", "GRP_A", "LAB")
        var_map = {"VL": v_lab}

        slot_details = {
            "TS_1": {"day": "Monday", "start_time": "09:00", "end_time": "10:00"},
            "TS_2": {"day": "Monday", "start_time": "10:00", "end_time": "11:00"},
            "TS_3": {"day": "Monday", "start_time": "14:00", "end_time": "15:00"},
        }

        # Valid continuous slots: 09:00-10:00 and 10:00-11:00
        val_cont = SchedulingAssignmentValue("TS_1", "CR_LAB201", "Monday", "09:00", "11:00", ("TS_1", "TS_2"), "FAC_A", "GRP_A")
        self.assertEqual(len(check_h7_lab_continuity({"VL": val_cont}, var_map, slot_details)), 0)

        # Discontinuous: 09:00-10:00 and 14:00-15:00
        val_discont = SchedulingAssignmentValue("TS_1", "CR_LAB201", "Monday", "09:00", "15:00", ("TS_1", "TS_3"), "FAC_A", "GRP_A")
        viols = check_h7_lab_continuity({"VL": val_discont}, var_map, slot_details)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].constraint_id, "H7")

    def test_audit_5_h8_working_hours_and_breaks_isolation(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_A", "LECTURE_HALL")
        var_map = {"V1": v1}

        slot_details = {
            "TS_CLASS": {"day": "Monday", "start_time": "09:00", "end_time": "10:00", "is_break": 0},
            "TS_LUNCH": {"day": "Monday", "start_time": "12:00", "end_time": "13:00", "is_break": 1},
        }

        # Valid regular slot
        val_ok = SchedulingAssignmentValue("TS_CLASS", "CR_LH101", "Monday", "09:00", "10:00", ("TS_CLASS",), "FAC_A", "GRP_A")
        self.assertEqual(len(check_h8_working_hours({"V1": val_ok}, var_map, slot_details)), 0)

        # Scheduled during lunch break
        val_break = SchedulingAssignmentValue("TS_LUNCH", "CR_LH101", "Monday", "12:00", "13:00", ("TS_LUNCH",), "FAC_A", "GRP_A")
        viols = check_h8_working_hours({"V1": val_break}, var_map, slot_details)
        self.assertEqual(len(viols), 1)
        self.assertEqual(viols[0].constraint_id, "H8")

    # ========================================================================
    # TEST 6: SOFT CONSTRAINTS (S1 to S4) QUANTITATIVE SCORING
    # ========================================================================
    def test_audit_6_soft_constraints_scoring(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_1", "LECTURE_HALL")
        v2 = SchedulingVariable("V2", "C2", "CS102", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_1", "LECTURE_HALL")
        v3 = SchedulingVariable("V3", "C3", "CS103", 1, 1, SessionType.THEORY, 1, "FAC_B", "GRP_1", "LECTURE_HALL")
        var_map = {"V1": v1, "V2": v2, "V3": v3}

        # S1: Late afternoon penalty (>14:00)
        val_late = SchedulingAssignmentValue("TS_5", "CR_LH101", "Monday", "14:00", "15:00", ("TS_5",), "FAC_A", "GRP_1")
        p1, viols1 = score_s1_faculty_preferences({"V1": val_late}, var_map)
        self.assertEqual(p1, 5.0)
        self.assertEqual(len(viols1), 1)
        self.assertEqual(viols1[0].constraint_id, "S1")

        # S2: Idle gaps > 60 mins between faculty sessions on same day
        val_early = SchedulingAssignmentValue("TS_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_1",), "FAC_A", "GRP_1")
        # 10:00 to 14:00 = 240 mins gap
        p2, viols2 = score_s2_faculty_idle_gaps({"V1": val_early, "V2": val_late}, var_map)
        self.assertGreater(p2, 0.0)
        self.assertEqual(len(viols2), 1)
        self.assertEqual(viols2[0].constraint_id, "S2")

        # S3: Consecutive heavy theory sessions (>= 3 contiguous hours)
        s_val1 = SchedulingAssignmentValue("S1", "CR_LH101", "Monday", "09:00", "10:00", ("S1",), "FAC_A", "GRP_1")
        s_val2 = SchedulingAssignmentValue("S2", "CR_LH101", "Monday", "10:00", "11:00", ("S2",), "FAC_A", "GRP_1")
        s_val3 = SchedulingAssignmentValue("S3", "CR_LH101", "Monday", "11:00", "12:00", ("S3",), "FAC_B", "GRP_1")
        p3, viols3 = score_s3_consecutive_theory_sessions({"V1": s_val1, "V2": s_val2, "V3": s_val3}, var_map)
        self.assertGreater(p3, 0.0)
        self.assertEqual(len(viols3), 1)
        self.assertEqual(viols3[0].constraint_id, "S3")

        # S4: Daily student workload balance (> 4 hours on single day)
        v4 = SchedulingVariable("V4", "C4", "CS104", 1, 1, SessionType.THEORY, 1, "FAC_C", "GRP_1", "LECTURE_HALL")
        v5 = SchedulingVariable("V5", "C5", "CS105", 1, 1, SessionType.THEORY, 1, "FAC_D", "GRP_1", "LECTURE_HALL")
        var_map_5 = dict(var_map)
        var_map_5.update({"V4": v4, "V5": v5})
        s_val4 = SchedulingAssignmentValue("S4", "CR_LH101", "Monday", "14:00", "15:00", ("S4",), "FAC_C", "GRP_1")
        s_val5 = SchedulingAssignmentValue("S5", "CR_LH101", "Monday", "15:00", "16:00", ("S5",), "FAC_D", "GRP_1")
        five_sessions = {"V1": s_val1, "V2": s_val2, "V3": s_val3, "V4": s_val4, "V5": s_val5}
        p4, viols4 = score_s4_balanced_daily_workload(five_sessions, var_map_5)
        self.assertGreater(p4, 0.0)
        self.assertEqual(len(viols4), 1)
        self.assertEqual(viols4[0].constraint_id, "S4")


if __name__ == "__main__":
    unittest.main()
