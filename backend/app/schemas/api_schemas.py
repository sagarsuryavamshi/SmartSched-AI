from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

# Resource Schemas
class ClassroomBase(BaseModel):
    room_id: str
    name: str
    capacity: int
    room_type: str = "Classroom"
    features: Optional[str] = ""

class ClassroomCreate(ClassroomBase):
    pass

class ClassroomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    room_type: Optional[str] = None
    features: Optional[str] = None

class ClassroomOut(ClassroomBase):
    pass

class FacultyBase(BaseModel):
    faculty_id: str
    name: str
    email: str
    department: str = "Computer Science"
    max_weekly_hours: int = 18
    available_days: Optional[Union[List[str], str]] = None
    qualified_courses: Optional[Union[List[str], str]] = None
    unavailable_slots: Optional[Union[List[str], str]] = None

class FacultyCreate(BaseModel):
    faculty_id: str
    name: str
    email: str
    department: str = "Computer Science"
    max_weekly_hours: int = 18
    available_days: Optional[List[str]] = None
    qualified_courses: Optional[List[str]] = None
    unavailable_slots: Optional[List[str]] = None

class FacultyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    max_weekly_hours: Optional[int] = None
    available_days: Optional[List[str]] = None
    qualified_courses: Optional[List[str]] = None
    unavailable_slots: Optional[List[str]] = None

class FacultyOut(FacultyBase):
    available_days_list: Optional[List[str]] = []
    qualified_courses_list: Optional[List[str]] = []
    unavailable_slots_list: Optional[List[str]] = []

class StudentGroupBase(BaseModel):
    group_id: str
    name: str
    size: int
    program: str = "B.Tech"
    semester: int = 1
    department: str = "Computer Science"

class StudentGroupCreate(StudentGroupBase):
    pass

class StudentGroupUpdate(BaseModel):
    name: Optional[str] = None
    size: Optional[int] = None
    program: Optional[str] = None
    semester: Optional[int] = None
    department: Optional[str] = None

class StudentGroupOut(StudentGroupBase):
    pass

class CourseBase(BaseModel):
    course_id: str
    code: str
    title: str
    weekly_hours: int = 3
    required_room_type: str = "Classroom"
    is_lab: bool = False
    assigned_faculty_id: Optional[str] = None
    target_group_id: Optional[str] = None
    category: str = "Core"

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    weekly_hours: Optional[int] = None
    required_room_type: Optional[str] = None
    is_lab: Optional[bool] = None
    assigned_faculty_id: Optional[str] = None
    target_group_id: Optional[str] = None
    category: Optional[str] = None

class CourseOut(CourseBase):
    assigned_faculty_name: Optional[str] = None
    target_group_name: Optional[str] = None

class TimeslotBase(BaseModel):
    slot_id: str
    day: str
    start_time: str
    end_time: str
    duration_minutes: int = 60
    is_break: bool = False

class TimeslotCreate(TimeslotBase):
    pass

class TimeslotUpdate(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_break: Optional[bool] = None

class TimeslotOut(TimeslotBase):
    pass

# Optimization Schemas
class CSPSolverRequest(BaseModel):
    use_mrv: bool = True
    use_degree: bool = True
    use_lcv: bool = True
    use_forward_checking: bool = True
    use_ac3_preprocess: bool = True
    enable_branch_and_bound: bool = False
    timeout_seconds: float = 30.0

class GASolverRequest(BaseModel):
    population_size: int = 100
    max_generations: int = 120
    crossover_prob: float = 0.85
    mutation_prob: float = 0.08
    elitism_count: int = 4
    tournament_size: int = 3
    timeout_seconds: float = 30.0

class BenchmarkRequest(BaseModel):
    csp_config: Optional[CSPSolverRequest] = None
    ga_pop_size: int = 100
    ga_generations: int = 120
    ga_timeout: float = 30.0

# Rescheduling Schemas
class ReschedulePreviewRequest(BaseModel):
    variable_id: str
    new_room_id: str
    new_day: Optional[str] = None
    new_slot_ids: List[str]
    reason: Optional[str] = "Administrator What-If Adjustment"

class RescheduleCommitRequest(BaseModel):
    assignment_ids: List[str]
    new_room_id: str
    new_slot_ids: List[str]
    reason: Optional[str] = "Admin Manual Adjustment"
