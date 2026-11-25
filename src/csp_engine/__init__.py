"""CSP Engine package exports."""

from src.csp_engine.domain_types import (
    ConstraintViolation,
    SchedulingAssignmentValue,
    SchedulingVariable,
    SessionType,
    TimetableStatus,
    ValidationReport,
)
from src.csp_engine.generator import generate_domains_from_db, generate_variables_from_db
from src.csp_engine.hard_constraints import (
    check_h1_faculty_overlap,
    check_h2_classroom_overlap,
    check_h3_student_group_overlap,
    check_h4_room_capacity,
    check_h5_faculty_availability,
    check_h6_room_type,
    check_h7_lab_continuity,
    check_h8_working_hours,
)
from src.csp_engine.model import CSPModel
from src.csp_engine.soft_constraints import (
    score_s1_faculty_preferences,
    score_s2_faculty_idle_gaps,
    score_s3_consecutive_theory_sessions,
    score_s4_balanced_daily_workload,
)
from src.csp_engine.solver import CSPProblem, CSPSolver, values_are_compatible
from src.csp_engine.solver_types import (
    SolverConfig,
    SolverResult,
    SolverStatistics,
    SolverStatus,
)

__all__ = [
    "CSPModel",
    "CSPProblem",
    "CSPSolver",
    "ConstraintViolation",
    "SchedulingAssignmentValue",
    "SchedulingVariable",
    "SessionType",
    "SolverConfig",
    "SolverResult",
    "SolverStatistics",
    "SolverStatus",
    "TimetableStatus",
    "ValidationReport",
    "check_h1_faculty_overlap",
    "check_h2_classroom_overlap",
    "check_h3_student_group_overlap",
    "check_h4_room_capacity",
    "check_h5_faculty_availability",
    "check_h6_room_type",
    "check_h7_lab_continuity",
    "check_h8_working_hours",
    "generate_domains_from_db",
    "generate_variables_from_db",
    "score_s1_faculty_preferences",
    "score_s2_faculty_idle_gaps",
    "score_s3_consecutive_theory_sessions",
    "score_s4_balanced_daily_workload",
    "values_are_compatible",
]
