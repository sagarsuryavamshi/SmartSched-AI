"""GA Engine package exports."""

from src.ga_engine.benchmark import (
    ComparativeBenchmarkResult,
    run_comparative_benchmark,
    run_equal_time_budget_benchmark,
)
from src.ga_engine.chromosome import TimetableChromosome
from src.ga_engine.crossover import uniform_crossover
from src.ga_engine.fitness import evaluate_fitness
from src.ga_engine.genetic_solver import GAConfig, GAResult, GeneticSolver
from src.ga_engine.initialization import initialize_population
from src.ga_engine.mutation import mutate_chromosome
from src.ga_engine.population import Population
from src.ga_engine.repair import repair_chromosome
from src.ga_engine.selection import tournament_selection

__all__ = [
    "ComparativeBenchmarkResult",
    "GAConfig",
    "GAResult",
    "GeneticSolver",
    "Population",
    "TimetableChromosome",
    "evaluate_fitness",
    "initialize_population",
    "mutate_chromosome",
    "repair_chromosome",
    "run_comparative_benchmark",
    "run_equal_time_budget_benchmark",
    "tournament_selection",
    "uniform_crossover",
]
