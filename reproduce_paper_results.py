"""
Reproduce the simulation results reported in

    J. Jeemon, K. Walid, M. Shaikh, and E. AbuKhousa, "Decision Support for
    Resilient IT Service Desk Staffing: An Interactive Monte Carlo Simulation
    Approach to Emergency Demand Bursts," CAISAIS 2026.

This script adds no model logic. It imports it_service_desk_dss_simulation.py
and calls its functions in the same order as that file's own __main__ block,
so the random-number stream (random.seed(42)) is consumed identically and the
printed output and figures are the same as running the model directly. It then
re-runs the same configurations silently with the same seed and prints a
paper-vs-reproduced comparison.

Usage:
    python reproduce_paper_results.py            # Table I, Fig. 2, Fig. 4, Sec. IV.C (seed 42)
    python reproduce_paper_results.py --all      # + Figs. 1 and 3 (seed 7), Sec. III.F check, 63.4% benchmark
    python reproduce_paper_results.py --long 40  # + long-run check: 40 x 30 = 1,200 replications per configuration

Figures are written to ./outputs/. Exit status is 1 if any reproduced value
differs from the value reported in the paper.
"""
import argparse
import random
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import it_service_desk_dss_simulation as M  # noqa: E402

# Values as reported in the paper.
PAPER_TABLE_I = {
    "Best Case":  {"wait": (0.1, 0.1), "sla": (100.0, 0.0)},
    "Baseline":   {"wait": (0.9, 0.6), "sla": (100.0, 0.0)},
    "Worst Case": {"wait": (12.4, 8.3), "sla": (96.2, 5.4)},
    "Emergency":  {"wait": (23.2, 13.1), "sla": (84.8, None), "burst": (40.8, 12.0)},
}
PAPER_FIG2 = {3: 33.6, 4: 92.5, 5: 99.8}                    # SLA % vs. agents, 14 tickets/h
PAPER_FIG4 = {6: 38.8, 10: 83.9, 11: 91.5, 12: 97.6}        # burst-window SLA % vs. on-call agents
SHORT = dict(zip(M.SCENARIOS.keys(), PAPER_TABLE_I.keys()))


def main_run():
    """Same call order as the model's __main__: scenarios -> staffing sweep -> emergency sweep."""
    random.seed(42)
    M.print_scenario_comparison()        # Table I
    M.run_sensitivity_sweep()            # Fig. 2 -> outputs/it_service_desk_sensitivity.png
    M.run_emergency_staffing_sweep()     # Fig. 4 -> outputs/it_service_desk_emergency_sensitivity.png

    # Second, silent pass with the same seed and call order to capture the numbers.
    random.seed(42)
    scen = {SHORT[k]: M.run_scenario(cfg) for k, cfg in M.SCENARIOS.items()}
    sens = {n: M.run_scenario({"arrival_rate": M.SENSITIVITY_ARRIVAL_RATE, "num_agents": n})
            for n in M.SENSITIVITY_AGENT_RANGE}
    emer = {n: M.run_scenario({"arrival_rate": M.SENSITIVITY_ARRIVAL_RATE, "num_agents": n,
                               "surge": M.EMERGENCY_SURGE})
            for n in M.EMERGENCY_AGENT_RANGE}
    return scen, sens, emer


def compare(scen, sens, emer):
    rows = []

    def add(item, paper, repro):
        rows.append((item, paper, repro, paper == repro))

    for name, p in PAPER_TABLE_I.items():
        r = scen[name]
        add(f"Table I {name}: avg wait (min)", f"{p['wait'][0]:.1f} (±{p['wait'][1]:.1f})",
            f"{r['avg_wait_mean']:.1f} (±{r['avg_wait_stdev']:.1f})")
        with_sd = p["sla"][1] is not None
        sla_p = f"{p['sla'][0]:.1f}" + (f" (±{p['sla'][1]:.1f})" if with_sd else "")
        sla_r = f"{r['sla_mean']:.1f}" + (f" (±{r['sla_stdev']:.1f})" if with_sd else "")
        add(f"Table I {name}: weekly SLA %", sla_p, sla_r)
        if "burst" in p:
            add("Sec. IV.C burst-window SLA %", f"{p['burst'][0]:.1f} (±{p['burst'][1]:.1f})",
                f"{r['surge_sla_mean']:.1f} (±{r['surge_sla_stdev']:.1f})")
    for n, v in PAPER_FIG2.items():
        add(f"Fig. 2: SLA % with {n} agents", f"{v:.1f}", f"{sens[n]['sla_mean']:.1f}")
    for n, v in PAPER_FIG4.items():
        add(f"Fig. 4: burst SLA % with {n} agents", f"{v:.1f}", f"{emer[n]['surge_sla_mean']:.1f}")
    add("Sec. IV.C: on-call agents for burst SLA > 90%", "11",
        str(min(n for n, r in emer.items() if r["surge_sla_mean"] > 90)))
    add("Sec. IV.B: minimum agents for SLA > 99%", "5",
        str(min(n for n, r in sens.items() if r["sla_mean"] > 99)))

    print("\n" + "=" * 94)
    print("PAPER vs. REPRODUCED (seed 42, 30 replications per configuration)")
    print("=" * 94)
    print(f"{'Item':<48}{'Paper':>16}{'Reproduced':>18}")
    for item, p, r, ok in rows:
        print(f"{item:<48}{p:>16}{r:>18}   {'match' if ok else 'DIFFERS'}")
    print("\nFig. 2 series (SLA % by agents):       " +
          ", ".join(f"{n}:{r['sla_mean']:.1f}" for n, r in sens.items()))
    print("Fig. 4 series (burst SLA % by agents): " +
          ", ".join(f"{n}:{r['surge_sla_mean']:.1f}" for n, r in emer.items()))
    n_ok = sum(ok for *_, ok in rows)
    print(f"\n{n_ok}/{len(rows)} values match the paper.")
    return n_ok == len(rows)


def long_run(k):
    """Average of k independent 30-replication runs (seed 2026), as a check that
    the conclusions do not depend on the particular seed."""
    random.seed(2026)
    cases = [("Best Case", {"arrival_rate": 8, "num_agents": 6}),
             ("Baseline", {"arrival_rate": 14, "num_agents": 6}),
             ("Worst Case", {"arrival_rate": 22, "num_agents": 6}),
             ("Emergency", {"arrival_rate": 14, "num_agents": 6, "surge": M.EMERGENCY_SURGE}),
             ("Emergency, 10 agents", {"arrival_rate": 14, "num_agents": 10, "surge": M.EMERGENCY_SURGE}),
             ("Emergency, 11 agents", {"arrival_rate": 14, "num_agents": 11, "surge": M.EMERGENCY_SURGE})]
    print(f"\nLONG-RUN CHECK: {k} x 30 = {k * 30} replications per configuration (seed 2026)")
    for name, cfg in cases:
        res = [M.run_scenario(cfg) for _ in range(k)]
        w = statistics.mean(r["avg_wait_mean"] for r in res)
        s = statistics.mean(r["sla_mean"] for r in res)
        b = statistics.mean(r["surge_sla_mean"] for r in res) if "surge" in cfg else None
        print(f"  {name:<22} wait {w:5.1f} min   weekly SLA {s:5.1f}%" +
              (f"   burst SLA {b:5.1f}%" if b is not None else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true",
                    help="also run generate_evidence_charts.py, priority_discipline_check.py and calc_63_4.py")
    ap.add_argument("--long", type=int, default=0, metavar="K",
                    help="also run K x 30 replications per configuration (seed 2026)")
    a = ap.parse_args()

    ok = compare(*main_run())
    if a.all:
        for title, script in [("Figs. 1 and 3 (seed 7)", "generate_evidence_charts.py"),
                              ("Sec. III.F queueing-discipline check (seed 42)", "priority_discipline_check.py"),
                              ("63.4% real-world benchmark", "calc_63_4.py")]:
            print(f"\n--- {title}: {script} ---", flush=True)
            subprocess.run([sys.executable, str(HERE / script)], check=True)
    if a.long:
        long_run(a.long)
    sys.exit(0 if ok else 1)
