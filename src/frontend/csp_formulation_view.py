"""CSP Problem Formulation and Model Builder view for Streamlit."""

import pandas as pd
import streamlit as st

from src.csp_engine.domain_types import TimetableStatus
from src.csp_engine.model import CSPModel
from src.database.db_manager import DEFAULT_DB_PATH
from src.frontend.components import render_metric_card


def render_csp_formulation_view() -> None:
    """Renders the comprehensive CSP Problem Formulation UI with model builder and analytics."""
    st.markdown('<div class="main-header">CSP Problem Formulation & Model Builder</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Mathematically formulate university timetable generation as a discrete Constraint Satisfaction Problem (Variables, Domains, Hard Constraints H1-H8, Soft Objectives S1-S4).</div>',
        unsafe_allow_html=True,
    )

    # Top Control Bar
    col_desc, col_action = st.columns([3, 1])
    with col_desc:
        st.markdown(
            """
            This module dynamically extracts academic courses, instructor commitments, room specs, and weekly slots
            from SQLite and builds the formal CSP tuple: **$\\mathcal{P} = \\langle X, D, C_{\\text{hard}}, C_{\\text{soft}} \\rangle$**.
            """
        )
    with col_action:
        st.write("")
        build_clicked = st.button("🏗️ Build CSP Model", type="primary", use_container_width=True)

    # Build or retrieve CSP Model in Session State
    if build_clicked or "csp_model" not in st.session_state:
        with st.spinner("Compiling variables, computing domains, and initializing constraints from SQLite..."):
            model = CSPModel.build_from_db(DEFAULT_DB_PATH)
            st.session_state["csp_model"] = model
            st.session_state.pop("last_report", None)
            if build_clicked:
                st.success("✅ CSP Problem Model successfully compiled from live database records!")

    csp_model: CSPModel = st.session_state["csp_model"]
    stats = csp_model.get_summary_statistics()

    # KPI Metric Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_metric_card("Scheduling Variables (X)", str(stats["num_variables"]), "🧩")
    with k2:
        render_metric_card("Domain Space (|D|)", f"{stats['total_domain_possibilities']:,}", "🌐")
    with k3:
        render_metric_card("Hard Constraints", f"{stats['num_hard_constraints']} Rules", "🛡️")
    with k4:
        render_metric_card("Soft Objectives", f"{stats['num_soft_constraints']} Functions", "🎯")

    st.markdown("<br>", unsafe_allow_html=True)

    # Multi-tab deep dive
    tab_vars, tab_domains, tab_hard, tab_soft, tab_validation = st.tabs([
        "🧩 Scheduling Variables (X)",
        "🌐 Domain Possibilities (D)",
        "🛡️ Hard Constraints (H1-H8)",
        "🎯 Soft Constraints (S1-S4)",
        "🧪 Constraint Validation Engine",
    ])

    # 1. Variables Tab
    with tab_vars:
        st.subheader("Scheduling Variables Formulation")
        st.caption("Each variable represents an atomic lecture session (1 hour) or laboratory session (consecutive 2 hours).")

        var_records = []
        for v in csp_model.variables:
            var_records.append({
                "Variable ID": v.var_id,
                "Course Code": v.course_code,
                "Session": f"Session {v.session_num} of {v.total_sessions}",
                "Type": v.session_type.value,
                "Duration": f"{v.duration_hours} hour(s)",
                "Faculty ID": v.faculty_id,
                "Student Group": v.group_id,
                "Required Room Type": v.required_room_type,
                "Domain Size": len(csp_model.domains.get(v.var_id, [])),
            })
        df_vars = pd.DataFrame(var_records)
        st.dataframe(df_vars, use_container_width=True, hide_index=True)

    # 2. Domains Tab
    with tab_domains:
        st.subheader("Domain Definition & Pre-Filtering")
        st.caption("Assignments = (Timeslot, Classroom, Faculty, Student Group). Impossible slots are pre-filtered.")

        selected_var_id = st.selectbox(
            "Inspect Domain for Variable:",
            options=[v.var_id for v in csp_model.variables],
            format_func=lambda x: f"{x} ({csp_model.variables_map[x].course_code} - {csp_model.variables_map[x].session_type.value})",
        )

        domain_vals = csp_model.domains.get(selected_var_id, [])
        st.markdown(f"**Variable `{selected_var_id}` has `{len(domain_vals)}` valid assignment options:**")

        if domain_vals:
            domain_records = []
            for d in domain_vals[:50]:  # Show top 50 in table
                domain_records.append({
                    "Day": d.day,
                    "Start Time": d.start_time,
                    "End Time": d.end_time,
                    "Room ID": d.room_id,
                    "Occupied Slot IDs": ", ".join(d.slot_ids),
                })
            df_dom = pd.DataFrame(domain_records)
            st.dataframe(df_dom, use_container_width=True, hide_index=True)
            if len(domain_vals) > 50:
                st.caption(f"Showing first 50 of {len(domain_vals)} total domain candidates.")
        else:
            st.warning("⚠️ Domain is empty! This variable has no valid assignment options with current constraints.")

    # 3. Hard Constraints Tab
    with tab_hard:
        st.subheader("Hard Constraint Formulations (Strict Invariants)")
        st.markdown(
            """
            | ID | Name | Mathematical Rule | Enforcement Method |
            | :--- | :--- | :--- | :--- |
            | **H1** | **Faculty Double-Booking** | $\\forall i \\neq j, f(v_i) = f(v_j) \\implies \\text{slot}(v_i) \\cap \\text{slot}(v_j) = \\emptyset$ | Pairwise clash checker & Forward Checking |
            | **H2** | **Classroom Double-Booking** | $\\forall i \\neq j, r(v_i) = r(v_j) \\implies \\text{slot}(v_i) \\cap \\text{slot}(v_j) = \\emptyset$ | Pairwise clash checker & Forward Checking |
            | **H3** | **Student Group Clash** | $\\forall i \\neq j, g(v_i) = g(v_j) \\implies \\text{slot}(v_i) \\cap \\text{slot}(v_j) = \\emptyset$ | Cohort concurrency checker |
            | **H4** | **Room Capacity** | $\\forall v_i, \\text{capacity}(r(v_i)) \\ge \\text{size}(g(v_i))$ | Domain pre-filtering & assignment validation |
            | **H5** | **Faculty Availability** | $\\forall v_i, \\text{slot}(v_i) \\cap \\text{unavail}(f(v_i)) = \\emptyset \\land \\text{day}(v_i) \\in \\text{days}(f(v_i))$ | Pre-filtering & availability validator |
            | **H6** | **Room Type Matching** | $\\forall v_i, \\text{type}(r(v_i)) = \\text{type}(v_i)$ | Facility compatibility filter |
            | **H7** | **Laboratory Continuity** | $\\forall v_{\\text{lab}}, \\text{continuous}(\\text{slot}_1, \\text{slot}_2)$ | Consecutive contiguous slot validator |
            | **H8** | **Working Hours & Breaks** | $\\forall v_i, \\text{slot}(v_i) \\notin \\text{RecessPeriods} \\land \\text{valid}(\\text{slot})$ | Operational schedule domain filter |
            """
        )

    # 4. Soft Constraints Tab
    with tab_soft:
        st.subheader("Soft Constraint Optimization Objectives")
        st.markdown(
            """
            | ID | Objective Name | Penalty Description | Weight / Impact |
            | :--- | :--- | :--- | :--- |
            | **S1** | **Faculty Preferred Slots** | Penalizes scheduling instructors outside their preferred intervals (or late afternoon) | $+5.0$ to $+10.0$ pts |
            | **S2** | **Minimize Faculty Idle Gaps** | Penalizes disjoint daily schedules with idle gaps $>60$ minutes between lectures | $+8.0$ pts per 30m idle |
            | **S3** | **Avoid Heavy Theory Run** | Penalizes student cohorts scheduled for $\\ge 3$ consecutive 1-hour theory lectures | $+15.0$ pts per extra hr |
            | **S4** | **Balanced Daily Workload** | Penalizes student days overloaded with $>4$ hours or under-utilized with 1 hour | $+6.0$ to $+12.0$ pts |
            """
        )

    # 5. Validation Tab
    with tab_validation:
        st.subheader("Timetable Constraint Validation Engine")
        st.caption("Validates proposed partial or complete timetable states and reports structured diagnostic violations.")

        col_v1, col_v2 = st.columns([1, 1])
        with col_v1:
            st.markdown("#### Test Scenario Selection")
            scenario = st.radio(
                "Choose timetable state to evaluate:",
                [
                    "Empty Timetable State (Unassigned)",
                    "Valid Sample Schedule (Conflict-Free Subset)",
                    "Deliberately Invalid Schedule (Double-Booking & Capacity Violation)",
                ],
            )
            run_eval = st.button("🔍 Run Constraint Evaluator", type="primary", use_container_width=True)

        with col_v2:
            st.markdown("#### Evaluation Results")
            if run_eval or "last_report" in st.session_state:
                # Generate sample assignments based on selected scenario
                sample_assignments = {}
                if scenario == "Valid Sample Schedule (Conflict-Free Subset)":
                    sample_assignments = csp_model.generate_valid_sample_schedule(num_variables=5)
                elif scenario == "Deliberately Invalid Schedule (Double-Booking & Capacity Violation)":
                    sample_assignments = csp_model.generate_deliberately_invalid_schedule()
                else:
                    sample_assignments = {}

                report = csp_model.validate_assignments(sample_assignments)
                st.session_state["last_report"] = report

                # Render unambiguous timetable state badges
                if report.status == TimetableStatus.EMPTY:
                    st.info("ℹ️ **TIMETABLE STATE: EMPTY** — No sessions currently scheduled (0 variables assigned). Ready for scheduling.")
                elif report.status == TimetableStatus.PARTIAL_VALID:
                    st.success(f"🟡 **TIMETABLE STATE: PARTIAL (CONSTRAINT-VALID)** — {report.assigned_variables}/{report.total_variables} sessions assigned with zero hard constraint violations!")
                elif report.status == TimetableStatus.COMPLETE_VALID:
                    st.success(f"🟢 **TIMETABLE STATE: COMPLETE VALID SCHEDULE** — All {report.total_variables}/{report.total_variables} sessions assigned with zero hard violations!")
                elif report.status == TimetableStatus.INVALID:
                    st.error(f"❌ **TIMETABLE STATE: INVALID** — {len(report.hard_violations)} Hard Constraint Violation(s) detected across {report.assigned_variables} assigned sessions!")

                st.markdown(f"**Assigned Sessions:** `{report.assigned_variables} / {report.total_variables}`")
                st.markdown(f"**Soft Constraint Penalty Score:** `{report.soft_penalty_score:.1f}`")

                # Constraint summary checklist
                st.markdown("##### Constraint Verification Checklist")
                col_c1, col_c2 = st.columns(2)
                summary_items = list(report.summary_by_constraint.items())
                with col_c1:
                    for cid, meta in summary_items[:6]:
                        status_icon = "✅" if meta.get("violations", 0) == 0 else "❌"
                        st.markdown(f"{status_icon} **[{cid}] {meta['name']}**: `{meta.get('violations', 0)}` violation(s)")
                with col_c2:
                    for cid, meta in summary_items[6:]:
                        if "penalty" in meta:
                            st.markdown(f"🎯 **[{cid}] {meta['name']}**: Penalty `{meta['penalty']:.1f}` ({meta['violations']} notice(s))")
                        else:
                            status_icon = "✅" if meta.get("violations", 0) == 0 else "❌"
                            st.markdown(f"{status_icon} **[{cid}] {meta['name']}**: `{meta.get('violations', 0)}` violation(s)")

                if report.hard_violations:
                    st.markdown("##### 🚨 Hard Constraint Violations")
                    for hv in report.hard_violations:
                        st.error(f"**[{hv.constraint_id}] {hv.constraint_name}** | Affected: `{hv.violating_var_ids}`\n\n{hv.explanation}")

                if report.soft_violations:
                    with st.expander(f"⚠️ Soft Constraint Optimization Notices ({len(report.soft_violations)} items)"):
                        for sv in report.soft_violations:
                            st.warning(f"**[{sv.constraint_id}] {sv.constraint_name}** | Affected: `{sv.violating_var_ids}`\n\n{sv.explanation}")
