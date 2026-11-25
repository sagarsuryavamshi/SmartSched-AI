import { WizardDraftState } from "@/types/wizard";
import { ApiClient } from "./apiClient";

export interface OptimizationSubmissionPayload {
  department: string;
  term: string;
  academic_year: string;
  scope: {
    course_ids: string[];
    group_ids: string[];
    room_ids: string[];
  };
  algorithm: "GENETIC_ALGORITHM" | "BACKTRACKING_CSP";
  ga_hyperparameters?: {
    population_size: number;
    max_generations: number;
    crossover_probability: number;
    mutation_rate: number;
    random_seed?: number;
  };
  csp_hyperparameters?: {
    use_mrv: boolean;
    use_degree: boolean;
    use_lcv: boolean;
    use_forward_checking: boolean;
    use_ac3_preprocess: boolean;
    use_incremental_ac3: boolean;
  };
  soft_objective_weights: {
    s1_faculty_preferences: number;
    s2_minimize_idle_gaps: number;
    s3_avoid_consecutive_lectures: number;
    s4_balanced_workload: number;
  };
}

export class OptimizationService {
  static formatPayload(state: WizardDraftState): OptimizationSubmissionPayload {
    return {
      department: state.department,
      term: state.term,
      academic_year: state.academicYear,
      scope: {
        course_ids: state.selectedCourseIds,
        group_ids: state.selectedGroupIds,
        room_ids: state.selectedRoomIds,
      },
      algorithm: state.algorithm === "GA" ? "GENETIC_ALGORITHM" : "BACKTRACKING_CSP",
      ga_hyperparameters:
        state.algorithm === "GA"
          ? {
              population_size: state.gaParams.populationSize,
              max_generations: state.gaParams.maxGenerations,
              crossover_probability: state.gaParams.crossoverProb,
              mutation_rate: state.gaParams.mutationRate,
              random_seed: 42,
            }
          : undefined,
      csp_hyperparameters:
        state.algorithm === "CSP"
          ? {
              use_mrv: state.cspParams.useMRV,
              use_degree: state.cspParams.useDegree,
              use_lcv: state.cspParams.useLCV,
              use_forward_checking: state.cspParams.useForwardChecking,
              use_ac3_preprocess: state.cspParams.useAC3Preprocess,
              use_incremental_ac3: state.cspParams.useIncrementalAC3,
            }
          : undefined,
      soft_objective_weights: {
        s1_faculty_preferences: state.softWeights.s1FacultyPreferences,
        s2_minimize_idle_gaps: state.softWeights.s2MinimizeGaps,
        s3_avoid_consecutive_lectures: state.softWeights.s3AvoidConsecutive,
        s4_balanced_workload: state.softWeights.s4BalancedWorkload,
      },
    };
  }

  /**
   * Submits optimization run directly to the FastAPI backend.
   */
  static async submitOptimizationRun(payload: OptimizationSubmissionPayload): Promise<{
    success: boolean;
    message: string;
    job_id?: string;
    run_id?: string;
  }> {
    try {
      if (payload.algorithm === "BACKTRACKING_CSP") {
        const cspPayload = {
          use_mrv: payload.csp_hyperparameters?.use_mrv ?? true,
          use_degree: payload.csp_hyperparameters?.use_degree ?? true,
          use_lcv: payload.csp_hyperparameters?.use_lcv ?? true,
          use_forward_checking: payload.csp_hyperparameters?.use_forward_checking ?? true,
          use_ac3_preprocess: payload.csp_hyperparameters?.use_ac3_preprocess ?? true,
          timeout_seconds: 30.0,
        };
        const res: any = await ApiClient.post("/optimize/csp/solve-backtracking?async_mode=false", cspPayload);
        return {
          success: res.success,
          message: res.message || `CSP solved successfully in ${res.execution_time_seconds}s (${res.assigned_sessions} sessions assigned).`,
          run_id: res.run_id,
        };
      } else {
        const gaPayload = {
          population_size: payload.ga_hyperparameters?.population_size ?? 100,
          max_generations: payload.ga_hyperparameters?.max_generations ?? 120,
          crossover_prob: payload.ga_hyperparameters?.crossover_probability ?? 0.85,
          mutation_prob: payload.ga_hyperparameters?.mutation_rate ?? 0.08,
          elitism_count: 4,
          tournament_size: 3,
          timeout_seconds: 30.0,
        };
        const res: any = await ApiClient.post("/optimize/ga/solve?async_mode=false", gaPayload);
        return {
          success: res.success,
          message: `Genetic Algorithm completed in ${res.execution_time_seconds}s (Hard violations: ${res.hard_violations}, Soft penalty: ${res.soft_penalty}).`,
          run_id: res.run_id,
        };
      }
    } catch (err: any) {
      return {
        success: false,
        message: `Backend optimization dispatch failed: ${err.message}`,
      };
    }
  }
}
