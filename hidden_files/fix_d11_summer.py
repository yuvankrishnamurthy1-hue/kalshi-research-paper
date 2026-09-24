#!/usr/bin/env python3
"""D11 fix: re-parse the 17 summer tickers whose historical-schema candles were
written price-less (parser read only live keys close_dollars/volume_fp).

For timestamps present in kalshi_api_data_summer/raw/<ticker>.json: re-parse
with the dual-schema reader. Raw files were overwritten by later narrower
fetches, so timestamps missing from raw are re-fetched from the public
Kalshi historical candlestick endpoint (same endpoint the collector uses;
read-only). The CSV is rewritten in place (backup first).
"""
import csv, json, os, shutil, time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = "https://api.elections.kalshi.com/trade-api/v2"
PAPER = "/home/hatch/workspace/kalshi-paper"
SUMMER = os.path.join(PAPER, "kalshi_api_data_summer")
CSV = os.path.join(SUMMER, "market_data.csv")
RAW = os.path.join(SUMMER, "raw")

def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()

def px_field(candle, *paths):
    for path in paths:
        node = candle
        for k in path[:-1]:
            node = node.get(k) if isinstance(node, dict) else None
        v = node.get(path[-1]) if isinstance(node, dict) else None
        if v not in (None, ""):
            return v
    return ""

def parse_candle(c):
    return {
        "bid": px_field(c, ("yes_bid", "close_dollars"), ("yes_bid", "close")),
        "ask": px_field(c, ("yes_ask", "close_dollars"), ("yes_ask", "close")),
        "last": px_field(c, ("price", "close_dollars"), ("price", "close")),
        "volume": c.get("volume_fp", "") or c.get("volume", "") or "",
        "open_interest": c.get("open_interest_fp", "") or c.get("open_interest", "") or "",
    }

def fetch_historical(ticker, start_ts, end_ts):
    params = {"start_ts": start_ts, "end_ts": end_ts, "period_interval": 1440}
    url = f"{BASE}/historical/markets/{ticker}/candlesticks?" + urlencode(params)
    for attempt in range(4):
        try:
            req = Request(url, headers={"User-Agent": "kalshi-event-study/1.0"})
            with urlopen(req, timeout=45) as r:
                d = json.load(r)
            time.sleep(0.5)
            return d.get("candlesticks", [])
        except HTTPError as e:
            if e.code == 404:
                return []
            if e.code in (429, 500, 502, 503) and attempt < 2:
                time.sleep(2 ** attempt); continue
            raise
        except URLError:
            if attempt < 3:
                time.sleep(min(2 ** attempt, 30)); continue
            raise
    return []

def main():
    # 1. backup
    bak = CSV + ".d11_bak"
    shutil.copy2(CSV, bak)
    print("backup ->", bak)

    rows = list(csv.DictReader(open(CSV)))
    print("total rows:", len(rows))

    # 2. identify target rows: empty bid+ask+last
    targets = [r for r in rows if not r["bid"] and not r["ask"] and not r["last"]]
    tickers = sorted({r["ticker"] for r in targets})
    print("price-less rows:", len(targets), "tickers:", len(tickers))

    # 3. build per-ticker parsed cache from raw files
    cache = {}          # (timestamp, ticker) -> fields
    need_fetch = {}     # ticker -> list of missing timestamps
    for t in tickers:
        f = os.path.join(RAW, f"{t}.json")
        d = json.load(open(f))
        for c in d.get("candlesticks", []):
            cache[(iso(c["end_period_ts"]), t)] = parse_candle(c)
        missing = [r["timestamp"] for r in targets
                   if r["ticker"] == t and (r["timestamp"], t) not in cache]
        need_fetch[t] = missing
        print(f"{t}: raw covers {sum(1 for k in cache if k[1]==t)}, missing {len(missing)}")

    # 4. re-fetch missing timestamps from the historical endpoint
    for t, mts in need_fetch.items():
        if not mts:
            continue
        days = sorted({m[:10] for m in mts})
        # fetch in one contiguous range covering all missing days
        start = datetime.fromisoformat(days[0]).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(days[-1]).replace(tzinfo=timezone.utc)
        start_ts = int(start.timestamp()) - 86400
        end_ts = int(end.timestamp()) + 2 * 86400
        print(f"fetch {t}: {days[0]} -> {days[-1]}")
        for c in fetch_historical(t, start_ts, end_ts):
            key = (iso(c["end_period_ts"]), t)
            if key not in cache:
                cache[key] = parse_candle(c)

    # 5. rewrite rows in place
    fixed, still_empty = 0, []
    for r in rows:
        if r["bid"] or r["ask"] or r["last"]:
            continue
        f = cache.get((r["timestamp"], r["ticker"]))
        if f and (f["bid"] or f["ask"] or f["last"]):
            r["bid"], r["ask"], r["last"] = f["bid"], f["ask"], f["last"]
            r["volume"], r["open_interest"] = f["volume"], f["open_interest"]
            fixed += 1
        else:
            still_empty.append((r["timestamp"], r["ticker"]))

    with open(CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "ticker", "bid", "ask",
                                          "last", "volume", "trades", "open_interest"])
        w.writeheader(); w.writerows(rows)

    print(f"fixed: {fixed}, still price-less: {len(still_empty)}")
    for s in still_empty[:20]:
        print("  STILL EMPTY:", s)

    # 6. verify
    rows2 = list(csv.DictReader(open(CSV)))
    rem = [r for r in rows2 if not r["bid"] and not r["ask"] and not r["last"]]
    print("VERIFY: total rows:", len(rows2), "| price-less rows:", len(rem))
    assert len(rows2) == len(rows), "row count changed!"
    return rem

if __name__ == "__main__":
    main()
