"""Comprehensive unit tests for CSP Problem Formulation, Domains, Hard Constraints H1-H8, and Timetable State Reporting."""

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
from src.csp_engine.generator import generate_domains_from_db, generate_variables_from_db
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


class TestCSPFormulationAndValidation(unittest.TestCase):
    """Test suite verifying variable creation, domain filtering, constraint evaluators, and debugging scenarios."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_smartsched.db")
        init_db(self.test_db)
        seed_synthetic_data(self.test_db, overwrite=True)
        self.model = CSPModel.build_from_db(self.test_db)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ------------------------------------------------------------------------
    # 1. Variable Generation
    # ------------------------------------------------------------------------
    def test_variable_generation_from_db(self) -> None:
        variables = generate_variables_from_db(self.test_db)
        self.assertGreater(len(variables), 0)

        # CS201 is 3 weekly hours theory -> should yield 3 theory variables of 1 hour
        cs201_vars = [v for v in variables if v.course_code == "CS201"]
        self.assertEqual(len(cs201_vars), 3)
        for v in cs201_vars:
            self.assertEqual(v.duration_hours, 1)
            self.assertEqual(v.session_type, SessionType.THEORY)

        # CS204 is 2 weekly hours practical lab -> should yield 1 lab variable of 2 hours
        cs204_vars = [v for v in variables if v.course_code == "CS204"]
        self.assertEqual(len(cs204_vars), 1)
        self.assertEqual(cs204_vars[0].duration_hours, 2)
        self.assertEqual(cs204_vars[0].session_type, SessionType.LAB)

    # ------------------------------------------------------------------------
    # 2. Domain Generation & Pre-filtering
    # ------------------------------------------------------------------------
    def test_domain_generation_and_prefiltering(self) -> None:
        variables = generate_variables_from_db(self.test_db)
        domains = generate_domains_from_db(variables, self.test_db)

        self.assertEqual(len(domains), len(variables))
        for v in variables:
            dom = domains[v.var_id]
            self.assertGreater(len(dom), 0, f"Domain for {v.var_id} should not be empty")

            # Check lab continuity: all lab assignments must have length == 2
            if v.session_type == SessionType.LAB and v.duration_hours == 2:
                for val in dom:
                    self.assertEqual(len(val.slot_ids), 2)

    # ------------------------------------------------------------------------
    # 3. H1: Faculty Overlap
    # ------------------------------------------------------------------------
    def test_h1_faculty_overlap_detection(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 2, SessionType.THEORY, 1, "FAC_A", "GRP_1", "LECTURE_HALL")
        v2 = SchedulingVariable("V2", "C1", "CS101", 2, 2, SessionType.THEORY, 1, "FAC_A", "GRP_2", "LECTURE_HALL")
        var_map = {"V1": v1, "V2": v2}

        # Conflicting assignment: same faculty, same day, same slot
        val1 = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_1")
        val2 = SchedulingAssignmentValue("TS_MON_1", "CR_LH102", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_2")

        violations = check_h1_faculty_overlap({"V1": val1, "V2": val2}, var_map)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].constraint_id, "H1")
        # Ensure unique IDs and session labels are reported
        self.assertIn("CS101-S1 (V1)", violations[0].explanation)
        self.assertIn("CS101-S2 (V2)", violations[0].explanation)

        # Non-conflicting: different slots
        val2_ok = SchedulingAssignmentValue("TS_MON_2", "CR_LH102", "Monday", "10:00", "11:00", ("TS_MON_2",), "FAC_A", "GRP_2")
        violations_ok = check_h1_faculty_overlap({"V1": val1, "V2": val2_ok}, var_map)
        self.assertEqual(len(violations_ok), 0)

    # ------------------------------------------------------------------------
    # 4. H2: Classroom Overlap
    # ------------------------------------------------------------------------
    def test_h2_classroom_overlap_detection(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_1", "LECTURE_HALL")
        v2 = SchedulingVariable("V2", "C2", "CS102", 1, 1, SessionType.THEORY, 1, "FAC_B", "GRP_2", "LECTURE_HALL")
        var_map = {"V1": v1, "V2": v2}

        val1 = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_1")
        val2 = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_B", "GRP_2")

        violations = check_h2_classroom_overlap({"V1": val1, "V2": val2}, var_map)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].constraint_id, "H2")

    # ------------------------------------------------------------------------
    # 5. H3: Student Group Clash
    # ------------------------------------------------------------------------
    def test_h3_student_group_overlap_detection(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_1", "LECTURE_HALL")
        v2 = SchedulingVariable("V2", "C2", "CS102", 1, 1, SessionType.THEORY, 1, "FAC_B", "GRP_1", "LECTURE_HALL")
        var_map = {"V1": v1, "V2": v2}

        val1 = SchedulingAssignmentValue("TS_TUE_1", "CR_LH101", "Tuesday", "09:00", "10:00", ("TS_TUE_1",), "FAC_A", "GRP_1")
        val2 = SchedulingAssignmentValue("TS_TUE_1", "CR_LH102", "Tuesday", "09:00", "10:00", ("TS_TUE_1",), "FAC_B", "GRP_1")

        violations = check_h3_student_group_overlap({"V1": val1, "V2": val2}, var_map)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].constraint_id, "H3")

    # ------------------------------------------------------------------------
    # 6. H4: Room Capacity Validation
    # ------------------------------------------------------------------------
    def test_h4_room_capacity_validation(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_LARGE", "LECTURE_HALL")
        var_map = {"V1": v1}
        val = SchedulingAssignmentValue("TS_MON_1", "CR_SMALL", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_LARGE")

        # Capacity 40, size 60 -> violation
        violations = check_h4_room_capacity({"V1": val}, var_map, {"CR_SMALL": 40}, {"GRP_LARGE": 60})
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].constraint_id, "H4")

        # Capacity 70, size 60 -> valid
        violations_ok = check_h4_room_capacity({"V1": val}, var_map, {"CR_SMALL": 70}, {"GRP_LARGE": 60})
        self.assertEqual(len(violations_ok), 0)

    # ------------------------------------------------------------------------
    # 7. H5: Faculty Availability Validation
    # ------------------------------------------------------------------------
    def test_h5_faculty_availability_validation(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_1", "LECTURE_HALL")
        var_map = {"V1": v1}

        val = SchedulingAssignmentValue("TS_FRI_4", "CR_LH101", "Friday", "14:00", "15:00", ("TS_FRI_4",), "FAC_A", "GRP_1")
        unavail = {"FAC_A": {"TS_FRI_4"}}
        days = {"FAC_A": {"Monday", "Friday"}}

        violations = check_h5_faculty_availability({"V1": val}, var_map, unavail, days)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].constraint_id, "H5")

    # ------------------------------------------------------------------------
    # 8. H6: Room Type Matching
    # ------------------------------------------------------------------------
    def test_h6_room_type_matching(self) -> None:
        v_lab = SchedulingVariable("V_LAB", "C1", "CS204", 1, 1, SessionType.LAB, 2, "FAC_A", "GRP_1", "LAB")
        var_map = {"V_LAB": v_lab}

        # Put lab into a lecture hall -> violation
        val_bad = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "11:00", ("TS_MON_1", "TS_MON_2"), "FAC_A", "GRP_1")
        violations = check_h6_room_type({"V_LAB": val_bad}, var_map, {"CR_LH101": "LECTURE_HALL", "CR_LAB201": "LAB"})
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].constraint_id, "H6")

    # ------------------------------------------------------------------------
    # 9. H7: Lab Slot Continuity
    # ------------------------------------------------------------------------
    def test_h7_lab_slot_continuity(self) -> None:
        v_lab = SchedulingVariable("V_LAB", "C1", "CS204", 1, 1, SessionType.LAB, 2, "FAC_A", "GRP_1", "LAB")
        var_map = {"V_LAB": v_lab}

        slots_meta = {
            "TS_MON_1": {"day": "Monday", "start_time": "09:00", "end_time": "10:00"},
            "TS_MON_2": {"day": "Monday", "start_time": "10:00", "end_time": "11:00"},
            "TS_MON_4": {"day": "Monday", "start_time": "14:00", "end_time": "15:00"},
        }

        # Non-continuous: 09:00-10:00 and 14:00-15:00
        val_discontinuous = SchedulingAssignmentValue(
            "TS_MON_1", "CR_LAB201", "Monday", "09:00", "15:00", ("TS_MON_1", "TS_MON_4"), "FAC_A", "GRP_1"
        )
        violations = check_h7_lab_continuity({"V_LAB": val_discontinuous}, var_map, slots_meta)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].constraint_id, "H7")

    # ------------------------------------------------------------------------
    # 10. H8: Working Hours & Breaks
    # ------------------------------------------------------------------------
    def test_h8_working_hours_and_breaks(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_1", "LECTURE_HALL")
        var_map = {"V1": v1}

        # TS_MON_4 is marked as break
        slots_meta = {
            "TS_MON_4": {"day": "Monday", "start_time": "12:00", "end_time": "13:00", "is_break": 1},
        }
        val = SchedulingAssignmentValue("TS_MON_4", "CR_LH101", "Monday", "12:00", "13:00", ("TS_MON_4",), "FAC_A", "GRP_1")
        violations = check_h8_working_hours({"V1": val}, var_map, slots_meta)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].constraint_id, "H8")

    # ------------------------------------------------------------------------
    # 11. Soft Constraints S1 - S4
    # ------------------------------------------------------------------------
    def test_soft_constraints_scoring(self) -> None:
        v1 = SchedulingVariable("V1", "C1", "CS101", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_1", "LECTURE_HALL")
        v2 = SchedulingVariable("V2", "C2", "CS102", 1, 1, SessionType.THEORY, 1, "FAC_A", "GRP_1", "LECTURE_HALL")
        var_map = {"V1": v1, "V2": v2}

        # S1: Afternoon slot penalization (14:00)
        val_afternoon = SchedulingAssignmentValue("TS_MON_5", "CR_LH101", "Monday", "14:00", "15:00", ("TS_MON_5",), "FAC_A", "GRP_1")
        p1, viol1 = score_s1_faculty_preferences({"V1": val_afternoon}, var_map)
        self.assertGreater(p1, 0.0)

        # S2: Idle gaps check
        val_morning = SchedulingAssignmentValue("TS_MON_1", "CR_LH101", "Monday", "09:00", "10:00", ("TS_MON_1",), "FAC_A", "GRP_1")
        p2, viol2 = score_s2_faculty_idle_gaps({"V1": val_morning, "V2": val_afternoon}, var_map)
        self.assertGreater(p2, 0.0)

    # ------------------------------------------------------------------------
    # 12. BUG 1 Verification: Deliberately Invalid Schedule Detects H1, H2, H3, H4
    # ------------------------------------------------------------------------
    def test_deliberately_invalid_schedule_detects_h1_h2_h3_h4(self) -> None:
        invalid_sample = self.model.generate_deliberately_invalid_schedule()
        report = self.model.validate_assignments(invalid_sample)

        self.assertFalse(report.is_valid)
        self.assertEqual(report.status, TimetableStatus.INVALID)

        detected_constraints = {v.constraint_id for v in report.hard_violations}
        self.assertIn("H1", detected_constraints, "H1 (Faculty double-booking) must be detected")
        self.assertIn("H2", detected_constraints, "H2 (Classroom double-booking) must be detected")
        self.assertIn("H3", detected_constraints, "H3 (Student group clash) must be detected")
        self.assertIn("H4", detected_constraints, "H4 (Room capacity violation) must be detected")

    # ------------------------------------------------------------------------
    # 13. BUG 2 Verification: Valid Sample Schedule has Exactly Zero Violations
    # ------------------------------------------------------------------------
    def test_valid_sample_schedule_has_zero_violations(self) -> None:
        valid_sample = self.model.generate_valid_sample_schedule(num_variables=5)
        self.assertEqual(len(valid_sample), 5)

        report = self.model.validate_assignments(valid_sample)
        self.assertTrue(report.is_valid, f"Expected valid sample to be valid, but got violations: {report.hard_violations}")
        self.assertEqual(len(report.hard_violations), 0)
        self.assertEqual(report.status, TimetableStatus.PARTIAL_VALID)

    # ------------------------------------------------------------------------
    # 14. BUG 3 Verification: No Duplicate Violations and Distinct Variable Identification
    # ------------------------------------------------------------------------
    def test_distinct_pair_comparison_and_no_self_comparison(self) -> None:
        invalid_sample = self.model.generate_deliberately_invalid_schedule()
        report = self.model.validate_assignments(invalid_sample)

        # Ensure no violation lists the exact same variable ID twice (var1 == var2)
        for hv in report.hard_violations:
            if len(hv.violating_var_ids) >= 2:
                self.assertNotEqual(hv.violating_var_ids[0], hv.violating_var_ids[1])
                # Ensure explanation distinguishes session numbers or variable IDs
                self.assertTrue(
                    "-S" in hv.explanation or "(" in hv.explanation,
                    f"Violation explanation should distinguish variables: {hv.explanation}",
                )

    # ------------------------------------------------------------------------
    # 15. BUG 4 Verification: Timetable State Classification
    # ------------------------------------------------------------------------
    def test_timetable_state_distinction(self) -> None:
        # State 1: EMPTY
        rep_empty = self.model.validate_assignments({})
        self.assertTrue(rep_empty.is_valid)
        self.assertEqual(rep_empty.status, TimetableStatus.EMPTY)

        # State 2: PARTIAL_VALID
        valid_sample = self.model.generate_valid_sample_schedule(num_variables=4)
        rep_partial = self.model.validate_assignments(valid_sample)
        self.assertTrue(rep_partial.is_valid)
        self.assertEqual(rep_partial.status, TimetableStatus.PARTIAL_VALID)

        # State 3: INVALID
        invalid_sample = self.model.generate_deliberately_invalid_schedule()
        rep_invalid = self.model.validate_assignments(invalid_sample)
        self.assertFalse(rep_invalid.is_valid)
        self.assertEqual(rep_invalid.status, TimetableStatus.INVALID)


if __name__ == "__main__":
    unittest.main()
