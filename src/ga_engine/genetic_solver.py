"""Production Genetic Algorithm Solver for Academic Timetable Generation.

Executes evolutionary optimization:
  1. Population initialization from CSP domains.
  2. Hierarchical fitness evaluation (Hard constraint feasibility > Soft penalty minimization).
  3. Elitism preservation of top candidate timetables.
  4. Tournament selection.
  5. Uniform crossover.
  6. Domain-guided mutation.
  7. Targeted constraint repair.
  8. Telemetry tracking across generations.
"""

from dataclasses import dataclass, field
import random
import time
from typing import Callable, List, Optional

from src.csp_engine.model import CSPModel
from src.ga_engine.chromosome import TimetableChromosome
from src.ga_engine.crossover import uniform_crossover
from src.ga_engine.fitness import evaluate_fitness
from src.ga_engine.initialization import initialize_population
from src.ga_engine.mutation import mutate_chromosome
from src.ga_engine.population import Population
from src.ga_engine.repair import repair_chromosome
from src.ga_engine.selection import tournament_selection
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.ga_engine.solver")


@dataclass
class GAConfig:
    """Configuration parameters for the Genetic Algorithm timetable generator."""

    population_size: int = 100
    max_generations: int = 150
    crossover_prob: float = 0.85
    mutation_prob: float = 0.08
    elitism_count: int = 4
    tournament_size: int = 3
    random_seed: Optional[int] = 42
    timeout_seconds: float = 30.0
    enable_repair: bool = True
    repair_prob: float = 0.40
    target_soft_penalty: Optional[float] = None


@dataclass
class GAResult:
    """Execution telemetry and outcome of a Genetic Algorithm search run."""

    status: str
    is_solution_found: bool
    best_chromosome: Optional[TimetableChromosome]
    generations_completed: int = 0
    fitness_evaluations: int = 0
    crossover_operations: int = 0
    mutation_operations: int = 0
    repair_attempts: int = 0
    successful_repairs: int = 0
    execution_time_seconds: float = 0.0
    history_best_fitness: List[float] = field(default_factory=list)
    history_best_hard_violations: List[int] = field(default_factory=list)
    history_best_soft_penalty: List[float] = field(default_factory=list)
    history_avg_fitness: List[float] = field(default_factory=list)
    message: str = ""
    config_used: GAConfig = field(default_factory=GAConfig)


class GeneticSolver:
    """Autonomous Genetic Algorithm Engine for Timetable Optimization."""

    def __init__(self, model: Optional[CSPModel] = None) -> None:
        self.model = model

    def solve(
        self,
        config: Optional[GAConfig] = None,
        model: Optional[CSPModel] = None,
        callback: Optional[Callable[[int, int, TimetableChromosome], None]] = None,
    ) -> GAResult:
        """Executes the Genetic Algorithm evolutionary cycle."""
        if model is not None:
            self.model = model

        if self.model is None:
            return GAResult(
                status="INVALID_CONFIGURATION",
                is_solution_found=False,
                best_chromosome=None,
                message="No CSPModel provided to GeneticSolver.",
            )

        cfg = config or GAConfig()
        rng = random.Random(cfg.random_seed)
        start_time = time.perf_counter()

        # Handle empty model problem
        if not self.model.variables:
            return GAResult(
                status="EMPTY_PROBLEM",
                is_solution_found=True,
                best_chromosome=TimetableChromosome(),
                generations_completed=0,
                execution_time_seconds=time.perf_counter() - start_time,
                message="Problem contains zero variables to schedule.",
                config_used=cfg,
            )

        # 1. Initialization
        population, init_errors = initialize_population(
            model=self.model,
            population_size=cfg.population_size,
            rng=rng,
        )

        if init_errors or len(population) == 0:
            return GAResult(
                status="INITIALIZATION_FAILED",
                is_solution_found=False,
                best_chromosome=None,
                execution_time_seconds=time.perf_counter() - start_time,
                message=f"Population initialization failed: {'; '.join(init_errors)}",
                config_used=cfg,
            )

        # Telemetry counters
        fitness_evals = 0
        crossover_ops = 0
        mutation_ops = 0
        repair_attempts = 0
        successful_repairs = 0

        # Evaluate initial population
        for ind in population:
            evaluate_fitness(ind, self.model)
            fitness_evals += 1

        population.sort_by_fitness(descending=True)
        best_overall = population.get_best().clone()

        # Convergence tracking lists
        hist_fitness = [best_overall.fitness]
        hist_hard = [best_overall.hard_violations_count]
        hist_soft = [best_overall.soft_penalty]
        hist_avg = [population.average_fitness]

        logger.info(
            "GA Generation 0: Best Fitness=%.6f, Hard Violations=%d, Soft Penalty=%.1f",
            best_overall.fitness,
            best_overall.hard_violations_count,
            best_overall.soft_penalty,
        )

        # 2. Evolutionary Loop
        status = "MAX_GENERATIONS_REACHED"
        generations_run = 0

        for gen in range(1, cfg.max_generations + 1):
            generations_run = gen

            # Check timeout limit
            elapsed = time.perf_counter() - start_time
            if elapsed >= cfg.timeout_seconds:
                status = "TIMEOUT"
                logger.warning("GA halted: Timeout (%.2fs) exceeded at generation %d.", cfg.timeout_seconds, gen)
                break

            # Check early stopping target if specified
            if (
                best_overall.is_feasible
                and cfg.target_soft_penalty is not None
                and best_overall.soft_penalty <= cfg.target_soft_penalty
            ):
                status = "TARGET_REACHED"
                logger.info("GA reached target soft penalty (%.1f) at generation %d.", cfg.target_soft_penalty, gen)
                break

            # Elitism: preserve top E individuals
            next_generation_chromosomes: List[TimetableChromosome] = []
            elitism_n = min(cfg.elitism_count, len(population))
            for i in range(elitism_n):
                next_generation_chromosomes.append(population[i].clone())

            # Spawn offspring to fill population
            while len(next_generation_chromosomes) < cfg.population_size:
                # Tournament Selection
                p1 = tournament_selection(population, cfg.tournament_size, rng)
                p2 = tournament_selection(population, cfg.tournament_size, rng)

                # Crossover
                c1, c2 = uniform_crossover(p1, p2, cfg.crossover_prob, rng)
                crossover_ops += 1

                # Mutation
                mut1 = mutate_chromosome(c1, self.model.domains, cfg.mutation_prob, rng)
                mut2 = mutate_chromosome(c2, self.model.domains, cfg.mutation_prob, rng)
                mutation_ops += (mut1 + mut2)

                # Repair heuristic
                if cfg.enable_repair:
                    if rng.random() < cfg.repair_prob:
                        repair_attempts += 1
                        _, swaps1 = repair_chromosome(c1, self.model, rng=rng)
                        successful_repairs += swaps1

                    if rng.random() < cfg.repair_prob:
                        repair_attempts += 1
                        _, swaps2 = repair_chromosome(c2, self.model, rng=rng)
                        successful_repairs += swaps2

                # Evaluate fitness
                evaluate_fitness(c1, self.model)
                evaluate_fitness(c2, self.model)
                fitness_evals += 2

                next_generation_chromosomes.append(c1)
                if len(next_generation_chromosomes) < cfg.population_size:
                    next_generation_chromosomes.append(c2)

            # Update population for next generation
            population = Population(chromosomes=next_generation_chromosomes, generation=gen)
            population.sort_by_fitness(descending=True)
            gen_best = population.get_best()

            # Update global best if strictly improved
            if gen_best is not None and gen_best.fitness > best_overall.fitness:
                best_overall = gen_best.clone()

            # Record history
            hist_fitness.append(best_overall.fitness)
            hist_hard.append(best_overall.hard_violations_count)
            hist_soft.append(best_overall.soft_penalty)
            hist_avg.append(population.average_fitness)

            # Trigger optional progress callback
            if callback is not None:
                callback(gen, cfg.max_generations, best_overall)

        total_time = time.perf_counter() - start_time

        if best_overall.is_feasible:
            if status != "TARGET_REACHED":
                status = "SUCCESS"
            msg = (
                f"Genetic Algorithm successfully evolved a conflict-free timetable "
                f"({len(best_overall.genes)}/{len(self.model.variables)} sessions assigned, "
                f"0 hard violations, Soft Penalty={best_overall.soft_penalty:.1f}) in {total_time:.2f}s."
            )
        else:
            msg = (
                f"Genetic Algorithm terminated ({status}): Found best timetable with "
                f"{best_overall.hard_violations_count} remaining hard violations in {total_time:.2f}s."
            )

        logger.info("GA Finished: %s", msg)

        return GAResult(
            status=status,
            is_solution_found=best_overall.is_feasible,
            best_chromosome=best_overall,
            generations_completed=generations_run,
            fitness_evaluations=fitness_evals,
            crossover_operations=crossover_ops,
            mutation_operations=mutation_ops,
            repair_attempts=repair_attempts,
            successful_repairs=successful_repairs,
            execution_time_seconds=total_time,
            history_best_fitness=hist_fitness,
            history_best_hard_violations=hist_hard,
            history_best_soft_penalty=hist_soft,
            history_avg_fitness=hist_avg,
            message=msg,
            config_used=cfg,
        )
