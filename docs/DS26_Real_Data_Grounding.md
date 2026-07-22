# Real-World Data Grounding
## UCI "Incident Management Process Enriched Event Log" — Findings & Application

---

## 1. The Dataset

**Citation:**
> Amaral, C., Fantinato, M., & Peres, S. (2018). *Incident management process enriched event log* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C57S4H

**What it is:** A real, anonymized event log extracted from the audit system of an actual ServiceNow instance used by a real IT company, enriched with data from the underlying relational database. Donated to the UCI Machine Learning Repository on 7/13/2019.

**Scale:** 141,712 events, covering 24,918 unique incidents, 36 attributes per record.

**License:** CC BY 4.0 — freely citable and usable with attribution.

**Why this dataset specifically:** Unlike most public "IT ticket" datasets (which are often synthetic or generated for ML classification demos), this one is real production data from a real company's incident management process, including a genuine `made_sla` field (whether the incident missed its target SLA) and a `priority` field calculated by the system from `impact` × `urgency` — exactly the two variables our simulation cares about.

---

## 2. How These Numbers Were Obtained

We did not download and process the full 44.1 MB raw event log ourselves (a full reconstruction of ticket-level records from the event log was judged too time-costly for the remaining project timeline — see the "real challenge" discussion earlier in the project). Instead, we located and verified a third-party public analysis notebook that computed direct cross-tabulations from the actual raw data, and cross-checked its numbers against the dataset's own official documentation for consistency.

**Cross-check performed:** The notebook's "Closed" incident count (24,985) matches the official incident-state breakdown published on the UCI page, and the overall SLA-miss rate we calculated from the raw cross-tab (36.6%) matches the notebook author's own independently stated finding ("~37% of incidents are missing SLAs"). This agreement across two independent computations gives us reasonable confidence the extracted numbers are accurate.

---

## 3. Real Numbers Extracted

### 3.1 Priority Distribution (across 24,985 closed incidents)

| Priority | Count | Share |
|---|---|---|
| 1 – Critical | 271 | ~1.1% |
| 2 – High | 408 | ~1.6% |
| 3 – Moderate | 23,529 | ~94.2% |
| 4 – Low | 777 | ~3.1% |

### 3.2 SLA Attainment by Priority

| Priority | Met SLA / Total | Attainment % |
|---|---|---|
| Critical | 6 / 271 | ~2.2% |
| High | 2 / 408 | ~0.5% |
| Moderate | 15,171 / 23,529 | ~64.5% |
| Low | 652 / 777 | ~83.9% |
| **Overall (all priorities)** | 15,831 / 24,985 | **~63.4%** |

### 3.3 What the Data Does *Not* Give Us
This particular analysis did not compute resolution-time-in-minutes statistics per priority (the source notebook focused on `reassignment_count`, `reopen_count`, and SLA outcome, not raw duration). Service-time assumptions in our simulation therefore remain **clearly labeled team assumptions**, not data-derived figures — this is stated explicitly rather than implied otherwise.

---

## 4. The Interesting, Counterintuitive Finding

The real pattern in this data is worth highlighting explicitly in the report's discussion: **Critical and High priority tickets had dramatically worse SLA attainment (2.2%, 0.5%) than Moderate and Low priority tickets (64.5%, 83.9%)** — the opposite of what intuition might suggest.

**Likely explanation:** Urgent tickets are typically assigned very tight SLA deadlines, which are easy to breach under real-world friction (reassignment, escalation, complexity), while low-priority tickets are given generous deadlines that are comparatively easy to hit even with normal delays. This is a genuine, non-obvious, citable insight — not something we assumed or engineered, but something the real data shows.

**Where to use this:** Conclusions & Recommendations section, as evidence that SLA design (not just staffing level) matters — a nice added layer of insight beyond the core staffing question.

---

## 5. How This Will Be Applied to Our Simulation

**What we're keeping as our own designed assumption:** Our working 20% High / 50% Medium / 30% Low priority mix, because the real dataset's actual distribution (94% in a single "Moderate" bucket) is too flat to produce a demonstrative sensitivity analysis — a required part of the assignment. This is a deliberate modeling choice, and it will be stated explicitly as such in the report, not presented as if it came directly from the data.

**What we're citing the real dataset for:**
- The real-world ~63.4% overall SLA attainment figure, as a benchmark/reality-check against our simulation's baseline output
- The finding that SLA attainment varies sharply and counterintuitively by priority, discussed in Conclusions
- General credibility: evidence that our model's core concern (SLA breach risk varying by priority under real operational conditions) is a genuine, observed phenomenon, not a hypothetical one

**What remains a labeled team assumption:**
- Exact service time per priority (minutes to resolve)
- Exact SLA target thresholds (30/60/240 minutes)
- Ticket arrival rate (tickets per hour)

---

## 6. Full Citation List for This Section

- Amaral, C., Fantinato, M., & Peres, S. (2018). *Incident management process enriched event log* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C57S4H
- Third-party analysis notebook used for cross-tabulation verification: san-git, *ML-Incident-Management* (GitHub repository), `Incident_event_log.ipynb`
