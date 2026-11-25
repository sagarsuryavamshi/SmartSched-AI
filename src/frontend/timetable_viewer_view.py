"""Interactive Timetable Viewer Streamlit View.

Enables multi-angle institutional timetable visualization:
- Master Department View
- Faculty-Specific View
- Classroom-Specific View
- Student Group / Cohort View
Includes dynamic filtering, color-coded visual grid, and CSV / PDF downloads.
"""

import pandas as pd
import streamlit as st

from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection
from src.database.timetable_repository import load_saved_timetable
from src.frontend.components import render_metric_card
from src.utils.export_service import export_timetable_to_csv, export_timetable_to_pdf
from src.visualization.timetable_plots import create_timetable_grid_figure


def render_timetable_viewer_view() -> None:
    """Renders the comprehensive multi-view university timetable visualization."""
    st.markdown('<div class="main-header">University Timetable Schedule Matrix</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Interactive weekly schedules rendered from active SQLite records and CSP optimization engines.</div>',
        unsafe_allow_html=True,
    )

    # Load active schedule records from database
    schedule_records = load_saved_timetable(db_path=DEFAULT_DB_PATH)

    if not schedule_records:
        st.warning(
            "⚠️ **No saved timetable assignments found in SQLite.** "
            "Please generate and save a timetable from the **⚙️ CSP Solver Engine** or **🧬 Genetic Algorithm** panel."
        )
        return

    df_sched = pd.DataFrame(schedule_records)

    # 1. Top KPI Summary Strip
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        render_metric_card("Assigned Slots", str(len(schedule_records)), "📅")
    with kpi2:
        render_metric_card("Active Courses", str(len(df_sched["course_code"].unique())), "📖")
    with kpi3:
        render_metric_card("Faculty Active", str(len(df_sched["faculty_id"].unique())), "👨‍🏫")
    with kpi4:
        render_metric_card("Rooms Utilized", str(len(df_sched["room_id"].unique())), "🏛️")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. View Mode and Filtering Controls
    st.markdown("### 🎛️ Timetable Perspective & Filter Controls")
    c_view, c_filter, c_day = st.columns([1.5, 2, 1.5])

    with c_view:
        view_mode = st.selectbox(
            "Select Timetable Perspective",
            ["Department Master", "Faculty Timetable", "Classroom Timetable", "Student Cohort Timetable", "Course Timetable"],
        )

    with get_db_connection(DEFAULT_DB_PATH) as conn:
        faculty_df = pd.read_sql_query("SELECT faculty_id, name FROM faculty", conn)
        rooms_df = pd.read_sql_query("SELECT room_id, name, room_type FROM classrooms", conn)
        groups_df = pd.read_sql_query("SELECT group_id, name FROM student_groups", conn)
        courses_df = pd.read_sql_query("SELECT code, title FROM courses", conn)

    filter_entity_id = None
    filter_label = None

    with c_filter:
        if view_mode == "Faculty Timetable":
            fac_opts = faculty_df["faculty_id"].tolist()
            fac_map = dict(zip(faculty_df["faculty_id"], faculty_df["name"]))
            filter_entity_id = st.selectbox("Select Faculty Member", fac_opts, format_func=lambda x: f"{fac_map.get(x, x)} ({x})")
            filter_label = f"Faculty: {fac_map.get(filter_entity_id, filter_entity_id)}"
        elif view_mode == "Classroom Timetable":
            room_opts = rooms_df["room_id"].tolist()
            room_map = dict(zip(rooms_df["room_id"], rooms_df["name"]))
            filter_entity_id = st.selectbox("Select Classroom / Lab", room_opts, format_func=lambda x: f"{room_map.get(x, x)} ({x})")
            filter_label = f"Room: {room_map.get(filter_entity_id, filter_entity_id)}"
        elif view_mode == "Student Cohort Timetable":
            grp_opts = groups_df["group_id"].tolist()
            grp_map = dict(zip(groups_df["group_id"], groups_df["name"]))
            filter_entity_id = st.selectbox("Select Student Cohort", grp_opts, format_func=lambda x: f"{grp_map.get(x, x)} ({x})")
            filter_label = f"Cohort: {grp_map.get(filter_entity_id, filter_entity_id)}"
        elif view_mode == "Course Timetable":
            crs_opts = courses_df["code"].tolist()
            crs_map = dict(zip(courses_df["code"], courses_df["title"]))
            filter_entity_id = st.selectbox("Select Course", crs_opts, format_func=lambda x: f"{x} - {crs_map.get(x, x)}")
            filter_label = f"Course: {filter_entity_id}"
        else:
            st.info("🌐 Showing master institutional timetable across all departments and cohorts.")
            filter_label = "Department Master"

    with c_day:
        day_filter = st.selectbox("Filter by Specific Day", ["All Working Days", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])

    # Filter records by day if selected
    display_records = list(schedule_records)
    if day_filter != "All Working Days":
        display_records = [r for r in display_records if r.get("day") == day_filter]

    # Map perspective to plot internal view type
    view_type_map = {
        "Department Master": "Department",
        "Faculty Timetable": "Faculty",
        "Classroom Timetable": "Classroom",
        "Student Cohort Timetable": "Student Group",
        "Course Timetable": "Course",
    }
    internal_view = view_type_map.get(view_mode, "Department")

    # 3. Interactive Plotly Grid
    st.markdown("---")
    st.markdown(f"#### 📅 Weekly Schedule Matrix: {filter_label}")
    fig = create_timetable_grid_figure(
        schedule_records=display_records,
        view_type=internal_view,
        filter_entity_id=filter_entity_id,
    )
    st.plotly_chart(fig, use_container_width=True)

    # 4. Download Export Controls
    st.markdown("### 📥 Export & Share Timetables")
    col_dl1, col_dl2 = st.columns([1, 1])

    with col_dl1:
        csv_data = export_timetable_to_csv(display_records)
        st.download_button(
            label="📄 Download Timetable as CSV",
            data=csv_data,
            file_name=f"timetable_{internal_view.lower()}_{filter_entity_id or 'master'}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_dl2:
        pdf_data = export_timetable_to_pdf(
            schedule_records=display_records,
            title=f"University Academic Timetable ({view_mode})",
            filter_label=filter_label,
        )
        st.download_button(
            label="📑 Download Timetable as PDF",
            data=pdf_data,
            file_name=f"timetable_{internal_view.lower()}_{filter_entity_id or 'master'}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # 5. Tabular Data Inspection
    with st.expander("🔍 View Raw Schedule Tabular Records", expanded=False):
        filtered_df = pd.DataFrame(display_records)
        if not filtered_df.empty:
            cols_to_show = [c for c in ["day", "start_time", "end_time", "course_code", "course_title", "room_id", "faculty_name", "group_name"] if c in filtered_df.columns]
            st.dataframe(filtered_df[cols_to_show], use_container_width=True, hide_index=True)
