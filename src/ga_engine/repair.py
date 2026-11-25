"""Repair heuristics for Academic Timetable Genetic Algorithm.

Selectively detects hard constraint clashes (faculty overlap, room overlap, cohort clashes)
and attempts to reassign conflicting variables to non-conflicting legal domain coordinates.
"""

import random
from typing import Dict, List, Optional, Set, Tuple

from src.csp_engine.domain_types import SchedulingAssignmentValue
from src.csp_engine.model import CSPModel
from src.csp_engine.solver import values_are_compatible
from src.ga_engine.chromosome import TimetableChromosome
from src.ga_engine.fitness import evaluate_fitness
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.ga_engine.repair")


def repair_chromosome(
    chromosome: TimetableChromosome,
    model: CSPModel,
    max_repair_passes: int = 5,
    rng: Optional[random.Random] = None,
) -> Tuple[bool, int]:
    """Targeted constraint repair heuristic.

    1. Identifies variables actively participating in hard constraint violations (H1-H8).
    2. Searches each conflicting variable's domain for an assignment compatible with
       all non-conflicting variables.
    3. Re-evaluates chromosome fitness and feasibility.

    Returns:
        Tuple of (is_now_feasible: bool, successful_repair_swaps: int)
    """
    if rng is None:
        rng = random.Random()

    if chromosome.validation_report is None:
        evaluate_fitness(chromosome, model)

    if chromosome.is_feasible:
        return True, 0

    successful_swaps = 0

    for _ in range(max_repair_passes):
        report = chromosome.validation_report
        if report is None or report.is_valid:
            break

        # Collect unique variable IDs participating in hard violations
        violating_var_ids: List[str] = []
        for viol in report.hard_violations:
            for v_id in viol.violating_var_ids:
                if v_id in chromosome.genes and v_id not in violating_var_ids:
                    violating_var_ids.append(v_id)

        if not violating_var_ids:
            break

        # Shuffle violating variables to avoid deterministic bias
        rng.shuffle(violating_var_ids)
        progress_made = False

        for v_id in violating_var_ids:
            current_val = chromosome.genes[v_id]
            domain_options = model.domains.get(v_id, [])
            if not domain_options:
                continue

            # Candidate scoring: find domain value with fewest binary clashes
            best_candidate = None
            min_clashes = float("inf")

            # Shuffle domain options to explore diverse placements
            shuffled_options = list(domain_options)
            rng.shuffle(shuffled_options)

            for cand in shuffled_options:
                clashes = 0
                for other_id, other_val in chromosome.genes.items():
                    if other_id == v_id:
                        continue
                    if not values_are_compatible(cand, other_val):
                        clashes += 1
                        if clashes >= min_clashes:
                            break

                if clashes < min_clashes:
                    min_clashes = clashes
                    best_candidate = cand
                    if min_clashes == 0:
                        break  # Found completely clash-free alternative

            # If an alternative strictly better than current was found, swap it
            if best_candidate is not None and min_clashes < float("inf") and best_candidate != current_val:
                chromosome.genes[v_id] = best_candidate
                successful_swaps += 1
                progress_made = True
                # Re-evaluate after swap
                evaluate_fitness(chromosome, model)
                if chromosome.is_feasible:
                    return True, successful_swaps

        if not progress_made:
            break

    # Final fitness update
    evaluate_fitness(chromosome, model)
    return chromosome.is_feasible, successful_swaps
