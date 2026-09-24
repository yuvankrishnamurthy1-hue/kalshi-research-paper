# Historical discovery report — whole-summer expansion

**Date:** 2026-09-21
**Author:** subagent (for parent agent / Dash)
**Goal:** determine how to discover settled/expired Kalshi markets from 2026-06-01 onward, which the current `collect_kalshi.py` misses (it only pages `GET /markets?series_ticker=...` with no status handling).

## Current coverage (from `kalshi_api_data/collection_log.json`)

- Sept 18 pull: 474 tickers, 10,582 daily candle rows, 6 gaps.
- Discovery was `GET /markets?series_ticker=X` (no `status` param), filtered client-side to markets open during each event's [T−45, T+10] window.
- Per the OpenAPI spec, **markets that settled before the historical cutoff are NOT returned by `/markets` at all** — they live only in `/historical/markets`. This is the gap for June/early-July 2026.

## What I verified today (all via public API, no auth, 0.5s spacing, no 429s)

### 1. The cutoff: `GET /historical/cutoff`

```
market_settled_ts: 2026-07-23T00:00:00Z   <- the boundary that matters
trades_created_ts: 2026-07-23T00:00:00Z
orders_updated_ts: 2026-07-23T00:00:00Z
market_positions_last_updated_ts: 2026-07-23T00:00:00Z
```

Anything settled **before 2026-07-23** (e.g. KXCPI-26JUN closed 2026-07-14, KXFED-26JUN closed 2026-06-17) is historical-DB-only. Anything settled after is in the live `/markets` endpoint.

### 2. Historical discovery works: `GET /historical/markets?series_ticker=X`

- Returns paginated markets with `status: "finalized"` (not "settled" — label differs), full `open_time`/`close_time`, strikes, etc.
- Filters are **mutually exclusive**: `tickers` | `event_ticker` | `series_ticker` — use `series_ticker` + paginate.
- **No server-side date filters** — filter client-side by `open_time <= window_end && close_time >= window_start` (same as current code).
- Total historical inventory is small — one page each (limit=1000):

| Series | Historical markets |
|---|---|
| KXCPI | 483 |
| KXCPICORE | 434 |
| KXFED | 391 |
| KXNBA | 60 |
| KXSB | 36 |
| **Total** | **1,404** |

### 3. Live settled discovery works: `GET /markets?series_ticker=X&status=settled`

- KXCPI / KXFED / KXCPICORE returned settled markets (e.g. KXCPI-26AUG closed 2026-09-11, KXFED-26SEP closed 2026-09-16), paginated.
- KXNBA / KXSB returned **0 settled** — their championship futures for the current season are still `open` (live). Correct behavior, not a bug.
- Spec also supports `min_settled_ts`/`max_settled_ts` combined with `status=settled` if we want server-side date bounding.

### 4. Historical candles work — validated on 6 June-settled tickers

Sampled KXCPI-26MAY-T-0.3 / -0.2 / T1.0 / T0.9 / T0.8 / T0.7 (closed 2026-06-10, i.e. settled before cutoff):

- `GET /historical/markets/{ticker}` → metadata OK for all 6.
- `GET /historical/markets/{ticker}/candlesticks?period_interval=1440` for 2026-06-01→2026-07-05 → 5–11 daily candles each (thin because the contracts closed June 10; candles only exist while the market was open — expected).
- The collector's existing `get_candles()` live→historical fallback logic already handles this path correctly.

### 5. Bonus: batch candle endpoint exists

`GET /markets/candlesticks?market_tickers=...` — up to 100 tickers, 10,000 candles per call. Could cut live-ticker pull time ~50x. **Unverified for archived tickers** — assume live-only; keep the per-ticker fallback for anything the batch call misses.

## What we CAN'T do

- **No date filter on `/historical/markets`** — must page (cheap: 5 calls total) and filter client-side.
- **No historical orderbooks** — orderbook endpoints are live-only. Not needed for the daily-candle event-study design.
- **`/events?with_nested_markets=true` excludes pre-cutoff markets** — don't use it for discovery; use `/historical/markets`.
- **Trade counts for pre-cutoff fills**: `/historical/trades` exists (appears public); candle `volume_fp` is what the collector already uses. If we need trade counts, verify the candle schema's trade-count field separately.
- Pre-cutoff markets report `status: "finalized"` — downstream code that branches on `status == "settled"` should accept both.

## Proposed approach for the full summer pull

1. **Event registry first.** The new summer window (2026-06-01 onward) needs the unscheduled-sports event list finalized (variety taxonomy: trades, signings, extensions, other major roster news — injuries EXCLUDED per Yuvan 2026-09-21) before we know which windows/series to pull.
2. **Discovery per series** (replace `list_series_markets`):
   - Live: `GET /markets?series_ticker=X` with no status (spec: empty = all statuses) **plus** explicit `status=settled` pages as a safety net; dedupe by ticker.
   - Historical: `GET /historical/markets?series_ticker=X`, paginate to exhaustion (≤1–2 pages per series).
   - Merge, dedupe, then client-side filter: keep markets with `open_time <= window_end` and `close_time >= window_start`.
3. **Candles**: keep existing per-ticker `get_candles()` (live → historical fallback). Optionally route live tickers through the batch `/markets/candlesticks` endpoint in chunks of ≤100.
4. **Keep the raw/ cache** logic as-is; add a `discovery_source` field (`live`/`historical`) to `market_metadata.csv` for provenance.
5. **Rate budget**: ~20 discovery calls + ~500–800 candle calls (only tickers overlapping actual event windows, not all 1,404) at 0.5s ≈ 5–10 minutes. Well within polite limits.
6. **Sports-series note**: KXNBA/KXSB summer-relevant contracts (2026-27 season / 2026 season) are still `open` and were already captured by the Sept 18 live pull — but their `open_time` must be ≤ window start; the client-side filter will confirm. The 60+36 historical sports markets are prior seasons and will mostly filter out.

## Validation script

`hidden_files/probe_historical.py` — rerunnable; reproduces all checks above and writes `/tmp/probe_historical_out.json`.

## Open question for parent agent

- Should the full pull also re-verify the Sept 18 "no status param" `/markets` behavior (i.e., did it actually include post-cutoff settled markets like KXCPI-26AUG)? The new discovery code makes this moot, but the existing `collection_log.json` coverage claim depends on it.
