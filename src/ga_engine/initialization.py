"""Population initialization routines for the Timetable Genetic Algorithm.

Constructs initial candidate chromosomes by sampling from pre-filtered CSP variable domains,
supporting reproducible pseudorandom seeds and domain emptiness diagnostic reporting.
"""

import random
from typing import Dict, List, Optional, Tuple

from src.csp_engine.domain_types import SchedulingAssignmentValue, SchedulingVariable
from src.csp_engine.model import CSPModel
from src.ga_engine.chromosome import TimetableChromosome
from src.ga_engine.population import Population
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.ga_engine.initialization")


def initialize_population(
    model: CSPModel,
    population_size: int = 100,
    rng: Optional[random.Random] = None,
) -> Tuple[Population, List[str]]:
    """Generates an initial population of candidate timetable chromosomes.

    Args:
        model: Academic CSPModel providing variables and pre-filtered domains.
        population_size: Number of individual chromosomes to initialize.
        rng: Deterministic random number generator instance.

    Returns:
        Tuple of (Population, initialization_errors)
    """
    if rng is None:
        rng = random.Random()

    errors: List[str] = []
    variables = model.variables
    domains = model.domains

    # Check for variables with empty domains (e.g. impossible room/time constraints)
    empty_domain_vars = [v.var_id for v in variables if not domains.get(v.var_id)]
    if empty_domain_vars:
        msg = f"Cannot generate complete initial timetable: variables {empty_domain_vars} have empty domains."
        logger.error(msg)
        errors.append(msg)
        return Population(chromosomes=[], generation=0), errors

    population = Population(chromosomes=[], generation=0)

    for i in range(population_size):
        genes: Dict[str, SchedulingAssignmentValue] = {}
        for var in variables:
            var_domain = domains[var.var_id]
            # Randomly select a legal domain assignment coordinate
            chosen_val = rng.choice(var_domain)
            genes[var.var_id] = chosen_val

        chromosome = TimetableChromosome(genes=genes)
        population.add(chromosome)

    logger.info(
        "Successfully initialized GA population with %d chromosomes across %d variables.",
        len(population),
        len(variables),
    )
    return population, errors
