# Project Q&A — Decisions, Data, and Justifications
## Simulation-Based DSS for IT Service Desk Staffing

**Purpose:** A single reference document answering the questions most likely to come up — from teammates, from yourselves while rehearsing, or from the professor in the viva. Every answer here reflects a decision actually made during this project, with the reasoning behind it.

---

## Part 1 — Topic & Methodology Decisions

### Q: Why did the team choose IT Service Desk Staffing as the topic?
After exploring several IT/cloud domains (cloud provisioning, LLM/GPU capacity planning, ransomware propagation, diamond-cooling investment modeling, and others), the team scored each option against pain-point currency, literature strength, propagation/scenario richness, and — critically, once the deadline compressed to about 3 days — buildability. IT Service Desk Staffing won on a combination of low technical risk, a strong existing academic precedent (Orta et al., 2014), and a genuinely well-documented, tractable simulation structure (queueing theory).

### Q: Did the team validate this topic with anyone outside the class before committing to it?
Yes. Before finalizing a topic, the team reached out to several researchers working in the Decision Support Systems space, hoping for expert input on where a DSS could genuinely make a difference. Of everyone contacted, only one replied: **Dr. A. Naderi**, from the University of Tehran, whose published research focuses on financial resource allocation DSS for universities. He confirmed that DSS approaches are genuinely applicable to real organizational resource problems — useful validation of the team's general direction, even though his own research area (university finance) was in a different domain from where the project ultimately landed.

### Q: So where did the actual IT Service Desk Staffing topic come from?
From inside the team itself. **Khaled** shared a real challenge from his own workplace: IT service desks often make staffing decisions largely by gut feel and historical habit, rather than any evidence-based method — leading to exactly the tension this project is built around, overstaffing and wasting budget, or understaffing and risking missed SLAs when demand spikes. That real, lived example is what turned this from an abstract assignment into a problem the team actually cared about solving, and it's the problem this DSS is built to address.

### Q: Why Simulation-Based DSS instead of GDSS or Optimization-Based DSS?
Three reasons, each tied to a specific weakness in the alternatives:
- **Not GDSS**, because the decision is made by a single accountable decision-maker (the IT Service Manager) against defined constraints — not a group of stakeholders jointly negotiating an unstructured problem in real time (DeSanctis & Gallupe, 1987).
- **Not Optimization-Based DSS**, because optimization assumes reasonably stable, forecastable demand. Our ticket arrivals are genuinely stochastic and non-stationary (they spike unpredictably during outages), so a single optimized answer computed against one assumed demand level could look completely wrong the week reality deviates from that assumption.
- **Not a closed-form queueing formula** (e.g., Erlang-C), because it assumes a single ticket type, exponential service times, and one uniform agent pool — assumptions a real, multi-priority service desk violates (Gans, Koole & Mandelbaum, 2003).

### Q: Why is simulation specifically the right fit, positively (not just "the others don't fit")?
Because it lets the team safely explore scenarios that cannot ethically or practically be tested on a real service desk (e.g., deliberately understaffing to observe what breaks), it produces a distribution of outcomes rather than a single deterministic number (supporting genuine confidence in the result), and it directly supports the sensitivity analysis the assignment requires — sweeping staffing levels to find the point where performance degrades.

---

## Part 2 — What Data the Simulation Uses, and Why

### Q: What inputs does the simulation actually need to run?
Four categories, defined in the `PRIORITY_PROFILES` and `SCENARIOS` blocks of the code:
1. **Ticket priority mix** — the proportion of High / Medium / Low priority tickets
2. **Service time per priority** — average handling time per priority level
3. **SLA target per priority** — the deadline each priority level must be resolved within
4. **Arrival rate and agent count** — tickets per hour and staffing level, varied per scenario

### Q: Where did these numbers come from — real data, or assumptions?
Both, and the project is explicit about which is which:
- **Priority mix (20% High / 50% Medium / 30% Low), service times, and SLA target minutes are team assumptions**, clearly labeled as such in the code and report. They were not pulled directly from a dataset.
- **The overall shape and reality-check for those assumptions came from a real dataset** (see Part 3 below) — used for benchmarking and to justify that the *kind* of variability we're modeling (SLA attainment varying sharply by priority, real desks not achieving 100% SLA) is a genuine, observed phenomenon, not something invented for convenience.

### Q: Why use team assumptions instead of deriving everything from real data?
Two honest reasons:
1. **Time constraint.** With a 3-day runway to submission, fully reconstructing ticket-level records from a real event log (see Part 3) was judged too costly relative to the benefit — it would have consumed most of a day for a payoff that mostly changes how "grounded-sounding" the numbers are, not the core decision-support logic.
2. **The real data's actual distribution wasn't usable as-is.** The real dataset's priority split was extremely skewed (~94% of tickets in a single "Moderate" bucket) — too flat to produce a demonstrative sensitivity analysis, which the assignment specifically requires. Using it directly would have made the staffing sensitivity sweep far less illustrative.

### Q: Isn't it a problem that the priority mix, service times, and SLA targets are "made up"?
No — this is normal, expected practice for a first-pass academic simulation model, provided (a) it's clearly labeled rather than hidden, and (b) the *type* of randomness used is standard and defensible. Every number is either cited to a source or explicitly flagged as a team assumption — nothing is presented as data-derived when it isn't. This transparency is itself part of good simulation methodology (Law & Kelton).

### Q: Why exponential distributions specifically, for arrivals and service times?
For arrivals: exponential inter-arrival times are the standard way to generate a Poisson process — the widely used mathematical model for "events happening independently at some average rate," and the same underlying assumption behind classical formulas like Erlang-C, which keeps our model comparable to that textbook baseline.
For service times: the exponential distribution is the simplest, most standard starting assumption in queueing simulation. It's a known simplification — real resolution times are typically heavier-tailed — but it's a reasonable, well-precedented choice, not an arbitrary one, and it's explicitly named as a limitation in the report rather than left unstated.

### Q: Why does the simulation use randomness at all — why not fixed numbers?
Because real ticket arrivals and real handling times are not perfectly even in practice — they cluster and vary. A model with zero randomness would never reveal the realistic risk of a bad stretch (e.g., several slow tickets landing on the same agent back-to-back) even when the *average* workload looks fine. The randomness is what lets the simulation show the difference between "the math works out on average" and "the math holds up under real, messy variability" — which is the entire reason simulation was chosen over a static calculation in the first place.

### Q: If it's random, how can the results be trusted?
Because the simulation never relies on a single random run. Each scenario is run **30 times independently** (Monte Carlo replication), and the team reports the *average* result across all 30, plus the standard deviation (how much they varied). This is the same statistical logic as flipping a coin many times instead of once — individual outcomes are random, but the pattern that emerges across many trials is stable and trustworthy. This is standard simulation practice, following Law & Kelton's *Simulation Modeling and Analysis*.

---

## Part 3 — The Real-World Data Reference

### Q: Did the team use any real data at all, or is everything simulated/assumed?
Yes — the team explicitly grounded the model's credibility in a real dataset, used specifically for benchmarking and a discussion insight, not as the direct source of simulation input parameters.

### Q: What is the real dataset, and why that one?
**Amaral, C., Fantinato, M., & Peres, S. (2018). "Incident management process enriched event log."** UCI Machine Learning Repository. DOI: 10.24432/C57S4H.

It was chosen because it is **real, anonymized production data** from an actual company's ServiceNow instance — not synthetic or generated for a machine-learning demo, which is what most public "IT ticket" datasets are. It includes a genuine `made_sla` field (whether an incident missed its target SLA) and a `priority` field — exactly the two variables this project's decision problem revolves around. It is also CC BY 4.0 licensed, meaning it's freely citable with attribution.

### Q: How did the team actually get numbers out of it, given the time constraint?
The full raw event log (141,712 events across 24,918 incidents) was not downloaded and processed directly — reconstructing ticket-level records from an *event log* (which has multiple rows per incident, for each state change) is a real data-engineering task that would have consumed time the team didn't have. Instead, the team located a third-party public analysis notebook that had already computed direct cross-tabulations from the actual raw data, and cross-checked its numbers against the dataset's own official documentation for consistency (the notebook's closed-incident count of 24,985 matched the official UCI incident-state breakdown, and the derived overall SLA-miss rate of 36.6% matched the notebook author's own independently stated ~37% figure). This agreement across two independent sources gave reasonable confidence the extracted numbers were accurate.

### Q: What real numbers were actually extracted?
**Priority distribution** across 24,985 closed incidents: Critical ~1.1%, High ~1.6%, Moderate ~94.2%, Low ~3.1%.
**SLA attainment by priority**: Critical ~2.2%, High ~0.5%, Moderate ~64.5%, Low ~83.9%, **overall ~63.4%**.

### Q: What was the most interesting/useful finding from the real data?
That **Critical and High priority tickets had dramatically worse real-world SLA attainment than Moderate and Low priority tickets** — the opposite of naive intuition. The likely explanation: urgent tickets are given very tight SLA deadlines that are easy to breach under real-world friction (reassignment, escalation, complexity), while low-priority tickets get generous deadlines that are comparatively easy to hit. This became a genuine, citable insight used in the Conclusions section — evidence that SLA *design*, not just staffing level, is a real lever worth examining.

### Q: Why didn't the team just use the real priority mix (94% Moderate) in the simulation?
Because it's too flat to produce a demonstrative sensitivity analysis — the assignment specifically requires showing how SLA attainment changes as staffing varies, and a model where 94% of tickets are in one bucket wouldn't clearly show that dynamic. The team's own 20/50/30 mix was kept instead, explicitly labeled as a deliberate modeling choice made for demonstration purposes, not presented as if it came directly from the data.

### Q: What did the real data NOT give the team?
Resolution-time-in-minutes statistics per priority (the specific third-party analysis used focused on reassignment counts, reopen counts, and SLA outcome — not raw duration), and SLA target thresholds themselves (real ITSM datasets typically record actual outcomes, not the target deadlines being measured against). Both of these remain clearly labeled team assumptions in the simulation.

### Q: How was the real data actually used in the final simulation code and report?
As a **benchmark constant** (`REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT = 63.4`) printed alongside the simulation's own scenario results, and as a discussion point in the Evaluation & Scenario Analysis and Conclusions sections — specifically to compare against the model's Best Case/Baseline scenarios (which show 100% SLA attainment) and to explain that gap honestly: the model doesn't yet capture real-world operational friction (reassignments, reopened tickets, non-exponential service times), so a well-staffed simulated desk outperforms real-world averages. This is stated as a limitation, not hidden.

### Q: Is the real dataset used to validate the simulation, or just for color/context?
Mostly context and credibility, with one coincidental (not formal) validation point: the simulation's 3-agent sensitivity result (37.4% SLA attainment) happens to land close to the real dataset's overall SLA-miss rate (~36.6%). This is flagged explicitly as an interesting parallel, not proof of validation, since the two figures come from different underlying conditions (a specific low-staffing scenario in the model vs. an aggregate real-world figure across all conditions in the dataset).

---

## Part 4 — Model Design Decisions

### Q: Why three scenarios (Best/Baseline/Worst), and why add a fourth (Emergency)?
The assignment requires evaluation across multiple scenarios including best case, worst case, and sensitivity to changing conditions. The team built the three required scenarios first, then added a fourth — **Emergency (major outage)** — specifically because a sustained demand increase (Worst Case) and a short, sharp incident burst are genuinely different real-world situations with different decision implications. The Emergency scenario models a 2-hour, 45-ticket/hour burst skewed 70% toward High priority (simulating a major system outage), layered on top of otherwise-normal staffing.

### Q: What did the Emergency scenario reveal that the other three didn't?
That **a weekly average can completely hide a real crisis.** The Emergency scenario's weekly SLA average (84.8%) looks like a moderately bad week — but the SLA attainment computed *only* for the outage window itself is 40.8%, revealing the desk was in genuine crisis for those two hours even though the week "on average" looked tolerable. This is arguably the project's most valuable single finding, and it directly demonstrates why simulation (which can track this window separately) beats a static, single-number calculation.

### Q: Why 30 Monte Carlo replications specifically, and not more or fewer?
30 is a commonly used baseline in simulation practice for getting a stable average without excessive runtime. Since this particular simulation is extremely fast (each replication completes in a fraction of a second), the team could have afforded far more replications (100+) for an even tighter statistical picture — 30 was chosen as a reasonable, standard, defensible number, not a hard technical ceiling.

### Q: Why does the simulation discard the first hour of each replication ("warmup")?
Because a simulation "starting from empty" (no tickets in the queue yet at time zero) briefly looks artificially fast at the very beginning, before the system reaches its normal operating pattern. Discarding this warmup period is standard practice in discrete-event simulation, avoiding that startup distortion from contaminating the reported results.

### Q: Why is the dashboard's live simulation described as separate from the "official" results?
Because the Best/Baseline/Worst/Emergency scenario cards and the two sensitivity charts shown in the dashboard and report are fixed, cited numbers from actual Python runs — the ones the report's conclusions are built on. The dashboard additionally includes a genuinely live, browser-based re-implementation of the same core simulation logic (same queueing math, same Monte Carlo replication) that recomputes fresh results on demand, so a viewer can interact with new inputs rather than only browsing pre-computed data. Keeping these visually distinct avoids the official, citable results silently changing on every page reload.

---

### Q: Does the model serve High-priority tickets first?
No — and this is worth being precise about in the viva. The queue is **FIFO** (first-come-first-served): priorities determine each ticket's SLA target and average service time, but not the order of service. A real desk would typically triage High tickets to the front. The team tested this explicitly before submission: re-running the model with priority-ordered service (SimPy `PriorityResource`) showed the headline findings are **robust to this choice** — the 5-agent minimum holds under both disciplines, and the emergency on-call threshold shifts only slightly (~10 agents with priority service vs. 11 with FIFO). Since FIFO produces the more conservative (higher) staffing recommendation, the reported numbers err on the safe side. Priority-ordered dispatch is listed as a natural future improvement.

## Part 5 — Honest Limitations (Good to Have Ready)

### Q: What does the team acknowledge as weaknesses in this model?
- Exponential service times are a simplification; real IT ticket resolution times are typically heavier-tailed.
- Arrivals are modeled as constant-rate (plus one scripted emergency burst), not genuinely time-varying across business hours or days of the week.
- No agent skill differentiation — every agent can currently handle every priority level.
- No cost layer yet — the model reports SLA attainment but not labor cost per scenario.
- The model is a relative decision tool (comparing staffing levels against each other), not an absolute predictor of a real organization's exact SLA percentage.

### Q: If asked "how would you improve this given more time," what's the answer?
Empirical resampling of service times from a real recorded distribution instead of an assumed exponential curve; time-varying arrival rates reflecting real business-hour patterns; multi-skill agent routing (per Wallace & Whitt, 2005); an explicit cost-per-agent layer to make the Finance-vs-SLA tradeoff fully quantitative; and validation against a larger set of real incident logs beyond the single cross-tabulation used here.
