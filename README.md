# SmartSched AI 📅

> **Production-Grade Automated University Timetable Generation using Constraint Satisfaction Problem (CSP) Search & Evolutionary Metaheuristics.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-red.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/database-SQLite%203-green.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Passing](https://img.shields.io/badge/tests-93%2F93%20passing-brightgreen.svg)]()

---

## 📖 Overview

**SmartSched AI** is an advanced university-level Artificial Intelligence system that automates the generation of complex, conflict-free academic timetables. It combines two core AI search paradigms:
1. **Exact Constraint Satisfaction Problem (CSP) Solver:** Systematic Backtracking search with Minimum Remaining Values (MRV), Degree Heuristic, Least Constraining Value (LCV), Forward Checking, and Arc Consistency (AC-3) inference.
2. **Genetic Algorithm (GA) Metaheuristic:** Population-based evolutionary search with domain-aware chromosome repair, tournament selection, two-point crossover, and multi-objective soft constraint optimization ($S_1$–$S_4$).

---

## 🚀 Key Features

- **10-Step Guided Optimization Wizard:** Systematic guided administrative workflow from resource review to model compilation, algorithm execution, hard constraint auditing, and export.
- **Eight Enforced Hard Constraints ($H_1$–$H_8$):** Strict zero-conflict guarantees for faculty availability, classroom occupancy, student cohorts, room capacities, room types, lab continuity, and break periods.
- **Four Soft Objectives ($S_1$–$S_4$):** Optimizes faculty preferences, minimizes idle gaps between classes, avoids heavy consecutive lectures, and balances daily cohort workload.
- **Interactive Weekly Grid & Analytics:** Multi-perspective weekly schedules (Department, Faculty, Cohort, Classroom) powered by Plotly, with real-time room utilization and workload metrics.
- **What-If Rescheduling & Atomic Rollback:** Interactive scenario evaluation with delta soft score previews, continuous 2-hour lab block selection, and transaction-safe SQLite commits and rollbacks.
- **Production-Ready Containerization:** Dockerfile and Docker Compose configurations with persistent SQLite volume mounting.

---

## ⚡ Quickstart Installation

### 1. Clone & Setup Environment
```bash
git clone https://github.com/organization/smartsched-ai.git
cd smartsched-ai

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize Database & Synthetic Benchmark Data
```bash
python scripts/init_db.py
python scripts/seed_data.py --overwrite
```

### 3. Launch Web Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🐳 Docker Deployment

Run with Docker:
```bash
docker build -t smartsched-ai:latest .
docker run -d -p 8501:8501 -v smartsched_data:/app/data --name smartsched smartsched-ai:latest
```

Run with Docker Compose:
```bash
docker-compose up -d
```

---

## 🧪 Running Automated Tests

Run the complete regression suite across all 93 unit tests:
```bash
./venv/bin/python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📚 Complete Technical Documentation

For formal mathematical formulation, algorithm pseudocode, and benchmark results, see:
- [docs/ACADEMIC_REPORT.md](docs/ACADEMIC_REPORT.md)
