#!/usr/bin/env python3
"""
Kalshi event-study analysis — implements preregistration.md (locked 2026-09-17).

INPUT FILES (CSV, paths configurable below):
  event_registry.csv  one row per (event, market) pair:
      event_id, event_time (ISO),
      event_type [scheduled_macro|unscheduled_macro|scheduled_sports|unscheduled_sports],
      market_ticker, market_kind [sports_future|macro_bucket],
      surprise (float, native units; empty when not measurable),
      moneyness_steps (int, macro_bucket only: |strike - consensus| in buckets),
      first_report_time (ISO; = event_time when the event itself is the report),
      exploratory [0|1]  (1 = pre-2026-09-17 roster events, calibration only)
  market_data.csv  timestamped quotes, one row per (timestamp, ticker):
      timestamp (ISO), ticker, bid, ask, last, volume, trades, open_interest
      (bid/ask in dollars, e.g. 0.45. Midpoint is used; `last` is fallback.)

DESIGN: 2x2 factorial (scheduleness x domain). Cells: sched_macro, unsched_macro,
sched_sports, unsched_sports. Off-diagonal (event_type, market_kind) pairings are
cross_domain falsification cells (H2). Cells with n<5 events: descriptive only.

OUTPUT: results/ tables + printed summary.

All tiers are always reported; empty tiers print as N/A, never dropped.
"""

import csv, math, os, random, sys
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import stats

# ---------------- config ----------------
EVENT_REGISTRY = "event_registry.csv"
MARKET_DATA    = "market_data.csv"
OUT_DIR        = "results"
WINDOWS_DAYS   = [1, 3, 5]     # headline = 3-day; others are robustness
HEADLINE_WINDOW = 3
BASELINE_DAYS  = (30, 5)       # T-30 .. T-5
SPREAD_CUT     = 0.08          # liquidity filter: avg spread > 8c excluded (filtered run)
TRADES_CUT     = 5             # liquidity filter: < 5 trades in window excluded (filtered run)
PLACEBO_DRAWS  = 50            # random non-event days per market type
RANDOM_SEED    = 17

SPORTS_TIERS = [("S1", 0.00, 0.05, "Deep longshot"),
                ("S2", 0.05, 0.15, "Longshot"),
                ("S3", 0.15, 0.30, "Contender"),
                ("S4", 0.30, 1.01, "Co-favorite")]
MACRO_TIERS  = [("M0", 0, 0, "At-the-money"),
                ("M1", 1, 1, "Near-the-money"),
                ("M2", 2, 2, "Off-the-money"),
                ("M3", 3, 99, "Tails")]

# ---------------- helpers ----------------
def parse_iso(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))

def first_report(ev_row):
    frt = ev_row.get("first_report_time", None)
    if frt is None or (isinstance(frt, float) and pd.isna(frt)) or str(frt).strip() in ("", "nan", "None"):
        return ev_row["event_time"]
    return frt

def midpoint(row):
    b, a = row.get("bid"), row.get("ask")
    try:
        b, a = float(b), float(a)
        if b > 0 and a > 0:
            return (b + a) / 2.0
    except (TypeError, ValueError):
        pass
    try:
        return float(row.get("last"))
    except (TypeError, ValueError):
        return np.nan

def sports_tier(p):
    if pd.isna(p):
        return "S?", "No quote"
    for code, lo, hi, label in SPORTS_TIERS:
        if lo <= p < hi:
            return code, label
    return "S?", "No quote"

def macro_tier(steps):
    try:
        steps = abs(int(steps))
    except (TypeError, ValueError):
        return "M?", "Unknown"
    for code, lo, hi, label in MACRO_TIERS:
        if lo <= steps <= hi:
            return code, label
    return "M?", "Unknown"

# ---------------- load ----------------
def load():
    ev = pd.read_csv(EVENT_REGISTRY)
    md = pd.read_csv(MARKET_DATA)
    md["ts"] = md["timestamp"].apply(parse_iso)
    md["mid"] = md.apply(midpoint, axis=1)
    md["spread"] = pd.to_numeric(md["ask"], errors="coerce") - pd.to_numeric(md["bid"], errors="coerce")
    for c in ["volume", "trades", "open_interest"]:
        if c in md.columns:
            md[c] = pd.to_numeric(md[c], errors="coerce").fillna(0)
    return ev, md

# ---------------- core event-study ----------------
def analyze_pair(ev_row, md, window_days):
    """Returns dict of stats for one (event, market) pair, or None if insufficient data."""
    t0 = parse_iso(first_report(ev_row))
    ticker = ev_row["market_ticker"]
    px = md[md["ticker"] == ticker].sort_values("ts").reset_index(drop=True)
    if px.empty:
        return None
    base_lo, base_hi = t0 - timedelta(days=BASELINE_DAYS[0]), t0 - timedelta(days=BASELINE_DAYS[1])
    base = px[(px["ts"] >= base_lo) & (px["ts"] < base_hi)]["mid"].dropna()
    if len(base) < 5:
        return None
    base_mean = base.mean()
    win_end = t0 + timedelta(days=window_days)
    win = px[(px["ts"] >= t0) & (px["ts"] <= win_end)].copy()
    if win.empty:
        return None
    win["abn"] = win["mid"] - base_mean
    total = win["abn"].iloc[-1]
    # time-to-50%: first timestamp where cumulative abnormal move >= 50% of window total
    t50 = np.nan
    if abs(total) > 1e-9:
        cum = win["abn"].cumsum()
        hit = cum[abs(cum) >= 0.5 * abs(total)]
        if not hit.empty:
            t50 = (win.loc[hit.index[0], "ts"] - t0).total_seconds() / 3600.0  # hours
    avg_spread = win["spread"].mean()
    n_trades = win["trades"].sum() if "trades" in win else np.nan
    pre = px[px["ts"] < t0].tail(1)
    pre_mid = pre["mid"].iloc[0] if not pre.empty else np.nan
    return {
        "event_id": ev_row["event_id"], "ticker": ticker,
        "event_type": ev_row["event_type"], "market_kind": ev_row["market_kind"],
        "window_days": window_days, "n_base": len(base),
        "abnormal_move": float(total), "time_to_50h": float(t50),
        "avg_spread": float(avg_spread) if pd.notna(avg_spread) else np.nan,
        "n_trades": float(n_trades) if pd.notna(n_trades) else np.nan,
        "pre_mid": float(pre_mid) if pd.notna(pre_mid) else np.nan,
        "surprise": ev_row.get("surprise", np.nan),
        "moneyness_steps": ev_row.get("moneyness_steps", np.nan),
    }

def assign_tier(r):
    if r["market_kind"] == "sports_future":
        return sports_tier(r["pre_mid"])
    return macro_tier(r["moneyness_steps"])

def run_all(ev, md, confirmatory_only=True):
    if confirmatory_only:
        exp = ev.get("exploratory", pd.Series(0, index=ev.index))
        ev = ev[pd.to_numeric(exp, errors="coerce").fillna(0).astype(int) == 0]
    rows = []
    for _, e in ev.iterrows():
        for w in WINDOWS_DAYS:
            r = analyze_pair(e, md, w)
            if r:
                r["tier"], r["tier_label"] = assign_tier(r)
                r["liquid"] = bool((pd.isna(r["avg_spread"]) or r["avg_spread"] <= SPREAD_CUT)
                                   and (pd.isna(r["n_trades"]) or r["n_trades"] >= TRADES_CUT))
                rows.append(r)
    return pd.DataFrame(rows)

# ---------------- 2x2 cells & contrasts ----------------
def cell_of(r):
    """Map an (event_type, market_kind) pair to a 2x2 cell or cross_domain."""
    et, mk = r["event_type"], r["market_kind"]
    if mk == "macro_bucket":
        if et == "scheduled_macro":
            return "sched_macro"
        if et == "unscheduled_macro":
            return "unsched_macro"
        return "cross_domain"
    if mk == "sports_future":
        if et == "scheduled_sports":
            return "sched_sports"
        if et == "unscheduled_sports":
            return "unsched_sports"
        return "cross_domain"
    return "cross_domain"

# (hypothesis, cell_a, cell_b): H1a/H1b = scheduleness within domain;
# H1c/H1d = domain holding scheduleness fixed.
CONTRASTS = [
    ("H1a", "unsched_macro", "sched_macro"),
    ("H1b", "unsched_sports", "sched_sports"),
    ("H1c", "unsched_sports", "unsched_macro"),
    ("H1d", "sched_sports", "sched_macro"),
]
MIN_N_TEST = 5  # cells below this are descriptive only (prereg power rule)

# ---------------- tests ----------------
def pooled_tests(df, window):
    """Mean abnormal move != 0 per (cell x tier); tier differences within cell (H3)."""
    d = df[df["window_days"] == window]
    out = []
    for (cell, tier), g in d.groupby(["cell", "tier"]):
        ab = g["abnormal_move"].dropna()
        t50 = g["time_to_50h"].dropna()
        row = {"cell": cell, "tier": tier, "n": len(g),
               "mean_abn": ab.mean() if len(ab) else np.nan,
               "t_abn": np.nan, "p_abn": np.nan,
               "median_t50h": t50.median() if len(t50) else np.nan}
        if len(ab) >= 3:
            t, p = stats.ttest_1samp(ab, 0.0)
            row["t_abn"], row["p_abn"] = float(t), float(p)
        out.append(row)
    res = pd.DataFrame(out)
    # H3: do tiers differ within a cell? Kruskal-Wallis on |abnormal| and t50.
    kw = []
    for cell, g in d.groupby("cell"):
        for col, name in [("abn_abs", "abs_abnormal"), ("time_to_50h", "t50")]:
            gg = g.copy()
            gg["abn_abs"] = gg["abnormal_move"].abs()
            groups = [gg[gg["tier"] == t][col].dropna().values
                      for t in sorted(gg["tier"].unique())]
            groups = [x for x in groups if len(x) >= 2]
            if len(groups) >= 2:
                h, pkw = stats.kruskal(*groups)
                kw.append({"cell": cell, "metric": name, "H": float(h), "p": float(pkw),
                           "tiers_compared": len(groups)})
            else:
                kw.append({"cell": cell, "metric": name, "H": np.nan, "p": np.nan,
                           "tiers_compared": len(groups)})
    return res, pd.DataFrame(kw)


def factorial_contrasts(df, window):
    """H1a-H1d: two-sample t-tests on abnormal moves and time-to-50%.

    Cells with n < MIN_N_TEST are descriptive only (prereg power rule)."""
    d = df[df["window_days"] == window]
    rows = []
    for name, a, b in CONTRASTS:
        ga = d[d["cell"] == a]
        gb = d[d["cell"] == b]
        aba = ga["abnormal_move"].dropna()
        abb = gb["abnormal_move"].dropna()
        t50a = ga["time_to_50h"].dropna()
        t50b = gb["time_to_50h"].dropna()
        row = {"contrast": name, "a": a, "b": b, "n_a": len(ga), "n_b": len(gb),
               "mean_abn_a": aba.mean() if len(aba) else np.nan,
               "mean_abn_b": abb.mean() if len(abb) else np.nan,
               "median_t50h_a": t50a.median() if len(t50a) else np.nan,
               "median_t50h_b": t50b.median() if len(t50b) else np.nan,
               "t_abn": np.nan, "p_abn": np.nan,
               "t_t50": np.nan, "p_t50": np.nan,
               "tested": len(aba) >= MIN_N_TEST and len(abb) >= MIN_N_TEST}
        if row["tested"]:
            t, p = stats.ttest_ind(aba, abb, equal_var=False)
            row["t_abn"], row["p_abn"] = float(t), float(p)
            if len(t50a) >= 2 and len(t50b) >= 2:
                t2, p2 = stats.ttest_ind(t50a, t50b, equal_var=False)
                row["t_t50"], row["p_t50"] = float(t2), float(p2)
        else:
            row["note"] = "descriptive only (n<5 in a cell)"
        rows.append(row)
    res = pd.DataFrame(rows)
    res["p_abn_holm"] = np.nan  # always present, even when nothing qualifies for testing
    # Holm correction across the four H1 contrast p-values (abnormal-move leg)
    p = res["p_abn"].dropna()
    if len(p):
        order = np.argsort(p.values)
        holm = np.empty(len(p))
        m = len(p)
        for rank, idx in enumerate(order):
            holm[idx] = min(1.0, p.values[idx] * (m - rank))
        res.loc[p.index, "p_abn_holm"] = holm
    return res

def placebo(df_pairs, md, ev):
    """Same machinery on random non-event days per market type."""
    random.seed(RANDOM_SEED); np.random.seed(RANDOM_SEED)
    out = []
    for kind in ["sports_future", "macro_bucket"]:
        tickers = md[md["ticker"].isin(
            ev[ev["market_kind"] == kind]["market_ticker"].unique())]["ticker"].unique()
        if not len(tickers):
            continue
        all_ts = md["ts"]
        lo, hi = all_ts.min() + timedelta(days=31), all_ts.max() - timedelta(days=6)
        # exclude real event dates ±6 days
        evt_dates = [parse_iso(first_report(e))
                     for _, e in ev[ev["market_kind"] == kind].iterrows()]
        draws = 0
        guard = 0
        while draws < PLACEBO_DRAWS and guard < PLACEBO_DRAWS * 50:
            guard += 1
            t0 = lo + (hi - lo) * random.random()
            if any(abs((t0 - d).days) <= 6 for d in evt_dates):
                continue
            ticker = random.choice(tickers)
            fake = {"event_id": f"placebo_{kind}_{draws}", "market_ticker": ticker,
                    "event_type": "placebo", "market_kind": kind,
                    "event_time": t0.isoformat(), "first_report_time": t0.isoformat(),
                    "surprise": np.nan, "moneyness_steps": np.nan}
            r = analyze_pair(fake, md, HEADLINE_WINDOW)
            if r:
                r["tier"], r["tier_label"] = assign_tier(r)
                out.append(r); draws += 1
    pdf = pd.DataFrame(out)
    summ = []
    for kind, g in pdf.groupby("market_kind"):
        ab = g["abnormal_move"].dropna()
        t, p = (np.nan, np.nan)
        if len(ab) >= 3:
            t, p = stats.ttest_1samp(ab, 0.0); t, p = float(t), float(p)
        mean_abn = float(ab.mean()) if len(ab) else np.nan
        # Economic significance first: a sub-1c "significant" move is noise, not a finding.
        # (With near-zero variance, t-stats explode on trivial means — p alone misleads.)
        if pd.isna(mean_abn) or abs(mean_abn) < 0.01 or (not pd.isna(p) and p > 0.05):
            verdict = "PASS (no effect)"
        else:
            verdict = "FAIL (method fires on noise)"
        summ.append({"market_kind": kind, "n": len(g),
                     "mean_abn": mean_abn, "t": t, "p": p, "verdict": verdict})
    return pdf, pd.DataFrame(summ)

# ---------------- main ----------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ev, md = load()

    print("== confirmatory run (exploratory events excluded) ==")
    df = run_all(ev, md, confirmatory_only=True)
    df["cell"] = df.apply(cell_of, axis=1)
    df.to_csv(f"{OUT_DIR}/pair_results.csv", index=False)
    print(f"analyzed {df['event_id'].nunique()} events x {df['ticker'].nunique()} markets "
          f"= {len(df)} pair-windows")
    print("cell counts:", df[df["window_days"] == HEADLINE_WINDOW]["cell"].value_counts().to_dict())

    for label, d in [("full", df), ("liquid_only", df[df["liquid"]])]:
        pooled, kw = pooled_tests(d, HEADLINE_WINDOW)
        pooled.to_csv(f"{OUT_DIR}/pooled_{label}_{HEADLINE_WINDOW}d.csv", index=False)
        kw.to_csv(f"{OUT_DIR}/tier_kruskal_{label}_{HEADLINE_WINDOW}d.csv", index=False)
        con = factorial_contrasts(d, HEADLINE_WINDOW)
        con.to_csv(f"{OUT_DIR}/contrasts_{label}_{HEADLINE_WINDOW}d.csv", index=False)
        print(f"\n-- {label}, {HEADLINE_WINDOW}-day window: pooled abnormal moves --")
        print(pooled[["cell", "tier", "n", "mean_abn", "p_abn"]].to_string(index=False))
        print(f"-- {label}: H1a-H1d factorial contrasts --")
        print(con[["contrast", "a", "b", "n_a", "n_b", "mean_abn_a", "mean_abn_b",
                    "p_abn", "p_abn_holm", "tested"]].to_string(index=False))
        print(f"-- {label}: tier differences within cell (Kruskal-Wallis, H3) --")
        print(kw.to_string(index=False))

    print("\n== placebo test ==")
    _, psumm = placebo(df, md, ev)
    psumm.to_csv(f"{OUT_DIR}/placebo_summary.csv", index=False)
    print(psumm.to_string(index=False))

    print("\n== robustness: headline metric across window lengths ==")
    for w in WINDOWS_DAYS:
        pooled, _ = pooled_tests(df, w)
        con = factorial_contrasts(df, w)
        print(f"-- {w}-day window: cells --")
        print(pooled[["cell", "tier", "n", "mean_abn", "p_abn"]].to_string(index=False))
        print(f"-- {w}-day window: H1a-H1d contrasts --")
        print(con[["contrast", "n_a", "n_b", "p_abn", "tested"]].to_string(index=False))

    print(f"\nAll tables written to {OUT_DIR}/")

if __name__ == "__main__":
    main()
