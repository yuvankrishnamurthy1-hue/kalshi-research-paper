#!/usr/bin/env python3
"""Leak-study PILOT: how much of a Kalshi repricing happens BEFORE the news is public?

Exploratory pilot on past events (2026-01 to 2026-11). It calibrates the design
in LEAK_PREREG_DRAFT.md; it is NOT the confirmatory test (that uses future
events, after the preregistration is locked).

Contracts
  Sports  - the involved team's championship future (acquiring/keeping side =
            primary; giving side reported as secondary). Only events with a
            minute-level first-report timestamp are measured (date-only T0s
            cannot separate "before" from "after" on hourly data).
  Macro   - scheduled FOMC decisions and CPI releases, measured on the NEXT
            FOMC meeting's KXFED contracts, which reprice on the news but do
            NOT settle at the release (avoids the settlement artefact,
            REVIEW.md M10). Strike = the one whose midpoint at T0-7d is
            closest to 50c (chosen from pre-period prices only).
            Data are embargoed until release, so macro is the low-leak
            comparison group.

Hourly candles, window [T0-30d, T0+3d]. Midpoint = (bid+ask)/2; when bid = 0
and ask > 0, ask/2 (floor contracts); forward-filled over empty hours.

Per event (s = sign of the total move):
  pre    = mid(T0-1h)  - mid(T0-7d)       pre-report drift, 7 days
  pre24  = mid(T0-1h)  - mid(T0-25h)      pre-report drift, last 24 hours
  post   = mid(T0+24h) - mid(T0-1h)       reaction to the report
  total  = pre + post
  PRS    = pre / total                    pre-report share (|total| >= 1c only)
  z24    = s*pre24 / sd(24h changes in [T0-30d, T0-8d])   abnormal last-day drift

Outputs: hidden_files/analysis_real/leak_pilot_events.csv, leak_pilot_tests.csv
"""
import os, json, sys
from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import collect_extended as ce  # noqa: E402  (reuse polite API client)

RAW = os.path.join(HERE, "kalshi_api_data_leak", "raw")
OUT = os.path.join(HERE, "hidden_files", "analysis_real")
os.makedirs(RAW, exist_ok=True)
H = 3600
RNG = np.random.default_rng(20261124)

# ---- sports: (event_id, first-report T0 UTC, [(ticker, role)]) ----
SPORTS = [
    ("giannis_to_heat", "2026-06-23T03:50:00Z", [("KXNBA-27-MIA", "get"), ("KXNBA-27-MIL", "give")]),
    ("jaylen_brown_to_76ers", "2026-07-01T22:20:00Z", [("KXNBA-27-PHI", "get"), ("KXNBA-27-BOS", "give")]),
    ("dlo_six_team_trade", "2026-07-08T00:53:00Z", [("KXNBA-27-MEM", "get")]),
    ("kawhi_to_raptors", "2026-09-14T18:56:00Z", [("KXNBA-27-TOR", "get"), ("KXNBA-27-LAC", "give")]),
    ("lebron_to_76ers", "2026-07-24T20:34:00Z", [("KXNBA-27-PHI", "get"), ("KXNBA-27-LAL", "give")]),
    ("donovan_mitchell_extension", "2026-07-07T10:01:00Z", [("KXNBA-27-CLE", "keep")]),
    ("myles_garrett_to_rams", "2026-06-01T17:19:00Z", [("KXSB-27-LAR", "get"), ("KXSB-27-CLE", "give")]),
    ("aj_brown_to_patriots", "2026-06-01T20:20:00Z", [("KXSB-27-NE", "get"), ("KXSB-27-PHI", "give")]),
    ("von_miller_to_cowboys", "2026-08-17T01:10:00Z", [("KXSB-27-DAL", "get")]),
    ("brian_oneill_extension", "2026-07-28T14:24:00Z", [("KXSB-27-MIN", "keep")]),
    ("aaron_donald_comeback", "2026-08-30T17:00:00Z", [("KXSB-27-LAR", "get")]),
]
# Boston signings/extensions excluded: windows overlap the Jul-1 Jaylen Brown trade.

# ---- macro: scheduled releases with exact official times (DST-corrected) ----
MACRO = [
    ("cpi_2026_01", "2026-01-13T13:30:00Z"), ("fomc_2026_01", "2026-01-28T19:00:00Z"),
    ("cpi_2026_02", "2026-02-13T13:30:00Z"), ("cpi_2026_03", "2026-03-11T12:30:00Z"),
    ("fomc_2026_03", "2026-03-18T18:00:00Z"), ("cpi_2026_04", "2026-04-10T12:30:00Z"),
    ("fomc_2026_04", "2026-04-29T18:00:00Z"), ("cpi_2026_05", "2026-05-12T12:30:00Z"),
    ("cpi_2026_06", "2026-06-10T12:30:00Z"), ("fomc_2026_06", "2026-06-17T18:00:00Z"),
    ("cpi_2026_07", "2026-07-14T12:30:00Z"), ("fomc_2026_07", "2026-07-29T18:00:00Z"),
    ("cpi_2026_08", "2026-08-12T12:30:00Z"), ("cpi_2026_09", "2026-09-11T12:30:00Z"),
    ("fomc_2026_09", "2026-09-16T18:00:00Z"), ("cpi_2026_10", "2026-10-14T12:30:00Z"),
    ("fomc_2026_10", "2026-10-28T18:00:00Z"), ("cpi_2026_11", "2026-11-10T13:30:00Z"),
]


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def kxfed_meetings():
    import glob
    m = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(HERE, "kalshi_api_data*", "market_metadata.csv"))])
    f = m[m.series == "KXFED"].drop_duplicates("ticker").copy()
    f["ev"] = f.ticker.str.split("-").str[1]
    f["close_ts"] = f.close_time.apply(ts)
    return f


def hourly(series, ticker, t0):
    path = os.path.join(RAW, f"{ticker}_{t0}.json")
    if os.path.exists(path):
        return json.load(open(path))
    params = {"start_ts": t0 - 30 * 86400, "end_ts": t0 + 3 * 86400, "period_interval": 60}
    d = ce.get_json(f"{ce.BASE}/series/{series}/markets/{ticker}/candlesticks", params)
    c = (d or {}).get("candlesticks") or []
    if not c:
        d = ce.get_json(f"{ce.BASE}/historical/markets/{ticker}/candlesticks", params)
        c = (d or {}).get("candlesticks") or []
    json.dump(c, open(path, "w"))
    return c


def mid_series(candles, t0):
    rows = []
    for c in candles:
        b = ce.px_field(c, ("yes_bid", "close_dollars"), ("yes_bid", "close"))
        a = ce.px_field(c, ("yes_ask", "close_dollars"), ("yes_ask", "close"))
        try:
            b, a = float(b), float(a)
        except (TypeError, ValueError):
            continue
        if a <= 0:
            continue
        rows.append((c["end_period_ts"], (b + a) / 2 if b > 0 else a / 2))
    if not rows:
        return None
    s = pd.Series(dict(rows)).sort_index()
    grid = np.arange(t0 - 30 * 86400, t0 + 3 * 86400 + 1, H)
    return s.reindex(sorted(set(grid) | set(s.index))).ffill().reindex(grid)


def at(s, t):
    """Last midpoint at or before t (hourly grid already forward-filled)."""
    v = s.loc[:t].dropna()
    return v.iloc[-1] if len(v) else np.nan


def metrics(s, t0):
    m7, m25, m1, p24 = at(s, t0 - 7 * 86400), at(s, t0 - 25 * H), at(s, t0 - H), at(s, t0 + 24 * H)
    pre, pre24, post = m1 - m7, m1 - m25, p24 - m1
    total = pre + post
    base = s.loc[t0 - 30 * 86400: t0 - 8 * 86400].dropna()
    d24 = (base.values[24:] - base.values[:-24]) if len(base) > 48 else np.array([])
    sd = np.std(d24, ddof=1) if len(d24) > 10 else np.nan
    sgn = np.sign(total) if abs(total) > 1e-9 else 0.0
    prs = pre / total if abs(total) >= 0.01 else np.nan
    z24 = (sgn * pre24 / sd) if (sd and sd > 1e-9 and sgn) else np.nan
    return {"mid_T-7d": m7, "mid_T-1h": m1, "mid_T+24h": p24,
            "pre_c": 100 * pre, "pre24_c": 100 * pre24, "post_c": 100 * post,
            "total_c": 100 * total, "prs": prs, "z24": z24, "sd24_c": 100 * sd if sd == sd else np.nan}


def perm(a, b, n=20000):
    a, b = np.asarray(a, float), np.asarray(b, float)
    obs = abs(np.median(a) - np.median(b))
    pool, hits = np.concatenate([a, b]), 0
    for _ in range(n):
        RNG.shuffle(pool)
        hits += abs(np.median(pool[:len(a)]) - np.median(pool[len(a):])) >= obs - 1e-12
    return (hits + 1) / (n + 1)


def main():
    rows = []
    for eid, t0s, legs in SPORTS:
        t0 = ts(t0s)
        for tk, role in legs:
            s = mid_series(hourly(tk.split("-")[0], tk, t0), t0)
            r = {"event_id": eid, "domain": "sports", "ticker": tk, "role": role, "t0": t0s}
            r.update(metrics(s, t0) if s is not None else {})
            rows.append(r)
            print(eid, tk, {k: round(v, 3) for k, v in r.items() if isinstance(v, float)}, flush=True)

    fed = kxfed_meetings()
    for eid, t0s in MACRO:
        t0 = ts(t0s)
        nxt = fed[fed.close_ts > t0 + H].sort_values("close_ts")
        ev = nxt.ev.iloc[0]
        best = None
        for tk in sorted(nxt[nxt.ev == ev].ticker):
            s = mid_series(hourly("KXFED", tk, t0), t0)
            if s is None:
                continue
            m7 = at(s, t0 - 7 * 86400)
            if pd.notna(m7) and (best is None or abs(m7 - 0.5) < best[0]):
                best = (abs(m7 - 0.5), tk, s)
        r = {"event_id": eid, "domain": "macro", "ticker": best[1] if best else "", "role": f"next_meeting_{ev}", "t0": t0s}
        if best:
            r.update(metrics(best[2], t0))
        rows.append(r)
        print(eid, r.get("ticker"), {k: round(v, 3) for k, v in r.items() if isinstance(v, float)}, flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "leak_pilot_events.csv"), index=False)

    sp = df[(df.domain == "sports") & (df.role.isin(["get", "keep"]))]
    mc = df[df.domain == "macro"]
    tests = []
    for label, col in [("pre-report share (PRS, |total|>=1c)", "prs"),
                       ("abnormal last-24h drift z", "z24")]:
        a, b = sp[col].dropna().values, mc[col].dropna().values
        if len(a) >= 3 and len(b) >= 3:
            u = stats.mannwhitneyu(a, b, alternative="two-sided")
            tests.append({"outcome": label, "n_sports": len(a), "median_sports": round(float(np.median(a)), 3),
                          "n_macro": len(b), "median_macro": round(float(np.median(b)), 3),
                          "mannwhitney_p": round(float(u.pvalue), 4), "perm_median_p": round(perm(a, b), 4)})
    # within-group: is sports last-24h drift abnormal (z > 0 => drifting toward the eventual move)?
    for dom, g in [("sports", sp), ("macro", mc)]:
        z = g["z24"].dropna().values
        if len(z) >= 3:
            w = stats.wilcoxon(z) if np.any(z != 0) else None
            tests.append({"outcome": f"{dom}: median z24 vs 0 (Wilcoxon)", f"n_{dom}": len(z),
                          f"median_{dom}": round(float(np.median(z)), 3),
                          "mannwhitney_p": round(float(w.pvalue), 4) if w else np.nan})
    tdf = pd.DataFrame(tests)
    tdf.to_csv(os.path.join(OUT, "leak_pilot_tests.csv"), index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    show = ["event_id", "domain", "ticker", "role", "pre_c", "pre24_c", "post_c", "total_c", "prs", "z24"]
    print("\n", df[show].round(3).to_string(index=False))
    print("\n", tdf.to_string(index=False))


if __name__ == "__main__":
    main()
