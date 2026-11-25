"""What-If Rescheduling Workbench Streamlit View.

Enables administrators to interactively:
1. Select an existing scheduled session.
2. Propose an alternative timeslot and classroom.
3. Preview candidate changes against the full H1-H8 & S1-S4 constraint engine.
4. Compare original vs proposed schedules.
5. Commit only conflict-free changes atomically using SQLite transactions.
6. Review audit history and execute instant rollback of previous adjustments.
"""

from typing import Dict, List
import pandas as pd
import streamlit as st

from src.csp_engine.domain_types import SchedulingAssignmentValue
from src.csp_engine.model import CSPModel
from src.database.db_manager import DEFAULT_DB_PATH, get_db_connection
from src.database.rescheduling_repository import (
    apply_reschedule_transaction,
    get_rescheduling_history,
    rollback_reschedule_transaction,
)
from src.database.timetable_repository import load_saved_timetable
from src.frontend.components import render_metric_card
from src.optimization.rescheduling_engine import evaluate_what_if_reschedule


def render_what_if_rescheduling_view() -> None:
    """Renders the complete What-If Rescheduling and Transactional Rollback interface."""
    st.markdown('<div class="main-header">What-If Rescheduling & Safe Adjustment Workbench</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Interactive timetable scenario planning with instant constraint validation, penalty delta computation, and atomic rollback.</div>',
        unsafe_allow_html=True,
    )

    tab_whatif, tab_history = st.tabs([
        "🔄 What-If Scenario Rescheduler",
        "📜 Rescheduling Audit History & Rollback",
    ])

    with tab_whatif:
        _render_what_if_planner_tab()

    with tab_history:
        _render_history_tab()


def _render_what_if_planner_tab() -> None:
    """Sub-view for formulating, testing, and committing what-if adjustments."""
    schedule_records = load_saved_timetable(db_path=DEFAULT_DB_PATH)
    if not schedule_records:
        st.warning("⚠️ No active timetable assignments found in SQLite. Please generate and save a timetable first.")
        return

    model = CSPModel.build_from_db(DEFAULT_DB_PATH)

    # Reconstruct assignment map from DB records
    # Group multi-slot sessions by assignment_id prefix
    assignment_map: Dict[str, SchedulingAssignmentValue] = {}
    record_by_session: Dict[str, List[dict]] = {}

    for r in schedule_records:
        # ASG_{course_code}_S{session_num}_{slot_id}
        asg_id = r["assignment_id"]
        parts = asg_id.split("_")
        # Find variable in model
        v_matched = None
        for v in model.variables:
            if v.course_code == r["course_code"] and v.group_id == r["group_id"]:
                if v.var_id not in assignment_map:
                    v_matched = v
                    break
        if not v_matched:
            # Fallback by course_id
            for v in model.variables:
                if v.course_code == r["course_code"] and v.var_id not in assignment_map:
                    v_matched = v
                    break

        target_v_id = v_matched.var_id if v_matched else asg_id
        if target_v_id not in record_by_session:
            record_by_session[target_v_id] = []
        record_by_session[target_v_id].append(r)

    # Build active assignments
    for v_id, rows in record_by_session.items():
        first_r = rows[0]
        slot_ids = [r["slot_id"] for r in rows]
        assignment_map[v_id] = SchedulingAssignmentValue(
            slot_id=slot_ids[0],
            room_id=first_r["room_id"],
            day=first_r["day"],
            start_time=first_r["start_time"],
            end_time=rows[-1]["end_time"],
            slot_ids=slot_ids,
            faculty_id=first_r["faculty_id"],
            group_id=first_r["group_id"],
        )

    st.markdown("### 1. Select Scheduled Session to Adjust")
    session_options = list(assignment_map.keys())

    def format_session_label(v_id: str) -> str:
        val = assignment_map[v_id]
        var = model.variables_map.get(v_id)
        c_code = var.course_code if var else v_id
        return f"{c_code} — {val.day} {val.start_time}-{val.end_time} in {val.room_id} (Prof: {val.faculty_id}, Cohort: {val.group_id})"

    selected_var_id = st.selectbox("Choose Target Session", session_options, format_func=format_session_label)
    cur_val = assignment_map[selected_var_id]
    var_obj = model.variables_map.get(selected_var_id)
    is_multi_hour = len(cur_val.slot_ids) > 1

    st.markdown("---")
    st.markdown("### 2. Propose Alternative Room & Timeslot")

    with get_db_connection(DEFAULT_DB_PATH) as conn:
        all_rooms_df = pd.read_sql_query("SELECT room_id, name, room_type, capacity FROM classrooms", conn)
        all_slots_df = pd.read_sql_query("SELECT slot_id, day, start_time, end_time FROM timeslots WHERE is_break = 0 ORDER BY day, start_time", conn)

    c_p1, c_p2 = st.columns(2)

    with c_p1:
        st.markdown("**Target Classroom:**")
        room_choices = all_rooms_df["room_id"].tolist()
        room_labels = {r["room_id"]: f"{r['name']} ({r['room_id']}) — {r['room_type']}, Cap: {r['capacity']}" for _, r in all_rooms_df.iterrows()}
        new_room_id = st.selectbox(
            "Select New Room",
            room_choices,
            index=room_choices.index(cur_val.room_id) if cur_val.room_id in room_choices else 0,
            format_func=lambda x: room_labels.get(x, x),
        )

    with c_p2:
        st.markdown("**Target Timeslot:**")
        slot_choices = all_slots_df["slot_id"].tolist()
        slot_labels = {r["slot_id"]: f"{r['day']} {r['start_time']} - {r['end_time']}" for _, r in all_slots_df.iterrows()}

        if not is_multi_hour:
            new_slot_id = st.selectbox(
                "Select New Starting Slot (1-hour)",
                slot_choices,
                index=slot_choices.index(cur_val.slot_id) if cur_val.slot_id in slot_choices else 0,
                format_func=lambda x: slot_labels.get(x, x),
            )
            proposed_slot_ids = [new_slot_id]
        else:
            st.info("🔬 **Multi-Hour Practical Session (2-Hour Continuous Block Selector):** The system strictly enforces H7 by presenting only valid consecutive time blocks.")
            
            # Construct valid 2-hour continuous blocks from all_slots_df
            # Must be same day, slot1.end_time == slot2.start_time, and neither is break
            valid_blocks = []
            for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
                d_slots = all_slots_df[all_slots_df["day"] == d].to_dict("records")
                for k in range(len(d_slots) - 1):
                    s1 = d_slots[k]
                    s2 = d_slots[k + 1]
                    if s1["end_time"] == s2["start_time"]:
                        block_key = f"{s1['slot_id']}+{s2['slot_id']}"
                        block_label = f"{d} {s1['start_time']} - {s2['end_time']} ({s1['slot_id']} & {s2['slot_id']})"
                        valid_blocks.append((block_key, block_label, [s1["slot_id"], s2["slot_id"]]))

            block_keys = [b[0] for b in valid_blocks]
            block_labels = {b[0]: b[1] for b in valid_blocks}
            block_slots_map = {b[0]: b[2] for b in valid_blocks}

            current_block_key = f"{cur_val.slot_ids[0]}+{cur_val.slot_ids[1]}" if len(cur_val.slot_ids) >= 2 else (block_keys[0] if block_keys else "")
            default_idx = block_keys.index(current_block_key) if current_block_key in block_keys else 0

            selected_block_key = st.selectbox(
                "Select 2-Hour Continuous Block",
                block_keys,
                index=default_idx,
                format_func=lambda k: block_labels.get(k, k),
            )
            proposed_slot_ids = block_slots_map.get(selected_block_key, cur_val.slot_ids)

    st.markdown("<br>", unsafe_allow_html=True)
    eval_btn = st.button("🔍 Preview & Validate Proposed Reschedule", type="primary", use_container_width=True)

    if eval_btn:
        with st.spinner("Executing full H1-H8 constraint validation and soft penalty calculation..."):
            whatif_res = evaluate_what_if_reschedule(
                current_assignment=assignment_map,
                variable_id=selected_var_id,
                new_room_id=new_room_id,
                new_slot_ids=proposed_slot_ids,
                model=model,
            )
            st.session_state["whatif_result"] = whatif_res
            st.session_state["whatif_var_id"] = selected_var_id
            st.session_state["whatif_room"] = new_room_id
            st.session_state["whatif_slots"] = proposed_slot_ids

    # 3. Render Validation Results and Side-by-Side Comparison
    whatif_res = st.session_state.get("whatif_result")
    if whatif_res:
        st.markdown("---")
        st.markdown("### 3. Constraint Evaluation & Impact Analysis")

        # Status Banner
        if whatif_res.is_valid:
            st.success(f"✅ **FEASIBLE PROPOSAL:** {whatif_res.message}")
        else:
            st.error(f"❌ **REJECTED (HARD CONSTRAINT VIOLATION):** {whatif_res.message}")

        # Metrics Comparison
        c_k1, c_k2, c_k3, c_k4 = st.columns(4)
        with c_k1:
            render_metric_card("Hard Violations", str(len(whatif_res.hard_violations)), "⚖️")
        with c_k2:
            render_metric_card("Original Soft Penalty", f"{whatif_res.original_soft_penalty:.1f}", "📉")
        with c_k3:
            render_metric_card("Proposed Soft Penalty", f"{whatif_res.proposed_soft_penalty:.1f}", "📊")
        with c_k4:
            delta_str = f"{whatif_res.soft_penalty_delta:+.1f}"
            delta_icon = "🟢" if whatif_res.soft_penalty_delta <= 0 else "🔴"
            render_metric_card("Penalty Impact (Delta)", delta_str, delta_icon)

        # Detailed Hard Violations List
        if whatif_res.hard_violations:
            st.markdown("#### 🚨 Detected Conflict Details")
            for idx, v in enumerate(whatif_res.hard_violations, 1):
                st.markdown(f"**{idx}. [{v.constraint_type}] {v.constraint_name}**")
                st.caption(f"{v.description} (Session: `{v.variable_id}`)")

        # Side-by-side assignment diff table
        st.markdown("#### 🔄 Schedule Assignment Diff")
        old_val = whatif_res.old_assignment
        new_val = whatif_res.new_assignment
        df_diff = pd.DataFrame([
            {"Attribute": "Classroom", "Original Schedule": old_val.room_id if old_val else "", "Proposed What-If": new_val.room_id if new_val else ""},
            {"Attribute": "Day of Week", "Original Schedule": old_val.day if old_val else "", "Proposed What-If": new_val.day if new_val else ""},
            {"Attribute": "Time Window", "Original Schedule": f"{old_val.start_time} - {old_val.end_time}" if old_val else "", "Proposed What-If": f"{new_val.start_time} - {new_val.end_time}" if new_val else ""},
            {"Attribute": "Slot IDs", "Original Schedule": ", ".join(old_val.slot_ids) if old_val else "", "Proposed What-If": ", ".join(new_val.slot_ids) if new_val else ""},
        ])
        st.table(df_diff)

        # 4. Commit to Database
        st.markdown("---")
        st.markdown("### 4. Commit Reschedule to SQLite")
        if whatif_res.is_valid:
            st.write("Commit this valid rescheduling modification atomically into the university timetable database.")
            confirm_commit = st.checkbox("I confirm this change should overwrite the current timetable assignment in SQLite.", value=False)
            commit_btn = st.button("💾 Commit Reschedule to Database", type="secondary", disabled=not confirm_commit)

            if commit_btn:
                # Find DB assignment IDs matching this session
                db_asg_ids = [r["assignment_id"] for r in record_by_session.get(selected_var_id, [])]
                if not db_asg_ids:
                    st.error("No database assignment IDs found to update.")
                else:
                    ok, chg_id, msg = apply_reschedule_transaction(
                        assignment_ids=db_asg_ids,
                        new_room_id=new_room_id,
                        new_slot_ids=proposed_slot_ids,
                        reason=f"Administrator What-If Adjustment for {var_obj.course_code if var_obj else selected_var_id}",
                    )
                    if ok:
                        st.success(f"🎉 **{msg}**")
                        st.session_state.pop("whatif_result", None)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
        else:
            st.warning("⚠️ **Commit Disabled:** The system strictly rejects committing any schedule proposal that violates hard constraints.")


def _render_history_tab() -> None:
    """Sub-view for reviewing committed adjustments and triggering atomic rollbacks."""
    st.markdown("### 📜 Rescheduling Transaction Audit Trail")
    st.caption("Complete chronological record of all administrative schedule modifications with instant rollback capability.")

    history_records = get_rescheduling_history(limit=50, db_path=DEFAULT_DB_PATH)

    if not history_records:
        st.info("💡 No rescheduling adjustments have been committed yet.")
        return

    df_hist = pd.DataFrame(history_records)
    cols = ["change_id", "course_code", "group_id", "old_day", "old_start_time", "new_day", "new_start_time", "old_room_id", "new_room_id", "status", "timestamp"]
    st.dataframe(df_hist[cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### ↩️ Atomic Rollback Controller")
    committed_changes = [h["change_id"] for h in history_records if h["status"] == "COMMITTED"]

    if not committed_changes:
        st.success("✅ All recorded changes are either clean or already rolled back.")
        return

    col_r1, col_r2 = st.columns([2, 1])
    with col_r1:
        selected_rollback_id = st.selectbox("Select Change to Rollback", committed_changes)
    with col_r2:
        st.markdown("<br>", unsafe_allow_html=True)
        rollback_btn = st.button("↩️ Execute Atomic Rollback", type="secondary", use_container_width=True)

    if rollback_btn:
        with st.spinner("Reverting database assignments within transaction..."):
            ok_rb, msg_rb = rollback_reschedule_transaction(selected_rollback_id, db_path=DEFAULT_DB_PATH)
            if ok_rb:
                st.success(f"✅ {msg_rb}")
                st.rerun()
            else:
                st.error(f"❌ {msg_rb}")
