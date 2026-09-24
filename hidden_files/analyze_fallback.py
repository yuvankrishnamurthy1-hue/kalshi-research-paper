#!/usr/bin/env python3
"""
analyze_fallback.py — NON-CONFIRMATORY fallback descriptive track.

POST-PREREG SUPPLEMENTARY. This file does not touch preregistration.md,
analyze_kalshi_fixed.py, or any confirmatory output.

Motivation (the "Giannis rule"): the confirmatory pipeline excludes any
(event, market) pair with <5 baseline observations in T-45..T-5
(analyze_kalshi_fixed.py FIX 7). That rule silently dropped the single biggest
trade in the sample — giannis_to_heat (KXNBA-27-MIA 3c -> 8c on 2026-06-23,
4-6x volume spike) — because the KXNBA-27 contracts were only listed 8 days
before T0. This module guarantees that never happens again:

  * Any registered event with ZERO confirmatory pairs but >=3 pre-T0
    observations on at least one ticker gets a descriptive abnormal-move
    computation on the MAXIMUM available pre-window (T-45..T-5 preferred;
    all pre-T0 data if that is still <3 obs).
  * Every row is labeled NON-CONFIRMATORY / POST-PREREG. These numbers must
    never be pooled with confirmatory results or used in hypothesis tests.

Output: hidden_files/analysis_real/fallback_descriptive_3d.csv

Usage:
    python3 hidden_files/analyze_fallback.py
"""

import os, sys
from datetime import timedelta

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import analyze_kalshi_fixed as K  # reuse parse_iso_utc, first_report, midpoint

REGISTRY_PAIRS = os.path.join(BASE, "hidden_files", "analysis_registry_pairs.csv")
MARKET_DATA = os.path.join(BASE, "kalshi_api_data_summer", "market_data.csv")
CONFIRM_PAIRS = os.path.join(BASE, "hidden_files", "analysis_real", "pair_results.csv")
OUT_CSV = os.path.join(BASE, "hidden_files", "analysis_real",
                       "fallback_descriptive_3d.csv")

LABEL = "NON-CONFIRMATORY / POST-PREREG"
WINDOW_DAYS = 3
PREF_WINDOW_DAYS = 45   # preferred max pre-window (limits regime drift)
MIN_FALLBACK_N = 3      # descriptive threshold (>=3 pre-T0 obs)


def fallback_pair(ev_row, md, window_days=WINDOW_DAYS):
    """Descriptive abnormal move for one (event, market) pair.

    Baseline = mean midpoint over the maximum available pre-window:
    [T0-45d, T0) preferred; all pre-T0 observations if that yields <3.
    Returns dict or None (with reason in 'exclude_reason').
    """
    t0 = K.parse_iso_utc(K.first_report(ev_row))
    ticker = ev_row["market_ticker"]
    eid = ev_row["event_id"]

    px = md[md["ticker"] == ticker].sort_values("ts").reset_index(drop=True)
    if px.empty:
        return {"event_id": eid, "ticker": ticker, "exclude_reason": "no_market_data"}

    pre45 = px[(px["ts"] >= t0 - timedelta(days=PREF_WINDOW_DAYS))
               & (px["ts"] < t0)]["mid"].dropna()
    baseline_window = f"T0-{PREF_WINDOW_DAYS}d..T0"
    base = pre45
    if len(base) < MIN_FALLBACK_N:
        base = px[px["ts"] < t0]["mid"].dropna()
        baseline_window = "all pre-T0"
    if len(base) < MIN_FALLBACK_N:
        return {"event_id": eid, "ticker": ticker,
                "exclude_reason": "insufficient_preT0_history_lt3"}
    base_mean = float(base.mean())

    post = px[px["ts"] >= t0].reset_index(drop=True)
    if post.empty:
        return {"event_id": eid, "ticker": ticker,
                "exclude_reason": "no_post_event_data"}
    day0 = post.iloc[0]
    win_end = t0 + timedelta(days=window_days)
    win = post[post["ts"] <= win_end]
    win_end_row = win.iloc[-1]

    # volume: day-0 (first post candle) vs mean daily pre-window volume
    pre_vol = px[px["ts"] < t0]["volume"].dropna()
    vol_base = float(pre_vol.mean()) if len(pre_vol) else np.nan
    vol_day0 = float(day0["volume"]) if pd.notna(day0["volume"]) else np.nan
    vol_ratio = (vol_day0 / vol_base
                 if pd.notna(vol_day0) and pd.notna(vol_base) and vol_base > 0
                 else np.nan)

    return {
        "event_id": eid, "ticker": ticker, "exclude_reason": "",
        "n_base": len(base), "baseline_window": baseline_window,
        "baseline_mean": round(base_mean, 4),
        "day0_date": str(day0["ts"].date()), "day0_mid": round(float(day0["mid"]), 4),
        "abn_day0": round(float(day0["mid"]) - base_mean, 4),
        "win_end_date": str(win_end_row["ts"].date()),
        "win_end_mid": round(float(win_end_row["mid"]), 4),
        "abn_win_end": round(float(win_end_row["mid"]) - base_mean, 4),
        "vol_day0": round(vol_day0, 1) if pd.notna(vol_day0) else "",
        "vol_base_daily": round(vol_base, 1) if pd.notna(vol_base) else "",
        "vol_ratio": round(float(vol_ratio), 2) if pd.notna(vol_ratio) else "",
        "label": LABEL,
    }


def main():
    ev = pd.read_csv(REGISTRY_PAIRS)
    md = pd.read_csv(MARKET_DATA)
    md["ts"] = md["timestamp"].apply(K.parse_iso_utc)
    md["mid"] = md.apply(K.midpoint, axis=1)
    for c in ["volume"]:
        md[c] = pd.to_numeric(md[c], errors="coerce")

    confirm = pd.read_csv(CONFIRM_PAIRS)
    confirm_events = set(confirm["event_id"].unique())
    target = ev[~ev["event_id"].isin(confirm_events)].copy()
    print(f"events with zero confirmatory pairs: {sorted(target['event_id'].unique())}")

    rows = []
    for _, e in target.iterrows():
        r = fallback_pair(e, md)
        rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    ok = df[df["exclude_reason"] == ""]
    print(f"fallback descriptive rows: {len(ok)} "
          f"({ok['event_id'].nunique()} events with data)")
    for eid, g in ok.groupby("event_id"):
        print(f"  {eid}: {len(g)} tickers, "
              f"mean abn_day0={g['abn_day0'].mean():+.4f}, "
              f"mean abn_win_end={g['abn_win_end'].mean():+.4f}")
    bad = df[df["exclude_reason"] != ""]
    if len(bad):
        print("excluded from fallback too:")
        for eid, g in bad.groupby("event_id"):
            print(f"  {eid}: {len(g)} tickers — "
                  f"{g['exclude_reason'].value_counts().to_dict()}")
    print(f"wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
