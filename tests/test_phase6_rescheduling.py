"""Unit tests for Phase 6: What-If Rescheduling Engine, Conflict Rejection (H1-H4), and Transactional Rollback."""

import os
import sys
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.csp_engine.domain_types import SchedulingAssignmentValue, TimetableStatus
from src.csp_engine.model import CSPModel
from src.database.db_manager import init_db
from src.database.rescheduling_repository import (
    apply_reschedule_transaction,
    get_rescheduling_history,
    rollback_reschedule_transaction,
)
from src.database.timetable_repository import load_saved_timetable, save_timetable_solution
from src.data_management.loader import seed_synthetic_data
from src.ga_engine.genetic_solver import GAConfig, GeneticSolver
from src.optimization.rescheduling_engine import evaluate_what_if_reschedule


class TestPhase6WhatIfRescheduling(unittest.TestCase):
    """Test suite for What-If Rescheduling, H1-H4 Conflict Diagnostics, and Atomic Rollback."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_p6_resched.db")
        init_db(cls.db_path)
        seed_synthetic_data(cls.db_path)

        cls.model = CSPModel.build_from_db(cls.db_path)
        solver = GeneticSolver(cls.model)
        res = solver.solve(GAConfig(population_size=60, max_generations=30, random_seed=42))
        cls.best = res.best_chromosome

        save_timetable_solution(
            cls.best.genes,
            cls.model.variables_map,
            overwrite_existing=True,
            db_path=cls.db_path,
        )
        cls.current_assignment = dict(cls.best.genes)

    def test_01_valid_what_if_proposal(self):
        """Verifies that proposing an available, valid timeslot and room evaluates to feasible."""
        var_id = list(self.current_assignment.keys())[0]
        cur_val = self.current_assignment[var_id]

        # Find an alternative valid slot from the variable's precomputed domain
        domain = self.model.domains[var_id]
        alt_val = None
        for cand in domain:
            if cand.slot_id != cur_val.slot_id:
                # Test candidate
                test_asg = dict(self.current_assignment)
                test_asg[var_id] = cand
                eval_res = evaluate_what_if_reschedule(
                    current_assignment=self.current_assignment,
                    variable_id=var_id,
                    new_room_id=cand.room_id,
                    new_slot_ids=cand.slot_ids,
                    model=self.model,
                )
                if eval_res.is_valid:
                    alt_val = cand
                    break

        if alt_val:
            res = evaluate_what_if_reschedule(
                current_assignment=self.current_assignment,
                variable_id=var_id,
                new_room_id=alt_val.room_id,
                new_slot_ids=alt_val.slot_ids,
                model=self.model,
            )
            self.assertTrue(res.is_valid)
            self.assertTrue(res.is_hard_conflict_free)
            self.assertEqual(len(res.hard_violations), 0)
            self.assertIn("FEASIBLE", res.message)

    def test_02_h1_faculty_overlap_rejection(self):
        """Verifies rejection when rescheduling a session into a slot where its instructor is already teaching."""
        # Find two variables with the SAME faculty member
        f_map = {}
        target_pair = None
        for v_id, val in self.current_assignment.items():
            fid = val.faculty_id
            if fid in f_map:
                target_pair = (f_map[fid], v_id)
                break
            f_map[fid] = v_id

        self.assertIsNotNone(target_pair, "Expected at least two sessions sharing an instructor")
        v1_id, v2_id = target_pair
        val1 = self.current_assignment[v1_id]

        # Deliberately propose assigning v2 to the exact same timeslot as v1
        res = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=v2_id,
            new_room_id="CR_AUD_B",  # different room to isolate faculty clash
            new_slot_ids=val1.slot_ids,
            model=self.model,
        )

        self.assertFalse(res.is_valid, "Expected proposal to be rejected due to faculty conflict")
        self.assertFalse(res.is_hard_conflict_free)
        conflict_types = [v.constraint_id for v in res.hard_violations]
        self.assertTrue(any("H1" in c for c in conflict_types), f"H1 not in {conflict_types}")

    def test_03_h2_classroom_overlap_rejection(self):
        """Verifies rejection when rescheduling a session into a classroom that is already occupied in that slot."""
        var_ids = list(self.current_assignment.keys())
        v1_id, v2_id = var_ids[0], var_ids[1]
        val1 = self.current_assignment[v1_id]

        # Propose moving v2 into v1's classroom during v1's timeslot
        res = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=v2_id,
            new_room_id=val1.room_id,
            new_slot_ids=val1.slot_ids,
            model=self.model,
        )

        self.assertFalse(res.is_valid)
        conflict_types = [v.constraint_id for v in res.hard_violations]
        self.assertTrue(any("H2" in c for c in conflict_types), f"H2 not in {conflict_types}")

    def test_04_h3_student_group_overlap_rejection(self):
        """Verifies rejection when rescheduling a session into a slot where the student cohort already has class."""
        g_map = {}
        target_pair = None
        for v_id, val in self.current_assignment.items():
            gid = val.group_id
            if gid in g_map:
                target_pair = (g_map[gid], v_id)
                break
            g_map[gid] = v_id

        self.assertIsNotNone(target_pair)
        v1_id, v2_id = target_pair
        val1 = self.current_assignment[v1_id]

        # Move v2 to v1's slot in a different room
        alt_room = "CR_LH102" if val1.room_id != "CR_LH102" else "CR_LH101"
        res = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=v2_id,
            new_room_id=alt_room,
            new_slot_ids=val1.slot_ids,
            model=self.model,
        )

        self.assertFalse(res.is_valid)
        conflict_types = [v.constraint_id for v in res.hard_violations]
        self.assertTrue(any("H3" in c for c in conflict_types), f"H3 not in {conflict_types}")

    def test_05_h4_room_capacity_rejection(self):
        """Verifies rejection when placing a large cohort into an undersized classroom."""
        # Find a large group and a small classroom
        var_id = list(self.current_assignment.keys())[0]
        cur_val = self.current_assignment[var_id]

        # Find smallest room capacity
        small_room_id = min(self.model.room_capacities.keys(), key=lambda r: self.model.room_capacities[r])
        small_room_cap = self.model.room_capacities[small_room_id]
        cohort_sz = self.model.group_sizes.get(cur_val.group_id, 0)

        if cohort_sz > small_room_cap:
            res = evaluate_what_if_reschedule(
                current_assignment=self.current_assignment,
                variable_id=var_id,
                new_room_id=small_room_id,
                new_slot_ids=cur_val.slot_ids,
                model=self.model,
            )
            self.assertFalse(res.is_valid)
            conflict_types = [v.constraint_id for v in res.hard_violations]
            self.assertTrue(any("H4" in c for c in conflict_types), f"H4 not in {conflict_types}")

    def test_06_atomic_transaction_and_rollback(self):
        """Verifies that committing a valid reschedule persists in SQLite and can be cleanly rolled back."""
        records_before = load_saved_timetable(db_path=self.db_path)
        target_rec = records_before[0]
        asg_id = target_rec["assignment_id"]
        orig_room = target_rec["room_id"]
        orig_slot = target_rec["slot_id"]

        # Propose target change with real classroom and slot
        new_test_room = "CR_LH102" if orig_room != "CR_LH102" else "CR_LH103"
        new_test_slot = "TS_FRI_5" if orig_slot != "TS_FRI_5" else "TS_THU_5"

        # Apply transaction
        ok, change_id, msg = apply_reschedule_transaction(
            assignment_ids=[asg_id],
            new_room_id=new_test_room,
            new_slot_ids=[new_test_slot],
            reason="Unit Test Reschedule",
            db_path=self.db_path,
        )
        self.assertTrue(ok, f"apply_reschedule_transaction failed: {msg}")
        self.assertTrue(change_id.startswith("CHG_"))

        # Verify update persisted in DB
        records_after = load_saved_timetable(db_path=self.db_path)
        updated_rec = [r for r in records_after if r["assignment_id"] == asg_id][0]
        self.assertEqual(updated_rec["room_id"], new_test_room)
        self.assertEqual(updated_rec["slot_id"], new_test_slot)

        # Verify history recorded
        history = get_rescheduling_history(limit=5, db_path=self.db_path)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]["change_id"], change_id)
        self.assertEqual(history[0]["status"], "COMMITTED")

        # Execute Rollback
        ok_rb, msg_rb = rollback_reschedule_transaction(change_id, db_path=self.db_path)
        self.assertTrue(ok_rb)

        # Verify state reverted to original
        records_restored = load_saved_timetable(db_path=self.db_path)
        reverted_rec = [r for r in records_restored if r["assignment_id"] == asg_id][0]
        self.assertEqual(reverted_rec["room_id"], orig_room)
        self.assertEqual(reverted_rec["slot_id"], orig_slot)

        # Verify history status updated to ROLLED_BACK
        history_updated = get_rescheduling_history(limit=5, db_path=self.db_path)
        self.assertEqual(history_updated[0]["status"], "ROLLED_BACK")

        # Verify second rollback on same change is safely rejected
        ok_rb2, msg_rb2 = rollback_reschedule_transaction(change_id, db_path=self.db_path)
        self.assertFalse(ok_rb2)
        self.assertIn("already been rolled back", msg_rb2)

    def test_07_h5_faculty_unavailability_rejection(self):
        """Verifies rejection when rescheduling a session to a day/slot where faculty is unavailable."""
        # Find a faculty member with restricted days or unavail slots
        # FAC_GRACE has working days MON-THU (no FRI) or check model.faculty_working_days
        target_var_id = None
        target_day = None
        for v_id, val in self.current_assignment.items():
            fid = val.faculty_id
            allowed = self.model.faculty_working_days.get(fid, set())
            # Find a day not in allowed
            all_days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
            disallowed = all_days - allowed
            if disallowed:
                target_var_id = v_id
                target_day = list(disallowed)[0]
                break

        self.assertIsNotNone(target_var_id, "Expected at least one faculty with day restrictions")
        # Find a slot on target_day
        slot_on_target_day = [
            sid for sid, details in self.model.timeslot_details.items()
            if details["day"] == target_day and details.get("is_break", 0) == 0
        ][0]

        cur_val = self.current_assignment[target_var_id]
        res = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=target_var_id,
            new_room_id=cur_val.room_id,
            new_slot_ids=[slot_on_target_day],
            model=self.model,
        )

        self.assertFalse(res.is_valid, "Expected proposal to be rejected due to faculty unavailability")
        conflict_types = [v.constraint_id for v in res.hard_violations]
        self.assertTrue(any("H5" in c for c in conflict_types), f"H5 not in {conflict_types}")

    def test_08_h6_room_type_incompatibility_rejection(self):
        """Verifies rejection when assigning a lab session to a lecture hall or vice versa."""
        # Find a LAB session
        lab_var_id = None
        for v_id, var in self.model.variables_map.items():
            if var.required_room_type == "LAB":
                lab_var_id = v_id
                break

        self.assertIsNotNone(lab_var_id, "Expected at least one LAB variable")
        lab_val = self.current_assignment[lab_var_id]

        # Find a LECTURE_HALL room
        lecture_room = [rid for rid, rtype in self.model.room_types.items() if rtype == "LECTURE_HALL"][0]

        res = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=lab_var_id,
            new_room_id=lecture_room,
            new_slot_ids=lab_val.slot_ids,
            model=self.model,
        )

        self.assertFalse(res.is_valid, "Expected proposal to be rejected due to room type mismatch")
        conflict_types = [v.constraint_id for v in res.hard_violations]
        self.assertTrue(any("H6" in c for c in conflict_types), f"H6 not in {conflict_types}")

    def test_09_h7_lab_continuity_rejection(self):
        """Verifies rejection when multi-hour lab sessions have broken continuity or missing slots."""
        lab_var_id = None
        for v_id, var in self.model.variables_map.items():
            if var.required_room_type == "LAB" and var.duration_hours > 1:
                lab_var_id = v_id
                break

        self.assertIsNotNone(lab_var_id, "Expected a multi-hour LAB variable")
        lab_val = self.current_assignment[lab_var_id]

        # Case A: Non-consecutive slots on same day (e.g. 09:00-10:00 and 11:00-12:00)
        discontinuous_slots = ["TS_MON_1", "TS_MON_3"]
        res = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=lab_var_id,
            new_room_id=lab_val.room_id,
            new_slot_ids=discontinuous_slots,
            model=self.model,
        )

        self.assertFalse(res.is_valid, "Expected rejection for broken lab continuity")
        conflict_types = [v.constraint_id for v in res.hard_violations]
        self.assertTrue(any("H7" in c for c in conflict_types), f"H7 not in {conflict_types}")

        # Case B: Insufficient duration (1 slot for 2-hour lab)
        res_single = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=lab_var_id,
            new_room_id=lab_val.room_id,
            new_slot_ids=["TS_MON_1"],
            model=self.model,
        )
        self.assertFalse(res_single.is_valid)
        conflict_types_single = [v.constraint_id for v in res_single.hard_violations]
        self.assertTrue(any("H7" in c for c in conflict_types_single))

    def test_10_h8_working_hours_and_break_rejection(self):
        """Verifies rejection when assigning a session during an institutional break period."""
        break_slots = [
            sid for sid, details in self.model.timeslot_details.items()
            if details.get("is_break", 0) == 1
        ]
        self.assertGreater(len(break_slots), 0, "Expected institutional break slots to exist")
        break_slot = break_slots[0]

        var_id = list(self.current_assignment.keys())[0]
        cur_val = self.current_assignment[var_id]

        res = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=var_id,
            new_room_id=cur_val.room_id,
            new_slot_ids=[break_slot],
            model=self.model,
        )

        self.assertFalse(res.is_valid, "Expected rejection for scheduling during break period")
        conflict_types = [v.constraint_id for v in res.hard_violations]
        self.assertTrue(any("H8" in c for c in conflict_types), f"H8 not in {conflict_types}")

    def test_11_unrelated_assignments_untouched_on_rollback(self):
        """Verifies that executing a reschedule and rollback does not modify any unrelated assignments."""
        records_initial = load_saved_timetable(db_path=self.db_path)
        self.assertGreater(len(records_initial), 1)

        target_asg_id = records_initial[0]["assignment_id"]
        other_records_before = {
            r["assignment_id"]: (r["room_id"], r["slot_id"])
            for r in records_initial if r["assignment_id"] != target_asg_id
        }

        # Apply transaction
        ok, chg_id, _ = apply_reschedule_transaction(
            assignment_ids=[target_asg_id],
            new_room_id="CR_LH103",
            new_slot_ids=["TS_THU_5"],
            reason="Non-interference test",
            db_path=self.db_path,
        )
        self.assertTrue(ok)

        # Check other records during commit
        records_during = load_saved_timetable(db_path=self.db_path)
        other_records_during = {
            r["assignment_id"]: (r["room_id"], r["slot_id"])
            for r in records_during if r["assignment_id"] != target_asg_id
        }
        self.assertEqual(other_records_before, other_records_during)

        # Rollback
        ok_rb, _ = rollback_reschedule_transaction(chg_id, db_path=self.db_path)
        self.assertTrue(ok_rb)

        # Check other records after rollback
        records_after = load_saved_timetable(db_path=self.db_path)
        other_records_after = {
            r["assignment_id"]: (r["room_id"], r["slot_id"])
            for r in records_after if r["assignment_id"] != target_asg_id
        }
        self.assertEqual(other_records_before, other_records_after)

    def test_12_persistence_across_simulated_restart(self):
        """Verifies that committed reschedule persists after a simulated application restart (new DB connection)."""
        records = load_saved_timetable(db_path=self.db_path)
        target_asg = records[1]
        t_id = target_asg["assignment_id"]

        ok, chg_id, _ = apply_reschedule_transaction(
            assignment_ids=[t_id],
            new_room_id="CR_LH102",
            new_slot_ids=["TS_FRI_5"],
            reason="Persistence test",
            db_path=self.db_path,
        )
        self.assertTrue(ok)

        # Simulate fresh app startup by reloading model and records from disk
        fresh_model = CSPModel.build_from_db(self.db_path)
        fresh_records = load_saved_timetable(db_path=self.db_path)
        persisted = [r for r in fresh_records if r["assignment_id"] == t_id][0]
        self.assertEqual(persisted["room_id"], "CR_LH102")
        self.assertEqual(persisted["slot_id"], "TS_FRI_5")

        # Rollback to keep fixture clean
        rollback_reschedule_transaction(chg_id, db_path=self.db_path)


if __name__ == "__main__":
    unittest.main()
