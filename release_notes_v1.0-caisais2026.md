# v1.0-caisais2026

Code release accompanying the CAISAIS 2026 paper:

> J. Jeemon, K. Walid, M. Shaikh, and E. AbuKhousa, "Decision Support for Resilient IT Service Desk Staffing: An Interactive Monte Carlo Simulation Approach to Emergency Demand Bursts," CAISAIS 2026, Ajman University, United Arab Emirates, 2026.

This release reproduces all simulation results reported in the paper: Table I, Figs. 1–4, the emergency-burst findings (Sec. IV.C), the queueing-discipline robustness check (Sec. III.F), and the 63.4% real-world SLA benchmark.

## Reproducing the paper

```bash
pip install -r requirements.txt
python reproduce_paper_results.py --all
```

The script runs the model with the seeds used in the paper, writes all figures to `outputs/`, and prints a paper-vs-reproduced table (18/18 values match). The interactive browser version is available at <https://joshuva1272.github.io/DSS_SLA_Model/> or by opening `index.html` locally.

## What's new since the initial commit

- **`reproduce_paper_results.py`**: one-command reproduction with an automatic paper-vs-reproduced check; optional `--long K` seed-robustness run.
- **`priority_discipline_check.py`**: FIFO vs. non-preemptive priority-ordered service (Sec. III.F).
- **`calc_63_4.py`**: derivation of the 63.4% benchmark (15,831 of 24,985 closed records with `made_sla = True`) from the ServiceNow incident event log of Amaral, Fantinato & Peres (2018), UCI Machine Learning Repository, doi:10.24432/C57S4H.
- All scripts write figures to `outputs/` relative to the repository, independent of the working directory.
- `generate_evidence_charts.py`: updated for Matplotlib 3.9+ (`tick_labels`); documents which figures correspond to Figs. 1 and 3.
- `index.html`: static staffing-sweep chart updated to the values reported in Fig. 2 (33.6 / 92.5 / 99.8% for 3 / 4 / 5 agents); the live in-browser Monte Carlo engine is unchanged. `dashboard.html` now redirects to `index.html`.
- README rewritten with a paper-artefact-to-code mapping, seeds and expected numbers; added `LICENSE` (MIT), `CITATION.cff`, pinned `requirements.txt` and an expanded `.gitignore`.

No changes were made to the simulation logic, parameters or random-number usage.

## Tested environment

Python 3.13 with simpy 4.1.1 / matplotlib 3.9.4 / numpy 2.1.3 / pandas 2.2.3, and with simpy 4.1.2 / matplotlib 3.11.2 / numpy 2.5.3 / pandas 3.0.6. Both produce identical numerical output.
