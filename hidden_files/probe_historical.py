#!/usr/bin/env python3
"""Probe: historical market discovery for the whole-summer expansion.

Tests:
 1. GET /historical/cutoff                    -> live vs historical boundary
 2. GET /historical/markets?series_ticker=... -> settled-market discovery for June+
 3. GET /markets?series_ticker=...&status=settled -> live settled discovery
 4. Small sample: metadata + daily candles for ~6 June-settled tickers

Polite: 0.5s between calls. No auth.
"""
import json, time, sys
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

BASE = "https://api.elections.kalshi.com/trade-api/v2"
SLEEP = 0.5
OUT = {}

def get_json(url, params=None, retries=2):
    if params:
        url += "?" + urlencode(params)
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "kalshi-event-study/1.0"})
            with urlopen(req, timeout=30) as r:
                return json.load(r), None
        except HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None, f"HTTP {e.code}"
        except URLError as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None, f"URL error: {e}"
        finally:
            time.sleep(SLEEP)
    return None, "retries exhausted"

def ts(s):
    return datetime.fromtimestamp(s, timezone.utc).strftime("%Y-%m-%d")

print("== 1. /historical/cutoff ==")
d, err = get_json(f"{BASE}/historical/cutoff")
if err:
    print("  ERROR:", err); OUT["cutoff"] = {"error": err}
else:
    OUT["cutoff"] = d
    for k, v in d.items():
        try:
            print(f"  {k}: {v} ({ts(v)})")
        except Exception:
            print(f"  {k}: {v}")

SERIES = ["KXCPI", "KXNBA", "KXSB", "KXFED", "KXCPICORE"]

print("\n== 2. /historical/markets?series_ticker=X (first page, limit 5) ==")
OUT["historical_markets"] = {}
for s in SERIES:
    d, err = get_json(f"{BASE}/historical/markets", {"series_ticker": s, "limit": 5})
    if err:
        print(f"  {s}: ERROR {err}"); OUT["historical_markets"][s] = {"error": err}
        continue
    mkts = d.get("markets", [])
    cursor = d.get("cursor")
    OUT["historical_markets"][s] = {
        "n_returned": len(mkts),
        "has_more_pages": bool(cursor),
        "sample_tickers": [m.get("ticker") for m in mkts[:5]],
        "sample_fields": sorted(mkts[0].keys()) if mkts else [],
        "sample_statuses": sorted({m.get("status") for m in mkts}),
    }
    print(f"  {s}: {len(mkts)} markets, more_pages={bool(cursor)}")
    for m in mkts[:3]:
        print(f"    {m.get('ticker')} status={m.get('status')} "
              f"open={m.get('open_time','')[:10]} close={m.get('close_time','')[:10]}")

print("\n== 3. /markets?series_ticker=X&status=settled (live settled discovery) ==")
OUT["live_settled"] = {}
for s in SERIES:
    d, err = get_json(f"{BASE}/markets", {"series_ticker": s, "status": "settled", "limit": 5})
    if err:
        print(f"  {s}: ERROR {err}"); OUT["live_settled"][s] = {"error": err}
        continue
    mkts = d.get("markets", [])
    OUT["live_settled"][s] = {
        "n_returned": len(mkts),
        "has_more_pages": bool(d.get("cursor")),
        "sample_tickers": [m.get("ticker") for m in mkts[:5]],
    }
    print(f"  {s}: {len(mkts)} settled markets, more_pages={bool(d.get('cursor'))}")
    for m in mkts[:3]:
        print(f"    {m.get('ticker')} close={m.get('close_time','')[:10]}")

print("\n== 4. sample: June-2026 settled tickers -> metadata + daily candles ==")
# pull up to ~30 historical markets per series to find June-settled ones
june_tickers = []
for s in ["KXCPI", "KXNBA", "KXSB"]:
    d, err = get_json(f"{BASE}/historical/markets", {"series_ticker": s, "limit": 30})
    if err or not d:
        print(f"  {s}: ERROR {err}"); continue
    for m in d.get("markets", []):
        ct = m.get("close_time", "")
        if ct.startswith("2026-06"):
            june_tickers.append((s, m["ticker"], ct[:10]))
            if len(june_tickers) >= 8:
                break
    if len(june_tickers) >= 8:
        break

print(f"  found {len(june_tickers)} June-settled tickers")
OUT["june_sample"] = []
for s, tk, close_d in june_tickers[:6]:
    meta, merr = get_json(f"{BASE}/historical/markets/{tk}")
    start = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
    end = int(datetime(2026, 7, 5, tzinfo=timezone.utc).timestamp())
    cd, cerr = get_json(f"{BASE}/historical/markets/{tk}/candlesticks",
                        {"start_ts": start, "end_ts": end, "period_interval": 1440})
    n_candles = len(cd.get("candlesticks", [])) if cd else 0
    ok = merr is None and cerr is None and n_candles > 0
    print(f"  {tk}: meta={'OK' if merr is None else merr}, "
          f"candles={n_candles} ({'OK' if ok else 'FAIL ' + str(cerr)})")
    OUT["june_sample"].append({
        "series": s, "ticker": tk, "close_date": close_d,
        "meta_ok": merr is None,
        "n_candles_jun1_jul5": n_candles,
        "candle_error": cerr,
        "sample_close_cents": (cd.get("candlesticks", [{}])[0].get("price", {}).get("close_dollars")
                               if n_candles else None),
    })

with open("/tmp/probe_historical_out.json", "w") as f:
    json.dump(OUT, f, indent=1)
print("\nWrote /tmp/probe_historical_out.json")
