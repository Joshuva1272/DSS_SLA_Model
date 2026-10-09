"""
IT Service Desk Staffing — Simulation-Based Decision Support System
=====================================================================

DECISION PROBLEM:
  How many support agents should the IT Service Desk staff per shift to
  hit SLA targets (time to first response, i.e. queue wait until an agent
  picks up the ticket) without overstaffing and wasting labor cost?

DECISION-MAKER: IT Service Manager
STAKEHOLDERS: Support agents, end-users waiting on tickets, Finance (headcount cost)

WHY SIMULATION (not a closed-form queueing formula):
  Classic Erlang-C / M/M/c formulas assume a single ticket type, Markovian
  (exponential) service times, and a single agent skill pool. Real service
  desks have multiple ticket priorities, non-exponential service times, and
  variable arrival rates — which is exactly the argument Orta, Ruiz, Hurtado
  & Gawn (2014, Decision Support Systems journal) make for why simulation is
  needed instead of static formulas. This script follows that same logic.

USAGE:
  python it_service_desk_dss_simulation.py
  Prints the scenario comparison (Table I) and saves the staffing sweep
  (Fig. 2) and the emergency on-call sweep (Fig. 4) to ./outputs/.
  Seed: random.seed(42). All model parameters are in the ASSUMPTIONS block.
"""

from pathlib import Path

import simpy
import random
import statistics
import matplotlib
matplotlib.use("Agg")  # headless rendering; figures are written to files
import matplotlib.pyplot as plt

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

# =====================================================================
# ASSUMPTIONS
# =====================================================================
#
# REAL-DATA GROUNDING:
#   Amaral, C., Fantinato, M., & Peres, S. (2018). "Incident management
#   process enriched event log" [Dataset]. UCI Machine Learning Repository.
#   https://doi.org/10.24432/C57S4H
#   (Real, anonymized ServiceNow data; 24,985 closed incidents.)
#
#   From this real dataset (see docs/DS26_Real_Data_Grounding.md for full detail):
#     - Real-world overall SLA attainment benchmark: ~63.4%
#       (i.e. real service desks miss SLA on ~37% of tickets overall —
#        useful as a reality-check against our Baseline scenario output)
#     - Real priority split was highly skewed (~94% "Moderate"), which is
#       too flat to demonstrate a staffing sensitivity analysis, so we
#       deliberately keep our own 20/50/30 High/Medium/Low mix below as a
#       TEAM ASSUMPTION chosen for a demonstrative model, not a data-derived
#       figure. This choice is stated explicitly, not hidden.
#     - The real data also shows High/Critical tickets had far WORSE SLA
#       attainment than Low priority ones (tight deadlines vs. real-world
#       friction) -- a citable, counterintuitive finding for the
#       Conclusions section, independent of the staffing question itself.
#     - Real per-priority resolution-time-in-minutes was not available in
#       the analysis we could access in our timeframe, so service times
#       below remain TEAM ASSUMPTIONS (clearly labeled as such).
#
# =====================================================================

SIM_HOURS = 8 * 5          # simulate one work week (8-hour days x 5 days)
WARMUP_HOURS = 1           # discard first hour of stats (system "warming up")
NUM_REPLICATIONS = 30      # Monte Carlo replications per scenario (for confidence, not just one run)

# Ticket priority mix: TEAM ASSUMPTION (see note above -- real data was too
# skewed at ~94% single-tier to demonstrate sensitivity analysis).
# Service times and SLA targets: TEAM ASSUMPTIONS, not data-derived.
PRIORITY_PROFILES = {
    "High":   {"share": 0.20, "mean_service_min": 20, "sla_min": 30},
    "Medium": {"share": 0.50, "mean_service_min": 15, "sla_min": 60},
    "Low":    {"share": 0.30, "mean_service_min": 10, "sla_min": 240},
}

# Real-world benchmark for sanity-checking simulation output against
# (Amaral, Fantinato & Peres, 2018) -- NOT used directly in the model,
# only referenced when discussing results in the report.
REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT = 63.4

# EMERGENCY SCENARIO — a major incident/outage, not just "more tickets":
# a short, sharp burst of mostly-High-priority tickets hitting a desk
# staffed for a normal day. This is a TEAM ASSUMPTION representing a
# plausible major-outage shape (e.g. a core system going down mid-shift).
EMERGENCY_SURGE = {
    "surge_start_hour": 6,          # outage hits 6 simulated hours into the week
    "surge_duration_hours": 2,      # lasts 2 simulated hours
    "surge_arrival_rate": 45,       # tickets/hour flooding in during the outage (vs. 14 baseline)
    "surge_priority_weights": {"High": 0.70, "Medium": 0.20, "Low": 0.10},  # mostly High during an outage
}

# Scenarios: (label, tickets_per_hour, num_agents, optional surge config)
SCENARIOS = {
    "Best Case (low volume, fully staffed)":        {"arrival_rate": 8,  "num_agents": 6},
    "Baseline (typical week)":                       {"arrival_rate": 14, "num_agents": 6},
    "Worst Case (surge, same staffing)":             {"arrival_rate": 22, "num_agents": 6},
    "Emergency Incident (major outage)":             {"arrival_rate": 14, "num_agents": 6, "surge": EMERGENCY_SURGE},
}

# For the emergency staffing sweep: how many on-call agents are needed to
# hold SLA during the outage window itself (not just the weekly average)?
EMERGENCY_AGENT_RANGE = range(4, 16)

# For the sensitivity sweep: how does SLA attainment change as we vary staffing,
# holding arrival rate at the "Baseline" level?
SENSITIVITY_ARRIVAL_RATE = 14
SENSITIVITY_AGENT_RANGE = range(3, 11)  # test 3 to 10 agents


# =====================================================================
# SIMULATION ENGINE
# =====================================================================

class ServiceDesk:
    def __init__(self, env, num_agents):
        self.env = env
        self.agents = simpy.Resource(env, capacity=num_agents)
        self.wait_times = []          # (priority, wait_minutes)
        self.sla_met = []             # (priority, True/False, in_surge)

    def handle_ticket(self, priority, mean_service_min, sla_min, in_surge=False):
        arrival_time = self.env.now
        with self.agents.request() as req:
            yield req
            wait_minutes = (self.env.now - arrival_time) * 60
            self.wait_times.append((priority, wait_minutes))
            self.sla_met.append((priority, wait_minutes <= sla_min, in_surge))
            service_time_hours = random.expovariate(1.0 / (mean_service_min / 60))
            yield self.env.timeout(service_time_hours)


def _in_surge_window(now, surge):
    if not surge:
        return False
    return surge["surge_start_hour"] <= now < surge["surge_start_hour"] + surge["surge_duration_hours"]


def ticket_generator(env, desk, cfg, priority_profiles):
    """Generates tickets as a Poisson process; each ticket is randomly
    assigned a priority level according to the configured mix.

    If cfg contains a "surge" config (see EMERGENCY_SURGE), arrival rate and
    priority mix both switch to the surge values while simulated time falls
    inside the surge window -- modeling a short, sharp major-incident burst
    rather than just a uniformly busier week."""
    base_rate = cfg["arrival_rate"]
    surge = cfg.get("surge")

    priorities = list(priority_profiles.keys())
    base_weights = [priority_profiles[p]["share"] for p in priorities]

    if surge:
        surge_priorities = list(surge["surge_priority_weights"].keys())
        surge_weights = [surge["surge_priority_weights"][p] for p in surge_priorities]

    while True:
        rate = surge["surge_arrival_rate"] if _in_surge_window(env.now, surge) else base_rate
        interarrival_hours = random.expovariate(rate)
        yield env.timeout(interarrival_hours)

        in_surge_now = _in_surge_window(env.now, surge)
        if in_surge_now:
            priority = random.choices(surge_priorities, weights=surge_weights, k=1)[0]
        else:
            priority = random.choices(priorities, weights=base_weights, k=1)[0]

        profile = priority_profiles[priority]
        env.process(desk.handle_ticket(priority, profile["mean_service_min"], profile["sla_min"], in_surge_now))


def run_single_replication(cfg, priority_profiles, sim_hours, warmup_hours):
    env = simpy.Environment()
    desk = ServiceDesk(env, cfg["num_agents"])
    env.process(ticket_generator(env, desk, cfg, priority_profiles))
    env.run(until=sim_hours)

    # simple warmup filter: drop entries recorded before warmup_hours elapsed
    # (approximation — for a rigorous warmup removal, track timestamps directly)
    cutoff_count = int(len(desk.wait_times) * (warmup_hours / sim_hours))
    filtered_waits = desk.wait_times[cutoff_count:]
    filtered_sla = desk.sla_met[cutoff_count:]

    avg_wait = statistics.mean(w for _, w in filtered_waits) if filtered_waits else 0
    sla_attainment = (sum(1 for _, met, _ in filtered_sla if met) / len(filtered_sla) * 100
                       if filtered_sla else 0)

    # If this scenario has an emergency surge window, also report SLA
    # attainment for JUST the tickets that arrived during the outage itself
    # — the weekly average can look fine even while the outage window is
    # in genuine crisis, so this is the more honest number for that window.
    surge_entries = [e for e in filtered_sla if e[2]]
    surge_sla_attainment = (
        sum(1 for _, met, _ in surge_entries if met) / len(surge_entries) * 100
        if surge_entries else None
    )

    return {
        "avg_wait_minutes": avg_wait,
        "sla_attainment_pct": sla_attainment,
        "surge_sla_attainment_pct": surge_sla_attainment,
        "tickets_handled": len(filtered_waits),
    }


def run_scenario(cfg, replications=NUM_REPLICATIONS):
    """Runs many replications (Monte Carlo) and returns mean + spread —
    a single run can be misleading due to randomness; replication gives you
    a defensible confidence range for your Evaluation & Scenario Analysis section."""
    results = [
        run_single_replication(cfg, PRIORITY_PROFILES, SIM_HOURS, WARMUP_HOURS)
        for _ in range(replications)
    ]
    avg_waits = [r["avg_wait_minutes"] for r in results]
    sla_pcts = [r["sla_attainment_pct"] for r in results]
    surge_pcts = [r["surge_sla_attainment_pct"] for r in results if r["surge_sla_attainment_pct"] is not None]

    out = {
        "avg_wait_mean": statistics.mean(avg_waits),
        "avg_wait_stdev": statistics.stdev(avg_waits) if len(avg_waits) > 1 else 0,
        "sla_mean": statistics.mean(sla_pcts),
        "sla_stdev": statistics.stdev(sla_pcts) if len(sla_pcts) > 1 else 0,
    }
    if surge_pcts:
        out["surge_sla_mean"] = statistics.mean(surge_pcts)
        out["surge_sla_stdev"] = statistics.stdev(surge_pcts) if len(surge_pcts) > 1 else 0
    return out


# =====================================================================
# RUN SCENARIOS
# =====================================================================

def print_scenario_comparison():
    print("=" * 78)
    print("SCENARIO COMPARISON — IT Service Desk Staffing DSS")
    print("=" * 78)
    print(f"{'Scenario':<42} {'Avg Wait (min)':<18} {'SLA Attainment %':<18}")
    print("-" * 78)
    for label, cfg in SCENARIOS.items():
        result = run_scenario(cfg)
        print(f"{label:<42} "
              f"{result['avg_wait_mean']:>6.1f} (±{result['avg_wait_stdev']:.1f})   "
              f"{result['sla_mean']:>6.1f} (±{result['sla_stdev']:.1f})")
        if "surge_sla_mean" in result:
            print(f"  {'':<42} └─ DURING the outage window itself: "
                  f"SLA attainment {result['surge_sla_mean']:.1f}% (±{result['surge_sla_stdev']:.1f}) "
                  f"— same {cfg['num_agents']} agents, no surge response")
    print("=" * 78)
    print("(± values are standard deviation across", NUM_REPLICATIONS, "Monte Carlo replications)")
    print(f"(Real-world SLA attainment benchmark, Amaral et al. 2018 UCI dataset: "
          f"{REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT}%)\n")


def run_sensitivity_sweep():
    print("Running staffing sensitivity sweep...")
    agent_counts = list(SENSITIVITY_AGENT_RANGE)
    sla_means = []
    sla_stdevs = []

    for n in agent_counts:
        result = run_scenario({"arrival_rate": SENSITIVITY_ARRIVAL_RATE, "num_agents": n})
        sla_means.append(result["sla_mean"])
        sla_stdevs.append(result["sla_stdev"])
        print(f"  {n} agents -> SLA attainment: {result['sla_mean']:.1f}%")

    plt.figure(figsize=(8, 5))
    plt.errorbar(agent_counts, sla_means, yerr=sla_stdevs, marker='o', capsize=4)
    plt.axhline(y=90, color='red', linestyle='--', label='Example 90% SLA target')
    plt.xlabel("Number of Agents Staffed")
    plt.ylabel("SLA Attainment (%)")
    plt.title(f"Staffing Sensitivity Analysis\n(arrival rate = {SENSITIVITY_ARRIVAL_RATE} tickets/hour)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / "it_service_desk_sensitivity.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"\nSaved chart: {out}")


def run_emergency_staffing_sweep():
    """Answers the decision-support question this scenario exists for:
    'if a major outage hits, how many agents do we need ON CALL to hold
    SLA during the outage itself, given normal day-to-day staffing alone
    isn't enough?' Sweeps agent count under the EMERGENCY_SURGE conditions
    and measures SLA attainment for just the surge window."""
    print("Running emergency (major-outage) staffing sweep...")
    print(f"(Outage: {EMERGENCY_SURGE['surge_arrival_rate']} tickets/hr for "
          f"{EMERGENCY_SURGE['surge_duration_hours']}h, "
          f"{int(EMERGENCY_SURGE['surge_priority_weights']['High']*100)}% High priority)\n")

    agent_counts = list(EMERGENCY_AGENT_RANGE)
    surge_sla_means = []
    surge_sla_stdevs = []

    for n in agent_counts:
        cfg = {"arrival_rate": SENSITIVITY_ARRIVAL_RATE, "num_agents": n, "surge": EMERGENCY_SURGE}
        result = run_scenario(cfg)
        mean_val = result.get("surge_sla_mean", 0)
        stdev_val = result.get("surge_sla_stdev", 0)
        surge_sla_means.append(mean_val)
        surge_sla_stdevs.append(stdev_val)
        print(f"  {n} agents on-call -> SLA attainment DURING the outage: {mean_val:.1f}%")

    plt.figure(figsize=(8, 5))
    plt.errorbar(agent_counts, surge_sla_means, yerr=surge_sla_stdevs, marker='o', capsize=4, color='#B23B3B')
    plt.axhline(y=90, color='red', linestyle='--', label='Example 90% SLA target')
    plt.xlabel("Number of Agents On-Call During Outage")
    plt.ylabel("SLA Attainment During Outage Window (%)")
    plt.title("Emergency Staffing Sweep\n(major outage: mostly-High-priority ticket burst)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / "it_service_desk_emergency_sensitivity.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"\nSaved chart: {out}")


if __name__ == "__main__":
    random.seed(42)  # reproducibility — remove or change for different random runs
    print_scenario_comparison()
    run_sensitivity_sweep()
    run_emergency_staffing_sweep()
