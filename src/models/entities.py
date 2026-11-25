"""Domain data models and schemas for SmartSched AI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set


class RoomType(str, Enum):
    """Types of rooms available for scheduling."""
    LECTURE_HALL = "LECTURE_HALL"
    LAB = "LAB"
    SEMINAR_ROOM = "SEMINAR_ROOM"


class CourseCategory(str, Enum):
    """Pedagogical category of course."""
    THEORY = "Theory"
    PRACTICAL = "Practical"


class DayOfWeek(str, Enum):
    """Days of the academic week."""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"


@dataclass(frozen=True)
class TimeSlot:
    """Represents a specific recurring weekly lecture/lab timeslot."""
    slot_id: str
    day: DayOfWeek
    start_time: str           # e.g., "09:00"
    end_time: str             # e.g., "10:00"
    duration_minutes: int = 60
    is_break: bool = False

    def __str__(self) -> str:
        tag = " [BREAK]" if self.is_break else ""
        return f"{self.day.value} {self.start_time}-{self.end_time} ({self.duration_minutes}m){tag}"


@dataclass
class Classroom:
    """Classroom or laboratory facility."""
    room_id: str
    name: str
    capacity: int
    room_type: RoomType = RoomType.LECTURE_HALL
    features: List[str] = field(default_factory=list)


@dataclass
class Faculty:
    """Academic instructor with specific teaching subjects and time availability."""
    faculty_id: str
    name: str
    email: str
    department: str = "Computer Science"
    max_weekly_hours: int = 18
    available_days: List[str] = field(default_factory=lambda: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    qualified_courses: List[str] = field(default_factory=list)
    unavailable_slots: Set[str] = field(default_factory=set)  # set of slot_ids


@dataclass
class StudentGroup:
    """Cohort, batch, or section of students taking a common curriculum."""
    group_id: str
    name: str
    department: str = "Computer Science"
    size: int = 50
    program: str = "B.Tech"
    semester: int = 1


@dataclass
class Course:
    """Academic course requiring one or more weekly lecture/lab sessions."""
    course_id: str
    code: str
    title: str
    weekly_hours: int
    required_room_type: RoomType = RoomType.LECTURE_HALL
    category: CourseCategory = CourseCategory.THEORY
    is_lab: bool = False
    assigned_faculty_id: Optional[str] = None
    target_group_id: Optional[str] = None


@dataclass
class LessonAssignment:
    """A scheduled lecture session assigned to a room, timeslot, faculty, and group."""
    assignment_id: str
    course_id: str
    group_id: str
    faculty_id: str
    room_id: str
    slot_id: str
