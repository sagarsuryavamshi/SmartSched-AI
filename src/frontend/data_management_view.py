"""Comprehensive CRUD Data Management View for SmartSched AI."""

import json
from typing import List
import pandas as pd
import streamlit as st

from src.data_management.crud_services import (
    create_classroom,
    create_course,
    create_faculty,
    create_student_group,
    create_timeslot,
    delete_classroom,
    delete_course,
    delete_faculty,
    delete_student_group,
    delete_timeslot,
    get_all_classrooms,
    get_all_courses,
    get_all_faculty,
    get_all_student_groups,
    get_all_timeslots,
    get_classroom_by_id,
    get_course_by_id,
    get_faculty_by_id,
    get_student_group_by_id,
    get_timeslot_by_id,
    update_classroom,
    update_course,
    update_faculty,
    update_student_group,
    update_timeslot,
)


def render_crud_data_management() -> None:
    """Renders the comprehensive multi-entity CRUD administrative panel."""
    st.markdown('<div class="main-header">Academic Data Operations & CSP Setup</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Add, edit, inspect, and safely manage classrooms, faculty availability, student cohorts, courses, and time slots.</div>',
        unsafe_allow_html=True,
    )

    tab_rooms, tab_faculty, tab_groups, tab_courses, tab_slots = st.tabs([
        "🏛️ Classrooms",
        "👨‍🏫 Faculty & Availability",
        "🎓 Student Groups",
        "📖 Courses & Curricula",
        "⏰ Time Slots & Breaks",
    ])

    with tab_rooms:
        _render_classrooms_crud()

    with tab_faculty:
        _render_faculty_crud()

    with tab_groups:
        _render_groups_crud()

    with tab_courses:
        _render_courses_crud()

    with tab_slots:
        _render_timeslots_crud()


# ============================================================================
# 1. CLASSROOMS CRUD TAB
# ============================================================================

def _render_classrooms_crud() -> None:
    st.subheader("Classrooms & Laboratories")
    st.caption("Manage instructional venues, seating capacities, and equipment requirements for CSP room matching.")

    # Search & Action Header
    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Classrooms", placeholder="Search by ID, name, room type, features...", key="cls_search")
    with col_btn:
        st.write("")
        st.write("")
        show_add = st.button("➕ Add New Classroom", use_container_width=True, type="primary")

    # Add Classroom Form / Expander
    if show_add or st.session_state.get("show_add_classroom", False):
        st.session_state["show_add_classroom"] = True
        with st.form("form_add_classroom", clear_on_submit=False):
            st.markdown("#### Register New Classroom or Lab")
            c1, c2 = st.columns(2)
            with c1:
                r_id = st.text_input("Room ID * (e.g. CR_LH104)", placeholder="CR_LH104").strip()
                r_name = st.text_input("Room Name *", placeholder="Lecture Hall 104").strip()
                r_capacity = st.number_input("Capacity (Seats) *", min_value=1, max_value=500, value=60, step=5)
            with c2:
                r_type = st.selectbox("Room Type *", ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"])
                r_features = st.text_area("Features & Equipment", placeholder="Projector, High-End Workstations, Audio...")

            fc1, fc2 = st.columns([1, 1])
            with fc1:
                submitted = st.form_submit_button("Save Classroom", use_container_width=True, type="primary")
            with fc2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                success, msg = create_classroom(r_id, r_name, int(r_capacity), r_type, r_features)
                if success:
                    st.success(f"✅ {msg}")
                    st.session_state["show_add_classroom"] = False
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            if cancelled:
                st.session_state["show_add_classroom"] = False
                st.rerun()

    # Data Table
    classrooms = get_all_classrooms(search_query)
    if classrooms:
        df_rooms = pd.DataFrame(classrooms)
        st.dataframe(df_rooms, use_container_width=True, hide_index=True)
    else:
        st.info("No classrooms found matching search criteria.")
        return

    # Edit & Delete Sub-panel
    st.markdown("---")
    st.markdown("##### ✏️ Modify or Delete Classroom")
    room_options = {r["room_id"]: f"{r['room_id']} - {r['name']} ({r['room_type']}, {r['capacity']} seats)" for r in classrooms}
    selected_room_id = st.selectbox("Select Classroom to manage", options=list(room_options.keys()), format_func=lambda x: room_options[x], key="select_room_manage")

    col_edit_view, col_del_view = st.columns([2, 1])

    with col_edit_view:
        current_room = get_classroom_by_id(selected_room_id)
        if current_room:
            with st.form("form_edit_classroom"):
                st.markdown(f"**Editing: `{current_room['room_id']}`**")
                e1, e2 = st.columns(2)
                with e1:
                    edit_name = st.text_input("Room Name", value=current_room["name"])
                    edit_cap = st.number_input("Capacity", min_value=1, max_value=500, value=int(current_room["capacity"]), step=5)
                with e2:
                    current_idx = ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"].index(current_room["room_type"]) if current_room["room_type"] in ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"] else 0
                    edit_type = st.selectbox("Room Type", ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"], index=current_idx)
                    edit_features = st.text_input("Features", value=current_room["features"] or "")

                if st.form_submit_button("Update Classroom Details", use_container_width=True, type="primary"):
                    success, msg = update_classroom(selected_room_id, edit_name, int(edit_cap), edit_type, edit_features)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    with col_del_view:
        st.markdown(f"**Delete Safety Zone**")
        st.caption(f"Permanently remove `{selected_room_id}`. Deletion is automatically blocked if linked to active schedules.")
        if st.button(f"🗑️ Delete `{selected_room_id}`", type="secondary", use_container_width=True):
            success, msg = delete_classroom(selected_room_id)
            if success:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


# ============================================================================
# 2. FACULTY & AVAILABILITY CRUD TAB
# ============================================================================

def _render_faculty_crud() -> None:
    st.subheader("Faculty Members & Availability Constraints")
    st.caption("Manage professors, maximum teaching load, allowed days, and unavailable timeslots for CSP search.")

    # Lookup all timeslots for availability selection
    all_slots = get_all_timeslots()
    slot_id_map = {s["slot_id"]: f"{s['slot_id']} ({s['day']} {s['start_time']}-{s['end_time']})" for s in all_slots}
    all_courses = get_all_courses()
    course_codes = [c["code"] for c in all_courses]
    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Faculty", placeholder="Search by ID, name, email, department...", key="fac_search")
    with col_btn:
        st.write("")
        st.write("")
        show_add = st.button("➕ Add Faculty Member", use_container_width=True, type="primary")

    if show_add or st.session_state.get("show_add_faculty", False):
        st.session_state["show_add_faculty"] = True
        with st.form("form_add_faculty", clear_on_submit=False):
            st.markdown("#### Register New Faculty Member")
            f1, f2 = st.columns(2)
            with f1:
                f_id = st.text_input("Faculty ID * (e.g. FAC_MARVIN)", placeholder="FAC_MARVIN").strip()
                f_name = st.text_input("Full Name *", placeholder="Prof. Marvin Minsky").strip()
                f_email = st.text_input("Email *", placeholder="m.minsky@university.edu").strip()
                f_dept = st.text_input("Department", value="Computer Science").strip()
            with f2:
                f_max_hours = st.number_input("Max Weekly Teaching Hours", min_value=1, max_value=40, value=16)
                f_days = st.multiselect("Available Working Days", options=all_days, default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
                f_qual = st.multiselect("Qualified Course Codes", options=course_codes, default=[])
                f_unavail = st.multiselect("Explicitly Unavailable Slots", options=list(slot_id_map.keys()), format_func=lambda x: slot_id_map.get(x, x))

            btn1, btn2 = st.columns([1, 1])
            with btn1:
                submitted = st.form_submit_button("Register Faculty", use_container_width=True, type="primary")
            with btn2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                success, msg = create_faculty(
                    faculty_id=f_id,
                    name=f_name,
                    email=f_email,
                    department=f_dept,
                    max_weekly_hours=int(f_max_hours),
                    available_days=f_days,
                    qualified_courses=f_qual,
                    unavailable_slots=f_unavail,
                )
                if success:
                    st.success(f"✅ {msg}")
                    st.session_state["show_add_faculty"] = False
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            if cancelled:
                st.session_state["show_add_faculty"] = False
                st.rerun()

    faculty_list = get_all_faculty(search_query)
    if faculty_list:
        display_data = []
        for f in faculty_list:
            display_data.append({
                "Faculty ID": f["faculty_id"],
                "Name": f["name"],
                "Department": f.get("department", "Computer Science"),
                "Email": f["email"],
                "Max Hours": f["max_weekly_hours"],
                "Available Days": ", ".join(f.get("available_days_list", [])),
                "Unavailable Slots": ", ".join(f.get("unavailable_slots_list", [])) or "None",
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)
    else:
        st.info("No faculty records found.")
        return

    st.markdown("---")
    st.markdown("##### ✏️ Modify or Delete Faculty Member")
    faculty_options = {f["faculty_id"]: f"{f['faculty_id']} - {f['name']} ({f.get('department', 'CS')})" for f in faculty_list}
    selected_fac_id = st.selectbox("Select Faculty to manage", options=list(faculty_options.keys()), format_func=lambda x: faculty_options[x], key="select_fac_manage")

    col_edit_view, col_del_view = st.columns([2, 1])
    with col_edit_view:
        curr = get_faculty_by_id(selected_fac_id)
        if curr:
            with st.form("form_edit_faculty"):
                st.markdown(f"**Editing: `{curr['faculty_id']}`**")
                ef1, ef2 = st.columns(2)
                with ef1:
                    edit_name = st.text_input("Name", value=curr["name"])
                    edit_email = st.text_input("Email", value=curr["email"])
                    edit_dept = st.text_input("Department", value=curr.get("department", "Computer Science"))
                with ef2:
                    edit_hours = st.number_input("Max Weekly Hours", min_value=1, max_value=40, value=int(curr["max_weekly_hours"]))
                    edit_days = st.multiselect("Available Days", options=all_days, default=curr.get("available_days_list", []))
                    edit_qual = st.multiselect("Qualified Courses", options=course_codes, default=[c for c in curr.get("qualified_courses_list", []) if c in course_codes])
                    edit_unavail = st.multiselect("Unavailable Slots", options=list(slot_id_map.keys()), default=[s for s in curr.get("unavailable_slots_list", []) if s in slot_id_map], format_func=lambda x: slot_id_map.get(x, x))

                if st.form_submit_button("Update Faculty Information", use_container_width=True, type="primary"):
                    success, msg = update_faculty(
                        faculty_id=selected_fac_id,
                        name=edit_name,
                        email=edit_email,
                        department=edit_dept,
                        max_weekly_hours=int(edit_hours),
                        available_days=edit_days,
                        qualified_courses=edit_qual,
                        unavailable_slots=edit_unavail,
                    )
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    with col_del_view:
        st.markdown("**Delete Safety Zone**")
        st.caption(f"Safely remove `{selected_fac_id}`. Deletion is blocked if this instructor is assigned to courses or timetables.")
        if st.button(f"🗑️ Delete `{selected_fac_id}`", type="secondary", use_container_width=True):
            success, msg = delete_faculty(selected_fac_id)
            if success:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


# ============================================================================
# 3. STUDENT GROUPS CRUD TAB
# ============================================================================

def _render_groups_crud() -> None:
    st.subheader("Student Cohorts & Batches")
    st.caption("Manage student batches, enrollment sizes, and programs for classroom capacity validation in CSP.")

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Student Groups", placeholder="Search by ID, name, department, program...", key="grp_search")
    with col_btn:
        st.write("")
        st.write("")
        show_add = st.button("➕ Add Student Group", use_container_width=True, type="primary")

    if show_add or st.session_state.get("show_add_group", False):
        st.session_state["show_add_group"] = True
        with st.form("form_add_group", clear_on_submit=False):
            st.markdown("#### Register New Student Cohort")
            g1, g2 = st.columns(2)
            with g1:
                g_id = st.text_input("Group ID * (e.g. GRP_DS_SEM3)", placeholder="GRP_DS_SEM3").strip()
                g_name = st.text_input("Group Name *", placeholder="Data Science Batch 2024 (Semester 3)").strip()
                g_dept = st.text_input("Department", value="Computer Science").strip()
            with g2:
                g_size = st.number_input("Student Count (Size) *", min_value=1, max_value=300, value=50, step=5)
                g_prog = st.text_input("Program", value="B.Tech Computer Science").strip()
                g_sem = st.number_input("Semester", min_value=1, max_value=12, value=3)

            btn1, btn2 = st.columns([1, 1])
            with btn1:
                submitted = st.form_submit_button("Save Student Group", use_container_width=True, type="primary")
            with btn2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                success, msg = create_student_group(g_id, g_name, g_dept, int(g_size), g_prog, int(g_sem))
                if success:
                    st.success(f"✅ {msg}")
                    st.session_state["show_add_group"] = False
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            if cancelled:
                st.session_state["show_add_group"] = False
                st.rerun()

    groups_list = get_all_student_groups(search_query)
    if groups_list:
        st.dataframe(pd.DataFrame(groups_list), use_container_width=True, hide_index=True)
    else:
        st.info("No student groups found.")
        return

    st.markdown("---")
    st.markdown("##### ✏️ Modify or Delete Student Group")
    group_options = {g["group_id"]: f"{g['group_id']} - {g['name']} ({g['size']} students, Sem {g['semester']})" for g in groups_list}
    selected_grp_id = st.selectbox("Select Student Group to manage", options=list(group_options.keys()), format_func=lambda x: group_options[x], key="select_grp_manage")

    col_edit_view, col_del_view = st.columns([2, 1])
    with col_edit_view:
        curr = get_student_group_by_id(selected_grp_id)
        if curr:
            with st.form("form_edit_group"):
                st.markdown(f"**Editing: `{curr['group_id']}`**")
                eg1, eg2 = st.columns(2)
                with eg1:
                    edit_name = st.text_input("Name", value=curr["name"])
                    edit_dept = st.text_input("Department", value=curr.get("department", "Computer Science"))
                    edit_size = st.number_input("Student Count", min_value=1, max_value=300, value=int(curr["size"]), step=5)
                with eg2:
                    edit_prog = st.text_input("Program", value=curr["program"])
                    edit_sem = st.number_input("Semester", min_value=1, max_value=12, value=int(curr["semester"]))

                if st.form_submit_button("Update Student Group", use_container_width=True, type="primary"):
                    success, msg = update_student_group(selected_grp_id, edit_name, edit_dept, int(edit_size), edit_prog, int(edit_sem))
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    with col_del_view:
        st.markdown("**Delete Safety Zone**")
        st.caption(f"Remove `{selected_grp_id}`. Blocked if courses or schedules are mapped to this cohort.")
        if st.button(f"🗑️ Delete `{selected_grp_id}`", type="secondary", use_container_width=True):
            success, msg = delete_student_group(selected_grp_id)
            if success:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


# ============================================================================
# 4. COURSES CRUD TAB
# ============================================================================

def _render_courses_crud() -> None:
    st.subheader("Academic Courses & Curriculum Requirements")
    st.caption("Define lecture and practical session requirements, assigned instructors, and student cohorts.")

    faculty_list = get_all_faculty()
    fac_map = {f["faculty_id"]: f"{f['name']} ({f['faculty_id']})" for f in faculty_list}
    groups_list = get_all_student_groups()
    grp_map = {g["group_id"]: f"{g['name']} ({g['group_id']})" for g in groups_list}

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Courses", placeholder="Search by code, title, category, instructor...", key="crs_search")
    with col_btn:
        st.write("")
        st.write("")
        show_add = st.button("➕ Add New Course", use_container_width=True, type="primary")

    if show_add or st.session_state.get("show_add_course", False):
        st.session_state["show_add_course"] = True
        with st.form("form_add_course", clear_on_submit=False):
            st.markdown("#### Register New Course")
            cr1, cr2 = st.columns(2)
            with cr1:
                c_id = st.text_input("Course ID * (e.g. CRS_CS205)", placeholder="CRS_CS205").strip()
                c_code = st.text_input("Course Code * (e.g. CS205)", placeholder="CS205").strip()
                c_title = st.text_input("Course Title *", placeholder="Database Management Systems").strip()
                c_hours = st.number_input("Weekly Hours *", min_value=1, max_value=10, value=3)
            with cr2:
                c_category = st.selectbox("Course Category", ["Theory", "Practical"])
                c_room_type = st.selectbox("Required Room Type", ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"], index=1 if c_category == "Practical" else 0)
                c_faculty = st.selectbox("Assigned Faculty Member", options=[""] + list(fac_map.keys()), format_func=lambda x: fac_map.get(x, "None (Unassigned)"))
                c_group = st.selectbox("Target Student Cohort", options=[""] + list(grp_map.keys()), format_func=lambda x: grp_map.get(x, "None (Unassigned)"))

            btn1, btn2 = st.columns([1, 1])
            with btn1:
                submitted = st.form_submit_button("Save Course", use_container_width=True, type="primary")
            with btn2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                success, msg = create_course(
                    course_id=c_id,
                    code=c_code,
                    title=c_title,
                    weekly_hours=int(c_hours),
                    required_room_type=c_room_type,
                    category=c_category,
                    is_lab=(c_category == "Practical" or c_room_type == "LAB"),
                    assigned_faculty_id=c_faculty if c_faculty else None,
                    target_group_id=c_group if c_group else None,
                )
                if success:
                    st.success(f"✅ {msg}")
                    st.session_state["show_add_course"] = False
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            if cancelled:
                st.session_state["show_add_course"] = False
                st.rerun()

    courses = get_all_courses(search_query)
    if courses:
        display_df = pd.DataFrame(courses)[[
            "code", "title", "weekly_hours", "category", "required_room_type",
            "assigned_faculty_name", "target_group_name", "course_id"
        ]]
        display_df.rename(columns={
            "code": "Code",
            "title": "Course Title",
            "weekly_hours": "Weekly Hrs",
            "category": "Category",
            "required_room_type": "Room Requirement",
            "assigned_faculty_name": "Instructor",
            "target_group_name": "Student Cohort",
            "course_id": "ID",
        }, inplace=True)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No courses found.")
        return

    st.markdown("---")
    st.markdown("##### ✏️ Modify or Delete Course")
    course_options = {c["course_id"]: f"{c['code']} - {c['title']} ({c.get('category', 'Theory')})" for c in courses}
    selected_crs_id = st.selectbox("Select Course to manage", options=list(course_options.keys()), format_func=lambda x: course_options[x], key="select_crs_manage")

    col_edit_view, col_del_view = st.columns([2, 1])
    with col_edit_view:
        curr = get_course_by_id(selected_crs_id)
        if curr:
            with st.form("form_edit_course"):
                st.markdown(f"**Editing: `{curr['code']}` ({curr['course_id']})**")
                ec1, ec2 = st.columns(2)
                with ec1:
                    edit_code = st.text_input("Course Code", value=curr["code"])
                    edit_title = st.text_input("Course Title", value=curr["title"])
                    edit_hours = st.number_input("Weekly Hours", min_value=1, max_value=10, value=int(curr["weekly_hours"]))
                with ec2:
                    edit_category = st.selectbox("Category", ["Theory", "Practical"], index=0 if curr.get("category") == "Theory" else 1)
                    room_idx = ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"].index(curr["required_room_type"]) if curr["required_room_type"] in ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"] else 0
                    edit_room = st.selectbox("Required Room Type", ["LECTURE_HALL", "LAB", "SEMINAR_ROOM"], index=room_idx)

                    # Faculty selection
                    fac_keys = [""] + list(fac_map.keys())
                    current_fac_idx = fac_keys.index(curr["assigned_faculty_id"]) if curr["assigned_faculty_id"] in fac_keys else 0
                    edit_fac = st.selectbox("Assigned Faculty", options=fac_keys, index=current_fac_idx, format_func=lambda x: fac_map.get(x, "None (Unassigned)"))

                    # Group selection
                    grp_keys = [""] + list(grp_map.keys())
                    current_grp_idx = grp_keys.index(curr["target_group_id"]) if curr["target_group_id"] in grp_keys else 0
                    edit_grp = st.selectbox("Target Cohort", options=grp_keys, index=current_grp_idx, format_func=lambda x: grp_map.get(x, "None (Unassigned)"))

                if st.form_submit_button("Update Course", use_container_width=True, type="primary"):
                    success, msg = update_course(
                        course_id=selected_crs_id,
                        code=edit_code,
                        title=edit_title,
                        weekly_hours=int(edit_hours),
                        required_room_type=edit_room,
                        category=edit_category,
                        is_lab=(edit_category == "Practical" or edit_room == "LAB"),
                        assigned_faculty_id=edit_fac if edit_fac else None,
                        target_group_id=edit_grp if edit_grp else None,
                    )
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    with col_del_view:
        st.markdown("**Delete Safety Zone**")
        st.caption(f"Safely delete `{selected_crs_id}`. Blocked if there are active timetable assignments.")
        if st.button(f"🗑️ Delete `{selected_crs_id}`", type="secondary", use_container_width=True):
            success, msg = delete_course(selected_crs_id)
            if success:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


# ============================================================================
# 5. TIME SLOTS & BREAKS CRUD TAB
# ============================================================================

def _render_timeslots_crud() -> None:
    st.subheader("Academic Timeslots & Institutional Breaks")
    st.caption("Manage daily lecture intervals, duration, and lunch/assembly break periods for the scheduling domain.")

    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Timeslots", placeholder="Search by ID, day, time...", key="ts_search")
    with col_btn:
        st.write("")
        st.write("")
        show_add = st.button("➕ Add Timeslot", use_container_width=True, type="primary")

    if show_add or st.session_state.get("show_add_slot", False):
        st.session_state["show_add_slot"] = True
        with st.form("form_add_slot", clear_on_submit=False):
            st.markdown("#### Create New Timeslot or Break")
            t1, t2 = st.columns(2)
            with t1:
                s_id = st.text_input("Slot ID * (e.g. TS_MON_5)", placeholder="TS_MON_5").strip()
                s_day = st.selectbox("Day of Week *", all_days)
                s_duration = st.number_input("Duration (Minutes)", min_value=15, max_value=240, value=60, step=15)
            with t2:
                s_start = st.text_input("Start Time * (24h HH:MM)", value="15:00").strip()
                s_end = st.text_input("End Time * (24h HH:MM)", value="16:00").strip()
                s_break = st.checkbox("Is Break / Recess Period (No classes scheduled)", value=False)

            btn1, btn2 = st.columns([1, 1])
            with btn1:
                submitted = st.form_submit_button("Save Timeslot", use_container_width=True, type="primary")
            with btn2:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                success, msg = create_timeslot(s_id, s_day, s_start, s_end, int(s_duration), s_break)
                if success:
                    st.success(f"✅ {msg}")
                    st.session_state["show_add_slot"] = False
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            if cancelled:
                st.session_state["show_add_slot"] = False
                st.rerun()

    slots = get_all_timeslots(search_query)
    if slots:
        df_slots = pd.DataFrame(slots)
        df_slots["is_break_label"] = df_slots["is_break"].apply(lambda x: "🥪 Break" if x == 1 else "📚 Lecture Slot")
        st.dataframe(df_slots[["slot_id", "day", "start_time", "end_time", "duration_minutes", "is_break_label"]], use_container_width=True, hide_index=True)
    else:
        st.info("No timeslots found.")
        return

    st.markdown("---")
    st.markdown("##### ✏️ Modify or Delete Timeslot")
    slot_options = {s["slot_id"]: f"{s['slot_id']} - {s['day']} {s['start_time']}-{s['end_time']} ({'Break' if s.get('is_break') else 'Lecture'})" for s in slots}
    selected_ts_id = st.selectbox("Select Timeslot to manage", options=list(slot_options.keys()), format_func=lambda x: slot_options[x], key="select_ts_manage")

    col_edit_view, col_del_view = st.columns([2, 1])
    with col_edit_view:
        curr = get_timeslot_by_id(selected_ts_id)
        if curr:
            with st.form("form_edit_slot"):
                st.markdown(f"**Editing: `{curr['slot_id']}`**")
                et1, et2 = st.columns(2)
                with et1:
                    day_idx = all_days.index(curr["day"]) if curr["day"] in all_days else 0
                    edit_day = st.selectbox("Day", all_days, index=day_idx)
                    edit_duration = st.number_input("Duration (Minutes)", min_value=15, max_value=240, value=int(curr.get("duration_minutes", 60)), step=15)
                with et2:
                    edit_start = st.text_input("Start Time", value=curr["start_time"])
                    edit_end = st.text_input("End Time", value=curr["end_time"])
                    edit_break = st.checkbox("Is Break Period", value=bool(curr.get("is_break", 0)))

                if st.form_submit_button("Update Timeslot", use_container_width=True, type="primary"):
                    success, msg = update_timeslot(selected_ts_id, edit_day, edit_start, edit_end, int(edit_duration), edit_break)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    with col_del_view:
        st.markdown("**Delete Safety Zone**")
        st.caption(f"Remove `{selected_ts_id}`. Blocked if active schedule assignments use this slot.")
        if st.button(f"🗑️ Delete `{selected_ts_id}`", type="secondary", use_container_width=True):
            success, msg = delete_timeslot(selected_ts_id)
            if success:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")
