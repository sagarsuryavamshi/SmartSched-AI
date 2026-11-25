"""Dynamic Timetable Analytics Streamlit View.

Presents operational academic intelligence from actual SQLite database records
and current CSP optimization states:
- Classroom Utilization Percentage & Distribution
- Faculty Teaching Workload vs Max Weekly Capacity
- Daily Student Cohort Workload Balance
- Faculty Idle Gaps Analysis
- Soft Constraint Penalty Breakdown
"""

import pandas as pd
import streamlit as st

from src.csp_engine.model import CSPModel
from src.database.db_manager import DEFAULT_DB_PATH
from src.database.timetable_repository import load_saved_timetable
from src.evaluation.metrics import (
    calculate_timetable_analytics,
    create_faculty_workload_figure,
    create_room_utilization_figure,
    create_student_workload_figure,
)
from src.frontend.components import render_metric_card


def render_analytics_view() -> None:
    """Renders the comprehensive institutional timetable analytics dashboard."""
    st.markdown('<div class="main-header">Academic Timetable Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Operational intelligence, room utilization, and faculty workload calculated from active database records.</div>',
        unsafe_allow_html=True,
    )

    # Load real records from SQLite and CSP Model
    schedule_records = load_saved_timetable(db_path=DEFAULT_DB_PATH)
    if not schedule_records:
        st.warning("⚠️ No active timetable assignments found in database. Run and save a timetable first to inspect analytics.")
        return

    model = CSPModel.build_from_db(DEFAULT_DB_PATH)
    analytics = calculate_timetable_analytics(schedule_records, model, DEFAULT_DB_PATH)

    # 1. Executive Metric KPI Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_metric_card("Scheduled Sessions", f"{analytics['total_scheduled_sessions']} / {analytics['total_required_sessions']}", "📅")
    with m2:
        render_metric_card("Schedule Completeness", f"{analytics['completeness_percentage']}%", "🎯")
    with m3:
        render_metric_card("Classroom Utilization", f"{analytics['overall_classroom_utilization_pct']}%", "🏛️")
    with m4:
        render_metric_card("Total Booked Hours", f"{analytics['total_booked_hours']} hrs", "⏰")
    with m5:
        render_metric_card("Total Idle Gaps", f"{analytics['total_idle_gap_hours']} hrs", "⏳")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Interactive Charts: Classroom & Faculty
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        fig_room = create_room_utilization_figure(analytics)
        st.plotly_chart(fig_room, use_container_width=True)

    with c_chart2:
        fig_fac = create_faculty_workload_figure(analytics)
        st.plotly_chart(fig_fac, use_container_width=True)

    st.markdown("---")

    # 3. Daily Student Cohort Workload & Soft Constraint Penalties
    c_chart3, c_pen = st.columns([1.5, 1])
    with c_chart3:
        fig_grp = create_student_workload_figure(analytics)
        st.plotly_chart(fig_grp, use_container_width=True)

    with c_pen:
        st.markdown("#### ⚖️ Soft Constraint Penalty Breakdown")
        soft = analytics.get("soft_constraint_breakdown", {})
        st.markdown(f"- **Total Soft Penalty:** `{soft.get('total', 0.0):.1f}`")
        st.markdown(f"  - **[S1] Faculty Preferred Slots:** `{soft.get('S1', 0.0):.1f} pts`")
        st.markdown(f"  - **[S2] Faculty Idle Gaps:** `{soft.get('S2', 0.0):.1f} pts`")
        st.markdown(f"  - **[S3] Consecutive Theory Lectures:** `{soft.get('S3', 0.0):.1f} pts`")
        st.markdown(f"  - **[S4] Daily Student Load Balance:** `{soft.get('S4', 0.0):.1f} pts`")

        st.caption("Lower penalty scores indicate superior adherence to institutional preferences.")

    # 4. Detailed Breakdown Tables in Expanders
    with st.expander("📋 View Detailed Classroom Utilization Table", expanded=False):
        df_rooms_detail = pd.DataFrame([
            {
                "Classroom ID": r_id,
                "Name": data["name"],
                "Type": data["type"],
                "Seating Capacity": data["capacity"],
                "Booked Weekly Hours": data["booked_hours"],
                "Utilization Rate (%)": f"{data['utilization_pct']}%",
            }
            for r_id, data in analytics.get("room_utilization", {}).items()
        ])
        st.dataframe(df_rooms_detail, use_container_width=True, hide_index=True)

    with st.expander("👨‍🏫 View Detailed Faculty Workload Table", expanded=False):
        df_fac_detail = pd.DataFrame([
            {
                "Faculty ID": fid,
                "Name": data["name"],
                "Department": data["department"],
                "Assigned Hours": data["assigned_hours"],
                "Max Allowed Hours": data["max_hours"],
                "Capacity Used (%)": f"{data['utilization_pct']}%",
                "Teaching Days": data["days_active"],
                "Idle Window Gaps (hrs)": analytics.get("faculty_idle_gaps", {}).get(fid, 0),
            }
            for fid, data in analytics.get("faculty_workload", {}).items()
        ])
        st.dataframe(df_fac_detail, use_container_width=True, hide_index=True)
