import unittest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app

class TestFastAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        r_admin = cls.client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@SmartSched2026"})
        cls.admin_headers = {"Authorization": f"Bearer {r_admin.json()['access_token']}"}
        r_viewer = cls.client.post("/api/v1/auth/login", json={"username": "viewer", "password": "Viewer@SmartSched2026"})
        cls.viewer_headers = {"Authorization": f"Bearer {r_viewer.json()['access_token']}"}

    def test_01_health_check(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["database"]["connected"])
        self.assertIn("classrooms", data["database"]["record_counts"])

    def test_02_resources_list(self):
        # Classrooms
        r_rooms = self.client.get("/api/v1/resources/classrooms")
        self.assertEqual(r_rooms.status_code, 200)
        self.assertIsInstance(r_rooms.json(), list)
        self.assertGreater(len(r_rooms.json()), 0)

        # Faculty
        r_fac = self.client.get("/api/v1/resources/faculty")
        self.assertEqual(r_fac.status_code, 200)
        self.assertIsInstance(r_fac.json(), list)
        self.assertGreater(len(r_fac.json()), 0)

        # Groups
        r_grp = self.client.get("/api/v1/resources/groups")
        self.assertEqual(r_grp.status_code, 200)
        self.assertIsInstance(r_grp.json(), list)
        self.assertGreater(len(r_grp.json()), 0)

        # Courses
        r_crs = self.client.get("/api/v1/resources/courses")
        self.assertEqual(r_crs.status_code, 200)
        self.assertIsInstance(r_crs.json(), list)
        self.assertGreater(len(r_crs.json()), 0)

        # Timeslots
        r_slots = self.client.get("/api/v1/resources/timeslots")
        self.assertEqual(r_slots.status_code, 200)
        self.assertIsInstance(r_slots.json(), list)
        self.assertGreater(len(r_slots.json()), 0)

    def test_03_active_timetable_and_analytics(self):
        r_tt = self.client.get("/api/v1/timetable/active")
        self.assertEqual(r_tt.status_code, 200)
        tt_data = r_tt.json()
        self.assertIn("sessions", tt_data)

        # Analytics summary
        r_an = self.client.get("/api/v1/analytics/summary")
        self.assertEqual(r_an.status_code, 200)
        self.assertIn("analytics", r_an.json())

        # Validation
        r_val = self.client.post("/api/v1/validation/validate")
        self.assertEqual(r_val.status_code, 200)
        val_data = r_val.json()
        self.assertIn("is_valid", val_data)

    def test_04_csp_solve_synchronous(self):
        payload = {
            "use_mrv": True,
            "use_degree": True,
            "use_lcv": True,
            "use_forward_checking": True,
            "use_ac3_preprocess": True,
            "timeout_seconds": 10.0
        }
        # Unauthenticated & viewer should be rejected
        anon_client = TestClient(app)
        unauth_res = anon_client.post("/api/v1/optimize/csp/solve-backtracking?async_mode=false", json=payload)
        self.assertEqual(unauth_res.status_code, 401)
        viewer_res = self.client.post("/api/v1/optimize/csp/solve-backtracking?async_mode=false", json=payload, headers=self.viewer_headers)
        self.assertEqual(viewer_res.status_code, 403)

        response = self.client.post("/api/v1/optimize/csp/solve-backtracking?async_mode=false", json=payload, headers=self.admin_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["assigned_sessions"], 0)

    def test_05_reschedule_preview_and_history(self):
        r_tt = self.client.get("/api/v1/timetable/active")
        sessions = r_tt.json().get("sessions", [])
        if sessions:
            first_session = sessions[0]
            preview_payload = {
                "variable_id": first_session["assignment_id"],
                "new_room_id": "CR_102",
                "new_slot_ids": ["SLOT_TUE_2"],
                "reason": "Test unit API reschedule"
            }
            r_prev = self.client.post("/api/v1/rescheduling/preview", json=preview_payload)
            self.assertEqual(r_prev.status_code, 200)
            self.assertIn("is_hard_conflict_free", r_prev.json())

        # Rescheduling history
        r_hist = self.client.get("/api/v1/rescheduling/history")
        self.assertEqual(r_hist.status_code, 200)
        self.assertIsInstance(r_hist.json(), list)

if __name__ == "__main__":
    unittest.main()
