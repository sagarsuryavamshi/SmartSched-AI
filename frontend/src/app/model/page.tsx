"use client";

import React from "react";
import Link from "next/link";
import {
  Cpu,
  Dna,
  Scale,
  Sliders,
  Play,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Award,
  Info,
} from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { KpiCard } from "@/components/ui/KpiCard";
import { useResources } from "@/context/ResourceContext";

export default function OptimizationLandingPage() {
  const { courses, classrooms, faculty, studentGroups, timeslots } = useResources();

  const discreteVariablesCount = courses.reduce((acc, c) => acc + (c.is_lab ? 1 : c.weekly_hours), 0);
  const activeTeachingSlots = timeslots.filter((s) => !s.is_break);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Optimization Engine Control Centre"
        description="Unified administration and execution portal for exact Constraint Satisfaction (CSP) and multi-objective Genetic Algorithm (GA) solvers."
      />

      {/* Resource Formulation Readiness Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiCard
          title="Variables to Schedule"
          value={discreteVariablesCount}
          subtitle="Discrete course hours"
          icon={Cpu}
          accent="blue"
        />
        <KpiCard
          title="Teaching Slots"
          value={activeTeachingSlots.length}
          subtitle={`${timeslots.filter((s) => s.is_break).length} Breaks Excluded (H8)`}
          icon={Clock}
          accent="purple"
        />
        <KpiCard
          title="Classrooms & Labs"
          value={classrooms.length}
          subtitle={`${classrooms.filter((r) => r.room_type === "LAB").length} Specialized Labs`}
          icon={Sliders}
          accent="green"
        />
        <KpiCard
          title="Student Cohorts"
          value={studentGroups.length}
          subtitle={`${faculty.length} Appointed Faculty`}
          icon={ShieldCheck}
          accent="amber"
        />
      </div>

      {/* Optimization Engines Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card 1: Backtracking CSP Solver */}
        <Card className="p-6 flex flex-col justify-between space-y-4 hover:border-primary transition-all">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-blue-100 text-primary flex items-center justify-center">
                <Cpu className="w-6 h-6" />
              </div>
              <Badge variant="info">Systematic Search</Badge>
            </div>
            <h3 className="font-bold text-navy-900 text-base">Backtracking CSP Solver</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Exact depth-first search tree exploration using MRV, Degree Heuristic, LCV, Forward Checking, and AC-3 Arc Consistency.
            </p>
            <ul className="text-[11px] text-slate-600 space-y-1.5 pt-2 border-t border-slate-100">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Deterministic first-feasible solution discovery</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Mathematical proof of feasibility/infeasibility</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Fast execution (~0.08s on baseline dataset)</span>
              </li>
            </ul>
          </div>
          <Link href="/solver" className="pt-2">
            <Button variant="primary" className="w-full text-xs justify-between">
              <span>Launch CSP Engine</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </Card>

        {/* Card 2: Genetic Algorithm Engine */}
        <Card className="p-6 flex flex-col justify-between space-y-4 hover:border-accent-purple transition-all">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-purple-100 text-accent-purple flex items-center justify-center">
                <Dna className="w-6 h-6" />
              </div>
              <Badge variant="purple">Metaheuristic</Badge>
            </div>
            <h3 className="font-bold text-navy-900 text-base">Genetic Algorithm Optimizer</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Population-based multi-objective evolutionary search prioritizing human satisfaction (S1–S4) while guaranteeing 100% hard feasibility.
            </p>
            <ul className="text-[11px] text-slate-600 space-y-1.5 pt-2 border-t border-slate-100">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>High faculty & student preference satisfaction</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Domain-guided chromosome repair operator</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Soft penalty minimization (Mean: 13.5)</span>
              </li>
            </ul>
          </div>
          <Link href="/genetic" className="pt-2">
            <Button variant="primary" className="w-full text-xs justify-between bg-accent-purple hover:bg-purple-700">
              <span>Launch GA Engine</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </Card>

        {/* Card 3: Comparative Benchmarking */}
        <Card className="p-6 flex flex-col justify-between space-y-4 hover:border-emerald-500 transition-all">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                <Scale className="w-6 h-6" />
              </div>
              <Badge variant="success">Scientific Audit</Badge>
            </div>
            <h3 className="font-bold text-navy-900 text-base">Algorithm Benchmarking</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Scientific side-by-side empirical performance evaluations across runtimes, search effort, soft penalties, and multi-seed stability.
            </p>
            <ul className="text-[11px] text-slate-600 space-y-1.5 pt-2 border-t border-slate-100">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Side-by-side bar charts and comparison tables</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>10-seed empirical stability evaluation</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Equal problem instance constraint grounding</span>
              </li>
            </ul>
          </div>
          <Link href="/analytics/benchmark" className="pt-2">
            <Button variant="primary" className="w-full text-xs justify-between bg-emerald-600 hover:bg-emerald-700">
              <span>Launch Benchmarking</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </Card>
      </div>

      {/* Architectural Decoupling Notice */}
      <Card className="p-5 bg-slate-50 border border-slate-200">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-primary shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <span className="font-bold text-navy-900 block">Production API Service Architecture</span>
            <p className="text-slate-600 leading-relaxed">
              The Next.js optimization interfaces are fully decoupled and communicate via strongly-typed contracts defined in <code>src/types/solver.ts</code>.
              When the FastAPI backend is launched, endpoints <code>/api/v1/optimize/csp/solve-backtracking</code>, <code>/api/v1/optimize/ga/solve</code>,
              and <code>/api/v1/optimize/benchmark</code> will execute the Python algorithms asynchronously.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
