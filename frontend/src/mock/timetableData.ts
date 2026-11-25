import { ScheduledSession } from "@/types/timetable";
import SAVED_RECORDS from "./saved_timetable.json";

export const INITIAL_SCHEDULED_SESSIONS: ScheduledSession[] = (SAVED_RECORDS as any[]).map((r) => ({
  id: r.id,
  assignment_id: r.assignment_id,
  generation_run_id: r.generation_run_id,
  course_code: r.course_code,
  course_title: r.course_title,
  course_category: (r.course_category === "Practical" ? "Practical" : r.course_category === "Seminar" ? "Seminar" : "Theory"),
  faculty_id: r.faculty_id,
  faculty_name: r.faculty_name,
  group_id: r.group_id,
  group_name: r.group_name,
  room_id: r.room_id,
  room_name: r.room_name,
  room_type: r.room_type,
  slot_id: r.slot_id,
  day: r.day,
  start_time: r.start_time,
  end_time: r.end_time,
  duration_minutes: r.duration_minutes || 60,
  is_continuous_lab: r.course_category === "Practical",
  validation_status: "VALID",
}));
