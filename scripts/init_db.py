#!/usr/bin/env python3
"""Database Initialization CLI Utility for SmartSched AI (Production / Deployment)."""

import os
import sys

# Ensure repository root is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.database.db_manager import DEFAULT_DB_PATH, init_db

def main():
    db_path = os.environ.get("SMARTSCHED_DB_PATH", DEFAULT_DB_PATH)
    print(f"Initializing SmartSched AI SQLite database at: {db_path}")
    init_db(db_path)
    print("Database schema successfully initialized and migrated.")

if __name__ == "__main__":
    main()
