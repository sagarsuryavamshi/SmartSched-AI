"""Comprehensive Unit and Integration Test Suite for SmartSched AI Phase 5: Genetic Algorithm.

Covers all 17 Phase 5 testing requirements:
  1. Chromosome construction and properties.
  2. Chromosome-to-timetable conversion and round-tripping.
  3. Population initialization from CSP domains.
  4. Fitness evaluation mathematical formula.
  5. Hard constraint strict prioritization over soft objectives.
  6. Soft penalty calculation.
  7. Tournament selection operator.
  8. Uniform crossover operator and variable preservation.
  9. Domain-guided mutation operator.
  10. Elitism preservation across generations.
  11. Targeted constraint repair mechanism.
  12. Complete evolutionary generation loop and monotonic elite fitness.
  13. Deterministic random seed reproducibility.
  14. Inherently infeasible dataset handling.
  15. Scientific Backtracking vs GA benchmarking engine.
  16. SQLite timetable persistence of GA solutions.
  17. UI integration and module exports.
"""

import os
import random
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
from src.csp_engine.model import CSPModel
from src.database.db_manager import init_db
from src.database.timetable_repository import (
    load_saved_timetable,
    save_timetable_solution,
)
from src.data_management.loader import seed_synthetic_data
from src.ga_engine.benchmark import (
    ComparativeBenchmarkResult,
    run_comparative_benchmark,
)
from src.ga_engine.chromosome import TimetableChromosome
from src.ga_engine.crossover import uniform_crossover
from src.ga_engine.fitness import HARD_CONSTRAINT_WEIGHT, evaluate_fitness
from src.ga_engine.genetic_solver import GAConfig, GAResult, GeneticSolver
from src.ga_engine.initialization import initialize_population
from src.ga_engine.mutation import mutate_chromosome
from src.ga_engine.population import Population
from src.ga_engine.repair import repair_chromosome
from src.ga_engine.selection import tournament_selection


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


class TestGAEnginePhase5(unittest.TestCase):
    """Independent technical QA test suite for SmartSched AI Phase 5 Genetic Algorithm."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_smartsched_ga.db")
        init_db(self.test_db)
        seed_synthetic_data(self.test_db, overwrite=True)
        self.model = CSPModel.build_from_db(self.test_db)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # ========================================================================
    # 1. Chromosome Construction & Properties
    # ========================================================================
    def test_01_chromosome_construction(self) -> None:
        val1 = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F1", "G1")
        val2 = make_val("SLOT2", "R1", "Monday", "10:00", "11:00", "F1", "G1")
        chromosome = TimetableChromosome(genes={"V1": val1, "V2": val2})

        self.assertEqual(len(chromosome), 2)
        self.assertEqual(chromosome.assigned_count, 2)
        self.assertTrue(chromosome.is_complete({"V1", "V2"}))
        self.assertFalse(chromosome.is_complete({"V1", "V2", "V3"}))

        # Clone test
        cloned = chromosome.clone()
        self.assertEqual(cloned.genes, chromosome.genes)
        cloned.genes["V3"] = val1
        self.assertNotIn("V3", chromosome.genes)

    # ========================================================================
    # 2. Chromosome-to-Timetable Conversion
    # ========================================================================
    def test_02_chromosome_conversion(self) -> None:
        val1 = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F1", "G1")
        chromosome = TimetableChromosome(genes={"V1": val1})

        asg_dict = chromosome.to_assignment_dict()
        self.assertIsInstance(asg_dict, dict)
        self.assertEqual(asg_dict["V1"], val1)

        # Round trip
        restored = TimetableChromosome.from_assignment_dict(asg_dict)
        self.assertEqual(restored.genes, chromosome.genes)

    # ========================================================================
    # 3. Population Initialization from CSP Domains
    # ========================================================================
    def test_03_population_initialization(self) -> None:
        rng = random.Random(42)
        pop_size = 30
        population, errors = initialize_population(self.model, population_size=pop_size, rng=rng)

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(population), pop_size)

        all_var_ids = {v.var_id for v in self.model.variables}
        for chromosome in population:
            self.assertEqual(len(chromosome), len(self.model.variables))
            self.assertTrue(chromosome.is_complete(all_var_ids))
            # Verify each gene is an authentic domain option for that variable
            for var_id, gene_val in chromosome.genes.items():
                self.assertIn(gene_val, self.model.domains[var_id])

    # ========================================================================
    # 4. Fitness Evaluation Formula
    # ========================================================================
    def test_04_fitness_evaluation_formula(self) -> None:
        rng = random.Random(42)
        population, _ = initialize_population(self.model, population_size=5, rng=rng)
        chrom = population[0]

        fitness = evaluate_fitness(chrom, self.model)
        self.assertGreater(fitness, 0.0)
        self.assertLessEqual(fitness, 1.0)

        # Verify mathematical consistency
        cost = (HARD_CONSTRAINT_WEIGHT * chrom.hard_violations_count) + chrom.soft_penalty
        expected_fitness = 1.0 / (1.0 + cost)
        self.assertAlmostEqual(chrom.fitness, expected_fitness, places=7)

    # ========================================================================
    # 5. Hard Constraint Prioritization
    # ========================================================================
    def test_05_hard_constraint_prioritization(self) -> None:
        # Construct an artificial feasible chromosome (H=0, high soft penalty)
        chrom_feasible = TimetableChromosome(genes={})
        chrom_feasible.hard_violations_count = 0
        chrom_feasible.soft_penalty = 500.0  # high soft penalty
        cost_feas = (HARD_CONSTRAINT_WEIGHT * 0) + 500.0
        chrom_feasible.fitness = 1.0 / (1.0 + cost_feas)

        # Construct an artificial infeasible chromosome (H=1, zero soft penalty)
        chrom_infeasible = TimetableChromosome(genes={})
        chrom_infeasible.hard_violations_count = 1
        chrom_infeasible.soft_penalty = 0.0  # zero soft penalty
        cost_infeas = (HARD_CONSTRAINT_WEIGHT * 1) + 0.0
        chrom_infeasible.fitness = 1.0 / (1.0 + cost_infeas)

        # Feasible chromosome MUST strictly have higher fitness than infeasible
        self.assertGreater(
            chrom_feasible.fitness,
            chrom_infeasible.fitness,
            "A feasible timetable with high soft penalty must strictly out-rank an invalid timetable with 1 hard violation",
        )

    # ========================================================================
    # 6. Soft Penalty Calculation
    # ========================================================================
    def test_06_soft_penalty_calculation(self) -> None:
        rng = random.Random(42)
        population, _ = initialize_population(self.model, population_size=1, rng=rng)
        chrom = population[0]
        evaluate_fitness(chrom, self.model)

        self.assertIsInstance(chrom.soft_penalty, float)
        self.assertGreaterEqual(chrom.soft_penalty, 0.0)
        self.assertIsNotNone(chrom.validation_report)
        self.assertEqual(chrom.soft_penalty, chrom.validation_report.soft_penalty_score)

    # ========================================================================
    # 7. Tournament Selection
    # ========================================================================
    def test_07_tournament_selection(self) -> None:
        c1 = TimetableChromosome(fitness=0.001)
        c2 = TimetableChromosome(fitness=0.005)  # Highest
        c3 = TimetableChromosome(fitness=0.002)
        pop = Population(chromosomes=[c1, c2, c3])

        # Tournament with all 3 competitors must always return c2
        winner = tournament_selection(pop, tournament_size=3, rng=random.Random(42))
        self.assertEqual(winner, c2)

    # ========================================================================
    # 8. Crossover Operator and Variable Preservation
    # ========================================================================
    def test_08_crossover_variable_preservation(self) -> None:
        rng = random.Random(42)
        pop, _ = initialize_population(self.model, population_size=2, rng=rng)
        parent1, parent2 = pop[0], pop[1]

        child1, child2 = uniform_crossover(parent1, parent2, crossover_prob=1.0, rng=rng)

        # Children must have all variables present
        all_vars = {v.var_id for v in self.model.variables}
        self.assertEqual(set(child1.genes.keys()), all_vars)
        self.assertEqual(set(child2.genes.keys()), all_vars)

        # Each gene must come from either parent 1 or parent 2
        for v_id in all_vars:
            self.assertIn(child1.genes[v_id], [parent1.genes[v_id], parent2.genes[v_id]])
            self.assertIn(child2.genes[v_id], [parent1.genes[v_id], parent2.genes[v_id]])

    # ========================================================================
    # 9. Domain-Guided Mutation Operator
    # ========================================================================
    def test_09_mutation_operator(self) -> None:
        rng = random.Random(42)
        pop, _ = initialize_population(self.model, population_size=1, rng=rng)
        chrom = pop[0].clone()

        # Mutation with 100% probability
        mut_count = mutate_chromosome(chrom, self.model.domains, mutation_prob=1.0, rng=rng)

        self.assertGreater(mut_count, 0)
        # All mutated genes must remain within legal domain options
        for v_id, gene_val in chrom.genes.items():
            self.assertIn(gene_val, self.model.domains[v_id])

    # ========================================================================
    # 10. Elitism Preservation Across Generations
    # ========================================================================
    def test_10_elitism_preservation(self) -> None:
        solver = GeneticSolver(self.model)
        cfg = GAConfig(
            population_size=20,
            max_generations=5,
            elitism_count=3,
            random_seed=42,
            enable_repair=False,
        )
        res = solver.solve(cfg)

        # Best fitness in history must be monotonically non-decreasing
        hist = res.history_best_fitness
        for i in range(len(hist) - 1):
            self.assertGreaterEqual(
                hist[i + 1],
                hist[i],
                f"Elitism violation: best fitness decreased at generation {i+1}",
            )

    # ========================================================================
    # 11. Targeted Constraint Repair Mechanism
    # ========================================================================
    def test_11_repair_mechanism(self) -> None:
        rng = random.Random(42)
        pop, _ = initialize_population(self.model, population_size=1, rng=rng)
        chrom = pop[0]
        evaluate_fitness(chrom, self.model)

        initial_hard_viols = chrom.hard_violations_count
        if initial_hard_viols > 0:
            is_feas, swaps = repair_chromosome(chrom, self.model, max_repair_passes=5, rng=rng)
            # Hard violations after repair should be <= initial
            self.assertLessEqual(chrom.hard_violations_count, initial_hard_viols)

    # ========================================================================
    # 12. Complete Evolutionary Loop
    # ========================================================================
    def test_12_complete_generation_loop(self) -> None:
        solver = GeneticSolver(self.model)
        cfg = GAConfig(
            population_size=30,
            max_generations=15,
            crossover_prob=0.85,
            mutation_prob=0.10,
            elitism_count=2,
            random_seed=42,
        )
        res = solver.solve(cfg)

        self.assertEqual(res.generations_completed, 15)
        self.assertGreater(res.fitness_evaluations, 30)
        self.assertGreater(res.crossover_operations, 0)
        self.assertIsNotNone(res.best_chromosome)
        self.assertEqual(len(res.history_best_fitness), 16)  # gen 0 + 15 gens

    # ========================================================================
    # 13. Deterministic Random Seed Reproducibility
    # ========================================================================
    def test_13_deterministic_seed_reproducibility(self) -> None:
        solver = GeneticSolver(self.model)
        cfg1 = GAConfig(population_size=20, max_generations=8, random_seed=999)
        cfg2 = GAConfig(population_size=20, max_generations=8, random_seed=999)

        res1 = solver.solve(cfg1)
        res2 = solver.solve(cfg2)

        self.assertEqual(res1.history_best_fitness, res2.history_best_fitness)
        self.assertEqual(res1.best_chromosome.genes, res2.best_chromosome.genes)

    # ========================================================================
    # 14. Inherently Infeasible Dataset Handling
    # ========================================================================
    def test_14_infeasible_dataset_handling(self) -> None:
        # Create an unsatisfiable pigeonhole model:
        # 2 sessions for the same faculty at the exact same single available timeslot
        v1 = make_var("V1", faculty_id="F_SAME", group_id="G1")
        v2 = make_var("V2", faculty_id="F_SAME", group_id="G2")
        val_shared = make_val("SLOT1", "R1", "Monday", "09:00", "10:00", "F_SAME", "G1")
        val_shared_g2 = make_val("SLOT1", "R2", "Monday", "09:00", "10:00", "F_SAME", "G2")

        unsat_model = CSPModel(
            variables=[v1, v2],
            domains={"V1": [val_shared], "V2": [val_shared_g2]},
            room_capacities={"R1": 50, "R2": 50},
            room_types={"R1": "LECTURE_HALL", "R2": "LECTURE_HALL"},
            group_sizes={"G1": 30, "G2": 30},
            faculty_working_days={"F_SAME": {"Monday"}},
            timeslot_details={"SLOT1": {"slot_id": "SLOT1", "day": "Monday", "start_time": "09:00", "end_time": "10:00", "is_break": 0}},
        )

        solver = GeneticSolver(unsat_model)
        cfg = GAConfig(population_size=10, max_generations=5, random_seed=42)
        res = solver.solve(cfg)

        self.assertFalse(res.is_solution_found)
        self.assertGreater(res.best_chromosome.hard_violations_count, 0)
        self.assertIn("remaining hard violations", res.message)

    # ========================================================================
    # 15. Scientific Backtracking vs GA Benchmarking
    # ========================================================================
    def test_15_backtracking_vs_ga_benchmarking(self) -> None:
        bench = run_comparative_benchmark(
            model=self.model,
            seeds=[42, 101],
            ga_pop_size=20,
            ga_generations=10,
        )

        self.assertIsInstance(bench, ComparativeBenchmarkResult)
        self.assertEqual(bench.backtracking_metrics["status"], "SUCCESS")
        self.assertEqual(bench.ga_aggregate_metrics["total_runs"], 2)
        self.assertGreater(len(bench.comparison_table), 5)
        self.assertEqual(len(bench.ga_individual_runs), 2)

    # ========================================================================
    # 16. SQLite Timetable Persistence of GA Solutions
    # ========================================================================
    def test_16_sqlite_persistence_of_ga_solution(self) -> None:
        solver = GeneticSolver(self.model)
        cfg = GAConfig(population_size=50, max_generations=30, random_seed=42)
        res = solver.solve(cfg)

        self.assertIsNotNone(res.best_chromosome)
        run_id = "GA_TEST_RUN"
        ok, msg = save_timetable_solution(
            assignment=res.best_chromosome.genes,
            variables_map=self.model.variables_map,
            run_id=run_id,
            overwrite_existing=True,
            db_path=self.test_db,
        )

        self.assertTrue(ok)
        loaded = load_saved_timetable(run_id=run_id, db_path=self.test_db)
        self.assertGreater(len(loaded), 0)
        self.assertEqual(loaded[0]["generation_run_id"], run_id)

    # ========================================================================
    # 17. UI Integration & Exports
    # ========================================================================
    def test_17_ui_integration_exports(self) -> None:
        from src.frontend import render_ga_view
        self.assertTrue(callable(render_ga_view))

        from src.optimization.genetic_algorithm import GeneticAlgorithmScheduler
        scheduler = GeneticAlgorithmScheduler(population_size=10, generations=2)
        out = scheduler.run(self.model)
        self.assertIn("status", out)
        self.assertEqual(out["algorithm"], "Genetic Algorithm")


if __name__ == "__main__":
    unittest.main()
