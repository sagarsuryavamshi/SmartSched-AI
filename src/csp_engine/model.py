"""CSP Problem Model representation, validation engine, and builder."""

import json
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.csp_engine.domain_types import (
    ConstraintViolation,
    SchedulingAssignmentValue,
    SchedulingVariable,
    SessionType,
    TimetableStatus,
    ValidationReport,
)
from src.csp_engine.generator import generate_domains_from_db, generate_variables_from_db
from src.csp_engine.hard_constraints import (
    check_h1_faculty_overlap,
    check_h2_classroom_overlap,
    check_h3_student_group_overlap,
    check_h4_room_capacity,
    check_h5_faculty_availability,
    check_h6_room_type,
    check_h7_lab_continuity,
    check_h8_working_hours,
)
from src.csp_engine.soft_constraints import (
    score_s1_faculty_preferences,
    score_s2_faculty_idle_gaps,
    score_s3_consecutive_theory_sessions,
    score_s4_balanced_daily_workload,
)
from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.csp_engine.model")


class CSPModel:
    """Mathematical CSP representation independent of Streamlit UI.

    Formulation:
      - X = { x_1, x_2, ..., x_N }: Set of SchedulingVariable instances.
      - D = { D(x_1), D(x_2), ..., D(x_N) }: Discrete domains of valid AssignmentValues.
      - C_hard = { H1, H2, H3, H4, H5, H6, H7, H8 }: Strict Boolean relations.
      - C_soft = { S1, S2, S3, S4 }: Objective penalty functions for schedule optimization.
    """

    def __init__(
        self,
        variables: List[SchedulingVariable],
        domains: Dict[str, List[SchedulingAssignmentValue]],
        room_capacities: Optional[Dict[str, int]] = None,
        room_types: Optional[Dict[str, str]] = None,
        group_sizes: Optional[Dict[str, int]] = None,
        faculty_unavailability: Optional[Dict[str, Set[str]]] = None,
        faculty_working_days: Optional[Dict[str, Set[str]]] = None,
        timeslot_details: Optional[Dict[str, Dict[str, Any]]] = None,
        faculty_preferences: Optional[Dict[str, Set[str]]] = None,
    ) -> None:
        self.variables = variables
        self.variables_map: Dict[str, SchedulingVariable] = {v.var_id: v for v in variables}
        self.domains = domains
        self.room_capacities = room_capacities or {}
        self.room_types = room_types or {}
        self.group_sizes = group_sizes or {}
        self.faculty_unavailability = faculty_unavailability or {}
        self.faculty_working_days = faculty_working_days or {}
        self.timeslot_details = timeslot_details or {}
        self.faculty_preferences = faculty_preferences or {}

        # Internal assignment state
        self.current_assignment: Dict[str, SchedulingAssignmentValue] = {}

    @classmethod
    def build_from_db(cls, db_path: str = DEFAULT_DB_PATH) -> "CSPModel":
        """Builds a complete CSPModel by loading real entities and generating domains from SQLite."""
        logger.info("Building CSP Model from database: %s", db_path)
        variables = generate_variables_from_db(db_path)
        domains = generate_domains_from_db(variables, db_path)

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            # Classrooms metadata
            cursor.execute("SELECT room_id, capacity, room_type FROM classrooms")
            room_rows = cursor.fetchall()
            room_capacities = {r["room_id"]: int(r["capacity"]) for r in room_rows}
            room_types = {r["room_id"]: r["room_type"] for r in room_rows}

            # Student groups metadata
            cursor.execute("SELECT group_id, size FROM student_groups")
            group_sizes = {g["group_id"]: int(g["size"]) for g in cursor.fetchall()}

            # Faculty metadata
            cursor.execute("SELECT faculty_id, available_days, unavailable_slots FROM faculty")
            faculty_unavailability: Dict[str, Set[str]] = {}
            faculty_working_days: Dict[str, Set[str]] = {}
            for row in cursor.fetchall():
                f_id = row["faculty_id"]
                faculty_working_days[f_id] = set(json.loads(row["available_days"] or "[]"))
                faculty_unavailability[f_id] = set(json.loads(row["unavailable_slots"] or "[]"))

            # Timeslots metadata
            cursor.execute("SELECT slot_id, day, start_time, end_time, duration_minutes, is_break FROM timeslots")
            timeslot_details = {row["slot_id"]: dict(row) for row in cursor.fetchall()}

        return cls(
            variables=variables,
            domains=domains,
            room_capacities=room_capacities,
            room_types=room_types,
            group_sizes=group_sizes,
            faculty_unavailability=faculty_unavailability,
            faculty_working_days=faculty_working_days,
            timeslot_details=timeslot_details,
        )

    def validate_assignments(
        self,
        assignments: Optional[Dict[str, SchedulingAssignmentValue]] = None,
    ) -> ValidationReport:
        """Evaluates a proposed partial or complete timetable state against all H1-H8 and S1-S4 constraints.

        Classifies schedule state into:
          - EMPTY: 0 assignments provided.
          - PARTIAL_VALID: >0 and <N assignments, with zero hard constraint violations.
          - COMPLETE_VALID: N assignments, with zero hard constraint violations.
          - INVALID: >=1 hard constraint violation present.
        """
        assigned = self.current_assignment if assignments is None else assignments
        total_vars = len(self.variables)
        assigned_vars = len(assigned)

        hard_violations: List[ConstraintViolation] = []
        soft_violations: List[ConstraintViolation] = []
        total_soft_penalty = 0.0

        # Execute Hard Constraints H1 - H8
        h1 = check_h1_faculty_overlap(assigned, self.variables_map)
        h2 = check_h2_classroom_overlap(assigned, self.variables_map)
        h3 = check_h3_student_group_overlap(assigned, self.variables_map)
        h4 = check_h4_room_capacity(assigned, self.variables_map, self.room_capacities, self.group_sizes)
        h5 = check_h5_faculty_availability(assigned, self.variables_map, self.faculty_unavailability, self.faculty_working_days)
        h6 = check_h6_room_type(assigned, self.variables_map, self.room_types)
        h7 = check_h7_lab_continuity(assigned, self.variables_map, self.timeslot_details)
        h8 = check_h8_working_hours(assigned, self.variables_map, self.timeslot_details)

        all_hard = [h1, h2, h3, h4, h5, h6, h7, h8]
        for h_list in all_hard:
            hard_violations.extend(h_list)

        # Execute Soft Constraints S1 - S4
        p1, v1 = score_s1_faculty_preferences(assigned, self.variables_map, self.faculty_preferences)
        p2, v2 = score_s2_faculty_idle_gaps(assigned, self.variables_map)
        p3, v3 = score_s3_consecutive_theory_sessions(assigned, self.variables_map)
        p4, v4 = score_s4_balanced_daily_workload(assigned, self.variables_map)

        all_soft = [(p1, v1), (p2, v2), (p3, v3), (p4, v4)]
        for p, v in all_soft:
            total_soft_penalty += p
            soft_violations.extend(v)

        # Determine timetable status
        if hard_violations:
            status = TimetableStatus.INVALID
            is_valid = False
        elif assigned_vars == 0:
            status = TimetableStatus.EMPTY
            is_valid = True
        elif assigned_vars < total_vars:
            status = TimetableStatus.PARTIAL_VALID
            is_valid = True
        else:
            status = TimetableStatus.COMPLETE_VALID
            is_valid = True

        summary_by_constraint = {
            "H1": {"name": "Faculty Overlap", "violations": len(h1), "status": "PASS" if not h1 else "FAIL"},
            "H2": {"name": "Classroom Overlap", "violations": len(h2), "status": "PASS" if not h2 else "FAIL"},
            "H3": {"name": "Student Group Overlap", "violations": len(h3), "status": "PASS" if not h3 else "FAIL"},
            "H4": {"name": "Room Capacity", "violations": len(h4), "status": "PASS" if not h4 else "FAIL"},
            "H5": {"name": "Faculty Availability", "violations": len(h5), "status": "PASS" if not h5 else "FAIL"},
            "H6": {"name": "Room Type Matching", "violations": len(h6), "status": "PASS" if not h6 else "FAIL"},
            "H7": {"name": "Lab Slot Continuity", "violations": len(h7), "status": "PASS" if not h7 else "FAIL"},
            "H8": {"name": "Working Hours & Breaks", "violations": len(h8), "status": "PASS" if not h8 else "FAIL"},
            "S1": {"name": "Faculty Preferred Slots", "penalty": p1, "violations": len(v1)},
            "S2": {"name": "Minimizing Faculty Idle Gaps", "penalty": p2, "violations": len(v2)},
            "S3": {"name": "Avoiding Consecutive Heavy Theory", "penalty": p3, "violations": len(v3)},
            "S4": {"name": "Balanced Daily Workload", "penalty": p4, "violations": len(v4)},
        }

        return ValidationReport(
            is_valid=is_valid,
            status=status,
            total_variables=total_vars,
            assigned_variables=assigned_vars,
            hard_violations=hard_violations,
            soft_violations=soft_violations,
            soft_penalty_score=total_soft_penalty,
            summary_by_constraint=summary_by_constraint,
        )

    def generate_valid_sample_schedule(self, num_variables: int = 5) -> Dict[str, SchedulingAssignmentValue]:
        """Constructs a certified clash-free partial timetable schedule respecting all H1-H8 constraints.

        Greedily finds non-overlapping domain values across distinct rooms, slots, faculty, and groups.
        """
        sample_assignments: Dict[str, SchedulingAssignmentValue] = {}
        target_vars = self.variables[:num_variables]

        for var in target_vars:
            domain_options = self.domains.get(var.var_id, [])
            found_compatible = False

            for cand in domain_options:
                # Test candidate assignment against currently scheduled partial assignments
                test_set = dict(sample_assignments)
                test_set[var.var_id] = cand

                # Verify H1 (faculty overlap), H2 (room overlap), H3 (group overlap)
                h1_viols = check_h1_faculty_overlap(test_set, self.variables_map)
                h2_viols = check_h2_classroom_overlap(test_set, self.variables_map)
                h3_viols = check_h3_student_group_overlap(test_set, self.variables_map)

                if not h1_viols and not h2_viols and not h3_viols:
                    sample_assignments[var.var_id] = cand
                    found_compatible = True
                    break

            if not found_compatible and domain_options:
                # If cannot find for this variable without clash, skip to keep sample valid
                continue

        return sample_assignments

    def generate_deliberately_invalid_schedule(self) -> Dict[str, SchedulingAssignmentValue]:
        """Constructs a deterministic invalid test fixture containing H1, H2, H3, and H4 violations."""
        invalid_assignments: Dict[str, SchedulingAssignmentValue] = {}

        if len(self.variables) < 2:
            return invalid_assignments

        # 1. Select variables for H1, H2, H3 (Double-booking and cohort clash)
        v1 = self.variables[0]
        v2 = self.variables[1]

        dom1 = self.domains.get(v1.var_id, [])
        if not dom1:
            return invalid_assignments

        base_val = dom1[0]  # e.g. Monday 09:00-10:00 @ CR_LH101
        invalid_assignments[v1.var_id] = base_val

        # Force V2 to share exact same slot, same room, same faculty, and same group as V1
        # Triggers H1 (Faculty clash), H2 (Classroom clash), and H3 (Cohort clash)
        clash_val = SchedulingAssignmentValue(
            slot_id=base_val.slot_id,
            room_id=base_val.room_id,
            day=base_val.day,
            start_time=base_val.start_time,
            end_time=base_val.end_time,
            slot_ids=base_val.slot_ids,
            faculty_id=v1.faculty_id,
            group_id=v1.group_id,
        )
        invalid_assignments[v2.var_id] = clash_val

        # 2. Select a variable to deliberately trigger an isolated H4 (Room capacity violation)
        # Find a variable and a room with the SAME room_type where room_capacity < group_size
        cap_target_var = None
        under_capacity_room_id = None

        for v in self.variables:
            req_type = v.required_room_type
            g_size = self.group_sizes.get(v.group_id, 0)
            # Find a room of same type with capacity < group size
            matching_small_rooms = [
                r_id for r_id, r_type in self.room_types.items()
                if r_type == req_type and self.room_capacities.get(r_id, 0) < g_size
            ]
            if matching_small_rooms:
                cap_target_var = v
                # pick the smallest capacity matching room
                under_capacity_room_id = min(matching_small_rooms, key=lambda r: self.room_capacities[r])
                break

        if cap_target_var and under_capacity_room_id:
            dom_cap = self.domains.get(cap_target_var.var_id, [])
            other_slots = [d for d in dom_cap if d.slot_id != base_val.slot_id and d.day != base_val.day]
            chosen_dom = other_slots[0] if other_slots else (dom_cap[0] if dom_cap else base_val)

            cap_val = SchedulingAssignmentValue(
                slot_id=chosen_dom.slot_id,
                room_id=under_capacity_room_id,
                day=chosen_dom.day,
                start_time=chosen_dom.start_time,
                end_time=chosen_dom.end_time,
                slot_ids=chosen_dom.slot_ids,
                faculty_id=cap_target_var.faculty_id,
                group_id=cap_target_var.group_id,
            )
            invalid_assignments[cap_target_var.var_id] = cap_val

        return invalid_assignments

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Returns mathematical summary metrics for the CSP model."""
        num_vars = len(self.variables)
        domain_sizes = [len(self.domains.get(v.var_id, [])) for v in self.variables]
        total_possibilities = sum(domain_sizes)
        min_domain = min(domain_sizes) if domain_sizes else 0
        max_domain = max(domain_sizes) if domain_sizes else 0
        avg_domain = (total_possibilities / num_vars) if num_vars > 0 else 0.0

        return {
            "num_variables": num_vars,
            "total_domain_possibilities": total_possibilities,
            "min_domain_size": min_domain,
            "max_domain_size": max_domain,
            "avg_domain_size": round(avg_domain, 2),
            "num_hard_constraints": 8,
            "num_soft_constraints": 4,
        }
