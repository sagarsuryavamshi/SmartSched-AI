# SmartSched AI: Automated University Timetable Generation using Constraint-Based Search & Evolutionary Metaheuristics

## Formal Academic & Engineering Technical Report
**Project:** SmartSched AI  
**Academic Level:** University Senior Project / Master's Capstone  
**Authors & System Architects:** Senior AI Research Team  
**Technology Stack:** Python 3.9, SQLite 3, Streamlit, Plotly, NumPy, Pandas, ReportLab  
**Release Version:** 1.0.0 (Production Release — Phase 7)

---

## 1. PROJECT ABSTRACT

University course timetabling is a notoriously complex, NP-hard combinatorial optimization challenge. Academic institutions must schedule dozens of courses, theoretical lectures, multi-hour laboratory practicals, specialized facilities, and faculty members across weekly timeslots while strictly satisfying physical, biological, and administrative constraints. This report presents **SmartSched AI**, a production-grade, constraint-based academic scheduling and optimization system. SmartSched AI integrates two distinct algorithmic paradigms: an exact **Backtracking Constraint Satisfaction Problem (CSP)** solver enhanced with Minimum Remaining Values (MRV), Degree, Least Constraining Value (LCV), and Arc Consistency (AC-3) inference; and a domain-aware **Genetic Algorithm (GA)** metaheuristic featuring chromosome repair and multi-objective soft optimization. The platform features an interactive weekly timetable matrix, real-time analytics, transactional "What-If" rescheduling with full constraint rejection ($H_1$–$H_8$) and atomic rollback, and a guided 10-step administrative optimization wizard.

---

## 2. PROBLEM STATEMENT

Manual timetable construction in university departments requires days of trial-and-error, frequently leading to:
1. **Resource Collisions:** Faculty double-booking, classroom occupancy conflicts, or cohort simultaneous session clashes.
2. **Pedagogical Inefficiencies:** Broken multi-hour laboratory continuity, excessive consecutive lectures, or assigning practical labs to generic lecture halls.
3. **Faculty Fatigue & Student Dissatisfaction:** Unbalanced daily workloads, undesirable scheduling outside faculty availability windows, and fragmented idle gaps between classes.

The automated course timetabling problem requires assigning each session $x_i$ to a timeslot $t$ and room $r$ such that no hard physical constraint is violated, while simultaneously minimizing soft penalty objectives.

---

## 3. PROJECT OBJECTIVES

1. Formulate the university scheduling challenge into a rigorous mathematical CSP model $(X, D, C)$.
2. Enforce eight non-negotiable Hard Constraints ($H_1$–$H_8$) guaranteeing zero-conflict feasibility.
3. Optimize four Soft Objectives ($S_1$–$S_4$) evaluating faculty preferences, idle time, consecutive lectures, and daily workload balance.
4. Develop and contrast an exact CSP Backtracking Search engine against a Genetic Algorithm optimizer.
5. Provide administrative safety through atomic SQLite transactions, What-If rescheduling diagnostics, and one-click rollback.
6. Deliver interactive weekly visualizations, analytical dashboards, and official PDF/CSV exports.

---

## 4. SYSTEM ARCHITECTURE

SmartSched AI follows a modular, layered software architecture:

```
+---------------------------------------------------------------------------+
|                     Presentation Layer (Streamlit UI)                    |
|  - 10-Step Wizard       - Interactive Matrix      - Analytics Dashboard   |
|  - What-If Rescheduler  - Violation Inspector     - Data Management CRUD  |
+---------------------------------------------------------------------------+
                                     |
+---------------------------------------------------------------------------+
|                      Optimization & Search Engines                        |
|  +-------------------------------+   +---------------------------------+  |
|  |     Exact CSP Solver          |   |    Genetic Algorithm Engine     |  |
|  | - Backtracking Search         |   | - Tournament Selection          |  |
|  | - MRV & Degree Heuristics     |   | - Two-Point Crossover           |  |
|  | - LCV Value Ordering          |   | - Uniform Gene Mutation         |  |
|  | - AC-3 & Forward Checking     |   | - Domain-Aware Chromosome Repair|  |
|  +-------------------------------+   +---------------------------------+  |
+---------------------------------------------------------------------------+
                                     |
+---------------------------------------------------------------------------+
|                      Constraint Evaluation Layer                          |
|  - Hard Constraints (H1-H8): Physical & Administrative Invariants         |
|  - Soft Objectives (S1-S4): Preference Penalties & Workload Optimization  |
|  - What-If Rescheduling Engine: Difference Evaluation & Delta Scoring     |
+---------------------------------------------------------------------------+
                                     |
+---------------------------------------------------------------------------+
|                      Data & Persistence Layer                             |
|  - SQLite 3 Relational Database (WAL Mode, Foreign Key Cascade Locks)     |
|  - Tables: classrooms, faculty, student_groups, courses, timeslots,       |
|            scheduled_assignments, rescheduling_history                    |
+---------------------------------------------------------------------------+
```

---

## 5. MATHEMATICAL CSP FORMULATION

The Course Timetabling Problem is formally formulated as a Constraint Satisfaction Problem:
$$\mathcal{P} = \langle X, D, C \rangle$$

### 5.1 Variables ($X$)
Let $X = \{x_1, x_2, \dots, x_N\}$ represent the required weekly teaching sessions. Each variable $x_i$ represents an indivisible scheduling requirement defined by the tuple:
$$x_i = \langle \text{course\_id}, \text{faculty\_id}, \text{group\_id}, \text{session\_type}, \text{duration\_hours}, \text{required\_room\_type} \rangle$$
Where:
- $\text{session\_type} \in \{\text{THEORY}, \text{LAB}\}$
- $\text{duration\_hours} \in \{1, 2\}$

For our standard reference academic benchmark, $N = 24$ variables (21 theory sessions of 1 hour, and 3 laboratory sessions of 2 hours, totaling 27 teaching hours).

### 5.2 Domains ($D$)
Each variable $x_i$ has a discrete domain $D_i$ representing the set of valid room-timeslot candidate assignments:
$$D_i = \{ v = \langle r, t_1, \dots, t_k \rangle \mid r \in R, t_j \in T \}$$
Where:
- $R$ is the set of university classrooms and laboratories.
- $T$ is the set of scheduled institutional timeslots across Monday to Saturday.
- $k = \text{duration\_hours}(x_i)$.

### 5.3 Domain Pre-Filtering
Before search initiation, domains are pre-filtered using unary constraints:
1. **Room Type Matching:** $v.r.\text{type} == x_i.\text{required\_room\_type}$.
2. **Room Capacity:** $v.r.\text{capacity} \ge \text{group\_size}(x_i.\text{group\_id})$.
3. **Faculty Availability Window:** $v.t_j \in \text{working\_slots}(x_i.\text{faculty\_id})$.
4. **Institutional Break Avoidance:** $v.t_j.\text{is\_break} == 0$.
5. **Laboratory Continuity:** If $k = 2$, $v.t_2.\text{start\_time} == v.t_1.\text{end\_time} \land v.t_2.\text{day} == v.t_1.\text{day}$.

---

## 6. HARD CONSTRAINTS ($H_1$–$H_8$)

A timetable assignment $A$ is **feasible** if and only if all eight hard constraints are satisfied:
$$\sum_{k=1}^8 \text{violations}(H_k) = 0$$

1. **$H_1$: Faculty Conflict-Free Scheduling**  
   No faculty member can instruct more than one session at any identical timeslot $t$:
   $$\forall x_i, x_j \in X \ (i \ne j), \ A(x_i).\text{faculty} = A(x_j).\text{faculty} \implies A(x_i).\text{slots} \cap A(x_j).\text{slots} = \emptyset$$

2. **$H_2$: Classroom Occupancy Invariant**  
   No classroom or laboratory $r$ can host multiple sessions simultaneously:
   $$\forall x_i, x_j \in X \ (i \ne j), \ A(x_i).\text{room} = A(x_j).\text{room} \implies A(x_i).\text{slots} \cap A(x_j).\text{slots} = \emptyset$$

3. **$H_3$: Student Cohort Clash Prevention**  
   A student group $g$ cannot attend concurrent sessions:
   $$\forall x_i, x_j \in X \ (i \ne j), \ A(x_i).\text{group} = A(x_j).\text{group} \implies A(x_i).\text{slots} \cap A(x_j).\text{slots} = \emptyset$$

4. **$H_4$: Classroom Seating Capacity**  
   Classroom capacity must accommodate enrolled students:
   $$\forall x_i \in X, \ \text{capacity}(A(x_i).\text{room}) \ge \text{group\_size}(x_i.\text{group})$$

5. **$H_5$: Faculty Availability & Contract Days**  
   Sessions must occur on days and timeslots when the instructor is available:
   $$\forall x_i \in X, \ A(x_i).\text{day} \in \text{work\_days}(x_i.\text{faculty}) \land A(x_i).\text{slots} \cap \text{unavail}(x_i.\text{faculty}) = \emptyset$$

6. **$H_6$: Facility Type Matching**  
   Theory classes must be assigned to lecture halls; labs must be assigned to specialized laboratories:
   $$\forall x_i \in X, \ \text{type}(A(x_i).\text{room}) = x_i.\text{required\_room\_type}$$

7. **$H_7$: Multi-Hour Laboratory Continuity**  
   Multi-hour practicals must be allocated to strictly contiguous slots on the same day without intermission:
   $$\forall x_i \in X \text{ where } x_i.\text{duration} = 2, \ \text{slot}_2.\text{start} = \text{slot}_1.\text{end} \land \text{slot}_2.\text{day} = \text{slot}_1.\text{day}$$

8. **$H_8$: Working Hours & Recess Observance**  
   No class can be scheduled outside operating hours or during institutional lunch periods:
   $$\forall x_i \in X, \ \forall s \in A(x_i).\text{slots}, \ \text{is\_break}(s) = 0$$

---

## 7. SOFT OBJECTIVES ($S_1$–$S_4$)

Soft objectives model institutional preference satisfaction and academic quality-of-life. Each objective carries an empirical penalty weight $w_k$:

$$P_{\text{soft}}(A) = w_1 S_1(A) + w_2 S_2(A) + w_3 S_3(A) + w_4 S_4(A)$$

1. **$S_1$: Faculty Preferred Timeslots ($w_1 = 1.0$)**  
   Penalizes scheduling faculty outside their preferred morning or afternoon time preferences.
2. **$S_2$: Minimizing Faculty Idle Gaps ($w_2 = 2.0$)**  
   Penalizes fragmented waiting intervals ($>1$ hour) between an instructor's classes on the same day.
3. **$S_3$: Avoiding Consecutive Heavy Lectures ($w_3 = 1.5$)**  
   Penalizes scheduling 3 or more consecutive theoretical lectures for any student cohort without a rest period.
4. **$S_4$: Balanced Daily Cohort Workload ($w_4 = 1.0$)**  
   Penalizes variance in student daily teaching hours across Monday through Saturday, encouraging evenly distributed academic effort.

---

## 8. BACKTRACKING CSP SEARCH ALGORITHM

SmartSched AI implements systematic depth-first backtracking search equipped with classic AI heuristics:

### 8.1 Variable Ordering Heuristics
- **Minimum Remaining Values (MRV):** Selects the unassigned variable with the smallest remaining domain size $|D_i|$.
- **Degree Heuristic:** Breaks MRV ties by selecting the variable involved in the highest number of constraints with other unassigned variables.

### 8.2 Value Ordering Heuristic
- **Least Constraining Value (LCV):** Evaluates candidate values in order of how few choices they rule out for neighboring unassigned variables.

### 8.3 Constraint Propagation
- **Forward Checking (FC):** Prunes incompatible values from neighboring domains immediately following an assignment.
- **Arc Consistency (AC-3):** Enforces arc consistency over the binary constraint network before search and optionally at search nodes:
  $$\forall (X_i, X_j) \in \text{Arcs}, \ \forall v_i \in D_i, \ \exists v_j \in D_j \text{ s.t. } \text{compatible}(v_i, v_j)$$

---

## 9. GENETIC ALGORITHM METAHEURISTIC

The Genetic Algorithm solver searches the discrete combinatorial solution space using simulated biological evolution:

### 9.1 Chromosome Encoding
Each chromosome consists of $N = 24$ genes:
$$C = [g_1, g_2, \dots, g_N], \quad g_i \in D_i$$
Genes represent direct domain index pointers or value tuples $\langle r, s \rangle$.

### 9.2 Fitness Function Formulation
To guarantee that **every feasible schedule strictly outranks any infeasible candidate**, a weighted penalty fitness function is defined:
$$F(C) = \frac{1}{1.0 + W_{\text{hard}} \cdot V_{\text{hard}}(C) + P_{\text{soft}}(C)}$$
Where $W_{\text{hard}} = 50,000$.

### 9.3 Evolutionary Operators
1. **Tournament Selection:** Selects individuals from tournaments of size $k = 3$.
2. **Two-Point Crossover:** Exchanges genetic segments between paired parents with probability $P_c = 0.85$.
3. **Uniform Gene Mutation:** Replaces genes with alternative domain values with probability $P_m = 0.08$.
4. **Domain-Aware Chromosome Repair:** Automatically detects collisions ($H_1, H_2, H_3$) and applies localized greedy reassignments from $D_i$.
5. **Elitism:** Directly preserves the top $E = 2$ fittest individuals into the next generation.

---

## 10. EXPERIMENTAL BENCHMARK RESULTS

Experiments conducted on macOS (Darwin arm64, Apple Silicon) using the 24-variable university reference benchmark:

| Metric / Parameter | Exact Backtracking (MRV + LCV + FC) | Genetic Algorithm (60 Pop, 40 Gens) |
| :--- | :--- | :--- |
| **Feasibility Rate** | 100% (Guaranteed) | 100% (Across 10 Random Seeds) |
| **Execution Time** | 0.024 seconds | 0.82 seconds |
| **Hard Violations** | 0 | 0 |
| **Soft Penalty Score** | 346.0 | **12.0 (Mean) / 5.0 (Best)** |
| **Quality Improvement**| Baseline | **+96.5% Soft Penalty Reduction** |
| **Search Operations** | 24 Nodes, 0 Backtracks | 2,400 Candidate Evaluations |

**Key Finding:** Backtracking delivers instantaneous feasibility (0.024s) for operational scheduling, while the Genetic Algorithm achieves human-centric optimality with superior soft penalty minimization.

---

## 11. DATABASE SCHEMA & DATA DICTIONARY

The underlying SQLite database enforces relational integrity with `PRAGMA foreign_keys = ON;`:

1. **`classrooms`**: `room_id` (PK), `name`, `capacity`, `room_type`, `building`.
2. **`faculty`**: `faculty_id` (PK), `name`, `email`, `department`, `max_hours_per_week`.
3. **`student_groups`**: `group_id` (PK), `name`, `size`, `department`.
4. **`courses`**: `course_id` (PK), `code`, `title`, `weekly_hours`, `category`, `required_room_type`, `assigned_faculty_id` (FK), `target_group_id` (FK).
5. **`timeslots`**: `slot_id` (PK), `day`, `start_time`, `end_time`, `is_break`.
6. **`scheduled_assignments`**: `assignment_id` (PK), `run_id`, `course_id` (FK), `room_id` (FK), `slot_id` (FK), `faculty_id` (FK), `group_id` (FK), `created_at`.
7. **`rescheduling_history`**: `id` (PK), `change_id`, `session_id`, `course_code`, `group_id`, `faculty_id`, `old_room_id`, `old_slot_id`, `old_day`, `old_start_time`, `new_room_id`, `new_slot_id`, `new_day`, `new_start_time`, `status`, `reason`, `timestamp`.

---

## 12. WHAT-IF RESCHEDULING & ATOMIC ROLLBACK

SmartSched AI provides administrative scenario planning without compromising schedule integrity:
- **Pre-Commit Evaluation:** `evaluate_what_if_reschedule` runs proposed modifications through the complete constraint validator, reporting hard conflicts and soft score deltas ($\Delta S$) before database alteration.
- **Continuous 2-Hour Lab Selector:** Laboratory practicals are selected and assigned as paired continuous slots on the same day.
- **ACID Transaction Commits:** Updates execute in an atomic SQLite transaction via `apply_reschedule_transaction`.
- **One-Click Rollback:** `rollback_reschedule_transaction` restores the previous room and slot IDs with 100% precision.

---

## 13. INSTALLATION & SETUP GUIDE

### Prerequisites
- Python 3.9+ installed.
- Git & SQLite 3.

### Quickstart Installation
```bash
# 1. Clone repository
git clone https://github.com/organization/smartsched-ai.git
cd smartsched-ai

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install production dependencies
pip install -r requirements.txt

# 4. Initialize database and seed synthetic benchmark data
python scripts/init_db.py
python scripts/seed_data.py --overwrite

# 5. Launch application
streamlit run app.py
```
Access the application at `http://localhost:8501`.

---

## 14. DOCKER & CONTAINERIZED DEPLOYMENT

### Docker Run
```bash
# Build production image
docker build -t smartsched-ai:latest .

# Run container with persistent SQLite volume
docker run -d -p 8501:8501 -v smartsched_data:/app/data --name smartsched smartsched-ai:latest
```

### Docker Compose
```bash
docker-compose up -d
```

---

## 15. HOSTING PLATFORM RECOMMENDATION

### Evaluation of Target Environments:
1. **Google Cloud Run (Recommended for Enterprise GCP):**
   - Containerized stateless execution with automatic SSL and zero-scaling cost.
   - Persistence achieved by mounting Google Cloud Storage (GCS) FUSE or connecting to Cloud SQL SQLite/PostgreSQL.
2. **Render.com / Railway (Recommended for Quick Cloud Hosting):**
   - Native Docker hosting with persistent disk storage attached to `/app/data`.
   - Low cost (\$7/mo) with guaranteed SQLite file persistence.
3. **Streamlit Community Cloud:**
   - Free and convenient for demos, but uses an ephemeral container filesystem (SQLite resets on container sleep without external S3/GCS sync).

---

## 16. USER & ADMINISTRATIVE MANUAL

1. **Dashboard:** View university operational overview, classroom capacities, and active schedules.
2. **10-Step Wizard:** Step-by-step guided flow to configure, solve, validate, and export timetables.
3. **Data Management:** Add, edit, or delete classrooms, faculty members, courses, or student cohorts.
4. **Timetable Viewer:** Filter by department, cohort, or instructor; export CSV and landscape PDF.
5. **Analytics:** Inspect room utilization percentages, faculty workload hours, and soft penalty distributions.
6. **What-If Rescheduling:** Move sessions interactively; preview hard conflicts; commit or roll back changes safely.
7. **Violation Inspector:** Run diagnostic constraint audits on any timetable state.

---

## 17. TESTING & QUALITY ASSURANCE

The test suite contains **93 passing unit tests**:
```bash
./venv/bin/python -m unittest discover -s tests -p "test_*.py"
```
- **Database CRUD & Constraints:** 8 tests.
- **Synthetic Data Loader:** 5 tests.
- **CSP Variable & Domain Construction:** 10 tests.
- **Hard Constraints ($H_1$–$H_8$):** 8 tests.
- **Soft Objectives ($S_1$–$S_4$):** 5 tests.
- **CSP Backtracking & Heuristics:** 19 tests.
- **Genetic Algorithm:** 17 tests.
- **Timetable Visualization & Exports:** 9 tests.
- **What-If Rescheduling & Rollback:** 12 tests.

---

## 18. DEMONSTRATION WORKFLOW

For academic presentations and jury defenses:
1. Navigate to **🏛️ Admin Dashboard** and click **"Reset to Synthetic Seed Data"**.
2. Click **"🎯 Launch 10-Step Wizard"** from Quick Operations.
3. Step through Steps 1 to 5; select **Genetic Algorithm**.
4. Click **"Start Timetable Generation"** in Step 6; observe real-time convergence.
5. Advance to Steps 7 and 8 to showcase **0 Hard Violations** and detailed **Soft Objective scores**.
6. View the interactive schedule grid in Step 9 and download the certified **PDF Report** in Step 10.
7. Navigate to **🔄 What-If Rescheduling**, select a 2-hour laboratory, demonstrate the **Continuous 2-Hour Block Selector**, commit an atomic adjustment, and trigger an **Atomic Rollback**.

---

## 19. SYSTEM LIMITATIONS

1. **Single-Node SQLite Concurrency:** SQLite WAL mode handles concurrent readers safely, but writes are serialized; multi-tenant enterprise deployments with 10,000+ students should adopt PostgreSQL.
2. **Multi-Week Rotating Curricula:** The current formulation assumes a weekly repeating schedule; bi-weekly or modular block schedules require extending timeslots into multi-week horizons.

---

## 20. FUTURE SCOPE & EXTENSIONS

1. **Elective Course Bundling:** Supporting multi-track elective courses where students from different cohorts choose from grouped elective buckets.
2. **Real-Time Notification Dispatch:** Integrating webhook and email alerts to notify faculty and students automatically upon approved schedule adjustments.
3. **Deep Reinforcement Learning (DRL):** Exploring Graph Neural Network (GNN) heuristics for dynamic variable ordering in massive multi-campus university networks.
