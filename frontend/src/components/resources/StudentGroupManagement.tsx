"use client";

import React, { useState } from "react";
import { Plus, Search, Edit2, Trash2, X, ShieldAlert } from "lucide-react";
import { useResources } from "@/context/ResourceContext";
import { StudentGroup } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function StudentGroupManagement() {
  const { studentGroups, addStudentGroup, updateStudentGroup, deleteStudentGroup } = useResources();

  const [searchQuery, setSearchQuery] = useState("");
  const [deptFilter, setDeptFilter] = useState("ALL");
  const [semFilter, setSemFilter] = useState<number>(0);

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<StudentGroup | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  // Form State
  const [formId, setFormId] = useState("");
  const [formName, setFormName] = useState("");
  const [formDept, setFormDept] = useState("Computer Science");
  const [formSize, setFormSize] = useState(50);
  const [formProgram, setFormProgram] = useState("B.Tech Computer Science");
  const [formSemester, setFormSemester] = useState(4);

  const filteredGroups = studentGroups.filter((g) => {
    const matchesSearch =
      g.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.group_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.program.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDept = deptFilter === "ALL" || g.department === deptFilter;
    const matchesSem = semFilter === 0 || g.semester === semFilter;
    return matchesSearch && matchesDept && matchesSem;
  });

  const handleOpenAdd = () => {
    setEditingGroup(null);
    setFormId(`GRP_${Math.random().toString(36).substring(2, 6).toUpperCase()}`);
    setFormName("");
    setFormDept("Computer Science");
    setFormSize(50);
    setFormProgram("B.Tech Computer Science");
    setFormSemester(4);
    setErrorMessage("");
    setIsModalOpen(true);
  };

  const handleOpenEdit = (g: StudentGroup) => {
    setEditingGroup(g);
    setFormId(g.group_id);
    setFormName(g.name);
    setFormDept(g.department);
    setFormSize(g.size);
    setFormProgram(g.program);
    setFormSemester(g.semester);
    setErrorMessage("");
    setIsModalOpen(true);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) {
      setErrorMessage("Group name is required.");
      return;
    }
    if (formSize <= 0) {
      setErrorMessage("Cohort student count must be greater than 0.");
      return;
    }

    const payload: StudentGroup = {
      group_id: formId,
      name: formName.trim(),
      department: formDept,
      size: Number(formSize),
      program: formProgram.trim(),
      semester: Number(formSemester),
    };

    if (editingGroup) {
      updateStudentGroup(payload);
    } else {
      const ok = addStudentGroup(payload);
      if (!ok) {
        setErrorMessage(`Student group ID '${formId}' already exists.`);
        return;
      }
    }
    setIsModalOpen(false);
  };

  const confirmDelete = () => {
    if (deleteTargetId) {
      const res = deleteStudentGroup(deleteTargetId);
      if (!res.success) {
        alert(res.message);
      }
      setDeleteTargetId(null);
    }
  };

  const departments = Array.from(new Set(studentGroups.map((g) => g.department)));

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          <div className="relative min-w-[220px] flex-1 sm:max-w-xs">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search cohorts, programs or IDs..."
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

          <select
            value={semFilter}
            onChange={(e) => setSemFilter(Number(e.target.value))}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value={0}>All Semesters</option>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
              <option key={s} value={s}>Semester {s}</option>
            ))}
          </select>
        </div>

        <Button variant="primary" size="sm" onClick={handleOpenAdd}>
          <Plus className="w-4 h-4" />
          <span>Add Student Group</span>
        </Button>
      </div>

      {/* Student Groups Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Group ID</th>
                <th className="py-3 px-4">Cohort Name</th>
                <th className="py-3 px-4">Academic Program</th>
                <th className="py-3 px-4">Semester</th>
                <th className="py-3 px-4">Enrolled Students</th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredGroups.map((g) => (
                <tr key={g.group_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-navy-900">{g.group_id}</td>
                  <td className="py-3 px-4 font-bold text-slate-900">{g.name}</td>
                  <td className="py-3 px-4 text-slate-700">{g.program}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                      Semester {g.semester}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-bold text-navy-900">{g.size}</span>
                    <span className="text-slate-400 ml-1">students (H4 capacity check)</span>
                  </td>
                  <td className="py-3 px-4 text-slate-600">{g.department}</td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => handleOpenEdit(g)}
                        className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-primary transition-colors"
                        title="Edit Student Group"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setDeleteTargetId(g.group_id)}
                        className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-danger transition-colors"
                        title="Delete Student Group"
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

      {/* Add / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-navy-900 text-base">
                {editingGroup ? "Edit Student Cohort" : "Register New Student Group"}
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
                <label className="block font-semibold text-slate-700 mb-1">Group ID</label>
                <input
                  type="text"
                  value={formId}
                  onChange={(e) => setFormId(e.target.value.toUpperCase())}
                  disabled={!!editingGroup}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 font-mono font-bold text-navy-900"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Cohort Display Name *</label>
                <input
                  type="text"
                  placeholder="e.g. CS Batch 2024 (Semester 4)"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Degree Program</label>
                <input
                  type="text"
                  placeholder="e.g. B.Tech Computer Science"
                  value={formProgram}
                  onChange={(e) => setFormProgram(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Student Enrollment Count *</label>
                  <input
                    type="number"
                    min={1}
                    max={250}
                    value={formSize}
                    onChange={(e) => setFormSize(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Current Semester</label>
                  <select
                    value={formSemester}
                    onChange={(e) => setFormSemester(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  >
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                      <option key={s} value={s}>Semester {s}</option>
                    ))}
                  </select>
                </div>
              </div>

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

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button type="submit" variant="primary" size="sm">{editingGroup ? "Save Changes" : "Register Group"}</Button>
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
            <h3 className="font-bold text-navy-900 text-base mb-1">Delete Student Group?</h3>
            <p className="text-xs text-slate-500 mb-4">
              Are you sure you want to delete cohort <span className="font-mono font-bold text-navy-900">{deleteTargetId}</span>? Relational locks protect against deleting cohorts tied to active courses.
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
