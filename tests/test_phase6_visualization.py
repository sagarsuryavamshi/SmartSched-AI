"""Unit tests for Phase 6: Timetable Visualization, Multi-Angle Filtering, CSV/PDF Exports, and Analytics."""

import os
import sys
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.csp_engine.model import CSPModel
from src.database.db_manager import init_db
from src.database.timetable_repository import load_saved_timetable, save_timetable_solution
from src.data_management.loader import seed_synthetic_data
from src.evaluation.metrics import calculate_timetable_analytics
from src.ga_engine.genetic_solver import GAConfig, GeneticSolver
from src.utils.export_service import export_timetable_to_csv, export_timetable_to_pdf
from src.visualization.timetable_plots import create_timetable_grid_figure


class TestPhase6VisualizationAndAnalytics(unittest.TestCase):
    """Test suite for Timetable Filtering, Plotly Grid, CSV/PDF Exports, and Analytics."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_p6_viz.db")
        init_db(cls.db_path)
        seed_synthetic_data(cls.db_path)

        cls.model = CSPModel.build_from_db(cls.db_path)
        solver = GeneticSolver(cls.model)
        res = solver.solve(GAConfig(population_size=60, max_generations=30, random_seed=42))
        cls.solution = res.best_chromosome

        # Persist timetable to SQLite
        save_timetable_solution(
            cls.solution.genes,
            cls.model.variables_map,
            overwrite_existing=True,
            db_path=cls.db_path,
        )
        cls.schedule_records = load_saved_timetable(db_path=cls.db_path)

    def test_schedule_records_loaded_successfully(self):
        """Verifies that saved schedule records exist and have required relational fields."""
        self.assertGreater(len(self.schedule_records), 0)
        first_r = self.schedule_records[0]
        self.assertIn("course_code", first_r)
        self.assertIn("faculty_id", first_r)
        self.assertIn("room_id", first_r)
        self.assertIn("group_id", first_r)
        self.assertIn("day", first_r)
        self.assertIn("start_time", first_r)

    def test_department_master_view(self):
        """Verifies rendering of the Master Department view figure."""
        fig = create_timetable_grid_figure(self.schedule_records, view_type="Department")
        self.assertIsNotNone(fig)
        self.assertIn("University Timetable Grid", fig.layout.title.text)

    def test_faculty_timetable_filtering(self):
        """Verifies filtering by specific faculty member."""
        target_fac = self.schedule_records[0]["faculty_id"]
        fig = create_timetable_grid_figure(
            self.schedule_records,
            view_type="Faculty",
            filter_entity_id=target_fac,
        )
        self.assertIsNotNone(fig)
        self.assertIn(target_fac, fig.layout.title.text)

    def test_classroom_timetable_filtering(self):
        """Verifies filtering by specific classroom."""
        target_room = self.schedule_records[0]["room_id"]
        fig = create_timetable_grid_figure(
            self.schedule_records,
            view_type="Classroom",
            filter_entity_id=target_room,
        )
        self.assertIsNotNone(fig)
        self.assertIn(target_room, fig.layout.title.text)

    def test_student_group_filtering(self):
        """Verifies filtering by student group / cohort."""
        target_group = self.schedule_records[0]["group_id"]
        fig = create_timetable_grid_figure(
            self.schedule_records,
            view_type="Student Group",
            filter_entity_id=target_group,
        )
        self.assertIsNotNone(fig)
        self.assertIn(target_group, fig.layout.title.text)

    def test_course_filtering(self):
        """Verifies filtering by course code."""
        target_course = self.schedule_records[0]["course_code"]
        fig = create_timetable_grid_figure(
            self.schedule_records,
            view_type="Course",
            filter_entity_id=target_course,
        )
        self.assertIsNotNone(fig)
        self.assertIn(target_course, fig.layout.title.text)

    def test_csv_export(self):
        """Verifies standardized CSV generation and column headers."""
        csv_text = export_timetable_to_csv(self.schedule_records)
        self.assertTrue(csv_text.startswith("Assignment ID,Course Code,Course Title"))
        lines = csv_text.strip().split("\n")
        self.assertGreater(len(lines), 1)  # Header + at least one data row
        self.assertIn(self.schedule_records[0]["course_code"], csv_text)

    def test_pdf_export(self):
        """Verifies ReportLab PDF document compilation."""
        pdf_bytes = export_timetable_to_pdf(
            self.schedule_records,
            title="University Engineering Timetable",
            filter_label="Department Master",
        )
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"), "Exported file does not have valid PDF header")

    def test_dynamic_analytics_calculation(self):
        """Verifies dynamic calculation of utilization, workload, and soft penalties."""
        analytics = calculate_timetable_analytics(self.schedule_records, self.model, self.db_path)

        self.assertGreater(analytics["total_scheduled_sessions"], 0)
        self.assertGreater(analytics["overall_classroom_utilization_pct"], 0.0)
        self.assertLessEqual(analytics["overall_classroom_utilization_pct"], 100.0)
        self.assertIn("room_utilization", analytics)
        self.assertIn("faculty_workload", analytics)
        self.assertIn("daily_group_workload", analytics)
        self.assertIn("soft_constraint_breakdown", analytics)

        # Confirm soft breakdown contains all 4 objectives
        soft = analytics["soft_constraint_breakdown"]
        self.assertIn("S1", soft)
        self.assertIn("S2", soft)
        self.assertIn("S3", soft)
        self.assertIn("S4", soft)


if __name__ == "__main__":
    unittest.main()
