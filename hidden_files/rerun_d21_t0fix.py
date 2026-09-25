#!/usr/bin/env python3
"""D21: re-run the 3 batch-C scheduled-sports events with VERIFIED T0s.

The D14 batch-C pull ran with web search down, so it used approx T0s:
  nba_draft_lottery_2026: 2026-05-11 -> verified 2026-05-10 (Sun, 3pm ET, ABC)
  nba_draft_2026:         2026-06-24 -> verified 2026-06-23 (round 1, 8pm ET;
                          Jun 24 was round 2 - the news lands on night 1)
  mlb_allstar_2026:       2026-07-14 -> verified correct (Tue Jul 14, 8pm ET)

Replicates analyze_d16.analyze_pair exactly (same baseline rules incl. D16),
then re-aggregates to event means and recomputes the H1b extended contrast.
"""
import sys, importlib.util
import numpy as np
import pandas as pd
from scipy import stats

spec = importlib.util.spec_from_file_location("a16", "analyze_d16.py")
a16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a16)

CORRECTED_T0 = {
    "nba_draft_lottery_2026": "2026-05-10T19:00:00Z",  # 3pm ET -> 19:00Z
    "nba_draft_2026":         "2026-06-24T00:00:00Z",  # placeholder, set below
    "mlb_allstar_2026":       "2026-07-14T12:00:00Z",
}
# Draft round 1: Tue Jun 23, 8pm ET = Jun 24 00:00Z. Event DAY is Jun 23;
# use noon ET Jun 23 so the [T0, T0+3d] window covers the reaction candles.
CORRECTED_T0["nba_draft_2026"] = "2026-06-23T16:00:00Z"  # noon ET Jun 23
# All-Star: Tue Jul 14, 8pm ET. Same treatment: noon ET on game day.
CORRECTED_T0["mlb_allstar_2026"] = "2026-07-14T16:00:00Z"
# Lottery: Sun May 10, 3pm ET.
CORRECTED_T0["nba_draft_lottery_2026"] = "2026-05-10T19:00:00Z"

ev_all = pd.read_csv("hidden_files/pairs_combined.csv")
md = pd.read_csv("hidden_files/market_data_combined.csv")
md["ts_raw"] = md["timestamp"].astype(str)
md["ts"] = md["timestamp"].apply(a16.parse_iso_utc)
md["mid"] = md.apply(a16.midpoint, axis=1)
md["spread"] = pd.to_numeric(md["ask"], errors="coerce") - pd.to_numeric(md["bid"], errors="coerce")
for c in ["volume", "trades", "open_interest"]:
    if c in md.columns:
        md[c] = pd.to_numeric(md[c], errors="coerce")
a16.TRADES_AVAILABLE = "trades" in md.columns and md["trades"].notna().any()

print("event_id,n_pairs_run,n_ok,abn_event_cents,rule")
event_means = {}
for eid, t0 in CORRECTED_T0.items():
    rows = ev_all[ev_all["event_id"] == eid]
    pair_abns, rules = [], []
    for _, er in rows.iterrows():
        er = er.copy()
        er["event_time"] = t0
        er["first_report_time"] = t0
        r = a16.analyze_pair(er, md, 3)
        if r is not None:
            pair_abns.append(r["abnormal_move"])
            rules.append(r["baseline_rule"])
    ab = np.array(pair_abns)
    from collections import Counter
    rule = Counter(rules).most_common(1)[0][0] if rules else "n/a"
    mean_c = ab.mean() * 100 if len(ab) else float("nan")
    event_means[eid] = mean_c
    print(f"{eid},{len(rows)},{len(ab)},{mean_c:+.2f},{rule}")

# H1b extended: 15 unsched_sports (existing) vs 5 sched_sports (2 unchanged + 3 corrected)
old = pd.read_csv("hidden_files/analysis_real/event_results_d16xd.csv")
old = old[(old["window_days"] == 3)]
unsched = old[old["cell"] == "unsched_sports"]["abn_event"].values * 100
sched_old = {r["event_id"]: r["abn_event"] * 100 for _, r in
             old[old["cell"] == "sched_sports"].iterrows()}
sched = np.array([
    sched_old["nba_schedule_release"],
    sched_old["nfl_kickoff"],
    event_means["mlb_allstar_2026"],
    event_means["nba_draft_2026"],
    event_means["nba_draft_lottery_2026"],
])
print("\nsched_sports event means (cents):", np.round(sched, 2))
print("unsched_sports mean: %+.2f (n=%d)" % (unsched.mean(), len(unsched)))
print("sched_sports mean:   %+.2f (n=%d)" % (sched.mean(), len(sched)))
t, p = stats.ttest_ind(unsched, sched, equal_var=False)
print("Welch t=%.3f p=%.4f" % (t, p))
