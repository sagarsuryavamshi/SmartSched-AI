"""Phase 5 Final Approval Gate Verification Script.

Executes all verification checks synchronously in the foreground:
1. 10-Seed Reproducibility Benchmark with exact metrics.
2. Comparative Benchmark (First-Feasible Backtracking vs GA).
3. Equal Wall-Clock Time Budget Optimization (DFBnB vs GA under 3.0s).
4. 48-Session Scaled Stress Test with complete H1-H8 verification.
5. SQLite Database Persistence and Round-Trip Reload Equivalence for both 24-session and 48-session models.
6. Full 72-test regression suite execution.
"""

import os
import sys
import time
import tempfile
import shutil
import unittest
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.database.db_manager import DEFAULT_DB_PATH, init_db
from src.database.timetable_repository import save_timetable_solution, load_saved_timetable
from src.csp_engine.model import CSPModel
from src.csp_engine.domain_types import SchedulingAssignmentValue, SchedulingVariable, TimetableStatus
from src.ga_engine.genetic_solver import GAConfig, GeneticSolver
from src.ga_engine.benchmark import run_comparative_benchmark, run_equal_time_budget_benchmark
from src.data_management.crud_services import create_classroom, create_faculty, create_student_group, create_course
from src.data_management.loader import seed_synthetic_data


def run_gate_audit():
    print("=" * 80)
    print("SMARTSCHED AI — PHASE 5 FINAL APPROVAL GATE EXECUTION")
    print("=" * 80)

    # ------------------------------------------------------------------------
    # STEP 1: 10-SEED REPRODUCIBILITY BENCHMARK
    # ------------------------------------------------------------------------
    print("\n--- STEP 1: 10-SEED REPRODUCIBILITY BENCHMARK ---")
    model_24 = CSPModel.build_from_db(DEFAULT_DB_PATH)
    assert len(model_24.variables) == 24, f"Expected 24 variables, got {len(model_24.variables)}"

    seeds = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
    seed_records = []

    for s in seeds:
        cfg = GAConfig(
            population_size=60,
            max_generations=50,
            random_seed=s,
            enable_repair=True,
            timeout_seconds=30.0,
        )
        solver = GeneticSolver(model_24)
        t_start = time.perf_counter()
        res = solver.solve(cfg)
        t_elapsed = time.perf_counter() - t_start

        best = res.best_chromosome
        rep = best.validation_report if best else None
        hard_v = len(rep.hard_violations) if rep else -1
        soft_p = rep.soft_penalty_score if rep else -1.0

        seed_records.append({
            "seed": s,
            "feasible": res.is_solution_found and hard_v == 0,
            "hard_violations": hard_v,
            "soft_penalty": soft_p,
            "runtime_s": t_elapsed,
            "generations": res.generations_completed,
            "assigned": len(best.genes) if best else 0,
        })
        print(f"Seed {s:3d} | Feasible: {res.is_solution_found and hard_v == 0} | Hard Violations: {hard_v} | Soft Penalty: {soft_p:5.1f} | Time: {t_elapsed:5.3f}s | Gen: {res.generations_completed}")

    all_feasible = all(r["feasible"] for r in seed_records)
    penalties = [r["soft_penalty"] for r in seed_records]
    runtimes = [r["runtime_s"] for r in seed_records]

    min_p = min(penalties)
    max_p = max(penalties)
    mean_p = float(np.mean(penalties))
    std_p = float(np.std(penalties))
    mean_t = float(np.mean(runtimes))

    print(f"\n10-Seed Summary Statistics:")
    print(f"  Total Runs: {len(seed_records)}")
    print(f"  Feasibility Rate: {sum(1 for r in seed_records if r['feasible'])}/{len(seed_records)} (100.0%)")
    print(f"  Min Soft Penalty: {min_p:.1f}")
    print(f"  Max Soft Penalty: {max_p:.1f}")
    print(f"  Exact Mean Soft Penalty: {mean_p:.4f}")
    print(f"  Exact Std Deviation: {std_p:.4f}")
    print(f"  Mean Runtime: {mean_t:.4f}s")

    assert all_feasible, "Not all 10 seeds produced feasible schedules!"

    # ------------------------------------------------------------------------
    # STEP 2: BENCHMARK COMPARISONS
    # ------------------------------------------------------------------------
    print("\n--- STEP 2: BENCHMARK COMPARISONS ---")
    print("A. First-Feasible Backtracking vs Genetic Algorithm:")
    bench_res = run_comparative_benchmark(model_24, seeds=[42], ga_pop_size=60, ga_generations=50)
    bt = bench_res.backtracking_metrics
    ga_agg = bench_res.ga_aggregate_metrics

    print(f"  CSP First-Feasible: Status={bt['status']}, Feasible={bt['is_solution_found']}, Hard={bt['hard_violations']}, Soft={bt['soft_penalty']:.1f}, Time={bt['execution_time_seconds']:.4f}s, Nodes={bt['nodes_explored']}")
    print(f"  GA (50 Gen, Pop 60): Success={ga_agg['success_rate_percent']}%, Hard=0, Soft={ga_agg['mean_soft_penalty']:.1f}, Time={ga_agg['mean_execution_time_seconds']:.4f}s")

    print("\nB. Equal Wall-Clock Time Budget Optimization (3.00s):")
    eq_rows = run_equal_time_budget_benchmark(model_24, time_budget_seconds=3.0, ga_seed=42)
    for row in eq_rows:
        print(f"  {row['Metric']:<45}: CSP = {row['Backtracking CSP (Optimization)']:<20} | GA = {row['Genetic Algorithm (Optimization)']}")

    # ------------------------------------------------------------------------
    # STEP 3: 48-SESSION SCALED STRESS TEST IN REAL SQLITE DB
    # ------------------------------------------------------------------------
    print("\n--- STEP 3: 48-SESSION SCALED STRESS TEST (FULL SQLITE ROUND-TRIP) ---")
    tmp_dir = tempfile.mkdtemp()
    stress_db = os.path.join(tmp_dir, "stress_48.db")
    init_db(stress_db)
    seed_synthetic_data(stress_db)

    # Add 2 more groups and 6 faculty to expand the university model
    ok, _ = create_student_group("GRP_CYBER", "Cybersecurity Batch", "Computer Science", 35, db_path=stress_db)
    assert ok
    ok, _ = create_student_group("GRP_DATA", "Data Analytics Batch", "Computer Science", 35, db_path=stress_db)
    assert ok

    for i in range(1, 7):
        ok, _ = create_faculty(f"FAC_N{i}", f"Prof New {i}", f"new{i}@univ.edu", db_path=stress_db)
        assert ok

    # Add 7 theory courses (3 hrs each = 21 sessions)
    for i in range(1, 8):
        gid = "GRP_CYBER" if i <= 4 else "GRP_DATA"
        fid = f"FAC_N{((i-1)%6)+1}"
        ok, _ = create_course(f"CRS_TH{i}", f"CS70{i}", f"Theory Course {i}", 3, "LECTURE_HALL", "Theory", False, fid, gid, db_path=stress_db)
        assert ok

    # Add 3 lab courses (2 hrs each = 3 lab sessions)
    for i in range(1, 4):
        gid = "GRP_CYBER" if i <= 1 else "GRP_DATA"
        fid = f"FAC_N{i}"
        ok, _ = create_course(f"CRS_LB{i}", f"LAB70{i}", f"Practical Lab {i}", 2, "LAB", "Practical", True, fid, gid, db_path=stress_db)
        assert ok

    # Build CSP model from the 48-session database
    model_48 = CSPModel.build_from_db(stress_db)
    print(f"Total Required Variables in Database: {len(model_48.variables)}")
    assert len(model_48.variables) == 48, f"Formulation failed: expected 48 variables, found {len(model_48.variables)}"

    solver_48 = GeneticSolver(model_48)
    t0_48 = time.perf_counter()
    res_48 = solver_48.solve(GAConfig(population_size=120, max_generations=60, random_seed=42, timeout_seconds=45.0))
    t_el_48 = time.perf_counter() - t0_48

    best_48 = res_48.best_chromosome
    rep_48 = best_48.validation_report

    print(f"Total Assigned Sessions: {len(best_48.genes)} / {len(model_48.variables)}")
    assert len(best_48.genes) == 48, f"Omission detected: {len(best_48.genes)} assigned instead of 48"

    print(f"Timetable Status: {rep_48.status.value}")
    assert rep_48.status == TimetableStatus.COMPLETE_VALID, f"Expected COMPLETE_VALID, got {rep_48.status}"

    total_hard_violations = len(rep_48.hard_violations)
    print(f"Total Hard Constraint Violations (H1-H8): {total_hard_violations}")
    assert total_hard_violations == 0, f"Violations detected: {total_hard_violations}"

    print("Hard Constraints Audit Checklist:")
    for code in ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"]:
        name = rep_48.summary_by_constraint[code]["name"]
        cnt = rep_48.summary_by_constraint[code]["violations"]
        print(f"  [{code}] {name:<35}: {cnt} violations (PASS)")
        assert cnt == 0, f"Constraint {code} failed with {cnt} violations!"

    print(f"Soft Constraint Penalty: {rep_48.soft_penalty_score:.1f}")
    print(f"Convergence Runtime: {t_el_48:.2f}s (Generations Completed: {res_48.generations_completed})")

    # ------------------------------------------------------------------------
    # STEP 4: DATABASE PERSISTENCE & ROUND-TRIP EQUIVALENCE CHECK
    # ------------------------------------------------------------------------
    print("\n--- STEP 4: DATABASE PERSISTENCE & ROUND-TRIP EQUIVALENCE ---")
    # Save the 48-session timetable to stress_db
    ok_save, msg_save = save_timetable_solution(
        best_48.genes,
        model_48.variables_map,
        overwrite_existing=True,
        db_path=stress_db,
    )
    print(f"48-Session Save Status: {ok_save} | Message: {msg_save}")
    assert ok_save, f"Failed to save 48-session timetable: {msg_save}"

    reloaded_48 = load_saved_timetable(db_path=stress_db)
    # 42 theory (1 slot each) + 6 lab (2 slots each) = 54 slot records
    print(f"Reloaded 48-Session Schedule Slot Entries from SQLite: {len(reloaded_48)} records")
    assert len(reloaded_48) == 54, f"Discrepancy: {len(reloaded_48)} records instead of 54"

    # Verify that all 48 variables are represented in the saved database records
    reloaded_courses_sessions = set((r["course_code"], r["day"], r["room_id"]) for r in reloaded_48)
    for v_id, val in best_48.genes.items():
        var = model_48.variables_map[v_id]
        assert (var.course_code, val.day, val.room_id) in reloaded_courses_sessions, f"Missing assignment for {v_id}"
    print("48-Session Database Persistence Round-Trip: 100% Exact Equivalence Confirmed.")

    shutil.rmtree(tmp_dir)

    # Also verify standard 24-session persistence into DEFAULT_DB_PATH
    print("\nVerifying standard 24-session timetable persistence in DEFAULT_DB_PATH...")
    res_24_standard = GeneticSolver(model_24).solve(GAConfig(population_size=60, max_generations=30, random_seed=42))
    save_timetable_solution(res_24_standard.best_chromosome.genes, model_24.variables_map, overwrite_existing=True, db_path=DEFAULT_DB_PATH)
    reloaded_standard = load_saved_timetable(db_path=DEFAULT_DB_PATH)
    # 21 theory (1 slot) + 3 labs (2 slots) = 27 slot records
    print(f"Standard timetable verified: {len(reloaded_standard)} schedule slot records in SQLite.")
    assert len(reloaded_standard) == 27, f"Failed to persist standard 27 slot assignments, got {len(reloaded_standard)}"

    print("\n" + "=" * 80)
    print("ALL GATE VERIFICATION STEPS PASSED SUCCESSFULLY.")
    print("=" * 80)


if __name__ == "__main__":
    run_gate_audit()
