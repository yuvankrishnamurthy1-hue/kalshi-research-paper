"""D23: H2 sports->macro intraday feasibility sweep.
For each of the 15 unscheduled sports events, find the most-active macro
contract (nearest KXFED / KXCPI month) and pull minute candles in [T0-3h, T0+3h].
Reports liquidity + price movement. No conclusions drawn here; analysis next.
"""
import urllib.request, json, csv, calendar, time, datetime

BASE = "https://api.elections.kalshi.com/trade-api/v2"
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "kalshi-research/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def legs(series, month):
    out, cursor = [], ""
    for _ in range(10):
        d = get(f"{BASE}/markets?series_ticker={series}&status=settled&limit=200" +
                (f"&cursor={cursor}" if cursor else ""))
        for m in d.get("markets", []):
            if f"-{month}" in m["ticker"]:
                out.append(m["ticker"])
        cursor = d.get("cursor", "")
        if not cursor:
            break
    return sorted(set(out))

def daily_vol(series, ticker, t0):
    url = (f"{BASE}/series/{series}/markets/{ticker}/candlesticks"
           f"?start_ts={t0-8*86400}&end_ts={t0+86400}&period_interval=1440")
    try:
        cs = get(url).get("candlesticks", [])
        return sum(float(c.get("volume_fp", 0)) for c in cs)
    except Exception:
        return 0.0

def minute_window(series, ticker, t0, hours=3):
    url = (f"{BASE}/series/{series}/markets/{ticker}/candlesticks"
           f"?start_ts={t0-hours*3600}&end_ts={t0+hours*3600}&period_interval=1")
    cs = get(url).get("candlesticks", [])
    return cs

# nearest macro month per event date
def macro_months(ev_date):
    ymd = ev_date[:10]
    fed = "26JUL" if ymd < "2026-07-29" else "26SEP"
    cpi = "26JUL" if ymd < "2026-07-15" else "26AUG"
    return {"KXFED": fed, "KXCPI": cpi}

events = [r for r in csv.DictReader(open("hidden_files/event_registry.csv"))
          if r["cell"] == "unscheduled_sports"]

fed_legs = {"26JUL": legs("KXFED", "26JUL"), "26SEP": legs("KXFED", "26SEP")}
cpi_legs = {"26JUL": legs("KXCPI", "26JUL"), "26AUG": legs("KXCPI", "26AUG")}
print("fed legs:", {k: len(v) for k, v in fed_legs.items()},
      "cpi legs:", {k: len(v) for k, v in cpi_legs.items()}, flush=True)

results = []
for r in events:
    eid = r["event_id"]
    t0 = calendar.timegm(time.strptime(r["t0_utc"], "%Y-%m-%dT%H:%M:%SZ"))
    mm = macro_months(r["t0_utc"])
    for series, month in mm.items():
        legpool = (fed_legs if series == "KXFED" else cpi_legs)[month]
        # most-active leg in the 8 days before T0
        scored = [(daily_vol(series, tk, t0), tk) for tk in legpool]
        scored.sort(reverse=True)
        top_vol, top_tk = scored[0]
        # minute candles +-3h on the most-active leg
        try:
            cs = minute_window(series, top_tk, t0)
        except Exception as e:
            results.append(dict(event=eid, series=series, month=month, ticker=top_tk,
                                err=str(e)[:60]))
            continue
        vols = [float(c.get("volume_fp", 0)) for c in cs]
        mids = []
        spreads = []
        for c in cs:
            try:
                b = float(c["yes_bid"]["close_dollars"]); a = float(c["yes_ask"]["close_dollars"])
                mids.append((a + b) / 2); spreads.append(a - b)
            except Exception:
                pass
        n = len(cs)
        results.append(dict(
            event=eid, series=series, month=month, ticker=top_tk,
            top_leg_8d_vol=round(top_vol, 1),
            n_min=n, min_with_trades=sum(1 for v in vols if v > 0),
            total_vol_6h=round(sum(vols), 1),
            median_spread_c=round(sorted(spreads)[len(spreads)//2]*100, 2) if spreads else None,
            mid_range_c=round((max(mids)-min(mids))*100, 2) if mids else None,
            n_legs_avail=len(legpool),
        ))
        time.sleep(0.15)
    print("done", eid, flush=True)

with open("hidden_files/analysis_real/d23_h2_intraday_sweep.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    w.writeheader(); w.writerows(results)
print("wrote d23_h2_intraday_sweep.csv")
