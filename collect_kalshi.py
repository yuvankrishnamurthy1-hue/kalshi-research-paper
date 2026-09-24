#!/usr/bin/env python3
"""Collect Kalshi market data for the 2x2 event study via the public REST API.

For each candidate event, finds every market in the relevant series that was open
during [T-45d, T+10d] and pulls daily candlesticks for that window.

Outputs (in OUT_DIR):
  market_metadata.csv  ticker-level metadata (strikes, open/close times)
  market_data.csv      timestamped quotes in analyze_kalshi.py schema
                       (timestamp, ticker, bid, ask, last, volume, trades, open_interest)
  raw/                 per-ticker raw candle JSON (provenance)
  collection_log.json  what was requested, what came back, coverage gaps

No auth needed — public endpoints only. Polite rate limiting built in.
"""
import csv, json, os, time, sys
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

BASE = "https://api.elections.kalshi.com/trade-api/v2"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kalshi_api_data")
RAW_DIR = os.path.join(OUT_DIR, "raw")
SLEEP = 0.25
PRE_DAYS, POST_DAYS = 45, 10

# (event_id, T=0 date approx, event_type, [series])
EVENTS = [
    ("tariff_eu_threat",      "2026-09-16", "unscheduled_macro", ["KXFED", "KXCPI", "KXCPICORE"]),
    ("russia_sanctions_bill", "2026-09-16", "unscheduled_macro", ["KXFED", "KXCPI", "KXCPICORE"]),
    ("trump_truth_fed",       "2026-09-16", "unscheduled_macro", ["KXFED"]),
    ("hormuz_retaliation_threat", "2026-09-08", "unscheduled_macro", ["KXCPI", "KXCPICORE", "KXFED"]),
    ("perim_island_seized",   "2026-09-11", "unscheduled_macro", ["KXCPI", "KXCPICORE", "KXFED"]),
    ("hormuz_strike_pipeline_shutdown", "2026-09-13", "unscheduled_macro", ["KXCPI", "KXCPICORE", "KXFED"]),
    ("canada_proclamations",  "2026-09-08", "unscheduled_macro", ["KXCPI", "KXCPICORE"]),
    ("nvda_earnings",         "2026-08-26", "unscheduled_macro", ["KXFED", "KXCPI"]),  # cross-domain/H2
    ("fomc_sep_hike",         "2026-09-16", "scheduled_macro",   ["KXFED"]),
    ("nfl_kickoff",           "2026-09-10", "scheduled_sports",  ["KXSB"]),
    ("nba_schedule_release",  "2026-08-14", "scheduled_sports",  ["KXNBA"]),
]


def get_json(url, params=None, retries=3):
    if params:
        url += "?" + urlencode(params)
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "kalshi-event-study/1.0"})
            with urlopen(req, timeout=30) as r:
                return json.load(r)
        except HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            if e.code == 404:
                return None
            raise
        except URLError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        finally:
            time.sleep(SLEEP)


def list_series_markets(series_ticker):
    """All markets in a series (paginated)."""
    markets, cursor = [], None
    while True:
        params = {"series_ticker": series_ticker, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        d = get_json(f"{BASE}/markets", params)
        if not d:
            break
        markets.extend(d.get("markets", []))
        cursor = d.get("cursor")
        if not cursor:
            break
    return markets


def get_candles(series_ticker, ticker, start_ts, end_ts):
    """Daily candles; falls back to the historical endpoint for settled markets."""
    params = {"start_ts": start_ts, "end_ts": end_ts, "period_interval": 1440}
    d = get_json(f"{BASE}/series/{series_ticker}/markets/{ticker}/candlesticks", params)
    if d and d.get("candlesticks"):
        return d["candlesticks"], "live"
    d2 = get_json(f"{BASE}/historical/markets/{ticker}/candlesticks", params)
    if d2 and d2.get("candlesticks"):
        return d2["candlesticks"], "historical"
    return [], "empty"


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    log = {"events": [], "tickers": {}}
    meta_rows, data_rows = [], []
    candle_cache = {}  # (series, ticker) -> (candles, source)

    for event_id, date_s, event_type, series_list in EVENTS:
        t0 = datetime.fromisoformat(date_s).replace(tzinfo=timezone.utc)
        start_ts = int((t0 - timedelta(days=PRE_DAYS)).timestamp())
        end_ts = int((t0 + timedelta(days=POST_DAYS)).timestamp())
        ev_log = {"event_id": event_id, "t0": date_s, "type": event_type,
                  "series": series_list, "tickers": [], "gaps": []}
        print(f"\n== {event_id} ({date_s}, {event_type}) ==", flush=True)

        for series in series_list:
            markets = list_series_markets(series)
            # keep markets open at any point in [T-45d, T+10d]
            lo = (t0 - timedelta(days=PRE_DAYS)).isoformat()
            hi = (t0 + timedelta(days=POST_DAYS)).isoformat()
            relevant = [m for m in markets
                        if m.get("open_time", "") <= hi and m.get("close_time", "") >= lo]
            print(f"  {series}: {len(markets)} listed, {len(relevant)} open in window", flush=True)

            for m in relevant:
                tk = m["ticker"]
                key = (series, tk)
                if key not in candle_cache:
                    raw_path = os.path.join(RAW_DIR, f"{tk}.json")
                    reused = False
                    if os.path.exists(raw_path):
                        try:
                            with open(raw_path) as f:
                                saved = json.load(f)
                            sc = saved.get("candlesticks", [])
                            if sc:
                                lo_ts = min(c["end_period_ts"] for c in sc)
                                hi_ts = max(c["end_period_ts"] for c in sc)
                                if lo_ts <= start_ts and hi_ts >= end_ts:
                                    candle_cache[key] = ([c for c in sc
                                                          if start_ts <= c["end_period_ts"] <= end_ts],
                                                         saved.get("source", "cached"))
                                    reused = True
                        except (json.JSONDecodeError, KeyError):
                            pass
                    if not reused:
                        candles, src = get_candles(series, tk, start_ts, end_ts)
                        candle_cache[key] = (candles, src)
                        with open(raw_path, "w") as f:
                            json.dump({"ticker": tk, "series": series, "source": src,
                                       "candlesticks": candles}, f)
                candles, src = candle_cache[key]
                if not candles:
                    ev_log["gaps"].append(tk)
                    continue
                ev_log["tickers"].append(tk)
                log["tickers"][tk] = {"series": series, "candles": len(candles),
                                      "source": src, "status": m.get("status"),
                                      "open_time": m.get("open_time"),
                                      "close_time": m.get("close_time")}
                meta_rows.append({
                    "ticker": tk, "series": series, "event_id": event_id,
                    "status": m.get("status"), "market_type": m.get("market_type"),
                    "subtitle": m.get("subtitle", ""), "yes_sub_title": m.get("yes_sub_title", ""),
                    "floor_strike": m.get("floor_strike", ""), "cap_strike": m.get("cap_strike", ""),
                    "open_time": m.get("open_time"), "close_time": m.get("close_time"),
                    "candle_source": src, "n_candles": len(candles)})
                for c in candles:
                    bid = (c.get("yes_bid") or {}).get("close_dollars", "")
                    ask = (c.get("yes_ask") or {}).get("close_dollars", "")
                    last = (c.get("price") or {}).get("close_dollars", "")
                    data_rows.append({
                        "timestamp": iso(c["end_period_ts"]), "ticker": tk,
                        "bid": bid, "ask": ask, "last": last,
                        "volume": c.get("volume_fp", ""), "trades": "",
                        "open_interest": c.get("open_interest_fp", "")})
        log["events"].append(ev_log)

    # de-dupe (same ticker can serve multiple events)
    seen = set()
    meta_unique = [r for r in meta_rows if not (r["ticker"], r["event_id"]) in seen
                   and not seen.add((r["ticker"], r["event_id"]))]
    seen2 = set()
    data_unique = [r for r in data_rows if not (r["timestamp"], r["ticker"]) in seen2
                   and not seen2.add((r["timestamp"], r["ticker"]))]

    with open(os.path.join(OUT_DIR, "market_metadata.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(meta_unique[0].keys()))
        w.writeheader(); w.writerows(meta_unique)
    with open(os.path.join(OUT_DIR, "market_data.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "ticker", "bid", "ask",
                                          "last", "volume", "trades", "open_interest"])
        w.writeheader(); w.writerows(data_unique)
    with open(os.path.join(OUT_DIR, "collection_log.json"), "w") as f:
        json.dump(log, f, indent=1)

    n_tk = len(log["tickers"])
    print(f"\nDONE: {n_tk} tickers, {len(data_unique)} candle-rows, "
          f"{sum(len(e['gaps']) for e in log['events'])} gaps", flush=True)
    print(f"wrote {OUT_DIR}/market_data.csv etc.", flush=True)


if __name__ == "__main__":
    main()
