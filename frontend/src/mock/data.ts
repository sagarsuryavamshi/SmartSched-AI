import { Classroom, Course, Faculty, StudentGroup, Timeslot } from "@/types";

export const MOCK_SYSTEM_SUMMARY = {
  classrooms: 6,
  faculty: 5,
  courses: 10,
  student_groups: 3,
  timeslots: 25,
  total_required_sessions: 24,
  assigned_sessions: 24,
  current_status: "FEASIBLE" as const,
  active_run_id: "RUN_2026_FALL_CS",
  hard_violations: 0,
  soft_penalty_score: 12.0,
  last_generated_at: "2026-11-26 01:21:48",
  solver_used: "Genetic Algorithm (Hybrid Repair)",
};

export const INITIAL_CLASSROOMS: Classroom[] = [
  { room_id: "CR_LH101", name: "Lecture Hall 101", capacity: 80, room_type: "LECTURE_HALL", features: "Projector, Audio System, Wi-Fi", building: "Academic Block A", is_available: true },
  { room_id: "CR_LH102", name: "Lecture Hall 102", capacity: 70, room_type: "LECTURE_HALL", features: "Smart Board, Projector", building: "Academic Block A", is_available: true },
  { room_id: "CR_LH103", name: "Lecture Hall 103", capacity: 50, room_type: "LECTURE_HALL", features: "Projector, Whiteboard", building: "Academic Block A", is_available: true },
  { room_id: "CR_LAB201", name: "AI & Robotics Lab", capacity: 60, room_type: "LAB", features: "High-End GPUs, Linux Workstations", building: "Computing Centre", is_available: true },
  { room_id: "CR_LAB202", name: "Software Systems Lab", capacity: 60, room_type: "LAB", features: "Dual Monitors, Dev Environments", building: "Computing Centre", is_available: true },
  { room_id: "CR_SEM301", name: "Seminar Room A", capacity: 40, room_type: "SEMINAR_ROOM", features: "Video Conferencing, Display", building: "Dean's Wing", is_available: true },
];

export const INITIAL_STUDENT_GROUPS: StudentGroup[] = [
  { group_id: "GRP_CS_SEM4", name: "CS Batch 2024 (Semester 4)", department: "Computer Science", size: 55, program: "B.Tech Computer Science", semester: 4 },
  { group_id: "GRP_CS_SEM6", name: "CS Batch 2023 (Semester 6)", department: "Computer Science", size: 48, program: "B.Tech Computer Science", semester: 6 },
  { group_id: "GRP_AI_SEM2", name: "AI & Data Science (Semester 2)", department: "Artificial Intelligence", size: 38, program: "M.Tech AI & DS", semester: 2 },
];

export const INITIAL_FACULTY: Faculty[] = [
  {
    faculty_id: "FAC_ALAN",
    name: "Prof. Alan Turing",
    email: "a.turing@university.edu",
    department: "Computer Science",
    max_weekly_hours: 14,
    available_days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    qualified_courses: ["CS201", "CS401"],
    unavailable_slots: ["TS_FRI_5"],
    preferred_slots: ["TS_MON_1", "TS_WED_2"],
    specialization: "Theoretical CS & Distributed Systems",
  },
  {
    faculty_id: "FAC_GRACE",
    name: "Prof. Grace Hopper",
    email: "g.hopper@university.edu",
    department: "Computer Science",
    max_weekly_hours: 16,
    available_days: ["Monday", "Tuesday", "Wednesday", "Thursday"], // No Friday
    qualified_courses: ["CS202", "CS302"],
    unavailable_slots: ["TS_MON_1"],
    preferred_slots: ["TS_TUE_2", "TS_THU_3"],
    specialization: "Compilers & Architecture",
  },
  {
    faculty_id: "FAC_JOHN",
    name: "Prof. John von Neumann",
    email: "j.vonneumann@university.edu",
    department: "Computer Science",
    max_weekly_hours: 14,
    available_days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    qualified_courses: ["CS203", "AI501"],
    unavailable_slots: [],
    preferred_slots: ["TS_MON_2", "TS_TUE_1"],
    specialization: "Operating Systems & Quantum Info",
  },
  {
    faculty_id: "FAC_ADA",
    name: "Prof. Ada Lovelace",
    email: "a.lovelace@university.edu",
    department: "Computer Science",
    max_weekly_hours: 16,
    available_days: ["Tuesday", "Wednesday", "Thursday", "Friday"], // No Monday
    qualified_courses: ["CS204", "AI502"],
    unavailable_slots: ["TS_WED_5"],
    preferred_slots: ["TS_WED_2", "TS_FRI_3"],
    specialization: "Practical Algorithms & NLP",
  },
  {
    faculty_id: "FAC_CLAUDE",
    name: "Prof. Claude Shannon",
    email: "c.shannon@university.edu",
    department: "Artificial Intelligence",
    max_weekly_hours: 14,
    available_days: ["Monday", "Wednesday", "Friday"],
    qualified_courses: ["CS305", "AI503"],
    unavailable_slots: [],
    preferred_slots: ["TS_MON_3", "TS_FRI_1"],
    specialization: "Information Theory & Probabilistic Models",
  },
];

export const INITIAL_COURSES: Course[] = [
  // CS Sem 4 courses
  { course_id: "CRS_CS201", code: "CS201", title: "Data Structures & Algorithms", weekly_hours: 3, required_room_type: "LECTURE_HALL", category: "Theory", is_lab: false, assigned_faculty_id: "FAC_ALAN", target_group_id: "GRP_CS_SEM4" },
  { course_id: "CRS_CS202", code: "CS202", title: "Computer Organization & Architecture", weekly_hours: 3, required_room_type: "LECTURE_HALL", category: "Theory", is_lab: false, assigned_faculty_id: "FAC_GRACE", target_group_id: "GRP_CS_SEM4" },
  { course_id: "CRS_CS203", code: "CS203", title: "Operating Systems", weekly_hours: 3, required_room_type: "LECTURE_HALL", category: "Theory", is_lab: false, assigned_faculty_id: "FAC_JOHN", target_group_id: "GRP_CS_SEM4" },
  { course_id: "CRS_CS204", code: "CS204", title: "Operating Systems Practical Lab", weekly_hours: 2, required_room_type: "LAB", category: "Practical", is_lab: true, assigned_faculty_id: "FAC_ADA", target_group_id: "GRP_CS_SEM4" },

  // CS Sem 6 courses
  { course_id: "CRS_CS302", code: "CS302", title: "Compiler Design", weekly_hours: 3, required_room_type: "LECTURE_HALL", category: "Theory", is_lab: false, assigned_faculty_id: "FAC_GRACE", target_group_id: "GRP_CS_SEM6" },
  { course_id: "CRS_CS305", code: "CS305", title: "Information & Coding Theory", weekly_hours: 3, required_room_type: "LECTURE_HALL", category: "Theory", is_lab: false, assigned_faculty_id: "FAC_CLAUDE", target_group_id: "GRP_CS_SEM6" },
  { course_id: "CRS_CS401", code: "CS401", title: "Distributed Computing Lab", weekly_hours: 2, required_room_type: "LAB", category: "Practical", is_lab: true, assigned_faculty_id: "FAC_ALAN", target_group_id: "GRP_CS_SEM6" },

  // M.Tech AI Sem 2 courses
  { course_id: "CRS_AI501", code: "AI501", title: "Advanced Machine Learning", weekly_hours: 3, required_room_type: "LECTURE_HALL", category: "Theory", is_lab: false, assigned_faculty_id: "FAC_JOHN", target_group_id: "GRP_AI_SEM2" },
  { course_id: "CRS_AI502", code: "AI502", title: "Natural Language Processing Lab", weekly_hours: 2, required_room_type: "LAB", category: "Practical", is_lab: true, assigned_faculty_id: "FAC_ADA", target_group_id: "GRP_AI_SEM2" },
  { course_id: "CRS_AI503", code: "AI503", title: "Probabilistic Graphical Models", weekly_hours: 3, required_room_type: "LECTURE_HALL", category: "Theory", is_lab: false, assigned_faculty_id: "FAC_CLAUDE", target_group_id: "GRP_AI_SEM2" },
];

export const INITIAL_TIMESLOTS: Timeslot[] = (() => {
  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] as const;
  const hours = [
    { start: "09:00", end: "10:00", isBreak: false },
    { start: "10:00", end: "11:00", isBreak: false },
    { start: "11:00", end: "12:00", isBreak: false },
    { start: "12:00", end: "13:00", isBreak: true }, // Institutional Lunch Break
    { start: "14:00", end: "15:00", isBreak: false },
  ];

  const slots: Timeslot[] = [];
  days.forEach((day) => {
    hours.forEach((h, hIdx) => {
      slots.push({
        slot_id: `TS_${day.substring(0, 3).toUpperCase()}_${hIdx + 1}`,
        day,
        start_time: h.start,
        end_time: h.end,
        duration_minutes: 60,
        is_break: h.isBreak,
      });
    });
  });
  return slots;
})();

export const MOCK_COURSES = INITIAL_COURSES;
export const MOCK_CLASSROOMS = INITIAL_CLASSROOMS;
export const MOCK_FACULTY = INITIAL_FACULTY;

export const MOCK_ROOM_UTILIZATION = [
  { name: "Lecture Hall 101", utilization: 72, capacity: 80 },
  { name: "Lecture Hall 102", utilization: 68, capacity: 70 },
  { name: "Lecture Hall 103", utilization: 55, capacity: 50 },
  { name: "AI & Robotics Lab", utilization: 80, capacity: 60 },
  { name: "Software Systems Lab", utilization: 75, capacity: 60 },
  { name: "Seminar Room A", utilization: 30, capacity: 40 },
];
