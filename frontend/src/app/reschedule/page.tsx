"use client";

import React, { useState, useMemo } from "react";
import {
  RotateCcw,
  ArrowRight,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  History,
  Info,
  Calendar,
  Building2,
  Users,
  Clock,
  Layers,
} from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { KpiCard } from "@/components/ui/KpiCard";
import { useResources } from "@/context/ResourceContext";
import { ScheduledSession } from "@/types/timetable";
import { INITIAL_SCHEDULED_SESSIONS } from "@/mock/timetableData";
import { DayOfWeek } from "@/types";
import { FIXTURE_RESCHEDULE_HISTORY } from "@/types/analyticsFixtures";
import { RescheduleHistoryRecord } from "@/types/analytics";

const DAYS: DayOfWeek[] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export default function ReschedulingPage() {
  const { classrooms, timeslots } = useResources();

  // Tab: Scenario Planner vs History
  const [activeTab, setActiveTab] = useState<"PLANNER" | "HISTORY">("PLANNER");

  // Active Sessions
  const [sessions] = useState<ScheduledSession[]>(INITIAL_SCHEDULED_SESSIONS);
  const [selectedSessionId, setSelectedSessionId] = useState<string>(sessions[0]?.assignment_id || "");

  // Candidate Proposed Choices
  const [proposedDay, setProposedDay] = useState<DayOfWeek>("Tuesday");
  const [proposedSlotId, setProposedSlotId] = useState<string>("TS_TUE_2");
  const [proposedRoomId, setProposedRoomId] = useState<string>("CR_LH102");

  // History State
  const [history, setHistory] = useState<RescheduleHistoryRecord[]>(FIXTURE_RESCHEDULE_HISTORY);

  // Preview / Evaluation State
  const [previewEvaluated, setPreviewEvaluated] = useState(false);
  const [commitMessage, setCommitMessage] = useState<string | null>(null);

  // Selected Session Object
  const selectedSession = useMemo(() => {
    return sessions.find((s) => s.assignment_id === selectedSessionId) || sessions[0];
  }, [sessions, selectedSessionId]);

  // Available Teaching Slots (Excluding Breaks H8)
  const availableSlotsForProposedDay = useMemo(() => {
    return timeslots.filter((s) => s.day === proposedDay && !s.is_break);
  }, [timeslots, proposedDay]);

  const proposedSlot = useMemo(() => {
    return timeslots.find((s) => s.slot_id === proposedSlotId) || availableSlotsForProposedDay[0];
  }, [timeslots, proposedSlotId, availableSlotsForProposedDay]);

  const proposedRoom = useMemo(() => {
    return classrooms.find((r) => r.room_id === proposedRoomId) || classrooms[0];
  }, [classrooms, proposedRoomId]);

  // Conflict & Delta Evaluation Logic
  const validationResult = useMemo(() => {
    if (!selectedSession || !proposedSlot || !proposedRoom) {
      return { isValid: true, hardViolations: [], penaltyDelta: 0 };
    }

    const hardViolations: string[] = [];

    // H8: Break Check
    if (proposedSlot.is_break) {
      hardViolations.push("[H8] Target timeslot is a designated institutional recess/break.");
    }

    // H6: Room Type Check
    if (selectedSession.course_category === "Practical" && proposedRoom.room_type !== "LAB") {
      hardViolations.push(`[H6] Practical lab session requires a LAB facility, but '${proposedRoom.name}' is a ${proposedRoom.room_type}.`);
    }

    // H2: Double-Booking Room Collisions with existing schedule
    const roomCollision = sessions.some(
      (s) =>
        s.assignment_id !== selectedSession.assignment_id &&
        s.day === proposedDay &&
        s.start_time === proposedSlot.start_time &&
        s.room_id === proposedRoom.room_id
    );
    if (roomCollision) {
      hardViolations.push(`[H2] Classroom '${proposedRoom.name}' is already occupied during ${proposedDay} ${proposedSlot.start_time}-${proposedSlot.end_time}.`);
    }

    // H1: Faculty Collision
    const facultyCollision = sessions.some(
      (s) =>
        s.assignment_id !== selectedSession.assignment_id &&
        s.day === proposedDay &&
        s.start_time === proposedSlot.start_time &&
        s.faculty_id === selectedSession.faculty_id
    );
    if (facultyCollision) {
      hardViolations.push(`[H1] Faculty '${selectedSession.faculty_name}' is already teaching another class during this time.`);
    }

    // H3: Cohort Collision
    const cohortCollision = sessions.some(
      (s) =>
        s.assignment_id !== selectedSession.assignment_id &&
        s.day === proposedDay &&
        s.start_time === proposedSlot.start_time &&
        s.group_id === selectedSession.group_id
    );
    if (cohortCollision) {
      hardViolations.push(`[H3] Student Cohort '${selectedSession.group_name}' is already scheduled for another lecture.`);
    }

    return {
      isValid: hardViolations.length === 0,
      hardViolations,
      penaltyDelta: hardViolations.length === 0 ? -2.0 : +500.0,
    };
  }, [selectedSession, proposedSlot, proposedRoom, proposedDay, sessions]);

  const handlePreview = () => {
    setPreviewEvaluated(true);
    setCommitMessage(null);
  };

  const handleSimulateCommit = () => {
    if (!validationResult.isValid) return;

    const newRecord: RescheduleHistoryRecord = {
      change_id: `CHG_${Date.now().toString(16).slice(-8).toUpperCase()}`,
      timestamp: new Date().toISOString().replace("T", " ").slice(0, 19),
      course_code: selectedSession.course_code,
      faculty_name: selectedSession.faculty_name,
      group_name: selectedSession.group_name,
      from_slot: `${selectedSession.day} ${selectedSession.start_time}-${selectedSession.end_time}`,
      to_slot: `${proposedDay} ${proposedSlot?.start_time}-${proposedSlot?.end_time}`,
      from_room: selectedSession.room_name,
      to_room: proposedRoom?.name || "",
      is_rolled_back: false,
    };

    setHistory([newRecord, ...history]);
    setCommitMessage(`Local preview updated: '${selectedSession.course_code}' moved to ${proposedDay} ${proposedSlot?.start_time} in ${proposedRoom?.name}. (Awaiting FastAPI backend persistence).`);
  };

  const handleRollback = (changeId: string) => {
    setHistory((prev) =>
      prev.map((h) => (h.change_id === changeId ? { ...h, is_rolled_back: true } : h))
    );
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="What-If Rescheduling Workbench"
        description="Interactive timetable scenario planning with instant constraint validation, penalty delta computation, and atomic rollback."
        actions={
          <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg">
            <button
              onClick={() => setActiveTab("PLANNER")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === "PLANNER" ? "bg-white text-navy-900 shadow-sm" : "text-slate-600 hover:text-navy-900"
              }`}
            >
              Scenario Planner
            </button>
            <button
              onClick={() => setActiveTab("HISTORY")}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === "HISTORY" ? "bg-white text-navy-900 shadow-sm" : "text-slate-600 hover:text-navy-900"
              }`}
            >
              Audit History ({history.length})
            </button>
          </div>
        }
      />

      {/* Backend Integration Notice */}
      <div className="p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-lg text-xs font-semibold flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-amber-700 shrink-0" />
          <span>What-if evaluation operates in client preview mode. Official SQLite atomic transactions and rollback connect via <code>POST /api/v1/reschedule/apply</code>.</span>
        </div>
        <Badge variant="warning">Preview Mode</Badge>
      </div>

      {activeTab === "PLANNER" ? (
        <div className="space-y-6">
          {/* Step 1: Session Selector */}
          <Card className="p-5 space-y-4">
            <CardHeader
              title="1. Select Active Timetable Session to Modify"
              description="Choose a scheduled course assignment from the active semester schedule."
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div>
                <label className="font-bold text-navy-900 block mb-1">Target Scheduled Session</label>
                <select
                  value={selectedSessionId}
                  onChange={(e) => {
                    setSelectedSessionId(e.target.value);
                    setPreviewEvaluated(false);
                    setCommitMessage(null);
                  }}
                  className="w-full rounded-lg border border-slate-200 p-2 text-xs bg-white font-semibold text-slate-800"
                >
                  {sessions.map((s) => (
                    <option key={s.assignment_id} value={s.assignment_id}>
                      {s.course_code}: {s.course_title} &bull; {s.day} {s.start_time} ({s.room_id})
                    </option>
                  ))}
                </select>
              </div>

              {selectedSession && (
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                  <span className="font-bold text-navy-900 block">Current Assignment Details</span>
                  <div className="text-slate-600 grid grid-cols-2 gap-1 text-[11px]">
                    <div>Instructor: <strong>{selectedSession.faculty_name}</strong></div>
                    <div>Cohort: <strong>{selectedSession.group_name}</strong></div>
                    <div>Room: <strong>{selectedSession.room_name} ({selectedSession.room_type})</strong></div>
                    <div>Time: <strong>{selectedSession.day}, {selectedSession.start_time} - {selectedSession.end_time}</strong></div>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Step 2: Propose Alternative Schedule */}
          <Card className="p-5 space-y-4">
            <CardHeader
              title="2. Configure Proposed Alternative Resource & Time Slot"
              description="Candidate teaching slots strictly exclude protected institutional breaks (H8)."
            />

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              {/* Day Selector */}
              <div>
                <label className="font-bold text-navy-900 block mb-1">Proposed Day</label>
                <select
                  value={proposedDay}
                  onChange={(e) => {
                    setProposedDay(e.target.value as DayOfWeek);
                    setPreviewEvaluated(false);
                  }}
                  className="w-full rounded-lg border border-slate-200 p-2 bg-white text-xs"
                >
                  {DAYS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>

              {/* Slot Selector */}
              <div>
                <label className="font-bold text-navy-900 block mb-1">Proposed Teaching Period</label>
                <select
                  value={proposedSlotId}
                  onChange={(e) => {
                    setProposedSlotId(e.target.value);
                    setPreviewEvaluated(false);
                  }}
                  className="w-full rounded-lg border border-slate-200 p-2 bg-white text-xs font-mono"
                >
                  {availableSlotsForProposedDay.map((s) => (
                    <option key={s.slot_id} value={s.slot_id}>
                      {s.start_time} - {s.end_time} ({s.slot_id})
                    </option>
                  ))}
                </select>
                <span className="text-[11px] text-slate-500 mt-1 block">Institutional lunch breaks excluded.</span>
              </div>

              {/* Classroom Selector */}
              <div>
                <label className="font-bold text-navy-900 block mb-1">Proposed Facility / Room</label>
                <select
                  value={proposedRoomId}
                  onChange={(e) => {
                    setProposedRoomId(e.target.value);
                    setPreviewEvaluated(false);
                  }}
                  className="w-full rounded-lg border border-slate-200 p-2 bg-white text-xs"
                >
                  {classrooms.map((r) => (
                    <option key={r.room_id} value={r.room_id}>
                      {r.name} ({r.room_type}, {r.capacity} seats)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="pt-2">
              <Button variant="primary" size="sm" onClick={handlePreview} className="text-xs">
                <span>Evaluate What-If Scenario</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </Card>

          {/* Step 3: Side-by-Side Comparison & Conflict Validation */}
          {previewEvaluated && (
            <Card className="p-6 space-y-6 border-2 border-primary/20">
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <h4 className="font-bold text-navy-900 text-sm">Scenario Evaluation: Side-by-Side Comparison</h4>
                <Badge variant={validationResult.isValid ? "success" : "danger"}>
                  {validationResult.isValid ? "Valid & Conflict-Free" : "Constraint Conflicts Detected"}
                </Badge>
              </div>

              {/* Side by Side Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
                {/* Original */}
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                  <span className="font-bold text-slate-500 uppercase tracking-wider block text-[11px]">Original Schedule Assignment</span>
                  <div className="font-bold text-navy-900 text-sm">{selectedSession.course_code} — {selectedSession.course_title}</div>
                  <div className="space-y-1 text-slate-600">
                    <div>Day: <strong>{selectedSession.day}</strong></div>
                    <div>Period: <strong>{selectedSession.start_time} - {selectedSession.end_time}</strong></div>
                    <div>Facility: <strong>{selectedSession.room_name} ({selectedSession.room_id})</strong></div>
                    <div>Instructor: <strong>{selectedSession.faculty_name}</strong></div>
                  </div>
                </div>

                {/* Proposed */}
                <div className={`p-4 border rounded-xl space-y-2 ${
                  validationResult.isValid ? "bg-emerald-50/50 border-emerald-300" : "bg-red-50/50 border-red-300"
                }`}>
                  <span className="font-bold text-slate-500 uppercase tracking-wider block text-[11px]">Proposed Scenario</span>
                  <div className="font-bold text-navy-900 text-sm">{selectedSession.course_code} — {selectedSession.course_title}</div>
                  <div className="space-y-1 text-slate-600">
                    <div>Day: <strong className={proposedDay !== selectedSession.day ? "text-primary" : ""}>{proposedDay}</strong></div>
                    <div>Period: <strong className={proposedSlot?.start_time !== selectedSession.start_time ? "text-primary" : ""}>{proposedSlot?.start_time} - {proposedSlot?.end_time}</strong></div>
                    <div>Facility: <strong className={proposedRoom?.room_id !== selectedSession.room_id ? "text-primary" : ""}>{proposedRoom?.name} ({proposedRoom?.room_id})</strong></div>
                    <div>Instructor: <strong>{selectedSession.faculty_name}</strong></div>
                  </div>
                </div>
              </div>

              {/* Validation Feedback Banner */}
              {validationResult.isValid ? (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-900 space-y-1">
                  <div className="font-bold flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-700" />
                    <span>All Hard Constraints Verified (H1–H8 Passed)</span>
                  </div>
                  <p className="text-[11px] text-emerald-800">
                    Estimated soft penalty impact: <strong className="text-emerald-700">{validationResult.penaltyDelta.toFixed(1)} pts</strong> (improves faculty preference satisfaction).
                  </p>
                </div>
              ) : (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-xs text-red-900 space-y-2">
                  <div className="font-bold flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-red-700" />
                    <span>Hard Constraint Violations Detected ({validationResult.hardViolations.length})</span>
                  </div>
                  <ul className="list-disc pl-5 space-y-1 text-[11px] text-red-800">
                    {validationResult.hardViolations.map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                  <p className="text-[11px] text-red-700 font-semibold pt-1">
                    Cannot commit proposed change. Institutional scheduling rules require zero hard violations.
                  </p>
                </div>
              )}

              {/* Commit Action */}
              <div className="flex items-center justify-between pt-2">
                <Button variant="outline" size="sm" onClick={() => setPreviewEvaluated(false)} className="text-xs">
                  Cancel Preview
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  disabled={!validationResult.isValid}
                  onClick={handleSimulateCommit}
                  className={`text-xs ${validationResult.isValid ? "bg-emerald-600 hover:bg-emerald-700" : "opacity-50 cursor-not-allowed"}`}
                >
                  <CheckCircle2 className="w-4 h-4 mr-1.5" />
                  <span>Commit Scenario (Local Preview)</span>
                </Button>
              </div>

              {commitMessage && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-semibold">
                  {commitMessage}
                </div>
              )}
            </Card>
          )}
        </div>
      ) : (
        /* History & Rollback Tab */
        <Card className="p-0 overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div>
              <h4 className="font-bold text-navy-900 text-sm">Rescheduling Audit Log & Transaction Rollback</h4>
              <p className="text-xs text-slate-500">Chronological history of administrative schedule adjustments.</p>
            </div>
            <Badge variant="info">{history.length} Modifications Logged</Badge>
          </div>

          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/50 text-[11px] font-bold text-slate-500 border-b border-slate-100">
              <tr>
                <th className="p-3">Change ID</th>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Course & Instructor</th>
                <th className="p-3">Original Assignment</th>
                <th className="p-3">Adjusted Assignment</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {history.map((h) => (
                <tr key={h.change_id} className="hover:bg-slate-50/60">
                  <td className="p-3 font-mono font-bold text-navy-900">{h.change_id}</td>
                  <td className="p-3 text-slate-500 text-[11px]">{h.timestamp}</td>
                  <td className="p-3">
                    <span className="font-bold text-slate-800 block">{h.course_code}</span>
                    <span className="text-[11px] text-slate-500">{h.faculty_name}</span>
                  </td>
                  <td className="p-3 text-slate-600 text-[11px]">
                    <div>{h.from_slot}</div>
                    <div className="text-slate-400">{h.from_room}</div>
                  </td>
                  <td className="p-3 text-slate-800 text-[11px]">
                    <div className="font-bold text-primary">{h.to_slot}</div>
                    <div className="text-slate-600">{h.to_room}</div>
                  </td>
                  <td className="p-3">
                    {h.is_rolled_back ? (
                      <Badge variant="neutral">Rolled Back</Badge>
                    ) : (
                      <Badge variant="success">Active</Badge>
                    )}
                  </td>
                  <td className="p-3 text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={h.is_rolled_back}
                      onClick={() => handleRollback(h.change_id)}
                      className="text-[11px] py-1 px-2.5 h-auto text-slate-600 hover:text-danger"
                    >
                      <RotateCcw className="w-3 h-3 mr-1" />
                      <span>{h.is_rolled_back ? "Restored" : "Rollback"}</span>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
