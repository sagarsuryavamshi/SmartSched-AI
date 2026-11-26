"""Isolated tests for persistent authentication, RBAC, security, and job persistence."""

import os
import tempfile
import unittest
import uuid
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.security import get_password_hash, verify_password
from src.database.db_manager import get_db_connection, init_db
from src.database.user_repository import create_user, get_user_by_username
from src.database.job_repository import create_job, get_job, update_job_status


class TestAuthAndJobPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_auth_jobs.db")
        init_db(self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_01_password_hashing_and_user_persistence(self):
        raw_pw = "TestAdmin#Secure2026"
        hashed = get_password_hash(raw_pw)
        self.assertNotEqual(raw_pw, hashed)
        self.assertTrue(hashed.startswith("$2"))
        self.assertTrue(verify_password(raw_pw, hashed))
        self.assertFalse(verify_password("wrong-password", hashed))

        ok, _ = create_user(
            username="persisted_admin",
            full_name="Persisted Admin",
            email="persisted_admin@test.edu",
            hashed_password=hashed,
            role="admin",
            db_path=self.db_path,
        )
        self.assertTrue(ok)

        # Simulate restart by reading fresh from DB
        fetched = get_user_by_username("persisted_admin", db_path=self.db_path)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["role"], "admin")
        self.assertNotEqual(fetched["hashed_password"], raw_pw)

        # Verify invalid role rejected
        ok_bad, _ = create_user(
            username="bad_role_user",
            full_name="Bad Role",
            email="bad@test.edu",
            hashed_password=hashed,
            role="superuser",
            db_path=self.db_path,
        )
        self.assertFalse(ok_bad)

    def test_02_job_persistence_across_reads(self):
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        create_job(job_id=job_id, job_type="csp", status="queued", db_path=self.db_path)

        queued = get_job(job_id, db_path=self.db_path)
        self.assertIsNotNone(queued)
        self.assertEqual(queued["status"], "queued")
        self.assertEqual(queued["type"], "csp")

        update_job_status(
            job_id=job_id,
            status="completed",
            result={"success": True, "assigned_sessions": 24},
            completed_at=123456.78,
            db_path=self.db_path,
        )
        completed = get_job(job_id, db_path=self.db_path)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["result"]["assigned_sessions"], 24)

    def test_03_rbac_prevents_public_admin_registration(self):
        # Isolate app DB_PATH to temp DB for this API test
        orig_db = settings.DB_PATH
        settings.DB_PATH = Path(self.db_path)
        try:
            admin_pw = "TestAdmin#9999"
            viewer_pw = "TestViewer#9999"
            create_user("test_admin", "Admin", "a@test.edu", get_password_hash(admin_pw), "admin", db_path=self.db_path)
            create_user("test_viewer", "Viewer", "v@test.edu", get_password_hash(viewer_pw), "viewer", db_path=self.db_path)

            anon = TestClient(app)
            # Anonymous cannot register an admin
            r_anon = anon.post("/api/v1/auth/users", json={
                "username": "rogue_admin",
                "full_name": "Rogue",
                "email": "r@test.edu",
                "password": "RoguePassword123",
                "role": "admin",
            })
            self.assertEqual(r_anon.status_code, 401)

            # Viewer cannot register an admin
            viewer_client = TestClient(app)
            r_vlogin = viewer_client.post("/api/v1/auth/login", json={"username": "test_viewer", "password": viewer_pw})
            self.assertEqual(r_vlogin.status_code, 200)
            v_headers = {"Authorization": f"Bearer {r_vlogin.json()['access_token']}"}

            r_vreg = viewer_client.post("/api/v1/auth/users", json={
                "username": "rogue_admin",
                "full_name": "Rogue",
                "email": "r@test.edu",
                "password": "RoguePassword123",
                "role": "admin",
            }, headers=v_headers)
            self.assertEqual(r_vreg.status_code, 403)

            # Admin CAN create a viewer account
            admin_client = TestClient(app)
            r_alogin = admin_client.post("/api/v1/auth/login", json={"username": "test_admin", "password": admin_pw})
            self.assertEqual(r_alogin.status_code, 200)
            a_headers = {"Authorization": f"Bearer {r_alogin.json()['access_token']}"}

            r_areg = admin_client.post("/api/v1/auth/users", json={
                "username": "new_viewer",
                "full_name": "New Viewer",
                "email": "nv@test.edu",
                "password": "ValidPassword123",
                "role": "viewer",
            }, headers=a_headers)
            self.assertEqual(r_areg.status_code, 200)
        finally:
            settings.DB_PATH = orig_db


if __name__ == "__main__":
    unittest.main()
