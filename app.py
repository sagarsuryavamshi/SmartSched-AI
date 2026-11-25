"""SmartSched AI - Main Streamlit Application Entrypoint.

Automated Timetable Generation using Constraint-Based Search (CSP).
"""

import os
import sys
import pandas as pd
import streamlit as st

# Ensure repository root is in python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection, init_db
from src.data_management.loader import load_dataset_summary, seed_synthetic_data
from src.frontend.components import apply_custom_styles, render_metric_card
from src.frontend.csp_formulation_view import render_csp_formulation_view
from src.frontend.csp_solver_view import render_csp_solver_view
from src.frontend.data_management_view import render_crud_data_management
from src.frontend.ga_view import render_ga_view
from src.frontend.timetable_viewer_view import render_timetable_viewer_view
from src.frontend.analytics_view import render_analytics_view
from src.frontend.what_if_rescheduling_view import render_what_if_rescheduling_view
from src.frontend.violation_inspector_view import render_violation_inspector_view
from src.frontend.workflow_view import render_optimization_workflow_view
from src.visualization.timetable_plots import create_timetable_grid_figure
from src.utils.logger import setup_logger

logger = setup_logger("smartsched.app")

# Page Configuration
st.set_page_config(
    page_title="SmartSched AI | Academic Timetable Generator",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    """Main application lifecycle controller."""
    apply_custom_styles()

    # Sidebar Navigation
    st.sidebar.image(
        "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=400&auto=format&fit=crop&q=80",
        caption="University AI Operations",
    )
    st.sidebar.title("SmartSched AI")
    st.sidebar.caption("Automated Timetable Generation using CSP & Heuristics")

    # Allow programmatic tab switching via session state
    if "nav_selection" in st.session_state:
        default_idx = [
            "🏛️ Admin Dashboard",
            "🎯 10-Step Optimization Wizard",
            "📚 Data Management",
            "⚙️ CSP Formulation & Model",
            "⚙️ CSP Solver Engine",
            "🧬 Genetic Algorithm & Benchmarking",
            "📊 Timetable Viewer",
            "📈 Timetable Analytics",
            "🔄 What-If Rescheduling",
            "🔍 Violation Inspector",
        ].index(st.session_state["nav_selection"]) if st.session_state["nav_selection"] in [
            "🏛️ Admin Dashboard",
            "🎯 10-Step Optimization Wizard",
            "📚 Data Management",
            "⚙️ CSP Formulation & Model",
            "⚙️ CSP Solver Engine",
            "🧬 Genetic Algorithm & Benchmarking",
            "📊 Timetable Viewer",
            "📈 Timetable Analytics",
            "🔄 What-If Rescheduling",
            "🔍 Violation Inspector",
        ] else 0
        del st.session_state["nav_selection"]
    else:
        default_idx = 0

    nav_selection = st.sidebar.radio(
        "Navigation",
        [
            "🏛️ Admin Dashboard",
            "🎯 10-Step Optimization Wizard",
            "📚 Data Management",
            "⚙️ CSP Formulation & Model",
            "⚙️ CSP Solver Engine",
            "🧬 Genetic Algorithm & Benchmarking",
            "📊 Timetable Viewer",
            "📈 Timetable Analytics",
            "🔄 What-If Rescheduling",
            "🔍 Violation Inspector",
        ],
        index=default_idx,
    )

    # Initialize DB & Seed data if needed
    init_db()
    summary = load_dataset_summary()
    if summary.get("classrooms", 0) == 0:
        seed_synthetic_data()
        summary = load_dataset_summary()

    # Sidebar quick stats
    st.sidebar.divider()
    st.sidebar.subheader("System Status")
    st.sidebar.markdown(f"**Database:** `SQLite ({os.path.basename(DEFAULT_DB_PATH)})`")
    st.sidebar.markdown(f"**Classrooms:** `{summary.get('classrooms', 0)}` | **Faculty:** `{summary.get('faculty', 0)}`")
    st.sidebar.markdown(f"**Courses:** `{summary.get('courses', 0)}` | **Slots:** `{summary.get('timeslots', 0)}`")
    st.sidebar.markdown("**Engine Status:** `Phase 6 Full Suite Active`")
    if st.sidebar.button("🔄 Reset to Synthetic Seed Data", use_container_width=True):
        seed_synthetic_data(overwrite=True)
        st.session_state.pop("csp_model", None)
        st.sidebar.success("Database restored to synthetic reference dataset!")
        st.rerun()

    # View Routing
    if nav_selection == "🏛️ Admin Dashboard":
        render_dashboard(summary)
    elif nav_selection == "🎯 10-Step Optimization Wizard":
        render_optimization_workflow_view()
    elif nav_selection == "📚 Data Management":
        render_crud_data_management()
    elif nav_selection == "⚙️ CSP Formulation & Model":
        render_csp_formulation_view()
    elif nav_selection == "⚙️ CSP Solver Engine":
        render_csp_solver_view()
    elif nav_selection == "🧬 Genetic Algorithm & Benchmarking":
        render_ga_view()
    elif nav_selection == "📊 Timetable Viewer":
        render_timetable_viewer_view()
    elif nav_selection == "📈 Timetable Analytics":
        render_analytics_view()
    elif nav_selection == "🔄 What-If Rescheduling":
        render_what_if_rescheduling_view()
    elif nav_selection == "🔍 Violation Inspector":
        render_violation_inspector_view()


def render_dashboard(summary: dict) -> None:
    """Renders the executive academic administration dashboard."""
    st.markdown('<div class="main-header">University Timetable Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Constraint Satisfaction Problem (CSP) & Metaheuristic Academic Timetable Scheduling System.</div>',
        unsafe_allow_html=True,
    )

    # Top Metric KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Classrooms & Labs", str(summary.get("classrooms", 0)), "🏛️")
    with col2:
        render_metric_card("Appointed Faculty", str(summary.get("faculty", 0)), "👨‍🏫")
    with col3:
        render_metric_card("Academic Courses", str(summary.get("courses", 0)), "📖")
    with col4:
        render_metric_card("Weekly Slots", str(summary.get("timeslots", 0)), "⏰")

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick Action Buttons
    st.subheader("⚡ Quick Operations Launcher")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("🎯 Launch 10-Step Wizard", use_container_width=True, type="primary"):
            st.session_state["nav_selection"] = "🎯 10-Step Optimization Wizard"
            st.rerun()
    with q2:
        if st.button("📊 View Active Timetable", use_container_width=True):
            st.session_state["nav_selection"] = "📊 Timetable Viewer"
            st.rerun()
    with q3:
        if st.button("🔄 What-If Rescheduling", use_container_width=True):
            st.session_state["nav_selection"] = "🔄 What-If Rescheduling"
            st.rerun()
    with q4:
        if st.button("🧬 Algorithm Benchmark", use_container_width=True):
            st.session_state["nav_selection"] = "🧬 Genetic Algorithm & Benchmarking"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Curricular Resource Allocations")
        with get_db_connection() as conn:
            courses_df = pd.read_sql_query(
                """
                SELECT c.code, c.title, c.weekly_hours, c.category, c.required_room_type,
                       COALESCE(f.name, 'Unassigned') AS instructor,
                       COALESCE(g.name, 'Unassigned') AS target_cohort
                FROM courses c
                LEFT JOIN faculty f ON c.assigned_faculty_id = f.faculty_id
                LEFT JOIN student_groups g ON c.target_group_id = g.group_id
                ORDER BY c.code
                """,
                conn,
            )
        st.dataframe(courses_df, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("Institutional Operational Status")
        st.info(
            """
            **Production Capabilities (Phase 7):**
            - ✅ Relational SQLite Database with Foreign Key Enforcement
            - ✅ Complete CRUD for Classrooms, Faculty, Groups, Courses, Slots
            - ✅ Formal CSP Model ($X, D, C$) with Pre-Filtered Domain Construction
            - ✅ 8 Hard Constraints ($H_1$–$H_8$) & 4 Soft Objectives ($S_1$–$S_4$)
            - ✅ Constraint Backtracking Solver (MRV, Degree, LCV, FC, AC-3)
            - ✅ Genetic Algorithm Optimizer with Domain-Aware Repair & Elitism
            - ✅ Multi-Perspective Interactive Plotly Weekly Schedule Matrix
            - ✅ Official Institutional Timetable Export (CSV & Landscape PDF)
            - ✅ What-If Rescheduling with Continuous 2-Hour Lab Block Selection
            - ✅ Transaction-Safe Database Auditing & Instant Rollback
            - ✅ Automated 10-Step Guided Optimization Wizard
            """
        )


def render_ga_comparison() -> None:
    """Renders the Genetic Algorithm comparison workbench."""
    st.markdown('<div class="main-header">Genetic Algorithm Benchmark Comparison</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Compare CSP constraint-based search against metaheuristic optimization.</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.slider("Population Size", min_value=20, max_value=300, value=100, step=10)
        st.slider("Generations", min_value=50, max_value=1000, value=250, step=50)
    with col2:
        st.slider("Crossover Probability", min_value=0.1, max_value=1.0, value=0.8, step=0.05)
        st.slider("Mutation Rate", min_value=0.01, max_value=0.3, value=0.05, step=0.01)

    st.button("🧬 Run Genetic Algorithm Baseline (Preview)", type="secondary")


def render_timetable_viewer() -> None:
    """Renders timetable schedule grid visualizer."""
    st.markdown('<div class="main-header">Weekly Timetable Matrix</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Visual matrix of scheduled lectures and laboratory sections.</div>',
        unsafe_allow_html=True,
    )

    with get_db_connection() as conn:
        groups_df = pd.read_sql_query("SELECT group_id, name FROM student_groups", conn)

    selected_group = st.selectbox(
        "Select Cohort / Student Group",
        options=groups_df["group_id"].tolist(),
        format_func=lambda x: groups_df[groups_df["group_id"] == x]["name"].values[0] if not groups_df.empty else x,
    )

    st.plotly_chart(create_timetable_grid_figure(), use_container_width=True)


def render_violation_inspector() -> None:
    """Renders constraint violation reporting and diagnostics."""
    st.markdown('<div class="main-header">Constraint Violation Diagnostics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Detailed analysis of hard conflicts and soft penalty trade-offs.</div>',
        unsafe_allow_html=True,
    )

    st.success("✅ Zero active constraint violations detected. Ready for schedule generation.")


if __name__ == "__main__":
    main()
