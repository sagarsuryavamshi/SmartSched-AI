import { DayOfWeek, RoomType } from "./index";

export type TimetablePerspective =
  | "DEPARTMENT_MASTER"
  | "STUDENT_GROUP"
  | "FACULTY"
  | "CLASSROOM";

export type SessionCategory = "Theory" | "Practical" | "Seminar";

export interface ScheduledSession {
  id?: number;
  assignment_id: string;
  generation_run_id?: string;
  course_code: string;
  course_title: string;
  course_category: SessionCategory;
  faculty_id: string;
  faculty_name: string;
  group_id: string;
  group_name: string;
  room_id: string;
  room_name: string;
  room_type: RoomType;
  slot_id: string;
  day: DayOfWeek;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  is_continuous_lab?: boolean;
  validation_status?: "VALID" | "CONFLICT_DETECTED" | "UNVALIDATED";
  conflict_details?: string[];
}

export interface TimetableExportOptions {
  perspective: TimetablePerspective;
  filterId?: string;
  format: "CSV" | "PDF";
}
