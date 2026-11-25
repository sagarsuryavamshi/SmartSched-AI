/**
 * Strongly-typed definitions for Analytics, What-If Rescheduling, and Constraint Violations.
 * Aligned with Python src/evaluation/metrics.py, src/optimization/rescheduling_engine.py,
 * and src/csp_engine/domain_types.py.
 */

import { DayOfWeek } from "./index";

export interface RoomUtilizationMetric {
  room_id: string;
  name: string;
  type: string;
  capacity: number;
  booked_hours: number;
  utilization_pct: number;
}

export interface FacultyWorkloadMetric {
  faculty_id: string;
  name: string;
  department: string;
  assigned_hours: number;
  max_hours: number;
  utilization_pct: number;
  days_active: number;
}

export interface DailyGroupWorkloadMetric {
  group_id: string;
  name: string;
  by_day: Record<string, number>;
  total_hours: number;
}

export interface SoftConstraintBreakdown {
  S1: number;
  S2: number;
  S3: number;
  S4: number;
  total: number;
}

export interface TimetableAnalyticsPayload {
  total_required_sessions: number;
  total_scheduled_sessions: number;
  total_unscheduled_sessions: number;
  completeness_percentage: number;
  overall_classroom_utilization_pct: number;
  total_booked_hours: number;
  total_idle_gap_hours: number;
  soft_constraint_breakdown: SoftConstraintBreakdown;
  room_utilization: Record<string, RoomUtilizationMetric>;
  faculty_workload: Record<string, FacultyWorkloadMetric>;
  daily_group_workload: Record<string, DailyGroupWorkloadMetric>;
}

export interface ReschedulingProposal {
  assignment_id: string;
  course_code: string;
  course_title: string;
  group_name: string;
  faculty_name: string;
  current_day: DayOfWeek;
  current_start_time: string;
  current_end_time: string;
  current_room_id: string;
  current_room_name: string;
  proposed_day: DayOfWeek;
  proposed_slot_id: string;
  proposed_start_time: string;
  proposed_end_time: string;
  proposed_room_id: string;
  proposed_room_name: string;
}

export interface ReschedulingValidationDelta {
  is_valid: boolean;
  hard_violations_count: number;
  hard_violation_messages: string[];
  soft_penalty_delta: number;
  original_penalty: number;
  new_penalty: number;
  delta_description: string;
}

export interface RescheduleHistoryRecord {
  change_id: string;
  timestamp: string;
  course_code: string;
  faculty_name: string;
  group_name: string;
  from_slot: string;
  to_slot: string;
  from_room: string;
  to_room: string;
  is_rolled_back: boolean;
}

export interface ConstraintViolationItem {
  violation_id: string;
  constraint_id: "H1" | "H2" | "H3" | "H4" | "H5" | "H6" | "H7" | "H8";
  name: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
  affected_course: string;
  affected_faculty: string;
  affected_group: string;
  affected_room: string;
  day: DayOfWeek;
  time_window: string;
  description: string;
  suggested_action: string;
}
