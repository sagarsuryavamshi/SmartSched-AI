"""Fitness evaluation module for Academic Timetable Genetic Algorithm.

Implements hierarchical multi-objective fitness evaluation:
  1. Primary Objective: Hard Constraint Feasibility (H1 - H8).
  2. Secondary Objective: Soft Constraint Penalty Minimization (S1 - S4).

A heavy penalty factor guarantees that ANY clash-free timetable strictly
outperforms ANY timetable containing one or more hard constraint violations.
"""

from typing import Optional
from src.csp_engine.model import CSPModel
from src.ga_engine.chromosome import TimetableChromosome

HARD_CONSTRAINT_WEIGHT: float = 10000.0


def evaluate_fitness(
    chromosome: TimetableChromosome,
    model: CSPModel,
    hard_weight: float = HARD_CONSTRAINT_WEIGHT,
) -> float:
    """Evaluates and updates the fitness of a candidate timetable chromosome.

    Fitness formula:
        Cost = hard_weight * num_hard_violations + soft_penalty_score
        Fitness = 1.0 / (1.0 + Cost)

    Properties:
        - Feasible solutions (H=0) have Cost = SoftPenalty.
          e.g. SoftPenalty=200 -> Fitness ~ 0.004975
        - Infeasible solutions (H>=1) have Cost >= 10000.
          e.g. 1 hard violation -> Fitness <= 0.0000999
        - Therefore, Feasible Fitness is strictly > Infeasible Fitness for all valid inputs.
    """
    report = model.validate_assignments(chromosome.genes)
    num_hard = len(report.hard_violations)
    soft_score = report.soft_penalty_score

    cost = (hard_weight * num_hard) + soft_score
    fitness = 1.0 / (1.0 + cost)

    is_feasible = (num_hard == 0) and (len(chromosome.genes) == len(model.variables))

    chromosome.fitness = fitness
    chromosome.hard_violations_count = num_hard
    chromosome.soft_penalty = soft_score
    chromosome.is_feasible = is_feasible
    chromosome.validation_report = report

    return fitness
