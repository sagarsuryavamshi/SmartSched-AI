"use client";

import React, { useState } from "react";
import { Plus, Clock, Coffee, ShieldAlert, X, AlertTriangle, Calendar } from "lucide-react";
import { useResources } from "@/context/ResourceContext";
import { Timeslot, DayOfWeek } from "@/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const DAYS: DayOfWeek[] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export function TimeslotManagement() {
  const { timeslots, addTimeslot, updateTimeslot, deleteTimeslot, toggleTimeslotBreak } = useResources();

  const [selectedDay, setSelectedDay] = useState<DayOfWeek>("Monday");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSlot, setEditingSlot] = useState<Timeslot | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // Form State
  const [formId, setFormId] = useState("");
  const [formDay, setFormDay] = useState<DayOfWeek>("Monday");
  const [formStart, setFormStart] = useState("09:00");
  const [formEnd, setFormEnd] = useState("10:00");
  const [formIsBreak, setFormIsBreak] = useState(false);
  const [validationError, setValidationError] = useState("");

  const slotsForDay = timeslots
    .filter((s) => s.day === selectedDay)
    .sort((a, b) => a.start_time.localeCompare(b.start_time));

  const handleOpenAdd = () => {
    setEditingSlot(null);
    const nextIdx = timeslots.filter((s) => s.day === selectedDay).length + 1;
    setFormId(`TS_${selectedDay.substring(0, 3).toUpperCase()}_${nextIdx}`);
    setFormDay(selectedDay);
    setFormStart("15:00");
    setFormEnd("16:00");
    setFormIsBreak(false);
    setValidationError("");
    setIsModalOpen(true);
  };

  const handleOpenEdit = (s: Timeslot) => {
    setEditingSlot(s);
    setFormId(s.slot_id);
    setFormDay(s.day);
    setFormStart(s.start_time);
    setFormEnd(s.end_time);
    setFormIsBreak(s.is_break);
    setValidationError("");
    setIsModalOpen(true);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (formStart >= formEnd) {
      setValidationError("Start time must be strictly before end time.");
      return;
    }

    const payload: Timeslot = {
      slot_id: formId,
      day: formDay,
      start_time: formStart,
      end_time: formEnd,
      duration_minutes: 60,
      is_break: formIsBreak,
    };

    if (editingSlot) {
      const res = updateTimeslot(payload);
      if (!res.success) {
        setValidationError(res.message || "Failed to update slot.");
        return;
      }
    } else {
      const res = addTimeslot(payload);
      if (!res.success) {
        setValidationError(res.message || "Failed to add slot.");
        return;
      }
    }
    setIsModalOpen(false);
  };

  const confirmDelete = () => {
    if (deleteTargetId) {
      deleteTimeslot(deleteTargetId);
      setDeleteTargetId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Institutional Working Days & Control Header */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        {/* Day Selector Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {DAYS.map((d) => {
            const count = timeslots.filter((s) => s.day === d).length;
            const isSelected = d === selectedDay;
            return (
              <button
                key={d}
                onClick={() => setSelectedDay(d)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isSelected
                    ? "bg-navy-900 text-white shadow-sm"
                    : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                }`}
              >
                <span>{d}</span>
                <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${isSelected ? "bg-navy-800 text-slate-300" : "bg-slate-100 text-slate-600"}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <Button variant="primary" size="sm" onClick={handleOpenAdd}>
          <Plus className="w-4 h-4" />
          <span>Add Slot to {selectedDay}</span>
        </Button>
      </div>

      {/* Daily Timeslots Grid & Break Config */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <Card className="p-0 overflow-hidden">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-navy-900 text-sm">{selectedDay} Teaching Schedule Periods</h3>
                <p className="text-xs text-slate-500">Ordered chronological sequence with break flags for constraint H8.</p>
              </div>
              <Badge variant="info">{slotsForDay.length} Periods Configured</Badge>
            </div>

            <div className="divide-y divide-slate-100">
              {slotsForDay.map((slot, idx) => (
                <div
                  key={slot.slot_id}
                  className={`p-4 flex items-center justify-between text-xs transition-colors ${
                    slot.is_break ? "bg-amber-50/50" : "hover:bg-slate-50/80"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-lg bg-slate-100 font-mono font-bold text-slate-700 flex items-center justify-center shrink-0">
                      #{idx + 1}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-navy-900 text-sm">
                          {slot.start_time} - {slot.end_time}
                        </span>
                        <span className="font-mono text-[11px] text-slate-400">({slot.slot_id})</span>
                        {slot.is_break && (
                          <Badge variant="warning" className="gap-1">
                            <Coffee className="w-3 h-3" /> Institutional Break (H8)
                          </Badge>
                        )}
                      </div>
                      <div className="text-slate-500 text-[11px] mt-0.5">
                        Duration: 60 minutes &bull; Status: {slot.is_break ? "Protected recess (no sessions allowed)" : "Active teaching period"}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant={slot.is_break ? "outline" : "outline"}
                      size="sm"
                      onClick={() => toggleTimeslotBreak(slot.slot_id)}
                      className={`text-[11px] py-1 px-2.5 h-auto ${
                        slot.is_break ? "text-amber-800 border-amber-300 bg-amber-50 hover:bg-amber-100" : "text-slate-600"
                      }`}
                    >
                      <Coffee className="w-3.5 h-3.5 mr-1" />
                      <span>{slot.is_break ? "Unmark Break" : "Set as Break"}</span>
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleOpenEdit(slot)}
                      className="text-slate-500 hover:text-primary py-1 px-2 h-auto"
                    >
                      Edit
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeleteTargetId(slot.slot_id)}
                      className="text-slate-500 hover:text-danger py-1 px-2 h-auto"
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Weekly Timeslot Matrix Overview */}
        <Card className="space-y-4">
          <CardHeader
            title="Institutional Weekly Schedule Outline"
            description="High-level layout of periods across all working days."
          />
          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-blue-50/70 border border-blue-200 text-blue-900">
              <div className="font-bold flex items-center gap-1.5 mb-1">
                <Clock className="w-4 h-4 text-primary" />
                <span>Working Hours Invariant (H8)</span>
              </div>
              <p className="text-[11px] text-blue-800 leading-relaxed">
                Sessions can only be assigned to slots where <code className="font-mono bg-white px-1 py-0.5 rounded">is_break = 0</code>.
                Any session scheduled on an institutional recess triggers hard constraint rejection.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-purple-50/70 border border-purple-200 text-purple-900">
              <div className="font-bold flex items-center gap-1.5 mb-1">
                <Calendar className="w-4 h-4 text-accent-purple" />
                <span>Multi-Hour Lab Continuity (H7)</span>
              </div>
              <p className="text-[11px] text-purple-800 leading-relaxed">
                2-hour practical labs require consecutive slots on the same day without intermission.
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Add / Edit Timeslot Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-sm w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-navy-900 text-base">
                {editingSlot ? "Edit Timeslot" : `Add Period to ${formDay}`}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="w-7 h-7 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-600 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSave} className="space-y-4 text-xs">
              {validationError && (
                <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-1.5">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{validationError}</span>
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Timeslot ID</label>
                <input
                  type="text"
                  value={formId}
                  disabled={!!editingSlot}
                  onChange={(e) => setFormId(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 font-mono font-bold"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Day of Week</label>
                <select
                  value={formDay}
                  onChange={(e) => setFormDay(e.target.value as DayOfWeek)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200"
                >
                  {DAYS.map((d) => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Start Time (24h) *</label>
                  <input
                    type="time"
                    value={formStart}
                    onChange={(e) => setFormStart(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">End Time (24h) *</label>
                  <input
                    type="time"
                    value={formEnd}
                    onChange={(e) => setFormEnd(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                    required
                  />
                </div>
              </div>

              <div className="pt-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formIsBreak}
                    onChange={(e) => setFormIsBreak(e.target.checked)}
                    className="w-4 h-4 text-primary rounded border-slate-300"
                  />
                  <span className="font-semibold text-slate-700">Designate as Institutional Lunch / Recess Break (H8)</span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button type="submit" variant="primary" size="sm">{editingSlot ? "Save Changes" : "Create Timeslot"}</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTargetId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-sm w-full p-6 text-center animate-in fade-in zoom-in-95 duration-150">
            <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto mb-3">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-navy-900 text-base mb-1">Delete Timeslot Period?</h3>
            <p className="text-xs text-slate-500 mb-4">
              Are you sure you want to delete timeslot <span className="font-mono font-bold text-navy-900">{deleteTargetId}</span>?
            </p>
            <div className="flex items-center justify-center gap-3">
              <Button variant="outline" size="sm" onClick={() => setDeleteTargetId(null)}>Cancel</Button>
              <Button variant="danger" size="sm" onClick={confirmDelete}>Confirm Delete</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
