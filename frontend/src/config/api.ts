/**
 * Central API Configuration for SmartSched AI.
 * Points to the FastAPI backend deployed on Render or local dev.
 */
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1",
  TIMEOUT_MS: 30000,
  ENDPOINTS: {
    ACADEMIC: {
      CLASSROOMS: "/academic/classrooms",
      FACULTY: "/academic/faculty",
      COURSES: "/academic/courses",
      STUDENT_GROUPS: "/academic/student-groups",
      TIMESLOTS: "/academic/timeslots",
      SUMMARY: "/academic/summary",
    },
    OPTIMIZE: {
      COMPILE_MODEL: "/optimize/csp/compile-model",
      SOLVE_CSP: "/optimize/csp/solve-backtracking",
      SOLVE_GA: "/optimize/ga/solve",
      VALIDATE: "/optimize/validate",
      BENCHMARK: "/optimize/benchmark",
    },
    TIMETABLE: {
      ACTIVE: "/timetables/active",
      SAVE: "/timetables/save",
      ANALYTICS: "/timetables/analytics",
      EXPORT_CSV: "/timetables/export/csv",
      EXPORT_PDF: "/timetables/export/pdf",
    },
    RESCHEDULE: {
      WHAT_IF_PREVIEW: "/reschedule/what-if/preview",
      COMMIT: "/reschedule/commit",
      HISTORY: "/reschedule/history",
      ROLLBACK: "/reschedule/rollback",
    },
  },
};
