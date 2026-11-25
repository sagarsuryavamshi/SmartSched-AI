"""Chromosome representation for Academic Timetable Genetic Algorithm.

Represents candidate timetables as chromosomes composed of individual session genes,
maintaining 100% interoperability with the CSP model and validation engine.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src.csp_engine.domain_types import (
    SchedulingAssignmentValue,
    SchedulingVariable,
    ValidationReport,
)


@dataclass
class TimetableChromosome:
    """Represents a single candidate timetable in the Genetic Algorithm population.

    Each gene maps `var_id` -> `SchedulingAssignmentValue`.
    Faculty, student cohort, duration, and room type requirements are guaranteed
    by the underlying domain values.
    """

    genes: Dict[str, SchedulingAssignmentValue] = field(default_factory=dict)
    fitness: float = 0.0
    hard_violations_count: int = 0
    soft_penalty: float = 0.0
    is_feasible: bool = False
    validation_report: Optional[ValidationReport] = None

    def to_assignment_dict(self) -> Dict[str, SchedulingAssignmentValue]:
        """Returns the dictionary of variable assignments for CSP validation and persistence."""
        return dict(self.genes)

    @classmethod
    def from_assignment_dict(
        cls,
        assignments: Dict[str, SchedulingAssignmentValue],
    ) -> "TimetableChromosome":
        """Constructs a chromosome from an existing dictionary of assignments."""
        return cls(genes=dict(assignments))

    def clone(self) -> "TimetableChromosome":
        """Produces an independent clone of the chromosome."""
        return TimetableChromosome(
            genes=dict(self.genes),
            fitness=self.fitness,
            hard_violations_count=self.hard_violations_count,
            soft_penalty=self.soft_penalty,
            is_feasible=self.is_feasible,
            validation_report=self.validation_report,
        )

    def is_complete(self, expected_variables: Set[str]) -> bool:
        """Verifies whether all required academic scheduling variables are present in the chromosome."""
        return expected_variables.issubset(self.genes.keys())

    @property
    def assigned_count(self) -> int:
        """Returns the number of scheduled sessions."""
        return len(self.genes)

    def __len__(self) -> int:
        return len(self.genes)

    def __repr__(self) -> str:
        status_tag = "FEASIBLE" if self.is_feasible else f"INVALID(H={self.hard_violations_count})"
        return (
            f"<TimetableChromosome: {len(self.genes)} genes, "
            f"Fitness={self.fitness:.6f}, {status_tag}, SoftPenalty={self.soft_penalty:.1f}>"
        )
