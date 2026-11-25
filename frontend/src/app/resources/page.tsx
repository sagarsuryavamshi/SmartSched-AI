"use client";

import React, { useState } from "react";
import { Building2, Users, BookOpen, Clock, Layers, RotateCcw } from "lucide-react";
import { useResources } from "@/context/ResourceContext";
import { PageHeader } from "@/components/ui/PageHeader";
import { KpiCard } from "@/components/ui/KpiCard";
import { Button } from "@/components/ui/Button";
import { ClassroomManagement } from "@/components/resources/ClassroomManagement";
import { FacultyManagement } from "@/components/resources/FacultyManagement";
import { StudentGroupManagement } from "@/components/resources/StudentGroupManagement";
import { CourseManagement } from "@/components/resources/CourseManagement";
import { TimeslotManagement } from "@/components/resources/TimeslotManagement";

type ResourceTab = "classrooms" | "faculty" | "groups" | "courses" | "timeslots";

export default function ResourcesPage() {
  const { classrooms, faculty, studentGroups, courses, timeslots, resetToDefault } = useResources();
  const [activeTab, setActiveTab] = useState<ResourceTab>("classrooms");

  const tabs = [
    { id: "classrooms", label: "Classrooms & Labs", icon: Building2, count: classrooms.length },
    { id: "faculty", label: "Faculty & Availability", icon: Users, count: faculty.length },
    { id: "groups", label: "Student Groups", icon: Layers, count: studentGroups.length },
    { id: "courses", label: "Courses & Curriculum", icon: BookOpen, count: courses.length },
    { id: "timeslots", label: "Timeslots & Breaks", icon: Clock, count: timeslots.length },
  ] as const;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Academic Resource Management"
        description="Comprehensive administration for classrooms, faculty teaching preferences, student cohorts, syllabus courses, and institutional timeslots."
        actions={
          <Button variant="outline" size="sm" onClick={resetToDefault} title="Reset session mock data to original baseline">
            <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
            <span>Reset Baseline Data</span>
          </Button>
        }
      />

      {/* Resource Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <KpiCard
          title="Classrooms"
          value={classrooms.length}
          subtitle={`${classrooms.filter((r) => r.room_type === "LAB").length} Specialized Labs`}
          icon={Building2}
          accent="blue"
        />
        <KpiCard
          title="Faculty Members"
          value={faculty.length}
          subtitle="Contract & availability active"
          icon={Users}
          accent="purple"
        />
        <KpiCard
          title="Student Groups"
          value={studentGroups.length}
          subtitle={`${studentGroups.reduce((acc, g) => acc + g.size, 0)} Total Students`}
          icon={Layers}
          accent="green"
        />
        <KpiCard
          title="Courses & Labs"
          value={courses.length}
          subtitle={`${courses.reduce((acc, c) => acc + c.weekly_hours, 0)} Total Weekly Hours`}
          icon={BookOpen}
          accent="amber"
        />
        <KpiCard
          title="Weekly Slots"
          value={timeslots.length}
          subtitle={`${timeslots.filter((s) => s.is_break).length} Lunch/Recess Breaks`}
          icon={Clock}
          accent="slate"
        />
      </div>

      {/* Module Navigation Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex items-center gap-2 overflow-x-auto pb-px">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as ResourceTab)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-t-lg border-b-2 transition-all whitespace-nowrap ${
                  isActive
                    ? "border-primary text-primary bg-white shadow-sm"
                    : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100/60"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-primary" : "text-slate-400"}`} />
                <span>{tab.label}</span>
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                    isActive ? "bg-primary-subtle text-primary" : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Panel Content */}
      <div className="pt-2">
        {activeTab === "classrooms" && <ClassroomManagement />}
        {activeTab === "faculty" && <FacultyManagement />}
        {activeTab === "groups" && <StudentGroupManagement />}
        {activeTab === "courses" && <CourseManagement />}
        {activeTab === "timeslots" && <TimeslotManagement />}
      </div>
    </div>
  );
}
