"use client";

import React, { useState } from "react";
import { Plus, Search, Edit2, Trash2, Eye, Check, X, ShieldAlert } from "lucide-react";
import { useResources } from "@/context/ResourceContext";
import { Classroom, RoomType } from "@/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function ClassroomManagement() {
  const { classrooms, addClassroom, updateClassroom, deleteClassroom } = useResources();

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [minCapacityFilter, setMinCapacityFilter] = useState<number>(0);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRoom, setEditingRoom] = useState<Classroom | null>(null);
  const [viewingRoom, setViewingRoom] = useState<Classroom | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  // Form State
  const [formId, setFormId] = useState("");
  const [formName, setFormName] = useState("");
  const [formCapacity, setFormCapacity] = useState<number>(60);
  const [formType, setFormType] = useState<RoomType>("LECTURE_HALL");
  const [formBuilding, setFormBuilding] = useState("Academic Block A");
  const [formFeatures, setFormFeatures] = useState("");
  const [formError, setFormError] = useState("");

  const filteredClassrooms = classrooms.filter((r) => {
    const matchesSearch =
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.room_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.building?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === "ALL" || r.room_type === typeFilter;
    const matchesCap = r.capacity >= minCapacityFilter;
    return matchesSearch && matchesType && matchesCap;
  });

  const handleOpenAdd = () => {
    setEditingRoom(null);
    setFormId(`CR_${Math.random().toString(36).substring(2, 6).toUpperCase()}`);
    setFormName("");
    setFormCapacity(60);
    setFormType("LECTURE_HALL");
    setFormBuilding("Academic Block A");
    setFormFeatures("Projector, Whiteboard");
    setFormError("");
    setIsModalOpen(true);
  };

  const handleOpenEdit = (room: Classroom) => {
    setEditingRoom(room);
    setFormId(room.room_id);
    setFormName(room.name);
    setFormCapacity(room.capacity);
    setFormType(room.room_type);
    setFormBuilding(room.building || "Academic Block A");
    setFormFeatures(room.features || "");
    setFormError("");
    setIsModalOpen(true);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) {
      setFormError("Classroom name is required.");
      return;
    }
    if (formCapacity <= 0) {
      setFormError("Room capacity must be greater than 0.");
      return;
    }

    const payload: Classroom = {
      room_id: formId,
      name: formName.trim(),
      capacity: Number(formCapacity),
      room_type: formType,
      building: formBuilding.trim(),
      features: formFeatures.trim(),
      is_available: true,
    };

    if (editingRoom) {
      updateClassroom(payload);
    } else {
      const ok = addClassroom(payload);
      if (!ok) {
        setFormError(`Classroom ID '${formId}' already exists.`);
        return;
      }
    }
    setIsModalOpen(false);
  };

  const confirmDelete = () => {
    if (deleteTargetId) {
      deleteClassroom(deleteTargetId);
      setDeleteTargetId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Search Input */}
          <div className="relative min-w-[220px] flex-1 sm:max-w-xs">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search classrooms or buildings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>

          {/* Type Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="ALL">All Facility Types</option>
            <option value="LECTURE_HALL">Lecture Halls</option>
            <option value="LAB">Laboratories</option>
            <option value="SEMINAR_ROOM">Seminar Rooms</option>
          </select>

          {/* Capacity Filter */}
          <select
            value={minCapacityFilter}
            onChange={(e) => setMinCapacityFilter(Number(e.target.value))}
            className="text-xs py-1.5 px-3 rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value={0}>Any Capacity</option>
            <option value={40}>Min 40 Seats</option>
            <option value={60}>Min 60 Seats</option>
            <option value={80}>Min 80 Seats</option>
          </select>
        </div>

        <Button variant="primary" size="sm" onClick={handleOpenAdd}>
          <Plus className="w-4 h-4" />
          <span>Add Classroom</span>
        </Button>
      </div>

      {/* Classrooms Data Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Room ID</th>
                <th className="py-3 px-4">Classroom Name</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Seating Capacity</th>
                <th className="py-3 px-4">Building & Facilities</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredClassrooms.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No classrooms found matching search or filter criteria.
                  </td>
                </tr>
              ) : (
                filteredClassrooms.map((room) => (
                  <tr key={room.room_id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-navy-900">{room.room_id}</td>
                    <td className="py-3 px-4 font-medium text-slate-900">{room.name}</td>
                    <td className="py-3 px-4">
                      <Badge variant={room.room_type === "LAB" ? "purple" : room.room_type === "LECTURE_HALL" ? "info" : "neutral"}>
                        {room.room_type}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-navy-900">{room.capacity}</span>
                      <span className="text-slate-400 ml-1">students</span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-slate-800">{room.building || "Academic Block"}</div>
                      <div className="text-[11px] text-slate-400 truncate max-w-xs">{room.features || "Standard"}</div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                        <Check className="w-3 h-3" /> Available
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setViewingRoom(room)}
                          className="p-1.5 rounded-md hover:bg-slate-100 text-slate-500 hover:text-navy-900 transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleOpenEdit(room)}
                          className="p-1.5 rounded-md hover:bg-blue-50 text-slate-500 hover:text-primary transition-colors"
                          title="Edit Classroom"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteTargetId(room.room_id)}
                          className="p-1.5 rounded-md hover:bg-red-50 text-slate-500 hover:text-danger transition-colors"
                          title="Delete Classroom"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add / Edit Classroom Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-navy-900 text-base">
                {editingRoom ? "Edit Classroom Facility" : "Add New Classroom / Laboratory"}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="w-7 h-7 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-600 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSave} className="space-y-4 text-xs">
              {formError && (
                <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs">
                  {formError}
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Room Identifier (ID)</label>
                <input
                  type="text"
                  value={formId}
                  onChange={(e) => setFormId(e.target.value.toUpperCase())}
                  disabled={!!editingRoom}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 font-mono font-bold text-navy-900"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Facility Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Turing Lecture Auditorium"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/20"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Room Type *</label>
                  <select
                    value={formType}
                    onChange={(e) => setFormType(e.target.value as RoomType)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/20"
                  >
                    <option value="LECTURE_HALL">Lecture Hall</option>
                    <option value="LAB">Laboratory</option>
                    <option value="SEMINAR_ROOM">Seminar Room</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Seating Capacity *</label>
                  <input
                    type="number"
                    min={1}
                    max={500}
                    value={formCapacity}
                    onChange={(e) => setFormCapacity(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary/20"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Campus Building</label>
                <input
                  type="text"
                  value={formBuilding}
                  onChange={(e) => setFormBuilding(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Equipment & Features</label>
                <input
                  type="text"
                  placeholder="e.g. Projector, High-End GPUs, Sound System"
                  value={formFeatures}
                  onChange={(e) => setFormFeatures(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  {editingRoom ? "Save Changes" : "Create Classroom"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Details Modal */}
      {viewingRoom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-sm w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-navy-900 text-base">{viewingRoom.name}</h3>
              <button
                onClick={() => setViewingRoom(null)}
                className="w-7 h-7 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-600 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-3 text-xs text-slate-700">
              <div className="flex justify-between border-b pb-1.5"><span className="text-slate-400">Room Code:</span> <span className="font-mono font-bold">{viewingRoom.room_id}</span></div>
              <div className="flex justify-between border-b pb-1.5"><span className="text-slate-400">Type:</span> <Badge variant={viewingRoom.room_type === "LAB" ? "purple" : "info"}>{viewingRoom.room_type}</Badge></div>
              <div className="flex justify-between border-b pb-1.5"><span className="text-slate-400">Max Capacity:</span> <span className="font-bold">{viewingRoom.capacity} Students</span></div>
              <div className="flex justify-between border-b pb-1.5"><span className="text-slate-400">Location:</span> <span>{viewingRoom.building}</span></div>
              <div><span className="text-slate-400 block mb-1">Installed Equipment:</span> <p className="bg-slate-50 p-2 rounded text-slate-600">{viewingRoom.features || "Standard Classroom Setup"}</p></div>
            </div>
            <div className="pt-4 border-t border-slate-100 mt-4 flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => setViewingRoom(null)}>Close</Button>
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
            <h3 className="font-bold text-navy-900 text-base mb-1">Delete Classroom?</h3>
            <p className="text-xs text-slate-500 mb-4">
              Are you sure you want to delete classroom <span className="font-mono font-bold text-navy-900">{deleteTargetId}</span>? This action cannot be undone.
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
