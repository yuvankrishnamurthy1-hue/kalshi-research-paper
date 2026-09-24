#!/usr/bin/env python3
"""
coverage_precheck.py — REGISTRATION-TIME exclusion guard for the Kalshi event study.

Purpose (the "Giannis rule"): no registered event may ever again be SILENTLY
dropped from confirmatory analysis because its contracts lacked baseline
history. Giannis-to-Heat (2026-06-23) was the single biggest trade in the
sample — KXNBA-27-MIA went 3c -> 8c on trade day with a 4-6x volume spike —
yet it was fully excluded (KXNBA-27 contracts were only listed 2026-06-15,
8 days before T0, failing the old >=5 baseline-obs rule) and the exclusion was
buried in a footnote. D16 relaxed the rule to >=3 obs in [T-30,T-5] (flagged
thin at 3-4) plus an extended-baseline fallback ([T-30,T-1] for tickers with
>=5 total pre-T0 obs); this script enforces the D16 rule.

Run this BEFORE/AT registration time, right after the data pull for an event
lands. For every event in hidden_files/event_registry.csv it checks the
earliest available contract listing date in kalshi_api_data_summer/ against
T0-30 and prints a LOUD warning for any event whose confirmatory baseline
will be thin (<3 baseline obs expected, or extended-baseline only). Warnings are also saved to
hidden_files/coverage_precheck_report.txt.

This script changes NOTHING about the locked preregistration or the
confirmatory analysis. It is a process guard: a loud warning at registration
time forces an explicit decision (extend the pull, switch to the fallback
descriptive track in analyze_fallback.py, or document the exclusion in
excluded_but_material.md) instead of a silent drop discovered after analysis.

Usage:
    python3 hidden_files/coverage_precheck.py
"""

import csv, json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Env overrides allow running the guard on later batches (e.g. extended pull).
REGISTRY = os.environ.get("KALSHI_PRECHECK_REGISTRY",
           os.path.join(BASE, "hidden_files", "event_registry.csv"))
_raw_log = os.environ.get("KALSHI_PRECHECK_LOG")
MDATA = os.environ.get("KALSHI_PRECHECK_MDATA",
        os.path.join(BASE, "kalshi_api_data_summer", "market_data.csv"))
REPORT = os.environ.get("KALSHI_PRECHECK_REPORT",
         os.path.join(BASE, "hidden_files", "coverage_precheck_report.txt"))
# The registry may be event-level (event_registry.csv) or the collection log;
# when KALSHI_PRECHECK_LOG is set, event<->ticker mapping comes from it.
LOG = _raw_log or os.path.join(BASE, "kalshi_api_data_summer", "collection_log.json")

MIN_BASELINE_N = 3          # D16 rule (was 5 pre-D16): >=3 obs in [T-30,T-5]
BASELINE_START = 30         # T-30
BASELINE_END = 5            # T-5
THIN_BASELINE_N = 5         # 3-4 obs = confirmatory-eligible but flagged thin (D16)
EXTENDED_MIN_N = 5          # >=5 total pre-T0 obs -> extended-baseline [T-30,T-1] (D16)
FALLBACK_MIN_N = 3          # analyze_fallback.py descriptive threshold


def parse_utc(s):
    s = str(s).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        # date-only registry entries (macro events): treat as midnight UTC
        dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def main():
    out_lines = []
    def emit(line=""):
        print(line, flush=True)
        out_lines.append(line)

    # ---- load per-event ticker lists ----
    with open(LOG) as f:
        log = json.load(f)
    tickers_by_event = {e["event_id"]: e.get("tickers", []) for e in log["events"]}

    # ---- load earliest listing date + per-ticker date sets from market_data ----
    earliest = {}                       # ticker -> earliest date (datetime.date)
    dates_by_ticker = defaultdict(set)  # ticker -> set of dates with a usable mid
    with open(MDATA) as f:
        for r in csv.DictReader(f):
            t = r["ticker"]
            try:
                ts = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                continue
            d = ts.date()
            if t not in earliest or d < earliest[t]:
                earliest[t] = d
            # usable mid: bid/ask present, else last
            try:
                b, a = float(r["bid"] or 0), float(r["ask"] or 0)
                ok = b > 0 and a > 0
            except (TypeError, ValueError):
                ok = False
            if not ok:
                try:
                    float(r["last"])
                    ok = True
                except (TypeError, ValueError):
                    ok = False
            if ok:
                dates_by_ticker[t].add(d)
    data_max = max((d for ds in dates_by_ticker.values() for d in ds), default=None)

    # ---- per-event precheck ----
    n_events = n_ok = n_warn = n_crit = 0
    with open(REGISTRY) as f:
        events = list(csv.DictReader(f))

    emit("=" * 78)
    emit("COVERAGE PRECHECK — registration-time exclusion guard")
    emit("Rule: every event must have >= %d baseline obs in [T0-%dd, T0-%dd) on at"
         % (MIN_BASELINE_N, BASELINE_START, BASELINE_END))
    emit("least one ticker, or it WILL be excluded from confirmatory analysis.")
    emit("=" * 78)

    for ev in events:
        n_events += 1
        eid = ev["event_id"]
        t0 = parse_utc(ev["t0_utc"])
        tickers = tickers_by_event.get(eid, [])
        emit("")
        emit(f"--- {eid}  T0={ev['t0_utc']}  cell={ev.get('cell', '?')}")

        if t0 is None:
            n_crit += 1
            emit("!!! CRITICAL: unparseable T0 — cannot precheck; fix registry row.")
            continue
        if data_max is not None and t0.date() > data_max:
            n_warn += 1
            emit(f"!!! WARNING: T0 ({t0.date()}) is AFTER the latest market data "
                 f"({data_max}). Baseline cannot be prechecked until the post-event "
                 f"pull lands. Re-run this script after pulling.")
            continue
        if not tickers:
            n_crit += 1
            emit("!!! CRITICAL: NO TICKERS DISCOVERED for this event. It will be "
                 "FULLY EXCLUDED from confirmatory analysis. Action: extend the "
                 "ticker pull, or document in excluded_but_material.md.")
            continue

        blo = (t0 - timedelta(days=BASELINE_START)).date()
        bhi = (t0 - timedelta(days=BASELINE_END)).date()
        per_ticker_n = {}
        late_listings = []
        for t in tickers:
            ds = dates_by_ticker.get(t, set())
            n = sum(1 for d in ds if blo <= d < bhi)
            per_ticker_n[t] = n
            if t in earliest and earliest[t] > blo:
                late_listings.append((t, earliest[t]))
        n_good = sum(1 for n in per_ticker_n.values() if n >= MIN_BASELINE_N)
        n_thin = sum(1 for n in per_ticker_n.values()
                     if MIN_BASELINE_N <= n < THIN_BASELINE_N)
        # D16 extended baseline: <3 in-window obs but >=5 total pre-T0 obs
        t0d = t0.date()
        n_extended = 0
        for t in tickers:
            ds = dates_by_ticker.get(t, set())
            n_pre = sum(1 for d in ds if d < t0d)
            if per_ticker_n[t] < MIN_BASELINE_N and n_pre >= EXTENDED_MIN_N:
                n_extended += 1
        n_out = len(tickers) - n_good - n_extended
        emit(f"    tickers: {len(tickers)} | >=3 baseline obs: {n_good} "
             f"(thin 3-4: {n_thin}) | extended-baseline eligible: {n_extended} | "
             f"descriptive-only (<5 pre-T0): {n_out}")
        if late_listings:
            ex = ", ".join(f"{t} (listed {d})" for t, d in late_listings[:5])
            more = f" +{len(late_listings) - 5} more" if len(late_listings) > 5 else ""
            emit(f"    note: {len(late_listings)} tickers listed AFTER T0-30: {ex}{more}")

        if n_good == 0 and n_extended == 0:
            n_crit += 1
            emit("!!! CRITICAL: NO ticker for this event reaches a confirmatory "
                 "baseline (D16: >=3 obs in [T-30,T-5], or >=5 pre-T0 obs for the "
                 "extended baseline). This event WILL BE FULLY EXCLUDED from "
                 "confirmatory analysis — the Giannis failure mode. Required "
                 "actions BEFORE analysis: (1) try an earlier/longer pull for "
                 "these contracts; (2) if data truly does not exist, route the "
                 "event to the fallback descriptive track "
                 "(hidden_files/analyze_fallback.py); (3) record it in "
                 "hidden_files/excluded_but_material.md with its descriptive "
                 "result. DO NOT let it drop silently.")
        elif n_good + n_extended < len(tickers):
            n_warn += 1
            emit(f"!!! WARNING: only {n_good + n_extended}/{len(tickers)} tickers meet a "
                 f"confirmatory baseline (incl. {n_extended} extended-baseline). The rest are excluded pair-by-pair "
                 f"(see analysis_real/exclusions.csv). Check that the EXCLUDED "
                 "tickers are not the economically central ones for this event "
                 "(e.g. the two teams in a trade).")
        else:
            n_ok += 1
            emit("    OK: full baseline coverage.")

    emit("")
    emit("=" * 78)
    emit(f"SUMMARY: {n_events} events | {n_ok} OK | {n_warn} warnings | "
         f"{n_crit} CRITICAL")
    if n_crit:
        emit("!!! ACTION REQUIRED: resolve every CRITICAL item before analysis — "
             "an unexamined CRITICAL here is how Giannis happened.")
    emit("=" * 78)

    with open(REPORT, "w") as f:
        f.write("\n".join(out_lines) + "\n")
    print(f"\nReport saved to {REPORT}")


if __name__ == "__main__":
    main()
