"use client";

import React, { useState } from "react";
import { Plus, Search, Edit2, Trash2, Clock, UserCheck, Users, X, ShieldAlert } from "lucide-react";
import { useResources } from "@/context/ResourceContext";
import { Course, RoomType } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function CourseManagement() {
  const { courses, faculty, studentGroups, addCourse, updateCourse, deleteCourse } = useResources();

  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [roomTypeFilter, setRoomTypeFilter] = useState("ALL");

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  // Form State
  const [formId, setFormId] = useState("");
  const [formCode, setFormCode] = useState("");
  const [formTitle, setFormTitle] = useState("");
  const [formWeeklyHours, setFormWeeklyHours] = useState(3);
  const [formRoomType, setFormRoomType] = useState<RoomType>("LECTURE_HALL");
  const [formCategory, setFormCategory] = useState<"Theory" | "Practical" | "Seminar">("Theory");
  const [formIsLab, setFormIsLab] = useState(false);
  const [formFacultyId, setFormFacultyId] = useState("");
  const [formGroupId, setFormGroupId] = useState("");

  const filteredCourses = courses.filter((c) => {
    const matchesSearch =
      c.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat = categoryFilter === "ALL" || (categoryFilter === "LAB" ? c.is_lab : !c.is_lab);
    const matchesRoom = roomTypeFilter === "ALL" || c.required_room_type === roomTypeFilter;
    return matchesSearch && matchesCat && matchesRoom;
  });

  const handleOpenAdd = () => {
    setEditingCourse(null);
    const randCode = `CS${Math.floor(100 + Math.random() * 800)}`;
    setFormId(`CRS_${randCode}`);
    setFormCode(randCode);
    setFormTitle("");
    setFormWeeklyHours(3);
    setFormRoomType("LECTURE_HALL");
    setFormCategory("Theory");
    setFormIsLab(false);
    setFormFacultyId(faculty[0]?.faculty_id || "");
    setFormGroupId(studentGroups[0]?.group_id || "");
    setErrorMessage("");
    setIsModalOpen(true);
  };

  const handleOpenEdit = (c: Course) => {
    setEditingCourse(c);
    setFormId(c.course_id);
    setFormCode(c.code);
    setFormTitle(c.title);
    setFormWeeklyHours(c.weekly_hours);
    setFormRoomType(c.required_room_type);
    setFormCategory(c.category);
    setFormIsLab(c.is_lab);
    setFormFacultyId(c.assigned_faculty_id || "");
    setFormGroupId(c.target_group_id || "");
    setErrorMessage("");
    setIsModalOpen(true);
  };

  const handleCategoryChange = (cat: "Theory" | "Practical" | "Seminar") => {
    setFormCategory(cat);
    if (cat === "Practical") {
      setFormIsLab(true);
      setFormRoomType("LAB");
      setFormWeeklyHours(2); // standard 2-hour continuous lab
    } else {
      setFormIsLab(false);
      setFormRoomType("LECTURE_HALL");
      setFormWeeklyHours(3);
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formCode.trim() || !formTitle.trim()) {
      setErrorMessage("Course code and title are required.");
      return;
    }
    if (formWeeklyHours <= 0 || formWeeklyHours > 6) {
      setErrorMessage("Weekly hours must be between 1 and 6.");
      return;
    }

    const payload: Course = {
      course_id: formId,
      code: formCode.trim().toUpperCase(),
      title: formTitle.trim(),
      weekly_hours: Number(formWeeklyHours),
      required_room_type: formRoomType,
      category: formCategory,
      is_lab: formIsLab,
      assigned_faculty_id: formFacultyId || undefined,
      target_group_id: formGroupId || undefined,
    };

    if (editingCourse) {
      updateCourse(payload);
    } else {
      const ok = addCourse(payload);
      if (!ok) {
        setErrorMessage(`Course with ID '${formId}' or Code '${formCode}' already exists.`);
        return;
      }
    }
    setIsModalOpen(false);
  };

  const confirmDelete = () => {
    if (deleteTargetId) {
      deleteCourse(deleteTargetId);
      setDeleteTargetId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          <div className="relative min-w-[220px] flex-1 sm:max-w-xs">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search course title or code..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="ALL">All Categories</option>
            <option value="THEORY">Theory Only</option>
            <option value="LAB">Practicals / Labs Only</option>
          </select>

          <select
            value={roomTypeFilter}
            onChange={(e) => setRoomTypeFilter(e.target.value)}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="ALL">All Required Rooms</option>
            <option value="LECTURE_HALL">Lecture Hall (H6)</option>
            <option value="LAB">Specialized Lab (H6)</option>
            <option value="SEMINAR_ROOM">Seminar Room</option>
          </select>
        </div>

        <Button variant="primary" size="sm" onClick={handleOpenAdd}>
          <Plus className="w-4 h-4" />
          <span>Add Course</span>
        </Button>
      </div>

      {/* Courses Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Code</th>
                <th className="py-3 px-4">Course Title</th>
                <th className="py-3 px-4">Weekly Sessions</th>
                <th className="py-3 px-4">Required Facility</th>
                <th className="py-3 px-4">Assigned Instructor</th>
                <th className="py-3 px-4">Enrolled Cohort</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredCourses.map((c) => {
                const assignedProf = faculty.find((f) => f.faculty_id === c.assigned_faculty_id);
                const assignedGroup = studentGroups.find((g) => g.group_id === c.target_group_id);

                return (
                  <tr key={c.course_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-navy-900">{c.code}</td>
                    <td className="py-3 px-4 font-bold text-slate-900">
                      <div>{c.title}</div>
                      <div className="text-[10px] text-slate-400 font-normal">ID: {c.course_id}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 font-semibold text-navy-900">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{c.weekly_hours} hrs/week</span>
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {c.is_lab ? "1 session × 2h continuous (H7)" : `${c.weekly_hours} sessions × 1h`}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant={c.is_lab ? "purple" : "info"}>
                        {c.required_room_type}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      {assignedProf ? (
                        <div className="text-slate-800 font-medium flex items-center gap-1">
                          <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
                          <span>{assignedProf.name}</span>
                        </div>
                      ) : (
                        <span className="text-amber-600 italic">Unassigned</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {assignedGroup ? (
                        <div className="text-slate-800 font-medium flex items-center gap-1">
                          <Users className="w-3.5 h-3.5 text-blue-600" />
                          <span>{assignedGroup.name}</span>
                        </div>
                      ) : (
                        <span className="text-slate-400">None</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleOpenEdit(c)}
                          className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-primary transition-colors"
                          title="Edit Course"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteTargetId(c.course_id)}
                          className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-danger transition-colors"
                          title="Delete Course"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add / Edit Course Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-navy-900 text-base">
                {editingCourse ? "Edit Course Syllabus" : "Add New Academic Course"}
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

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Course Code *</label>
                  <input
                    type="text"
                    placeholder="e.g. CS305"
                    value={formCode}
                    onChange={(e) => setFormCode(e.target.value.toUpperCase())}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 font-mono font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Course ID</label>
                  <input
                    type="text"
                    value={formId}
                    disabled
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 font-mono text-slate-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Course Title *</label>
                <input
                  type="text"
                  placeholder="e.g. Distributed Operating Systems"
                  value={formTitle}
                  onChange={(e) => setFormTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  required
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Category</label>
                  <select
                    value={formCategory}
                    onChange={(e) => handleCategoryChange(e.target.value as "Theory" | "Practical" | "Seminar")}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  >
                    <option value="Theory">Theory Lecture</option>
                    <option value="Practical">Practical Laboratory</option>
                    <option value="Seminar">Seminar Session</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Weekly Hours</label>
                  <input
                    type="number"
                    min={1}
                    max={6}
                    value={formWeeklyHours}
                    onChange={(e) => setFormWeeklyHours(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 font-bold"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Required Room Type</label>
                  <select
                    value={formRoomType}
                    onChange={(e) => setFormRoomType(e.target.value as RoomType)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  >
                    <option value="LECTURE_HALL">Lecture Hall</option>
                    <option value="LAB">Laboratory</option>
                    <option value="SEMINAR_ROOM">Seminar Room</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Assigned Faculty (H1 / H5)</label>
                  <select
                    value={formFacultyId}
                    onChange={(e) => setFormFacultyId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  >
                    <option value="">Unassigned</option>
                    {faculty.map((f) => (
                      <option key={f.faculty_id} value={f.faculty_id}>{f.name} ({f.faculty_id})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Target Cohort (H3 / H4)</label>
                  <select
                    value={formGroupId}
                    onChange={(e) => setFormGroupId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200"
                  >
                    <option value="">Unassigned</option>
                    {studentGroups.map((g) => (
                      <option key={g.group_id} value={g.group_id}>{g.name} ({g.size} std)</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button type="submit" variant="primary" size="sm">{editingCourse ? "Save Changes" : "Create Course"}</Button>
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
            <h3 className="font-bold text-navy-900 text-base mb-1">Delete Academic Course?</h3>
            <p className="text-xs text-slate-500 mb-4">
              Are you sure you want to delete course <span className="font-mono font-bold text-navy-900">{deleteTargetId}</span>? This removes it from future CSP formulations.
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
