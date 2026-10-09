"""
Generate the evidence charts. All figures are produced from runs of the
simulation engine in it_service_desk_dss_simulation.py (imported directly,
not re-implemented), so every number is traceable back to the model.

Paper figures produced here (seed 7, an independent 30-replication run):
  outputs/evidence_01_scenario_sla_comparison.png   -> Fig. 1
  outputs/evidence_04_emergency_averaging_problem.png -> Fig. 3
Supplementary figures:
  outputs/evidence_02_replication_spread_boxplot.png
  outputs/evidence_03_wait_time_distribution.png

Usage:  python generate_evidence_charts.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))

import matplotlib
matplotlib.use("Agg")

import random
import statistics
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from it_service_desk_dss_simulation import (
    SCENARIOS, PRIORITY_PROFILES, SIM_HOURS, WARMUP_HOURS, NUM_REPLICATIONS,
    SENSITIVITY_ARRIVAL_RATE, EMERGENCY_SURGE, REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT,
    run_single_replication, ServiceDesk, ticket_generator,
)
import simpy

random.seed(7)  # different seed from the main script's demo run, still reproducible

COLORS = {
    "Best Case (low volume, fully staffed)": "#1F8A5F",
    "Baseline (typical week)": "#0E6E64",
    "Worst Case (surge, same staffing)": "#C9820A",
    "Emergency Incident (major outage)": "#B23B3B",
}
SHORT_LABELS = {
    "Best Case (low volume, fully staffed)": "Best Case",
    "Baseline (typical week)": "Baseline",
    "Worst Case (surge, same staffing)": "Worst Case",
    "Emergency Incident (major outage)": "Emergency",
}

# =====================================================================
# 1. Collect raw per-replication data for every scenario (30 reps each)
# =====================================================================
raw = {}
for label, cfg in SCENARIOS.items():
    sla_list, wait_list = [], []
    for _ in range(NUM_REPLICATIONS):
        r = run_single_replication(cfg, PRIORITY_PROFILES, SIM_HOURS, WARMUP_HOURS)
        sla_list.append(r["sla_attainment_pct"])
        wait_list.append(r["avg_wait_minutes"])
    raw[label] = {"sla": sla_list, "wait": wait_list}
    print(f"{label}: mean SLA {statistics.mean(sla_list):.1f}%, mean wait {statistics.mean(wait_list):.2f} min")

labels = list(SCENARIOS.keys())
short = [SHORT_LABELS[l] for l in labels]
colors = [COLORS[l] for l in labels]

# =====================================================================
# FIGURE 1 — Scenario comparison bar chart (SLA attainment, with real-world
# benchmark line) — a cleaner visual alternative to the table for slides
# =====================================================================
fig, ax = plt.subplots(figsize=(9, 5.5))
means = [statistics.mean(raw[l]["sla"]) for l in labels]
stdevs = [statistics.stdev(raw[l]["sla"]) for l in labels]
bars = ax.bar(short, means, yerr=stdevs, capsize=6, color=colors, edgecolor="white", linewidth=0.6)
ax.axhline(REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT, color="#444444", linestyle="--", linewidth=1.4,
            label=f"Real-world benchmark ({REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT}%, Amaral et al. 2018)")
for bar, m in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, m + 2.5, f"{m:.1f}%", ha="center", fontsize=10, fontweight="bold")
ax.set_ylim(0, 112)
ax.set_ylabel("SLA Attainment (%)")
ax.set_title("Scenario Comparison — SLA Attainment\n(mean ± std. dev. across 30 Monte Carlo replications)")
ax.legend(loc="lower left", fontsize=9)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "evidence_01_scenario_sla_comparison.png", dpi=160)
plt.close()

# =====================================================================
# FIGURE 2 — Box plots: distribution of SLA attainment across the 30
# replications per scenario (shows spread/reliability, not just the mean)
# =====================================================================
fig, ax = plt.subplots(figsize=(9, 5.5))
box_data = [raw[l]["sla"] for l in labels]
bp = ax.boxplot(box_data, tick_labels=short, patch_artist=True, widths=0.55)
for patch, c in zip(bp['boxes'], colors):
    patch.set_facecolor(c)
    patch.set_alpha(0.55)
for median in bp['medians']:
    median.set_color("black")
    median.set_linewidth(1.6)
ax.axhline(REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT, color="#444444", linestyle="--", linewidth=1.2,
            label=f"Real-world benchmark ({REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT}%)")
ax.set_ylabel("SLA Attainment per Replication (%)")
ax.set_title("Spread of Outcomes Across 30 Independent Replications\n(why a single run would be misleading)")
ax.legend(loc="lower left", fontsize=9)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "evidence_02_replication_spread_boxplot.png", dpi=160)
plt.close()

# =====================================================================
# FIGURE 3 — Wait-time distribution histogram for ONE full replication
# under Worst Case (ticket-level evidence of stochastic behavior / tail risk)
# =====================================================================
env = simpy.Environment()
desk = ServiceDesk(env, SCENARIOS["Worst Case (surge, same staffing)"]["num_agents"])
env.process(ticket_generator(env, desk, SCENARIOS["Worst Case (surge, same staffing)"], PRIORITY_PROFILES))
env.run(until=SIM_HOURS)
individual_waits = [w for _, w in desk.wait_times]

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.hist(individual_waits, bins=40, color="#C9820A", edgecolor="white", alpha=0.9)
ax.axvline(statistics.mean(individual_waits), color="#12312E", linestyle="-", linewidth=1.6,
            label=f"Mean wait = {statistics.mean(individual_waits):.1f} min")
ax.set_xlabel("Individual Ticket Wait Time (minutes)")
ax.set_ylabel("Number of Tickets")
ax.set_title(f"Ticket-Level Wait Time Distribution — Worst Case, one representative run\n({len(individual_waits)} tickets simulated)")
ax.legend(fontsize=9)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "evidence_03_wait_time_distribution.png", dpi=160)
plt.close()

# =====================================================================
# FIGURE 4 — Emergency: weekly average vs outage-window SLA, side by side
# (directly visualizes the "averages hide the crisis" finding)
# =====================================================================
emergency_cfg = SCENARIOS["Emergency Incident (major outage)"]
weekly_slas, surge_slas = [], []
for _ in range(NUM_REPLICATIONS):
    r = run_single_replication(emergency_cfg, PRIORITY_PROFILES, SIM_HOURS, WARMUP_HOURS)
    weekly_slas.append(r["sla_attainment_pct"])
    if r["surge_sla_attainment_pct"] is not None:
        surge_slas.append(r["surge_sla_attainment_pct"])

fig, ax = plt.subplots(figsize=(7.5, 5.5))
means2 = [statistics.mean(weekly_slas), statistics.mean(surge_slas)]
stdevs2 = [statistics.stdev(weekly_slas), statistics.stdev(surge_slas)]
bars2 = ax.bar(["Weekly average", "During the outage\nwindow itself"], means2, yerr=stdevs2,
                capsize=6, color=["#0E6E64", "#B23B3B"], width=0.5, edgecolor="white")
for bar, m in zip(bars2, means2):
    ax.text(bar.get_x() + bar.get_width()/2, m + 2.5, f"{m:.1f}%", ha="center", fontsize=11, fontweight="bold")
ax.set_ylim(0, 112)
ax.set_ylabel("SLA Attainment (%)")
ax.set_title("The Averaging Problem\nSame Emergency scenario, two different views of the same week")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "evidence_04_emergency_averaging_problem.png", dpi=160)
plt.close()
print(f"Emergency (averaging-problem figure): weekly SLA {means2[0]:.1f}%, "
      f"outage-window SLA {means2[1]:.1f}%")

print("\nAll evidence charts saved to", OUTPUT_DIR)
