"""Population data structure and statistics for Genetic Algorithm."""

from dataclasses import dataclass, field
from typing import List, Optional

from src.ga_engine.chromosome import TimetableChromosome


@dataclass
class Population:
    """Manages an evolving cohort of timetable chromosomes."""

    chromosomes: List[TimetableChromosome] = field(default_factory=list)
    generation: int = 0

    def add(self, chromosome: TimetableChromosome) -> None:
        """Appends a candidate chromosome to the population."""
        self.chromosomes.append(chromosome)

    def sort_by_fitness(self, descending: bool = True) -> None:
        """Sorts the population in-place by fitness (highest fitness first by default)."""
        self.chromosomes.sort(key=lambda c: c.fitness, reverse=descending)

    def get_best(self) -> Optional[TimetableChromosome]:
        """Returns the individual with the highest fitness."""
        if not self.chromosomes:
            return None
        return max(self.chromosomes, key=lambda c: c.fitness)

    def get_worst(self) -> Optional[TimetableChromosome]:
        """Returns the individual with the lowest fitness."""
        if not self.chromosomes:
            return None
        return min(self.chromosomes, key=lambda c: c.fitness)

    @property
    def average_fitness(self) -> float:
        """Computes mean fitness across the population."""
        if not self.chromosomes:
            return 0.0
        return sum(c.fitness for c in self.chromosomes) / len(self.chromosomes)

    @property
    def average_hard_violations(self) -> float:
        """Computes mean hard constraint violations across the population."""
        if not self.chromosomes:
            return 0.0
        return sum(c.hard_violations_count for c in self.chromosomes) / len(self.chromosomes)

    @property
    def average_soft_penalty(self) -> float:
        """Computes mean soft constraint penalty score across the population."""
        if not self.chromosomes:
            return 0.0
        return sum(c.soft_penalty for c in self.chromosomes) / len(self.chromosomes)

    @property
    def feasible_count(self) -> int:
        """Returns the number of conflict-free chromosomes in the population."""
        return sum(1 for c in self.chromosomes if c.is_feasible)

    def __len__(self) -> int:
        return len(self.chromosomes)

    def __iter__(self):
        return iter(self.chromosomes)

    def __getitem__(self, idx: int) -> TimetableChromosome:
        return self.chromosomes[idx]
