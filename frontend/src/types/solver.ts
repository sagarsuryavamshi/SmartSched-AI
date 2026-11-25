/**
 * Execution Job and Solver Result Type Definitions.
 * Aligned with Python src/csp_engine/solver_types.py and src/ga_engine/genetic_solver.py.
 */

export type JobStatus = "NOT_STARTED" | "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";

export type AlgorithmType = "BACKTRACKING_CSP" | "GENETIC_ALGORITHM" | "COMPARATIVE_BENCHMARK";

export interface CSPSolverConfig {
  use_mrv: boolean;
  use_degree: boolean;
  use_lcv: boolean;
  use_forward_checking: boolean;
  use_ac3_preprocess: boolean;
  use_incremental_ac3: boolean;
  max_search_nodes: number;
  timeout_seconds: number;
}

export interface CSPSolverStatistics {
  nodes_explored: number;
  assignment_attempts: number;
  successful_assignments: number;
  backtracks: number;
  constraint_checks: number;
  domain_reductions: number;
  ac3_arcs_processed: number;
  ac3_values_removed: number;
  dead_ends: number;
  max_depth_reached: number;
  execution_time_seconds: number;
}

export interface HardConstraintAuditResult {
  constraint_id: "H1" | "H2" | "H3" | "H4" | "H5" | "H6" | "H7" | "H8";
  name: string;
  passed: boolean;
  violations_count: number;
  details?: string;
}

export interface SoftObjectiveAuditResult {
  objective_id: "S1" | "S2" | "S3" | "S4";
  name: string;
  weight: number;
  penalty_score: number;
  description: string;
}

export interface CSPSolverResultPayload {
  status: "SUCCESS" | "INFEASIBLE" | "NODE_LIMIT_REACHED" | "TIMEOUT" | "INVALID_CONFIGURATION";
  is_solution_found: boolean;
  statistics: CSPSolverStatistics;
  assigned_sessions_count: number;
  total_variables_count: number;
  hard_audit: HardConstraintAuditResult[];
  soft_audit: SoftObjectiveAuditResult[];
  message: string;
  config_used: CSPSolverConfig;
}

export interface GAHyperparameters {
  population_size: number;
  max_generations: number;
  crossover_prob: number;
  mutation_prob: number;
  elitism_count: number;
  tournament_size: number;
  random_seed: number;
  timeout_seconds: number;
  enable_repair: boolean;
  repair_prob: number;
  target_soft_penalty?: number;
}

export interface GAHistoryRecord {
  generation: number;
  best_fitness: number;
  avg_fitness: number;
  hard_violations: number;
  soft_penalty: number;
}

export interface GAResultPayload {
  status: "FEASIBLE" | "OPTIMAL" | "CONVERGED_WITH_VIOLATIONS" | "TIMEOUT";
  is_solution_found: boolean;
  generations_completed: number;
  fitness_evaluations: number;
  crossover_operations: number;
  mutation_operations: number;
  repair_attempts: number;
  successful_repairs: number;
  execution_time_seconds: number;
  best_fitness: number;
  best_hard_violations: number;
  best_soft_penalty: number;
  history: GAHistoryRecord[];
  hard_audit: HardConstraintAuditResult[];
  soft_audit: SoftObjectiveAuditResult[];
  message: string;
  config_used: GAHyperparameters;
}

export interface BenchmarkComparativeMetric {
  metric_name: string;
  csp_value: string | number;
  ga_value: string | number;
  advantage: "CSP" | "GA" | "TIED";
}

export interface BenchmarkSeedRun {
  seed: number;
  feasibility: boolean;
  hard_violations: number;
  soft_penalty: number;
  runtime_seconds: number;
  generations: number;
}

export interface BenchmarkResultPayload {
  dataset_variables_count: number;
  csp_summary: {
    status: string;
    runtime_seconds: number;
    nodes_explored: number;
    backtracks: number;
    hard_violations: number;
    soft_penalty: number;
  };
  ga_aggregate: {
    mean_runtime_seconds: number;
    feasibility_rate_pct: number;
    mean_soft_penalty: number;
    best_soft_penalty: number;
    worst_soft_penalty: number;
    mean_generations: number;
  };
  seed_runs: BenchmarkSeedRun[];
  metrics_comparison: BenchmarkComparativeMetric[];
}

export interface ExecutionJob<T = any> {
  job_id: string;
  algorithm: AlgorithmType;
  status: JobStatus;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  progress_pct: number;
  result?: T;
  error?: string;
}
