"""Coverage audit for the Kalshi summer pull. Run: python3 hidden_files/coverage_audit.py"""
import csv, json
from datetime import datetime, timedelta
from collections import defaultdict

BASE = 'kalshi_api_data_summer/'
log = json.load(open(BASE + 'collection_log.json'))
meta_rows = list(csv.DictReader(open(BASE + 'market_metadata.csv')))
data_rows = list(csv.DictReader(open(BASE + 'market_data.csv')))

def t0d(e):
    s = e['t0_utc']
    return datetime.fromisoformat(s.replace('Z', '+00:00')).date()

# ticker -> set of events (from metadata)
ticker_events = defaultdict(set)
for m in meta_rows:
    ticker_events[m['ticker']].add(m['event_id'])

multi = {t: evs for t, evs in ticker_events.items() if len(evs) > 1}

# data coverage per (ticker)
data_by_ticker = defaultdict(list)
for r in data_rows:
    data_by_ticker[r['ticker']].append(r['timestamp'][:10])

print("=== OVERALL ===")
print(f"events={len(log['events'])} tickers_in_log={len(log['tickers'])} "
      f"meta_rows={len(meta_rows)} data_rows={len(data_rows)}")
print(f"tickers appearing in >1 event: {len(multi)}")
for t, evs in sorted(multi.items()):
    print(f"  {t}: {sorted(evs)}")

print("\n=== PER EVENT ===")
print(f"{'event':32s} {'cell':19s} {'tick':>4s} {'rows':>6s} {'min_d':>10s} {'max_d':>10s} "
      f"{'win_start':>10s} {'win_end':>10s} {'pre_cov':>7s} {'post_cov':>8s} {'gaps':>4s} srcs")
for e in sorted(log['events'], key=t0d):
    eid = e['event_id']
    tickers = e['tickers']
    w0, w1 = t0d(e) - timedelta(days=45), t0d(e) + timedelta(days=10)
    alld, rows = [], 0
    srcs = set()
    for t in tickers:
        alld += data_by_ticker.get(t, [])
        rows += len(data_by_ticker.get(t, []))
        srcs |= {m['discovery_source'] for m in meta_rows if m['ticker'] == t and m['event_id'] == eid}
    gaps = len(e.get('gaps', []))
    if alld:
        mind, maxd = min(alld), max(alld)
        pre = sum(1 for d in set(alld) if w0.isoformat() <= d <= t0d(e).isoformat())
        post = sum(1 for d in set(alld) if t0d(e).isoformat() < d <= w1.isoformat())
        print(f"{eid:32s} {e['cell']:19s} {len(tickers):4d} {rows:6d} {mind:>10s} {maxd:>10s} "
              f"{w0.isoformat():>10s} {w1.isoformat():>10s} {pre:3d}/45 {post:3d}/10 {gaps:4d} {','.join(sorted(srcs))}")
    else:
        print(f"{eid:32s} {e['cell']:19s} {len(tickers):4d} {rows:6d} {'NO DATA':>10s} {'':>10s} "
              f"{w0.isoformat():>10s} {w1.isoformat():>10s} {'':>7s} {'':>8s} {gaps:4d}")

print("\n=== SERIES x DISCOVERY SOURCE ===")
by = defaultdict(int)
for m in meta_rows:
    by[(m['series'], m['discovery_source'])] += 1
for k in sorted(by):
    print(f"  {k[0]:10s} {k[1]:12s} {by[k]:4d} tickers")

print("\n=== CANDLE SOURCE (live vs historical) ===")
by2 = defaultdict(int)
for m in meta_rows:
    by2[m['candle_source']] += 1
for k in sorted(by2):
    print(f"  {k:12s} {by2[k]:4d}")

print("\n=== ZERO-ROW TICKERS (in log but no candles) ===")
zero = [t for t, v in log['tickers'].items() if v.get('candles', 0) == 0]
print(f"  count={len(zero)}")
for t in zero[:20]:
    print(f"  {t}")
