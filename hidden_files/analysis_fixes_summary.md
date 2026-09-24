# Analysis fixes — `analyze_kalshi_fixed.py` vs `analyze_kalshi.py`

Date: 2026-09-21. Original **not** overwritten; fixed version at
`~/workspace/kalshi-paper/analyze_kalshi_fixed.py`. All changes are marked
`# FIX n` in the code. Verified on synthetic data
(`/tmp/synth_test/`: 24 events, 4 tickers, 6h bars, known jumps).

## Critical fixes

**FIX 1 — time-to-50% definition.** Old code took the cumulative *sum* of
abnormal deviations and found when it hit 50% of the window total. That
degenerates: a price that jumps instantly and stays flat reaches 50% of the
cumulative sum on the first bar (t50 ≈ 0 always). New definition, matching the
prereg: first timestamp where the abnormal *price* (mid − baseline) reaches 50%
of the eventual directional move (abnormal move at end of window), in the same
direction. Verified: jumps at +6h/+12h/+18h recover t50 = 10h/12h/12h
(10h not 6h is correct — the +6h jump falls between 6h bars and is first
observable at the next bar).

**FIX 2 — n≥5 counts unique events, not event-market rows.** `factorial_contrasts`
and `pooled_tests` now use `event_id.nunique()` per cell for the power rule;
both tables report `n_events` *and* `n_pairs`, plus a `tested` flag and a
"descriptive only (n<5 unique events)" note. Synthetic check: contrasts show
n_a=n_b=6 (not 12); 3-event cross cells correctly untested.

**FIX 3 — clustering by event.** New `aggregate_by_event()` collapses each
(event × cell) to one observation: mean abnormal move across its contracts,
median time-to-50%. All tests (pooled, H1a–H1d, H2, H3) run on event-level
observations. Grouping is by (event_id, cell) — not event alone — because one
event contributes both on-domain and cross-domain (H2) pairs that must not be
averaged together. New outputs: `results/event_results.csv`.

## Further fixes

**FIX 4 — scaled/log-odds movement.** Pair rows now carry `abn_logodds`
(log-odds(mid_end) − log-odds(baseline), prices clipped to [1e-6, 1−1e-6]) and
`abn_scaled` (move ÷ baseline price); pooled/contrast tables report
`mean_abn_logodds` alongside absolute-cent moves.

**FIX 5 — explicit H2 cells.** `cell_of()` now returns `cross_macro_on_sports`
and `cross_sports_on_macro` as separate falsification cells; new
`h2_cross_domain()` tests each against zero with 95% CIs
(`results/h2_cross_domain_{full,liquid_only}_3d.csv`).

**FIX 6 — macro bucket verification.** New `verify_macro_buckets()` check at
startup: every macro pair must have `moneyness_steps`; tiers M0–M3 are treated
as mutually exclusive per Kalshi bucket-market construction, and the check
documents that the consensus→bucket mapping audit belongs to the registry
build. Missing moneyness → tier `M?`, excluded from tier tests with a warning.

**FIX 7 — baseline fallback/exclusion.** If <5 baseline obs in T−30..T−5, retry
T−45..T−5 and set `baseline_fallback=True`; if still <5, the pair is excluded
and logged to `results/exclusions.csv` with a reason (`no_market_data`,
`insufficient_baseline_history`, `no_window_data`). Unit-tested: fallback path
returns `baseline_fallback=True, n_base=7`; no-history path logs
`insufficient_baseline_history`.

**FIX 8 — matched placebos.** Placebo draws now: (a) sample tickers from the
real registry frequency-weighted (market/maturity mix), (b) match weekday +
time-of-day of a real event, (c) stay within ±30d of a real event date (regime
match), (d) per-ticker contamination exclusion — no real event for the *same*
ticker inside [t0−33d, t0+3d] so the placebo's own baseline/window can't
overlap a real event. Warns and reports actual n if the exclusion binds.

**FIX 9/13 — field availability.** `check_fields()` at load: `TRADES_AVAILABLE`
(true only if the trades column exists with >0 values) and `SPREAD_AVAILABLE`.
Missing trades → `n_trades` reported as NaN (never 0) and the trades leg of the
liquidity filter is skipped with a printed warning; same for spread.

**FIX 10 — volume/OI semantics.** Candle volume is a per-period *flow* → summed
over the window (`vol_window`) vs baseline daily mean (`vol_base_daily`); open
interest is a *stock* → differenced over the window (`d_oi`).

**FIX 11 — UTC normalization.** `parse_iso_utc()` returns tz-aware UTC always
(naive inputs assumed UTC); raw source string preserved in `ts_raw`.

**FIX 12 — multiple testing, consistently.** New correct `holm_correct()`
(step-down, nan-safe, order-preserving — the old inline version had an
index-mapping bug, caught by unit test). Applied to **both** legs of H1a–H1d:
`p_abn_holm` and `p_t50_holm`. (Pooled cell×tier tests are not Holm-corrected,
per prereg which specifies Holm only for the four H1 contrasts.)

**Bonus robustness:** `stats.kruskal` wrapped in try/except (raises on
identical values); env-var overrides `KALSHI_EVENT_REGISTRY` /
`KALSHI_MARKET_DATA` / `KALSHI_OUT_DIR` for testing without touching defaults.

## Test results (synthetic, `/tmp/synth_test/`)

- Exit 0; all 11 output CSVs written (pair/event results, pooled, contrasts,
  H2, Kruskal, placebo, exclusions when non-empty).
- t50 recovered at bar-observable jump times; NaN correctly when total move ≈ 0.
- Contrasts: n_a=n_b=6 unique events, `tested=True`; cross cells (3 events)
  `tested=False`, descriptive only.
- H2 rows present for both directions, means ≈ 0 as constructed.
- Placebo: macro 50/50 PASS; sports 0/50 with explicit warning — expected on
  this degenerate synthetic (all 6 sports events share 2 dates, so the
  contamination exclusion covers the sample); honest behavior, will not bind
  on sparse real data.
- Holm unit tests: `[0.04,0.01,0.30,0.50] → [0.12,0.04,0.60,0.60]` ✓;
  NaN-safe ✓; single value ✓.

## Known limitations / not changed

- Real-data run not done (per task). `event_registry.csv` still doesn't exist —
  nothing to run against yet.
- Prereg's injury/availability inclusion was decided after this fix (injuries
  EXCLUDED per Yuvan 2026-09-21); the code is type-agnostic so no change needed,
  but the fixed script's docstring still says "availability shock" generically.
- H3 Kruskal-Wallis uses each event's *modal* tier; events spanning tiers are
  assigned their most common tier (documented in code).
- Placebo maturity matching is via ticker-frequency weighting (ticker embeds
  expiry); no separate maturity covariate since `market_data.csv` lacks
  `close_time`.
