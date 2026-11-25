"""Mutation operators for Academic Timetable Genetic Algorithm."""

import random
from typing import Dict, List, Optional
from src.csp_engine.domain_types import SchedulingAssignmentValue
from src.ga_engine.chromosome import TimetableChromosome


def mutate_chromosome(
    chromosome: TimetableChromosome,
    domains: Dict[str, List[SchedulingAssignmentValue]],
    mutation_prob: float = 0.10,
    rng: Optional[random.Random] = None,
) -> int:
    """Mutates a timetable chromosome by randomly reassigning genes to alternate domain coordinates.

    Args:
        chromosome: Target chromosome to mutate in-place.
        domains: Pre-filtered legal domains for each variable.
        mutation_prob: Per-gene probability of undergoing mutation.
        rng: Deterministic random generator.

    Returns:
        Total number of gene mutations applied.
    """
    if rng is None:
        rng = random.Random()

    mutations_applied = 0

    for var_id, current_val in list(chromosome.genes.items()):
        if rng.random() < mutation_prob:
            var_domain = domains.get(var_id, [])
            if len(var_domain) > 1:
                # Prefer selecting a different assignment coordinate
                alternatives = [opt for opt in var_domain if opt != current_val]
                new_val = rng.choice(alternatives) if alternatives else rng.choice(var_domain)
                chromosome.genes[var_id] = new_val
                mutations_applied += 1

    return mutations_applied
