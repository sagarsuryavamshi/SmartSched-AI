from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any

from backend.app.core.config import settings
from backend.app.schemas.api_schemas import (
    ClassroomOut, ClassroomCreate, ClassroomUpdate,
    FacultyOut, FacultyCreate, FacultyUpdate,
    StudentGroupOut, StudentGroupCreate, StudentGroupUpdate,
    CourseOut, CourseCreate, CourseUpdate,
    TimeslotOut, TimeslotCreate, TimeslotUpdate
)
from src.data_management.crud_services import (
    get_all_classrooms, get_classroom_by_id, create_classroom, update_classroom, delete_classroom,
    get_all_faculty, get_faculty_by_id, create_faculty, update_faculty, delete_faculty,
    get_all_student_groups, get_student_group_by_id, create_student_group, update_student_group, delete_student_group,
    get_all_courses, get_course_by_id, create_course, update_course, delete_course,
    get_all_timeslots, get_timeslot_by_id, create_timeslot, update_timeslot, delete_timeslot
)

router = APIRouter()
DB_PATH = str(settings.DB_PATH)

# ----------------- CLASSROOMS -----------------
@router.get("/classrooms", response_model=List[ClassroomOut])
def list_classrooms(search: str = ""):
    return get_all_classrooms(search_term=search, db_path=DB_PATH)

@router.get("/classrooms/{room_id}", response_model=ClassroomOut)
def get_classroom(room_id: str):
    room = get_classroom_by_id(room_id, db_path=DB_PATH)
    if not room:
        raise HTTPException(status_code=404, detail=f"Classroom '{room_id}' not found")
    return room

@router.post("/classrooms", response_model=Dict[str, Any])
def add_classroom(payload: ClassroomCreate):
    ok, msg = create_classroom(
        room_id=payload.room_id,
        name=payload.name,
        capacity=payload.capacity,
        room_type=payload.room_type,
        features=payload.features or "",
        db_path=DB_PATH
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "room_id": payload.room_id}

@router.put("/classrooms/{room_id}", response_model=Dict[str, Any])
def edit_classroom(room_id: str, payload: ClassroomUpdate):
    existing = get_classroom_by_id(room_id, db_path=DB_PATH)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Classroom '{room_id}' not found")
    name = payload.name if payload.name is not None else existing["name"]
    capacity = payload.capacity if payload.capacity is not None else existing["capacity"]
    room_type = payload.room_type if payload.room_type is not None else existing["room_type"]
    features = payload.features if payload.features is not None else existing.get("features", "")
    ok, msg = update_classroom(room_id=room_id, name=name, capacity=capacity, room_type=room_type, features=features, db_path=DB_PATH)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "room_id": room_id}

@router.delete("/classrooms/{room_id}")
def remove_classroom(room_id: str):
    ok, msg = delete_classroom(room_id, db_path=DB_PATH)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "deleted", "room_id": room_id, "message": msg}

# ----------------- FACULTY -----------------
@router.get("/faculty", response_model=List[FacultyOut])
def list_faculty(search: str = ""):
    return get_all_faculty(search_term=search, db_path=DB_PATH)

@router.get("/faculty/{faculty_id}", response_model=FacultyOut)
def get_faculty(faculty_id: str):
    fac = get_faculty_by_id(faculty_id, db_path=DB_PATH)
    if not fac:
        raise HTTPException(status_code=404, detail=f"Faculty '{faculty_id}' not found")
    return fac

@router.post("/faculty", response_model=Dict[str, Any])
def add_faculty(payload: FacultyCreate):
    ok, msg = create_faculty(
        faculty_id=payload.faculty_id,
        name=payload.name,
        email=payload.email,
        department=payload.department,
        max_weekly_hours=payload.max_weekly_hours,
        available_days=payload.available_days,
        qualified_courses=payload.qualified_courses,
        unavailable_slots=payload.unavailable_slots,
        db_path=DB_PATH
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "faculty_id": payload.faculty_id}

@router.put("/faculty/{faculty_id}", response_model=Dict[str, Any])
def edit_faculty(faculty_id: str, payload: FacultyUpdate):
    existing = get_faculty_by_id(faculty_id, db_path=DB_PATH)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Faculty '{faculty_id}' not found")
    name = payload.name if payload.name is not None else existing["name"]
    email = payload.email if payload.email is not None else existing["email"]
    dept = payload.department if payload.department is not None else existing["department"]
    hours = payload.max_weekly_hours if payload.max_weekly_hours is not None else existing["max_weekly_hours"]
    days = payload.available_days if payload.available_days is not None else existing.get("available_days_list")
    courses = payload.qualified_courses if payload.qualified_courses is not None else existing.get("qualified_courses_list")
    unavail = payload.unavailable_slots if payload.unavailable_slots is not None else existing.get("unavailable_slots_list")

    ok, msg = update_faculty(
        faculty_id=faculty_id, name=name, email=email, department=dept,
        max_weekly_hours=hours, available_days=days, qualified_courses=courses,
        unavailable_slots=unavail, db_path=DB_PATH
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "faculty_id": faculty_id}

@router.delete("/faculty/{faculty_id}")
def remove_faculty(faculty_id: str):
    ok, msg = delete_faculty(faculty_id, db_path=DB_PATH)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "deleted", "faculty_id": faculty_id, "message": msg}

# ----------------- STUDENT GROUPS -----------------
@router.get("/groups", response_model=List[StudentGroupOut])
def list_groups(search: str = ""):
    return get_all_student_groups(search_term=search, db_path=DB_PATH)

@router.get("/groups/{group_id}", response_model=StudentGroupOut)
def get_group(group_id: str):
    grp = get_student_group_by_id(group_id, db_path=DB_PATH)
    if not grp:
        raise HTTPException(status_code=404, detail=f"Student group '{group_id}' not found")
    return grp

@router.post("/groups", response_model=Dict[str, Any])
def add_group(payload: StudentGroupCreate):
    ok, msg = create_student_group(
        group_id=payload.group_id,
        name=payload.name,
        size=payload.size,
        program=payload.program,
        semester=payload.semester,
        department=payload.department,
        db_path=DB_PATH
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "group_id": payload.group_id}

@router.put("/groups/{group_id}", response_model=Dict[str, Any])
def edit_group(group_id: str, payload: StudentGroupUpdate):
    existing = get_student_group_by_id(group_id, db_path=DB_PATH)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Student group '{group_id}' not found")
    name = payload.name if payload.name is not None else existing["name"]
    dept = payload.department if payload.department is not None else existing["department"]
    size = payload.size if payload.size is not None else existing["size"]
    program = payload.program if payload.program is not None else existing["program"]
    sem = payload.semester if payload.semester is not None else existing["semester"]

    ok, msg = update_student_group(
        group_id=group_id, name=name, department=dept, size=size,
        program=program, semester=sem, db_path=DB_PATH
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "group_id": group_id}

@router.delete("/groups/{group_id}")
def remove_group(group_id: str):
    ok, msg = delete_student_group(group_id, db_path=DB_PATH)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "deleted", "group_id": group_id, "message": msg}

# ----------------- COURSES -----------------
@router.get("/courses", response_model=List[CourseOut])
def list_courses(search: str = ""):
    return get_all_courses(search_term=search, db_path=DB_PATH)

@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(course_id: str):
    crs = get_course_by_id(course_id, db_path=DB_PATH)
    if not crs:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    return crs

@router.post("/courses", response_model=Dict[str, Any])
def add_course(payload: CourseCreate):
    ok, msg = create_course(
        course_id=payload.course_id,
        code=payload.code,
        title=payload.title,
        weekly_hours=payload.weekly_hours,
        required_room_type=payload.required_room_type,
        is_lab=payload.is_lab,
        assigned_faculty_id=payload.assigned_faculty_id,
        target_group_id=payload.target_group_id,
        category=payload.category,
        db_path=DB_PATH
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "course_id": payload.course_id}

@router.put("/courses/{course_id}", response_model=Dict[str, Any])
def edit_course(course_id: str, payload: CourseUpdate):
    existing = get_course_by_id(course_id, db_path=DB_PATH)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    code = payload.code if payload.code is not None else existing["code"]
    title = payload.title if payload.title is not None else existing["title"]
    hours = payload.weekly_hours if payload.weekly_hours is not None else existing["weekly_hours"]
    room_type = payload.required_room_type if payload.required_room_type is not None else existing["required_room_type"]
    category = payload.category if payload.category is not None else existing["category"]
    is_lab = payload.is_lab if payload.is_lab is not None else bool(existing["is_lab"])
    faculty_id = payload.assigned_faculty_id if payload.assigned_faculty_id is not None else existing.get("assigned_faculty_id")
    group_id = payload.target_group_id if payload.target_group_id is not None else existing.get("target_group_id")

    ok, msg = update_course(
        course_id=course_id, code=code, title=title, weekly_hours=hours,
        required_room_type=room_type, category=category, is_lab=is_lab,
        assigned_faculty_id=faculty_id, target_group_id=group_id, db_path=DB_PATH
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "course_id": course_id}

@router.delete("/courses/{course_id}")
def remove_course(course_id: str):
    ok, msg = delete_course(course_id, db_path=DB_PATH)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "deleted", "course_id": course_id, "message": msg}

# ----------------- TIMESLOTS -----------------
@router.get("/timeslots", response_model=List[TimeslotOut])
def list_timeslots(search: str = ""):
    return get_all_timeslots(search_term=search, db_path=DB_PATH)

@router.get("/timeslots/{slot_id}", response_model=TimeslotOut)
def get_timeslot(slot_id: str):
    slot = get_timeslot_by_id(slot_id, db_path=DB_PATH)
    if not slot:
        raise HTTPException(status_code=404, detail=f"Timeslot '{slot_id}' not found")
    return slot

@router.post("/timeslots", response_model=Dict[str, Any])
def add_timeslot(payload: TimeslotCreate):
    ok, msg = create_timeslot(
        slot_id=payload.slot_id,
        day=payload.day,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_minutes=payload.duration_minutes,
        is_break=payload.is_break,
        db_path=DB_PATH
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "slot_id": payload.slot_id}

@router.put("/timeslots/{slot_id}", response_model=Dict[str, Any])
def edit_timeslot(slot_id: str, payload: TimeslotUpdate):
    existing = get_timeslot_by_id(slot_id, db_path=DB_PATH)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Timeslot '{slot_id}' not found")
    day = existing["day"]
    start_time = payload.start_time if payload.start_time is not None else existing["start_time"]
    end_time = payload.end_time if payload.end_time is not None else existing["end_time"]
    duration = payload.duration_minutes if payload.duration_minutes is not None else existing["duration_minutes"]
    is_break = payload.is_break if payload.is_break is not None else bool(existing["is_break"])

    ok, msg = update_timeslot(
        slot_id=slot_id, day=day, start_time=start_time, end_time=end_time,
        duration_minutes=duration, is_break=is_break, db_path=DB_PATH
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "slot_id": slot_id}

@router.delete("/timeslots/{slot_id}")
def remove_timeslot(slot_id: str):
    ok, msg = delete_timeslot(slot_id, db_path=DB_PATH)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "deleted", "slot_id": slot_id, "message": msg}
