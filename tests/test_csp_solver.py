"""Comprehensive Unit and Integration Test Suite for SmartSched AI Phase 4: CSP Solver.

Covers all 19 Phase 4 requirements:
  1. Basic backtracking solution on solvable academic problem.
  2. Backtracking after a forced dead end.
  3. MRV dynamically selecting the smallest legal domain.
  4. Degree heuristic breaking MRV ties.
  5. LCV ordering values by least constraining impact.
  6. Forward checking pruning incompatible neighbor values.
  7. Forward checking detecting empty domains (wipeout).
  8. AC-3 removing unsupported values from arcs.
  9. AC-3 detecting domain wipeouts before search.
  10. Domain restoration via trail on backtrack.
  11. Infeasible problem returns SolverStatus.INFEASIBLE.
  12. Empty CSP returns SolverStatus.EMPTY_PROBLEM.
  13. Search node limit triggering SolverStatus.NODE_LIMIT_REACHED.
  14. Timeout triggering SolverStatus.TIMEOUT.
  15. Complete timetable validation against CSPModel.validate_assignments (H1-H8 zero violations).
  16. Soft penalty calculation (S1-S4 non-negative numeric scores).
  17. SQLite timetable persistence (save_timetable_solution & load_saved_timetable).
  18. No duplicate schedule records and clean overwrite behavior.
  19. Full regression check of all Phase 1-3 functionality.
"""

import os
import shutil
import tempfile
import unittest
from typing import Dict, List, Set, Tuple

from src.csp_engine.domain_types import (
    SchedulingAssignmentValue,
    SchedulingVariable,
    SessionType,
    TimetableStatus,
)
from src.csp_engine.generator import generate_domains_from_db, generate_variables_from_db
from src.csp_engine.model import CSPModel
from src.csp_engine.solver import CSPSolver, values_are_compatible
from src.csp_engine.solver_types import (
    SolverConfig,
    SolverResult,
    SolverStatistics,
    SolverStatus,
)
from src.database.db_manager import get_db_connection, init_db
from src.database.timetable_repository import (
    load_saved_timetable,
    save_timetable_solution,
)
from src.data_management.loader import load_dataset_summary, seed_synthetic_data


def make_var(
    var_id: str,
    course_code: str = "CS101",
    faculty_id: str = "FAC1",
    group_id: str = "GRP1",
    room_type: str = "LECTURE_HALL",
) -> SchedulingVariable:
    """Helper to construct a valid SchedulingVariable for testing."""
    return SchedulingVariable(
        var_id=var_id,
        course_id=f"CRS_{course_code}",
        course_code=course_code,
        session_num=1,
        total_sessions=1,
        session_type=SessionType.THEORY,
        duration_hours=1,
        faculty_id=faculty_id,
        group_id=group_id,
        required_room_type=room_type,
    )


def make_val(
    slot_id: str,
    room_id: str,
    day: str,
    start_time: str,
    end_time: str,
    faculty_id: str,
    group_id: str,
) -> SchedulingAssignmentValue:
    """Helper to construct a valid SchedulingAssignmentValue for testing."""
    return SchedulingAssignmentValue(
        slot_id=slot_id,
        room_id=room_id,
        day=day,
        start_time=start_time,
        end_time=end_time,
        slot_ids=(slot_id,),
        faculty_id=faculty_id,
        group_id=group_id,
    )


class TestCSPSolverPhase4(unittest.TestCase):
    """Independent technical QA test suite for SmartSched AI Phase 4 CSP Solver."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_smartsched.db")
        init_db(self.test_db)
        seed_synthetic_data(self.test_db, overwrite=True)
        self.model = CSPModel.build_from_db(self.test_db)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ========================================================================
    # 1. Basic Backtracking Solution on Solvable Academic Problem
    # ========================================================================
    def test_01_basic_backtracking_solvable(self) -> None:
        solver = CSPSolver(self.model)
        config = SolverConfig(
            use_mrv=True,
            use_degree=True,
            use_lcv=True,
            use_forward_checking=True,
            use_ac3_preprocess=True,
            use_incremental_ac3=False,
            max_search_nodes=50000,
            timeout_seconds=30.0,
        )
        result = solver.solve(config)

        self.assertEqual(result.status, SolverStatus.SUCCESS)
        self.assertTrue(result.is_solution_found)
        self.assertEqual(len(result.assignment), len(self.model.variables))
        self.assertIsNotNone(result.validation_report)
        self.assertTrue(result.validation_report.is_valid)
        self.assertEqual(len(result.validation_report.hard_violations), 0)

    # ========================================================================
    # 2. Backtracking After a Forced Dead End
    # ========================================================================
    def test_02_backtracking_after_forced_dead_end(self) -> None:
        # V1 and V2 share faculty FAC1
        var1 = make_var("V1", course_code="CS101", faculty_id="FAC1", group_id="GRP1")
        var2 = make_var("V2", course_code="CS102", faculty_id="FAC1", group_id="GRP2")

        val_slot1 = make_val("SLOT1", "ROOM1", "Monday", "09:00", "10:00", "FAC1", "GRP1")
        val_slot2 = make_val("SLOT2", "ROOM1", "Monday", "10:00", "11:00", "FAC1", "GRP1")
        val2_slot1 = make_val("SLOT1", "ROOM2", "Monday", "09:00", "10:00", "FAC1", "GRP2")

        # Domain of V1 has [val_slot1, val_slot2]
        # Domain of V2 ONLY has [val2_slot1]
        # If V1 chooses val_slot1, V2 has no compatible value (dead end due to same faculty & time).
        # Solver must backtrack and try val_slot2, which succeeds.
        custom_model = CSPModel(
            variables=[var1, var2],
            domains={"V1": [val_slot1, val_slot2], "V2": [val2_slot1]},
            room_capacities={"ROOM1": 100, "ROOM2": 100},
            room_types={"ROOM1": "LECTURE_HALL", "ROOM2": "LECTURE_HALL"},
            group_sizes={"GRP1": 30, "GRP2": 30},
            faculty_working_days={"FAC1": {"Monday"}},
            faculty_unavailability={"FAC1": set()},
            timeslot_details={
                "SLOT1": {"slot_id": "SLOT1", "day": "Monday", "start_time": "09:00", "end_time": "10:00", "is_break": 0},
                "SLOT2": {"slot_id": "SLOT2", "day": "Monday", "start_time": "10:00", "end_time": "11:00", "is_break": 0},
            },
        )

        solver = CSPSolver(custom_model)
        config = SolverConfig(
            use_mrv=False,
            use_degree=False,
            use_lcv=False,
            use_forward_checking=False,
            use_ac3_preprocess=False,
        )
        result = solver.solve(config)

        self.assertEqual(result.status, SolverStatus.SUCCESS)
        self.assertTrue(result.is_solution_found)
        self.assertEqual(result.assignment["V1"], val_slot2)
        self.assertEqual(result.assignment["V2"], val2_slot1)
        self.assertGreaterEqual(result.statistics.backtracks, 1)

    # ========================================================================
    # 3. MRV Dynamically Selecting Smallest Legal Domain
    # ========================================================================
    def test_03_mrv_dynamic_variable_selection(self) -> None:
        solver = CSPSolver(self.model)
        solver.config = SolverConfig(use_mrv=True, use_degree=False)

        assignment: Dict[str, SchedulingAssignmentValue] = {}
        working_domains: Dict[str, List[SchedulingAssignmentValue]] = {
            v.var_id: [None] * 10 for v in self.model.variables  # type: ignore
        }
        # Force one variable to have domain size 2
        target_var = self.model.variables[2].var_id
        working_domains[target_var] = [None, None]  # type: ignore

        adj_graph = solver._build_adjacency_graph(self.model.variables)
        chosen_var = solver.select_unassigned_variable(assignment, working_domains, adj_graph)

        self.assertEqual(chosen_var, target_var)

    # ========================================================================
    # 4. Degree Heuristic Breaking MRV Ties
    # ========================================================================
    def test_04_degree_heuristic_breaking_mrv_ties(self) -> None:
        var_a = make_var("VA")
        var_b = make_var("VB")
        var_c = make_var("VC")

        custom_model = CSPModel(
            variables=[var_a, var_b, var_c],
            domains={"VA": [1, 2], "VB": [1, 2], "VC": [1, 2, 3]},  # type: ignore
        )
        solver = CSPSolver(custom_model)
        solver.config = SolverConfig(use_mrv=True, use_degree=True)

        # Both VA and VB have domain size 2 (tied for MRV).
        # adj_graph gives VA 2 neighbors (VB, VC) and VB only 0 neighbors.
        adj_graph = {"VA": {"VB", "VC"}, "VB": set(), "VC": {"VA"}}
        working_domains = {"VA": [1, 2], "VB": [1, 2], "VC": [1, 2, 3]}  # type: ignore
        assignment: Dict[str, SchedulingAssignmentValue] = {}

        chosen = solver.select_unassigned_variable(assignment, working_domains, adj_graph)
        self.assertEqual(chosen, "VA", "Degree heuristic must choose VA with more unassigned neighbors")

    # ========================================================================
    # 5. LCV Ordering Values by Least Constraining Impact
    # ========================================================================
    def test_05_lcv_orders_values_least_constraining(self) -> None:
        # Candidate values for V1:
        # val_a conflicts with 3 neighbor values on Monday SLOT1
        # val_b conflicts with 0 neighbor values on Tuesday SLOT_TUE1
        val_a = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F1", "G1")
        val_b = make_val("SLOT_TUE1", "R1", "Tuesday", "09:00", "10:00", "F1", "G1")

        # Neighbor V2 on Monday has 3 values sharing Slot 1 & Room R1
        n_vals = [
            make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F2", "G2"),
            make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F3", "G3"),
            make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F4", "G4"),
        ]

        var1 = make_var("V1", faculty_id="F1", group_id="G1")
        var2 = make_var("V2", faculty_id="F2", group_id="G2")

        custom_model = CSPModel(
            variables=[var1, var2],
            domains={"V1": [val_a, val_b], "V2": n_vals},
        )
        solver = CSPSolver(custom_model)
        solver.config = SolverConfig(use_lcv=True)
        adj_graph = {"V1": {"V2"}, "V2": {"V1"}}
        working_domains = {"V1": [val_a, val_b], "V2": n_vals}

        ordered = solver.order_domain_values("V1", working_domains, adj_graph)
        self.assertEqual(ordered[0], val_b, "LCV must order val_b (0 eliminations) before val_a (3 eliminations)")

    # ========================================================================
    # 6. Forward Checking Prunes Incompatible Neighbor Values
    # ========================================================================
    def test_06_forward_checking_prunes_incompatible_neighbors(self) -> None:
        val1 = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F1", "G1")
        val2_compat = make_val("SLOT_TUE1", "R1", "Tuesday", "09:00", "10:00", "F1", "G2")
        val2_incompat = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F1", "G2")

        solver = CSPSolver(self.model)
        working_domains = {
            "V1": [val1],
            "V2": [val2_compat, val2_incompat],
        }
        adj_graph = {"V1": {"V2"}, "V2": {"V1"}}
        domain_trail: List[Tuple[str, SchedulingAssignmentValue]] = []
        assignment: Dict[str, SchedulingAssignmentValue] = {}

        ok = solver.forward_check("V1", val1, assignment, working_domains, adj_graph, domain_trail)

        self.assertTrue(ok)
        self.assertEqual(working_domains["V2"], [val2_compat])
        self.assertEqual(len(domain_trail), 1)
        self.assertEqual(domain_trail[0], ("V2", val2_incompat))

    # ========================================================================
    # 7. Forward Checking Detects Empty Domains (Wipeout)
    # ========================================================================
    def test_07_forward_checking_detects_empty_domains_wipeout(self) -> None:
        val1 = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F1", "G1")
        val2_incompat = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F1", "G2")

        solver = CSPSolver(self.model)
        working_domains = {
            "V1": [val1],
            "V2": [val2_incompat],
        }
        adj_graph = {"V1": {"V2"}, "V2": {"V1"}}
        domain_trail: List[Tuple[str, SchedulingAssignmentValue]] = []
        assignment: Dict[str, SchedulingAssignmentValue] = {}

        ok = solver.forward_check("V1", val1, assignment, working_domains, adj_graph, domain_trail)

        self.assertFalse(ok, "Forward checking must immediately return False upon domain wipeout")

    # ========================================================================
    # 8. AC-3 Removing Unsupported Values from Arcs
    # ========================================================================
    def test_08_ac3_removes_unsupported_values(self) -> None:
        val_overlap = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F1", "G1")
        val_compat_v1 = make_val("SLOT_TUE1", "R1", "Tuesday", "09:00", "10:00", "F1", "G1")
        val_v2 = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F2", "G2")

        solver = CSPSolver(self.model)
        working_domains = {
            "V1": [val_overlap, val_compat_v1],
            "V2": [val_v2],
        }
        adj_graph = {"V1": {"V2"}, "V2": {"V1"}}

        revised, wiped_out = solver._revise("V1", "V2", working_domains, domain_trail=None)

        self.assertTrue(revised)
        self.assertFalse(wiped_out)
        self.assertIn(val_compat_v1, working_domains["V1"])
        self.assertNotIn(val_overlap, working_domains["V1"])

    # ========================================================================
    # 9. AC-3 Detecting Domain Wipeouts Before Search
    # ========================================================================
    def test_09_ac3_detects_domain_wipeouts_before_search(self) -> None:
        # Two variables requiring the exact same faculty at the exact same timeslot
        val1 = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "FAC_SHARED", "G1")
        val2 = make_val("SLOT1", "R2", "Monday", "09:00", "10:00", "FAC_SHARED", "G2")

        var1 = make_var("V1", faculty_id="FAC_SHARED", group_id="G1")
        var2 = make_var("V2", faculty_id="FAC_SHARED", group_id="G2")

        custom_model = CSPModel(
            variables=[var1, var2],
            domains={"V1": [val1], "V2": [val2]},
        )

        solver = CSPSolver(custom_model)
        config = SolverConfig(use_ac3_preprocess=True)
        result = solver.solve(config)

        self.assertEqual(result.status, SolverStatus.INFEASIBLE)
        self.assertFalse(result.is_solution_found)
        self.assertIn("AC-3", result.message)

    # ========================================================================
    # 10. Domain Restoration via Trail on Backtrack
    # ========================================================================
    def test_10_domain_restoration_via_trail_on_backtrack(self) -> None:
        solver = CSPSolver(self.model)
        val_pruned = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F1", "G1")
        working_domains = {"V2": []}
        domain_trail = [("V2", val_pruned)]

        solver._restore_domain_trail(domain_trail, working_domains)

        self.assertEqual(len(domain_trail), 0)
        self.assertIn(val_pruned, working_domains["V2"])

    # ========================================================================
    # 11. Infeasible Problem Returns SolverStatus.INFEASIBLE
    # ========================================================================
    def test_11_infeasible_problem_returns_infeasible(self) -> None:
        var1 = make_var("V1")
        custom_model = CSPModel(
            variables=[var1],
            domains={"V1": []},
        )
        solver = CSPSolver(custom_model)
        result = solver.solve()

        self.assertEqual(result.status, SolverStatus.INFEASIBLE)
        self.assertFalse(result.is_solution_found)

    # ========================================================================
    # 12. Empty CSP Returns SolverStatus.EMPTY_PROBLEM
    # ========================================================================
    def test_12_empty_csp_returns_empty_problem(self) -> None:
        custom_model = CSPModel(variables=[], domains={})
        solver = CSPSolver(custom_model)
        result = solver.solve()

        self.assertEqual(result.status, SolverStatus.EMPTY_PROBLEM)
        self.assertTrue(result.is_solution_found)
        self.assertEqual(result.assignment, {})

    # ========================================================================
    # 13. Search Node Limit Triggering SolverStatus.NODE_LIMIT_REACHED
    # ========================================================================
    def test_13_search_node_limit_triggering_limit(self) -> None:
        solver = CSPSolver(self.model)
        config = SolverConfig(
            max_search_nodes=1,
            use_ac3_preprocess=False,
            use_forward_checking=False,
        )
        result = solver.solve(config)

        self.assertEqual(result.status, SolverStatus.NODE_LIMIT_REACHED)
        self.assertFalse(result.is_solution_found)
        self.assertIn("Node limit", result.message)

    # ========================================================================
    # 14. Timeout Triggering SolverStatus.TIMEOUT
    # ========================================================================
    def test_14_timeout_triggering_timeout(self) -> None:
        solver = CSPSolver(self.model)
        config = SolverConfig(
            timeout_seconds=0.0000000001,
            max_search_nodes=1000000,
            use_ac3_preprocess=False,
            use_forward_checking=False,
        )
        result = solver.solve(config)

        self.assertEqual(result.status, SolverStatus.TIMEOUT)
        self.assertFalse(result.is_solution_found)
        self.assertIn("timeout", result.message.lower())

    # ========================================================================
    # 15. Complete Timetable Validation Against CSPModel.validate_assignments
    # ========================================================================
    def test_15_complete_timetable_validation_h1_to_h8(self) -> None:
        solver = CSPSolver(self.model)
        result = solver.solve()

        self.assertEqual(result.status, SolverStatus.SUCCESS)
        val_report = self.model.validate_assignments(result.assignment)

        self.assertEqual(val_report.status, TimetableStatus.COMPLETE_VALID)
        self.assertTrue(val_report.is_valid)
        self.assertEqual(val_report.assigned_variables, len(self.model.variables))
        self.assertEqual(len(val_report.hard_violations), 0)

        # All 8 hard constraints must report PASS
        for h_id in ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"]:
            summary = val_report.summary_by_constraint.get(h_id)
            self.assertIsNotNone(summary)
            self.assertEqual(summary["violations"], 0)
            self.assertEqual(summary["status"], "PASS")

    # ========================================================================
    # 16. Soft Penalty Calculation (S1-S4)
    # ========================================================================
    def test_16_soft_penalty_calculation_s1_to_s4(self) -> None:
        solver = CSPSolver(self.model)
        result = solver.solve()

        self.assertEqual(result.status, SolverStatus.SUCCESS)
        val_report = result.validation_report

        self.assertIsNotNone(val_report)
        self.assertIsInstance(val_report.soft_penalty_score, float)
        self.assertGreaterEqual(val_report.soft_penalty_score, 0.0)

        for s_id in ["S1", "S2", "S3", "S4"]:
            s_sum = val_report.summary_by_constraint.get(s_id)
            self.assertIsNotNone(s_sum, f"Missing soft constraint summary for {s_id}")
            self.assertIsInstance(s_sum["penalty"], float)
            self.assertGreaterEqual(s_sum["penalty"], 0.0)

    # ========================================================================
    # 17. SQLite Timetable Persistence (save_timetable_solution & load)
    # ========================================================================
    def test_17_sqlite_timetable_persistence(self) -> None:
        solver = CSPSolver(self.model)
        result = solver.solve()
        self.assertEqual(result.status, SolverStatus.SUCCESS)

        run_id = "RUN_TEST_PHASE4"
        ok, msg = save_timetable_solution(
            assignment=result.assignment,
            variables_map=self.model.variables_map,
            run_id=run_id,
            overwrite_existing=True,
            db_path=self.test_db,
        )

        self.assertTrue(ok)
        self.assertIn("saved successfully", msg.lower())

        loaded = load_saved_timetable(run_id=run_id, db_path=self.test_db)
        self.assertGreater(len(loaded), 0)

        # Verify joined fields are populated
        first_entry = loaded[0]
        self.assertIn("course_code", first_entry)
        self.assertIn("faculty_name", first_entry)
        self.assertIn("group_name", first_entry)
        self.assertIn("room_name", first_entry)
        self.assertIn("slot_id", first_entry)
        self.assertEqual(first_entry["generation_run_id"], run_id)

    # ========================================================================
    # 18. No Duplicate Schedule Records and Clean Overwrite Behavior
    # ========================================================================
    def test_18_no_duplicate_records_and_clean_overwrite(self) -> None:
        solver = CSPSolver(self.model)
        result = solver.solve()
        self.assertEqual(result.status, SolverStatus.SUCCESS)

        # First save
        ok1, _ = save_timetable_solution(
            assignment=result.assignment,
            variables_map=self.model.variables_map,
            run_id="RUN_1",
            overwrite_existing=True,
            db_path=self.test_db,
        )
        self.assertTrue(ok1)
        count_first = len(load_saved_timetable(db_path=self.test_db))

        # Second save with overwrite_existing=True
        ok2, _ = save_timetable_solution(
            assignment=result.assignment,
            variables_map=self.model.variables_map,
            run_id="RUN_2",
            overwrite_existing=True,
            db_path=self.test_db,
        )
        self.assertTrue(ok2)
        count_second = len(load_saved_timetable(db_path=self.test_db))

        # Count must remain exactly equal (no duplicate rows accumulated)
        self.assertEqual(count_first, count_second)

        # Check unique generation run ID
        records = load_saved_timetable(db_path=self.test_db)
        run_ids = {r["generation_run_id"] for r in records}
        self.assertEqual(run_ids, {"RUN_2"})

    # ========================================================================
    # 19. Full Regression Check of Phase 1-3 Functionality
    # ========================================================================
    def test_19_regression_check_phase1_to_phase3(self) -> None:
        summary = load_dataset_summary(self.test_db)
        self.assertGreater(summary["classrooms"], 0)
        self.assertGreater(summary["faculty"], 0)
        self.assertGreater(summary["student_groups"], 0)
        self.assertGreater(summary["courses"], 0)
        self.assertGreater(summary["timeslots"], 0)

        vars_list = generate_variables_from_db(self.test_db)
        self.assertGreater(len(vars_list), 0)
        doms_map = generate_domains_from_db(vars_list, self.test_db)
        for v in vars_list:
            self.assertIn(v.var_id, doms_map)
            self.assertGreater(len(doms_map[v.var_id]), 0)

        empty_rep = self.model.validate_assignments({})
        self.assertEqual(empty_rep.status, TimetableStatus.EMPTY)

        valid_sample = self.model.generate_valid_sample_schedule(num_variables=4)
        sample_rep = self.model.validate_assignments(valid_sample)
        self.assertEqual(sample_rep.status, TimetableStatus.PARTIAL_VALID)
        self.assertEqual(len(sample_rep.hard_violations), 0)


if __name__ == "__main__":
    unittest.main()
