"""Scientific Benchmarking Engine: Backtracking CSP vs Genetic Algorithm.

Provides rigorous comparative performance evaluations across:
  - Execution runtime.
  - Solution feasibility success rate.
  - Hard constraint violations (H1-H8).
  - Soft objective penalty minimization (S1-S4).
  - Computational search effort (Search Nodes vs Fitness Evaluations).
  - Multi-seed statistical stability for stochastic metaheuristics.
"""

from dataclasses import dataclass, field
import statistics
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from src.csp_engine.model import CSPModel
from src.csp_engine.solver import CSPSolver
from src.csp_engine.solver_types import SolverConfig, SolverResult, SolverStatus
from src.ga_engine.genetic_solver import GAConfig, GAResult, GeneticSolver
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.ga_engine.benchmark")

DEFAULT_BENCHMARK_SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]


@dataclass
class AlgorithmRunStats:
    """Standardized metrics for an individual algorithm execution."""

    algorithm_name: str
    execution_time_seconds: float
    is_solution_found: bool
    assigned_sessions: int
    hard_violations: int
    soft_penalty: float
    search_effort: int  # Search nodes for CSP, fitness evaluations for GA
    branching_or_generations: int  # Backtracks for CSP, generations for GA


@dataclass
class ComparativeBenchmarkResult:
    """Aggregated empirical benchmark comparing systematic CSP against stochastic GA."""

    backtracking_metrics: Dict[str, Any]
    ga_aggregate_metrics: Dict[str, Any]
    ga_individual_runs: List[Dict[str, Any]]
    comparison_table: List[Dict[str, Any]]
    dataset_variables_count: int
    equal_time_table: Optional[List[Dict[str, Any]]] = None


def run_comparative_benchmark(
    model: CSPModel,
    seeds: Optional[List[int]] = None,
    csp_config: Optional[SolverConfig] = None,
    ga_pop_size: int = 100,
    ga_generations: int = 120,
    ga_timeout: float = 30.0,
) -> ComparativeBenchmarkResult:
    """Executes a scientific side-by-side benchmark between Backtracking and GA.

    Both algorithms execute on the exact same academic dataset, CSP variables,
    domains, hard constraints, and soft scoring formulas.
    """
    logger.info("Starting comparative benchmark: Backtracking CSP vs Genetic Algorithm.")
    eval_seeds = seeds or DEFAULT_BENCHMARK_SEEDS

    # 1. Systematic CSP Backtracking Solver Run
    csp_solver = CSPSolver(model)
    csp_cfg = csp_config or SolverConfig(
        use_mrv=True,
        use_degree=True,
        use_lcv=True,
        use_forward_checking=True,
        use_ac3_preprocess=True,
    )
    csp_res: SolverResult = csp_solver.solve(csp_cfg)

    csp_soft = csp_res.validation_report.soft_penalty_score if csp_res.validation_report else -1.0
    csp_hard = len(csp_res.validation_report.hard_violations) if csp_res.validation_report else -1

    backtracking_metrics = {
        "status": csp_res.status.value,
        "is_solution_found": csp_res.is_solution_found,
        "execution_time_seconds": csp_res.statistics.execution_time_seconds,
        "nodes_explored": csp_res.statistics.nodes_explored,
        "backtracks": csp_res.statistics.backtracks,
        "constraint_checks": csp_res.statistics.constraint_checks,
        "hard_violations": csp_hard,
        "soft_penalty": csp_soft,
        "assigned_sessions": len(csp_res.assignment),
        "total_variables": len(model.variables),
    }

    # 2. Multi-Seed Genetic Algorithm Runs
    ga_solver = GeneticSolver(model)
    ga_runs: List[Dict[str, Any]] = []

    for seed in eval_seeds:
        g_cfg = GAConfig(
            population_size=ga_pop_size,
            max_generations=ga_generations,
            random_seed=seed,
            timeout_seconds=ga_timeout,
            enable_repair=True,
        )
        g_res: GAResult = ga_solver.solve(g_cfg)
        best = g_res.best_chromosome

        run_stat = {
            "seed": seed,
            "status": g_res.status,
            "is_solution_found": g_res.is_solution_found,
            "execution_time_seconds": g_res.execution_time_seconds,
            "generations_completed": g_res.generations_completed,
            "fitness_evaluations": g_res.fitness_evaluations,
            "hard_violations": best.hard_violations_count if best else -1,
            "soft_penalty": best.soft_penalty if best else -1.0,
            "best_fitness": best.fitness if best else 0.0,
            "assigned_sessions": best.assigned_count if best else 0,
        }
        ga_runs.append(run_stat)

    # 3. Compute GA Aggregates
    num_runs = len(ga_runs)
    feasible_runs = [r for r in ga_runs if r["is_solution_found"]]
    success_rate = (len(feasible_runs) / num_runs) * 100.0 if num_runs > 0 else 0.0

    times = [r["execution_time_seconds"] for r in ga_runs]
    mean_time = statistics.mean(times) if times else 0.0

    soft_scores = [r["soft_penalty"] for r in feasible_runs] if feasible_runs else [r["soft_penalty"] for r in ga_runs]
    best_soft = min(soft_scores) if soft_scores else -1.0
    mean_soft = statistics.mean(soft_scores) if soft_scores else -1.0

    fitness_scores = [r["best_fitness"] for r in ga_runs]
    best_fitness = max(fitness_scores) if fitness_scores else 0.0
    mean_fitness = statistics.mean(fitness_scores) if fitness_scores else 0.0

    ga_aggregate_metrics = {
        "total_runs": num_runs,
        "feasible_runs_count": len(feasible_runs),
        "success_rate_percent": success_rate,
        "mean_execution_time_seconds": mean_time,
        "min_execution_time_seconds": min(times) if times else 0.0,
        "max_execution_time_seconds": max(times) if times else 0.0,
        "best_soft_penalty": best_soft,
        "mean_soft_penalty": mean_soft,
        "best_fitness": best_fitness,
        "mean_fitness": mean_fitness,
        "seeds_evaluated": eval_seeds,
    }

    # 4. Side-by-Side Comparison Matrix
    comparison_table = [
        {
            "Metric": "Algorithmic Paradigm",
            "Backtracking CSP (Phase 4)": "Systematic Constraint Satisfaction",
            "Genetic Algorithm (Phase 5)": "Stochastic Evolutionary Optimization",
        },
        {
            "Metric": "Feasible Solution Found",
            "Backtracking CSP (Phase 4)": "Yes (Deterministic)" if csp_res.is_solution_found else "No",
            "Genetic Algorithm (Phase 5)": f"{len(feasible_runs)}/{num_runs} Runs ({success_rate:.1f}%)",
        },
        {
            "Metric": "Execution Runtime",
            "Backtracking CSP (Phase 4)": f"{csp_res.statistics.execution_time_seconds:.3f} s",
            "Genetic Algorithm (Phase 5)": f"{mean_time:.3f} s (Mean across {num_runs} seeds)",
        },
        {
            "Metric": "Hard Violations (H1-H8)",
            "Backtracking CSP (Phase 4)": str(csp_hard),
            "Genetic Algorithm (Phase 5)": f"0 (in {len(feasible_runs)}/{num_runs} runs)",
        },
        {
            "Metric": "Best Soft Penalty Score",
            "Backtracking CSP (Phase 4)": f"{csp_soft:.1f}",
            "Genetic Algorithm (Phase 5)": f"{best_soft:.1f} (Mean: {mean_soft:.1f})",
        },
        {
            "Metric": "Search Effort",
            "Backtracking CSP (Phase 4)": f"{csp_res.statistics.nodes_explored:,} Search Nodes",
            "Genetic Algorithm (Phase 5)": f"{statistics.mean([r['fitness_evaluations'] for r in ga_runs]):,.0f} Fitness Evals",
        },
        {
            "Metric": "Branching / Iterations",
            "Backtracking CSP (Phase 4)": f"{csp_res.statistics.backtracks} Backtracks",
            "Genetic Algorithm (Phase 5)": f"{statistics.mean([r['generations_completed'] for r in ga_runs]):.0f} Generations",
        },
        {
            "Metric": "Theoretical Guarantees",
            "Backtracking CSP (Phase 4)": "Complete (Proves Satisfiability/Infeasibility)",
            "Genetic Algorithm (Phase 5)": "Incomplete (Probabilistic soft optimization)",
        },
    ]

    return ComparativeBenchmarkResult(
        backtracking_metrics=backtracking_metrics,
        ga_aggregate_metrics=ga_aggregate_metrics,
        ga_individual_runs=ga_runs,
        comparison_table=comparison_table,
        dataset_variables_count=len(model.variables),
    )


def run_equal_time_budget_benchmark(
    model: CSPModel,
    time_budget_seconds: float = 5.0,
    ga_seed: int = 42,
    ga_pop_size: int = 100,
) -> List[Dict[str, Any]]:
    """Executes a strictly fair comparison where both algorithms receive an identical wall-clock time budget."""
    logger.info("Executing equal time budget benchmark (budget=%.2fs)...", time_budget_seconds)

    # 1. Backtracking CSP Optimization Run
    csp_solver = CSPSolver(model)
    csp_res = csp_solver.solve_optimize(
        time_budget_seconds=time_budget_seconds,
        config=SolverConfig(use_mrv=True, use_degree=True, use_lcv=False, use_forward_checking=True),
    )
    csp_soft = csp_res.validation_report.soft_penalty_score if csp_res.validation_report else -1.0
    csp_hard = len(csp_res.validation_report.hard_violations) if csp_res.validation_report else -1

    # 2. Genetic Algorithm Optimization Run with Identical Time Budget
    ga_solver = GeneticSolver(model)
    ga_cfg = GAConfig(
        population_size=ga_pop_size,
        max_generations=2000,  # Bound strictly by timeout
        random_seed=ga_seed,
        timeout_seconds=time_budget_seconds,
        enable_repair=True,
    )
    ga_res = ga_solver.solve(ga_cfg)
    best_chrom = ga_res.best_chromosome
    ga_soft = best_chrom.soft_penalty if best_chrom else -1.0
    ga_hard = best_chrom.hard_violations_count if best_chrom else -1

    equal_time_matrix = [
        {
            "Metric": "Allocated Time Budget",
            "Backtracking CSP (Optimization)": f"{time_budget_seconds:.2f} s",
            "Genetic Algorithm (Optimization)": f"{time_budget_seconds:.2f} s",
        },
        {
            "Metric": "Actual Measured Runtime",
            "Backtracking CSP (Optimization)": f"{csp_res.statistics.execution_time_seconds:.3f} s",
            "Genetic Algorithm (Optimization)": f"{ga_res.execution_time_seconds:.3f} s",
        },
        {
            "Metric": "Best Feasible Solution Found",
            "Backtracking CSP (Optimization)": "Yes" if csp_res.is_solution_found else "No",
            "Genetic Algorithm (Optimization)": "Yes" if ga_res.is_solution_found else "No",
        },
        {
            "Metric": "Hard Violations (H1-H8)",
            "Backtracking CSP (Optimization)": str(csp_hard),
            "Genetic Algorithm (Optimization)": str(ga_hard),
        },
        {
            "Metric": "Best Soft Penalty Score (Lower is Better)",
            "Backtracking CSP (Optimization)": f"{csp_soft:.1f}",
            "Genetic Algorithm (Optimization)": f"{ga_soft:.1f}",
        },
        {
            "Metric": "Computational Effort",
            "Backtracking CSP (Optimization)": f"{csp_res.statistics.nodes_explored:,} Search Nodes",
            "Genetic Algorithm (Optimization)": f"{ga_res.fitness_evaluations:,} Fitness Evals",
        },
        {
            "Metric": "Search Depth / Iterations",
            "Backtracking CSP (Optimization)": f"{csp_res.statistics.backtracks:,} Backtracks",
            "Genetic Algorithm (Optimization)": f"{ga_res.generations_completed:,} Generations",
        },
    ]

    return equal_time_matrix
