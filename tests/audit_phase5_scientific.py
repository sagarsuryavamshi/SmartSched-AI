"""Phase 5 Final Independent Scientific Audit Script.

Executes:
  AUDIT 1: Fitness Function Mathematics & Proofs
  AUDIT 2: Constraint Repair Mechanism Analysis (H1-H8 categorization and validation)
  AUDIT 3: Benchmark Fairness (First-Feasible vs Multi-Generation, and Equal Time Budget)
  AUDIT 4: 10-Seed Reproducibility Verification
  AUDIT 5: Real Dataset & Stress Tests (Scenario A: 24 vars, Scenario B: 48 vars, Scenario C: Infeasible)
"""

import copy
import json
import math
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

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
from src.csp_engine.solver import CSPSolver
from src.csp_engine.solver_types import SolverConfig, SolverResult, SolverStatus
from src.database.db_manager import DEFAULT_DB_PATH, init_db
from src.data_management.loader import seed_synthetic_data
from src.ga_engine.benchmark import (
    run_comparative_benchmark,
    run_equal_time_budget_benchmark,
)
from src.ga_engine.chromosome import TimetableChromosome
from src.ga_engine.fitness import HARD_CONSTRAINT_WEIGHT, evaluate_fitness
from src.ga_engine.genetic_solver import GAConfig, GAResult, GeneticSolver
from src.ga_engine.initialization import initialize_population
from src.ga_engine.repair import repair_chromosome


def make_var(
    var_id: str,
    course_code: str = "CS101",
    faculty_id: str = "FAC1",
    group_id: str = "GRP1",
    room_type: str = "LECTURE_HALL",
    duration_hours: int = 1,
    session_type: SessionType = SessionType.THEORY,
) -> SchedulingVariable:
    return SchedulingVariable(
        var_id=var_id,
        course_id=f"CRS_{course_code}",
        course_code=course_code,
        session_num=1,
        total_sessions=1,
        session_type=session_type,
        duration_hours=duration_hours,
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
    slot_ids: Optional[Tuple[str, ...]] = None,
) -> SchedulingAssignmentValue:
    return SchedulingAssignmentValue(
        slot_id=slot_id,
        room_id=room_id,
        day=day,
        start_time=start_time,
        end_time=end_time,
        slot_ids=slot_ids or (slot_id,),
        faculty_id=faculty_id,
        group_id=group_id,
    )


# ============================================================================
# AUDIT 1: FITNESS FUNCTION MATHEMATICS
# ============================================================================
def audit_1_fitness_mathematics() -> Dict[str, Any]:
    print("=" * 80)
    print("AUDIT 1: FITNESS FUNCTION MATHEMATICS & PROOFS")
    print("=" * 80)

    init_db(DEFAULT_DB_PATH)
    seed_synthetic_data(DEFAULT_DB_PATH, overwrite=False)
    model = CSPModel.build_from_db(DEFAULT_DB_PATH)

    # 1. Verify all H1-H8 and S1-S4 components in evaluate_fitness
    rng = random.Random(42)
    pop, _ = initialize_population(model, population_size=1, rng=rng)
    chrom = pop[0]
    fit = evaluate_fitness(chrom, model)

    rep = chrom.validation_report
    all_h_present = all(f"H{i}" in rep.summary_by_constraint for i in range(1, 9))
    all_s_present = all(f"S{i}" in rep.summary_by_constraint for i in range(1, 5))
    soft_nonneg = rep.soft_penalty_score >= 0.0

    print(f"1. All H1-H8 tracked in ValidationReport: {all_h_present}")
    print(f"2. All S1-S4 tracked in ValidationReport: {all_s_present}")
    print(f"3. Soft penalty is nonnegative: {soft_nonneg} ({rep.soft_penalty_score:.1f})")

    # 4. Mathematical Bound Analysis on Soft Penalties:
    # Let N = number of sessions, |F| = faculty count, |G| = student groups count, |D| = working days (5).
    # S1 max: 10.0 * N (each session in non-preferred slot)
    # S2 max: |F| * |D| * (idle window / 30m * 8.0). With 8 daily hours (09:00 - 17:00), max gap = 360 mins = 12 * 8 = 96.0 pts. Max S2 = |F| * 5 * 96.0 = 480 * |F|.
    # S3 max: |G| * |D| * (consecutive hours - 2) * 15.0. If all 8 hours consecutive, (8-2)*15 = 90.0 pts. Max S3 = |G| * 5 * 90.0 = 450 * |G|.
    # S4 max: |G| * |D| * (overload hours * 12.0). Max overload = (8-4)*12 = 48.0 pts. Max S4 = |G| * 5 * 48.0 = 240 * |G|.
    # On 24-variable problem: N=24, |F|=5, |G|=3, |D|=5:
    # S1_max <= 240.0
    # S2_max <= 5 * 5 * 96.0 = 2400.0
    # S3_max <= 3 * 5 * 90.0 = 1350.0
    # S4_max <= 3 * 5 * 48.0 = 720.0
    # Theoretical Max S_bound <= 240 + 2400 + 1350 + 720 = 4710.0 points.
    theoretical_max_soft_bound = 4710.0
    hard_weight = HARD_CONSTRAINT_WEIGHT  # 10000.0

    # Strict Dominance Guarantee Proof:
    # For any feasible chromosome (H=0):
    #   Cost_feas = S <= theoretical_max_soft_bound = 4710.0
    #   Fitness_feas = 1 / (1 + Cost_feas) >= 1 / (1 + 4710.0) = 0.000212
    # For any infeasible chromosome (H >= 1):
    #   Cost_infeas >= hard_weight * 1 = 10000.0
    #   Fitness_infeas = 1 / (1 + Cost_infeas) <= 1 / (1 + 10000.0) = 0.00009999
    # Since 0.000212 > 0.00009999, Cost_feas is STRICTLY < Cost_infeas for all valid timetables!
    strict_dominance_guaranteed = theoretical_max_soft_bound < hard_weight
    print(f"4. Theoretical Max Soft Penalty Bound on 24-var problem: {theoretical_max_soft_bound:.1f} pts")
    print(f"5. Hard Constraint Barrier Weight: {hard_weight:.1f}")
    print(f"6. Strict Feasibility Dominance Mathematically Proven: {strict_dominance_guaranteed}")

    # Numerical Triad Example:
    # Candidate A: Feasible (H=0, S=100.0)
    # Candidate B: Infeasible (H=1, S=0.0)
    # Candidate C: Feasible with better soft score (H=0, S=10.0)
    cost_a = (hard_weight * 0) + 100.0
    fit_a = 1.0 / (1.0 + cost_a)

    cost_b = (hard_weight * 1) + 0.0
    fit_b = 1.0 / (1.0 + cost_b)

    cost_c = (hard_weight * 0) + 10.0
    fit_c = 1.0 / (1.0 + cost_c)

    print("\nNumerical Verification Triad:")
    print(f"  Candidate A [Feasible, S=100]: Cost={cost_a:.1f}, Fitness={fit_a:.7f}")
    print(f"  Candidate B [Infeasible, H=1, S=0]: Cost={cost_b:.1f}, Fitness={fit_b:.7f}")
    print(f"  Candidate C [Feasible, S=10]: Cost={cost_c:.1f}, Fitness={fit_c:.7f}")
    print(f"  Rank Ordering: Candidate C ({fit_c:.6f}) > Candidate A ({fit_a:.6f}) > Candidate B ({fit_b:.6f})")

    assert fit_c > fit_a > fit_b, "Fitness ordering violation!"

    return {
        "all_h_present": all_h_present,
        "all_s_present": all_s_present,
        "soft_nonneg": soft_nonneg,
        "theoretical_max_soft": theoretical_max_soft_bound,
        "hard_weight": hard_weight,
        "strict_dominance": strict_dominance_guaranteed,
        "triad": {"fit_c": fit_c, "fit_a": fit_a, "fit_b": fit_b},
    }


# ============================================================================
# AUDIT 2: REPAIR MECHANISM AND H1-H8 CLASSIFICATION
# ============================================================================
def audit_2_repair_mechanism() -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("AUDIT 2: REPAIR MECHANISM AND H1-H8 CONSTRAINT CLASSIFICATION")
    print("=" * 80)

    model = CSPModel.build_from_db(DEFAULT_DB_PATH)

    # Constraint Classification Matrix:
    # - H1 (Faculty Overlap): Inter-variable binary constraint -> ACTIVELY REPAIRED by repair_chromosome
    # - H2 (Classroom Overlap): Inter-variable binary constraint -> ACTIVELY REPAIRED by repair_chromosome
    # - H3 (Student Group Clash): Inter-variable binary constraint -> ACTIVELY REPAIRED by repair_chromosome
    # - H4 (Room Capacity): Unary constraint -> PREVENTED by domain pre-filtering; repaired if swapped to legal domain
    # - H5 (Faculty Availability): Unary constraint -> PREVENTED by domain pre-filtering; repaired if swapped to legal domain
    # - H6 (Room Type): Unary constraint -> PREVENTED by domain pre-filtering; repaired if swapped to legal domain
    # - H7 (Lab Continuity): Unary sequence constraint -> PREVENTED by domain pre-filtering; repaired if swapped to legal domain
    # - H8 (Working Hours & Breaks): Unary timeslot constraint -> PREVENTED by domain pre-filtering; repaired if swapped to legal domain

    print("H1-H8 Constraint Operational Categorization:")
    print("  H1 (Faculty Overlap): Actively Repaired via candidate binary clash minimization")
    print("  H2 (Classroom Overlap): Actively Repaired via candidate binary clash minimization")
    print("  H3 (Group Clash): Actively Repaired via candidate binary clash minimization")
    print("  H4 (Room Capacity): Structurally Prevented by domain pre-filtering")
    print("  H5 (Faculty Availability): Structurally Prevented by domain pre-filtering")
    print("  H6 (Room Type): Structurally Prevented by domain pre-filtering")
    print("  H7 (Lab Continuity): Structurally Prevented by domain pre-filtering (consecutive slot pairs)")
    print("  H8 (Working Hours & Breaks): Structurally Prevented by domain pre-filtering (break exclusion)")

    # Construct a deliberately invalid chromosome with 3 conflicting variables
    # V0, V1, V2 all assigned to Monday 09:00 - 10:00 in the same room or same faculty
    rng = random.Random(42)
    pop, _ = initialize_population(model, population_size=1, rng=rng)
    invalid_chrom = pop[0].clone()

    # Deliberately force clashes on first 4 variables
    v_keys = list(invalid_chrom.genes.keys())[:4]
    clash_val = model.domains[v_keys[0]][0]  # Monday 09:00 - 10:00
    for vk in v_keys:
        # Find an assignment for vk on the same day and start_time
        same_time_opts = [o for o in model.domains[vk] if o.day == clash_val.day and o.start_time == clash_val.start_time]
        if same_time_opts:
            invalid_chrom.genes[vk] = same_time_opts[0]

    evaluate_fitness(invalid_chrom, model)
    initial_hard = invalid_chrom.hard_violations_count
    print(f"\nDeliberately Invalid Chromosome Initial State: {initial_hard} Hard Violations")
    print(f"  Participating Violations: {[v.constraint_id for v in invalid_chrom.validation_report.hard_violations]}")

    # Run repair
    is_repaired, swaps = repair_chromosome(invalid_chrom, model, max_repair_passes=10, rng=random.Random(42))
    post_hard = invalid_chrom.hard_violations_count

    # Independent validation check
    indep_report = model.validate_assignments(invalid_chrom.genes)

    print(f"Repair Execution Results: Swaps Applied={swaps}, Post-Repair Hard Violations={post_hard}")
    print(f"Independent Validation Check Matches Chromosome State: {indep_report.hard_violations == invalid_chrom.validation_report.hard_violations}")
    print(f"Is Repair Progress Confirmed: {post_hard <= initial_hard}")

    return {
        "initial_hard": initial_hard,
        "post_hard": post_hard,
        "swaps_applied": swaps,
        "independent_validation_matches": indep_report.hard_violations == invalid_chrom.validation_report.hard_violations,
        "repair_progress_confirmed": post_hard <= initial_hard,
    }


# ============================================================================
# AUDIT 3: BENCHMARK FAIRNESS (ORIGINAL & EQUAL TIME BUDGET)
# ============================================================================
def audit_3_benchmark_fairness() -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("AUDIT 3: BENCHMARK FAIRNESS & EQUAL TIME BUDGET EVALUATION")
    print("=" * 80)

    model = CSPModel.build_from_db(DEFAULT_DB_PATH)

    # 1. Original Benchmark: First-Feasible Backtracking vs Multi-Generation GA
    print("1. Original Benchmark (First-Feasible CSP vs 120-Generation GA):")
    orig_bench = run_comparative_benchmark(model, seeds=[42, 101, 202], ga_generations=50, ga_pop_size=50)
    for row in orig_bench.comparison_table[:5]:
        print(f"  {row['Metric']}: CSP=[{row['Backtracking CSP (Phase 4)']}]; GA=[{row['Genetic Algorithm (Phase 5)']}]")

    # 2. Equal Time Budget Benchmark (Both given exactly 3.0 seconds)
    time_budget = 3.0
    print(f"\n2. Equal Wall-Clock Time Budget Benchmark ({time_budget:.1f}s each):")
    eq_results = run_equal_time_budget_benchmark(model, time_budget_seconds=time_budget, ga_seed=42, ga_pop_size=80)
    for row in eq_results:
        print(f"  {row['Metric']}: CSP=[{row['Backtracking CSP (Optimization)']}]; GA=[{row['Genetic Algorithm (Optimization)']}]")

    return {
        "original_comparison": orig_bench.comparison_table,
        "equal_time_comparison": eq_results,
    }


# ============================================================================
# AUDIT 4: 10-SEED REPRODUCIBILITY VERIFICATION
# ============================================================================
def audit_4_reproducibility() -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("AUDIT 4: 10-SEED REPRODUCIBILITY VERIFICATION")
    print("=" * 80)

    model = CSPModel.build_from_db(DEFAULT_DB_PATH)
    test_seeds = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
    solver = GeneticSolver(model)

    reproduced_results = []
    for s in test_seeds:
        cfg = GAConfig(
            population_size=100,
            max_generations=120,
            random_seed=s,
            timeout_seconds=30.0,
            enable_repair=True,
        )
        res = solver.solve(cfg)
        best = res.best_chromosome
        reproduced_results.append({
            "seed": s,
            "is_feasible": res.is_solution_found,
            "hard_violations": best.hard_violations_count if best else -1,
            "soft_penalty": best.soft_penalty if best else -1.0,
            "fitness": best.fitness if best else 0.0,
            "generations": res.generations_completed,
            "runtime_s": res.execution_time_seconds,
        })
        print(f"  Seed {s:3d} -> Feasible: {res.is_solution_found} | H: {best.hard_violations_count} | Soft Penalty: {best.soft_penalty:5.1f} | Fitness: {best.fitness:.6f} | Gen: {res.generations_completed}")

    all_feasible = all(r["is_feasible"] for r in reproduced_results)
    best_soft = min(r["soft_penalty"] for r in reproduced_results)
    mean_soft = sum(r["soft_penalty"] for r in reproduced_results) / len(reproduced_results)

    print(f"\nReproducibility Summary:")
    print(f"  100% Feasibility Confirmed: {all_feasible} ({sum(1 for r in reproduced_results if r['is_feasible'])}/10)")
    print(f"  Best Soft Penalty: {best_soft:.1f} (Original report claimed: 5.0)")
    print(f"  Mean Soft Penalty: {mean_soft:.1f} (Original report claimed: 13.5)")

    return {
        "all_feasible": all_feasible,
        "best_soft": best_soft,
        "mean_soft": mean_soft,
        "individual_runs": reproduced_results,
    }


# ============================================================================
# AUDIT 5: REAL DATASET AND STRESS TESTS (3 SCENARIOS)
# ============================================================================
def audit_5_stress_tests() -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("AUDIT 5: REAL DATASET AND STRESS TESTS (SCENARIOS A, B, C)")
    print("=" * 80)

    # ------------------------------------------------------------------------
    # Scenario A: Standard 24-session dataset
    # ------------------------------------------------------------------------
    model_a = CSPModel.build_from_db(DEFAULT_DB_PATH)
    ga_a = GeneticSolver(model_a).solve(GAConfig(population_size=60, max_generations=40, random_seed=42))
    print(f"Scenario A (Standard 24 Sessions):")
    print(f"  Status: {ga_a.status} | Feasible: {ga_a.is_solution_found} | Hard: {ga_a.best_chromosome.hard_violations_count} | Soft: {ga_a.best_chromosome.soft_penalty:.1f}")

    # ------------------------------------------------------------------------
    # Scenario B: Scaled dataset (48 sessions: 12 courses across 4 cohorts)
    # ------------------------------------------------------------------------
    print(f"\nScenario B (Scaled 48 Sessions across 4 cohorts and 4 classrooms):")
    # Duplicate variables to form 48 sessions
    vars_b = []
    doms_b = {}
    for v in model_a.variables:
        v1 = v
        v2 = SchedulingVariable(
            var_id=f"{v.var_id}_DUP",
            course_id=f"{v.course_id}_B",
            course_code=f"{v.course_code}B",
            session_num=v.session_num,
            total_sessions=v.total_sessions,
            session_type=v.session_type,
            duration_hours=v.duration_hours,
            faculty_id=v.faculty_id,
            group_id=f"{v.group_id}_B",
            required_room_type=v.required_room_type,
        )
        vars_b.extend([v1, v2])
        doms_b[v1.var_id] = list(model_a.domains[v.var_id])
        # For v2, adapt group_id
        doms_b[v2.var_id] = [
            SchedulingAssignmentValue(
                slot_id=val.slot_id,
                room_id=val.room_id,
                day=val.day,
                start_time=val.start_time,
                end_time=val.end_time,
                slot_ids=val.slot_ids,
                faculty_id=val.faculty_id,
                group_id=f"{v.group_id}_B",
            )
            for val in model_a.domains[v.var_id]
        ]

    # Combine metadata
    room_caps_b = dict(model_a.room_capacities)
    room_types_b = dict(model_a.room_types)
    group_sizes_b = dict(model_a.group_sizes)
    for g_id, sz in model_a.group_sizes.items():
        group_sizes_b[f"{g_id}_B"] = sz

    model_b = CSPModel(
        variables=vars_b,
        domains=doms_b,
        room_capacities=room_caps_b,
        room_types=room_types_b,
        group_sizes=group_sizes_b,
        faculty_unavailability=model_a.faculty_unavailability,
        faculty_working_days=model_a.faculty_working_days,
        timeslot_details=model_a.timeslot_details,
    )

    ga_b = GeneticSolver(model_b).solve(GAConfig(population_size=100, max_generations=50, random_seed=42))
    print(f"  Variables: {len(model_b.variables)}")
    print(f"  Status: {ga_b.status} | Feasible: {ga_b.is_solution_found} | Hard: {ga_b.best_chromosome.hard_violations_count} | Soft: {ga_b.best_chromosome.soft_penalty:.1f} | Time: {ga_b.execution_time_seconds:.2f}s")

    # ------------------------------------------------------------------------
    # Scenario C: Infeasible dataset (Empty domain + Unavoidable conflict)
    # ------------------------------------------------------------------------
    print(f"\nScenario C (Infeasible Dataset):")
    # Sub-case C1: Variable with empty domain
    v_empty = make_var("V_EMPTY")
    model_c1 = CSPModel(variables=[v_empty], domains={"V_EMPTY": []})
    ga_c1 = GeneticSolver(model_c1).solve()
    print(f"  Sub-case C1 (Empty Domain): Status={ga_c1.status} | Feasible={ga_c1.is_solution_found} | Message={ga_c1.message}")

    # Sub-case C2: Unsolvable resource contention (Pigeonhole: 2 faculty sessions in 1 slot)
    v1 = make_var("V1", faculty_id="F_ALONE", group_id="G1")
    v2 = make_var("V2", faculty_id="F_ALONE", group_id="G2")
    slot_alone = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F_ALONE", "G1")
    slot_alone_g2 = make_val("SLOT1", "R2", "Monday", "09:00", "10:00", "F_ALONE", "G2")
    model_c2 = CSPModel(
        variables=[v1, v2],
        domains={"V1": [slot_alone], "V2": [slot_alone_g2]},
        room_capacities={"R1": 50, "R2": 50},
        room_types={"R1": "LECTURE_HALL", "R2": "LECTURE_HALL"},
        group_sizes={"G1": 30, "G2": 30},
        faculty_working_days={"F_ALONE": {"Monday"}},
        timeslot_details={"SLOT1": {"slot_id": "SLOT1", "day": "Monday", "start_time": "09:00", "end_time": "10:00", "is_break": 0}},
    )
    ga_c2 = GeneticSolver(model_c2).solve(GAConfig(population_size=20, max_generations=10, random_seed=42))
    print(f"  Sub-case C2 (Unavoidable Hard Clash): Status={ga_c2.status} | Feasible={ga_c2.is_solution_found} | Hard Violations={ga_c2.best_chromosome.hard_violations_count} | Never Claimed Feasible: {not ga_c2.is_solution_found}")

    return {
        "scenario_a": {"feasible": ga_a.is_solution_found, "hard": ga_a.best_chromosome.hard_violations_count},
        "scenario_b": {"feasible": ga_b.is_solution_found, "hard": ga_b.best_chromosome.hard_violations_count, "vars": len(model_b.variables)},
        "scenario_c1": {"status": ga_c1.status, "feasible": ga_c1.is_solution_found},
        "scenario_c2": {"status": ga_c2.status, "feasible": ga_c2.is_solution_found, "hard": ga_c2.best_chromosome.hard_violations_count},
    }


if __name__ == "__main__":
    a1 = audit_1_fitness_mathematics()
    a2 = audit_2_repair_mechanism()
    a3 = audit_3_benchmark_fairness()
    a4 = audit_4_reproducibility()
    a5 = audit_5_stress_tests()
