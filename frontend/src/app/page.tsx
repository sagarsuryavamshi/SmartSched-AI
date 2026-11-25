"use client";

import React from "react";
import Link from "next/link";
import {
  Building2,
  Users,
  BookOpen,
  Clock,
  Sparkles,
  RefreshCw,
  Grid,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Cpu,
  Layers,
} from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { KpiCard } from "@/components/ui/KpiCard";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  MOCK_SYSTEM_SUMMARY,
  MOCK_COURSES,
  MOCK_ROOM_UTILIZATION,
} from "@/mock/data";

export default function DashboardPage() {
  const summary = MOCK_SYSTEM_SUMMARY;

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <PageHeader
        title="University Timetable Operations Dashboard"
        description="Constraint Satisfaction Problem (CSP) automated academic scheduling and metaheuristic optimization."
        actions={
          <div className="flex items-center gap-3">
            <Link href="/wizard">
              <Button variant="primary" size="md">
                <Sparkles className="w-4 h-4" />
                <span>Launch 10-Step Wizard</span>
              </Button>
            </Link>
          </div>
        }
      />

      {/* Top 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Classrooms & Labs"
          value={summary.classrooms}
          subtitle="Lecture halls & practical labs"
          icon={Building2}
          accent="blue"
        />
        <KpiCard
          title="Appointed Faculty"
          value={summary.faculty}
          subtitle="Active course instructors"
          icon={Users}
          accent="purple"
        />
        <KpiCard
          title="Academic Courses"
          value={summary.courses}
          subtitle="21 Theory + 3 Lab Sessions"
          icon={BookOpen}
          accent="green"
        />
        <KpiCard
          title="Weekly Timeslots"
          value={summary.timeslots}
          subtitle="Mon - Sat scheduling periods"
          icon={Clock}
          accent="amber"
        />
      </div>

      {/* Active Schedule Status Banner */}
      <Card className="bg-gradient-to-r from-blue-50/70 via-white to-purple-50/50 border-blue-200">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-primary text-white flex items-center justify-center shrink-0 shadow-sm">
              <CheckCircle2 className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-navy-900 text-base">Active Schedule Status: 100% Conflict-Free</h3>
                <Badge variant="success">FEASIBLE (0 Conflicts)</Badge>
              </div>
              <p className="text-xs text-slate-600 mt-0.5">
                Run ID: <span className="font-mono font-medium text-navy-800">{summary.active_run_id}</span> &bull; 
                Generated via: <span className="font-medium text-navy-800">{summary.solver_used}</span> &bull; 
                Soft Penalty: <span className="font-bold text-primary">{summary.soft_penalty_score}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link href="/timetable">
              <Button variant="outline" size="sm">
                <Grid className="w-3.5 h-3.5" />
                <span>View Grid</span>
              </Button>
            </Link>
            <Link href="/reschedule">
              <Button variant="secondary" size="sm">
                <RefreshCw className="w-3.5 h-3.5" />
                <span>What-If Reschedule</span>
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      {/* Two-Column Operations Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Curricular Resource Allocation */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader
              title="Curricular Allocation & Teaching Assignments"
              description="Current academic catalog with instructor and student cohort mapping."
              action={
                <Link href="/resources" className="text-xs text-primary font-semibold hover:underline flex items-center gap-1">
                  <span>Manage Catalog</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              }
            />

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider border-y border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Code</th>
                    <th className="py-2.5 px-3">Course Title</th>
                    <th className="py-2.5 px-3">Hours</th>
                    <th className="py-2.5 px-3">Type</th>
                    <th className="py-2.5 px-3">Assigned Faculty</th>
                    <th className="py-2.5 px-3">Cohort</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {MOCK_COURSES.map((c) => (
                    <tr key={c.code} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-bold text-navy-900">{c.code}</td>
                      <td className="py-2.5 px-3 font-medium text-slate-800">{c.title}</td>
                      <td className="py-2.5 px-3">{c.weekly_hours} hrs</td>
                      <td className="py-2.5 px-3">
                        <Badge variant={c.is_lab ? "purple" : "info"}>
                          {c.category}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-3 text-slate-600">{c.instructor_name}</td>
                      <td className="py-2.5 px-3 text-slate-600">{c.group_name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Classroom Utilization Metrics */}
          <Card>
            <CardHeader
              title="Classroom Space Utilization"
              description="Real-time occupancy rates across theoretical auditoriums and practical laboratories."
            />
            <div className="space-y-4 pt-1">
              {MOCK_ROOM_UTILIZATION.map((room) => (
                <div key={room.name} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-navy-900">{room.name} (Cap: {room.capacity})</span>
                    <span className="text-slate-600 font-semibold">{room.utilization}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${room.utilization}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: System Capabilities & Quick Links */}
        <div className="space-y-6">
          <Card className="border-navy-100 bg-white">
            <CardHeader
              title="Production Architecture"
              description="Phase 8 Next.js & FastAPI decoupled foundation."
            />
            <div className="space-y-3 text-xs text-slate-600">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>98 / 98 Passing Tests</strong> in underlying Python algorithm repository.</span>
              </div>
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>Dual Solvers:</strong> Exact Backtracking (MRV/LCV) & Genetic Algorithm metaheuristic.</span>
              </div>
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>Constraint Invariant:</strong> H1–H8 guaranteed zero hard violations.</span>
              </div>
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span><strong>What-If Engine:</strong> Continuous 2-hour lab selector with atomic rollback.</span>
              </div>
            </div>

            <div className="mt-5 pt-4 border-t border-slate-100">
              <Link href="/wizard">
                <Button variant="secondary" size="sm" className="w-full justify-between">
                  <span>Start Optimization Workflow</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          </Card>

          {/* Quick Nav Cards */}
          <div className="grid grid-cols-2 gap-3">
            <Link href="/solver" className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-primary/50 hover:shadow-sm transition-all group">
              <Cpu className="w-5 h-5 text-primary group-hover:scale-110 transition-transform mb-2" />
              <div className="text-xs font-bold text-navy-900">Backtracking</div>
              <div className="text-[10px] text-slate-500">Tree search & heuristics</div>
            </Link>
            <Link href="/genetic" className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-purple-300 hover:shadow-sm transition-all group">
              <Layers className="w-5 h-5 text-accent-purple group-hover:scale-110 transition-transform mb-2" />
              <div className="text-xs font-bold text-navy-900">Genetic Solver</div>
              <div className="text-[10px] text-slate-500">Multi-objective evolution</div>
            </Link>
            <Link href="/reschedule" className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-emerald-300 hover:shadow-sm transition-all group">
              <RefreshCw className="w-5 h-5 text-emerald-600 group-hover:scale-110 transition-transform mb-2" />
              <div className="text-xs font-bold text-navy-900">What-If Tool</div>
              <div className="text-[10px] text-slate-500">Continuous lab move</div>
            </Link>
            <Link href="/inspector" className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-amber-300 hover:shadow-sm transition-all group">
              <AlertTriangle className="w-5 h-5 text-amber-600 group-hover:scale-110 transition-transform mb-2" />
              <div className="text-xs font-bold text-navy-900">Inspector</div>
              <div className="text-[10px] text-slate-500">Diagnostics & audit</div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
