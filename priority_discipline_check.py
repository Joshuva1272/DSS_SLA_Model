"""
Robustness check: FIFO vs. priority-ordered (non-preemptive) service.
Supports Section III.F ("Robustness to Queueing Discipline") of the paper.

The main model serves tickets FIFO from a shared agent pool (simpy.Resource).
This script reruns the staffing sweep (14 tickets/h, 3-6 agents) and the
emergency on-call sweep (6, 10, 11, 12 agents) with a simpy.PriorityResource,
so that High-priority tickets are picked up before Medium and Low ones
(non-preemptive). All other parameters are imported from the main model.

Usage:  python priority_discipline_check.py      (seed 42, 30 replications)
"""
import random
import statistics
import sys
from pathlib import Path

import simpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from it_service_desk_dss_simulation import (PRIORITY_PROFILES, SIM_HOURS, WARMUP_HOURS,
    NUM_REPLICATIONS, EMERGENCY_SURGE, _in_surge_window)

PRIO_RANK = {"High": 0, "Medium": 1, "Low": 2}

# FIFO reference values from the main model (it_service_desk_dss_simulation.py,
# seed 42), as reported in Fig. 2 (SLA %) and Fig. 4 (burst-window SLA %).
FIFO_SENSITIVITY = {3: 33.6, 4: 92.5, 5: 99.8, 6: 100.0}
FIFO_EMERGENCY = {6: 38.8, 10: 83.9, 11: 91.5, 12: 97.6}

class PriorityDesk:
    def __init__(self, env, n):
        self.env = env
        self.agents = simpy.PriorityResource(env, capacity=n)
        self.sla_met = []
    def handle(self, priority, mean_service_min, sla_min, in_surge):
        arrive = self.env.now
        with self.agents.request(priority=PRIO_RANK[priority]) as req:
            yield req
            wait_min = (self.env.now - arrive) * 60
            self.sla_met.append((priority, wait_min <= sla_min, in_surge))
            yield self.env.timeout(random.expovariate(1.0/(mean_service_min/60)))

def gen(env, desk, rate, surge):
    ps = list(PRIORITY_PROFILES); ws = [PRIORITY_PROFILES[p]["share"] for p in ps]
    sp = list(surge["surge_priority_weights"]) if surge else None
    sw = [surge["surge_priority_weights"][p] for p in sp] if surge else None
    while True:
        r = surge["surge_arrival_rate"] if _in_surge_window(env.now, surge) else rate
        yield env.timeout(random.expovariate(r))
        s = _in_surge_window(env.now, surge)
        pr = random.choices(sp, weights=sw, k=1)[0] if s else random.choices(ps, weights=ws, k=1)[0]
        prof = PRIORITY_PROFILES[pr]
        env.process(desk.handle(pr, prof["mean_service_min"], prof["sla_min"], s))

def run_prio(rate, n, surge=None):
    slas, surge_slas = [], []
    for _ in range(NUM_REPLICATIONS):
        env = simpy.Environment(); d = PriorityDesk(env, n)
        env.process(gen(env, d, rate, surge)); env.run(until=SIM_HOURS)
        cut = int(len(d.sla_met)*(WARMUP_HOURS/SIM_HOURS)); f = d.sla_met[cut:]
        slas.append(sum(1 for _,m,_ in f if m)/len(f)*100 if f else 0)
        se = [e for e in f if e[2]]
        if se: surge_slas.append(sum(1 for _,m,_ in se if m)/len(se)*100)
    return statistics.mean(slas), (statistics.mean(surge_slas) if surge_slas else None)

if __name__ == "__main__":
    random.seed(42)
    print("=== FIFO (current model) vs PRIORITY-ordered service ===\n")
    print("Sensitivity sweep @ 14/hr (headline: 5-agent minimum):")
    for n in [3,4,5,6]:
        s,_ = run_prio(14, n)
        print(f"  {n} agents PRIORITY: {s:.1f}%   (FIFO, Fig. 2: {FIFO_SENSITIVITY[n]}%)")
    print("\nEmergency sweep (headline: 11 agents for 90% during outage):")
    for n in [6,10,11,12]:
        _,ss = run_prio(14, n, EMERGENCY_SURGE)
        print(f"  {n} agents PRIORITY: {ss:.1f}% during outage  (FIFO, Fig. 4: {FIFO_EMERGENCY[n]}%)")
