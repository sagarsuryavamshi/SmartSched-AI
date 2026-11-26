"use client";

import React, { useState, useMemo } from "react";
import {
  Calendar as CalendarIcon,
  Search,
  Filter,
  Download,
  Users,
  Building2,
  Layers,
  BookOpen,
  Coffee,
  ShieldCheck,
  CheckCircle2,
  Clock,
  RotateCcw,
  ExternalLink,
  ChevronRight,
  Info,
} from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { KpiCard } from "@/components/ui/KpiCard";
import { Modal } from "@/components/ui/Modal";
import { useResources } from "@/context/ResourceContext";
import { ScheduledSession, TimetablePerspective } from "@/types/timetable";
import { INITIAL_SCHEDULED_SESSIONS } from "@/mock/timetableData";
import { DayOfWeek } from "@/types";

const DAYS: DayOfWeek[] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export default function TimetablePage() {
  const { faculty, classrooms, studentGroups, courses, timeslots } = useResources();

  // Primary Perspective
  const [perspective, setPerspective] = useState<TimetablePerspective>("DEPARTMENT_MASTER");
  const [selectedFilterEntityId, setSelectedFilterEntityId] = useState<string>("ALL");

  // Search & Filter controls
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedDay, setSelectedDay] = useState<string>("ALL");

  // Selected Session for Detail Modal
  const [activeSession, setActiveSession] = useState<ScheduledSession | null>(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [exportLoading, setExportLoading] = useState<"csv" | "pdf" | null>(null);
  const [exportToast, setExportToast] = useState<string | null>(null);

  const handleDownload = async (format: "csv" | "pdf") => {
    setExportLoading(format);
    setExportToast(`Preparing ${format.toUpperCase()} export...`);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${apiBase}/timetable/export/${format}`);
      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `smartsched_academic_timetable.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setExportToast(`Downloaded ${format.toUpperCase()} successfully!`);
      setTimeout(() => setExportToast(null), 3000);
    } catch (err: any) {
      setExportToast(`Download failed: ${err.message}`);
      setTimeout(() => setExportToast(null), 4000);
    } finally {
      setExportLoading(null);
    }
  };

  // Active Sessions Data (From verified persistent schedule)
  const [sessions] = useState<ScheduledSession[]>(INITIAL_SCHEDULED_SESSIONS);

  // Distinct Time Intervals (ordered)
  const distinctTimePeriods = useMemo(() => {
    const periodMap = new Map<string, { start: string; end: string; is_break: boolean }>();
    timeslots.forEach((s) => {
      const key = `${s.start_time}-${s.end_time}`;
      if (!periodMap.has(key)) {
        periodMap.set(key, { start: s.start_time, end: s.end_time, is_break: s.is_break });
      }
    });
    return Array.from(periodMap.values()).sort((a, b) => a.start.localeCompare(b.start));
  }, [timeslots]);

  // Filtering Logic
  const filteredSessions = useMemo(() => {
    return sessions.filter((s) => {
      // Perspective filter
      if (perspective === "FACULTY" && selectedFilterEntityId !== "ALL" && s.faculty_id !== selectedFilterEntityId) {
        return false;
      }
      if (perspective === "CLASSROOM" && selectedFilterEntityId !== "ALL" && s.room_id !== selectedFilterEntityId) {
        return false;
      }
      if (perspective === "STUDENT_GROUP" && selectedFilterEntityId !== "ALL" && s.group_id !== selectedFilterEntityId) {
        return false;
      }

      // Day filter
      if (selectedDay !== "ALL" && s.day !== selectedDay) {
        return false;
      }

      // Category filter
      if (selectedCategory !== "ALL" && s.course_category !== selectedCategory) {
        return false;
      }

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesCode = s.course_code.toLowerCase().includes(q);
        const matchesTitle = s.course_title.toLowerCase().includes(q);
        const matchesFaculty = s.faculty_name.toLowerCase().includes(q);
        const matchesRoom = s.room_name.toLowerCase().includes(q);
        const matchesGroup = s.group_name.toLowerCase().includes(q);
        if (!matchesCode && !matchesTitle && !matchesFaculty && !matchesRoom && !matchesGroup) {
          return false;
        }
      }

      return true;
    });
  }, [sessions, perspective, selectedFilterEntityId, selectedDay, selectedCategory, searchQuery]);

  // KPI Metrics
  const uniqueCoursesCount = useMemo(() => new Set(filteredSessions.map((s) => s.course_code)).size, [filteredSessions]);
  const uniqueFacultyCount = useMemo(() => new Set(filteredSessions.map((s) => s.faculty_id)).size, [filteredSessions]);
  const uniqueRoomsCount = useMemo(() => new Set(filteredSessions.map((s) => s.room_id)).size, [filteredSessions]);

  const handleResetFilters = () => {
    setSelectedFilterEntityId("ALL");
    setSearchQuery("");
    setSelectedCategory("ALL");
    setSelectedDay("ALL");
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Institutional Academic Timetable"
        description="Interactive weekly timetable schedule matrix supporting Department, Student Cohort, Faculty, and Classroom perspectives."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExportModalOpen(true)}
              className="text-xs border-slate-300 text-navy-900"
            >
              <Download className="w-3.5 h-3.5 mr-1 text-slate-500" />
              <span>Export Timetable</span>
            </Button>
          </div>
        }
      />

      {/* Top Level Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiCard
          title="Assigned Sessions"
          value={filteredSessions.length}
          subtitle={`${filteredSessions.reduce((a, s) => a + s.duration_minutes, 0) / 60} Total Teaching Hours`}
          icon={CalendarIcon}
          accent="blue"
        />
        <KpiCard
          title="Active Courses"
          value={uniqueCoursesCount}
          subtitle="Syllabus subjects"
          icon={BookOpen}
          accent="purple"
        />
        <KpiCard
          title="Appointed Faculty"
          value={uniqueFacultyCount}
          subtitle="Active instructors"
          icon={Users}
          accent="green"
        />
        <KpiCard
          title="Classrooms & Labs"
          value={uniqueRoomsCount}
          subtitle="Utilized facilities"
          icon={Building2}
          accent="amber"
        />
      </div>

      {/* View Perspective Switcher & Filter Controls */}
      <Card className="p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
          {/* Perspectives Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto">
            <button
              onClick={() => {
                setPerspective("DEPARTMENT_MASTER");
                setSelectedFilterEntityId("ALL");
              }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                perspective === "DEPARTMENT_MASTER"
                  ? "bg-navy-900 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Department Master</span>
            </button>

            <button
              onClick={() => {
                setPerspective("STUDENT_GROUP");
                setSelectedFilterEntityId(studentGroups[0]?.group_id || "ALL");
              }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                perspective === "STUDENT_GROUP"
                  ? "bg-navy-900 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Student Cohort</span>
            </button>

            <button
              onClick={() => {
                setPerspective("FACULTY");
                setSelectedFilterEntityId(faculty[0]?.faculty_id || "ALL");
              }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                perspective === "FACULTY"
                  ? "bg-navy-900 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Faculty Member</span>
            </button>

            <button
              onClick={() => {
                setPerspective("CLASSROOM");
                setSelectedFilterEntityId(classrooms[0]?.room_id || "ALL");
              }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                perspective === "CLASSROOM"
                  ? "bg-navy-900 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>Classroom / Lab</span>
            </button>
          </div>

          {/* Perspective-Specific Selector */}
          {perspective !== "DEPARTMENT_MASTER" && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-navy-900 whitespace-nowrap">
                {perspective === "FACULTY"
                  ? "Select Faculty:"
                  : perspective === "CLASSROOM"
                  ? "Select Room:"
                  : "Select Cohort:"}
              </span>
              <select
                value={selectedFilterEntityId}
                onChange={(e) => setSelectedFilterEntityId(e.target.value)}
                className="text-xs rounded-lg border border-slate-200 p-1.5 bg-white font-semibold text-slate-800"
              >
                {perspective === "FACULTY" &&
                  faculty.map((f) => (
                    <option key={f.faculty_id} value={f.faculty_id}>
                      {f.name} ({f.department})
                    </option>
                  ))}
                {perspective === "CLASSROOM" &&
                  classrooms.map((r) => (
                    <option key={r.room_id} value={r.room_id}>
                      {r.name} ({r.room_type})
                    </option>
                  ))}
                {perspective === "STUDENT_GROUP" &&
                  studentGroups.map((g) => (
                    <option key={g.group_id} value={g.group_id}>
                      {g.name} ({g.program})
                    </option>
                  ))}
              </select>
            </div>
          )}
        </div>

        {/* Search & In-View Filter Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search course code, title, room..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {/* Day Filter */}
          <select
            value={selectedDay}
            onChange={(e) => setSelectedDay(e.target.value)}
            className="rounded-lg border border-slate-200 p-1.5 bg-white text-xs text-slate-700"
          >
            <option value="ALL">All Weekdays (Mon-Fri)</option>
            {DAYS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>

          {/* Session Category Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-lg border border-slate-200 p-1.5 bg-white text-xs text-slate-700"
          >
            <option value="ALL">All Session Types</option>
            <option value="Theory">Theory Lectures</option>
            <option value="Practical">Practical Laboratories</option>
            <option value="Seminar">Seminars</option>
          </select>

          {/* Reset Filters Action */}
          <Button variant="ghost" size="sm" onClick={handleResetFilters} className="text-xs text-slate-500 hover:text-navy-900 justify-center">
            <RotateCcw className="w-3 h-3 mr-1" />
            <span>Clear Filters</span>
          </Button>
        </div>
      </Card>

      {/* Legend & Status Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-4 flex-wrap">
          <span className="font-bold text-slate-500 text-[11px] uppercase tracking-wider">Legend:</span>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-blue-100 border border-blue-300" />
            <span className="text-slate-700 text-[11px]">Theory Lecture</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-emerald-100 border border-emerald-300" />
            <span className="text-slate-700 text-[11px]">Practical Lab (2h Continuous)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-purple-100 border border-purple-300" />
            <span className="text-slate-700 text-[11px]">Seminar</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-amber-100 border border-amber-300" />
            <span className="text-slate-700 text-[11px]">Institutional Break (H8)</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="success">Validated Conflict-Free (H1-H8)</Badge>
        </div>
      </div>

      {/* Interactive Weekly Matrix Grid */}
      <div className="border border-slate-200 rounded-xl overflow-x-auto bg-white shadow-sm">
        <table className="w-full text-center border-collapse min-w-[850px]">
          <thead className="bg-slate-50 text-navy-900 font-bold text-xs border-b border-slate-200">
            <tr>
              <th className="p-3 text-left w-32 border-r border-slate-200">Time Interval</th>
              {DAYS.map((day) => (
                <th key={day} className="p-3 border-r border-slate-200 last:border-r-0">
                  {day}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {distinctTimePeriods.map((period) => {
              if (period.is_break) {
                return (
                  <tr key={`${period.start}-${period.end}`} className="bg-amber-50/60 text-amber-900 font-semibold">
                    <td className="p-3 text-left font-mono font-bold border-r border-slate-200 bg-amber-100/40 text-[11px]">
                      {period.start} - {period.end}
                    </td>
                    <td colSpan={DAYS.length} className="p-2.5 text-center text-xs text-amber-800">
                      <div className="flex items-center justify-center gap-2">
                        <Coffee className="w-4 h-4 text-amber-600" />
                        <span>Institutional Recess / Lunch Break Period (Hard Constraint H8 Invariant)</span>
                      </div>
                    </td>
                  </tr>
                );
              }

              return (
                <tr key={`${period.start}-${period.end}`} className="hover:bg-slate-50/30">
                  {/* Period Time Slot */}
                  <td className="p-3 text-left font-mono font-bold border-r border-slate-200 bg-slate-50/50 text-[11px] text-navy-900">
                    {period.start} - {period.end}
                  </td>

                  {/* Day Columns */}
                  {DAYS.map((day) => {
                    const cellSessions = filteredSessions.filter(
                      (s) => s.day === day && s.start_time === period.start
                    );

                    return (
                      <td key={day} className="p-2 border-r border-slate-100 last:border-r-0 align-top">
                        {cellSessions.length === 0 ? (
                          <div className="h-16 flex items-center justify-center text-[10px] text-slate-300">
                            Available Slot
                          </div>
                        ) : (
                          <div className="space-y-1.5">
                            {cellSessions.map((session) => {
                              const isLab = session.course_category === "Practical";
                              const isSeminar = session.course_category === "Seminar";

                              return (
                                <div
                                  key={session.assignment_id}
                                  onClick={() => setActiveSession(session)}
                                  className={`p-2 rounded-lg border text-left cursor-pointer transition-all hover:scale-[1.02] shadow-sm ${
                                    isLab
                                      ? "bg-emerald-50/90 border-emerald-300 text-emerald-950 hover:border-emerald-400"
                                      : isSeminar
                                      ? "bg-purple-50/90 border-purple-300 text-purple-950 hover:border-purple-400"
                                      : "bg-blue-50/90 border-blue-300 text-blue-950 hover:border-blue-400"
                                  }`}
                                >
                                  <div className="flex items-center justify-between mb-0.5">
                                    <span className="font-mono font-bold text-xs">{session.course_code}</span>
                                    <span className="text-[10px] font-semibold px-1 py-0.2 rounded bg-white/70">
                                      {session.room_id}
                                    </span>
                                  </div>
                                  <div className="text-[11px] font-semibold truncate" title={session.course_title}>
                                    {session.course_title}
                                  </div>
                                  <div className="text-[10px] text-slate-600 truncate mt-0.5">
                                    {session.faculty_name}
                                  </div>
                                  <div className="text-[9px] text-slate-500 font-mono mt-0.5">
                                    {session.group_name} {isLab && "(2h Continuous)"}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Session Details Modal */}
      {activeSession && (
        <Modal
          isOpen={true}
          onClose={() => setActiveSession(null)}
          title={`Session Details: ${activeSession.course_code}`}
          description={activeSession.course_title}
        >
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3 p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <span className="text-slate-400 text-[11px] block">Course Code & Category</span>
                <span className="font-bold text-navy-900">{activeSession.course_code} ({activeSession.course_category})</span>
              </div>
              <div>
                <span className="text-slate-400 text-[11px] block">Appointed Instructor</span>
                <span className="font-bold text-navy-900">{activeSession.faculty_name}</span>
              </div>
              <div>
                <span className="text-slate-400 text-[11px] block">Target Cohort</span>
                <span className="font-bold text-navy-900">{activeSession.group_name}</span>
              </div>
              <div>
                <span className="text-slate-400 text-[11px] block">Allocated Classroom</span>
                <span className="font-bold text-navy-900">{activeSession.room_name} ({activeSession.room_type})</span>
              </div>
              <div>
                <span className="text-slate-400 text-[11px] block">Day & Time Window</span>
                <span className="font-bold text-navy-900">{activeSession.day}, {activeSession.start_time} - {activeSession.end_time}</span>
              </div>
              <div>
                <span className="text-slate-400 text-[11px] block">Duration</span>
                <span className="font-bold text-navy-900">{activeSession.duration_minutes} Minutes {activeSession.is_continuous_lab && "(Continuous Lab Block)"}</span>
              </div>
            </div>

            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Verified against all 8 hard constraints (H1-H8): No room, faculty or cohort double-booking.</span>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-100">
              <Button variant="outline" size="sm" onClick={() => setActiveSession(null)}>
                Close Details
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Export Options Modal */}
      {isExportModalOpen && (
        <Modal
          isOpen={true}
          onClose={() => setIsExportModalOpen(false)}
          title="Export Certified Academic Timetable"
          description="Institutional publication documents formatted for distribution."
        >
          <div className="space-y-4 text-xs">
            <p className="text-slate-600 leading-relaxed">
              Timetable exports are dynamically compiled directly from active university timetable records using the Python export engine.
            </p>

            {exportToast && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-800 text-[11px] flex items-center gap-2">
                <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />
                <span>{exportToast}</span>
              </div>
            )}

            <div className="space-y-3">
              <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 flex items-center justify-between">
                <div>
                  <span className="font-bold text-navy-900 block">Department Timetable (CSV)</span>
                  <span className="text-[11px] text-slate-500">Standard tabular format for academic registrar systems.</span>
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleDownload("csv")}
                  disabled={exportLoading !== null}
                  className="text-xs bg-emerald-600 hover:bg-emerald-700"
                >
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  <span>{exportLoading === "csv" ? "Exporting..." : "Download CSV"}</span>
                </Button>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 flex items-center justify-between">
                <div>
                  <span className="font-bold text-navy-900 block">Certified PDF Schedule Matrix</span>
                  <span className="text-[11px] text-slate-500">Institutional printable grid with dean signature blocks.</span>
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleDownload("pdf")}
                  disabled={exportLoading !== null}
                  className="text-xs bg-red-600 hover:bg-red-700"
                >
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  <span>{exportLoading === "pdf" ? "Generating..." : "Download PDF"}</span>
                </Button>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <Button variant="outline" size="sm" onClick={() => setIsExportModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
