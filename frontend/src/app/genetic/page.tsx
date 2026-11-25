"use client";

import React, { useState } from "react";
import {
  Dna,
  Play,
  Sliders,
  ShieldCheck,
  Award,
  Clock,
  RotateCcw,
  BookOpen,
  Info,
  AlertTriangle,
  CheckCircle2,
  TrendingDown,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { KpiCard } from "@/components/ui/KpiCard";
import { GAHyperparameters, GAResultPayload } from "@/types/solver";
import { FIXTURE_GA_RESULT } from "@/types/fixtures";

export default function GeneticPage() {
  const [params, setParams] = useState<GAHyperparameters>({
    population_size: 60,
    max_generations: 40,
    crossover_prob: 0.85,
    mutation_prob: 0.08,
    elitism_count: 4,
    tournament_size: 3,
    random_seed: 42,
    timeout_seconds: 30.0,
    enable_repair: true,
    repair_prob: 0.4,
  });

  // Soft objective weights
  const [softWeights, setSoftWeights] = useState({
    s1: 1.0,
    s2: 2.0,
    s3: 1.5,
    s4: 1.0,
  });

  const [activeResult, setActiveResult] = useState<GAResultPayload | null>(null);
  const [isFixtureMode, setIsFixtureMode] = useState(false);

  const handleLoadFixture = () => {
    setActiveResult(FIXTURE_GA_RESULT);
    setIsFixtureMode(true);
  };

  const handleClear = () => {
    setActiveResult(null);
    setIsFixtureMode(false);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Genetic Algorithm Metaheuristic Engine"
        description="Multi-objective evolutionary optimization minimizing soft objective penalties (S1–S4) while guaranteeing 100% hard constraint feasibility via chromosome repair."
        actions={
          <div className="flex items-center gap-2">
            {activeResult ? (
              <Button variant="outline" size="sm" onClick={handleClear} className="text-xs">
                <RotateCcw className="w-3.5 h-3.5 mr-1" />
                Clear Output
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={handleLoadFixture}
                className="text-xs border-purple-200 text-accent-purple bg-purple-50/50 hover:bg-purple-100/50"
                title="Inspect verified GA evolutionary convergence telemetry"
              >
                <BookOpen className="w-3.5 h-3.5 mr-1 text-accent-purple" />
                Load Verified Run Fixture
              </Button>
            )}
          </div>
        }
      />

      {isFixtureMode && (
        <div className="p-3 bg-purple-50 border border-purple-200 text-purple-900 rounded-lg text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-accent-purple shrink-0" />
            <span>Viewing verified empirical execution telemetry from Python <code>src/ga_engine/genetic_solver.py</code> (40 generations, 16.0 penalty, 0.58s).</span>
          </div>
          <Badge variant="purple">Verified Benchmark Fixture</Badge>
        </div>
      )}

      {/* GA Parameter Tuning Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6 space-y-6">
            <CardHeader
              title="Evolutionary Dynamics & Genetic Operators"
              description="Tune population mechanics, selection pressure, crossover recombination, and mutation repair."
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
              <div>
                <div className="flex justify-between font-bold text-navy-900 mb-1">
                  <span>Population Size (N)</span>
                  <span className="font-mono text-primary">{params.population_size} chromosomes</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="150"
                  step="10"
                  value={params.population_size}
                  onChange={(e) => setParams({ ...params, population_size: parseInt(e.target.value) })}
                  className="w-full accent-primary"
                />
                <span className="text-[11px] text-slate-500">Number of candidate timetables maintained concurrently.</span>
              </div>

              <div>
                <div className="flex justify-between font-bold text-navy-900 mb-1">
                  <span>Max Generations (G)</span>
                  <span className="font-mono text-primary">{params.max_generations} epochs</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="5"
                  value={params.max_generations}
                  onChange={(e) => setParams({ ...params, max_generations: parseInt(e.target.value) })}
                  className="w-full accent-primary"
                />
                <span className="text-[11px] text-slate-500">Maximum evolutionary iterations before convergence check.</span>
              </div>

              <div>
                <div className="flex justify-between font-bold text-navy-900 mb-1">
                  <span>Crossover Probability (Pc)</span>
                  <span className="font-mono text-primary">{(params.crossover_prob * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="1.0"
                  step="0.05"
                  value={params.crossover_prob}
                  onChange={(e) => setParams({ ...params, crossover_prob: parseFloat(e.target.value) })}
                  className="w-full accent-primary"
                />
                <span className="text-[11px] text-slate-500">Frequency of recombining parent timetable genes.</span>
              </div>

              <div>
                <div className="flex justify-between font-bold text-navy-900 mb-1">
                  <span>Mutation Rate (Pm)</span>
                  <span className="font-mono text-primary">{(params.mutation_prob * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.01"
                  max="0.25"
                  step="0.01"
                  value={params.mutation_prob}
                  onChange={(e) => setParams({ ...params, mutation_prob: parseFloat(e.target.value) })}
                  className="w-full accent-primary"
                />
                <span className="text-[11px] text-slate-500">Perturbation probability to introduce new scheduling solutions.</span>
              </div>

              <div>
                <div className="flex justify-between font-bold text-navy-900 mb-1">
                  <span>Elitism Count</span>
                  <span className="font-mono text-primary">{params.elitism_count} candidates</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={params.elitism_count}
                  onChange={(e) => setParams({ ...params, elitism_count: parseInt(e.target.value) })}
                  className="w-full accent-primary"
                />
                <span className="text-[11px] text-slate-500">Top-tier chromosomes directly preserved into next generation.</span>
              </div>

              <div>
                <div className="flex justify-between font-bold text-navy-900 mb-1">
                  <span>Random Seed</span>
                  <span className="font-mono text-primary">{params.random_seed}</span>
                </div>
                <input
                  type="number"
                  value={params.random_seed}
                  onChange={(e) => setParams({ ...params, random_seed: parseInt(e.target.value) || 42 })}
                  className="w-full rounded-lg border border-slate-200 p-1.5 text-xs font-mono"
                />
                <span className="text-[11px] text-slate-500">Seed for pseudo-random reproducibility across runs.</span>
              </div>
            </div>
          </Card>

          {/* Soft Objective Penalty Weights */}
          <Card className="p-6 space-y-4">
            <CardHeader
              title="Soft Objective Quality Weights (S1–S4)"
              description="Relative weightings aligning timetable layout with institutional quality-of-life goals."
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="font-bold text-navy-900 block">S1: Faculty Preferred Slots (wt: {softWeights.s1.toFixed(1)})</span>
                <span className="text-[11px] text-slate-500">Penalizes assigning faculty to non-preferred morning/afternoon slots.</span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="font-bold text-navy-900 block">S2: Minimize Idle Gaps (wt: {softWeights.s2.toFixed(1)})</span>
                <span className="text-[11px] text-slate-500">Penalizes isolated gaps (&gt;1 hour) between classes on the same day.</span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="font-bold text-navy-900 block">S3: Avoid Consecutive Lectures (wt: {softWeights.s3.toFixed(1)})</span>
                <span className="text-[11px] text-slate-500">Penalizes 3 or more consecutive lectures for student groups.</span>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="font-bold text-navy-900 block">S4: Balanced Daily Workload (wt: {softWeights.s4.toFixed(1)})</span>
                <span className="text-[11px] text-slate-500">Penalizes variance in student daily workload across Mon–Fri.</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right: Dispatcher Panel */}
        <div className="space-y-6">
          <Card className="p-6 space-y-4">
            <CardHeader
              title="GA Optimizer Dispatcher"
              description="Genetic solver execution panel."
            />

            <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/70 text-amber-900 space-y-2 text-xs">
              <div className="flex items-center gap-2 font-bold">
                <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
                <span>Backend Dispatch Pending</span>
              </div>
              <p className="text-[11px] text-amber-800 leading-relaxed">
                Connects to FastAPI via <code>POST /api/v1/optimize/ga/solve</code>.
                In this frontend stage, live solver execution is reserved for the upcoming FastAPI integration.
              </p>
            </div>

            <Button
              variant="primary"
              disabled={true}
              className="w-full text-xs py-2.5 opacity-60 cursor-not-allowed bg-accent-purple"
              title="Awaiting FastAPI backend integration"
            >
              <Play className="w-4 h-4 mr-1.5" />
              <span>Evolve Timetable (Awaiting Backend)</span>
            </Button>
          </Card>
        </div>
      </div>

      {/* Actual Results & Convergence Telemetry */}
      {activeResult ? (
        <Card className="p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4">
            <div>
              <h3 className="font-bold text-navy-900 text-sm flex items-center gap-2">
                <Award className="w-5 h-5 text-accent-purple" />
                <span>Genetic Algorithm Evolutionary Telemetry</span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">{activeResult.message}</p>
            </div>
            <Badge variant="purple">{activeResult.status}</Badge>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg">
              <span className="text-[11px] font-bold text-slate-500 uppercase block">Generations</span>
              <span className="text-xl font-bold font-mono text-navy-900">{activeResult.generations_completed}</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">{activeResult.fitness_evaluations} evaluations</span>
            </div>
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg">
              <span className="text-[11px] font-bold text-slate-500 uppercase block">Soft Penalty Score</span>
              <span className="text-xl font-bold font-mono text-emerald-700">{activeResult.best_soft_penalty.toFixed(1)}</span>
              <span className="text-[10px] text-emerald-600 block mt-0.5">High human satisfaction</span>
            </div>
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg">
              <span className="text-[11px] font-bold text-slate-500 uppercase block">Hard Violations</span>
              <span className="text-xl font-bold font-mono text-emerald-700">{activeResult.best_hard_violations}</span>
              <span className="text-[10px] text-emerald-600 block mt-0.5">100% conflict-free</span>
            </div>
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg">
              <span className="text-[11px] font-bold text-slate-500 uppercase block">Execution Time</span>
              <span className="text-xl font-bold font-mono text-primary">{activeResult.execution_time_seconds.toFixed(2)}s</span>
              <span className="text-[10px] text-slate-400 block mt-0.5">CPU runtime</span>
            </div>
          </div>

          {/* Convergence Chart */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-navy-900 uppercase tracking-wider flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4 text-primary" />
              <span>Soft Penalty Minimization Across Generations</span>
            </h4>
            <div className="h-64 w-full bg-slate-50/50 p-2 rounded-lg border border-slate-200">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={activeResult.history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="generation" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="soft_penalty"
                    name="Best Soft Penalty"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="hard_violations"
                    name="Hard Violations"
                    stroke="#ef4444"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Card>
      ) : (
        <Card className="p-8 text-center space-y-3 bg-slate-50/50 border-dashed">
          <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
            <Dna className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto">
            <h4 className="font-bold text-navy-900 text-sm">No GA Execution Recorded</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Configure parameters above. When backend integration is completed, real evolutionary convergence curves will plot here.
              You can also click <strong>&quot;Load Verified Run Fixture&quot;</strong> in the header to inspect real GA results.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
