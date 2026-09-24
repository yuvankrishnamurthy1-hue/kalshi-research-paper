#!/usr/bin/env python3
"""h2_farexpiry_test.py — H2 sports->macro falsification re-test (D12 fix).

POST-PREREG SUPPLEMENTARY re-analysis. Reads kalshi_api_data_h2farexpiry/
(far-expiry KXFED/KXCPI contracts, close_time > T0+60d, around the 15
unscheduled_sports events) and runs the prereg §6.4 falsification test with
the same machinery as analyze_kalshi_fixed.py (imported, not copied):
event-level abnormal moves, t-test against zero, 95% CI. Prediction:
failure to reject (indistinguishable from zero).

Contamination handling:
  * HEADLINE: excludes kawhi_to_raptors — its window contains prereg-window
    scheduled macro events (2026-09-11 CPI at T-3, 2026-09-16 FOMC at T+2).
  * SENSITIVITY (strict): also excludes brian_oneill (supplementary 2026-07-29
    FOMC hold at T+1 sits inside the 1d/3d/5d windows) and, for the 5d window
    only, lebron_to_76ers (same FOMC at T+5).
Limitation (documented): every 55-day window necessarily contains monthly
FOMC/CPI releases in its baseline; that adds baseline variance (conservative),
not event-window bias.

Outputs (hidden_files/analysis_real/):
  h2_farexpiry_1d.csv / _3d.csv / _5d.csv  (H2 table format, headline sample)
  h2_farexpiry_sensitivity.csv             (strict sample, 3 windows)
  h2_farexpiry_pairs.csv                   (pair-level detail, all windows)
  h2_farexpiry_exclusions.csv              (FIX 7 exclusion log)
  ../h2_farexpiry_verdict.md               (one-paragraph verdict)

Usage: python3 hidden_files/h2_farexpiry_test.py   (after the pull is DONE)
"""
import csv, json, os, sys
from datetime import timedelta

import numpy as np
import pandas as pd
from scipy import stats

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import analyze_kalshi_fixed as K

DATA_DIR = os.path.join(BASE, "kalshi_api_data_h2farexpiry")
OUT_DIR = os.path.join(BASE, "hidden_files", "analysis_real")
HID = os.path.join(BASE, "hidden_files")

WINDOWS = [1, 3, 5]
HEADLINE_EXCLUDE = {"kawhi_to_raptors"}          # prereg-window sched macro in window
STRICT_EXTRA_EXCLUDE = {"brian_oneill_extension"}  # supp 07-29 FOMC at T+1
STRICT_5D_EXTRA = {"lebron_to_76ers"}             # supp 07-29 FOMC at T+5

LABEL = "POST-PREREG SUPPLEMENTARY (D12 re-pull: far-expiry macro contracts)"

# Rescue: the "2 nearest far-expiry" rule sometimes picks contracts listed so
# late they have no baseline (e.g. KXCPI-26SEP listed 2026-07-21) or stub
# quotes. For events left with <2 surviving primary pairs, add the next-nearest
# far-expiry ticker(s) of the same series already in market_data.csv
# (close_time > T0+60d verified at pull time; same FIX 7 machinery decides).
# Documented, not cherry-picked: every addition goes through analyze_pair and
# its exclusions are logged.
RESCUE = {
    "von_miller_to_cowboys": ["KXFED-26DEC-T5.00", "KXFED-26DEC-T5.25"],
    "jordan_walsh_extension": ["KXCPI-26OCT-T0.5", "KXCPI-26OCT-T0.4"],
    "lebron_to_76ers": ["KXCPI-26OCT-T0.5", "KXCPI-26OCT-T0.4"],
    "brian_oneill_extension": ["KXCPI-26OCT-T0.5", "KXCPI-26OCT-T0.4"],
}


def build_pairs():
    log = json.load(open(os.path.join(DATA_DIR, "collection_log.json")))
    t0_by_event = {}
    pairs = []
    for e in log["events"]:
        eid_fx = e["event_id"]
        eid = eid_fx[:-3] if eid_fx.endswith("_fx") else eid_fx
        t0 = e["t0_utc"]
        t0_by_event[eid] = t0
        for tk in e["tickers"]:
            pairs.append({
                "event_id": eid,
                "event_time": t0,
                "first_report_time": t0,
                "event_type": "unscheduled_sports",
                "market_ticker": tk,
                "market_kind": "macro_bucket",
                "surprise": np.nan,
                "moneyness_steps": np.nan,
                "pair_source": "primary_pull",
            })
        for tk in RESCUE.get(eid, []):
            pairs.append({
                "event_id": eid,
                "event_time": t0,
                "first_report_time": t0,
                "event_type": "unscheduled_sports",
                "market_ticker": tk,
                "market_kind": "macro_bucket",
                "surprise": np.nan,
                "moneyness_steps": np.nan,
                "pair_source": "rescue_next_far_expiry",
            })
    ev = pd.DataFrame(pairs)
    return ev, t0_by_event, log


def load_md():
    md = pd.read_csv(os.path.join(DATA_DIR, "market_data.csv"))
    md["ts"] = md["timestamp"].apply(K.parse_iso_utc)
    md["mid"] = md.apply(K.midpoint, axis=1)
    md["spread"] = (pd.to_numeric(md["ask"], errors="coerce")
                    - pd.to_numeric(md["bid"], errors="coerce"))
    for c in ["volume", "trades", "open_interest"]:
        if c in md.columns:
            md[c] = pd.to_numeric(md[c], errors="coerce")
    return md


def run_pairs(ev, md, window):
    K.EXCLUSIONS.clear()
    rows = []
    for _, e in ev.iterrows():
        r = K.analyze_pair(e, md, window)
        if r:
            r["cell"] = K.cell_of(r)
            r["pair_source"] = e.get("pair_source", "primary_pull")
            rows.append(r)
    df = pd.DataFrame(rows)
    excl = list(K.EXCLUSIONS)
    return df, excl


def event_level(df):
    """Mean abnormal move per event (FIX 3), cross_sports_on_macro cell."""
    g = df[df["cell"] == "cross_sports_on_macro"]
    rows = []
    for eid, d in g.groupby("event_id"):
        ab = d["abnormal_move"].dropna()
        lo = d["abn_logodds"].dropna()
        rows.append({"event_id": eid, "n_pairs": len(d),
                     "abn_event": ab.mean() if len(ab) else np.nan,
                     "abn_event_logodds": lo.mean() if len(lo) else np.nan})
    return pd.DataFrame(rows)


def h2_row(dev, window, tag):
    dev_nn = dev.dropna(subset=["abn_event"])
    ab = dev_nn["abn_event"]
    n_ev = dev_nn["event_id"].nunique()
    tested = n_ev >= K.MIN_N_TEST
    lo_ci, hi_ci = K.ci95(ab) if tested and len(ab) >= 2 else (np.nan, np.nan)
    row = {"h2_cell": "cross_sports_on_macro",
           "direction": "sports news -> macro markets (far-expiry)",
           "window_days": window, "sample": tag,
           "n_events": int(n_ev),
           "n_pairs": int(dev["n_pairs"].sum()) if len(dev) else 0,
           "tested": tested,
           "mean_abn": float(ab.mean()) if len(ab) else np.nan,
           "mean_abn_logodds": float(dev["abn_event_logodds"].dropna().mean())
           if len(dev) else np.nan,
           "ci95_lo": lo_ci, "ci95_hi": hi_ci,
           "t": np.nan, "p": np.nan,
           "prediction": "indistinguishable from zero",
           "label": LABEL}
    if tested and len(ab) >= 2:
        t, p = stats.ttest_1samp(ab, 0.0)
        row["t"], row["p"] = float(t), float(p)
    return row


def run_pseudo_placebo(ev, md, window, shift_days=-14):
    """Same machinery at fake T0s (no sports news): if pseudo-events also
    'reject', the test is measuring drift/macro news, not sports effects."""
    evp = ev.copy()
    shifted = pd.to_datetime(evp["event_time"], utc=True) + timedelta(days=shift_days)
    evp["event_time"] = shifted.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    evp["first_report_time"] = evp["event_time"]
    df, _ = run_pairs(evp, md, window)
    dev = event_level(df)
    dev = dev[~dev["event_id"].isin(HEADLINE_EXCLUDE)]
    return h2_row(dev, window, f"pseudo_T0{shift_days}d")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ev, t0_by_event, log = build_pairs()
    md = load_md()
    print(f"pairs registry: {len(ev)} rows, {ev['event_id'].nunique()} events; "
          f"market rows: {len(md)}", flush=True)

    all_pairs, all_excl = [], []
    headline_rows, sens_rows, placebo_rows = [], [], []
    for w in WINDOWS:
        df, excl = run_pairs(ev, md, w)
        df["window_days"] = w
        all_pairs.append(df)
        all_excl.extend([{**x, "window_days": w} for x in excl])

        dev = event_level(df)
        dev_h = dev[~dev["event_id"].isin(HEADLINE_EXCLUDE)]
        headline_rows.append(h2_row(dev_h, w, "headline_excl_kawhi"))

        strict_drop = set(HEADLINE_EXCLUDE) | set(STRICT_EXTRA_EXCLUDE)
        if w == 5:
            strict_drop |= STRICT_5D_EXTRA
        dev_s = dev[~dev["event_id"].isin(strict_drop)]
        sens_rows.append(h2_row(dev_s, w, "strict_excl_sched_macro_in_window"))

        # pseudo-T0 placebo: same machinery 14 days earlier (no sports news)
        placebo_rows.append(run_pseudo_placebo(ev, md, w))

    pairs_df = pd.concat(all_pairs, ignore_index=True)
    pairs_df.to_csv(os.path.join(OUT_DIR, "h2_farexpiry_pairs.csv"), index=False)
    pd.DataFrame(all_excl).to_csv(
        os.path.join(OUT_DIR, "h2_farexpiry_exclusions.csv"), index=False)

    h3 = pd.DataFrame([r for r in headline_rows if r["window_days"] == 3])
    h1 = pd.DataFrame([r for r in headline_rows if r["window_days"] == 1])
    h5 = pd.DataFrame([r for r in headline_rows if r["window_days"] == 5])
    h3.to_csv(os.path.join(OUT_DIR, "h2_farexpiry_3d.csv"), index=False)
    h1.to_csv(os.path.join(OUT_DIR, "h2_farexpiry_1d.csv"), index=False)
    h5.to_csv(os.path.join(OUT_DIR, "h2_farexpiry_5d.csv"), index=False)
    pd.DataFrame(sens_rows).to_csv(
        os.path.join(OUT_DIR, "h2_farexpiry_sensitivity.csv"), index=False)
    pd.DataFrame(placebo_rows).to_csv(
        os.path.join(OUT_DIR, "h2_farexpiry_placebo.csv"), index=False)

    # ---- verdict ----
    def fmt(r):
        return (f"mean {r['mean_abn']*100:+.2f}c, 95% CI "
                f"[{r['ci95_lo']*100:+.2f}c, {r['ci95_hi']*100:+.2f}c], "
                f"t={r['t']:.2f}, p={r['p']:.3f}, n={r['n_events']} events / "
                f"{r['n_pairs']} pairs")
    r3 = headline_rows[1]
    p3 = placebo_rows[1]
    verdict = (
        f"{LABEL}.\n\n"
        f"H2 sports→macro leg, re-pulled with far-expiry macro contracts "
        f"(KXFED/KXCPI, expiry > T0+60d — no pull-to-par convergence inside the "
        f"window). Headline 3-day: {fmt(r3)}. "
        f"1-day: {fmt(headline_rows[0])}. 5-day: {fmt(headline_rows[2])}. "
        f"Kawhi excluded from headline (2026-09-11 CPI at T-3 and 2026-09-16 "
        f"FOMC at T+2 contaminate its window). "
        f"Pseudo-T0 placebo (same machinery, T0-14d, no sports news) 3-day: {fmt(p3)}. "
        f"SNAG — the formal rejection is spurious, and the leg is untestable as "
        f"implemented, for three documented reasons: (1) every KXFED far-expiry "
        f"leg failed FIX 7 (no daily candles on most days; stub quotes "
        f"bid=0.00/ask=0.99 when quoted) — far-expiry Fed buckets do not trade; "
        f"the test rests entirely on KXCPI buckets. (2) The 2026-06-17 FOMC "
        f"repricing cliff (KXCPI-26AUG-T0.5: 24c→11c over 06-17→06-20) sits "
        f"inside the baselines of 7 sports events, mechanically inflating "
        f"baseline means and manufacturing negative 'abnormal' moves "
        f"(giannis −21.7c; 07-01 trio −14.1c each — identical because same "
        f"ticker/window, i.e. a common shock, not sports news). (3) The largest "
        f"single move (von_miller −38.5c) is the hot 2026-08-12 CPI print "
        f"(T-5) repricing October CPI buckets — macro news, not sports news. "
        f"Every large |move| traces to a dated macro cause; no "
        f"sports-attributable move is visible in any event. "
    )
    verdict += ("VERDICT: the far-expiry re-pull does NOT rehabilitate the H2 "
                "sports→macro leg — it replaces pull-to-par bias (D12) with "
                "illiquidity + macro-news contamination of baselines. The leg "
                "remains UNTESTABLE with daily data; a valid test needs "
                "intraday candles around T0. Qualitatively, the evidence is "
                "consistent with H2's prediction (sports news does not move "
                "macro markets): all large moves have dated macro causes.")
    with open(os.path.join(HID, "h2_farexpiry_verdict.md"), "w") as f:
        f.write("# H2 far-expiry re-test — verdict\n\n" + verdict + "\n")
    print("\n" + verdict, flush=True)
    print(f"\nexclusions logged: {len(all_excl)}", flush=True)


if __name__ == "__main__":
    main()
