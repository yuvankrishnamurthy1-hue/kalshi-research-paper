#!/usr/bin/env python3
"""
Kalshi event-study analysis — FIXED version.

Implements preregistration.md (locked 2026-09-21). See
hidden_files/analysis_fixes_summary.md for the full list of fixes vs.
analyze_kalshi.py. Headline changes:

  FIX 1:  time-to-50% = first timestamp where the abnormal PRICE (mid - baseline)
          reaches 50% of the eventual directional move (abnormal move at end of
          window), same sign. The old code cumulated abnormal deviations, which
          degenerates (e.g. a flat post-event price gives t50 ~= 0 always).
  FIX 2:  the n>=5 power rule counts UNIQUE EVENTS per cell, not event-market rows.
  FIX 3:  contracts on the same event are correlated -> primary unit of analysis
          is the EVENT (mean abnormal move across its contracts); tests run on
          event-level observations.
  FIX 4:  both absolute-cent and log-odds movement reported.
  FIX 5:  H2 cross-domain cells split explicitly into macro-on-sports and
          sports-on-macro, each tested against zero with CIs.
  FIX 7:  baseline fallback: if <MIN_BASELINE_N obs in T-30..T-5, retry T-45..T-5;
          if still insufficient, the pair is excluded and logged (exclusions.csv).
  FIX 8:  placebos matched on weekday, ticker-frequency, and event regime (+/-30d
          around real events); contamination exclusion +/-6d kept.
  FIX 9/13: field-availability checks for trades/spread with explicit fallbacks.
  FIX 10: volume summed (flow), open-interest differenced (stock); both vs baseline.
  FIX 11: all timestamps normalized to tz-aware UTC; raw source string preserved.
  FIX 12: Holm correction applied to BOTH the movement and the speed legs of H1a-H1d.

INPUT FILES (CSV, overridable via KALSHI_EVENT_REGISTRY / KALSHI_MARKET_DATA env vars):
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
sched_sports, unsched_sports. Off-diagonal pairings are H2 falsification cells.
Cells with <5 UNIQUE EVENTS: descriptive only.

OUTPUT: results/ tables + printed summary.
All tiers are always reported; empty tiers print as N/A, never dropped.
"""

import csv, math, os, random, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from scipy import stats

# ---------------- config ----------------
EVENT_REGISTRY = os.environ.get("KALSHI_EVENT_REGISTRY", "event_registry.csv")
MARKET_DATA    = os.environ.get("KALSHI_MARKET_DATA", "market_data.csv")
OUT_DIR        = os.environ.get("KALSHI_OUT_DIR", "results")
WINDOWS_DAYS   = [1, 3, 5]     # headline = 3-day; others are robustness
HEADLINE_WINDOW = 3
BASELINE_DAYS  = (30, 5)       # T-30 .. T-5
BASELINE_FALLBACK_DAYS = (45, 5)  # FIX 7: fallback window when T-30..T-5 is thin
MIN_BASELINE_N = 5            # minimum baseline observations (else excluded)
SPREAD_CUT     = 0.08          # liquidity filter: avg spread > 8c excluded (filtered run)
TRADES_CUT     = 5             # liquidity filter: < 5 trades in window excluded (filtered run)
PLACEBO_DRAWS  = 50            # random non-event days per market type
PLACEBO_REGIME_DAYS = 30      # FIX 8: placebo dates within +/-30d of a real event date
RANDOM_SEED    = 17
LOGODDS_CLIP   = 1e-6         # FIX 4: clip prices away from 0/1 for log-odds

SPORTS_TIERS = [("S1", 0.00, 0.05, "Deep longshot"),
                ("S2", 0.05, 0.15, "Longshot"),
                ("S3", 0.15, 0.30, "Contender"),
                ("S4", 0.30, 1.01, "Co-favorite")]
MACRO_TIERS  = [("M0", 0, 0, "At-the-money"),
                ("M1", 1, 1, "Near-the-money"),
                ("M2", 2, 2, "Off-the-money"),
                ("M3", 3, 99, "Tails")]

# FIX 7: exclusion log — every dropped (event, market, window) pair with a reason.
EXCLUSIONS = []
# FIX 9/13: populated by check_fields().
TRADES_AVAILABLE = False
SPREAD_AVAILABLE = False


# ---------------- helpers ----------------
def parse_iso_utc(s):
    """FIX 11: parse any ISO timestamp -> tz-aware UTC datetime.

    Naive inputs are assumed UTC and flagged (returned separately by callers
    via the raw string, which is always preserved in a `ts_raw` column).
    """
    dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # assume UTC; source kept in ts_raw
    return dt.astimezone(timezone.utc)


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


def logodds(p):
    """FIX 4: log-odds transform, clipped away from 0/1."""
    p = min(max(float(p), LOGODDS_CLIP), 1.0 - LOGODDS_CLIP)
    return math.log(p / (1.0 - p))


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


def holm_correct(pvals):
    """Holm step-down correction; returns array aligned with input (nan-safe).

    NaNs (untested contrasts) are ignored and stay NaN in the output.
    """
    p = np.asarray(pvals, dtype=float)
    out = np.full_like(p, np.nan)
    valid = ~np.isnan(p)
    vals = p[valid]
    if vals.size == 0:
        return out
    order = np.argsort(vals, kind="stable")   # ascending p-value
    m = len(vals)
    adj_sorted = np.minimum(1.0, vals[order] * (m - np.arange(m)))
    adj_sorted = np.maximum.accumulate(adj_sorted)  # step-down monotonicity
    adj = np.empty(m)
    adj[order] = adj_sorted                    # map back to input order
    out[valid] = adj
    return out


# ---------------- load ----------------
def check_fields(md):
    """FIX 9/13: confirm trade-count and spread availability separately from volume."""
    global TRADES_AVAILABLE, SPREAD_AVAILABLE
    TRADES_AVAILABLE = (
        "trades" in md.columns
        and md["trades"].notna().sum() > 0
        and (md["trades"] > 0).sum() > 0
    )
    SPREAD_AVAILABLE = (
        "spread" in md.columns and md["spread"].notna().sum() > 0
    )
    print(f"  field check: trades_available={TRADES_AVAILABLE}, "
          f"spread_available={SPREAD_AVAILABLE}, "
          f"volume_rows={(md['volume'] > 0).sum() if 'volume' in md.columns else 0}")
    if not TRADES_AVAILABLE:
        print("  WARNING: no usable trade counts — liquidity filter falls back to "
              "spread only, and 'n_trades' is reported as NaN (not zero).")
    if not SPREAD_AVAILABLE:
        print("  WARNING: no usable bid/ask spread — spread filter cannot be applied; "
              "all pairs marked liquid=True on spread leg.")


def verify_macro_buckets(ev):
    """FIX 6: verify macro-bucket registry assumptions before analysis.

    Kalshi bucket markets (KXFED/KXCPI/KXCPICORE) list mutually exclusive buckets
    by construction, so moneyness tiers M0..M3 are mutually exclusive *provided*
    the registry maps each row to exactly one bucket. This check enforces that
    the registry has a moneyness_steps value for every macro pair; the deeper
    consensus-mapping audit belongs to the registry build (documented here so it
    is not silently assumed).
    """
    macro = ev[ev["market_kind"] == "macro_bucket"]
    missing = macro[pd.to_numeric(macro.get("moneyness_steps",
                                            pd.Series(np.nan, index=macro.index)),
                                  errors="coerce").isna()]
    if len(missing):
        print(f"  WARNING (FIX 6): {len(missing)} macro pairs lack moneyness_steps; "
              f"they get tier 'M?' and are excluded from tier tests.")
    else:
        print(f"  macro bucket check: all {len(missing) if len(macro)==0 else len(macro)} "
              f"macro pairs have moneyness_steps; tiers M0..M3 treated as mutually "
              f"exclusive per Kalshi bucket-market construction.")


def load():
    ev = pd.read_csv(EVENT_REGISTRY)
    md = pd.read_csv(MARKET_DATA)
    md["ts_raw"] = md["timestamp"].astype(str)          # FIX 11: preserve source
    md["ts"] = md["timestamp"].apply(parse_iso_utc)     # FIX 11: tz-aware UTC
    md["mid"] = md.apply(midpoint, axis=1)
    md["spread"] = pd.to_numeric(md["ask"], errors="coerce") - pd.to_numeric(md["bid"], errors="coerce")
    for c in ["volume", "trades", "open_interest"]:
        if c in md.columns:
            md[c] = pd.to_numeric(md[c], errors="coerce")
    check_fields(md)   # FIX 9/13
    return ev, md


# ---------------- core event-study ----------------
def baseline_slice(px, t0, lo_days, hi_days):
    base_lo = t0 - timedelta(days=lo_days)
    base_hi = t0 - timedelta(days=hi_days)
    return px[(px["ts"] >= base_lo) & (px["ts"] < base_hi)]


def analyze_pair(ev_row, md, window_days):
    """Returns dict of stats for one (event, market) pair, or None if excluded.

    Exclusions are appended to EXCLUSIONS with a reason (FIX 7).
    """
    t0 = parse_iso_utc(first_report(ev_row))
    ticker = ev_row["market_ticker"]
    eid = ev_row["event_id"]

    def exclude(reason):
        EXCLUSIONS.append({"event_id": eid, "ticker": ticker,
                           "window_days": window_days, "reason": reason})
        return None

    px = md[md["ticker"] == ticker].sort_values("ts").reset_index(drop=True)
    if px.empty:
        return exclude("no_market_data")

    # FIX 7: baseline with fallback. Primary T-30..T-5; if too thin, retry T-45..T-5.
    base = baseline_slice(px, t0, *BASELINE_DAYS)["mid"].dropna()
    fallback = False
    if len(base) < MIN_BASELINE_N:
        base = baseline_slice(px, t0, *BASELINE_FALLBACK_DAYS)["mid"].dropna()
        fallback = True
    if len(base) < MIN_BASELINE_N:
        return exclude("insufficient_baseline_history")
    base_mean = base.mean()

    win_end = t0 + timedelta(days=window_days)
    win = px[(px["ts"] >= t0) & (px["ts"] <= win_end)].copy()
    if win.empty:
        return exclude("no_window_data")
    win["abn"] = win["mid"] - base_mean

    # FIX 1: time-to-50% = first timestamp where the abnormal PRICE reaches 50%
    # of the eventual directional move (abnormal move at end of window), in the
    # same direction. (Old code cumulated deviations, which degenerates: a flat
    # post-event price level hits 50% of the cumulative sum almost immediately.)
    total = win["abn"].iloc[-1]          # eventual directional move (absolute cents)
    t50 = np.nan
    if abs(total) > 1e-9:
        direction = np.sign(total)
        reached = (win["abn"] * direction) >= (0.5 * abs(total))
        hits = reached[reached].index
        if len(hits):
            t50 = (win.loc[hits[0], "ts"] - t0).total_seconds() / 3600.0  # hours

    # FIX 4: scaled / log-odds movement alongside absolute cents.
    last_mid = win["mid"].iloc[-1]
    abn_logodds = (logodds(last_mid) - logodds(base_mean)
                   if pd.notna(last_mid) and pd.notna(base_mean) else np.nan)
    abn_scaled = (float(total) / base_mean
                  if pd.notna(base_mean) and abs(base_mean) > 1e-9 else np.nan)

    # FIX 10: candle volume is a per-period FLOW -> sum over window (vs baseline
    # daily mean); open interest is a STOCK -> difference over window.
    vol_win = win["volume"].sum() if "volume" in win else np.nan
    base_vol_daily = base_slice_vol(px, t0)
    oi_first = win["open_interest"].iloc[0] if "open_interest" in win else np.nan
    oi_last = win["open_interest"].iloc[-1] if "open_interest" in win else np.nan
    d_oi = (oi_last - oi_first
            if pd.notna(oi_first) and pd.notna(oi_last) else np.nan)

    avg_spread = win["spread"].mean()
    # FIX 9: report NaN (not 0) when trade counts are unavailable.
    n_trades = (win["trades"].sum() if TRADES_AVAILABLE and "trades" in win
                else np.nan)
    pre = px[px["ts"] < t0].tail(1)
    pre_mid = pre["mid"].iloc[0] if not pre.empty else np.nan
    return {
        "event_id": eid, "ticker": ticker,
        "event_type": ev_row["event_type"], "market_kind": ev_row["market_kind"],
        "window_days": window_days, "n_base": len(base),
        "baseline_fallback": bool(fallback),
        "abnormal_move": float(total),          # absolute movement (fraction of $1)
        "abn_logodds": float(abn_logodds),      # FIX 4: log-odds movement
        "abn_scaled": float(abn_scaled),        # FIX 4: move / baseline price
        "time_to_50h": float(t50),
        "avg_spread": float(avg_spread) if pd.notna(avg_spread) else np.nan,
        "n_trades": float(n_trades) if pd.notna(n_trades) else np.nan,
        "vol_window": float(vol_win) if pd.notna(vol_win) else np.nan,
        "vol_base_daily": float(base_vol_daily),
        "d_oi": float(d_oi) if pd.notna(d_oi) else np.nan,
        "pre_mid": float(pre_mid) if pd.notna(pre_mid) else np.nan,
        "surprise": ev_row.get("surprise", np.nan),
        "moneyness_steps": ev_row.get("moneyness_steps", np.nan),
    }


def base_slice_vol(px, t0):
    """Mean per-period volume over the primary baseline window (flow comparison)."""
    base = baseline_slice(px, t0, *BASELINE_DAYS)
    if "volume" not in base or base.empty:
        return np.nan
    return float(base["volume"].mean())


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
                # FIX 13: spread leg skipped when spread unavailable; trades leg
                # skipped (treated as pass) when trade counts unavailable.
                spread_ok = (pd.isna(r["avg_spread"]) or r["avg_spread"] <= SPREAD_CUT
                             or not SPREAD_AVAILABLE)
                trades_ok = (pd.isna(r["n_trades"]) or r["n_trades"] >= TRADES_CUT
                             or not TRADES_AVAILABLE)
                r["liquid"] = bool(spread_ok and trades_ok)
                rows.append(r)
    return pd.DataFrame(rows)


# ---------------- 2x2 cells & contrasts ----------------
def cell_of(r):
    """Map an (event_type, market_kind) pair to a 2x2 cell or a directed
    cross-domain cell (FIX 5: H2 needs macro-on-sports and sports-on-macro
    as separate falsification cells)."""
    et, mk = r["event_type"], r["market_kind"]
    if mk == "macro_bucket":
        if et == "scheduled_macro":
            return "sched_macro"
        if et == "unscheduled_macro":
            return "unsched_macro"
        if et in ("scheduled_sports", "unscheduled_sports"):
            return "cross_sports_on_macro"   # FIX 5
        return "cross_other"
    if mk == "sports_future":
        if et == "scheduled_sports":
            return "sched_sports"
        if et == "unscheduled_sports":
            return "unsched_sports"
        if et in ("scheduled_macro", "unscheduled_macro"):
            return "cross_macro_on_sports"   # FIX 5
        return "cross_other"
    return "cross_other"


# (hypothesis, cell_a, cell_b): H1a/H1b = scheduleness within domain;
# H1c/H1d = domain holding scheduleness fixed.
CONTRASTS = [
    ("H1a", "unsched_macro", "sched_macro"),
    ("H1b", "unsched_sports", "sched_sports"),
    ("H1c", "unsched_sports", "unsched_macro"),
    ("H1d", "sched_sports", "sched_macro"),
]
MIN_N_TEST = 5  # FIX 2: UNIQUE EVENTS below this -> descriptive only (prereg power rule)


def aggregate_by_event(df):
    """FIX 3: collapse correlated contracts to one observation per event x cell.

    Event abnormal move = mean across its contracts *within the same cell*;
    event time-to-50% = median across those contracts (nan-safe). Grouping is by
    (event_id, cell) because one event can contribute both on-domain pairs and
    cross-domain (H2) pairs, which must not be averaged together. Tier = modal
    pair tier (documented; an event whose contracts span tiers is assigned its
    most common tier).
    """
    rows = []
    for (eid, cell, w), g in df.groupby(["event_id", "cell", "window_days"]):
        ab = g["abnormal_move"].dropna()
        lo = g["abn_logodds"].dropna()
        t50 = g["time_to_50h"].dropna()
        mode = g["tier"].mode()
        rows.append({
            "event_id": eid,
            "cell": cell,
            "window_days": w,
            "event_type": g["event_type"].iloc[0],
            "market_kind": g["market_kind"].iloc[0],
            "n_pairs": len(g),
            "tier": mode.iloc[0] if len(mode) else "N/A",
            "abn_event": ab.mean() if len(ab) else np.nan,
            "abn_event_logodds": lo.mean() if len(lo) else np.nan,
            "t50_event": t50.median() if len(t50) else np.nan,
        })
    return pd.DataFrame(rows)


def ci95(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return (np.nan, np.nan)
    m, se = x.mean(), stats.sem(x)
    h = se * stats.t.ppf(0.975, len(x) - 1)
    return (m - h, m + h)


# ---------------- tests ----------------
def pooled_tests(df_pairs, window):
    """Mean abnormal move != 0 per (cell x tier), on EVENT-level observations
    (FIX 3). FIX 2: p-values only when n_unique_events >= MIN_N_TEST."""
    dev = aggregate_by_event(df_pairs[df_pairs["window_days"] == window])
    out = []
    for (cell, tier), g in dev.groupby(["cell", "tier"]):
        ab = g["abn_event"].dropna()
        lo = g["abn_event_logodds"].dropna()
        t50 = g["t50_event"].dropna()
        n_ev = g["event_id"].nunique()
        tested = n_ev >= MIN_N_TEST
        lo_ci, hi_ci = ci95(ab) if tested else (np.nan, np.nan)
        row = {"cell": cell, "tier": tier, "n_events": n_ev,
               "n_pairs": int(g["n_pairs"].sum()),
               "tested": tested,
               "mean_abn": ab.mean() if len(ab) else np.nan,
               "mean_abn_logodds": lo.mean() if len(lo) else np.nan,
               "ci95_lo": lo_ci, "ci95_hi": hi_ci,
               "t_abn": np.nan, "p_abn": np.nan,
               "median_t50h": t50.median() if len(t50) else np.nan}
        if tested and len(ab) >= 2:
            t, p = stats.ttest_1samp(ab, 0.0)
            row["t_abn"], row["p_abn"] = float(t), float(p)
        elif not tested:
            row["note"] = "descriptive only (n<5 unique events)"
        out.append(row)
    res = pd.DataFrame(out)

    # H3: do tiers differ within a cell? Kruskal-Wallis on event-level
    # |abnormal| and t50, using each event's modal tier (FIX 3).
    kw = []
    for cell, g in dev.groupby("cell"):
        gg = g.copy()
        gg["abn_abs"] = gg["abn_event"].abs()
        for col, name in [("abn_abs", "abs_abnormal"), ("t50_event", "t50")]:
            groups = [gg[gg["tier"] == t][col].dropna().values
                      for t in sorted(gg["tier"].unique())]
            groups = [x for x in groups if len(x) >= 2]
            if len(groups) >= 2:
                try:
                    h, pkw = stats.kruskal(*groups)
                except ValueError:
                    # identical values within groups (e.g. degenerate synthetic
                    # data) -> no detectable tier difference
                    h, pkw = np.nan, np.nan
                kw.append({"cell": cell, "metric": name,
                           "H": float(h) if pd.notna(h) else np.nan,
                           "p": float(pkw) if pd.notna(pkw) else np.nan,
                           "tiers_compared": len(groups),
                           "n_events": int(g["event_id"].nunique())})
            else:
                kw.append({"cell": cell, "metric": name, "H": np.nan, "p": np.nan,
                           "tiers_compared": len(groups),
                           "n_events": int(g["event_id"].nunique())})
    return res, pd.DataFrame(kw)


def factorial_contrasts(df_pairs, window):
    """H1a-H1d on EVENT-level observations (FIX 3).

    FIX 2: a contrast is tested only if BOTH cells have >= MIN_N_TEST unique
    events. FIX 12: Holm correction on both the movement and the speed legs.
    """
    dev = aggregate_by_event(df_pairs[df_pairs["window_days"] == window])
    rows = []
    for name, a, b in CONTRASTS:
        ga = dev[dev["cell"] == a]
        gb = dev[dev["cell"] == b]
        na, nb = ga["event_id"].nunique(), gb["event_id"].nunique()
        aba = ga["abn_event"].dropna()
        abb = gb["abn_event"].dropna()
        t50a = ga["t50_event"].dropna()
        t50b = gb["t50_event"].dropna()
        tested = na >= MIN_N_TEST and nb >= MIN_N_TEST   # FIX 2: unique events
        row = {"contrast": name, "a": a, "b": b,
               "n_a": int(na), "n_b": int(nb),
               "n_pairs_a": int(ga["n_pairs"].sum()), "n_pairs_b": int(gb["n_pairs"].sum()),
               "mean_abn_a": aba.mean() if len(aba) else np.nan,
               "mean_abn_b": abb.mean() if len(abb) else np.nan,
               "mean_logodds_a": ga["abn_event_logodds"].dropna().mean(),
               "mean_logodds_b": gb["abn_event_logodds"].dropna().mean(),
               "median_t50h_a": t50a.median() if len(t50a) else np.nan,
               "median_t50h_b": t50b.median() if len(t50b) else np.nan,
               "t_abn": np.nan, "p_abn": np.nan,
               "t_t50": np.nan, "p_t50": np.nan,
               "tested": tested}
        if tested:
            t, p = stats.ttest_ind(aba, abb, equal_var=False)
            row["t_abn"], row["p_abn"] = float(t), float(p)
            if len(t50a) >= 2 and len(t50b) >= 2:
                t2, p2 = stats.ttest_ind(t50a, t50b, equal_var=False)
                row["t_t50"], row["p_t50"] = float(t2), float(p2)
        else:
            row["note"] = "descriptive only (n<5 unique events in a cell)"
        rows.append(row)
    res = pd.DataFrame(rows)
    # FIX 12: Holm on BOTH legs, consistently.
    res["p_abn_holm"] = holm_correct(res["p_abn"].values)
    res["p_t50_holm"] = holm_correct(res["p_t50"].values)
    return res


def h2_cross_domain(df_pairs, window):
    """FIX 5: H2 falsification — macro news on sports markets and sports news on
    macro markets, each tested against zero (event-level). Prediction: failure
    to reject (report CIs, not just p-values)."""
    dev = aggregate_by_event(df_pairs[df_pairs["window_days"] == window])
    rows = []
    for cell, label in [("cross_macro_on_sports", "macro news -> sports markets"),
                        ("cross_sports_on_macro", "sports news -> macro markets")]:
        g = dev[dev["cell"] == cell]
        ab = g["abn_event"].dropna()
        n_ev = g["event_id"].nunique()
        tested = n_ev >= MIN_N_TEST
        lo_ci, hi_ci = ci95(ab) if tested and len(ab) >= 2 else (np.nan, np.nan)
        row = {"h2_cell": cell, "direction": label, "n_events": int(n_ev),
               "n_pairs": int(g["n_pairs"].sum()) if len(g) else 0,
               "tested": tested,
               "mean_abn": ab.mean() if len(ab) else np.nan,
               "mean_abn_logodds": g["abn_event_logodds"].dropna().mean(),
               "ci95_lo": lo_ci, "ci95_hi": hi_ci,
               "t": np.nan, "p": np.nan,
               "prediction": "indistinguishable from zero"}
        if tested and len(ab) >= 2:
            t, p = stats.ttest_1samp(ab, 0.0)
            row["t"], row["p"] = float(t), float(p)
        elif not tested:
            row["note"] = "descriptive only (n<5 unique events)"
        rows.append(row)
    return pd.DataFrame(rows)


def placebo(df_pairs, md, ev):
    """Same machinery on placebo days per market type.

    FIX 8: placebos are matched — (a) same ticker pool as the real registry
    (frequency-weighted, so market/maturity mix matches), (b) same weekday and
    time-of-day as a real event, (c) date within +/-30d of a real event date
    (market-regime match), (d) per-ticker contamination exclusion: no real event
    for the SAME ticker inside [t0-33d, t0+3d], i.e. the placebo's own baseline
    (T-30..T-5) and event window cannot overlap a real event. Tier is assigned
    with the same machinery and its mix is reported.
    """
    random.seed(RANDOM_SEED); np.random.seed(RANDOM_SEED)
    CONTAM_LO = BASELINE_DAYS[0] + 3   # 33d before: baseline must not touch a real event
    CONTAM_HI = HEADLINE_WINDOW        # 3d after: window must not touch a real event
    out = []
    for kind in ["sports_future", "macro_bucket"]:
        reg = ev[ev["market_kind"] == kind]
        if reg.empty:
            continue
        tickers = reg["market_ticker"].unique().tolist()
        # frequency weights: tickers appearing in more registry rows get drawn more
        counts = reg["market_ticker"].value_counts()
        weights = np.array([counts[t] for t in tickers], dtype=float)
        weights /= weights.sum()
        # per-ticker real event dates (for contamination checks)
        ticker_events = {t: [parse_iso_utc(first_report(e))
                             for _, e in reg[reg["market_ticker"] == t].iterrows()]
                         for t in tickers}
        anchors = [(t, d) for t in tickers for d in ticker_events[t]]
        # FIX 11: tz-aware bounds
        all_ts = md["ts"]
        lo = all_ts.min() + timedelta(days=BASELINE_FALLBACK_DAYS[0] + 1)
        hi = all_ts.max() - timedelta(days=HEADLINE_WINDOW + 1)
        if hi <= lo:
            continue
        draws, guard = 0, 0
        while draws < PLACEBO_DRAWS and guard < PLACEBO_DRAWS * 500:
            guard += 1
            ticker, anchor = random.choice(anchors)
            # FIX 8: same weekday/time as a real event, within +/-30d regime window
            delta_days = random.randint(-PLACEBO_REGIME_DAYS, PLACEBO_REGIME_DAYS)
            t0 = (anchor + timedelta(days=delta_days)).replace(
                hour=anchor.hour, minute=anchor.minute, second=0, microsecond=0)
            while t0.weekday() != anchor.weekday():
                t0 += timedelta(days=1 if t0.weekday() < anchor.weekday() else -1)
            if not (lo <= t0 <= hi):
                continue
            # FIX 8: contamination exclusion — this ticker's own real events must
            # not fall inside the placebo's baseline or window span.
            if any(-CONTAM_LO <= (d - t0).days <= CONTAM_HI
                   for d in ticker_events[ticker]):
                continue
            fake = {"event_id": f"placebo_{kind}_{draws}", "market_ticker": ticker,
                    "event_type": "placebo", "market_kind": kind,
                    "event_time": t0.isoformat(), "first_report_time": t0.isoformat(),
                    "surprise": np.nan, "moneyness_steps": np.nan}
            r = analyze_pair(fake, md, HEADLINE_WINDOW)
            if r:
                r["tier"], r["tier_label"] = assign_tier(r)
                out.append(r); draws += 1
        if draws < PLACEBO_DRAWS:
            print(f"  WARNING: only {draws}/{PLACEBO_DRAWS} placebo draws for "
                  f"{kind} (contamination exclusion is binding).")
    pdf = pd.DataFrame(out)
    summ = []
    for kind, g in pdf.groupby("market_kind"):
        ab = g["abnormal_move"].dropna()
        t, p = (np.nan, np.nan)
        if len(ab) >= 2:
            t, p = stats.ttest_1samp(ab, 0.0); t, p = float(t), float(p)
        mean_abn = float(ab.mean()) if len(ab) else np.nan
        # Economic significance first: a sub-1c "significant" move is noise.
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
    verify_macro_buckets(ev)  # FIX 6

    print("== confirmatory run (exploratory events excluded) ==")
    df = run_all(ev, md, confirmatory_only=True)
    df["cell"] = df.apply(cell_of, axis=1)
    df.to_csv(f"{OUT_DIR}/pair_results.csv", index=False)
    # FIX 3: event-level results are the primary analysis unit.
    dev_all = aggregate_by_event(df)
    dev_all.to_csv(f"{OUT_DIR}/event_results.csv", index=False)
    n_ev_total = df["event_id"].nunique()
    print(f"analyzed {n_ev_total} unique events x {df['ticker'].nunique()} markets "
          f"= {len(df)} pair-windows ({len(dev_all)} event-windows)")
    hw = df[df["window_days"] == HEADLINE_WINDOW]
    dev_hw = aggregate_by_event(hw)
    print("pair cell counts:", hw["cell"].value_counts().to_dict())
    print("event cell counts:", dev_hw["cell"].value_counts().to_dict())

    if EXCLUSIONS:
        pd.DataFrame(EXCLUSIONS).to_csv(f"{OUT_DIR}/exclusions.csv", index=False)
        print("exclusions by reason:",
              pd.DataFrame(EXCLUSIONS)["reason"].value_counts().to_dict())
    else:
        print("exclusions: none")

    for label, d in [("full", df), ("liquid_only", df[df["liquid"]])]:
        pooled, kw = pooled_tests(d, HEADLINE_WINDOW)
        pooled.to_csv(f"{OUT_DIR}/pooled_{label}_{HEADLINE_WINDOW}d.csv", index=False)
        kw.to_csv(f"{OUT_DIR}/tier_kruskal_{label}_{HEADLINE_WINDOW}d.csv", index=False)
        con = factorial_contrasts(d, HEADLINE_WINDOW)
        con.to_csv(f"{OUT_DIR}/contrasts_{label}_{HEADLINE_WINDOW}d.csv", index=False)
        h2 = h2_cross_domain(d, HEADLINE_WINDOW)
        h2.to_csv(f"{OUT_DIR}/h2_cross_domain_{label}_{HEADLINE_WINDOW}d.csv", index=False)
        print(f"\n-- {label}, {HEADLINE_WINDOW}-day window: pooled abnormal moves "
              f"(event-level, FIX 2/3) --")
        print(pooled[["cell", "tier", "n_events", "n_pairs", "mean_abn",
                       "mean_abn_logodds", "p_abn", "tested"]].to_string(index=False))
        print(f"-- {label}: H1a-H1d factorial contrasts (event-level) --")
        print(con[["contrast", "a", "b", "n_a", "n_b", "mean_abn_a", "mean_abn_b",
                    "p_abn", "p_abn_holm", "p_t50", "p_t50_holm",
                    "tested"]].to_string(index=False))
        print(f"-- {label}: H2 cross-domain falsification --")
        print(h2[["h2_cell", "n_events", "mean_abn", "ci95_lo", "ci95_hi",
                   "p", "tested"]].to_string(index=False))
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
        print(pooled[["cell", "tier", "n_events", "mean_abn", "p_abn",
                       "tested"]].to_string(index=False))
        print(f"-- {w}-day window: H1a-H1d contrasts --")
        print(con[["contrast", "n_a", "n_b", "p_abn", "p_abn_holm",
                    "tested"]].to_string(index=False))

    print(f"\nAll tables written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
