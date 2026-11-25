"""Timetable Schedule Visualization Engine using Plotly.

Generates interactive, color-coded weekly university timetable grids with
support for Department, Faculty, Classroom, and Student Group views.
Visually distinguishes Theory lectures, Practical laboratories, and Free periods.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Canonical Day Order & Color Palette
DAYS_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAY_INDICES = {day: idx for idx, day in enumerate(DAYS_ORDER)}

THEORY_COLOR = "#1976D2"     # Professional Deep Blue
LAB_COLOR = "#7B1FA2"        # Distinct Violet/Purple
FREE_COLOR = "#212121"       # Subtle Dark Charcoal for open slots
CONFLICT_COLOR = "#D32F2F"   # Red alert for conflicts


def create_timetable_grid_figure(
    schedule_records: List[Dict[str, Any]],
    view_type: str = "Department",
    filter_entity_id: Optional[str] = None,
    highlight_session_id: Optional[str] = None,
) -> go.Figure:
    """Builds a weekly timetable grid visualization.

    Parameters:
      schedule_records: List of dictionaries loaded from `load_saved_timetable()`
      view_type: One of 'Department', 'Faculty', 'Classroom', 'Student Group'
      filter_entity_id: Specific entity ID to filter by (e.g., 'FAC_ALAN' or 'CR_AUD_A')
      highlight_session_id: Optional session variable/assignment ID to highlight (e.g. in What-If preview)
    """
    df = pd.DataFrame(schedule_records)

    # Standard Working Timeslots (09:00 to 17:00 hourly)
    standard_slots = [
        "09:00 - 10:00",
        "10:00 - 11:00",
        "11:00 - 12:00",
        "12:00 - 13:00",
        "14:00 - 15:00",
        "15:00 - 16:00",
        "16:00 - 17:00",
    ]
    slot_y_indices = {s: idx for idx, s in enumerate(standard_slots)}

    # Apply filtering based on selected view
    if not df.empty and filter_entity_id:
        if view_type == "Faculty" and "faculty_id" in df.columns:
            df = df[df["faculty_id"] == filter_entity_id]
        elif view_type == "Classroom" and "room_id" in df.columns:
            df = df[df["room_id"] == filter_entity_id]
        elif view_type == "Student Group" and "group_id" in df.columns:
            df = df[df["group_id"] == filter_entity_id]
        elif view_type == "Course" and "course_code" in df.columns:
            df = df[df["course_code"] == filter_entity_id]

    fig = go.Figure()

    # Determine unique days present
    present_days = [d for d in DAYS_ORDER if not df.empty and d in df["day"].values] or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # If empty schedule
    if df.empty:
        fig.add_annotation(
            text="No scheduled sessions match the current filter selection.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#9E9E9E"),
        )
        fig.update_layout(
            title=f"Weekly Timetable View ({view_type} View - No Active Records)",
            xaxis=dict(title="Day of Week", tickvals=list(range(len(present_days))), ticktext=present_days),
            yaxis=dict(title="Timeslot", tickvals=list(range(len(standard_slots))), ticktext=standard_slots, autorange="reversed"),
            template="plotly_dark",
            height=500,
        )
        return fig

    # Build background matrix of free periods
    for day_idx, day_name in enumerate(present_days):
        for slot_idx, slot_label in enumerate(standard_slots):
            # Check if lunch break (12:00 - 13:00)
            is_lunch = slot_label.startswith("12:00")
            cell_text = "🍽️ Lunch Break" if is_lunch else "Free Period"
            cell_color = "#1E222A" if not is_lunch else "#14171D"

            fig.add_shape(
                type="rect",
                x0=day_idx - 0.45,
                x1=day_idx + 0.45,
                y0=slot_idx - 0.45,
                y1=slot_idx + 0.45,
                fillcolor=cell_color,
                line=dict(color="#2D323F", width=1),
                layer="below",
            )

    # Plot each scheduled session as an interactive block
    for _, row in df.iterrows():
        day_name = row["day"]
        if day_name not in present_days:
            continue
        day_idx = present_days.index(day_name)

        slot_label = f"{row['start_time']} - {row['end_time']}"
        if slot_label not in slot_y_indices:
            # Find closest matching slot
            matched = [s for s in standard_slots if s.startswith(row["start_time"][:2])]
            slot_label = matched[0] if matched else standard_slots[0]
        slot_idx = slot_y_indices.get(slot_label, 0)

        is_lab = "LAB" in str(row.get("room_type", "")).upper() or "practical" in str(row.get("course_category", "")).lower()
        is_highlighted = highlight_session_id and (highlight_session_id in str(row.get("assignment_id", "")) or highlight_session_id in str(row.get("course_code", "")))

        bg_color = CONFLICT_COLOR if is_highlighted else (LAB_COLOR if is_lab else THEORY_COLOR)
        session_type = "🔬 Lab" if is_lab else "📖 Theory"

        # Label inside card
        card_text = (
            f"<b>{row.get('course_code', 'N/A')}</b> ({session_type})<br>"
            f"🏛️ {row.get('room_id', 'N/A')}<br>"
            f"👨‍🏫 {row.get('faculty_name', row.get('faculty_id', 'N/A'))}<br>"
            f"👥 {row.get('group_name', row.get('group_id', 'N/A'))}"
        )

        hover_info = (
            f"<b>Course:</b> {row.get('course_title', 'N/A')} ({row.get('course_code', 'N/A')})<br>"
            f"<b>Session Type:</b> {session_type}<br>"
            f"<b>Day & Time:</b> {day_name} {slot_label}<br>"
            f"<b>Room:</b> {row.get('room_name', row.get('room_id', 'N/A'))} ({row.get('room_type', 'N/A')})<br>"
            f"<b>Instructor:</b> {row.get('faculty_name', row.get('faculty_id', 'N/A'))}<br>"
            f"<b>Student Cohort:</b> {row.get('group_name', row.get('group_id', 'N/A'))}<br>"
            f"<b>Assignment ID:</b> {row.get('assignment_id', 'N/A')}"
        )

        # Draw card rectangle
        fig.add_shape(
            type="rect",
            x0=day_idx - 0.44,
            x1=day_idx + 0.44,
            y0=slot_idx - 0.44,
            y1=slot_idx + 0.44,
            fillcolor=bg_color,
            line=dict(color="#FFD54F" if is_highlighted else "#FFFFFF", width=2 if is_highlighted else 1),
            opacity=0.92,
        )

        # Add text annotation
        fig.add_annotation(
            x=day_idx,
            y=slot_idx,
            text=card_text,
            showarrow=False,
            font=dict(color="#FFFFFF", size=10),
            align="center",
            hovertext=hover_info,
        )

    title_suffix = f" — {view_type}: {filter_entity_id}" if filter_entity_id else f" — {view_type} Master View"
    fig.update_layout(
        title=f"University Timetable Grid{title_suffix}",
        xaxis=dict(
            title="Day of the Week",
            tickmode="array",
            tickvals=list(range(len(present_days))),
            ticktext=present_days,
            gridcolor="#2D323F",
        ),
        yaxis=dict(
            title="Operational Time Window",
            tickmode="array",
            tickvals=list(range(len(standard_slots))),
            ticktext=standard_slots,
            autorange="reversed",
            gridcolor="#2D323F",
        ),
        template="plotly_dark",
        height=580,
        margin=dict(l=60, r=40, t=60, b=50),
    )

    return fig
