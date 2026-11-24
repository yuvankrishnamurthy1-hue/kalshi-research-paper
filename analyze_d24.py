#!/usr/bin/env python3
"""D24 analysis: consistent estimand, Sep-16 contamination, and the
cutoff extension to 2026-11-24.

Why this script exists
----------------------
1. Reproducibility gap. The D17/D18 involved-teams numbers and the D22
   cluster sensitivity were computed ad hoc; no committed script produced
   hidden_files/analysis_real/involved_teams_3d.csv. This script recomputes
   them from the committed market data and reproduces the legacy numbers
   (section A) so the paper's headline is rerunnable.

2. Estimand mismatch (found 2026-11-24). D18 compared
     macro:  abnormal move = midpoint at the END of the 3-day window minus the
             T-30..T-5 baseline, window anchored at the exact T0 timestamp
             (analyze_d16.analyze_pair), averaged over the event's contracts;
     sports: abnormal move = MEAN of the 3 daily midpoints starting at
             midnight of the T0 date (so it includes the pre-news candle)
             minus the baseline.
   Those are different quantities. Here BOTH cells go through
   analyze_d16.analyze_pair, so the comparison is like-for-like.

3. Sep-16 contamination. Three "unscheduled macro" events share the date of
   the scheduled 2026-09-16 FOMC hike and the same KXFED contracts; their
   +8 to +9.5c moves are statistically indistinguishable from the hike's own
   +9.3c. Sensitivities: (a) collapse to one observation (D22), (b) drop all
   three (the prereg's contamination logic applied to macro, as D17 already
   applied it to the Boston sports events).

4. Cutoff extension (D24). Adds the events pulled by collect_d24.py.

Outputs: hidden_files/analysis_real/d24_*.csv and a printed summary.
"""
import os, sys
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
HID = os.path.join(HERE, "hidden_files")
OUT = os.path.join(HID, "analysis_real")
sys.path.insert(0, HERE)
import analyze_d16 as A  # noqa: E402

W = 3  # headline window
RNG = np.random.default_rng(20261124)

SEP16_UNSCHED = {"tariff_eu_threat", "russia_sanctions_bill", "trump_truth_fed"}

# Involved teams: (event_id, ticker, role). Summer roles copied from the
# legacy involved_teams_3d.csv; D24 roles from the transaction reports.
INVOLVED = [
    # --- summer (legacy D17 set) ---
    ("giannis_to_heat", "KXNBA-27-MIA", "get"), ("giannis_to_heat", "KXNBA-27-MIL", "give"),
    ("jaylen_brown_to_76ers", "KXNBA-27-PHI", "get"), ("jaylen_brown_to_76ers", "KXNBA-27-BOS", "give"),
    ("dlo_six_team_trade", "KXNBA-27-MEM", "get"),
    ("myles_garrett_to_rams", "KXSB-27-LAR", "get"), ("myles_garrett_to_rams", "KXSB-27-CLE", "give"),
    ("aj_brown_to_patriots", "KXSB-27-NE", "get"), ("aj_brown_to_patriots", "KXSB-27-PHI", "give"),
    ("kawhi_to_raptors", "KXNBA-27-TOR", "get"), ("kawhi_to_raptors", "KXNBA-27-LAC", "give"),
    ("lebron_to_76ers", "KXNBA-27-PHI", "get"), ("lebron_to_76ers", "KXNBA-27-LAL", "give"),
    ("von_miller_to_cowboys", "KXSB-27-DAL", "get"),
    ("donovan_mitchell_extension", "KXNBA-27-CLE", "keep"),
    ("brian_oneill_extension", "KXSB-27-MIN", "keep"),
    ("aaron_donald_comeback", "KXSB-27-LAR", "get"),
    # contaminated Boston rows (kept for transparency, excluded from tests)
    ("mitchell_robinson_to_celtics", "KXNBA-27-BOS", "get"),
    ("mike_conley_to_celtics", "KXNBA-27-BOS", "get"),
    ("neemias_queta_extension", "KXNBA-27-BOS", "keep"),
    ("jordan_walsh_extension", "KXNBA-27-BOS", "keep"),
    # --- D24 additions ---
    ("wemby_extension", "KXNBA-27-SAS", "keep"),
    ("mccarthy_to_giants", "KXSB-27-NYG", "get"), ("mccarthy_to_giants", "KXSB-27-MIN", "give"),
    ("harrison_to_texans", "KXSB-27-HOU", "get"), ("harrison_to_texans", "KXSB-27-ARI", "give"),
    ("buckner_to_49ers", "KXSB-27-SF", "get"), ("buckner_to_49ers", "KXSB-27-IND", "give"),
    ("simmons_to_bears", "KXSB-27-CHI", "get"), ("simmons_to_bears", "KXSB-27-TEN", "give"),
    ("jaguars_davis_bates", "KXSB-27-JAC", "get"), ("jaguars_davis_bates", "KXSB-27-PHI", "give"),
    ("cousins_to_vikings", "KXSB-27-MIN", "get"), ("cousins_to_vikings", "KXSB-27-LV", "give"),
    ("downs_to_chiefs", "KXSB-27-KC", "get"), ("downs_to_chiefs", "KXSB-27-IND", "give"),
    ("allen_to_49ers", "KXSB-27-SF", "get"),
]
CONTAMINATED = {"mitchell_robinson_to_celtics", "mike_conley_to_celtics",
                "neemias_queta_extension", "jordan_walsh_extension"}
D24_EVENTS = {"wemby_extension", "mccarthy_to_giants", "harrison_to_texans",
              "buckner_to_49ers", "simmons_to_bears", "jaguars_davis_bates",
              "cousins_to_vikings", "downs_to_chiefs", "allen_to_49ers",
              "nvda_earnings_q3", "hormuz_tanker_mines",
              "cpi_sep_release", "fomc_oct_hold", "cpi_oct_release"}
# Deadline-day NFL trades share the scheduled-deadline window and in-season
# game weeks; flagged, reported, and tested with and without.
INSEASON = {"mccarthy_to_giants", "harrison_to_texans", "buckner_to_49ers",
            "simmons_to_bears", "jaguars_davis_bates", "cousins_to_vikings",
            "downs_to_chiefs", "allen_to_49ers"}


def build_inputs():
    """Combined pair registry + market data (summer + extended + D24)."""
    pairs = pd.read_csv(os.path.join(HID, "pairs_combined_supp.csv"))
    md = pd.read_csv(os.path.join(HID, "market_data_combined.csv"))
    d24dir = os.path.join(HERE, "kalshi_api_data_d24")
    if os.path.exists(os.path.join(d24dir, "market_metadata.csv")):
        meta = pd.read_csv(os.path.join(d24dir, "market_metadata.csv"))
        sports = ("KXNBA", "KXSB", "KXMLB")
        new = pd.DataFrame({
            "event_id": meta["event_id"], "event_time": meta["t0_utc"],
            "event_type": meta["event_type"], "market_ticker": meta["ticker"],
            "market_kind": ["sports_future" if s in sports else "macro_bucket"
                            for s in meta["series"]],
            "surprise": "", "moneyness_steps": "",
            "first_report_time": meta["t0_utc"], "exploratory": 0})
        # events already registered with a placeholder row set are replaced
        pairs = pairs[~pairs["event_id"].isin(set(new["event_id"]))]
        pairs = pd.concat([pairs, new], ignore_index=True)
        md24 = pd.read_csv(os.path.join(d24dir, "market_data.csv"))
        md = pd.concat([md, md24], ignore_index=True).drop_duplicates(
            ["timestamp", "ticker"], keep="last")
    p_path = os.path.join(HID, "pairs_d24.csv")
    m_path = os.path.join(HID, "market_data_d24_combined.csv")
    pairs.to_csv(p_path, index=False)
    md.to_csv(m_path, index=False)
    return p_path, m_path


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    t, p = stats.ttest_ind(a, b, equal_var=False)
    return float(t), float(p)


def perm_p(a, b, n=20000):
    """Two-sided permutation p-value for difference in means (small-n check)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    obs = abs(a.mean() - b.mean())
    pool = np.concatenate([a, b])
    hits = 0
    for _ in range(n):
        RNG.shuffle(pool)
        if abs(pool[:len(a)].mean() - pool[len(a):].mean()) >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (n + 1)


def contrast(name, a, b, la, lb):
    a, b = np.asarray(a, float), np.asarray(b, float)
    t, p = welch(a, b)
    d = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return {"analysis": name, "group_a": la, "n_a": len(a), "mean_a_c": round(100 * a.mean(), 2),
            "group_b": lb, "n_b": len(b), "mean_b_c": round(100 * b.mean(), 2),
            "gap_c": round(100 * d, 2), "gap_ci95_c": f"[{100*(d-1.96*se):.2f}, {100*(d+1.96*se):.2f}]",
            "welch_t": round(t, 2), "p_welch": round(p, 4), "p_perm": round(perm_p(a, b), 4)}


def main():
    p_path, m_path = build_inputs()
    A.EVENT_REGISTRY, A.MARKET_DATA = p_path, m_path
    ev, md = A.load()

    # ---------- event-level results for every registered pair (same code) ----------
    df = A.run_all(ev[ev["exploratory"] == 0] if "exploratory" in ev else ev, md, confirmatory_only=False)
    df["cell"] = df.apply(A.cell_of, axis=1)
    dev = A.aggregate_by_event(df[df["window_days"] == W])
    dev.to_csv(os.path.join(OUT, "d24_event_results_3d.csv"), index=False)

    # ---------- involved teams, CONSISTENT estimand ----------
    rows = []
    for eid, tk, role in INVOLVED:
        er = ev[ev["event_id"] == eid]
        if er.empty:
            continue
        e = er.iloc[0].copy()
        e["market_ticker"], e["market_kind"] = tk, "sports_future"
        r = A.analyze_pair(e, md, W)
        abn = 100 * r["abnormal_move"] if r else np.nan
        rule = r["baseline_rule"] if r else "excluded"
        if pd.isna(abn):
            # Floor-pinned contract: bid 0 / ask <=1c across baseline+window, so
            # the pipeline midpoint (needs bid>0) falls back to a missing last
            # trade. The contract demonstrably did not move: record 0.0, flagged
            # (matches the legacy D17 treatment of Memphis).
            t0 = A.parse_iso_utc(A.first_report(e))
            px = md[(md["ticker"] == tk) & (md["ts"] >= t0 - pd.Timedelta(days=30)) &
                    (md["ts"] <= t0 + pd.Timedelta(days=W))]
            ask = pd.to_numeric(px["ask"], errors="coerce")
            if len(px) and (ask <= 0.01).all():
                abn, rule = 0.0, "floor_pinned"
        rows.append({"event_id": eid, "ticker": tk, "role": role,
                     "abn_cents": round(abn, 2) if pd.notna(abn) else np.nan,
                     "n_base": r["n_base"] if r else np.nan,
                     "baseline_rule": rule,
                     "contaminated": eid in CONTAMINATED,
                     "d24_added": eid in D24_EVENTS, "in_season": eid in INSEASON})
    inv = pd.DataFrame(rows)
    inv.to_csv(os.path.join(OUT, "d24_involved_teams_consistent_3d.csv"), index=False)

    legacy = pd.read_csv(os.path.join(OUT, "involved_teams_3d.csv"))

    def get_side(frame, events=None, col="abn_cents"):
        g = frame[(frame["role"].isin(["get", "keep"])) & (~frame["contaminated"])]
        if events is not None:
            g = g[g["event_id"].isin(events)]
        return g[col].dropna().values / 100.0

    summer_get = set(legacy[(legacy.role.isin(["get", "keep"])) & (~legacy.contaminated)].event_id)
    macro = dev[dev["cell"] == "unsched_macro"].set_index("event_id")["abn_event"]
    macro_summer = macro[[e for e in macro.index if e not in D24_EVENTS]]
    macro_nosep16 = macro_summer.drop([e for e in SEP16_UNSCHED if e in macro_summer.index])
    sep16_mean = macro_summer[[e for e in SEP16_UNSCHED if e in macro_summer.index]].mean()
    macro_collapsed = pd.concat([macro_nosep16, pd.Series({"sep16_cluster": sep16_mean})])
    macro_all = macro.drop([e for e in SEP16_UNSCHED if e in macro.index])

    res = []
    # A. reproduce the paper's D18 headline (legacy sports estimand)
    res.append(contrast("A_D18_as_published (legacy sports estimand)",
                        get_side(legacy), macro_summer.values, "sports involved (legacy)", "unsched macro"))
    # B. like-for-like estimand, summer sample
    sg = get_side(inv, summer_get)
    res.append(contrast("B_consistent_estimand", sg, macro_summer.values,
                        "sports involved (consistent)", "unsched macro"))
    res.append(contrast("B2_consistent + Sep16 collapsed", sg, macro_collapsed.values,
                        "sports involved (consistent)", "unsched macro, Sep16=1 obs"))
    res.append(contrast("B3_consistent + Sep16 dropped", sg, macro_nosep16.values,
                        "sports involved (consistent)", "unsched macro, no Sep16"))
    # C. D24 extended sample
    sg_all = get_side(inv)
    sg_off = get_side(inv, set(inv.event_id) - INSEASON)
    res.append(contrast("C_D24 extended, Sep16 dropped", sg_all, macro_all.values,
                        "sports involved, all", "unsched macro, no Sep16"))
    res.append(contrast("C2_D24 extended, offseason sports only, Sep16 dropped", sg_off, macro_all.values,
                        "sports involved, offseason", "unsched macro, no Sep16"))
    # D. absolute-move versions (direction of a macro threshold move is arbitrary)
    res.append(contrast("D_abs: consistent, Sep16 dropped (|move|)", np.abs(sg), np.abs(macro_nosep16.values),
                        "|sports involved|", "|unsched macro|"))
    res.append(contrast("D2_abs: D24 extended, Sep16 dropped (|move|)", np.abs(sg_all), np.abs(macro_all.values),
                        "|sports involved|", "|unsched macro|"))

    # E. H1a scheduled vs unscheduled macro (confirmatory window = Aug 14 -> cutoff)
    sched = dev[dev["cell"] == "sched_macro"].set_index("event_id")["abn_event"]
    sched_conf = sched[[e for e in sched.index if not e.endswith("_supp")]]
    res.append(contrast("E_H1a in-protocol (Aug14->Nov24), Sep16 dropped", macro_all.values, sched_conf.values,
                        "unsched macro", "sched macro (prereg window)"))
    res.append(contrast("E2_H1a |move|, in-protocol, Sep16 dropped", np.abs(macro_all.values), np.abs(sched_conf.values),
                        "|unsched macro|", "|sched macro|"))
    res.append(contrast("E3_H1a with Jan-Sep supp, Sep16 dropped", macro_all.values, sched.values,
                        "unsched macro", "sched macro incl. supp"))
    # F. H1b scheduled vs unscheduled sports (event level, all-teams avg = prereg estimand)
    ss = dev[dev["cell"] == "sched_sports"]["abn_event"].values
    us = dev[(dev["cell"] == "unsched_sports") & (~dev["event_id"].isin(CONTAMINATED))]["abn_event"].values
    res.append(contrast("F_H1b prereg estimand (all-teams avg)", us, ss, "unsched sports", "sched sports"))
    # G. H1d scheduled sports vs scheduled macro
    res.append(contrast("G_H1d prereg estimand", ss, sched_conf.values, "sched sports", "sched macro (prereg window)"))

    out = pd.DataFrame(res)
    out.to_csv(os.path.join(OUT, "d24_contrasts.csv"), index=False)

    # H2 macro -> sports for every macro event with a sports basket
    h2 = dev[dev["cell"] == "cross_macro_on_sports"]
    h2.to_csv(os.path.join(OUT, "d24_h2_macro_on_sports.csv"), index=False)

    pd.set_option("display.width", 250, "display.max_columns", 30)
    print("\n=== involved teams, consistent vs legacy estimand ===")
    cmp = inv.merge(legacy[["event_id", "ticker", "abn_cents"]], on=["event_id", "ticker"],
                    how="left", suffixes=("", "_legacy"))
    print(cmp.to_string(index=False))
    print("\n=== unscheduled macro event moves (c) ===")
    print((100 * macro).round(2).to_string())
    print("\n=== scheduled macro event moves (c) ===")
    print((100 * sched).round(2).to_string())
    print("\n=== scheduled / unscheduled sports event-level (c) ===")
    print((100 * dev[dev.cell.isin(["sched_sports", "unsched_sports"])].set_index("event_id")["abn_event"]).round(2).to_string())
    print("\n=== H2 macro->sports (c) ===")
    print((100 * h2.set_index("event_id")["abn_event"]).round(2).to_string())
    if len(h2) >= 2:
        x = h2["abn_event"].values
        print("  mean %.2fc, t-test vs 0 p=%.4f, n=%d" % (100 * x.mean(), stats.ttest_1samp(x, 0).pvalue, len(x)))
    print("\n=== CONTRASTS ===")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
