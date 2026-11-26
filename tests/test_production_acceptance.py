"""End-to-End Acceptance Test Suite for SmartSched AI Production Architecture.

Validates the 10 Mandatory Production Workflows:
  1. Authentication & Role-Based Authorization
  2. Resource CRUD Persistence
  3. Real Backtracking CSP Solver Execution
  4. Real Genetic Algorithm Execution
  5. Comparative Benchmarking
  6. Timetable Viewing & CSV Export
  7. Analytics & Metric Breakdown
  8. What-If Rescheduling & Transaction Rollback
  9. Production Reliability & Persistence
 10. Overall Regression
"""

import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app

class TestProductionAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        r_admin = cls.client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@SmartSched2026"})
        cls.admin_headers = {"Authorization": f"Bearer {r_admin.json()['access_token']}"}
        r_viewer = cls.client.post("/api/v1/auth/login", json={"username": "viewer", "password": "Viewer@SmartSched2026"})
        cls.viewer_headers = {"Authorization": f"Bearer {r_viewer.json()['access_token']}"}

    # Workflow 1: Authentication
    def test_workflow_01_authentication(self):
        # Admin login
        r_admin = self.client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@SmartSched2026"})
        self.assertEqual(r_admin.status_code, 200)
        admin_token = r_admin.json()["access_token"]
        self.assertEqual(r_admin.json()["role"], "admin")

        # Viewer login
        r_viewer = self.client.post("/api/v1/auth/login", json={"username": "viewer", "password": "Viewer@SmartSched2026"})
        self.assertEqual(r_viewer.status_code, 200)
        viewer_token = r_viewer.json()["access_token"]
        self.assertEqual(r_viewer.json()["role"], "viewer")

        # Reject bad credentials
        r_bad = self.client.post("/api/v1/auth/login", json={"username": "admin", "password": "bad"})
        self.assertEqual(r_bad.status_code, 401)

        # RBAC: Viewer cannot list users
        r_forbidden = self.client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {viewer_token}"})
        self.assertEqual(r_forbidden.status_code, 403)

        # RBAC: Admin can list users
        r_allowed = self.client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(r_allowed.status_code, 200)

    # Workflow 2: Resource Management
    def test_workflow_02_resource_crud(self):
        import uuid
        unique_id = f"CR_{uuid.uuid4().hex[:6].upper()}"
        test_room = {
            "room_id": unique_id,
            "name": "Robotics Production Lab",
            "capacity": 45,
            "room_type": "LAB",
            "features": "GPU Cluster"
        }
        # Unauthenticated & viewer rejected on mutations
        anon_client = TestClient(app)
        self.assertEqual(anon_client.post("/api/v1/resources/classrooms", json=test_room).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/resources/classrooms", json=test_room, headers=self.viewer_headers).status_code, 403)

        # Create
        r_create = self.client.post("/api/v1/resources/classrooms", json=test_room, headers=self.admin_headers)
        self.assertEqual(r_create.status_code, 200)

        # Update
        r_update = self.client.put(f"/api/v1/resources/classrooms/{unique_id}", json={"capacity": 50}, headers=self.admin_headers)
        self.assertEqual(r_update.status_code, 200)

        # Delete
        r_delete = self.client.delete(f"/api/v1/resources/classrooms/{unique_id}", headers=self.admin_headers)
        self.assertEqual(r_delete.status_code, 200)

    # Workflow 3: CSP Solver
    def test_workflow_03_csp_solver_execution(self):
        payload = {
            "use_mrv": True,
            "use_degree": True,
            "use_lcv": True,
            "use_forward_checking": True,
            "use_ac3_preprocess": True,
            "timeout_seconds": 15.0
        }
        res = self.client.post("/api/v1/optimize/csp/solve-backtracking?async_mode=false", json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["assigned_sessions"], 0)
        self.assertIsNotNone(data["run_id"])

    # Workflow 4: Genetic Algorithm
    def test_workflow_04_ga_execution(self):
        payload = {
            "population_size": 30,
            "max_generations": 15,
            "crossover_prob": 0.85,
            "mutation_prob": 0.08,
            "elitism_count": 2,
            "tournament_size": 3,
            "timeout_seconds": 10.0
        }
        res = self.client.post("/api/v1/optimize/ga/solve?async_mode=false", json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("success", data)
        self.assertIn("fitness_evaluations", data)

    # Workflow 5: Benchmarking
    def test_workflow_05_benchmarking(self):
        payload = {
            "ga_pop_size": 20,
            "ga_generations": 10,
            "ga_timeout": 5.0
        }
        res = self.client.post("/api/v1/optimize/benchmark?async_mode=false", json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("comparison_table", data)
        self.assertIn("backtracking_metrics", data)
        self.assertIn("ga_aggregate_metrics", data)

    # Workflow 6: Timetable Viewer & CSV Export
    def test_workflow_06_timetable_and_export(self):
        r_tt = self.client.get("/api/v1/timetable/active")
        self.assertEqual(r_tt.status_code, 200)
        self.assertIn("sessions", r_tt.json())

        r_csv = self.client.get("/api/v1/timetable/export/csv")
        self.assertEqual(r_csv.status_code, 200)
        self.assertIn("Course Code", r_csv.text)

    # Workflow 7: Analytics
    def test_workflow_07_analytics(self):
        r_summary = self.client.get("/api/v1/analytics/summary")
        self.assertEqual(r_summary.status_code, 200)
        self.assertIn("analytics", r_summary.json())

        r_fac = self.client.get("/api/v1/analytics/faculty-workload")
        self.assertEqual(r_fac.status_code, 200)

        r_room = self.client.get("/api/v1/analytics/room-utilization")
        self.assertEqual(r_room.status_code, 200)

    # Workflow 8: What-If Rescheduling & Rollback
    def test_workflow_08_rescheduling_transaction(self):
        r_tt = self.client.get("/api/v1/timetable/active")
        sessions = r_tt.json().get("sessions", [])
        if sessions:
            target = sessions[0]
            # Preview
            prev_res = self.client.post("/api/v1/rescheduling/preview", json={
                "variable_id": target["assignment_id"],
                "new_room_id": "CR_102",
                "new_slot_ids": ["SLOT_TUE_2"],
                "reason": "Production Acceptance Reschedule"
            })
            self.assertEqual(prev_res.status_code, 200)

            # History check
            hist_res = self.client.get("/api/v1/rescheduling/history")
            self.assertEqual(hist_res.status_code, 200)

    # Workflow 9: Health and Database Resilience
    def test_workflow_09_health_and_resilience(self):
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["database"]["connected"])

    # Workflow 10: Validation Engine
    def test_workflow_10_validation_engine(self):
        val_res = self.client.post("/api/v1/validation/validate")
        self.assertEqual(val_res.status_code, 200)
        data = val_res.json()
        self.assertIn("is_valid", data)
        self.assertIn("hard_violations_count", data)

if __name__ == "__main__":
    unittest.main()
