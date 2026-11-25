"""CSP Solver telemetry, configuration, and solver results data classes."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from src.csp_engine.domain_types import SchedulingAssignmentValue, ValidationReport


class SolverStatus(str, Enum):
    """Execution status of the CSP Solver."""
    SUCCESS = "SUCCESS"                         # Complete valid conflict-free solution found
    INFEASIBLE = "INFEASIBLE"                   # Search exhausted search space: proven no solution exists
    NODE_LIMIT_REACHED = "NODE_LIMIT_REACHED"   # Search halted due to max node exploration limit
    TIMEOUT = "TIMEOUT"                         # Search halted due to execution time limit
    EMPTY_PROBLEM = "EMPTY_PROBLEM"             # 0 variables to schedule
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"  # Initial domains or problem setup corrupted (e.g. initial wipeout)


@dataclass
class SolverConfig:
    """Configurable options and heuristics for the CSP Solver."""
    use_mrv: bool = True
    use_degree: bool = True
    use_lcv: bool = True
    use_forward_checking: bool = True
    use_ac3_preprocess: bool = True
    use_incremental_ac3: bool = False
    max_search_nodes: int = 50000
    timeout_seconds: float = 30.0


@dataclass
class SolverStatistics:
    """Detailed search telemetry tracking algorithm execution."""
    nodes_explored: int = 0
    assignment_attempts: int = 0
    successful_assignments: int = 0
    backtracks: int = 0
    constraint_checks: int = 0
    domain_reductions: int = 0
    ac3_arcs_processed: int = 0
    ac3_values_removed: int = 0
    dead_ends: int = 0
    max_depth_reached: int = 0
    execution_time_seconds: float = 0.0


@dataclass
class SolverResult:
    """Outcome of a CSP Solver run."""
    status: SolverStatus
    is_solution_found: bool
    assignment: Dict[str, SchedulingAssignmentValue] = field(default_factory=dict)
    statistics: SolverStatistics = field(default_factory=SolverStatistics)
    validation_report: Optional[ValidationReport] = None
    message: str = ""
    config_used: Optional[SolverConfig] = None
