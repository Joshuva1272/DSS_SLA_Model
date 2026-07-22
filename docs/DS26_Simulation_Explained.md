# How the Simulation Works — A Detailed Walkthrough
## Simulation-Based DSS for IT Service Desk Staffing

**Purpose of this document:** A complete, plain-language explanation of `it_service_desk_dss_simulation.py` — not just *what* the code does, but *why* every decision was made the way it was. This is meant so that every team member can explain any part of it in the viva without having personally written that part.

---

## 1. The Decision Problem, Restated Simply

We are trying to answer: **if we staff N agents on the IT service desk, how well will we actually meet our SLA targets, and how does that change as N goes up or down?**

We can't test this by actually understaffing a real service desk to see what breaks — that would hurt real users. So instead, we build a **pretend service desk inside the computer** that behaves statistically like a real one, and we experiment on that instead. That pretend desk is the simulation.

---

## 2. What "Running the Simulation" Actually Requires

Before touching the logic, it's worth being clear on the practical side, since this came up as a point of confusion:

- **Software needed:** Python, plus two libraries — `simpy` (the simulation engine) and `matplotlib` (for the chart). Installed once via `pip install simpy matplotlib`.
- **Hardware needed:** None special. This is not a machine-learning model — there is no "training," no GPU, no long processing time.
- **Time to run:** Under one second, even though it simulates the equivalent of many weeks of ticket traffic and runs every scenario dozens of times over. It does not need to be left running overnight — there is nothing for it to keep computing; it finishes almost instantly and simply exits.
- **Data needed to run it:** None required — the simulation *generates* its own tickets mathematically rather than reading them from a file (more on why below).

---

## 3. The Big Idea: Why We Generate Random Tickets Instead of Using Fixed Numbers

This is the part that raised the most questions, so it's worth explaining carefully.

### 3.1 Why not just say "tickets arrive every 5 minutes, exactly"?
Because that's not how real ticket arrivals behave, and pretending otherwise would make the model *less* trustworthy, not more. Real arrivals cluster and gap unpredictably — sometimes three tickets land in the same minute, sometimes there's a 20-minute lull. If we modeled arrivals as perfectly even, the simulation could never reveal what happens during a realistic cluster of tickets — which is exactly the situation that causes real SLA breaches.

### 3.2 Why not just say "every ticket takes exactly 20 minutes"?
Same reason. Real service times vary — a password reset takes 2 minutes, a tricky network issue takes an hour. If we hid that variability, the model would always look artificially smooth and would never show the realistic risk of a bad stretch where several slow tickets land on the same agent back-to-back, causing a temporary pileup even when the *average* workload is technically fine.

### 3.3 So how does randomness actually produce a trustworthy answer?
This is the key insight: **one random simulation run is not trustworthy on its own** — that part of the concern was completely valid. But we don't rely on one run. We run each scenario **30 times** and look at the average result across all 30, plus how much they vary.

The same logic as flipping a coin: one flip tells you nothing reliable, but 1,000 flips reliably tell you whether the coin is fair, because the randomness "averages out" into a stable, predictable pattern. This is a basic, well-established statistical principle (sometimes called the "law of large numbers"), and it's the exact justification the field's standard simulation textbook (Law & Kelton, *Simulation Modeling and Analysis*) gives for why simulations use multiple replications instead of a single run.

### 3.4 What this means for the decision's validity
The staffing recommendation is never "here's what happened in one lucky/unlucky trial." It's: *"across 30 simulated weeks with realistic random variation, this staffing level met SLA targets X% of the time, and here's how much that result varied."* That is a **more honest and more useful** answer than a single deterministic number, because it tells the IT Manager not just what to expect on average, but how much risk of a bad week still remains at a given staffing level.

---

## 4. Walking Through the Code, Section by Section

### 4.1 The Assumptions Block
```python
SIM_HOURS = 8 * 5          # simulate one work week (8-hour days x 5 days)
WARMUP_HOURS = 1           # discard first hour of stats
NUM_REPLICATIONS = 30      # Monte Carlo replications per scenario
```
**What this means:** We simulate a pretend work week (40 hours), repeated 30 times per scenario. The `WARMUP_HOURS` setting exists because a simulation "starting from empty" (no tickets in the queue yet) briefly looks artificially fast at the very beginning — discarding the first simulated hour avoids that startup distortion contaminating the results, a standard practice in discrete-event simulation.

**Why 30 replications specifically?** 30 is a commonly used baseline in simulation practice as a reasonable number to get a stable average without excessive runtime — since our simulation is so fast, we could actually afford far more (100+) if we wanted a tighter statistical picture, and this is an easy, defensible upgrade if you want to strengthen the report further.

```python
PRIORITY_PROFILES = {
    "High":   {"share": 0.20, "mean_service_min": 20, "sla_min": 30},
    "Medium": {"share": 0.50, "mean_service_min": 15, "sla_min": 60},
    "Low":    {"share": 0.30, "mean_service_min": 10, "sla_min": 240},
}
```
**What this means:** Of all tickets, 20% are High priority, 50% Medium, 30% Low. Each priority has its own *average* handling time and its own SLA deadline. These are currently placeholder numbers — this is exactly the block your team should replace with either real-data-informed figures or clearly labeled team assumptions.

```python
SCENARIOS = {
    "Best Case (low volume, fully staffed)":  {"arrival_rate": 8,  "num_agents": 6},
    "Baseline (typical week)":                 {"arrival_rate": 14, "num_agents": 6},
    "Worst Case (surge, same staffing)":       {"arrival_rate": 22, "num_agents": 6},
}
```
**What this means:** Three named scenarios, each defined by how many tickets arrive per hour and how many agents are on duty. Note the Worst Case keeps staffing *the same* as Baseline (6 agents) but increases ticket volume — this deliberately isolates the effect of a demand surge, rather than changing both variables at once, which would make it unclear what's actually causing any performance change.

### 4.2 The `ServiceDesk` Class — the pretend office itself
```python
class ServiceDesk:
    def __init__(self, env, num_agents):
        self.agents = simpy.Resource(env, capacity=num_agents)
        self.wait_times = []
        self.sla_met = []
```
**What this means:** This creates a pretend office with a fixed number of "agent seats" (`simpy.Resource`). Any ticket that arrives when all seats are full has to wait in line. Two lists are kept: how long each ticket waited, and whether it met its SLA — these are the raw ingredients for every statistic reported later.

```python
def handle_ticket(self, priority, mean_service_min, sla_min):
    arrival_time = self.env.now
    with self.agents.request() as req:
        yield req
        wait_minutes = (self.env.now - arrival_time) * 60
        ...
        service_time_hours = random.expovariate(1.0 / (mean_service_min / 60))
        yield self.env.timeout(service_time_hours)
```
**What this means, step by step:**
1. The ticket "arrives" and the clock starts.
2. It requests an agent (`req`) — if none are free, it simply waits here until one becomes available; this line *is* the queue.
3. Once an agent is free, we calculate how long the ticket waited.
4. We check whether that wait was within the SLA target, and record yes/no.
5. We generate a random service duration using `random.expovariate` — this is the actual random-number generator producing a realistic spread of times (see below for why this specific shape was chosen).
6. `env.timeout(...)` is SimPy's way of saying "the agent is now busy doing this for this simulated duration" — no real waiting happens; this is symbolic simulated time.

**Why `random.expovariate` (the exponential distribution) specifically?** This is the standard, simplest choice in queueing simulation for modeling "time until something finishes," and it's the same assumption underlying classical formulas like Erlang-C — using it here keeps our model comparable to that textbook baseline while still being flexible enough to add multiple priorities, which Erlang-C itself cannot do. It is a simplification (see Limitations below) — real resolution times are often more heavy-tailed than a pure exponential curve — but it's a reasonable, well-precedented starting assumption, not an arbitrary one.

### 4.3 The Ticket Generator — where tickets come from
```python
def ticket_generator(env, desk, arrival_rate_per_hour, priority_profiles):
    while True:
        interarrival_hours = random.expovariate(arrival_rate_per_hour)
        yield env.timeout(interarrival_hours)
        priority = random.choices(priorities, weights=weights, k=1)[0]
        env.process(desk.handle_ticket(...))
```
**What this means:** This is an infinite loop that keeps creating new tickets for as long as the simulated week runs. The *gap* between one ticket and the next is itself random (again exponential) — this is what makes arrivals a **Poisson process**, the standard mathematical model for "events happening independently at some average rate," used for everything from call arrivals to radioactive decay. Each new ticket is then randomly assigned a priority according to the percentages we set (`random.choices` with `weights`).

### 4.4 Running One Replication
```python
def run_single_replication(...):
    env = simpy.Environment()
    desk = ServiceDesk(env, num_agents)
    env.process(ticket_generator(...))
    env.run(until=sim_hours)
    ...
    avg_wait = statistics.mean(...)
    sla_attainment = (... / len(filtered_sla) * 100)
    return {...}
```
**What this means:** This sets up one pretend work week from scratch, lets it run to completion (`env.run`), then calculates two headline numbers from everything that happened: the average wait time, and the percentage of tickets that met their SLA. This whole function represents **one single trial** — one possible version of "how the week could have gone."

### 4.5 Running a Scenario — the Monte Carlo part
```python
def run_scenario(arrival_rate, num_agents, replications=NUM_REPLICATIONS):
    results = [run_single_replication(...) for _ in range(replications)]
    avg_waits = [r["avg_wait_minutes"] for r in results]
    sla_pcts = [r["sla_attainment_pct"] for r in results]
    return {
        "avg_wait_mean": statistics.mean(avg_waits),
        "avg_wait_stdev": statistics.stdev(avg_waits),
        "sla_mean": statistics.mean(sla_pcts),
        "sla_stdev": statistics.stdev(sla_pcts),
    }
```
**What this means:** This is where the "one random run isn't enough" problem gets solved. It calls the single-replication function 30 times in a row (30 independent pretend weeks, each with its own fresh random ticket stream), then reports the **average across all 30**, plus the **standard deviation** — a measure of how much the 30 results varied from each other. A small standard deviation means the result is stable and trustworthy; a large one means there's still meaningful week-to-week uncertainty at that staffing level, which is itself useful information for the decision-maker.

### 4.6 Scenario Comparison Output
```python
def print_scenario_comparison():
    for label, cfg in SCENARIOS.items():
        result = run_scenario(cfg["arrival_rate"], cfg["num_agents"])
        print(...)
```
**What this means:** This runs all three named scenarios (Best/Baseline/Worst) and prints a side-by-side table of their average wait time and SLA attainment, each with a ± range showing the spread across the 30 replications.

### 4.7 The Sensitivity Sweep
```python
def run_sensitivity_sweep():
    for n in SENSITIVITY_AGENT_RANGE:
        result = run_scenario(SENSITIVITY_ARRIVAL_RATE, n)
        ...
    plt.errorbar(agent_counts, sla_means, yerr=sla_stdevs, ...)
    plt.savefig("it_service_desk_sensitivity.png")
```
**What this means:** This repeats the entire 30-replication process for *every* staffing level from 3 to 10 agents, holding ticket volume fixed at the "Baseline" rate. The result is plotted as a chart: number of agents on the horizontal axis, SLA attainment percentage on the vertical axis, with error bars showing the ± spread at each point. This chart is the direct visual answer to "how many agents do we actually need" — you can see exactly where the line jumps from poor to acceptable performance, which is the **minimum viable staffing level**.

### 4.8 The Main Block
```python
if __name__ == "__main__":
    random.seed(42)
    print_scenario_comparison()
    run_sensitivity_sweep()
```
**What this means:** `random.seed(42)` is worth explaining specifically — it forces the "random" numbers to follow the same sequence every time the script is run, purely so that results are **reproducible** while developing and debugging (so you can compare two versions of the code fairly, without differences caused by luck). For your final report numbers, you can remove this line (or change the seed) to confirm the findings hold up under genuinely fresh randomness too — a good thing to mention if asked in the viva.

---

## 5. What You Actually See When It Runs

**In the terminal:** A table like this (example from an earlier test run):

| Scenario | Avg Wait (min) | SLA Attainment % |
|---|---|---|
| Best Case | 0.1 (±0.1) | 100.0 (±0.0) |
| Baseline | 0.9 (±0.6) | 100.0 (±0.0) |
| Worst Case | 12.4 (±8.3) | 96.2 (±5.4) |

Followed by the sensitivity sweep results (SLA attainment at each staffing level from 3 to 10 agents), and confirmation that the chart image was saved.

**As a file:** `it_service_desk_sensitivity.png` — the chart described above.

---

## 6. Limitations, Stated Honestly (Good Material for Your Conclusions Section)

- **Exponential service times are a simplification.** Real IT ticket resolution times are often heavier-tailed (most tickets resolve quickly, but a long tail take much longer). A stronger version of this model could use **empirical resampling** — drawing simulated service times randomly from a real list of recorded resolution times (e.g., from the Mendeley helpdesk dataset) instead of an assumed mathematical curve. This keeps the randomness (still essential, per Section 3) but grounds its *shape* in real recorded variability rather than a textbook assumption.
- **Arrivals are currently modeled as a constant average rate.** Real service desks see arrivals cluster around business hours and spike after incidents; this model doesn't yet capture time-of-day effects.
- **No agent skill differentiation yet.** Every agent can currently handle every priority level; extending this (per Wallace & Whitt, 2005, in the literature compendium) is a natural next step if time allows.
- **No cost layer yet.** The model reports SLA attainment but not labor cost per scenario — adding a simple "cost per agent per shift" figure would let you show the Finance-vs-SLA tradeoff explicitly.

None of these limitations invalidate the model — they're normal, expected simplifications for a first-pass simulation, and explicitly naming them (rather than letting a professor find them first) is itself good practice.

---

## 7. Quick-Reference: Likely Viva Questions About the Simulation

- **"Why 30 replications and not 1?"** → See Section 3.3 — a single run isn't statistically reliable; averaging many independent runs is standard simulation practice (Law & Kelton).
- **"Why exponential distribution for service times?"** → Standard, simple, comparable to the Erlang-C baseline we're arguing against; a known simplification, addressed as a stated limitation.
- **"Isn't this just random numbers — how is the output meaningful?"** → See Section 3 in full — the randomness reflects real-world variability; the *averaged pattern* across many trials is what's meaningful, not any single trial.
- **"How long did this take to run?"** → Under a second; this is a lightweight discrete-event simulation, not a machine learning model.
- **"What would make this more realistic?"** → Empirical resampling from real data, time-varying arrivals, multi-skill agents, added cost layer — all listed in Section 6.
