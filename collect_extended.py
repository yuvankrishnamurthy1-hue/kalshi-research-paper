#!/usr/bin/env python3
"""Extended pull for the Kalshi event study: H2 cross-domain, CPI 2026-09-11,
new scheduled sports, and supplementary scheduled macro back to 2026-01-01.

Same candle pipeline as collect_kalshi_summer.py (public REST API, daily
candles, [T-45d, T+10d] windows). Differences:

  * OUT_DIR = kalshi_api_data_extended/ (summer pull untouched).
  * EVENTS entries are 6-tuples with an opts dict supporting selection:
      - {"select": "top_volume", "top_n": 8}: fetch every ticker open in the
        window, keep the top_n by summed window volume (H2 sports baskets).
      - {"select": "nearest_expiry", "n_per_series": 2}: from market metadata
        alone, keep the n_per_series contracts per series whose close_time is
        nearest at-or-after T0 (H2 macro contracts for sports events).
      - {"ticker_contains": "26AUG"}: keep only tickers containing the
        substring (release-specific CPI / meeting-specific FOMC contracts).
  * Raw candle cache: checks kalshi_api_data_extended/raw/ first, then falls
    back to kalshi_api_data_summer/raw/ (same [T-45d, T+10d] windows, so
    overlapping events reuse the summer pull's candles without refetching).
  * Per-ticker progress prints (unbuffered) so stalls are visible in the log.

Batches:
  A. H2 cross-domain falsification: 8 unscheduled_macro events x sports
     basket (KXNBA+KXSB, top 8 by volume); 15 unscheduled_sports events x
     macro contracts (KXFED+KXCPI, 2 nearest-expiry per series).
  B. CPI August release 2026-09-11 12:30 UTC (prereg-mandated, never
     registered): KXCPI+KXCPICORE August contracts, scheduled_macro.
  C. New scheduled sports: 2026 NBA draft lottery (~2026-05-11, approx),
     2026 NBA draft (2026-06-24), 2026 MLB All-Star Game (~2026-07-14,
     approx). Lottery/draft -> KXNBA; All-Star -> KXMLB (World Series
     futures; exists on Kalshi).
  D. Supplementary scheduled macro back to 2026-01-01: FOMC decisions
     (KXFED, meeting-specific tickers) and CPI releases (KXCPI+KXCPICORE,
     release-month tickers). Old candles may not exist; gaps are logged.

No auth needed - public endpoints only. Polite rate limiting (0.5s).
"""
import csv, json, os, time, sys
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

BASE = "https://api.elections.kalshi.com/trade-api/v2"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "kalshi_api_data_extended")
RAW_DIR = os.path.join(OUT_DIR, "raw")
SUMMER_RAW_DIR = os.path.join(HERE, "kalshi_api_data_summer", "raw")
SLEEP = 0.5
PRE_DAYS, POST_DAYS = 45, 10

# (event_id, t0_utc ISO, cell, category, [series], opts)
# T0s for macro/sports events taken from hidden_files/event_registry.csv
# (corrected values). Batch C sports dates approx (web search unavailable at
# pull time - flagged in pull report). Batch D dates derived from Kalshi's
# own market close_time metadata (KXFED/KXCPI/KXCPICORE).
EVENTS = [
    # ---- A1: unscheduled macro events -> sports basket (top 8 by volume) ----
    ("hormuz_retaliation_threat_xd", "2026-09-07T13:53:00Z", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], {"select": "top_volume", "top_n": 8}),
    ("canada_proclamations_xd", "2026-09-08", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], {"select": "top_volume", "top_n": 8}),
    ("hormuz_strike_pipeline_shutdown_xd", "2026-09-10", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], {"select": "top_volume", "top_n": 8}),
    ("perim_island_seized_xd", "2026-09-11", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], {"select": "top_volume", "top_n": 8}),
    ("tariff_eu_threat_xd", "2026-09-16", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], {"select": "top_volume", "top_n": 8}),
    ("russia_sanctions_bill_xd", "2026-09-16", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], {"select": "top_volume", "top_n": 8}),
    ("trump_truth_fed_xd", "2026-09-16", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], {"select": "top_volume", "top_n": 8}),
    ("nvda_earnings_xd", "2026-08-26", "unscheduled_macro",
     "crossdomain_sports_basket", ["KXNBA", "KXSB"], {"select": "top_volume", "top_n": 8}),
    # ---- A2: unscheduled sports events -> macro contracts (nearest expiry) ----
    ("myles_garrett_to_rams_xd", "2026-06-01T17:19:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("aj_brown_to_patriots_xd", "2026-06-01T20:20:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("giannis_to_heat_xd", "2026-06-23T03:50:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("jaylen_brown_to_76ers_xd", "2026-07-01T22:20:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("mike_conley_to_celtics_xd", "2026-07-01T14:58:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("mitchell_robinson_to_celtics_xd", "2026-07-01T15:39:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("neemias_queta_extension_xd", "2026-07-03T13:53:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("donovan_mitchell_extension_xd", "2026-07-07T10:01:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("dlo_six_team_trade_xd", "2026-07-08T00:53:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("jordan_walsh_extension_xd", "2026-07-23T12:27:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("lebron_to_76ers_xd", "2026-07-24T20:34:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("brian_oneill_extension_xd", "2026-07-28T14:24:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("von_miller_to_cowboys_xd", "2026-08-17T01:10:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("aaron_donald_comeback_xd", "2026-08-30T17:00:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    ("kawhi_to_raptors_xd", "2026-09-14T18:56:00Z", "unscheduled_sports",
     "crossdomain_macro_contracts", ["KXFED", "KXCPI"], {"select": "nearest_expiry", "n_per_series": 2}),
    # ---- B: August CPI release (prereg-mandated, never registered) ----
    ("cpi_aug_release", "2026-09-11T12:30:00Z", "scheduled_macro",
     "scheduled_macro", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26AUG"}),
    # ---- C: new scheduled sports (lottery/ASG dates approx; search was down) ----
    ("nba_draft_lottery_2026", "2026-05-11", "scheduled_sports",
     "scheduled_sports", ["KXNBA"], {}),
    ("nba_draft_2026", "2026-06-24", "scheduled_sports",
     "scheduled_sports", ["KXNBA"], {}),
    ("mlb_allstar_2026", "2026-07-14", "scheduled_sports",
     "scheduled_sports", ["KXMLB"], {}),
    # ---- D: supplementary scheduled macro back to 2026-01-01 ----
    # FOMC decision dates from KXFED close_time metadata; T0 = 18:00 UTC
    # (~2pm ET announcement). 2026-09-16 already pulled (fomc_sep_hike);
    # Oct/Dec meetings are future - excluded.
    ("fomc_2026_01_supp", "2026-01-28T18:00:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXFED"], {"ticker_contains": "26JAN"}),
    ("fomc_2026_03_supp", "2026-03-18T18:00:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXFED"], {"ticker_contains": "26MAR"}),
    ("fomc_2026_04_supp", "2026-04-29T18:00:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXFED"], {"ticker_contains": "26APR"}),
    ("fomc_2026_06_supp", "2026-06-17T18:00:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXFED"], {"ticker_contains": "26JUN"}),
    ("fomc_2026_07_supp", "2026-07-29T18:00:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXFED"], {"ticker_contains": "26JUL"}),
    # CPI release dates from KXCPI/KXCPICORE close_time metadata;
    # T0 = 12:30 UTC (8:30am ET). ticker substring = reference month.
    ("cpi_2026_01_supp", "2026-01-13T12:30:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXCPI", "KXCPICORE"], {"ticker_contains": "25DEC"}),
    ("cpi_2026_02_supp", "2026-02-13T12:30:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26JAN"}),
    ("cpi_2026_03_supp", "2026-03-11T12:30:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26FEB"}),
    ("cpi_2026_04_supp", "2026-04-10T12:30:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26MAR"}),
    ("cpi_2026_05_supp", "2026-05-12T12:30:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26APR"}),
    ("cpi_2026_06_supp", "2026-06-10T12:30:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26MAY"}),
    ("cpi_2026_07_supp", "2026-07-14T12:30:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26JUN"}),
    ("cpi_2026_08_supp", "2026-08-12T12:30:00Z", "scheduled_macro",
     "scheduled_macro_supplementary", ["KXCPI", "KXCPICORE"], {"ticker_contains": "26JUL"}),
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
            if attempt < 3:
                time.sleep(min(2 ** attempt, 30))
                continue
            raise
        finally:
            time.sleep(SLEEP)


def list_live_markets(series_ticker):
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


def window_volume(candles):
    s = 0.0
    for c in candles:
        try:
            s += float(c.get("volume_fp") or 0)
        except (TypeError, ValueError):
            pass
    return s


def select_top_volume(fetched, top_n):
    """fetched: list of dicts with 'ticker' and 'candles'. Returns (kept, dropped)."""
    ranked = sorted(fetched, key=lambda f: window_volume(f["candles"]), reverse=True)
    return ranked[:top_n], ranked[top_n:]


def select_nearest_expiry(relevant, t0, n_per_series):
    """relevant: [(ticker, market, dsrc)] for ONE series. Keep the n_per_series
    contracts with close_time nearest at-or-after t0 (contracts live at the
    event could react); fill with most-recently-expired if short."""
    t0s = t0.isoformat()
    live = sorted([x for x in relevant if x[1].get("close_time", "") >= t0s],
                  key=lambda x: x[1].get("close_time", ""))
    expired = sorted([x for x in relevant if x[1].get("close_time", "") < t0s],
                     key=lambda x: x[1].get("close_time", ""), reverse=True)
    return (live + expired)[:n_per_series]


def px_field(candle, *paths):
    """Extract a price/volume field across both Kalshi candle schemas.

    The live candlestick endpoint uses close_dollars / volume_fp /
    open_interest_fp; the historical endpoint uses close / volume /
    open_interest. Missing keys or JSON nulls become "".
    """
    for path in paths:
        node = candle
        for k in path[:-1]:
            node = node.get(k) if isinstance(node, dict) else None
        v = node.get(path[-1]) if isinstance(node, dict) else None
        if v not in (None, ""):
            return v
    return ""


def parse_t0(s):
    if len(s) == 10:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def load_cached_candles(ticker, start_ts, end_ts):
    """Check extended raw dir, then summer raw dir, for candles covering the
    full window. Returns (candles, source) or None."""
    for raw_dir in (RAW_DIR, SUMMER_RAW_DIR):
        raw_path = os.path.join(raw_dir, f"{ticker}.json")
        if not os.path.exists(raw_path):
            continue
        try:
            with open(raw_path) as f:
                saved = json.load(f)
            sc = saved.get("candlesticks", [])
            if not sc:
                continue
            lo_ts = min(c["end_period_ts"] for c in sc)
            hi_ts = max(c["end_period_ts"] for c in sc)
            if lo_ts <= start_ts and hi_ts >= end_ts:
                return ([c for c in sc if start_ts <= c["end_period_ts"] <= end_ts],
                        saved.get("source", "cached") + "+reused")
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return None


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    log = {"run": "extended", "events": [], "tickers": {}}
    meta_rows, data_rows = [], []
    candle_cache = {}

    all_series = sorted({s for _, _, _, _, sl, _ in EVENTS for s in sl})
    print("== discovery phase ==", flush=True)
    discovered = {}
    for series in all_series:
        discovered[series] = discover_series_markets(series)

    for event_id, t0_iso, cell, category, series_list, opts in EVENTS:
        t0 = parse_t0(t0_iso)
        start_ts = int((t0 - timedelta(days=PRE_DAYS)).timestamp())
        end_ts = int((t0 + timedelta(days=POST_DAYS)).timestamp())
        ev_log = {"event_id": event_id, "t0_utc": t0_iso, "cell": cell,
                  "category": category, "series": series_list, "opts": opts,
                  "tickers": [], "gaps": [], "deselected": []}
        print(f"\n== {event_id} ({t0_iso}, {cell}/{category}) ==", flush=True)

        sel = opts.get("select")
        for series in series_list:
            markets = discovered[series]
            lo = (t0 - timedelta(days=PRE_DAYS)).isoformat()
            hi = (t0 + timedelta(days=POST_DAYS)).isoformat()
            relevant = [(tk, m, src) for tk, (m, src) in markets.items()
                        if m.get("open_time", "") <= hi and m.get("close_time", "") >= lo]
            if opts.get("ticker_contains"):
                relevant = [x for x in relevant if opts["ticker_contains"] in x[0]]
            if sel == "nearest_expiry":
                relevant = select_nearest_expiry(relevant, t0, opts.get("n_per_series", 2))
            print(f"  {series}: {len(relevant)} candidate tickers", flush=True)

            fetched = []
            for tk, m, dsrc in relevant:
                key = (series, tk, start_ts, end_ts)
                if key not in candle_cache:
                    hit = load_cached_candles(tk, start_ts, end_ts)
                    if hit is not None:
                        candle_cache[key] = hit
                    else:
                        candles, src = get_candles(series, tk, start_ts, end_ts)
                        candle_cache[key] = (candles, src)
                        with open(os.path.join(RAW_DIR, f"{tk}.json"), "w") as f:
                            json.dump({"ticker": tk, "series": series, "source": src,
                                       "candlesticks": candles}, f)
                candles, src = candle_cache[key]
                fetched.append({"ticker": tk, "market": m, "dsrc": dsrc,
                                "candles": candles, "src": src})
                print(f"    {tk}: {len(candles)} candles ({src})", flush=True)

            if sel == "top_volume":
                kept, dropped = select_top_volume(fetched, opts.get("top_n", 8))
                ev_log["deselected"].extend(
                    [{"ticker": f["ticker"], "series": series,
                      "window_volume": round(window_volume(f["candles"]), 2)}
                     for f in dropped])
                print(f"  {series}: kept top {len(kept)}/{len(fetched)} by window volume: "
                      f"{[f['ticker'] for f in kept]}", flush=True)
                fetched = kept

            for f in fetched:
                tk, m, dsrc, candles, src = f["ticker"], f["market"], f["dsrc"], f["candles"], f["src"]
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
                    bid = px_field(c, ("yes_bid", "close_dollars"), ("yes_bid", "close"))
                    ask = px_field(c, ("yes_ask", "close_dollars"), ("yes_ask", "close"))
                    last = px_field(c, ("price", "close_dollars"), ("price", "close"))
                    vol = c.get("volume_fp", "") or c.get("volume", "")
                    if vol is None:
                        vol = ""
                    oi = c.get("open_interest_fp", "") or c.get("open_interest", "")
                    if oi is None:
                        oi = ""
                    data_rows.append({
                        "timestamp": iso(c["end_period_ts"]), "ticker": tk,
                        "bid": bid, "ask": ask, "last": last,
                        "volume": vol, "trades": "",
                        "open_interest": oi})
        log["events"].append(ev_log)

    seen = set()
    meta_unique = [r for r in meta_rows if not (r["ticker"], r["event_id"]) in seen
                   and not seen.add((r["ticker"], r["event_id"]))]
    seen2 = set()
    data_unique = [r for r in data_rows if not (r["timestamp"], r["ticker"]) in seen2
                   and not seen2.add((r["timestamp"], r["ticker"]))]

    meta_fields = ["ticker", "series", "event_id", "event_type", "category",
                   "t0_utc", "discovery_source", "status", "market_type",
                   "subtitle", "yes_sub_title", "floor_strike", "cap_strike",
                   "open_time", "close_time", "candle_source", "n_candles"]
    with open(os.path.join(OUT_DIR, "market_metadata.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=meta_fields)
        w.writeheader()
        w.writerows(meta_unique)
    with open(os.path.join(OUT_DIR, "market_data.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "ticker", "bid", "ask",
                                          "last", "volume", "trades", "open_interest"])
        w.writeheader()
        w.writerows(data_unique)
    with open(os.path.join(OUT_DIR, "collection_log.json"), "w") as f:
        json.dump(log, f, indent=1)

    n_tk = len(log["tickers"])
    print(f"\nDONE: {n_tk} tickers, {len(data_unique)} candle-rows, "
          f"{sum(len(e['gaps']) for e in log['events'])} gaps, "
          f"{sum(len(e['deselected']) for e in log['events'])} deselected", flush=True)
    print(f"wrote {OUT_DIR}/market_data.csv etc.", flush=True)


if __name__ == "__main__":
    main()
