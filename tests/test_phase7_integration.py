"""Unit tests for Phase 7: Complete System Integration, Continuous Multi-Hour Lab Rescheduling, and CLI Scripts."""

import os
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.csp_engine.domain_types import TimetableStatus
from src.csp_engine.model import CSPModel
from src.database.db_manager import init_db
from src.database.rescheduling_repository import (
    apply_reschedule_transaction,
    get_rescheduling_history,
    rollback_reschedule_transaction,
)
from src.database.timetable_repository import load_saved_timetable, save_timetable_solution
from src.data_management.loader import load_dataset_summary, seed_synthetic_data
from src.ga_engine.chromosome import TimetableChromosome
from src.ga_engine.fitness import evaluate_fitness
from src.ga_engine.genetic_solver import GAConfig, GeneticSolver
from src.optimization.rescheduling_engine import evaluate_what_if_reschedule


class TestPhase7IntegrationAndContinuousLabRescheduling(unittest.TestCase):
    """Integration test suite for Phase 7 end-to-end functionality."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, "test_p7.db")
        init_db(cls.db_path)
        seed_synthetic_data(cls.db_path)

        cls.model = CSPModel.build_from_db(cls.db_path)
        solver = GeneticSolver(cls.model)
        res = solver.solve(GAConfig(population_size=50, max_generations=25, random_seed=42))
        cls.best = res.best_chromosome

        save_timetable_solution(
            cls.best.genes,
            cls.model.variables_map,
            overwrite_existing=True,
            db_path=cls.db_path,
        )
        cls.current_assignment = dict(cls.best.genes)

    def test_01_end_to_end_pipeline_integration(self):
        """Verifies full pipeline: DB -> CSPModel -> GA Solver -> Fitness Audit -> SQLite Persistence."""
        summary = load_dataset_summary(self.db_path)
        self.assertGreater(summary["courses"], 0)
        self.assertGreater(summary["classrooms"], 0)

        # Validate saved records
        records = load_saved_timetable(db_path=self.db_path)
        self.assertEqual(len(records), 27)  # 21 theory + 3*2 labs

        # Evaluate fitness
        chrom = TimetableChromosome(genes=self.current_assignment)
        evaluate_fitness(chrom, self.model)
        self.assertEqual(chrom.hard_violations_count, 0, "Expected zero hard constraint violations in generated schedule")
        self.assertGreater(chrom.fitness, 0.0)

    def test_02_continuous_2hour_lab_block_rescheduling(self):
        """Verifies that 2-hour laboratory sessions evaluate cleanly when using paired consecutive slots."""
        lab_var_id = None
        for v_id, var in self.model.variables_map.items():
            if var.duration_hours == 2 and var.required_room_type == "LAB":
                lab_var_id = v_id
                break

        self.assertIsNotNone(lab_var_id, "Expected at least one 2-hour lab variable")
        lab_val = self.current_assignment[lab_var_id]

        # Valid 2-hour continuous block on Friday afternoon: TS_FRI_2 and TS_FRI_3
        paired_slots = ["TS_FRI_2", "TS_FRI_3"]
        lab_room = lab_val.room_id

        eval_res = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=lab_var_id,
            new_room_id=lab_room,
            new_slot_ids=paired_slots,
            model=self.model,
        )

        # Ensure H7 is strictly NOT violated because the slots are continuous
        violation_cids = [v.constraint_id for v in eval_res.hard_violations]
        self.assertNotIn("H7", violation_cids, "Continuous paired slots must not violate H7 laboratory continuity")

    def test_03_discontinuous_lab_proposal_strictly_rejected(self):
        """Verifies that proposing discontinuous non-consecutive slots for a 2-hour lab triggers H7 rejection."""
        lab_var_id = [
            v_id for v_id, v in self.model.variables_map.items() if v.duration_hours == 2
        ][0]
        lab_val = self.current_assignment[lab_var_id]

        discontinuous = ["TS_TUE_1", "TS_TUE_3"]
        eval_res = evaluate_what_if_reschedule(
            current_assignment=self.current_assignment,
            variable_id=lab_var_id,
            new_room_id=lab_val.room_id,
            new_slot_ids=discontinuous,
            model=self.model,
        )

        self.assertFalse(eval_res.is_valid)
        self.assertTrue(any("H7" in v.constraint_id for v in eval_res.hard_violations))

    def test_04_cli_database_initialization_script(self):
        """Verifies that scripts/init_db.py executes cleanly."""
        cli_db = os.path.join(self.temp_dir, "test_cli.db")
        env = dict(os.environ, SMARTSCHED_DB_PATH=cli_db)
        res = subprocess.run(
            [sys.executable, os.path.join(ROOT_DIR, "scripts", "init_db.py")],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"init_db.py failed: {res.stderr}")
        self.assertTrue(os.path.exists(cli_db))

    def test_05_cli_seed_data_script(self):
        """Verifies that scripts/seed_data.py executes and populates synthetic entities."""
        cli_db = os.path.join(self.temp_dir, "test_cli_seed.db")
        res = subprocess.run(
            [sys.executable, os.path.join(ROOT_DIR, "scripts", "seed_data.py"), "--db-path", cli_db, "--overwrite"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"seed_data.py failed: {res.stderr}")
        summary = load_dataset_summary(cli_db)
        self.assertGreater(summary["courses"], 0)
        self.assertGreater(summary["classrooms"], 0)


if __name__ == "__main__":
    unittest.main()
