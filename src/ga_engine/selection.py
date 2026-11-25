"""Selection operators for Academic Timetable Genetic Algorithm."""

import random
from typing import Optional
from src.ga_engine.chromosome import TimetableChromosome
from src.ga_engine.population import Population


def tournament_selection(
    population: Population,
    tournament_size: int = 3,
    rng: Optional[random.Random] = None,
) -> TimetableChromosome:
    """Selects the fittest individual from a random tournament sample of the population.

    Args:
        population: Current cohort of chromosomes.
        tournament_size: Number of competitors in each tournament.
        rng: Deterministic random number generator.

    Returns:
        The winning TimetableChromosome.
    """
    if rng is None:
        rng = random.Random()

    if len(population) == 0:
        raise ValueError("Cannot perform tournament selection on an empty population.")

    k = min(tournament_size, len(population))
    competitors = rng.sample(population.chromosomes, k)
    winner = max(competitors, key=lambda c: c.fitness)
    return winner
