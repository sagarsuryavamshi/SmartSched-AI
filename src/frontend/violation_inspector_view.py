"""Constraint Violation and Timetable Quality Diagnostics Streamlit View.

Provides dedicated institutional audit reports for:
- Hard constraint violations (H1-H8)
- Soft constraint penalties (S1-S4)
- Faculty overlaps, classroom double-bookings, and student group collisions
- Room capacity violations and faculty availability infringements
- Downloadable quality audit reports in CSV and Markdown formats
"""

from typing import Dict, List
import pandas as pd
import streamlit as st

from src.csp_engine.domain_types import SchedulingAssignmentValue, TimetableStatus
from src.csp_engine.model import CSPModel
from src.database.db_manager import DEFAULT_DB_PATH
from src.database.timetable_repository import load_saved_timetable
from src.frontend.components import render_metric_card


def render_violation_inspector_view() -> None:
    """Renders the comprehensive constraint validation and diagnostic report interface."""
    st.markdown('<div class="main-header">Constraint Violation & Schedule Quality Audit</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Independent diagnostic auditor evaluating active SQLite timetable assignments against all institutional constraints.</div>',
        unsafe_allow_html=True,
    )

    schedule_records = load_saved_timetable(db_path=DEFAULT_DB_PATH)
    if not schedule_records:
        st.warning("⚠️ No active timetable assignments found in database to inspect.")
        return

    model = CSPModel.build_from_db(DEFAULT_DB_PATH)

    # Reconstruct assignment map from DB
    assignment_map: Dict[str, SchedulingAssignmentValue] = {}
    for r in schedule_records:
        # Match to model variable
        for v in model.variables:
            if v.course_code == r["course_code"] and v.group_id == r["group_id"]:
                if v.var_id not in assignment_map:
                    assignment_map[v.var_id] = SchedulingAssignmentValue(
                        slot_id=r["slot_id"],
                        room_id=r["room_id"],
                        day=r["day"],
                        start_time=r["start_time"],
                        end_time=r["end_time"],
                        slot_ids=[r["slot_id"]],
                        faculty_id=r["faculty_id"],
                        group_id=r["group_id"],
                    )
                    break

    # Evaluate using the standard constraint evaluator
    report = model.validate_assignments(assignment_map)

    # 1. Top KPI Summary
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        status_label = "✅ VALID" if report.is_valid else "❌ CONFLICT DETECTED"
        render_metric_card("Timetable State", status_label, "🎯")
    with c2:
        render_metric_card("Hard Violations", str(len(report.hard_violations)), "⚖️")
    with c3:
        render_metric_card("Soft Penalty Score", f"{report.soft_penalty_score:.1f}", "📉")
    with c4:
        render_metric_card("Sessions Audited", f"{len(assignment_map)} / {len(model.variables)}", "📋")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Hard Constraint Verification Matrix (H1-H8)
    st.markdown("### 📋 Hard Constraints Verification Checklist (H1 - H8)")
    h_cards = st.columns(4)
    codes_h = ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"]

    for idx, code in enumerate(codes_h):
        col = h_cards[idx % 4]
        summary = report.summary_by_constraint.get(code, {"name": code, "violations": 0})
        cnt = summary.get("violations", 0)
        with col:
            icon = "✅" if cnt == 0 else "❌"
            badge = f"{cnt} violation(s)" if cnt > 0 else "0 (PASS)"
            st.markdown(f"**{icon} [{code}] {summary.get('name', '')}**")
            st.caption(f"Status: `{badge}`")

    st.markdown("---")

    # 3. Conflict Diagnostic Details
    if report.hard_violations:
        st.markdown("### 🚨 Detected Conflict Details")
        rows = []
        for v in report.hard_violations:
            rows.append({
                "Constraint Code": v.constraint_id,
                "Constraint Name": v.constraint_name,
                "Session Involved": ", ".join(v.violating_var_ids),
                "Diagnostic Conflict Description": v.explanation,
            })
        st.table(pd.DataFrame(rows))
    else:
        st.success("🎉 **Zero Hard Constraint Violations:** All faculty, classroom, cohort, room capacity, and availability rules are 100% satisfied.")

    # 4. Soft Constraint Breakdown (S1 - S4)
    st.markdown("### 📊 Soft Constraints Preference Breakdown (S1 - S4)")
    s_cols = st.columns(4)
    codes_s = ["S1", "S2", "S3", "S4"]
    for idx, code in enumerate(codes_s):
        col = s_cols[idx]
        summary = report.summary_by_constraint.get(code, {"name": code, "penalty": 0.0, "notices": []})
        pen = summary.get("penalty", 0.0)
        with col:
            st.markdown(f"**[{code}] {summary.get('name', '')}**")
            st.metric("Penalty Points", f"{pen:.1f} pts")

    # 5. Downloadable Audit Report
    st.markdown("---")
    st.markdown("### 📥 Download Institutional Quality Audit Report")

    # Format Markdown Report
    report_md = f"""# SmartSched AI — Academic Timetable Quality Audit Report
Generated from SQLite Database: {DEFAULT_DB_PATH}

## Executive Summary
- Timetable Status: {report.status.value}
- Evaluated Sessions: {len(assignment_map)} / {len(model.variables)}
- Total Hard Constraint Violations: {len(report.hard_violations)}
- Total Soft Constraint Penalty: {report.soft_penalty_score:.1f}

## Hard Constraint Checklist (H1 - H8)
"""
    for code in codes_h:
        s = report.summary_by_constraint.get(code, {"name": code, "violations": 0})
        status_txt = "PASS (0 violations)" if s.get("violations", 0) == 0 else f"FAIL ({s.get('violations')} violations)"
        report_md += f"- [{code}] {s.get('name')}: {status_txt}\n"

    report_md += "\n## Soft Constraint Scores (S1 - S4)\n"
    for code in codes_s:
        s = report.summary_by_constraint.get(code, {"name": code, "penalty": 0.0})
        report_md += f"- [{code}] {s.get('name')}: {s.get('penalty'):.1f} pts\n"

    col_rep1, col_rep2 = st.columns([1, 1])
    with col_rep1:
        st.download_button(
            label="📄 Download Quality Audit Report (Markdown)",
            data=report_md,
            file_name="timetable_quality_audit.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col_rep2:
        # CSV of all constraint violation items
        audit_rows = []
        for code, data in report.summary_by_constraint.items():
            audit_rows.append({
                "Constraint Code": code,
                "Constraint Name": data.get("name", ""),
                "Type": "Hard" if code.startswith("H") else "Soft",
                "Violations Count": data.get("violations", 0),
                "Penalty Points": data.get("penalty", 0.0),
            })
        df_audit = pd.DataFrame(audit_rows)
        st.download_button(
            label="📊 Download Constraint Summary as CSV",
            data=df_audit.to_csv(index=False),
            file_name="constraint_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )
