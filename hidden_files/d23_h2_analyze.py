"""D23 analysis: H2 sports->macro, intraday minute-candle test.
Reads hidden_files/analysis_real/d23_h2_intraday_sweep.csv.
For each event x macro-contract with adequate liquidity, re-pull minute candles
and test for an abnormal move in a tight window around the sports T0.

Liquidity screen (pre-registered here, before seeing prices):
  LIQUID if minutes_with_trades >= 20 in the 6h window OR median spread <= 3c
  with >= 60 minute-candles present. Otherwise UNTESTABLE (illiquid).

Move metric: post_median_mid [+10,+180]min minus pre_median_mid [-180,-10]min.
Null band: distribution of all other non-overlapping 10-min block moves in the
same 6h window excluding [-15,+15]min around T0 (mini placebo). Report the
T0-block move's rank among placebo blocks.
"""
import urllib.request, json, csv, calendar, time
import statistics as st

BASE = "https://api.elections.kalshi.com/trade-api/v2"
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "kalshi-research/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def minute_series(series, ticker, t0, hours=3):
    url = (f"{BASE}/series/{series}/markets/{ticker}/candlesticks"
           f"?start_ts={t0-hours*3600}&end_ts={t0+hours*3600}&period_interval=1")
    cs = get(url).get("candlesticks", [])
    out = []
    for c in cs:
        try:
            b = float(c["yes_bid"]["close_dollars"]); a = float(c["yes_ask"]["close_dollars"])
            out.append((c["end_period_ts"], (a + b) / 2, a - b, float(c.get("volume_fp", 0))))
        except Exception:
            pass
    return sorted(out)

sweep = list(csv.DictReader(open("hidden_files/analysis_real/d23_h2_intraday_sweep.csv")))
events = {r["event_id"]: r["t0_utc"] for r in
          csv.DictReader(open("hidden_files/event_registry.csv"))
          if r["cell"] == "unscheduled_sports"}

rows = []
for s in sweep:
    if "err" in s and s["err"]:
        rows.append(dict(event=s["event"], series=s["series"], ticker=s.get("ticker",""),
                         verdict="ERROR", note=s["err"][:50]))
        continue
    eid, series, tk = s["event"], s["series"], s["ticker"]
    t0 = calendar.timegm(time.strptime(events[eid], "%Y-%m-%dT%H:%M:%SZ"))
    n_min = int(s["n_min"] or 0)
    n_tr = int(s["min_with_trades"] or 0)
    vol6h = float(s["total_vol_6h"] or 0)
    med_spr = float(s["median_spread_c"]) if s["median_spread_c"] else 99.0
    # liquid = real trading happened in the window (volume-based), with tight quotes
    liquid = (vol6h >= 500 and med_spr <= 5.0) or (n_tr >= 10 and med_spr <= 3.0)
    if not liquid:
        rows.append(dict(event=eid, series=series, ticker=tk, verdict="UNTESTABLE",
                         note=f"illiquid: {n_min} min-candles, {n_tr} w/ trades, spread {med_spr}c"))
        continue
    try:
        pts = minute_series(series, tk, t0)
    except Exception as e:
        rows.append(dict(event=eid, series=series, ticker=tk, verdict="ERROR",
                         note=f"refetch failed: {str(e)[:60]}"))
        time.sleep(0.15)
        continue
    # rolling-median jump: median(+5..+60min) - median(-60..-5min); needs >=5 pts a side
    q = [(ts, mid) for ts, mid, spr, v in pts]
    def wmed(lo, hi, need=5):
        xs = [m for ts, m in q if lo <= ts <= hi]
        return st.median(xs) if len(xs) >= need else None
    pre = wmed(t0-3600, t0-300); post = wmed(t0+300, t0+3600)
    if pre is None or post is None:
        rows.append(dict(event=eid, series=series, ticker=tk, verdict="UNTESTABLE",
                         note=f"too sparse: {len(q)} min-points in 6h"))
        time.sleep(0.15)
        continue
    jump = post - pre
    # placebo: same +/-60min rolling jump centered at every other 10-min mark,
    # excluding centers within 75min of T0
    plac = []
    m0 = (t0 - 3*3600 + 3600); m0 -= m0 % 600
    m = m0
    while m <= t0 + 3*3600 - 3600:
        if abs(m - t0) > 75*60:
            a = wmed(m-3600, m-300); b = wmed(m+300, m+3600)
            if a is not None and b is not None:
                plac.append(abs(b - a))
        m += 600
    rank = sum(1 for p in plac if p >= abs(jump)) + 1 if plac else None
    rows.append(dict(event=eid, series=series, ticker=tk, verdict="TESTED",
                     jump_c=round(jump*100, 2),
                     n_placebo=len(plac),
                     rank_of_jump=f"{rank}/{len(plac)+1}" if rank else "n/a",
                     note=f"{len(q)} min-points"))

FIELDS = ["event","series","ticker","verdict","jump_c","n_placebo","rank_of_jump","note"]
with open("hidden_files/analysis_real/d23_h2_intraday_results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    w.writeheader(); w.writerows(rows)
tested = [r for r in rows if r["verdict"] == "TESTED"]
print(f"TESTED: {len(tested)}, UNTESTABLE: {len(rows)-len(tested)}")
for r in tested:
    print(r["event"], r["series"], r["ticker"], "jump", r["jump_c"], "rank", r["rank_of_jump"])
