#!/usr/bin/env python3
"""Full-summer pull for the Kalshi event study (2x2 design).

Same candle pipeline as collect_kalshi.py (public REST API, daily candles,
[T-45d, T+10d] windows), but with two upgrades:

  1. Full summer event set: all verified summer 2026 sports events from the
     draft event registry (15 unscheduled + 4 scheduled) PLUS the existing
     macro events.
  2. Historical discovery: for each series, merges live /markets discovery
     (all-statuses pages + explicit status=settled pages) with
     /historical/markets pagination, deduped by ticker. Pre-cutoff
     (2026-07-23) settled markets are historical-DB-only, so the old
     live-only discovery missed June/early-July macro markets.

Outputs go to kalshi_api_data_summer/ so the Sept 18 pull is untouched.

No auth needed — public endpoints only. Polite rate limiting (0.5s) built in.
"""
import csv, json, os, time, sys
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

BASE = "https://api.elections.kalshi.com/trade-api/v2"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kalshi_api_data_summer")
RAW_DIR = os.path.join(OUT_DIR, "raw")
SLEEP = 0.5
PRE_DAYS, POST_DAYS = 45, 10

# (event_id, t0_utc ISO, cell [2x2], detailed category, [series])
# Sports events verified 2026-09-22 from Tier-1 sources; macro events kept
# from the Sept 18 pull. dexter_lawrence_trade dropped (April, outside window).
EVENTS = [
    # --- unscheduled sports: trades ---
    ("myles_garrett_to_rams",  "2026-06-01T17:19:00Z", "unscheduled_sports", "unscheduled_sports_trade",      ["KXSB"]),
    ("aj_brown_to_patriots",   "2026-06-01T20:20:00Z", "unscheduled_sports", "unscheduled_sports_trade",      ["KXSB"]),
    ("giannis_to_heat",        "2026-06-23T03:50:00Z", "unscheduled_sports", "unscheduled_sports_trade",      ["KXNBA"]),
    ("jaylen_brown_to_76ers",  "2026-07-01T22:20:00Z", "unscheduled_sports", "unscheduled_sports_trade",      ["KXNBA"]),
    ("dlo_six_team_trade",     "2026-07-08T00:53:00Z", "unscheduled_sports", "unscheduled_sports_trade",      ["KXNBA"]),
    ("kawhi_to_raptors",       "2026-09-14T18:56:00Z", "unscheduled_sports", "unscheduled_sports_trade",      ["KXNBA"]),
    # --- unscheduled sports: signings ---
    ("mike_conley_to_celtics",       "2026-07-01T14:58:00Z", "unscheduled_sports", "unscheduled_sports_signing", ["KXNBA"]),
    ("mitchell_robinson_to_celtics", "2026-07-01T15:39:00Z", "unscheduled_sports", "unscheduled_sports_signing", ["KXNBA"]),
    ("lebron_to_76ers",              "2026-07-24T20:34:00Z", "unscheduled_sports", "unscheduled_sports_signing", ["KXNBA"]),
    ("von_miller_to_cowboys",        "2026-08-17T01:10:00Z", "unscheduled_sports", "unscheduled_sports_signing", ["KXSB"]),
    # --- unscheduled sports: extensions ---
    ("neemias_queta_extension",  "2026-07-03T13:53:00Z", "unscheduled_sports", "unscheduled_sports_extension", ["KXNBA"]),
    ("donovan_mitchell_extension", "2026-07-07T10:01:00Z", "unscheduled_sports", "unscheduled_sports_extension", ["KXNBA"]),
    ("jordan_walsh_extension",   "2026-07-23T12:27:00Z", "unscheduled_sports", "unscheduled_sports_extension", ["KXNBA"]),
    ("brian_oneill_extension",   "2026-07-28T14:24:00Z", "unscheduled_sports", "unscheduled_sports_extension", ["KXSB"]),
    # --- unscheduled sports: other major roster news ---
    ("aaron_donald_comeback", "2026-08-30T17:00:00Z", "unscheduled_sports", "unscheduled_sports_other", ["KXSB"]),
    # --- scheduled sports ---
    ("nba_schedule_release", "2026-08-13T19:08:00Z", "scheduled_sports", "scheduled_sports", ["KXNBA"]),
    ("nfl_kickoff",          "2026-09-10T00:20:00Z", "scheduled_sports", "scheduled_sports", ["KXSB"]),
    ("nba_opening_night",    "2026-10-20",           "scheduled_sports", "scheduled_sports", ["KXNBA"]),  # future: partial data
    ("nfl_trade_deadline",   "2026-11-10T21:00:00Z", "scheduled_sports", "scheduled_sports", ["KXSB"]),   # future: no data yet
    # --- unscheduled macro (kept from Sept 18 pull) ---
    ("hormuz_retaliation_threat", "2026-09-08", "unscheduled_macro", "unscheduled_macro", ["KXCPI", "KXCPICORE", "KXFED"]),
    ("canada_proclamations",      "2026-09-08", "unscheduled_macro", "unscheduled_macro", ["KXCPI", "KXCPICORE"]),
    ("perim_island_seized",       "2026-09-11", "unscheduled_macro", "unscheduled_macro", ["KXCPI", "KXCPICORE", "KXFED"]),
    ("hormuz_strike_pipeline_shutdown", "2026-09-13", "unscheduled_macro", "unscheduled_macro", ["KXCPI", "KXCPICORE", "KXFED"]),
    ("tariff_eu_threat",      "2026-09-16", "unscheduled_macro", "unscheduled_macro", ["KXFED", "KXCPI", "KXCPICORE"]),
    ("russia_sanctions_bill", "2026-09-16", "unscheduled_macro", "unscheduled_macro", ["KXFED", "KXCPI", "KXCPICORE"]),
    ("trump_truth_fed",       "2026-09-16", "unscheduled_macro", "unscheduled_macro", ["KXFED"]),
    ("nvda_earnings",         "2026-08-26", "unscheduled_macro", "unscheduled_macro", ["KXFED", "KXCPI"]),  # cross-domain/H2
    # --- scheduled macro ---
    ("fomc_sep_hike",         "2026-09-16", "scheduled_macro", "scheduled_macro", ["KXFED"]),
]


def get_json(url, params=None):
    if params:
        url += "?" + urlencode(params)
    for attempt in range(6):
        try:
            req = Request(url, headers={"User-Agent": "kalshi-event-study/1.0"})
            with urlopen(req, timeout=45) as r:
                return json.load(r)
        except HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            if e.code == 404:
                return None
            raise
        except URLError:
            # network blips/timeouts: retry a few times, then let the caller
            # skip this ticker (a single bad ticker must not kill the pull)
            if attempt < 3:
                time.sleep(min(2 ** attempt, 30))
                continue
            raise
        finally:
            time.sleep(SLEEP)


def list_live_markets(series_ticker):
    """Live /markets discovery: all-statuses pages + explicit status=settled pages, deduped."""
    markets = {}
    for status in (None, "settled"):
        cursor = None
        while True:
            params = {"series_ticker": series_ticker, "limit": 200}
            if status:
                params["status"] = status
            if cursor:
                params["cursor"] = cursor
            d = get_json(f"{BASE}/markets", params)
            if not d:
                break
            for m in d.get("markets", []):
                markets[m["ticker"]] = m
            cursor = d.get("cursor")
            if not cursor:
                break
    return markets


def list_historical_markets(series_ticker):
    """Historical-DB discovery for markets settled before the 2026-07-23 cutoff."""
    markets, cursor = {}, None
    while True:
        params = {"series_ticker": series_ticker, "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        d = get_json(f"{BASE}/historical/markets", params)
        if not d:
            break
        for m in d.get("markets", []):
            markets[m["ticker"]] = m
        cursor = d.get("cursor")
        if not cursor:
            break
    return markets


def discover_series_markets(series_ticker):
    """Merge live + historical discovery. Returns {ticker: (market_dict, discovery_source)}."""
    merged = {}
    live = list_live_markets(series_ticker)
    for tk, m in live.items():
        merged[tk] = (m, "live")
    hist = list_historical_markets(series_ticker)
    new_hist = sum(1 for tk in hist if tk not in merged)
    for tk, m in hist.items():
        if tk not in merged:
            merged[tk] = (m, "historical")
    print(f"  {series_ticker}: {len(live)} live + {len(hist)} historical ({new_hist} new), "
          f"{len(merged)} total", flush=True)
    return merged


def get_candles(series_ticker, ticker, start_ts, end_ts):
    """Daily candles; falls back to the historical endpoint for settled markets.

    Never raises: a persistently failing ticker is skipped by the caller and
    logged, so one bad ticker cannot kill a ~600-ticker pull.
    """
    params = {"start_ts": start_ts, "end_ts": end_ts, "period_interval": 1440}
    try:
        d = get_json(f"{BASE}/series/{series_ticker}/markets/{ticker}/candlesticks", params)
    except Exception as e:
        print(f"  !! candle fetch failed (live) for {ticker}: {type(e).__name__}", flush=True)
        d = None
    if d and d.get("candlesticks"):
        return d["candlesticks"], "live"
    try:
        d2 = get_json(f"{BASE}/historical/markets/{ticker}/candlesticks", params)
    except Exception as e:
        print(f"  !! candle fetch failed (historical) for {ticker}: {type(e).__name__}", flush=True)
        d2 = None
    if d2 and d2.get("candlesticks"):
        return d2["candlesticks"], "historical"
    return [], "empty"


def parse_t0(s):
    """'2026-09-16' -> midnight UTC; full ISO with Z handled."""
    if len(s) == 10:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    log = {"events": [], "tickers": {}}
    meta_rows, data_rows = [], []
    candle_cache = {}  # (series, ticker) -> (candles, source)

    # --- discover each series once (not per event) ---
    all_series = sorted({s for _, _, _, _, sl in EVENTS for s in sl})
    print("== discovery phase ==", flush=True)
    discovered = {}
    for series in all_series:
        discovered[series] = discover_series_markets(series)

    # --- per-event window pulls ---
    for event_id, t0_iso, cell, category, series_list in EVENTS:
        t0 = parse_t0(t0_iso)
        start_ts = int((t0 - timedelta(days=PRE_DAYS)).timestamp())
        end_ts = int((t0 + timedelta(days=POST_DAYS)).timestamp())
        ev_log = {"event_id": event_id, "t0_utc": t0_iso, "cell": cell,
                  "category": category, "series": series_list,
                  "tickers": [], "gaps": []}
        print(f"\n== {event_id} ({t0_iso}, {cell}/{category}) ==", flush=True)

        for series in series_list:
            markets = discovered[series]
            # keep markets open at any point in [T-45d, T+10d]
            lo = (t0 - timedelta(days=PRE_DAYS)).isoformat()
            hi = (t0 + timedelta(days=POST_DAYS)).isoformat()
            relevant = [(tk, m, src) for tk, (m, src) in markets.items()
                        if m.get("open_time", "") <= hi and m.get("close_time", "") >= lo]
            print(f"  {series}: {len(markets)} discovered, {len(relevant)} open in window", flush=True)

            for tk, m, dsrc in relevant:
                # cache key must include the window: the same ticker can serve
                # multiple events with different [T-45d, T+10d] windows
                key = (series, tk, start_ts, end_ts)
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
                                      "source": src, "discovery_source": dsrc,
                                      "status": m.get("status"),
                                      "open_time": m.get("open_time"),
                                      "close_time": m.get("close_time")}
                meta_rows.append({
                    "ticker": tk, "series": series, "event_id": event_id,
                    "event_type": cell, "category": category, "t0_utc": t0_iso,
                    "discovery_source": dsrc,
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
