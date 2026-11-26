"""Safe Administrator Bootstrap CLI for SmartSched AI.

Creates the initial administrator (or viewer) account in the configured database
(Neon PostgreSQL when DATABASE_URL is set, or local SQLite otherwise).

Usage:
  # Interactive prompt (recommended):
  python backend/scripts/bootstrap_admin.py

  # Non-interactive via environment variables:
  ADMIN_USERNAME=admin ADMIN_EMAIL=admin@university.edu ADMIN_PASSWORD=... python backend/scripts/bootstrap_admin.py
"""

import getpass
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.core.config import settings
from backend.app.core.security import get_password_hash
from src.database.user_repository import create_user, get_user_by_username


def main() -> int:
    username = os.getenv("ADMIN_USERNAME") or input("Administrator username [admin]: ").strip() or "admin"
    full_name = os.getenv("ADMIN_FULL_NAME") or input("Full name [University Timetable Administrator]: ").strip() or "University Timetable Administrator"
    email = os.getenv("ADMIN_EMAIL") or input("Email [admin@smartsched.edu]: ").strip() or "admin@smartsched.edu"
    role = os.getenv("ADMIN_ROLE", "admin").strip()

    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Password (min 12 chars): ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match.")
            return 1

    if len(password) < 12:
        print("Error: Administrator password must be at least 12 characters.")
        return 1

    db_path = str(settings.DB_PATH)
    if get_user_by_username(username, db_path=db_path):
        print(f"Account '{username}' already exists. No changes made.")
        return 0

    ok, msg = create_user(
        username=username,
        full_name=full_name,
        email=email,
        hashed_password=get_password_hash(password),
        role=role,
        db_path=db_path,
    )
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
