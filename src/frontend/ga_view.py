"""Genetic Algorithm & Benchmarking interactive view for Streamlit.

Allows configuration and execution of the Genetic Algorithm timetable generator,
renders real-time evolutionary convergence graphs, displays the generated schedule,
enables timetable persistence to SQLite, and performs scientific side-by-side benchmarks
against the CSP Backtracking solver.
"""

from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.csp_engine.model import CSPModel
from src.database.db_manager import DEFAULT_DB_PATH
from src.database.timetable_repository import save_timetable_solution
from src.frontend.components import render_metric_card
from src.ga_engine.benchmark import run_comparative_benchmark, run_equal_time_budget_benchmark
from src.ga_engine.genetic_solver import GAConfig, GAResult, GeneticSolver


def render_ga_view() -> None:
    """Renders the comprehensive Genetic Algorithm & Benchmarking interface."""
    st.markdown('<div class="main-header">Genetic Algorithm & Algorithmic Benchmarking</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Stochastic metaheuristic evolutionary scheduling and comparative performance analysis against systematic Backtracking CSP.</div>',
        unsafe_allow_html=True,
    )

    tab_ga, tab_bench = st.tabs([
        "🧬 Genetic Algorithm Timetable Generator",
        "⚔️ Backtracking vs Genetic Algorithm Benchmark",
    ])

    with tab_ga:
        _render_ga_generator_tab()

    with tab_bench:
        _render_benchmark_tab()


def _render_ga_generator_tab() -> None:
    """Sub-view for GA configuration, execution, convergence graphs, and schedule matrix."""
    st.markdown("### ⚙️ Evolutionary Hyperparameters")
    st.caption("Configure population genetics, operator probabilities, and selection pressure.")

    c1, c2, c3 = st.columns(3)
    with c1:
        pop_size = st.slider("Population Size", min_value=20, max_value=300, value=100, step=10)
        generations = st.slider("Max Generations", min_value=20, max_value=500, value=120, step=10)
        seed = st.number_input("Random Seed (for reproducibility)", value=42, step=1)

    with c2:
        crossover_prob = st.slider("Crossover Probability (Uniform)", min_value=0.2, max_value=1.0, value=0.85, step=0.05)
        mutation_prob = st.slider("Mutation Probability (Per-Gene)", min_value=0.01, max_value=0.30, value=0.08, step=0.01)
        tournament_size = st.slider("Tournament Selection Size", min_value=2, max_value=10, value=3, step=1)

    with c3:
        elitism_count = st.number_input("Elitism Count (Elite Preserved)", min_value=1, max_value=20, value=4, step=1)
        enable_repair = st.checkbox("Enable Constraint Repair Heuristic", value=True, help="Applies targeted reassignment for variables causing H1-H8 clashes.")
        timeout_sec = st.number_input("Timeout (Seconds)", min_value=5.0, max_value=120.0, value=30.0, step=5.0)

    config = GAConfig(
        population_size=int(pop_size),
        max_generations=int(generations),
        crossover_prob=float(crossover_prob),
        mutation_prob=float(mutation_prob),
        elitism_count=int(elitism_count),
        tournament_size=int(tournament_size),
        random_seed=int(seed) if seed is not None else 42,
        timeout_seconds=float(timeout_sec),
        enable_repair=enable_repair,
    )

    st.markdown("---")

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        run_ga_clicked = st.button("🧬 Run Genetic Algorithm", type="primary", use_container_width=True)
    with col_info:
        st.caption("Initializes chromosome population from SQLite domains, applies evolutionary crossover, mutation, and repair, and evaluates against H1-H8 & S1-S4.")

    if run_ga_clicked:
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def ga_progress_callback(curr_gen: int, total_gen: int, best_chr) -> None:
            pct = min(1.0, curr_gen / max(1, total_gen))
            progress_bar.progress(pct)
            status_text.caption(f"Generation {curr_gen}/{total_gen} | Best Hard Violations: {best_chr.hard_violations_count} | Soft Penalty: {best_chr.soft_penalty:.1f}")

        with st.spinner("Executing Genetic Algorithm evolutionary cycle..."):
            model = CSPModel.build_from_db(DEFAULT_DB_PATH)
            solver = GeneticSolver(model)
            ga_result = solver.solve(config, callback=ga_progress_callback)
            st.session_state["ga_result"] = ga_result
            st.session_state["ga_model"] = model

        progress_bar.progress(1.0)
        status_text.empty()

    ga_res: Optional[GAResult] = st.session_state.get("ga_result")
    ga_model: Optional[CSPModel] = st.session_state.get("ga_model")

    if ga_res is None:
        st.info("💡 Click **'🧬 Run Genetic Algorithm'** above to start evolutionary timetable generation.")
        return

    best = ga_res.best_chromosome
    st.markdown("### 📊 Evolutionary Execution Telemetry")

    # Top KPI Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        status_label = "✅ FEASIBLE" if ga_res.is_solution_found else f"❌ {best.hard_violations_count} VIOLATIONS"
        render_metric_card("Solution Status", status_label, "🎯")
    with m2:
        render_metric_card("Best Fitness", f"{best.fitness:.6f}" if best else "0.0", "🧬")
    with m3:
        render_metric_card("Hard Violations", str(best.hard_violations_count) if best else "N/A", "⚖️")
    with m4:
        render_metric_card("Soft Penalty", f"{best.soft_penalty:.1f}" if best else "N/A", "📉")
    with m5:
        render_metric_card("Runtime", f"{ga_res.execution_time_seconds:.2f}s", "⚡")

    st.markdown("<br>", unsafe_allow_html=True)

    # Secondary KPI Row
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Generations Completed", f"{ga_res.generations_completed} / {config.max_generations}")
    with s2:
        st.metric("Fitness Evaluations", f"{ga_res.fitness_evaluations:,}")
    with s3:
        st.metric("Mutations / Crossovers", f"{ga_res.mutation_operations:,} / {ga_res.crossover_operations:,}")
    with s4:
        st.metric("Repairs Applied", f"{ga_res.successful_repairs:,} / {ga_res.repair_attempts:,}")

    st.markdown("---")

    # Convergence Visualization
    st.markdown("### 📈 Evolutionary Convergence Graphs")
    col_g1, col_g2 = st.columns(2)

    gen_axis = list(range(len(ga_res.history_best_fitness)))

    with col_g1:
        fig_fit = go.Figure()
        fig_fit.add_trace(go.Scatter(x=gen_axis, y=ga_res.history_best_fitness, mode="lines", name="Best Fitness", line=dict(color="#00C853", width=2.5)))
        fig_fit.add_trace(go.Scatter(x=gen_axis, y=ga_res.history_avg_fitness, mode="lines", name="Mean Population Fitness", line=dict(color="#29B6F6", width=1.5, dash="dot")))
        fig_fit.update_layout(
            title="Fitness Progression Across Generations",
            xaxis_title="Generation",
            yaxis_title="Fitness Score",
            template="plotly_dark",
            height=340,
        )
        st.plotly_chart(fig_fit, use_container_width=True)

    with col_g2:
        fig_pen = go.Figure()
        fig_pen.add_trace(go.Scatter(x=gen_axis, y=ga_res.history_best_hard_violations, mode="lines+markers", name="Hard Violations (H1-H8)", line=dict(color="#FF5252", width=2)))
        fig_pen.add_trace(go.Scatter(x=gen_axis, y=ga_res.history_best_soft_penalty, mode="lines", name="Soft Penalty (S1-S4)", line=dict(color="#FFA726", width=2)))
        fig_pen.update_layout(
            title="Constraint Penalties Across Generations",
            xaxis_title="Generation",
            yaxis_title="Penalty Value",
            template="plotly_dark",
            height=340,
        )
        st.plotly_chart(fig_pen, use_container_width=True)

    st.markdown("---")

    # Solution Details and Schedule Table
    if ga_res.is_solution_found and best:
        st.success(f"🎉 **{ga_res.message}**")

        c_sum1, c_sum2 = st.columns([1, 1])
        with c_sum1:
            st.markdown("#### Soft Constraint Score Breakdown")
            rep = best.validation_report
            if rep:
                st.markdown(f"- **Total Soft Penalty:** `{rep.soft_penalty_score:.1f}`")
                st.markdown(f"  - S1 (Faculty Preferred Slots): `Penalty {rep.summary_by_constraint['S1']['penalty']:.1f}`")
                st.markdown(f"  - S2 (Faculty Idle Gaps): `Penalty {rep.summary_by_constraint['S2']['penalty']:.1f}`")
                st.markdown(f"  - S3 (Consecutive Theory Lectures): `Penalty {rep.summary_by_constraint['S3']['penalty']:.1f}`")
                st.markdown(f"  - S4 (Daily Student Workload): `Penalty {rep.summary_by_constraint['S4']['penalty']:.1f}`")

        with c_sum2:
            st.markdown("#### Timetable Persistence")
            st.write("Persist this schedule to the official SQLite database.")
            confirm_save = st.checkbox("Confirm overwrite of existing timetable assignments", value=False)
            save_btn = st.button("💾 Save GA Timetable to SQLite", type="secondary", disabled=not confirm_save, use_container_width=True)

            if save_btn:
                ok, msg = save_timetable_solution(
                    assignment=best.genes,
                    variables_map=ga_model.variables_map,
                    overwrite_existing=True,
                )
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

        # Schedule Matrix Table
        st.markdown("#### Generated Timetable Schedule Matrix")
        schedule_rows = []
        for v_id, val in best.genes.items():
            var = ga_model.variables_map.get(v_id)
            if var:
                schedule_rows.append({
                    "Course": f"{var.course_code} - {var.session_type.value}",
                    "Session": f"Session {var.session_num}",
                    "Day": val.day,
                    "Time": f"{val.start_time} - {val.end_time}",
                    "Classroom": val.room_id,
                    "Instructor": val.faculty_id,
                    "Cohort": val.group_id,
                    "Slot ID(s)": ", ".join(val.slot_ids),
                })

        df_sched = pd.DataFrame(schedule_rows)
        day_order = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}
        df_sched["day_num"] = df_sched["Day"].map(day_order)
        df_sched.sort_values(by=["day_num", "Time"], inplace=True)
        df_sched.drop(columns=["day_num"], inplace=True)
        st.dataframe(df_sched, use_container_width=True, hide_index=True)

    else:
        st.error(f"❌ **{ga_res.message}**")
        st.warning(
            "The Genetic Algorithm did not converge to a 0-violation timetable within the configured generation budget. "
            "Try increasing the population size (e.g. 150), maximum generations (e.g. 200), or verifying the random seed."
        )


def _render_benchmark_tab() -> None:
    """Sub-view for side-by-side scientific comparison between CSP Backtracking and GA."""
    st.markdown("### ⚔️ Systematic CSP vs. Stochastic Metaheuristic Benchmark")
    st.markdown(
        """
        **Scientific Paradigm Comparison:**
        - **Backtracking CSP (Systematic Search):** Complete, deterministic tree search augmented with constraint propagation (AC-3, Forward Checking) and heuristics (MRV, Degree, LCV). Mathematically proves satisfiability or infeasibility.
        - **Genetic Algorithm (Stochastic Search):** Incomplete, population-based probabilistic search using biologically inspired selection, crossover, and mutation. Explores diverse areas of search space, trading completeness for soft-constraint optimization flexibility.
        """
    )

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        num_seeds = st.selectbox("GA Evaluation Seeds Count", [3, 5, 10], index=1, help="Runs GA across multiple deterministic seeds to calculate statistical mean and variance.")
    with col_b2:
        b_pop = st.slider("Benchmark GA Population", 50, 200, 100, 10)
    with col_b3:
        b_gen = st.slider("Benchmark GA Generations", 50, 200, 100, 10)

    if st.button("🚀 Execute Scientific Benchmark", type="primary"):
        with st.spinner("Running side-by-side comparative benchmark..."):
            model = CSPModel.build_from_db(DEFAULT_DB_PATH)
            seeds = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909][:num_seeds]
            bench_res = run_comparative_benchmark(
                model=model,
                seeds=seeds,
                ga_pop_size=int(b_pop),
                ga_generations=int(b_gen),
            )
            st.session_state["bench_result"] = bench_res

    bench_res = st.session_state.get("bench_result")
    if bench_res is None:
        st.info("💡 Click **'Execute Scientific Benchmark'** above to generate empirical comparison metrics.")
        return

    st.markdown("---")
    st.markdown("### 📊 Head-to-Head Comparison Table")
    df_cmp = pd.DataFrame(bench_res.comparison_table)
    st.table(df_cmp)

    # Graphical Comparisons
    st.markdown("### 📈 Visual Comparative Analytics")
    c_chart1, c_chart2 = st.columns(2)

    with c_chart1:
        # Runtime Comparison
        df_time = pd.DataFrame([
            {"Algorithm": "Backtracking CSP", "Runtime (s)": bench_res.backtracking_metrics["execution_time_seconds"]},
            {"Algorithm": "Genetic Algorithm (Mean)", "Runtime (s)": bench_res.ga_aggregate_metrics["mean_execution_time_seconds"]},
        ])
        fig_time = px.bar(df_time, x="Algorithm", y="Runtime (s)", title="Execution Runtime Comparison (Lower is Faster)", color="Algorithm", text_auto=".3f")
        fig_time.update_layout(template="plotly_dark", height=320, showlegend=False)
        st.plotly_chart(fig_time, use_container_width=True)

    with c_chart2:
        # Soft Constraint Score Comparison
        df_soft = pd.DataFrame([
            {"Algorithm": "Backtracking CSP", "Soft Penalty Score": bench_res.backtracking_metrics["soft_penalty"]},
            {"Algorithm": "Genetic Algorithm (Best)", "Soft Penalty Score": bench_res.ga_aggregate_metrics["best_soft_penalty"]},
            {"Algorithm": "Genetic Algorithm (Mean)", "Soft Penalty Score": bench_res.ga_aggregate_metrics["mean_soft_penalty"]},
        ])
        fig_soft = px.bar(df_soft, x="Algorithm", y="Soft Penalty Score", title="Soft Penalty Score (Lower is Better Quality)", color="Algorithm", text_auto=".1f")
        fig_soft.update_layout(template="plotly_dark", height=320, showlegend=False)
        st.plotly_chart(fig_soft, use_container_width=True)

    # Multi-Seed GA Run Details
    st.markdown("### 🎲 Multi-Seed Genetic Algorithm Distribution")
    df_runs = pd.DataFrame(bench_res.ga_individual_runs)
    st.dataframe(df_runs, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### ⏱️ Equal Wall-Clock Time Budget Benchmark")
    st.caption("Allocates an identical execution budget (e.g. 5.0 seconds) to both CSP Depth-First Branch & Bound and the Genetic Algorithm.")

    col_tb1, col_tb2 = st.columns([1, 2])
    with col_tb1:
        time_budget = st.slider("Equal Time Budget (Seconds)", min_value=1.0, max_value=15.0, value=5.0, step=1.0)
        run_equal_btn = st.button("⚖️ Run Equal Time Budget Benchmark", type="secondary", use_container_width=True)

    if run_equal_btn:
        with st.spinner(f"Executing equal {time_budget:.1f}s time budget comparison..."):
            model = CSPModel.build_from_db(DEFAULT_DB_PATH)
            eq_results = run_equal_time_budget_benchmark(model, time_budget_seconds=float(time_budget))
            st.session_state["equal_time_result"] = eq_results

    eq_res = st.session_state.get("equal_time_result")
    if eq_res:
        st.markdown(f"#### Results under Equal {time_budget:.1f}s Time Budget")
        st.table(pd.DataFrame(eq_res))
