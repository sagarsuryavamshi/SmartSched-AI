from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, Optional
import uuid
import time

from backend.app.core.config import settings
from backend.app.api.v1.endpoints.auth import require_admin
from backend.app.schemas.api_schemas import CSPSolverRequest, GASolverRequest, BenchmarkRequest
from src.csp_engine.model import CSPModel
from src.csp_engine.solver import CSPSolver
from src.csp_engine.solver_types import SolverConfig, SolverResult
from src.ga_engine.genetic_solver import GeneticSolver, GAConfig, GAResult
from src.ga_engine.benchmark import run_comparative_benchmark
from src.database.timetable_repository import save_timetable_solution
from src.database.job_repository import create_job, get_job, update_job_status

router = APIRouter()
DB_PATH = str(settings.DB_PATH)


def execute_csp_job(job_id: str, config: CSPSolverRequest):
    update_job_status(job_id, status="running", started_at=time.time(), db_path=DB_PATH)
    try:
        model = CSPModel.build_from_db(DB_PATH)
        solver = CSPSolver(model)
        cfg = SolverConfig(
            use_mrv=config.use_mrv,
            use_degree=config.use_degree,
            use_lcv=config.use_lcv,
            use_forward_checking=config.use_forward_checking,
            use_ac3_preprocess=config.use_ac3_preprocess,
            timeout_seconds=config.timeout_seconds
        )
        res: SolverResult = solver.solve(cfg)
        
        saved = False
        run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"
        if res.is_solution_found and res.assignment:
            saved, _ = save_timetable_solution(
                res.assignment,
                model.variables_map,
                run_id=run_id,
                db_path=DB_PATH
            )

        result_payload = {
            "success": res.is_solution_found,
            "status": res.status.value if hasattr(res.status, 'value') else str(res.status),
            "run_id": run_id if saved else None,
            "execution_time_seconds": round(res.statistics.execution_time_seconds, 4),
            "nodes_explored": res.statistics.nodes_explored,
            "backtracks": res.statistics.backtracks,
            "domain_reductions": res.statistics.domain_reductions,
            "assigned_sessions": len(res.assignment),
            "total_variables": len(model.variables),
            "message": res.message
        }
        update_job_status(job_id, status="completed", result=result_payload, completed_at=time.time(), db_path=DB_PATH)
    except Exception as e:
        update_job_status(job_id, status="failed", error=str(e), completed_at=time.time(), db_path=DB_PATH)


def execute_ga_job(job_id: str, config: GASolverRequest):
    update_job_status(job_id, status="running", started_at=time.time(), db_path=DB_PATH)
    try:
        model = CSPModel.build_from_db(DB_PATH)
        ga_cfg = GAConfig(
            population_size=config.population_size,
            max_generations=config.max_generations,
            crossover_prob=config.crossover_prob,
            mutation_prob=config.mutation_prob,
            elitism_count=config.elitism_count,
            tournament_size=config.tournament_size,
            timeout_seconds=config.timeout_seconds
        )
        solver = GeneticSolver(model)
        res: GAResult = solver.solve(ga_cfg)

        saved = False
        run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"
        if res.is_solution_found and res.best_chromosome:
            assignment_dict = res.best_chromosome.to_assignment_dict()
            saved, _ = save_timetable_solution(
                assignment_dict,
                model.variables_map,
                run_id=run_id,
                db_path=DB_PATH
            )

        result_payload = {
            "success": res.is_solution_found,
            "status": res.status,
            "run_id": run_id if saved else None,
            "generations_completed": res.generations_completed,
            "fitness_evaluations": res.fitness_evaluations,
            "execution_time_seconds": round(res.execution_time_seconds, 4),
            "hard_violations": res.best_chromosome.hard_violations_count if res.best_chromosome else 999,
            "soft_penalty": res.best_chromosome.soft_penalty if res.best_chromosome else 999.0
        }
        update_job_status(job_id, status="completed", result=result_payload, completed_at=time.time(), db_path=DB_PATH)
    except Exception as e:
        update_job_status(job_id, status="failed", error=str(e), completed_at=time.time(), db_path=DB_PATH)


def execute_benchmark_job(job_id: str, config: BenchmarkRequest):
    update_job_status(job_id, status="running", started_at=time.time(), db_path=DB_PATH)
    try:
        model = CSPModel.build_from_db(DB_PATH)
        csp_cfg = SolverConfig(
            use_mrv=config.csp_config.use_mrv if config.csp_config else True,
            use_degree=config.csp_config.use_degree if config.csp_config else True,
            use_lcv=config.csp_config.use_lcv if config.csp_config else True,
            use_forward_checking=config.csp_config.use_forward_checking if config.csp_config else True,
            use_ac3_preprocess=config.csp_config.use_ac3_preprocess if config.csp_config else True,
            timeout_seconds=config.csp_config.timeout_seconds if config.csp_config else 30.0
        )
        bench = run_comparative_benchmark(
            model=model,
            csp_config=csp_cfg,
            ga_pop_size=config.ga_pop_size,
            ga_generations=config.ga_generations,
            ga_timeout=config.ga_timeout
        )

        result_payload = {
            "comparison_table": bench.comparison_table,
            "backtracking_metrics": bench.backtracking_metrics,
            "ga_aggregate_metrics": bench.ga_aggregate_metrics,
            "dataset_variables_count": bench.dataset_variables_count
        }
        update_job_status(job_id, status="completed", result=result_payload, completed_at=time.time(), db_path=DB_PATH)
    except Exception as e:
        update_job_status(job_id, status="failed", error=str(e), completed_at=time.time(), db_path=DB_PATH)

@router.post("/csp/solve-backtracking", dependencies=[Depends(require_admin)])
def solve_csp(payload: CSPSolverRequest, background_tasks: BackgroundTasks, async_mode: bool = False):
    if not async_mode:
        model = CSPModel.build_from_db(DB_PATH)
        solver = CSPSolver(model)
        cfg = SolverConfig(
            use_mrv=payload.use_mrv,
            use_degree=payload.use_degree,
            use_lcv=payload.use_lcv,
            use_forward_checking=payload.use_forward_checking,
            use_ac3_preprocess=payload.use_ac3_preprocess,
            timeout_seconds=payload.timeout_seconds
        )
        res: SolverResult = solver.solve(cfg)
        
        saved = False
        run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"
        if res.is_solution_found and res.assignment:
            saved, _ = save_timetable_solution(
                res.assignment,
                model.variables_map,
                run_id=run_id,
                db_path=DB_PATH
            )

        return {
            "success": res.is_solution_found,
            "status": res.status.value if hasattr(res.status, 'value') else str(res.status),
            "run_id": run_id if saved else None,
            "execution_time_seconds": round(res.statistics.execution_time_seconds, 4),
            "nodes_explored": res.statistics.nodes_explored,
            "backtracks": res.statistics.backtracks,
            "domain_reductions": res.statistics.domain_reductions,
            "assigned_sessions": len(res.assignment),
            "total_variables": len(model.variables),
            "message": res.message
        }
    
    job_id = str(uuid.uuid4())
    create_job(job_id=job_id, job_type="csp", status="queued", db_path=DB_PATH)
    background_tasks.add_task(execute_csp_job, job_id, payload)
    return {"job_id": job_id, "status": "queued", "message": "CSP optimization job dispatched"}

@router.post("/ga/solve", dependencies=[Depends(require_admin)])
def solve_ga(payload: GASolverRequest, background_tasks: BackgroundTasks, async_mode: bool = False):
    if not async_mode:
        model = CSPModel.build_from_db(DB_PATH)
        ga_cfg = GAConfig(
            population_size=payload.population_size,
            max_generations=payload.max_generations,
            crossover_prob=payload.crossover_prob,
            mutation_prob=payload.mutation_prob,
            elitism_count=payload.elitism_count,
            tournament_size=payload.tournament_size,
            timeout_seconds=payload.timeout_seconds
        )
        solver = GeneticSolver(model)
        res: GAResult = solver.solve(ga_cfg)

        saved = False
        run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"
        if res.is_solution_found and res.best_chromosome:
            assignment_dict = res.best_chromosome.to_assignment_dict()
            saved, _ = save_timetable_solution(
                assignment_dict,
                model.variables_map,
                run_id=run_id,
                db_path=DB_PATH
            )

        return {
            "success": res.is_solution_found,
            "status": res.status,
            "run_id": run_id if saved else None,
            "generations_completed": res.generations_completed,
            "fitness_evaluations": res.fitness_evaluations,
            "execution_time_seconds": round(res.execution_time_seconds, 4),
            "hard_violations": res.best_chromosome.hard_violations_count if res.best_chromosome else 999,
            "soft_penalty": res.best_chromosome.soft_penalty if res.best_chromosome else 999.0
        }

    job_id = str(uuid.uuid4())
    create_job(job_id=job_id, job_type="ga", status="queued", db_path=DB_PATH)
    background_tasks.add_task(execute_ga_job, job_id, payload)
    return {"job_id": job_id, "status": "queued", "message": "Genetic Algorithm optimization job dispatched"}

@router.post("/benchmark", dependencies=[Depends(require_admin)])
def run_benchmark(payload: BenchmarkRequest, background_tasks: BackgroundTasks, async_mode: bool = False):
    if not async_mode:
        model = CSPModel.build_from_db(DB_PATH)
        csp_cfg = SolverConfig(
            use_mrv=payload.csp_config.use_mrv if payload.csp_config else True,
            use_degree=payload.csp_config.use_degree if payload.csp_config else True,
            use_lcv=payload.csp_config.use_lcv if payload.csp_config else True,
            use_forward_checking=payload.csp_config.use_forward_checking if payload.csp_config else True,
            use_ac3_preprocess=payload.csp_config.use_ac3_preprocess if payload.csp_config else True,
            timeout_seconds=payload.csp_config.timeout_seconds if payload.csp_config else 30.0
        )
        bench = run_comparative_benchmark(
            model=model,
            csp_config=csp_cfg,
            ga_pop_size=payload.ga_pop_size,
            ga_generations=payload.ga_generations,
            ga_timeout=payload.ga_timeout
        )
        return {
            "comparison_table": bench.comparison_table,
            "backtracking_metrics": bench.backtracking_metrics,
            "ga_aggregate_metrics": bench.ga_aggregate_metrics,
            "dataset_variables_count": bench.dataset_variables_count
        }

    job_id = str(uuid.uuid4())
    create_job(job_id=job_id, job_type="benchmark", status="queued", db_path=DB_PATH)
    background_tasks.add_task(execute_benchmark_job, job_id, payload)
    return {"job_id": job_id, "status": "queued", "message": "Comparative benchmark job dispatched"}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    job = get_job(job_id, db_path=DB_PATH)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
