"use client";

import React, { useState } from "react";
import { Plus, Search, Edit2, Trash2, Calendar, Mail, X, ShieldAlert } from "lucide-react";
import { useResources } from "@/context/ResourceContext";
import { Faculty, DayOfWeek } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const DAYS: DayOfWeek[] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export function FacultyManagement() {
  const { faculty, timeslots, addFaculty, updateFaculty, deleteFaculty, toggleFacultySlotAvailability, toggleFacultySlotPreferred } = useResources();

  const [searchQuery, setSearchQuery] = useState("");
  const [deptFilter, setDeptFilter] = useState("ALL");

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFaculty, setEditingFaculty] = useState<Faculty | null>(null);
  const [availabilityFaculty, setAvailabilityFaculty] = useState<Faculty | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  // Form State
  const [formId, setFormId] = useState("");
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formDept, setFormDept] = useState("Computer Science");
  const [formMaxHours, setFormMaxHours] = useState(16);
  const [formSpecialization, setFormSpecialization] = useState("");

  const filteredFaculty = faculty.filter((f) => {
    const matchesSearch =
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.faculty_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDept = deptFilter === "ALL" || f.department === deptFilter;
    return matchesSearch && matchesDept;
  });

  const handleOpenAdd = () => {
    setEditingFaculty(null);
    setFormId(`FAC_${Math.random().toString(36).substring(2, 6).toUpperCase()}`);
    setFormName("");
    setFormEmail("");
    setFormDept("Computer Science");
    setFormMaxHours(16);
    setFormSpecialization("Algorithms & Systems");
    setErrorMessage("");
    setIsModalOpen(true);
  };

  const handleOpenEdit = (f: Faculty) => {
    setEditingFaculty(f);
    setFormId(f.faculty_id);
    setFormName(f.name);
    setFormEmail(f.email);
    setFormDept(f.department);
    setFormMaxHours(f.max_weekly_hours);
    setFormSpecialization(f.specialization || "");
    setErrorMessage("");
    setIsModalOpen(true);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim() || !formEmail.trim()) {
      setErrorMessage("Name and email are required.");
      return;
    }

    const payload: Faculty = {
      faculty_id: formId,
      name: formName.trim(),
      email: formEmail.trim(),
      department: formDept,
      max_weekly_hours: Number(formMaxHours),
      available_days: editingFaculty ? editingFaculty.available_days : ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      qualified_courses: editingFaculty ? editingFaculty.qualified_courses : [],
      unavailable_slots: editingFaculty ? editingFaculty.unavailable_slots : [],
      preferred_slots: editingFaculty ? editingFaculty.preferred_slots : [],
      specialization: formSpecialization.trim(),
    };

    if (editingFaculty) {
      updateFaculty(payload);
    } else {
      const ok = addFaculty(payload);
      if (!ok) {
        setErrorMessage(`Faculty ID '${formId}' already exists.`);
        return;
      }
    }
    setIsModalOpen(false);
  };

  const confirmDelete = () => {
    if (deleteTargetId) {
      const res = deleteFaculty(deleteTargetId);
      if (!res.success) {
        alert(res.message);
      }
      setDeleteTargetId(null);
    }
  };

  // Unique departments for filter
  const departments = Array.from(new Set(faculty.map((f) => f.department)));

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          <div className="relative min-w-[220px] flex-1 sm:max-w-xs">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search faculty by name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <select
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="ALL">All Departments</option>
            {departments.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <Button variant="primary" size="sm" onClick={handleOpenAdd}>
          <Plus className="w-4 h-4" />
          <span>Appoint Faculty</span>
        </Button>
      </div>

      {/* Faculty Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Faculty ID</th>
                <th className="py-3 px-4">Instructor Name</th>
                <th className="py-3 px-4">Department & Specialization</th>
                <th className="py-3 px-4">Max Workload</th>
                <th className="py-3 px-4">Contract Days</th>
                <th className="py-3 px-4 text-center">Availability Grid</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredFaculty.map((f) => (
                <tr key={f.faculty_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-navy-900">{f.faculty_id}</td>
                  <td className="py-3 px-4">
                    <div className="font-bold text-navy-900">{f.name}</div>
                    <div className="text-slate-400 text-[11px] flex items-center gap-1">
                      <Mail className="w-3 h-3" /> {f.email}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="text-slate-800 font-medium">{f.department}</div>
                    <div className="text-[11px] text-slate-400">{f.specialization || "General"}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-bold text-primary">{f.max_weekly_hours} hrs</span>
                    <span className="text-slate-400 text-[11px]"> / week</span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1">
                      {f.available_days.map((d) => (
                        <span key={d} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 font-medium">
                          {d.substring(0, 3)}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setAvailabilityFaculty(f)}
                      className="text-[11px] py-1 px-2.5 h-auto text-primary border-primary/30 hover:bg-primary/5"
                    >
                      <Calendar className="w-3.5 h-3.5 mr-1 text-primary" />
                      <span>Configure Grid</span>
                    </Button>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => handleOpenEdit(f)}
                        className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-primary transition-colors"
                        title="Edit Faculty"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setDeleteTargetId(f.faculty_id)}
                        className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-danger transition-colors"
                        title="Delete Faculty"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add / Edit Faculty Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-navy-900 text-base">
                {editingFaculty ? "Edit Faculty Member" : "Appoint New Faculty Instructor"}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="w-7 h-7 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-600 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSave} className="space-y-4 text-xs">
              {errorMessage && (
                <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-red-700">
                  {errorMessage}
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Faculty ID</label>
                <input
                  type="text"
                  value={formId}
                  onChange={(e) => setFormId(e.target.value.toUpperCase())}
                  disabled={!!editingFaculty}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 font-mono font-bold text-navy-900"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Full Name & Title *</label>
                <input
                  type="text"
                  placeholder="e.g. Prof. Alan Turing"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Institutional Email *</label>
                <input
                  type="email"
                  placeholder="a.turing@university.edu"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Department</label>
                  <select
                    value={formDept}
                    onChange={(e) => setFormDept(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  >
                    <option value="Computer Science">Computer Science</option>
                    <option value="Artificial Intelligence">Artificial Intelligence</option>
                    <option value="Information Technology">Information Technology</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Max Weekly Hours</label>
                  <input
                    type="number"
                    min={4}
                    max={30}
                    value={formMaxHours}
                    onChange={(e) => setFormMaxHours(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Academic Specialization</label>
                <input
                  type="text"
                  placeholder="e.g. Machine Learning, Distributed Algorithms"
                  value={formSpecialization}
                  onChange={(e) => setFormSpecialization(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button type="submit" variant="primary" size="sm">{editingFaculty ? "Save Changes" : "Appoint Faculty"}</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Weekly Availability Grid Modal */}
      {availabilityFaculty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-2xl w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div>
                <h3 className="font-bold text-navy-900 text-base">Weekly Timeslot Availability Matrix</h3>
                <p className="text-xs text-slate-500">Instructor: <span className="font-bold text-navy-900">{availabilityFaculty.name}</span> ({availabilityFaculty.faculty_id})</p>
              </div>
              <button
                onClick={() => setAvailabilityFaculty(null)}
                className="w-7 h-7 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-600 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Availability Legend */}
            <div className="flex items-center gap-4 text-xs pb-3 border-b border-slate-100 mb-4">
              <span className="font-semibold text-slate-700">Legend:</span>
              <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-500" /> Available (Default)</span>
              <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-amber-400" /> S1 Preferred Slot</span>
              <span className="inline-flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-red-500" /> H5 Unavailable</span>
            </div>

            {/* Interactive Grid */}
            <div className="overflow-x-auto">
              <table className="w-full text-center text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 font-semibold uppercase">
                    <th className="p-2 border text-left">Period / Day</th>
                    {DAYS.map((d) => (
                      <th key={d} className="p-2 border">{d.substring(0, 3)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[1, 2, 3, 4, 5].map((periodIdx) => {
                    const sampleSlot = timeslots.find((s) => s.slot_id.endsWith(`_${periodIdx}`));
                    const timeRange = sampleSlot ? `${sampleSlot.start_time}-${sampleSlot.end_time}` : `Slot ${periodIdx}`;
                    const isBreak = sampleSlot?.is_break;

                    return (
                      <tr key={periodIdx} className={isBreak ? "bg-slate-50/80" : ""}>
                        <td className="p-2 border text-left font-mono font-medium text-slate-700">
                          {timeRange}
                          {isBreak && <span className="text-[10px] text-amber-600 block">(Lunch Break)</span>}
                        </td>
                        {DAYS.map((day) => {
                          const slotId = `TS_${day.substring(0, 3).toUpperCase()}_${periodIdx}`;
                          const isUnavail = availabilityFaculty.unavailable_slots.includes(slotId) || !availabilityFaculty.available_days.includes(day);
                          const isPreferred = availabilityFaculty.preferred_slots?.includes(slotId);

                          return (
                            <td key={slotId} className="p-2 border">
                              {isBreak ? (
                                <span className="text-slate-300 text-[10px]">—</span>
                              ) : (
                                <div className="flex items-center justify-center gap-1">
                                  <button
                                    onClick={() => toggleFacultySlotAvailability(availabilityFaculty.faculty_id, slotId)}
                                    className={`px-2 py-1 rounded text-[11px] font-bold transition-all ${
                                      isUnavail
                                        ? "bg-red-100 text-red-700 hover:bg-red-200 border border-red-200"
                                        : isPreferred
                                        ? "bg-amber-100 text-amber-800 hover:bg-amber-200 border border-amber-300"
                                        : "bg-emerald-100 text-emerald-800 hover:bg-emerald-200 border border-emerald-300"
                                    }`}
                                    title="Click to toggle Available vs Unavailable"
                                  >
                                    {isUnavail ? "H5 Unavail" : isPreferred ? "★ Preferred" : "Available"}
                                  </button>
                                  {!isUnavail && (
                                    <button
                                      onClick={() => toggleFacultySlotPreferred(availabilityFaculty.faculty_id, slotId)}
                                      className={`p-1 rounded text-[10px] ${
                                        isPreferred ? "text-amber-600 bg-amber-50" : "text-slate-400 hover:text-amber-500"
                                      }`}
                                      title="Toggle Soft Preference (S1)"
                                    >
                                      ★
                                    </button>
                                  )}
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

            <div className="pt-4 border-t border-slate-100 mt-4 flex items-center justify-between">
              <span className="text-xs text-slate-500">Changes persist in local application session state.</span>
              <Button variant="secondary" size="sm" onClick={() => setAvailabilityFaculty(null)}>Done</Button>
            </div>
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
            <h3 className="font-bold text-navy-900 text-base mb-1">Remove Faculty Member?</h3>
            <p className="text-xs text-slate-500 mb-4">
              Are you sure you want to remove <span className="font-mono font-bold text-navy-900">{deleteTargetId}</span>? Relational locks protect against deleting faculty with assigned teaching duties.
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
