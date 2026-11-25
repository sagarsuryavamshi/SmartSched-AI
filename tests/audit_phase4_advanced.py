"""Phase 4 Advanced Quality Audit Script.

Executes:
  TEST 1: Heuristic Configuration Ablation (Configs A through H).
  TEST 2: Soft Constraint Optimization Analysis (S1-S4 penalty breakdown, alternate solutions search).
  TEST 3: Realistic Difficult CSP (satisfiable tight instance with backtracks + unsatisfiable instance).
  TEST 4: UI & Database Integration verification.
"""

import copy
import json
import os
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.csp_engine.domain_types import (
    SchedulingAssignmentValue,
    SchedulingVariable,
    SessionType,
    TimetableStatus,
)
from src.csp_engine.generator import generate_domains_from_db, generate_variables_from_db
from src.csp_engine.model import CSPModel
from src.csp_engine.solver import CSPSolver, values_are_compatible
from src.csp_engine.solver_types import SolverConfig, SolverResult, SolverStatus
from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection, init_db
from src.database.timetable_repository import load_saved_timetable, save_timetable_solution
from src.data_management.loader import load_dataset_summary, seed_synthetic_data


def run_ablation_study() -> Dict[str, Dict]:
    """TEST 1: Heuristic Configuration Ablation Study."""
    print("=" * 80)
    print("TEST 1: HEURISTIC CONFIGURATION ABLATION STUDY")
    print("=" * 80)

    init_db(DEFAULT_DB_PATH)
    seed_synthetic_data(DEFAULT_DB_PATH, overwrite=False)
    model = CSPModel.build_from_db(DEFAULT_DB_PATH)

    configs = {
        "A (All Heuristics Enabled)": SolverConfig(
            use_mrv=True, use_degree=True, use_lcv=True,
            use_forward_checking=True, use_ac3_preprocess=True, use_incremental_ac3=False,
            max_search_nodes=50000, timeout_seconds=30.0
        ),
        "B (MRV Disabled)": SolverConfig(
            use_mrv=False, use_degree=True, use_lcv=True,
            use_forward_checking=True, use_ac3_preprocess=True, use_incremental_ac3=False,
            max_search_nodes=50000, timeout_seconds=30.0
        ),
        "C (Degree Heuristic Disabled)": SolverConfig(
            use_mrv=True, use_degree=False, use_lcv=True,
            use_forward_checking=True, use_ac3_preprocess=True, use_incremental_ac3=False,
            max_search_nodes=50000, timeout_seconds=30.0
        ),
        "D (LCV Disabled)": SolverConfig(
            use_mrv=True, use_degree=True, use_lcv=False,
            use_forward_checking=True, use_ac3_preprocess=True, use_incremental_ac3=False,
            max_search_nodes=50000, timeout_seconds=30.0
        ),
        "E (Forward Checking Disabled)": SolverConfig(
            use_mrv=True, use_degree=True, use_lcv=True,
            use_forward_checking=False, use_ac3_preprocess=True, use_incremental_ac3=False,
            max_search_nodes=50000, timeout_seconds=30.0
        ),
        "F (AC-3 Preprocess Disabled)": SolverConfig(
            use_mrv=True, use_degree=True, use_lcv=True,
            use_forward_checking=True, use_ac3_preprocess=False, use_incremental_ac3=False,
            max_search_nodes=50000, timeout_seconds=30.0
        ),
        "G (Incremental AC-3 Enabled)": SolverConfig(
            use_mrv=True, use_degree=True, use_lcv=True,
            use_forward_checking=True, use_ac3_preprocess=True, use_incremental_ac3=True,
            max_search_nodes=50000, timeout_seconds=30.0
        ),
        "H (All Heuristics & Pruning Disabled)": SolverConfig(
            use_mrv=False, use_degree=False, use_lcv=False,
            use_forward_checking=False, use_ac3_preprocess=False, use_incremental_ac3=False,
            max_search_nodes=50000, timeout_seconds=30.0
        ),
    }

    results = {}
    for name, cfg in configs.items():
        solver = CSPSolver(model)
        res = solver.solve(cfg)
        stats = res.statistics
        penalty = res.validation_report.soft_penalty_score if res.validation_report else -1.0
        results[name] = {
            "status": res.status.value,
            "nodes": stats.nodes_explored,
            "backtracks": stats.backtracks,
            "checks": stats.constraint_checks,
            "reductions": stats.domain_reductions,
            "ac3_arcs": stats.ac3_arcs_processed,
            "runtime_ms": stats.execution_time_seconds * 1000,
            "soft_penalty": penalty,
        }
        print(f"[{name}]")
        print(f"  Status: {res.status.value} | Nodes: {stats.nodes_explored} | Backtracks: {stats.backtracks} | Checks: {stats.constraint_checks:,} | Reductions: {stats.domain_reductions} | Time: {stats.execution_time_seconds*1000:.2f}ms | Penalty: {penalty}")

    return results


def analyze_soft_constraints() -> Dict:
    """TEST 2: Soft Constraint Optimization Analysis."""
    print("\n" + "=" * 80)
    print("TEST 2: SOFT CONSTRAINT OPTIMIZATION ANALYSIS")
    print("=" * 80)

    model = CSPModel.build_from_db(DEFAULT_DB_PATH)
    solver = CSPSolver(model)
    res = solver.solve(SolverConfig(use_mrv=True, use_degree=True, use_lcv=True, use_forward_checking=True))

    report = res.validation_report
    print(f"First-Feasible Solution Soft Penalty: {report.soft_penalty_score}")
    print("Component breakdown:")
    for s_id in ["S1", "S2", "S3", "S4"]:
        info = report.summary_by_constraint[s_id]
        print(f"  {s_id} ({info['name']}): Penalty = {info['penalty']:.1f}, Violations = {info['violations']}")

    # Check if alternate feasible solutions can be found and if penalties vary
    # We can do this by running search with different variable / value orderings
    alternate_penalties = []
    # Test variation 1: Natural value ordering (LCV False)
    res_no_lcv = CSPSolver(model).solve(SolverConfig(use_mrv=True, use_degree=True, use_lcv=False, use_forward_checking=True))
    if res_no_lcv.is_solution_found:
        p = res_no_lcv.validation_report.soft_penalty_score
        alternate_penalties.append(("Natural Value Ordering (No LCV)", p))

    # Test variation 2: Natural variable ordering (No MRV)
    res_no_mrv = CSPSolver(model).solve(SolverConfig(use_mrv=False, use_degree=False, use_lcv=True, use_forward_checking=True))
    if res_no_mrv.is_solution_found:
        p = res_no_mrv.validation_report.soft_penalty_score
        alternate_penalties.append(("Natural Variable Ordering (No MRV)", p))

    # Test variation 3: No MRV and No LCV
    res_raw = CSPSolver(model).solve(SolverConfig(use_mrv=False, use_degree=False, use_lcv=False, use_forward_checking=True))
    if res_raw.is_solution_found:
        p = res_raw.validation_report.soft_penalty_score
        alternate_penalties.append(("Pure Natural (No MRV, No LCV)", p))

    print("\nAlternate Feasible Solutions Discovered:")
    for label, p in alternate_penalties:
        print(f"  - {label}: Penalty = {p:.1f}")

    return {
        "first_feasible_score": report.soft_penalty_score,
        "breakdown": {s_id: report.summary_by_constraint[s_id] for s_id in ["S1", "S2", "S3", "S4"]},
        "alternate_scores": alternate_penalties,
    }


def test_difficult_and_infeasible_csp() -> Dict:
    """TEST 3: Realistic Difficult CSP & Unsatisfiable Instance."""
    print("\n" + "=" * 80)
    print("TEST 3: REALISTIC DIFFICULT CSP & UNSATISFIABLE INSTANCE")
    print("=" * 80)

    # Construct a difficult CSP:
    # 3 student groups, 2 shared faculty, only 1 classroom (CR_LH101) and 1 lab (CR_LAB201).
    # 8 variables competing for limited slots on Monday and Tuesday (slots 1 to 4).
    # Tight resource bottlenecks ensure that greedy choices lead to dead ends and backtracks!

    # 4 slots on Monday, 4 slots on Tuesday
    slots_data = {}
    for day in ["Monday", "Tuesday"]:
        for i, (st, et) in enumerate([("09:00", "10:00"), ("10:00", "11:00"), ("11:00", "12:00"), ("12:00", "13:00")], start=1):
            s_id = f"SLOT_{day[:3].upper()}_{i}"
            slots_data[s_id] = {
                "slot_id": s_id, "day": day, "start_time": st, "end_time": et,
                "duration_minutes": 60, "is_break": 0
            }

    # Consecutive lab slots on Monday (09:00-11:00) and Tuesday (09:00-11:00)
    lab_slot_m = ("SLOT_MON_1", "SLOT_MON_2")
    lab_slot_t = ("SLOT_TUE_1", "SLOT_TUE_2")

    # Variables:
    # V1: Group G1, Faculty F1, Lecture Hall (2 sessions)
    # V2: Group G1, Faculty F1, Lecture Hall (2 sessions)
    # V3: Group G2, Faculty F1, Lecture Hall (2 sessions) -> F1 shared between G1 and G2!
    # V4: Group G2, Faculty F2, Lecture Hall (2 sessions)
    # V5: Group G3, Faculty F2, Lecture Hall (1 session)  -> Only 1 Lecture Hall available!
    # V_LAB1: Group G1, Faculty F2, Lab (2 hours consecutive) -> Lab room CR_LAB201
    # V_LAB2: Group G2, Faculty F2, Lab (2 hours consecutive) -> Competing for same Lab room and Faculty F2!

    v1 = SchedulingVariable("V1", "C1", "CS101", 1, 2, SessionType.THEORY, 1, "F1", "G1", "LECTURE_HALL")
    v2 = SchedulingVariable("V2", "C1", "CS101", 2, 2, SessionType.THEORY, 1, "F1", "G1", "LECTURE_HALL")
    v3 = SchedulingVariable("V3", "C2", "CS102", 1, 2, SessionType.THEORY, 1, "F1", "G2", "LECTURE_HALL")
    v4 = SchedulingVariable("V4", "C3", "CS103", 1, 2, SessionType.THEORY, 1, "F2", "G2", "LECTURE_HALL")
    v5 = SchedulingVariable("V5", "C4", "CS104", 1, 1, SessionType.THEORY, 1, "F2", "G3", "LECTURE_HALL")
    v_lab1 = SchedulingVariable("V_LAB1", "C5", "CS105", 1, 1, SessionType.LAB, 2, "F2", "G1", "LAB")
    v_lab2 = SchedulingVariable("V_LAB2", "C6", "CS106", 1, 1, SessionType.LAB, 2, "F2", "G2", "LAB")

    diff_vars = [v1, v2, v3, v4, v5, v_lab1, v_lab2]

    # Generate restricted domains
    diff_domains: Dict[str, List[SchedulingAssignmentValue]] = {}

    # Theory domains: can only use CR_LH101, single 1h slots
    theory_values_f1_g1 = [
        SchedulingAssignmentValue(s["slot_id"], "CR_LH101", s["day"], s["start_time"], s["end_time"], (s["slot_id"],), "F1", "G1")
        for s in slots_data.values()
    ]
    theory_values_f1_g2 = [
        SchedulingAssignmentValue(s["slot_id"], "CR_LH101", s["day"], s["start_time"], s["end_time"], (s["slot_id"],), "F1", "G2")
        for s in slots_data.values()
    ]
    theory_values_f2_g2 = [
        SchedulingAssignmentValue(s["slot_id"], "CR_LH101", s["day"], s["start_time"], s["end_time"], (s["slot_id"],), "F2", "G2")
        for s in slots_data.values()
    ]
    theory_values_f2_g3 = [
        SchedulingAssignmentValue(s["slot_id"], "CR_LH101", s["day"], s["start_time"], s["end_time"], (s["slot_id"],), "F2", "G3")
        for s in slots_data.values()
    ]

    diff_domains["V1"] = list(theory_values_f1_g1)
    diff_domains["V2"] = list(theory_values_f1_g1)
    diff_domains["V3"] = list(theory_values_f1_g2)
    diff_domains["V4"] = list(theory_values_f2_g2)
    diff_domains["V5"] = list(theory_values_f2_g3)

    # Lab domains: only 2 possible windows (Mon 09-11 or Tue 09-11) in CR_LAB201
    lab1_val_mon = SchedulingAssignmentValue("SLOT_MON_1", "CR_LAB201", "Monday", "09:00", "11:00", lab_slot_m, "F2", "G1")
    lab1_val_tue = SchedulingAssignmentValue("SLOT_TUE_1", "CR_LAB201", "Tuesday", "09:00", "11:00", lab_slot_t, "F2", "G1")
    lab2_val_mon = SchedulingAssignmentValue("SLOT_MON_1", "CR_LAB201", "Monday", "09:00", "11:00", lab_slot_m, "F2", "G2")
    lab2_val_tue = SchedulingAssignmentValue("SLOT_TUE_1", "CR_LAB201", "Tuesday", "09:00", "11:00", lab_slot_t, "F2", "G2")

    diff_domains["V_LAB1"] = [lab1_val_mon, lab1_val_tue]
    diff_domains["V_LAB2"] = [lab2_val_mon, lab2_val_tue]

    difficult_model = CSPModel(
        variables=diff_vars,
        domains=diff_domains,
        room_capacities={"CR_LH101": 60, "CR_LAB201": 40},
        room_types={"CR_LH101": "LECTURE_HALL", "CR_LAB201": "LAB"},
        group_sizes={"G1": 30, "G2": 35, "G3": 25},
        faculty_working_days={"F1": {"Monday", "Tuesday"}, "F2": {"Monday", "Tuesday"}},
        faculty_unavailability={"F1": set(), "F2": set()},
        timeslot_details=slots_data,
    )

    # Solve difficult model with natural ordering (to trigger search path dead end)
    diff_solver = CSPSolver(difficult_model)
    diff_res = diff_solver.solve(SolverConfig(
        use_mrv=False, use_degree=False, use_lcv=False,
        use_forward_checking=True, use_ac3_preprocess=True,
    ))

    print(f"Difficult Satisfiable CSP Results:")
    print(f"  Status: {diff_res.status.value}")
    print(f"  Nodes Explored: {diff_res.statistics.nodes_explored}")
    print(f"  Backtracks: {diff_res.statistics.backtracks}")
    print(f"  Dead Ends Encountered: {diff_res.statistics.dead_ends}")
    print(f"  Domain Reductions via FC: {diff_res.statistics.domain_reductions}")
    print(f"  AC-3 Arcs Processed: {diff_res.statistics.ac3_arcs_processed}")
    print(f"  Validation Report is_valid: {diff_res.validation_report.is_valid if diff_res.validation_report else False}")
    if diff_res.validation_report:
        print(f"  Hard Violations: {len(diff_res.validation_report.hard_violations)}")

    # Construct an inherently unsatisfiable CSP instance:
    # 3 Lab sessions of 2h each, but only 2 lab windows available (Mon 09-11 and Tue 09-11)
    v_lab3 = SchedulingVariable("V_LAB3", "C7", "CS107", 1, 1, SessionType.LAB, 2, "F2", "G3", "LAB")
    lab3_val_mon = SchedulingAssignmentValue("SLOT_MON_1", "CR_LAB201", "Monday", "09:00", "11:00", lab_slot_m, "F2", "G3")
    lab3_val_tue = SchedulingAssignmentValue("SLOT_TUE_1", "CR_LAB201", "Tuesday", "09:00", "11:00", lab_slot_t, "F2", "G3")

    unsat_vars = [v_lab1, v_lab2, v_lab3]
    unsat_domains = {
        "V_LAB1": [lab1_val_mon, lab1_val_tue],
        "V_LAB2": [lab2_val_mon, lab2_val_tue],
        "V_LAB3": [lab3_val_mon, lab3_val_tue],
    }

    unsat_model = CSPModel(
        variables=unsat_vars,
        domains=unsat_domains,
        room_capacities={"CR_LAB201": 40},
        room_types={"CR_LAB201": "LAB"},
        group_sizes={"G1": 30, "G2": 30, "G3": 30},
        faculty_working_days={"F2": {"Monday", "Tuesday"}},
        faculty_unavailability={"F2": set()},
        timeslot_details=slots_data,
    )

    unsat_solver = CSPSolver(unsat_model)
    unsat_res = unsat_solver.solve()
    print(f"\nUnsatisfiable CSP Results (Pigeonhole 3 labs into 2 room-windows):")
    print(f"  Status: {unsat_res.status.value}")
    print(f"  Is Solution Found: {unsat_res.is_solution_found}")
    print(f"  Dead Ends: {unsat_res.statistics.dead_ends}")
    print(f"  Message: {unsat_res.message}")

    return {
        "satisfiable": {
            "status": diff_res.status.value,
            "nodes": diff_res.statistics.nodes_explored,
            "backtracks": diff_res.statistics.backtracks,
            "dead_ends": diff_res.statistics.dead_ends,
            "domain_reductions": diff_res.statistics.domain_reductions,
            "is_valid": diff_res.validation_report.is_valid if diff_res.validation_report else False,
        },
        "unsatisfiable": {
            "status": unsat_res.status.value,
            "is_solution_found": unsat_res.is_solution_found,
            "dead_ends": unsat_res.statistics.dead_ends,
            "message": unsat_res.message,
        }
    }


def verify_database_and_ui_integration() -> Dict:
    """TEST 4: Database and UI Integration Verification."""
    print("\n" + "=" * 80)
    print("TEST 4: DATABASE AND UI INTEGRATION VERIFICATION")
    print("=" * 80)

    model = CSPModel.build_from_db(DEFAULT_DB_PATH)
    solver = CSPSolver(model)
    res = solver.solve()

    # Test saving
    test_run_id = f"AUDIT_RUN_{int(time.time())}"
    ok, msg = save_timetable_solution(
        assignment=res.assignment,
        variables_map=model.variables_map,
        run_id=test_run_id,
        overwrite_existing=True,
    )
    print(f"Save Operation: {ok} | Message: {msg}")

    # Test loading
    loaded_records = load_saved_timetable(run_id=test_run_id)
    print(f"Loaded Records Count: {len(loaded_records)}")

    # Verify joined columns
    first = loaded_records[0]
    required_keys = ["course_code", "course_title", "faculty_name", "group_name", "room_name", "slot_id", "day", "start_time", "end_time"]
    keys_present = all(k in first for k in required_keys)
    print(f"All Joined Relational Keys Present: {keys_present}")

    # Test re-generation / overwrite behavior (no duplication)
    ok2, msg2 = save_timetable_solution(
        assignment=res.assignment,
        variables_map=model.variables_map,
        run_id=f"{test_run_id}_V2",
        overwrite_existing=True,
    )
    reloaded_records = load_saved_timetable()
    print(f"Overwritten Table Count: {len(reloaded_records)} (Identical to previous: {len(reloaded_records) == len(loaded_records)})")

    return {
        "save_success": ok,
        "records_count": len(loaded_records),
        "keys_present": keys_present,
        "overwrite_clean": len(reloaded_records) == len(loaded_records),
    }


if __name__ == "__main__":
    ablation = run_ablation_study()
    soft = analyze_soft_constraints()
    diff = test_difficult_and_infeasible_csp()
    ui_db = verify_database_and_ui_integration()
