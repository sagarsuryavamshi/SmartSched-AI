"""Crossover operators for Academic Timetable Genetic Algorithm."""

import random
from typing import Optional, Tuple
from src.ga_engine.chromosome import TimetableChromosome


def uniform_crossover(
    parent1: TimetableChromosome,
    parent2: TimetableChromosome,
    crossover_prob: float = 0.85,
    rng: Optional[random.Random] = None,
) -> Tuple[TimetableChromosome, TimetableChromosome]:
    """Applies uniform crossover across two parent timetable chromosomes.

    For each scheduling variable, child 1 inherits from parent 1 with probability 0.5,
    and from parent 2 with probability 0.5, while child 2 takes the alternate gene.
    Guarantees structural validity and preservation of all scheduling variables.
    """
    if rng is None:
        rng = random.Random()

    if rng.random() > crossover_prob:
        return parent1.clone(), parent2.clone()

    child1_genes = {}
    child2_genes = {}

    all_var_ids = set(parent1.genes.keys()) | set(parent2.genes.keys())

    for var_id in all_var_ids:
        gene1 = parent1.genes.get(var_id)
        gene2 = parent2.genes.get(var_id)

        if gene1 is not None and gene2 is not None:
            if rng.random() < 0.5:
                child1_genes[var_id] = gene1
                child2_genes[var_id] = gene2
            else:
                child1_genes[var_id] = gene2
                child2_genes[var_id] = gene1
        elif gene1 is not None:
            child1_genes[var_id] = gene1
            child2_genes[var_id] = gene1
        elif gene2 is not None:
            child1_genes[var_id] = gene2
            child2_genes[var_id] = gene2

    return (
        TimetableChromosome(genes=child1_genes),
        TimetableChromosome(genes=child2_genes),
    )
