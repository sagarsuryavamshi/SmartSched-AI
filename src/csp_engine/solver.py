"""Production-grade Constraint Satisfaction Problem (CSP) Solver.

Implements:
  1. Backtracking Search with Domain Trails (Restoration).
  2. Minimum Remaining Values (MRV) Dynamic Variable Selection.
  3. Degree Heuristic Tie-Breaking.
  4. Least Constraining Value (LCV) Value Ordering.
  5. Forward Checking (FC) with Immediate Dead-End Detection.
  6. AC-3 Arc Consistency Preprocessing and Incremental Search Pruning.
"""

import collections
import copy
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.csp_engine.domain_types import (
    SchedulingAssignmentValue,
    SchedulingVariable,
    TimetableStatus,
)
from src.csp_engine.model import CSPModel
from src.csp_engine.solver_types import (
    SolverConfig,
    SolverResult,
    SolverStatistics,
    SolverStatus,
)
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.csp_engine.solver")


def values_are_compatible(
    val1: SchedulingAssignmentValue,
    val2: SchedulingAssignmentValue,
) -> bool:
    """Checks binary consistency between two assignments:
    Incompatible if on the same day they share any timeslot AND:
      - same faculty (H1: faculty double-booking) OR
      - same room (H2: classroom double-booking) OR
      - same student group (H3: cohort clash).
    """
    if val1.day != val2.day:
        return True

    # Check timeslot intersection
    if not (set(val1.slot_ids) & set(val2.slot_ids)):
        return True

    # At overlapping timeslots, conflicts arise if faculty, room, or group match
    if val1.faculty_id == val2.faculty_id:
        return False
    if val1.room_id == val2.room_id:
        return False
    if val1.group_id == val2.group_id:
        return False

    return True


class CSPSolver:
    """Enterprise CSP Search Engine for Academic Timetable Generation."""

    def __init__(self, model: Optional[CSPModel] = None) -> None:
        self.model = model
        self.stats = SolverStatistics()
        self.config = SolverConfig()
        self._start_time = 0.0

    def solve(
        self,
        config: Optional[SolverConfig] = None,
        model: Optional[CSPModel] = None,
    ) -> SolverResult:
        """Executes the CSP search algorithm according to the provided configuration."""
        if model is not None:
            self.model = model

        if self.model is None:
            return SolverResult(
                status=SolverStatus.INVALID_CONFIGURATION,
                is_solution_found=False,
                message="No CSPModel provided to solver.",
            )

        self.config = config or SolverConfig()
        self.stats = SolverStatistics()
        self._start_time = time.perf_counter()

        variables = self.model.variables
        num_vars = len(variables)

        # Module 1 Edge Case: Empty Problem
        if num_vars == 0:
            self.stats.execution_time_seconds = time.perf_counter() - self._start_time
            return SolverResult(
                status=SolverStatus.EMPTY_PROBLEM,
                is_solution_found=True,
                assignment={},
                statistics=self.stats,
                validation_report=self.model.validate_assignments({}),
                message="Problem contains zero variables to schedule.",
                config_used=self.config,
            )

        # Build Constraint Adjacency Graph (Neighbors sharing faculty, room potential, or group)
        adj_graph = self._build_adjacency_graph(variables)

        # Initialize Working Domains (shallow copy of lists to allow pruning without modifying model)
        working_domains: Dict[str, List[SchedulingAssignmentValue]] = {
            v.var_id: list(self.model.domains.get(v.var_id, []))
            for v in variables
        }

        # Check for immediate initial domain wipeout
        for var_id, dom in working_domains.items():
            if len(dom) == 0:
                self.stats.execution_time_seconds = time.perf_counter() - self._start_time
                return SolverResult(
                    status=SolverStatus.INFEASIBLE,
                    is_solution_found=False,
                    assignment={},
                    statistics=self.stats,
                    validation_report=None,
                    message=f"Variable '{var_id}' has an empty initial domain; no solution possible.",
                    config_used=self.config,
                )

        # Module 6: AC-3 Arc Consistency Preprocessing
        if self.config.use_ac3_preprocess:
            ac3_ok = self.ac3(working_domains, adj_graph)
            if not ac3_ok:
                self.stats.execution_time_seconds = time.perf_counter() - self._start_time
                return SolverResult(
                    status=SolverStatus.INFEASIBLE,
                    is_solution_found=False,
                    assignment={},
                    statistics=self.stats,
                    validation_report=None,
                    message="AC-3 preprocessing determined the CSP problem is unsatisfiable (domain wipeout).",
                    config_used=self.config,
                )

        # Begin Recursive Backtracking Search
        assignment: Dict[str, SchedulingAssignmentValue] = {}
        status = self._backtrack(assignment, working_domains, adj_graph, depth=1)
        self.stats.execution_time_seconds = time.perf_counter() - self._start_time

        if status == SolverStatus.SUCCESS and len(assignment) == num_vars:
            # Validate completed schedule against the full H1-H8 / S1-S4 validation engine
            val_report = self.model.validate_assignments(assignment)
            if not val_report.is_valid:
                # Invariant protection: Never return an invalid timetable as a successful solution
                logger.error("Solver produced an assignment that failed validation: %s", val_report.hard_violations)
                return SolverResult(
                    status=SolverStatus.INFEASIBLE,
                    is_solution_found=False,
                    assignment=assignment,
                    statistics=self.stats,
                    validation_report=val_report,
                    message="Solver generated assignment, but independent validator detected constraint violations.",
                    config_used=self.config,
                )

            return SolverResult(
                status=SolverStatus.SUCCESS,
                is_solution_found=True,
                assignment=assignment,
                statistics=self.stats,
                validation_report=val_report,
                message=f"Successfully generated conflict-free timetable ({num_vars}/{num_vars} sessions assigned).",
                config_used=self.config,
            )

        return SolverResult(
            status=status,
            is_solution_found=False,
            assignment=assignment,
            statistics=self.stats,
            validation_report=self.model.validate_assignments(assignment) if assignment else None,
            message=self._generate_failure_message(status),
            config_used=self.config,
        )

    def solve_optimize(
        self,
        time_budget_seconds: float = 5.0,
        config: Optional[SolverConfig] = None,
        model: Optional[CSPModel] = None,
    ) -> SolverResult:
        """Executes Depth-First Branch & Bound search to find the minimum soft penalty timetable within a time budget."""
        if model is not None:
            self.model = model

        if self.model is None:
            return SolverResult(
                status=SolverStatus.INVALID_CONFIGURATION,
                is_solution_found=False,
                message="No CSPModel provided to solver.",
            )

        cfg = copy.copy(config or SolverConfig())
        cfg.timeout_seconds = time_budget_seconds
        self.config = cfg
        self.stats = SolverStatistics()
        self._start_time = time.perf_counter()

        variables = self.model.variables
        num_vars = len(variables)
        if num_vars == 0:
            return self.solve(cfg, model)

        adj_graph = self._build_adjacency_graph(variables)
        working_domains = {v.var_id: list(self.model.domains.get(v.var_id, [])) for v in variables}

        if self.config.use_ac3_preprocess:
            if not self.ac3(working_domains, adj_graph):
                return SolverResult(
                    status=SolverStatus.INFEASIBLE,
                    is_solution_found=False,
                    assignment={},
                    statistics=self.stats,
                    message="AC-3 preprocessing determined problem is unsatisfiable.",
                    config_used=self.config,
                )

        best_assignment: Dict[str, SchedulingAssignmentValue] = {}
        best_report = None
        best_penalty = float("inf")

        def _dfs_optimize(assignment: Dict[str, SchedulingAssignmentValue], depth: int) -> None:
            nonlocal best_assignment, best_report, best_penalty

            if (time.perf_counter() - self._start_time) >= self.config.timeout_seconds:
                return

            if self.stats.nodes_explored >= self.config.max_search_nodes:
                return

            if len(assignment) == num_vars:
                rep = self.model.validate_assignments(assignment)
                if rep.is_valid and rep.soft_penalty_score < best_penalty:
                    best_penalty = rep.soft_penalty_score
                    best_assignment = dict(assignment)
                    best_report = rep
                return

            self.stats.nodes_explored += 1
            if depth > self.stats.max_depth_reached:
                self.stats.max_depth_reached = depth

            sel_var = self.select_unassigned_variable(assignment, working_domains, adj_graph)
            if sel_var is None:
                return

            ordered_vals = self.order_domain_values(sel_var, working_domains, adj_graph)
            for val in ordered_vals:
                if (time.perf_counter() - self._start_time) >= self.config.timeout_seconds:
                    break

                if not self._is_consistent(val, assignment):
                    continue

                assignment[sel_var] = val
                self.stats.successful_assignments += 1

                domain_trail: List[Tuple[str, SchedulingAssignmentValue]] = []
                prop_ok = True
                if self.config.use_forward_checking:
                    prop_ok = self.forward_check(sel_var, val, assignment, working_domains, adj_graph, domain_trail)

                if prop_ok:
                    _dfs_optimize(assignment, depth + 1)

                self.stats.backtracks += 1
                del assignment[sel_var]
                self._restore_domain_trail(domain_trail, working_domains)

        curr_assignment: Dict[str, SchedulingAssignmentValue] = {}
        _dfs_optimize(curr_assignment, depth=1)
        self.stats.execution_time_seconds = time.perf_counter() - self._start_time

        if best_assignment:
            return SolverResult(
                status=SolverStatus.SUCCESS,
                is_solution_found=True,
                assignment=best_assignment,
                statistics=self.stats,
                validation_report=best_report,
                message=f"Optimal CSP search completed: Best feasible soft penalty={best_penalty:.1f} in {self.stats.execution_time_seconds:.2f}s.",
                config_used=self.config,
            )

        return SolverResult(
            status=SolverStatus.TIMEOUT if (time.perf_counter() - self._start_time) >= self.config.timeout_seconds else SolverStatus.INFEASIBLE,
            is_solution_found=False,
            assignment={},
            statistics=self.stats,
            message="No feasible assignment discovered within time budget.",
            config_used=self.config,
        )

    # ========================================================================
    # MODULE 1: BACKTRACKING RECURSION
    # ========================================================================
    def _backtrack(
        self,
        assignment: Dict[str, SchedulingAssignmentValue],
        working_domains: Dict[str, List[SchedulingAssignmentValue]],
        adj_graph: Dict[str, Set[str]],
        depth: int,
    ) -> SolverStatus:
        """Recursive backtracking search loop."""
        # Check termination limits
        if self.stats.nodes_explored >= self.config.max_search_nodes:
            return SolverStatus.NODE_LIMIT_REACHED

        if (time.perf_counter() - self._start_time) >= self.config.timeout_seconds:
            return SolverStatus.TIMEOUT

        # Base case: Complete assignment
        if len(assignment) == len(self.model.variables):
            return SolverStatus.SUCCESS

        self.stats.nodes_explored += 1
        if depth > self.stats.max_depth_reached:
            self.stats.max_depth_reached = depth

        # Module 2 & 3: Variable Selection via MRV and Degree Heuristics
        selected_var_id = self.select_unassigned_variable(assignment, working_domains, adj_graph)
        if selected_var_id is None:
            return SolverStatus.SUCCESS

        # Module 4: Order candidate values (LCV or Natural)
        ordered_values = self.order_domain_values(selected_var_id, working_domains, adj_graph)

        for val in ordered_values:
            self.stats.assignment_attempts += 1

            # Check consistency against current partial assignment
            if not self._is_consistent(val, assignment):
                continue

            # Assign candidate value
            assignment[selected_var_id] = val
            self.stats.successful_assignments += 1

            # Module 5 & 6: Constraint Propagation (Forward Checking & Incremental AC-3)
            # Domain trail records removals: List[Tuple[var_id, removed_val]]
            domain_trail: List[Tuple[str, SchedulingAssignmentValue]] = []
            propagation_ok = True

            if self.config.use_forward_checking:
                propagation_ok = self.forward_check(
                    selected_var_id, val, assignment, working_domains, adj_graph, domain_trail
                )

            if propagation_ok and self.config.use_incremental_ac3:
                # Run incremental AC-3 on affected neighbor arcs
                propagation_ok = self.incremental_ac3(
                    selected_var_id, working_domains, adj_graph, domain_trail
                )

            if propagation_ok:
                result_status = self._backtrack(assignment, working_domains, adj_graph, depth + 1)
                if result_status == SolverStatus.SUCCESS:
                    return SolverStatus.SUCCESS
                elif result_status in [SolverStatus.NODE_LIMIT_REACHED, SolverStatus.TIMEOUT]:
                    return result_status

            # Backtrack step: undo assignment and restore domain trail
            self.stats.backtracks += 1
            del assignment[selected_var_id]
            self._restore_domain_trail(domain_trail, working_domains)

        self.stats.dead_ends += 1
        return SolverStatus.INFEASIBLE

    # ========================================================================
    # MODULE 2 & 3: MRV AND DEGREE HEURISTICS
    # ========================================================================
    def select_unassigned_variable(
        self,
        assignment: Dict[str, SchedulingAssignmentValue],
        working_domains: Dict[str, List[SchedulingAssignmentValue]],
        adj_graph: Dict[str, Set[str]],
    ) -> Optional[str]:
        """Selects the next unassigned variable using MRV with Degree tie-breaking.
        Deterministic tie-breaking: sorts on alphabetical var_id if tied.
        """
        unassigned_vars = [v.var_id for v in self.model.variables if v.var_id not in assignment]
        if not unassigned_vars:
            return None

        if not self.config.use_mrv and not self.config.use_degree:
            # Natural order
            return unassigned_vars[0]

        best_var = None
        min_domain_size = float("inf")
        max_degree = -1

        for var_id in unassigned_vars:
            dom_size = len(working_domains.get(var_id, []))

            # Calculate degree: number of unassigned neighbors
            if self.config.use_degree:
                neighbors = adj_graph.get(var_id, set())
                degree = sum(1 for n in neighbors if n not in assignment)
            else:
                degree = 0

            if self.config.use_mrv:
                if dom_size < min_domain_size:
                    min_domain_size = dom_size
                    max_degree = degree
                    best_var = var_id
                elif dom_size == min_domain_size:
                    # Degree tie-breaker
                    if degree > max_degree:
                        max_degree = degree
                        best_var = var_id
                    elif degree == max_degree:
                        # Deterministic alphabetical tie-breaker
                        if best_var is None or var_id < best_var:
                            best_var = var_id
            else:
                # Degree only
                if degree > max_degree:
                    max_degree = degree
                    best_var = var_id
                elif degree == max_degree:
                    if best_var is None or var_id < best_var:
                        best_var = var_id

        return best_var

    # ========================================================================
    # MODULE 4: LEAST CONSTRAINING VALUE (LCV)
    # ========================================================================
    def order_domain_values(
        self,
        var_id: str,
        working_domains: Dict[str, List[SchedulingAssignmentValue]],
        adj_graph: Dict[str, Set[str]],
    ) -> List[SchedulingAssignmentValue]:
        """Orders values for var_id.
        If LCV is enabled: orders by increasing number of neighbor domain values ruled out.
        Deterministic tie-breaking: sorts by day, start_time, room_id.
        """
        domain_vals = working_domains.get(var_id, [])
        if not domain_vals:
            return []

        if not self.config.use_lcv:
            # Deterministic natural ordering
            return sorted(domain_vals, key=lambda val: (val.day, val.start_time, val.room_id))

        scored_values = []
        neighbors = adj_graph.get(var_id, set())

        for val in domain_vals:
            eliminations = 0
            for neighbor_id in neighbors:
                neighbor_dom = working_domains.get(neighbor_id, [])
                for n_val in neighbor_dom:
                    self.stats.constraint_checks += 1
                    if not values_are_compatible(val, n_val):
                        eliminations += 1
            # Primary: minimum eliminations. Secondary: deterministic coordinate tuple
            scored_values.append((eliminations, val.day, val.start_time, val.room_id, val))

        scored_values.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
        return [item[4] for item in scored_values]

    # ========================================================================
    # MODULE 5: FORWARD CHECKING
    # ========================================================================
    def forward_check(
        self,
        assigned_var_id: str,
        assigned_val: SchedulingAssignmentValue,
        assignment: Dict[str, SchedulingAssignmentValue],
        working_domains: Dict[str, List[SchedulingAssignmentValue]],
        adj_graph: Dict[str, Set[str]],
        domain_trail: List[Tuple[str, SchedulingAssignmentValue]],
    ) -> bool:
        """Removes incompatible values from unassigned neighbors' domains.
        Returns False immediately if any neighbor's domain is wiped out.
        """
        neighbors = adj_graph.get(assigned_var_id, set())

        for neighbor_id in neighbors:
            if neighbor_id in assignment:
                continue

            neighbor_dom = working_domains[neighbor_id]
            kept_values = []

            for n_val in neighbor_dom:
                self.stats.constraint_checks += 1
                if values_are_compatible(assigned_val, n_val):
                    kept_values.append(n_val)
                else:
                    domain_trail.append((neighbor_id, n_val))
                    self.stats.domain_reductions += 1

            if len(kept_values) == 0:
                # Immediate domain wipeout
                return False

            working_domains[neighbor_id] = kept_values

        return True

    # ========================================================================
    # MODULE 6: AC-3 ARC CONSISTENCY
    # ========================================================================
    def ac3(
        self,
        working_domains: Dict[str, List[SchedulingAssignmentValue]],
        adj_graph: Dict[str, Set[str]],
        initial_arcs: Optional[List[Tuple[str, str]]] = None,
        domain_trail: Optional[List[Tuple[str, SchedulingAssignmentValue]]] = None,
    ) -> bool:
        """Executes AC-3 arc consistency.
        Returns True if arc consistent, False if domain wipeout occurs.
        """
        queue = collections.deque()

        if initial_arcs is not None:
            queue.extend(initial_arcs)
        else:
            # Enqueue all binary directed arcs (Xi, Xj)
            for xi, neighbors in adj_graph.items():
                for xj in neighbors:
                    queue.append((xi, xj))

        while queue:
            xi, xj = queue.popleft()
            self.stats.ac3_arcs_processed += 1

            revised, wiped_out = self._revise(xi, xj, working_domains, domain_trail)
            if wiped_out:
                return False

            if revised:
                # If domain of Xi was reduced, re-insert arcs (Xk, Xi) for all neighbors Xk of Xi except Xj
                for xk in adj_graph.get(xi, set()):
                    if xk != xj:
                        queue.append((xk, xi))

        return True

    def _revise(
        self,
        xi: str,
        xj: str,
        working_domains: Dict[str, List[SchedulingAssignmentValue]],
        domain_trail: Optional[List[Tuple[str, SchedulingAssignmentValue]]],
    ) -> Tuple[bool, bool]:
        """REVISE(Xi, Xj) operation:
        Deletes any value x in D(Xi) that has no supporting value y in D(Xj) satisfying binary constraints.
        Returns (revised: bool, wiped_out: bool).
        """
        revised = False
        dom_xi = working_domains.get(xi, [])
        dom_xj = working_domains.get(xj, [])

        kept_xi = []
        for x_val in dom_xi:
            # Check if there exists ANY supporting value in D(Xj)
            has_support = False
            for y_val in dom_xj:
                self.stats.constraint_checks += 1
                if values_are_compatible(x_val, y_val):
                    has_support = True
                    break

            if has_support:
                kept_xi.append(x_val)
            else:
                revised = True
                self.stats.ac3_values_removed += 1
                self.stats.domain_reductions += 1
                if domain_trail is not None:
                    domain_trail.append((xi, x_val))

        if len(kept_xi) == 0:
            return True, True  # Domain wipeout

        if revised:
            working_domains[xi] = kept_xi

        return revised, False

    def incremental_ac3(
        self,
        assigned_var_id: str,
        working_domains: Dict[str, List[SchedulingAssignmentValue]],
        adj_graph: Dict[str, Set[str]],
        domain_trail: List[Tuple[str, SchedulingAssignmentValue]],
    ) -> bool:
        """Executes incremental AC-3 following an assignment by checking arcs into neighbors."""
        neighbors = adj_graph.get(assigned_var_id, set())
        arcs_to_check = [(n, assigned_var_id) for n in neighbors]
        return self.ac3(working_domains, adj_graph, initial_arcs=arcs_to_check, domain_trail=domain_trail)

    # ========================================================================
    # HELPER & RESTORATION UTILITIES
    # ========================================================================
    def _is_consistent(
        self,
        candidate_val: SchedulingAssignmentValue,
        assignment: Dict[str, SchedulingAssignmentValue],
    ) -> bool:
        """Verifies candidate value compatibility against all currently assigned variables."""
        for assigned_val in assignment.values():
            self.stats.constraint_checks += 1
            if not values_are_compatible(candidate_val, assigned_val):
                return False
        return True

    def _restore_domain_trail(
        self,
        domain_trail: List[Tuple[str, SchedulingAssignmentValue]],
        working_domains: Dict[str, List[SchedulingAssignmentValue]],
    ) -> None:
        """Restores values pruned during forward checking / AC-3 back to working domains."""
        while domain_trail:
            var_id, val = domain_trail.pop()
            working_domains[var_id].append(val)

    def _build_adjacency_graph(self, variables: List[SchedulingVariable]) -> Dict[str, Set[str]]:
        """Constructs constraint graph where variables are connected if they share:
          - Same faculty member
          - Same student cohort
          - Potential classroom overlap
        """
        adj: Dict[str, Set[str]] = {v.var_id: set() for v in variables}
        n = len(variables)

        for i in range(n):
            v1 = variables[i]
            for j in range(i + 1, n):
                v2 = variables[j]

                # If they share faculty or group, they strictly compete for timeslots
                shares_faculty = (v1.faculty_id == v2.faculty_id)
                shares_group = (v1.group_id == v2.group_id)

                # If they require compatible room types, they can compete for classrooms
                can_share_room = (v1.required_room_type == v2.required_room_type)

                if shares_faculty or shares_group or can_share_room:
                    adj[v1.var_id].add(v2.var_id)
                    adj[v2.var_id].add(v1.var_id)

        return adj

    def _generate_failure_message(self, status: SolverStatus) -> str:
        """Generates clear, diagnostic explanation of search termination."""
        if status == SolverStatus.NODE_LIMIT_REACHED:
            return (
                f"Search halted: Node limit ({self.config.max_search_nodes:,} nodes) reached. "
                f"Explored {self.stats.nodes_explored:,} states with {self.stats.backtracks:,} backtracks without finding a solution."
            )
        elif status == SolverStatus.TIMEOUT:
            return (
                f"Search halted: Execution timeout ({self.config.timeout_seconds:.1f}s) exceeded. "
                f"Explored {self.stats.nodes_explored:,} states before timeout."
            )
        elif status == SolverStatus.INFEASIBLE:
            return (
                f"Search exhausted: Mathematically proven that no conflict-free timetable exists under current hard constraints. "
                f"Total dead ends encountered: {self.stats.dead_ends:,}."
            )
        return "Search terminated without reaching a solution."


class CSPProblem:
    """Convenience wrapper for raw CSP problems, retaining backward compatibility."""

    def __init__(self, variables: List[str], domains: Dict[str, List[Any]]) -> None:
        self.variables = variables
        self.domains = domains
        self.constraints: List[Any] = []

    def add_constraint(self, constraint: Any) -> None:
        self.constraints.append(constraint)
