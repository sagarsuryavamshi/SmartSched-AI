"""Metaheuristic optimization algorithms (Genetic Algorithm, Local Search) for comparison."""

from typing import Any, Dict, Optional
from src.csp_engine.model import CSPModel
from src.ga_engine.genetic_solver import GAConfig, GAResult, GeneticSolver
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.optimization")


class GeneticAlgorithmScheduler:
    """Genetic Algorithm optimization solver for university timetabling comparison."""

    def __init__(
        self,
        population_size: int = 100,
        mutation_rate: float = 0.08,
        crossover_rate: float = 0.85,
        generations: int = 150,
        random_seed: Optional[int] = 42,
    ) -> None:
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.generations = generations
        self.random_seed = random_seed
        self.config = GAConfig(
            population_size=population_size,
            max_generations=generations,
            crossover_prob=crossover_rate,
            mutation_prob=mutation_rate,
            random_seed=random_seed,
        )

    def run(self, model: Optional[CSPModel] = None) -> Dict[str, Any]:
        """Runs the complete Genetic Algorithm on the provided CSPModel."""
        logger.info("GeneticAlgorithmScheduler running (pop=%s, gen=%s)", self.population_size, self.generations)
        solver = GeneticSolver(model)
        result: GAResult = solver.solve(self.config)
        return {
            "status": result.status,
            "algorithm": "Genetic Algorithm",
            "is_solution_found": result.is_solution_found,
            "best_fitness": result.best_chromosome.fitness if result.best_chromosome else 0.0,
            "generations_run": result.generations_completed,
            "runtime_seconds": result.execution_time_seconds,
            "hard_violations": result.best_chromosome.hard_violations_count if result.best_chromosome else -1,
            "soft_penalty": result.best_chromosome.soft_penalty if result.best_chromosome else -1.0,
            "result_object": result,
        }
