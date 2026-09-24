# Excluded but material — nothing drops silently

Every event registered in `hidden_files/event_registry.csv` that has ZERO
pairs in the confirmatory analysis (`hidden_files/analysis_real/pair_results.csv`),
with the reason and the fallback descriptive result. Guarded going forward by
`hidden_files/coverage_precheck.py` (registration-time loud warning) and
`hidden_files/analyze_fallback.py` (descriptive track for zero-confirmatory-pair
events with ≥3 pre-T0 observations). Fallback rows are labeled
NON-CONFIRMATORY / POST-PREREG and must never be pooled with confirmatory results.

Per-(event, market) partial exclusions (4,641 rows, overwhelmingly
`insufficient_baseline_history` for non-central contracts) are logged in
`hidden_files/analysis_real/exclusions.csv` — this file covers only
*fully* excluded events.

## 1. giannis_to_heat — EXCLUDED from confirmatory, MATERIAL descriptive result

- **T0:** 2026-06-23T03:50Z. Cell: unscheduled_sports (trade).
- **Reason:** all 38 tickers failed the ≥5 baseline-obs rule. The KXNBA-27
  2027-championship contracts were listed 2026-06-15 — 8 days before T0 —
  so the prereg baseline (T−30..T−5, fallback T−45..T−5) could not be built.
  The KXNBA-26 (2026-championship) contracts had settled when the Finals
  ended ~06-14. The trade fell exactly in the dead zone between contract
  generations: old contracts dead, new contracts newborn.
- **Fallback descriptive** (`hidden_files/analyze_fallback.py`, 8-day
  pre-window, max available): 30 tickers computed; 8 KXNBA-26 tickers
  excluded even from fallback (<3 pre-T0 obs — contracts settled pre-T0).
- **Result:** KXNBA-27-MIA (Heat title): baseline 2.63c flat (bid 2c/ask 3c
  every day 06-15→06-22) → day-0 midpoint 7.0c (bid 6c/ask 8c, last 8c):
  **abn_day0 +4.38c, abn_win_end +4.88c**, volume 186,326 vs 18,928/day
  pre-mean (**9.8x**; ~4.2x vs prior day). KXNBA-27-MIL (Bucks): flat 1c,
  0.00c move (thin book, never left the 1c tick). Mean abn_day0 across all 30
  tickers: −0.11c (unaffected teams, as expected).
- **Full per-ticker table:** `hidden_files/giannis_descriptive.csv`;
  writeup: `hidden_files/giannis_descriptive.md`.
- **Lesson encoded in the guard:** `coverage_precheck.py` flags this exact
  pattern (0 tickers with ≥5 baseline obs, contracts listed after T0−30) as
  CRITICAL at registration time, forcing an explicit routing decision.

## 2. nba_opening_night — excluded: no post-event data (future event)

- **T0:** 2026-10-20 (confirmed). Cell: scheduled_sports.
- **Reason:** T0 is after the market-data cutoff (2026-09-24). 30 tickers
  were discovered and have pre-event data, but there is no post-T0 window to
  measure. Excluded from confirmatory AND from the fallback descriptive
  (`no_post_event_data` on all 30 tickers).
- **Action:** re-run `coverage_precheck.py` + the pull after 2026-10-20; the
  event then becomes analyzable under the prereg rules.

## 3. nfl_trade_deadline — excluded: no contracts discovered (future event)

- **T0:** 2026-11-10T21:00Z (confirmed). Cell: scheduled_sports.
- **Reason:** zero tickers discovered in the pull (no KXSB contracts listed
  yet for the deadline markets at pull time); T0 is also after the data
  cutoff. Nothing to analyze — confirmatory or descriptive.
- **Action:** same as (2): pull after T0, re-run precheck.

## Coverage note

The remaining 25 registered events all have ≥1 confirmatory pair. The
confirmatory sports-cell headline (14 events, mean −0.12c) does NOT include
giannis_to_heat — the sample's largest trade and its largest single-contract
repricing (+4.38c on MIA, ~10x volume) — and any paper text reporting that
headline must say so, pointing here.

## 4. nba_draft_2026 — EXCLUDED from confirmatory (extended batch C)

- **T0:** 2026-06-24 (per brief; exact draft dates unverified — web search
  was down at pull time). Cell: scheduled_sports.
- **Reason:** Giannis-type thin baseline. KXNBA-27 (2027-championship)
  contracts were listed 2026-06-15, ~9 days before T0 — all 30 fail the ≥5
  baseline-obs rule (`insufficient_baseline_history`). The 8 KXNBA-26
  contracts had settled (Finals ended ~06-14) → `no_window_data`.
  `coverage_precheck.py` flags this event WARNING (3/38 tickers meet
  baseline); the guard worked — the exclusion was loud, not silent.
- **Fallback descriptive** (9-day pre-window, NON-CONFIRMATORY): 30 KXNBA-27
  tickers computed; 8 KXNBA-26 excluded (`no_post_event_data`).
  `hidden_files/analysis_real/fallback_draft_descriptive.csv`.
- **Result:** mean abn_day0 −0.32c across 30 tickers. Largest mover:
  KXNBA-27-MIA **+3.39c** (baseline 3.11c → day-0 6.5c, vol 7.5x) —
  the draft moved Miami's 2027 title odds materially. All other tickers
  |abn| ≤ 0.5c.
- **T0 caveat:** draft date (06-24) is approximate; windows are 55 days wide
  so a few days' error is immaterial for daily candles, but confirm the
  exact date before publication.

## 5. kawhi_to_raptors_xd — EXCLUDED from H2 cross-domain (extended batch A2)

- **T0:** 2026-09-14T18:56Z. Cell: cross_sports_on_macro (falsification).
- **Reason:** no usable macro contracts at T0. The 2 nearest-expiry KXFED
  picks (KXFED-26SEP-T5.00/T5.25) are deep out-of-the-money buckets with
  **zero bid** through the whole baseline window (no price discovery;
  mid frozen at 0.5c) → `insufficient_baseline_history`. The 2 KXCPI picks
  (KXCPI-26SEP-T0.8/T0.9) were first listed 2026-09-17, three days AFTER T0
  → post-only, dropped from the registry by analyst decision.
  `coverage_precheck.py` flags CRITICAL (0/4 tickers meet baseline).
- **No valid fallback descriptive:** the KXFED contracts have no real
  pre-T0 prices (zero-bid), and their +49.5c "window move" is pure
  contamination — the 2026-09-16 FOMC 25bp hike repricing the 5.00%/5.25%
  buckets at T+2, not Kawhi news. Reporting it as a Kawhi effect would be
  false. The KXCPI contracts did not exist at T0.
- **Design lesson:** nearest-expiry selection is dangerous for the
  sports→macro leg — near-expiry buckets are dominated by pull-to-par
  convergence and scheduled macro events in the window. A re-pull should
  use far-expiry macro contracts (expiry > T0+60d).
