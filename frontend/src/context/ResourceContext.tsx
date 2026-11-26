"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { Classroom, Course, Faculty, StudentGroup, Timeslot } from "@/types";
import {
  INITIAL_CLASSROOMS,
  INITIAL_COURSES,
  INITIAL_FACULTY,
  INITIAL_STUDENT_GROUPS,
  INITIAL_TIMESLOTS,
} from "@/mock/data";
import { ApiClient } from "@/services/apiClient";

interface ResourceContextType {
  classrooms: Classroom[];
  faculty: Faculty[];
  studentGroups: StudentGroup[];
  courses: Course[];
  timeslots: Timeslot[];
  isLiveBackend: boolean;
  syncError: string | null;
  clearSyncError: () => void;
  refreshResources: () => Promise<void>;

  // Classroom CRUD
  addClassroom: (room: Classroom) => boolean;
  updateClassroom: (room: Classroom) => boolean;
  deleteClassroom: (roomId: string) => { success: boolean; message?: string };

  // Faculty CRUD & Availability
  addFaculty: (f: Faculty) => boolean;
  updateFaculty: (f: Faculty) => boolean;
  deleteFaculty: (facultyId: string) => { success: boolean; message?: string };
  toggleFacultySlotAvailability: (facultyId: string, slotId: string) => void;
  toggleFacultySlotPreferred: (facultyId: string, slotId: string) => void;

  // Student Group CRUD
  addStudentGroup: (g: StudentGroup) => boolean;
  updateStudentGroup: (g: StudentGroup) => boolean;
  deleteStudentGroup: (groupId: string) => { success: boolean; message?: string };

  // Course CRUD
  addCourse: (c: Course) => boolean;
  updateCourse: (c: Course) => boolean;
  deleteCourse: (courseId: string) => { success: boolean; message?: string };

  // Timeslot CRUD
  addTimeslot: (ts: Timeslot) => { success: boolean; message?: string };
  updateTimeslot: (ts: Timeslot) => { success: boolean; message?: string };
  deleteTimeslot: (slotId: string) => { success: boolean; message?: string };
  toggleTimeslotBreak: (slotId: string) => void;

  // Session Reset
  resetToDefault: () => void;
}

const ResourceContext = createContext<ResourceContextType | undefined>(undefined);

export function ResourceProvider({ children }: { children: React.ReactNode }) {
  const [classrooms, setClassrooms] = useState<Classroom[]>(INITIAL_CLASSROOMS);
  const [faculty, setFaculty] = useState<Faculty[]>(INITIAL_FACULTY);
  const [studentGroups, setStudentGroups] = useState<StudentGroup[]>(INITIAL_STUDENT_GROUPS);
  const [courses, setCourses] = useState<Course[]>(INITIAL_COURSES);
  const [timeslots, setTimeslots] = useState<Timeslot[]>(INITIAL_TIMESLOTS);
  const [isLiveBackend, setIsLiveBackend] = useState<boolean>(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  const clearSyncError = () => setSyncError(null);

  const fetchLiveResources = async () => {
    try {
      const [rooms, fac, groups, crs, slots] = await Promise.all([
        ApiClient.get<Classroom[]>("/resources/classrooms"),
        ApiClient.get<any[]>("/resources/faculty"),
        ApiClient.get<StudentGroup[]>("/resources/groups"),
        ApiClient.get<Course[]>("/resources/courses"),
        ApiClient.get<Timeslot[]>("/resources/timeslots"),
      ]);

      if (rooms) setClassrooms(rooms);
      if (fac) {
        const normalizedFac: Faculty[] = fac.map((f: any) => ({
          faculty_id: f.faculty_id,
          name: f.name,
          email: f.email,
          department: f.department,
          max_weekly_hours: f.max_weekly_hours,
          available_days: f.available_days_list || (typeof f.available_days === "string" ? JSON.parse(f.available_days) : f.available_days) || [],
          qualified_courses: f.qualified_courses_list || (typeof f.qualified_courses === "string" ? JSON.parse(f.qualified_courses) : f.qualified_courses) || [],
          unavailable_slots: f.unavailable_slots_list || (typeof f.unavailable_slots === "string" ? JSON.parse(f.unavailable_slots) : f.unavailable_slots) || [],
        }));
        setFaculty(normalizedFac);
      }
      if (groups) setStudentGroups(groups);
      if (crs) setCourses(crs);
      if (slots) setTimeslots(slots);

      setIsLiveBackend(true);
    } catch (e) {
      console.warn("Could not connect to FastAPI backend, falling back to cached state:", e);
      setIsLiveBackend(false);
    }
  };

  // Fetch live resources directly from FastAPI backend on mount
  useEffect(() => {
    fetchLiveResources();
  }, []);

  const handleSyncFailure = (err: any) => {
    setSyncError(err?.message || "Failed to persist resource change to backend.");
    fetchLiveResources();
  };

  // Classroom CRUD
  const addClassroom = (room: Classroom) => {
    if (classrooms.some((r) => r.room_id === room.room_id)) return false;
    setSyncError(null);
    setClassrooms((prev) => [...prev, room]);
    ApiClient.post("/resources/classrooms", room).catch(handleSyncFailure);
    return true;
  };

  const updateClassroom = (room: Classroom) => {
    setSyncError(null);
    setClassrooms((prev) => prev.map((r) => (r.room_id === room.room_id ? room : r)));
    ApiClient.put(`/resources/classrooms/${room.room_id}`, room).catch(handleSyncFailure);
    return true;
  };

  const deleteClassroom = (roomId: string) => {
    setSyncError(null);
    setClassrooms((prev) => prev.filter((r) => r.room_id !== roomId));
    ApiClient.delete(`/resources/classrooms/${roomId}`).catch(handleSyncFailure);
    return { success: true };
  };

  // Faculty CRUD & Availability
  const addFaculty = (f: Faculty) => {
    if (faculty.some((item) => item.faculty_id === f.faculty_id)) return false;
    setSyncError(null);
    setFaculty((prev) => [...prev, f]);
    ApiClient.post("/resources/faculty", f).catch(handleSyncFailure);
    return true;
  };

  const updateFaculty = (f: Faculty) => {
    setSyncError(null);
    setFaculty((prev) => prev.map((item) => (item.faculty_id === f.faculty_id ? f : item)));
    ApiClient.put(`/resources/faculty/${f.faculty_id}`, f).catch(handleSyncFailure);
    return true;
  };

  const deleteFaculty = (facultyId: string) => {
    const isAssigned = courses.some((c) => c.assigned_faculty_id === facultyId);
    if (isAssigned) {
      return {
        success: false,
        message: `Cannot delete faculty '${facultyId}': assigned to active academic courses. Reassign courses first.`,
      };
    }
    setSyncError(null);
    setFaculty((prev) => prev.filter((item) => item.faculty_id !== facultyId));
    ApiClient.delete(`/resources/faculty/${facultyId}`).catch(handleSyncFailure);
    return { success: true };
  };

  const toggleFacultySlotAvailability = (facultyId: string, slotId: string) => {
    setSyncError(null);
    setFaculty((prev) =>
      prev.map((f) => {
        if (f.faculty_id !== facultyId) return f;
        const currentUnavail = f.unavailable_slots || [];
        const isUnavailable = currentUnavail.includes(slotId);
        const updated = isUnavailable
          ? currentUnavail.filter((s) => s !== slotId)
          : [...currentUnavail, slotId];
        
        ApiClient.put(`/resources/faculty/${facultyId}`, { unavailable_slots: updated }).catch(handleSyncFailure);

        return {
          ...f,
          unavailable_slots: updated,
        };
      })
    );
  };

  const toggleFacultySlotPreferred = (facultyId: string, slotId: string) => {
    setFaculty((prev) =>
      prev.map((f) => {
        if (f.faculty_id !== facultyId) return f;
        const currentPref = f.preferred_slots || [];
        const isPreferred = currentPref.includes(slotId);
        const updated = isPreferred
          ? currentPref.filter((s) => s !== slotId)
          : [...currentPref, slotId];
        return {
          ...f,
          preferred_slots: updated,
        };
      })
    );
  };

  // Student Group CRUD
  const addStudentGroup = (g: StudentGroup) => {
    if (studentGroups.some((item) => item.group_id === g.group_id)) return false;
    setSyncError(null);
    setStudentGroups((prev) => [...prev, g]);
    ApiClient.post("/resources/groups", g).catch(handleSyncFailure);
    return true;
  };

  const updateStudentGroup = (g: StudentGroup) => {
    setSyncError(null);
    setStudentGroups((prev) => prev.map((item) => (item.group_id === g.group_id ? g : item)));
    ApiClient.put(`/resources/groups/${g.group_id}`, g).catch(handleSyncFailure);
    return true;
  };

  const deleteStudentGroup = (groupId: string) => {
    const isAssigned = courses.some((c) => c.target_group_id === groupId);
    if (isAssigned) {
      return {
        success: false,
        message: `Cannot delete student group '${groupId}': active courses are scheduled for this group.`,
      };
    }
    setSyncError(null);
    setStudentGroups((prev) => prev.filter((item) => item.group_id !== groupId));
    ApiClient.delete(`/resources/groups/${groupId}`).catch(handleSyncFailure);
    return { success: true };
  };

  // Course CRUD
  const addCourse = (c: Course) => {
    if (courses.some((item) => item.course_id === c.course_id || item.code === c.code)) return false;
    setSyncError(null);
    setCourses((prev) => [...prev, c]);
    ApiClient.post("/resources/courses", c).catch(handleSyncFailure);
    return true;
  };

  const updateCourse = (c: Course) => {
    setSyncError(null);
    setCourses((prev) => prev.map((item) => (item.course_id === c.course_id ? c : item)));
    ApiClient.put(`/resources/courses/${c.course_id}`, c).catch(handleSyncFailure);
    return true;
  };

  const deleteCourse = (courseId: string) => {
    setSyncError(null);
    setCourses((prev) => prev.filter((item) => item.course_id !== courseId));
    ApiClient.delete(`/resources/courses/${courseId}`).catch(handleSyncFailure);
    return { success: true };
  };

  // Timeslot CRUD
  const addTimeslot = (ts: Timeslot) => {
    if (timeslots.some((item) => item.slot_id === ts.slot_id)) {
      return { success: false, message: `Timeslot '${ts.slot_id}' already exists.` };
    }
    setSyncError(null);
    setTimeslots((prev) => [...prev, ts]);
    ApiClient.post("/resources/timeslots", ts).catch(handleSyncFailure);
    return { success: true };
  };

  const updateTimeslot = (ts: Timeslot) => {
    setSyncError(null);
    setTimeslots((prev) => prev.map((item) => (item.slot_id === ts.slot_id ? ts : item)));
    ApiClient.put(`/resources/timeslots/${ts.slot_id}`, ts).catch(handleSyncFailure);
    return { success: true };
  };

  const deleteTimeslot = (slotId: string) => {
    setSyncError(null);
    setTimeslots((prev) => prev.filter((item) => item.slot_id !== slotId));
    ApiClient.delete(`/resources/timeslots/${slotId}`).catch(handleSyncFailure);
    return { success: true };
  };

  const toggleTimeslotBreak = (slotId: string) => {
    setSyncError(null);
    setTimeslots((prev) =>
      prev.map((ts) => {
        if (ts.slot_id !== slotId) return ts;
        const newBreak = !ts.is_break;
        ApiClient.put(`/resources/timeslots/${slotId}`, { is_break: newBreak }).catch(handleSyncFailure);
        return {
          ...ts,
          is_break: newBreak,
        };
      })
    );
  };

  const resetToDefault = () => {
    setClassrooms(INITIAL_CLASSROOMS);
    setFaculty(INITIAL_FACULTY);
    setStudentGroups(INITIAL_STUDENT_GROUPS);
    setCourses(INITIAL_COURSES);
    setTimeslots(INITIAL_TIMESLOTS);
  };

  return (
    <ResourceContext.Provider
      value={{
        classrooms,
        faculty,
        studentGroups,
        courses,
        timeslots,
        isLiveBackend,
        syncError,
        clearSyncError,
        refreshResources: fetchLiveResources,
        addClassroom,
        updateClassroom,
        deleteClassroom,
        addFaculty,
        updateFaculty,
        deleteFaculty,
        toggleFacultySlotAvailability,
        toggleFacultySlotPreferred,
        addStudentGroup,
        updateStudentGroup,
        deleteStudentGroup,
        addCourse,
        updateCourse,
        deleteCourse,
        addTimeslot,
        updateTimeslot,
        deleteTimeslot,
        toggleTimeslotBreak,
        resetToDefault,
      }}
    >
      {children}
    </ResourceContext.Provider>
  );
}

export function useResources() {
  const context = useContext(ResourceContext);
  if (!context) {
    throw new Error("useResources must be used within a ResourceProvider");
  }
  return context;
}
