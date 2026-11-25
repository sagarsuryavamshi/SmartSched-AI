"""CSP Solver Engine view for Streamlit.

Allows interactive configuration of MRV, Degree, LCV, Forward Checking, and AC-3,
triggers live timetable generation, displays execution telemetry, and supports timetable saving.
"""

from typing import Optional
import pandas as pd
import streamlit as st

from src.csp_engine.model import CSPModel
from src.csp_engine.solver import CSPSolver
from src.csp_engine.solver_types import SolverConfig, SolverResult, SolverStatus
from src.database.db_manager import DEFAULT_DB_PATH
from src.database.timetable_repository import load_saved_timetable, save_timetable_solution
from src.frontend.components import render_metric_card


def render_csp_solver_view() -> None:
    """Renders the comprehensive interactive CSP Solver control panel and live execution telemetry."""
    st.markdown('<div class="main-header">CSP Search Engine & Timetable Generator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Automated conflict-free academic schedule generation using Backtracking Search, MRV, Degree Heuristic, LCV, Forward Checking, and AC-3.</div>',
        unsafe_allow_html=True,
    )

    # Section A: Solver Configuration & Controls
    st.markdown("### ⚙️ Solver Heuristic Configuration")
    st.caption("Configure constraint propagation, variable ordering, and search limits. Defaults enable full optimization.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Variable & Value Selection**")
        use_mrv = st.checkbox("Minimum Remaining Values (MRV)", value=True, help="Chooses variable with smallest current legal domain (fail-first).")
        use_degree = st.checkbox("Degree Heuristic Tie-Breaker", value=True, help="Breaks MRV ties choosing variable with most unassigned neighbors.")
        use_lcv = st.checkbox("Least Constraining Value (LCV)", value=True, help="Orders domain values by least eliminations in neighbor domains.")

    with c2:
        st.markdown("**Constraint Propagation**")
        use_fc = st.checkbox("Forward Checking (FC)", value=True, help="Prunes inconsistent values from neighbor domains upon assignment.")
        use_ac3 = st.checkbox("AC-3 Preprocessing", value=True, help="Enforces initial binary arc consistency across the constraint graph.")
        use_inc_ac3 = st.checkbox("Incremental AC-3 during search", value=False, help="Runs AC-3 propagation after each variable assignment.")

    with c3:
        st.markdown("**Search Budgets**")
        max_nodes = st.number_input("Max Search Nodes", min_value=100, max_value=500000, value=50000, step=5000)
        timeout = st.number_input("Timeout (Seconds)", min_value=1.0, max_value=300.0, value=30.0, step=5.0)

    config = SolverConfig(
        use_mrv=use_mrv,
        use_degree=use_degree,
        use_lcv=use_lcv,
        use_forward_checking=use_fc,
        use_ac3_preprocess=use_ac3,
        use_incremental_ac3=use_inc_ac3,
        max_search_nodes=int(max_nodes),
        timeout_seconds=float(timeout),
    )

    st.markdown("---")

    # Section B: Generate Timetable Action
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        generate_clicked = st.button("🚀 Generate Conflict-Free Timetable", type="primary", use_container_width=True)
    with col_info:
        st.caption("Extracts real academic entities from SQLite, builds variables and domains, runs the constraint solver, and verifies all H1-H8 constraints.")

    if generate_clicked:
        with st.spinner("Compiling CSP problem and executing constraint-based search..."):
            model = CSPModel.build_from_db(DEFAULT_DB_PATH)
            solver = CSPSolver(model)
            result = solver.solve(config)
            st.session_state["solver_result"] = result
            st.session_state["solver_model"] = model

    solver_res: Optional[SolverResult] = st.session_state.get("solver_result")
    solver_model: Optional[CSPModel] = st.session_state.get("solver_model")

    if solver_res is None:
        st.info("💡 Click **'Generate Conflict-Free Timetable'** above to start the constraint satisfaction search.")
        return

    # Section C & D: Execution Telemetry and Solution Status
    st.markdown("### 📊 Search Execution Telemetry & Statistics")
    stats = solver_res.statistics

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_metric_card("Status", solver_res.status.value, "🎯")
    with k2:
        render_metric_card("Nodes Explored", f"{stats.nodes_explored:,}", "🔍")
    with k3:
        render_metric_card("Backtracks", str(stats.backtracks), "↩️")
    with k4:
        render_metric_card("Constraint Checks", f"{stats.constraint_checks:,}", "⚖️")
    with k5:
        render_metric_card("Runtime", f"{stats.execution_time_seconds:.3f}s", "⚡")

    st.markdown("<br>", unsafe_allow_html=True)

    # Secondary Telemetry row
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.metric("Successful Assignments", f"{stats.successful_assignments:,}")
    with t2:
        st.metric("Domain Reductions", f"{stats.domain_reductions:,}")
    with t3:
        st.metric("AC-3 Arcs Processed", f"{stats.ac3_arcs_processed:,}")
    with t4:
        st.metric("Max Search Depth", f"{stats.max_depth_reached}")

    st.markdown("---")

    # Section E: Outcome Reporting (Success vs Failure)
    if solver_res.is_solution_found and solver_res.status == SolverStatus.SUCCESS:
        st.success(f"🎉 **{solver_res.message}**")

        report = solver_res.validation_report
        col_res1, col_res2 = st.columns([1, 1])

        with col_res1:
            st.markdown("#### Solution Quality Summary")
            st.markdown(f"- **Total Variables Assigned:** `{len(solver_res.assignment)} / {len(solver_model.variables)}`")
            st.markdown(f"- **Hard Constraint Violations:** `0 (Strictly Valid)`")
            if report:
                st.markdown(f"- **Total Soft Penalty Score:** `{report.soft_penalty_score:.1f}`")
                st.markdown(f"  - S1 (Faculty Preferred Slots): `Penalty {report.summary_by_constraint['S1']['penalty']:.1f}`")
                st.markdown(f"  - S2 (Faculty Idle Gaps): `Penalty {report.summary_by_constraint['S2']['penalty']:.1f}`")
                st.markdown(f"  - S3 (Consecutive Theory Lectures): `Penalty {report.summary_by_constraint['S3']['penalty']:.1f}`")
                st.markdown(f"  - S4 (Daily Student Workload): `Penalty {report.summary_by_constraint['S4']['penalty']:.1f}`")

        with col_res2:
            st.markdown("#### Timetable Persistence")
            st.write("Persist this verified schedule to the SQLite database for official institutional deployment.")
            save_clicked = st.button("💾 Save Timetable to Database", type="secondary", use_container_width=True)

            if save_clicked:
                ok, msg = save_timetable_solution(
                    assignment=solver_res.assignment,
                    variables_map=solver_model.variables_map,
                    overwrite_existing=True,
                )
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

        # Timetable assignment table
        st.markdown("#### Generated Timetable Schedule Matrix")
        schedule_rows = []
        for v_id, val in solver_res.assignment.items():
            var = solver_model.variables_map.get(v_id)
            if var:
                schedule_rows.append({
                    "Course": f"{var.course_code} - {var.session_type.value}",
                    "Session": f"Session {var.session_num}",
                    "Day": val.day,
                    "Time": f"{val.start_time} - {val.end_time}",
                    "Room": val.room_id,
                    "Instructor": val.faculty_id,
                    "Student Cohort": val.group_id,
                    "Slot ID(s)": ", ".join(val.slot_ids),
                })

        df_sched = pd.DataFrame(schedule_rows)
        # Order chronologically
        day_order = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}
        df_sched["day_num"] = df_sched["Day"].map(day_order)
        df_sched.sort_values(by=["day_num", "Time"], inplace=True)
        df_sched.drop(columns=["day_num"], inplace=True)
        st.dataframe(df_sched, use_container_width=True, hide_index=True)

    else:
        # Failure Reporting (Module 8E)
        st.error(f"❌ **Search Failed: {solver_res.status.value}**")
        st.markdown(f"**Diagnostic Details:** {solver_res.message}")
        if stats.dead_ends > 0:
            st.warning(f"⚠️ Search encountered {stats.dead_ends:,} dead-end states requiring complete backtracking.")
        if solver_res.status == SolverStatus.NODE_LIMIT_REACHED:
            st.info("Tip: Increase 'Max Search Nodes' in the configuration panel above to permit deeper search exploration.")
        elif solver_res.status == SolverStatus.TIMEOUT:
            st.info("Tip: Increase 'Timeout (Seconds)' in the configuration panel above.")
