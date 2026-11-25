"""Mathematical data structures for CSP Variables, Values, and Validation Results."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class SessionType(str, Enum):
    """Categorization of individual scheduled sessions."""
    THEORY = "THEORY"
    LAB = "LAB"


class TimetableStatus(str, Enum):
    """Lifecycle classification of a timetable schedule state."""
    EMPTY = "EMPTY"                             # 0 variables assigned
    PARTIAL_VALID = "PARTIAL_VALID"             # >0 and <N variables assigned, 0 hard violations
    COMPLETE_VALID = "COMPLETE_VALID"           # N variables assigned, 0 hard violations
    INVALID = "INVALID"                         # >=1 hard constraint violation


@dataclass(frozen=True)
class SchedulingVariable:
    """Represents an atomic single lecture or lab session to be assigned in the timetable.

    A course with `weekly_hours = 3` decomposes into:
      - 3 independent theory sessions of 1 hour each, OR
      - 1 lab session of 2 or 3 consecutive hours.
    """
    var_id: str                 # Unique variable key, e.g. "VAR_CRS_CS201_S1"
    course_id: str             # e.g. "CRS_CS201"
    course_code: str           # e.g. "CS201"
    session_num: int           # 1, 2, 3...
    total_sessions: int        # Total sessions for this course
    session_type: SessionType  # THEORY or LAB
    duration_hours: int        # Duration in hours (e.g. 1 for lecture, 2 for lab)
    faculty_id: str            # Assigned instructor ID
    group_id: str              # Target student cohort ID
    required_room_type: str    # LECTURE_HALL, LAB, SEMINAR_ROOM

    def __str__(self) -> str:
        return f"{self.course_code}-S{self.session_num} ({self.session_type.value}, {self.duration_hours}h)"


@dataclass(frozen=True)
class SchedulingAssignmentValue:
    """Represents a potential assignment coordinate in the timetable domain:

    Assignment = (Timeslot, Classroom, Faculty, StudentGroup)
    For multi-hour lab sessions, `slot_ids` contains the consecutive timeslot sequence.
    """
    slot_id: str               # Primary starting slot ID
    room_id: str               # Classroom / Lab facility ID
    day: str                   # Monday, Tuesday, etc.
    start_time: str            # e.g. "09:00"
    end_time: str              # e.g. "10:00" or "11:00" for 2h lab
    slot_ids: Tuple[str, ...]  # Tuple of 1 or more consecutive slot_ids for this session
    faculty_id: str            # Assigned instructor
    group_id: str              # Target student group

    def __str__(self) -> str:
        return f"[{self.day} {self.start_time}-{self.end_time} @ {self.room_id}]"


@dataclass
class ConstraintViolation:
    """Details of a single constraint violation instance."""
    constraint_id: str
    constraint_name: str
    violating_var_ids: List[str]
    explanation: str
    severity: str = "HARD"  # HARD or SOFT


@dataclass
class ValidationReport:
    """Comprehensive validation output for a partial or complete timetable state."""
    is_valid: bool
    status: TimetableStatus = TimetableStatus.EMPTY
    total_variables: int = 0
    assigned_variables: int = 0
    hard_violations: List[ConstraintViolation] = field(default_factory=list)
    soft_violations: List[ConstraintViolation] = field(default_factory=list)
    soft_penalty_score: float = 0.0
    summary_by_constraint: Dict[str, Dict[str, Any]] = field(default_factory=dict)
