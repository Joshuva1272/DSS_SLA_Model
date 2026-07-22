# DSS_SLA_Model — Simulation-Based DSS for IT Service Desk Staffing

A Decision Support System that answers a real operational question: **how many IT support agents should a service desk staff per shift to meet SLA targets across ticket priorities, without overstaffing?**

Built for **DS26 — Decision Support Systems** by **Joshuva J, Khaled Walid, and Mujtaba**.

## What it does

- Discrete-event simulation (Python + [SimPy](https://simpy.readthedocs.io)) of a multi-priority ticket queue served by a configurable agent pool
- Poisson ticket arrivals, exponential service times, priority-specific SLA targets
- **30 Monte Carlo replications per scenario** — results reported as mean ± standard deviation, never a single noisy run
- Four scenarios: Best Case, Baseline, Worst Case (sustained surge), and **Emergency** (a 2-hour major-outage burst, 70% High-priority)
- Two sensitivity sweeps: normal-conditions staffing (3–10 agents) and emergency on-call staffing (4–15 agents)
- An interactive dashboard (`dashboard.html`) with a **live in-browser re-implementation** of the same Monte Carlo engine

## Headline findings

| Question | Answer | Evidence |
|---|---|---|
| Minimum viable staffing (normal demand) | **5 agents** | SLA attainment collapses below this: 99.7% → 92.4% → 37.4% at 5/4/3 agents |
| On-call staffing for a major outage | **~11 agents** | Point where SLA during the outage window crosses 90% |
| Why weekly averages are dangerous | The Emergency scenario averages **84.8%** for the week — but only **40.8%** during the outage itself | Averaging 38 normal hours with 2 crisis hours hides the crisis |

## Quick start

```bash
pip install simpy matplotlib
python3 it_service_desk_dss_simulation.py
```

Runs in under a second. Prints the scenario comparison table and saves both sensitivity charts. Open `dashboard.html` in any browser for the interactive version — the "Run It Yourself" section runs 30 fresh replications on every click.

To regenerate the full evidence chart pack:

```bash
python3 generate_evidence_charts.py
```

## Repository layout

```
it_service_desk_dss_simulation.py   # the simulation engine (Model component)
generate_evidence_charts.py         # builds all evidence charts from real runs
dashboard.html                      # interactive UI incl. live browser simulation
charts/                             # generated figures used in the report
docs/                               # simulation walkthrough, data grounding, Q&A
```

## Modeling notes (honest ones)

- **Queue discipline is FIFO.** Priorities set each ticket's SLA target and mean service time, not its place in line. We tested a priority-ordered variant (SimPy `PriorityResource`): the 5-agent minimum holds under both disciplines, and FIFO yields the more conservative emergency estimate (11 vs ~10 agents) — so the reported recommendations err on the safe side.
- **Service times are exponential** — a standard simplification; real resolution times are typically heavier-tailed.
- **Assumptions are labeled.** The 20/50/30 priority mix, service times, and SLA targets are explicit team assumptions. The real-data benchmark (63.4% overall SLA attainment) comes from Amaral, Fantinato & Peres (2018), *Incident management process enriched event log*, UCI Machine Learning Repository, DOI: [10.24432/C57S4H](https://doi.org/10.24432/C57S4H) (CC BY 4.0).

## Key references

- Orta, E., Ruiz, M., Hurtado, N., & Gawn, D. (2014). Decision-making in IT service management: a simulation based approach. *Decision Support Systems*, 66, 36–51.
- Sprague, R. H. (1980). A Framework for the Development of Decision Support Systems. *MIS Quarterly*, 4(4), 1–26.
- Gans, N., Koole, G., & Mandelbaum, A. (2003). Telephone Call Centers: Tutorial, Review, and Research Prospects. *M&SOM*, 5(2), 79–141.
- Law, A. M., & Kelton, W. D. *Simulation Modeling and Analysis*. McGraw-Hill.

## License

Academic coursework. Dataset citation above is CC BY 4.0; code shared for educational purposes.
