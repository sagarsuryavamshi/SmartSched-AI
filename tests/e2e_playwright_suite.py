"""Playwright Browser End-to-End Test Suite for SmartSched AI.

Runs headless Chromium against an isolated local FastAPI + Next.js test stack
backed by a temporary SQLite database (never touches Neon production).
"""

import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
BACKEND_PORT = 8000
FRONTEND_PORT = 3005
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"


def wait_for_http(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status < 500:
                    return
        except Exception:
            time.sleep(0.4)
    raise TimeoutError(f"Server did not become ready at {url} within {timeout}s")


def run_e2e() -> None:
    tmp_dir = tempfile.TemporaryDirectory()
    temp_db = os.path.join(tmp_dir.name, "e2e_smartsched.db")

    env_backend = os.environ.copy()
    env_backend.pop("DATABASE_URL", None)
    env_backend["ENVIRONMENT"] = "development"
    env_backend["SMARTSCHED_DB_PATH"] = temp_db
    env_backend["BOOTSTRAP_ADMIN_USERNAME"] = "e2e_admin"
    env_backend["BOOTSTRAP_ADMIN_PASSWORD"] = "E2EAdmin#Password2026"
    env_backend["CORS_ORIGINS"] = f"http://localhost:{FRONTEND_PORT},http://127.0.0.1:{FRONTEND_PORT}"

    # Start isolated FastAPI backend on port 8000
    backend_proc = subprocess.Popen(
        [
            str(BASE_DIR / "venv" / "bin" / "uvicorn"),
            "backend.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(BACKEND_PORT),
        ],
        cwd=str(BASE_DIR),
        env=env_backend,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    frontend_proc = subprocess.Popen(
        ["npx", "next", "start", "-p", str(FRONTEND_PORT)],
        cwd=str(FRONTEND_DIR),
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    results = []
    try:
        wait_for_http(f"http://127.0.0.1:{BACKEND_PORT}/api/v1/health", timeout=30)
        wait_for_http(FRONTEND_URL, timeout=30)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            # 1. Dashboard loading
            page.goto(FRONTEND_URL, wait_until="networkidle")
            assert "University Timetable Operations Dashboard" in page.content()
            results.append(("Dashboard loading", "PASS"))

            # 2. Invalid login error state + valid Login
            page.get_by_role("button", name="Sign In").click()
            page.fill('input[placeholder="admin or viewer"]', "e2e_admin")
            page.fill('input[placeholder="Enter account password"]', "WrongPass!")
            page.locator("form").get_by_role("button", name="Sign In").click()
            page.wait_for_selector("text=Incorrect username or password", timeout=5000)
            results.append(("Login error state", "PASS"))

            page.fill('input[placeholder="Enter account password"]', "E2EAdmin#Password2026")
            page.locator("form").get_by_role("button", name="Sign In").click()
            page.wait_for_selector("text=Sign Out", timeout=5000)
            results.append(("Login (Admin)", "PASS"))

            # 3. Resource Management (View tabs, Faculty Availability, Timeslot Breaks)
            page.goto(f"{FRONTEND_URL}/resources", wait_until="networkidle")
            assert "Academic Resource Management" in page.content()
            page.get_by_role("button", name="Faculty & Availability").click()
            page.wait_for_timeout(300)
            results.append(("Faculty availability tab", "PASS"))

            page.get_by_role("button", name="Timeslots & Breaks").click()
            page.wait_for_timeout(300)
            results.append(("Timeslots & Breaks tab", "PASS"))

            # 4. Genetic Algorithm Solver
            page.goto(f"{FRONTEND_URL}/genetic", wait_until="networkidle")
            page.get_by_role("button", name="Evolve Timetable with GA").click()
            page.wait_for_selector("text=Genetic Algorithm Evolutionary Telemetry", timeout=20000)
            results.append(("Genetic Algorithm generation", "PASS"))

            # 5. Backtracking CSP Solver (guarantees 0 hard violations in active DB)
            page.goto(f"{FRONTEND_URL}/solver", wait_until="networkidle")
            page.get_by_role("button", name="Execute Backtracking CSP Solver").click()
            page.wait_for_selector("text=CSP Solver Telemetry & Search Results", timeout=15000)
            results.append(("CSP generation", "PASS"))

            # 6. Timetable Viewing
            page.goto(f"{FRONTEND_URL}/timetable", wait_until="networkidle")
            assert "Institutional Academic Timetable" in page.content()
            page.wait_for_selector("text=Live Database", timeout=10000)
            results.append(("Timetable viewing (Live)", "PASS"))

            # 7. Analytics
            page.goto(f"{FRONTEND_URL}/analytics", wait_until="networkidle")
            assert "Institutional Academic Timetable Analytics" in page.content()
            page.wait_for_selector("text=Live Database Records", timeout=10000)
            results.append(("Analytics (Live)", "PASS"))

            # 8. Violation Inspector
            page.goto(f"{FRONTEND_URL}/inspector", wait_until="networkidle")
            page.get_by_role("button", name="Re-run Live Audit").click()
            page.wait_for_selector("text=100% Conflict-Free Feasible Timetable", timeout=10000)
            results.append(("Violation inspector (Live)", "PASS"))

            # 9. Rescheduling Preview & History
            page.goto(f"{FRONTEND_URL}/reschedule", wait_until="networkidle")
            assert "What-If Rescheduling Workbench" in page.content()
            page.get_by_role("button", name="Evaluate What-If Scenario").click()
            page.wait_for_selector("text=Scenario Evaluation: Side-by-Side Comparison", timeout=5000)
            page.locator("button", has_text="Audit History").click()
            page.wait_for_selector("text=Rescheduling Audit Log", timeout=5000)
            results.append(("Rescheduling Preview & History", "PASS"))

            # 10. Mobile Navigation (375x812)
            page.set_viewport_size({"width": 375, "height": 812})
            page.goto(FRONTEND_URL, wait_until="networkidle")
            menu_btn = page.get_by_label("Open navigation menu")
            assert menu_btn.is_visible()
            menu_btn.click()
            page.wait_for_timeout(300)
            results.append(("Mobile navigation drawer", "PASS"))

            # 11. Logout
            page.set_viewport_size({"width": 1440, "height": 900})
            page.get_by_role("button", name="Sign Out").click()
            page.wait_for_selector("text=Sign In", timeout=5000)
            results.append(("Logout", "PASS"))

            browser.close()
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except Exception:
            backend_proc.kill()
        try:
            frontend_proc.wait(timeout=5)
        except Exception:
            frontend_proc.kill()
        tmp_dir.cleanup()

    print("\nPlaywright E2E Results:")
    for name, status in results:
        print(f" - {name}: {status}")
    assert len(results) == 13


if __name__ == "__main__":
    run_e2e()
