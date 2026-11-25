#!/usr/bin/env python3
"""Reproducible Synthetic Academic Data Seeder CLI for SmartSched AI."""

import argparse
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.database.db_manager import DEFAULT_DB_PATH, init_db
from src.data_management.loader import load_dataset_summary, seed_synthetic_data

def main():
    parser = argparse.ArgumentParser(description="Seed synthetic academic dataset into SmartSched AI SQLite database.")
    parser.add_argument("--db-path", default=os.environ.get("SMARTSCHED_DB_PATH", DEFAULT_DB_PATH), help="Target SQLite DB path")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing academic data")
    args = parser.parse_args()

    print(f"Connecting to database at: {args.db_path}")
    init_db(args.db_path)
    seed_synthetic_data(db_path=args.db_path, overwrite=args.overwrite)
    summary = load_dataset_summary(db_path=args.db_path)
    print("Database seeding completed. Summary:")
    for k, v in summary.items():
        print(f" - {k}: {v}")

if __name__ == "__main__":
    main()
