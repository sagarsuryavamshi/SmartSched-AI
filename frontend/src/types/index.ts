export type RoomType = "LECTURE_HALL" | "LAB" | "SEMINAR_ROOM";

export interface Classroom {
  room_id: string;
  name: string;
  capacity: number;
  room_type: RoomType;
  features: string;
  building?: string;
  is_available?: boolean;
}

export type DayOfWeek = "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday";

export type SlotAvailabilityStatus = "AVAILABLE" | "UNAVAILABLE" | "PREFERRED";

export interface Faculty {
  faculty_id: string;
  name: string;
  email: string;
  department: string;
  max_weekly_hours: number;
  available_days: DayOfWeek[];
  qualified_courses: string[]; // course codes or IDs
  unavailable_slots: string[]; // slot IDs e.g. "TS_FRI_5"
  preferred_slots?: string[];   // slot IDs e.g. "TS_MON_1"
  specialization?: string;
}

export interface StudentGroup {
  group_id: string;
  name: string;
  department: string;
  size: number;
  program: string;
  semester: number;
}

export interface Course {
  course_id: string;
  code: string;
  title: string;
  weekly_hours: number;
  required_room_type: RoomType;
  category: "Theory" | "Practical" | "Seminar";
  is_lab: boolean;
  assigned_faculty_id?: string;
  target_group_id?: string;
  instructor_name?: string;
  group_name?: string;
}

export interface Timeslot {
  slot_id: string;
  day: DayOfWeek;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  is_break: boolean;
}

export interface TimetableAssignment {
  assignment_id: string;
  course_code: string;
  course_title: string;
  faculty_id: string;
  faculty_name: string;
  group_id: string;
  group_name: string;
  room_id: string;
  room_name: string;
  slot_id: string;
  day: string;
  start_time: string;
  end_time: string;
  session_type: "THEORY" | "LAB";
}

export interface OptimizationMetrics {
  algorithm: "Backtracking CSP" | "Genetic Algorithm";
  status: "FEASIBLE" | "OPTIMAL" | "INFEASIBLE";
  assigned_sessions: number;
  total_sessions: number;
  hard_violations: number;
  soft_penalty_score: number;
  runtime_seconds: number;
  search_nodes?: number;
  backtracks?: number;
  generations?: number;
}
