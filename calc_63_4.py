"""
Derivation of the 63.4% real-world SLA benchmark (Sec. IV.A, dashed line in Fig. 1).

63.4% is NOT a simulation output. It is an empirical reference value: the
share of closed incident records that met their SLA in an anonymised
ServiceNow incident event log:

    Amaral, C., Fantinato, M., & Peres, S. (2018). Incident management process
    enriched event log [Dataset]. UCI Machine Learning Repository.
    https://doi.org/10.24432/C57S4H  (CC BY 4.0)

Each record carries a boolean `made_sla` flag and a priority (impact x urgency).
The benchmark is computed over the 24,985 records with incident_state == "Closed":

    15,831 records with made_sla == True / 24,985 closed records = 63.4%

The per-priority cross-tabulation below is taken from a public analysis of the
same log (github.com/san-git/ML-Incident-Management, Incident_event_log.ipynb);
see docs/DS26_Real_Data_Grounding.md. Because the log contains one row per
event, the unit of analysis is closed-state event records, which is close to,
but not strictly identical with, the number of unique incidents.

In the simulation code the value is only a constant used for printing and for
the reference line in Fig. 1 (REAL_WORLD_SLA_ATTAINMENT_BENCHMARK_PCT = 63.4);
it does not feed any model parameter.

Usage:
    python calc_63_4.py                          # reproduce 63.4% from the cross-tab
    python calc_63_4.py incident_event_log.csv   # recompute from the raw UCI CSV (needs pandas)
"""
import sys

# Cross-tab of made_sla by priority, closed incidents (counts as recorded
# in docs/DS26_Real_Data_Grounding.md, Section 3.2)
CROSSTAB = {
    #  priority          met_sla  total
    "1 - Critical":     (6,       271),
    "2 - High":         (2,       408),
    "3 - Moderate":     (15171,   23529),
    "4 - Low":          (652,     777),
}


def from_crosstab():
    print("SLA attainment = (closed incidents with made_sla == True) / (all closed incidents)\n")
    print(f"{'Priority':<15}{'met SLA':>10}{'total':>10}{'attainment':>13}")
    met_sum = tot_sum = 0
    for p, (met, tot) in CROSSTAB.items():
        met_sum += met
        tot_sum += tot
        print(f"{p:<15}{met:>10,}{tot:>10,}{met / tot * 100:>12.1f}%")
    print("-" * 48)
    overall = met_sum / tot_sum * 100
    print(f"{'Overall':<15}{met_sum:>10,}{tot_sum:>10,}{overall:>12.1f}%")
    print()
    print(f"Numerator   = 6 + 2 + 15,171 + 652 = {met_sum:,}")
    print(f"Denominator = 271 + 408 + 23,529 + 777 = {tot_sum:,}")
    print(f"63.4% check : {met_sum:,} / {tot_sum:,} = {met_sum / tot_sum:.5f} -> {overall:.1f}%")
    print(f"Miss rate   : 100 - {overall:.2f} = {100 - overall:.1f}%  (the '~37% miss SLA' cross-check)")
    assert round(overall, 1) == 63.4
    return overall


def from_raw_csv(path):
    """Recompute from the raw UCI event log so the figure can be audited.
    The log has one row per EVENT, so an incident appears many times. Two
    unit-of-analysis choices are shown; the 24,985 denominator used in the
    paper corresponds to event rows whose incident_state == 'Closed'."""
    import pandas as pd
    df = pd.read_csv(path, na_values="?")
    df["made_sla"] = df["made_sla"].astype(str).str.lower().eq("true")
    closed = df[df["incident_state"] == "Closed"]
    print(f"[A] rows with incident_state == 'Closed': {len(closed):,}")
    ct = pd.crosstab(closed["priority"], closed["made_sla"], margins=True)
    print(ct)
    print(f"    overall made_sla rate: {closed['made_sla'].mean() * 100:.1f}%\n")
    last = df.sort_values("sys_updated_at").groupby("number").tail(1)
    print(f"[B] last event per incident number: {len(last):,} incidents")
    print(f"    overall made_sla rate: {last['made_sla'].mean() * 100:.1f}%")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        from_raw_csv(sys.argv[1])
    else:
        from_crosstab()
