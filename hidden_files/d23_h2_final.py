"""D23 final: standardized T0 jump for the 6 liquid event x macro-contract pairs.
Metric: median(mid in [T0+5min, T0+60min]) - median(mid in [T0-60min, T0-5min]).
Also reports one-sample t-test of jumps vs 0 (exploratory; n=6).
"""
import urllib.request, json, csv, calendar, time
import statistics as st

BASE = "https://api.elections.kalshi.com/trade-api/v2"
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "kalshi-research/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))

pairs = [
    ("giannis_to_heat",      "2026-06-23T03:50:00Z", "KXFED", "KXFED-26JUL-T3.75"),  # thin: check
    ("dlo_six_team_trade",   "2026-07-08T00:53:00Z", "KXFED", "KXFED-26JUL-T3.75"),
    ("kawhi_to_raptors",     "2026-09-14T18:56:00Z", "KXFED", "KXFED-26SEP-T3.75"),
    ("neemias_queta_extension","2026-07-03T13:53:00Z","KXFED","KXFED-26JUL-T3.75"),
    ("jordan_walsh_extension","2026-07-23T12:27:00Z", "KXFED", "KXFED-26JUL-T3.50"),
    ("brian_oneill_extension","2026-07-28T14:24:00Z", "KXFED", "KXFED-26JUL-T3.75"),
    ("aaron_donald_comeback","2026-08-30T17:00:00Z", "KXFED", "KXFED-26SEP-T3.75"),
]
rows = []
for eid, t0s, series, tk in pairs:
    t0 = calendar.timegm(time.strptime(t0s, "%Y-%m-%dT%H:%M:%SZ"))
    url = (f"{BASE}/series/{series}/markets/{tk}/candlesticks"
           f"?start_ts={t0-3*3600}&end_ts={t0+3*3600}&period_interval=1")
    cs = get(url).get("candlesticks", [])
    pts = []
    for c in cs:
        try:
            b = float(c["yes_bid"]["close_dollars"]); a = float(c["yes_ask"]["close_dollars"])
            pts.append((c["end_period_ts"], (a + b) / 2, float(c.get("volume_fp", 0))))
        except Exception:
            pass
    pre = [m for ts, m, v in pts if t0-3600 <= ts <= t0-300]
    post = [m for ts, m, v in pts if t0+300 <= ts <= t0+3600]
    vol = sum(v for ts, m, v in pts)
    if len(pre) >= 3 and len(post) >= 3:
        jump = st.median(post) - st.median(pre)
        rows.append(dict(event=eid, ticker=tk, n_pre=len(pre), n_post=len(post),
                         vol_6h=round(vol, 1), jump_c=round(jump*100, 2),
                         verdict="TESTED"))
    else:
        rows.append(dict(event=eid, ticker=tk, n_pre=len(pre), n_post=len(post),
                         vol_6h=round(vol, 1), jump_c="",
                         verdict="TOO_SPARSE"))
    time.sleep(0.2)

with open("hidden_files/analysis_real/d23_h2_final.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

tested = [float(r["jump_c"]) for r in rows if r["verdict"] == "TESTED"]
print(f"TESTED n={len(tested)}")
for r in rows:
    print(r["event"][:26], r["verdict"], r["jump_c"], f"vol={r['vol_6h']}")
if len(tested) >= 2:
    mean = st.mean(tested); sd = st.stdev(tested) if len(tested) > 1 else 0
    t = mean / (sd / (len(tested) ** 0.5)) if sd > 0 else 0.0
    print(f"mean jump = {mean:.2f}c, sd = {sd:.2f}c, t = {t:.2f} (one-sample vs 0)")
