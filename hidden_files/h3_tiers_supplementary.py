#!/usr/bin/env python3
"""
H3 supplementary tiers — POST-PREREG SUPPLEMENTARY, NON-CONFIRMATORY.

The preregistered H3 (contract-tier gradient, Kruskal-Wallis across tiers
within each cell) was untestable as specified:
  * sports prereg tiers S1-S4 are absolute-price bands; the analyzed sports
    contracts pile into S1/S2 (358/78 of 492 pairs), leaving S3 nearly empty
    and the gradient unidentified;
  * macro prereg tiers M0-M3 need verified consensus (moneyness_steps); the
    Sept-16 cluster events (russia_sanctions_bill, tariff_eu_threat,
    trump_truth_fed) are all M? (no verified consensus), and only 6 of 9
    macro events have any tiered contracts.

This script builds post-prereg supplementary tiers that are identified in
the data we actually have:
  * SPORTS: terciles of pre-event midpoint WITHIN each cell (P1=low, P2=mid,
    P3=high pre-price). Relative expensiveness replaces the absolute S1-S4 bands.
  * MACRO non-bucket markets: terciles of |midpoint - 0.5| at T-1 — N/A here:
    every analyzed macro pair is a macro_bucket contract, so this leg is empty
    by construction (recorded, not silently skipped).
  * MACRO bucket markets: keep prereg M0-M3 where moneyness_steps exists
    (M? excluded, same as confirmatory).

Test: Kruskal-Wallis across tiers within each cell, 3-day window, on
abnormal_move and on |abnormal_move| (mirrors D8's two legs). Pair-level
observations — pairs within an event are correlated, so p-values are
anti-conservative; treat as EXPLORATORY. Reported alongside per-tier
n_pairs / n_events / means so the reader can judge.

Output: hidden_files/analysis_real/tier_supplementary_3d.csv
Label POST-PREREG SUPPLEMENTARY on every row.
"""

import os
import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = os.path.join(BASE, "hidden_files", "analysis_real", "pair_results.csv")
OUT = os.path.join(BASE, "hidden_files", "analysis_real", "tier_supplementary_3d.csv")
LABEL = "POST-PREREG SUPPLEMENTARY"


def tercile_tiers(s, prefix):
    """Terciles of a series -> tier codes; returns (codes, n_bins)."""
    s = s.dropna()
    if s.nunique() < 2:
        return pd.Series("T1", index=s.index), 1
    try:
        cats = pd.qcut(s, 3, labels=[f"{prefix}1", f"{prefix}2", f"{prefix}3"],
                       duplicates="drop")
    except ValueError:
        return pd.Series(f"{prefix}1", index=s.index), 1
    return cats, len(cats.cat.categories)


def main():
    p = pd.read_csv(PAIRS)
    p = p[p["window_days"] == 3].copy()
    p["abs_abn"] = p["abnormal_move"].abs()

    rows = []
    for liquid_label, frame in [("full", p), ("liquid_only", p[p["liquid"]])]:
        for cell, g in frame.groupby("cell"):
            g = g.copy()
            note = ""
            if (g["market_kind"] == "sports_future").all():
                tiers, nb = tercile_tiers(g["pre_mid"], "P")
                g["supp_tier"] = tiers
                tier_def = ("terciles of pre-event midpoint within cell "
                            f"(n_bins={nb})")
            elif (g["market_kind"] == "macro_bucket").all():
                g["supp_tier"] = g["tier"].where(g["tier"] != "M?", np.nan)
                tier_def = "prereg M0-M3 where moneyness_steps exists (M? dropped)"
            else:
                # mixed kinds should not happen; keep prereg tiers as fallback
                g["supp_tier"] = g["tier"]
                tier_def = "mixed market kinds: prereg tiers"
            # macro non-bucket leg: explicitly record emptiness
            n_nonbucket = int((g["market_kind"] != "macro_bucket").sum()) \
                if (g["market_kind"] == "macro_bucket").any() else 0
            present = sorted(g["supp_tier"].dropna().unique())
            for metric in ["abnormal_move", "abs_abn"]:
                mname = "abnormal" if metric == "abnormal_move" else "abs_abnormal"
                groups = [g[g["supp_tier"] == t][metric].dropna().values
                          for t in present]
                groups = [x for x in groups if len(x) >= 2]
                tier_stats = "; ".join(
                    f"{t}: n_pairs={int((g['supp_tier'] == t).sum())}, "
                    f"n_events={int(g[g['supp_tier'] == t]['event_id'].nunique())}, "
                    f"mean_{mname}={g[g['supp_tier'] == t][metric].mean():+.4f}"
                    for t in present)
                if len(groups) >= 2 and int(g["event_id"].nunique()) >= 2:
                    try:
                        h, pkw = stats.kruskal(*groups)
                    except ValueError:
                        h, pkw = np.nan, np.nan
                    tested = True
                else:
                    h, pkw, tested = np.nan, np.nan, False
                    if int(g["event_id"].nunique()) < 2:
                        note = (note + " | " if note else "") + \
                            "single event in cell: cross-tier KW not interpretable"
                    else:
                        note = (note + " | " if note else "") + \
                            f"{mname}: <2 tiers with >=2 pairs; KW not run"
                rows.append({
                    "cell": cell, "metric": mname,
                    "tier_definition": tier_def,
                    "tiers_compared": present if tested else [],
                    "H": round(float(h), 4) if pd.notna(h) else "",
                    "p": round(float(pkw), 6) if pd.notna(pkw) else "",
                    "tested": tested,
                    "n_pairs": int(len(g)), "n_events": int(g["event_id"].nunique()),
                    "per_tier": tier_stats,
                    "note": note,
                    "macro_nonbucket_note": ("no non-bucket macro pairs in "
                                             "analyzed sample; |mid-0.5| tercile "
                                             "leg empty by construction"),
                    "caveat": ("pair-level KW; pairs within an event are "
                               "correlated so p-values are anti-conservative; "
                               "exploratory only"),
                    "sample_filter": liquid_label,
                    "label": LABEL,
                })
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(out[["cell", "sample_filter", "metric", "H", "p", "tested",
               "n_pairs", "n_events"]].to_string(index=False))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
