# Decision Support for Resilient IT Service Desk Staffing

**An Interactive Monte Carlo Simulation Approach to Emergency Demand Bursts**

Code and interactive prototype accompanying the paper submitted to **CAISAIS 2026**, Ajman University, United Arab Emirates.

**Authors:** Joshuva Jeemon, Khaled Walid, Mujtaba Shaikh, Eman AbuKhousa  
Department of Data Science, University of Europe for Applied Sciences, Dubai, United Arab Emirates

**Live browser version:** <https://joshuva1272.github.io/DSS_SLA_Model/>

## Summary

This repository contains a simulation-based decision support system (DSS) for staffing an IT service desk. The service desk is modelled as a discrete-event queueing system in SimPy: tickets arrive as a Poisson process, are assigned one of three priority classes (High, Medium, Low) with priority-specific exponential handle times and SLA targets, and are served by a shared pool of agents. Each configuration is evaluated with 30 Monte Carlo replications and reported as mean ± standard deviation. The model is used to compare four demand scenarios at the current staffing level (Table I), to find the minimum viable staffing under baseline demand (Fig. 2), and to analyse an emergency scenario in which a two-hour, High-priority-skewed burst is layered on baseline demand. For that scenario, SLA attainment is reported both for the week and for the burst window alone (Fig. 3), and an on-call staffing sweep identifies the number of agents required to hold SLA during the burst (Fig. 4). The same model is re-implemented in client-side JavaScript (`index.html`) so that decision makers can vary staffing, demand and the emergency burst and obtain new Monte Carlo results directly in the browser.

**SLA metric.** Throughout the code and the paper, a ticket meets its SLA if its **time to first response** — the queue wait from arrival until an agent picks it up — is within the priority's target (High 30 min, Medium 60 min, Low 240 min). Handle (resolution) time is simulated but is not part of the SLA test.

## Quick start

Requires Python 3.10 or later (tested with Python 3.13; see `requirements.txt` for the tested package versions).

```bash
git clone https://github.com/Joshuva1272/DSS_SLA_Model.git
cd DSS_SLA_Model
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python reproduce_paper_results.py --all
```

`reproduce_paper_results.py --all` runs every analysis in the paper (about 20 s on a laptop), writes all figures to `outputs/`, and prints a paper-vs-reproduced comparison table. It exits with a non-zero status if any value differs from the paper.

Individual scripts can also be run on their own:

| Command | What it does | Runtime |
|---|---|---|
| `python it_service_desk_dss_simulation.py` | The simulation model. Prints Table I and saves Fig. 2 and Fig. 4. | ~8 s |
| `python generate_evidence_charts.py` | Saves Fig. 1 and Fig. 3, plus two supplementary figures. | ~2 s |
| `python priority_discipline_check.py` | Sec. III.F robustness check: FIFO vs. priority-ordered service. | ~3 s |
| `python calc_63_4.py` | Derivation of the 63.4% real-world benchmark. | < 1 s |
| `python reproduce_paper_results.py --long 40` | Optional long-run check: 40 × 30 = 1,200 replications per configuration. | ~1.5 min |

**Browser version.** Open `index.html` in any modern browser (no server or installation required), or use the live link above. The "Run It Yourself" panel runs 30 fresh replications of the JavaScript engine each time "Run 30 replications" is clicked.

## Mapping of paper artefacts to code

All runs use 30 replications per configuration. Seeds are set with Python's `random.seed`.

| Paper artefact | Produced by | Seed | Output |
|---|---|---|---|
| Table I (scenario comparison, 6 agents) | `it_service_desk_dss_simulation.py` → `print_scenario_comparison()` | 42 | console |
| Sec. IV.C weekly vs. burst-window SLA (84.8% / 40.8%) | same call, Emergency row | 42 | console |
| Fig. 1 (scenario comparison vs. 63.4% benchmark) | `generate_evidence_charts.py` | 7 | `outputs/evidence_01_scenario_sla_comparison.png` |
| Fig. 2 (SLA attainment vs. agents, 14 tickets/h) | `it_service_desk_dss_simulation.py` → `run_sensitivity_sweep()` | 42 | `outputs/it_service_desk_sensitivity.png` |
| Fig. 3 (the averaging problem) | `generate_evidence_charts.py` | 7 | `outputs/evidence_04_emergency_averaging_problem.png` |
| Fig. 4 (on-call staffing sweep, burst window) | `it_service_desk_dss_simulation.py` → `run_emergency_staffing_sweep()` | 42 | `outputs/it_service_desk_emergency_sensitivity.png` |
| Sec. III.F (robustness to queueing discipline) | `priority_discipline_check.py` | 42 | console |
| 63.4% real-world benchmark (Sec. IV.A, Fig. 1) | `calc_63_4.py` | n/a (empirical) | console |
| Sec. III.E / IV.D interactive browser simulation | `index.html` (`runSingleReplicationJS`, `runLiveMonteCarlo`) | unseeded | browser |

`reproduce_paper_results.py` calls the model's functions in the same order as the model's own entry point, so it produces identical output for the seed-42 items; `--all` additionally runs the three supporting scripts. Figs. 1 and 3 come from an independent 30-replication run with seed 7 and therefore show values that differ slightly from the seed-42 values in Table I (see below). The figures in `charts/` correspond to the figures in the paper.

## Expected results

**Table I** (6 agents, seed 42):

| Scenario | Arrival rate | Avg. wait (min) | SLA attainment (%) |
|---|---|---|---|
| Best Case | 8/h | 0.1 (±0.1) | 100.0 (±0.0) |
| Baseline | 14/h | 0.9 (±0.6) | 100.0 (±0.0) |
| Worst Case | 22/h | 12.4 (±8.3) | 96.2 (±5.4) |
| Emergency | 14/h + burst | 23.2 (±13.1) | 84.8 weekly / 40.8 (±12.0) burst window |

**Fig. 2** (14 tickets/h, seed 42): 33.6% (3 agents), 92.5% (4), 99.8% (5), 100.0% (6–10). Minimum viable staffing: **5 agents**.

**Fig. 4** (burst-window SLA, seed 42): 20.6% (4 agents), 27.6% (5), 38.8% (6), 52.3% (7), 67.6% (8), 78.2% (9), 83.9% (10), **91.5% (11)**, 97.6% (12), 98.1% (13), 100.0% (14–15). Burst-window SLA first exceeds 90% at **11 agents**.

**Figs. 1 and 3** (seed 7): Best Case 100.0%, Baseline 100.0%, Worst Case 95.9%, Emergency 83.9% (Fig. 1); Emergency weekly 85.9% vs. burst window 38.7% (Fig. 3).

**Sec. III.F** (priority-ordered, non-preemptive service, seed 42): 100.0% SLA with 5 agents (the 5-agent minimum holds under both disciplines); burst-window SLA 93.1% with 10 agents, compared with 11 agents under FIFO.

**Long-run check** (`--long 40`, 1,200 replications per configuration, seed 2026): Worst Case 95.3%; Emergency 85.2% weekly / 39.6% burst window; burst-window SLA 85.1% with 10 agents and 92.7% with 11 agents. The 11-agent on-call recommendation does not depend on the particular seed.

The JavaScript engine in `index.html` implements the same model (tickets are assigned in arrival order to the earliest-available agent, equivalent to the SimPy FIFO `Resource`). It uses unseeded `Math.random()`, so each click gives a new 30-replication estimate that varies around the values above; for example, the burst-window SLA with 11 agents averaged 92.4% over 40 clicks, with individual runs between roughly 87% and 96%.

## Model parameters

All parameters are defined in the `ASSUMPTIONS` block of `it_service_desk_dss_simulation.py`.

| Parameter | Value |
|---|---|
| Horizon | 40 h (8 h × 5 days); the first 1 h is treated as warm-up and discarded |
| Arrivals | Poisson; Best Case 8/h, Baseline 14/h, Worst Case 22/h |
| Priority mix | High 20%, Medium 50%, Low 30% |
| Mean handle time (exponential) | High 20 min, Medium 15 min, Low 10 min |
| SLA target (time to first response) | High 30 min, Medium 60 min, Low 240 min |
| Agents | Shared pool (`simpy.Resource`), FIFO; 6 agents for Table I |
| Emergency burst | Starts 6 h into the week, lasts 2 h, 45 tickets/h, mix 70% High / 20% Medium / 10% Low, on top of Baseline demand |
| Replications | 30 per configuration; ± denotes the sample standard deviation across replications |

The priority mix, handle times, SLA targets and burst shape are modelling assumptions chosen to represent a plausible service desk and major-incident profile; they are not estimated from data. See the paper's limitations section.

## Real-world benchmark (63.4%)

The dashed reference line in Fig. 1 is an empirical benchmark, not a simulation output and not a model input. It is the share of closed incident records that met their SLA in an anonymised ServiceNow incident event log:

> Amaral, C., Fantinato, M., & Peres, S. (2018). *Incident management process enriched event log* [Dataset]. UCI Machine Learning Repository. <https://doi.org/10.24432/C57S4H> (CC BY 4.0)

Of the 24,985 records with `incident_state == "Closed"`, 15,831 have `made_sla == True`, giving 15,831 / 24,985 = **63.4%**. In the code the value is used only as a printed reference and as the reference line in Fig. 1 (`REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT`). `calc_63_4.py` reproduces the figure from the per-priority cross-tabulation and, given the raw CSV from the UCI repository, can recompute it from the event log.

## Repository structure

```
.
├── it_service_desk_dss_simulation.py   # SimPy model (Table I, Fig. 2, Fig. 4)
├── reproduce_paper_results.py          # one-command reproduction + paper-vs-reproduced table
├── generate_evidence_charts.py         # Fig. 1, Fig. 3 and supplementary figures
├── priority_discipline_check.py        # Sec. III.F: FIFO vs. priority-ordered service
├── calc_63_4.py                        # derivation of the 63.4% benchmark
├── index.html                          # interactive dashboard with in-browser Monte Carlo engine
├── dashboard.html                      # redirect to index.html (kept for existing links)
├── charts/                             # figures used in the paper and architecture diagram
├── docs/                               # model walkthrough, data grounding, project Q&A
├── outputs/                            # created on first run (git-ignored)
├── requirements.txt
├── CITATION.cff
└── LICENSE
```

## Citation

If you use this code, please cite the paper (see also `CITATION.cff`):

```bibtex
@inproceedings{jeemon2026servicedesk,
  author    = {Jeemon, Joshuva and Walid, Khaled and Shaikh, Mujtaba and AbuKhousa, Eman},
  title     = {Decision Support for Resilient {IT} Service Desk Staffing: An Interactive
               {Monte Carlo} Simulation Approach to Emergency Demand Bursts},
  booktitle = {CAISAIS 2026},
  address   = {Ajman University, Ajman, United Arab Emirates},
  year      = {2026}
}
```

## License

Code is released under the MIT License (see `LICENSE`). The ServiceNow incident event log is not redistributed here; it is available from the UCI Machine Learning Repository under CC BY 4.0.
