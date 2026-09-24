# Giannis-to-Heat (2026-06-23) — fallback descriptive

**Status: NON-CONFIRMATORY / POST-PREREG SUPPLEMENTARY.** This analysis was not
preregistered. It exists because the confirmatory pipeline fully excluded this
event (all 38 tickers failed the ≥5 baseline-obs rule: the KXNBA-27 contracts
were listed 2026-06-15, only 8 days before T0=2026-06-23T03:50Z), and the
exclusion was not surfaced in the headline results. Per the exclusion guard
(`hidden_files/coverage_precheck.py`, `analyze_fallback.py`), no material
event drops silently: events with zero confirmatory pairs but ≥3 pre-T0
observations get a descriptive abnormal-move computation on the maximum
available pre-window, clearly labeled. These numbers must not be pooled with
confirmatory results or used in hypothesis tests.

## Method

- Baseline: mean quote midpoint over the maximum available pre-window
  ([T0−45d, T0); all 30 tickers below have n=6–8 obs, listed 2026-06-15).
- `abn_day0` = day-0 midpoint − baseline mean (midpoint = (bid+ask)/2, prereg-consistent).
- `abn_win_end` = midpoint at end of the 3-day window − baseline mean.
- Volume ratio = day-0 volume ÷ mean daily pre-window volume.
- Per-ticker table: `hidden_files/giannis_descriptive.csv` (30 tickers, sorted
  by |abn_day0|). 8 further tickers (KXNBA-26 2026-championship contracts,
  settled when the Finals ended ~06-14) had <3 pre-T0 obs and are excluded even
  from the fallback — their contracts were dead before the trade.

## Headline numbers (verified from kalshi_api_data_summer/market_data.csv)

| Ticker | Baseline (8d mean) | Day-0 (06-23) | Abn. move | Volume |
|---|---|---|---|---|
| KXNBA-27-MIA (Heat title) | 2.63c (flat: bid 2c / ask 3c every day 06-15→06-22) | 7.0c mid (bid 6c / ask 8c, last 8c) | **+4.38c** day-0; **+4.88c** at 3d-window end | 186,326 vs 18,928/day pre-mean (**9.8x**); ~4.2x vs prior day (44,256) |
| KXNBA-27-MIL (Bucks title) | 1.00c (flat) | 1.00c (flat) | 0.00c | 4,418 vs 1,140/day (3.9x, thin book — price never moved off the 1c tick) |

The market reacted exactly as intuition says it should: the Heat's 2027
championship price roughly **tripled** (2.6c → 7c midpoint; 3c → 8c last) on
trade day with a ~10x volume spike vs its 8-day mean. The move persisted
through the 3-day window (settling 5–8c), so this is repricing, not a
one-candle artifact.

## Context for the rest of the sample

- Across the 30 fallback tickers, mean abn_day0 = −0.11c: unaffected teams
  barely moved, as expected. The trade's price impact was concentrated in MIA
  (+4.4c); the next-largest movers were SAS (−2.6c), NYK (−1.3c), DAL (−1.0c) —
  second-order reshuffling of contender odds, all within a thin 8-day baseline.
- The Bucks leg did not reprice downward (stuck at the 1c minimum tick on a
  thin book). Asymmetric liquidity, not evidence of "no effect" on Milwaukee.
- Anticipation caveat: Giannis had been on the market since the February trade
  deadline (registry expectation note). The 2.6c pre-price already embedded
  *some* probability of a Heat move, so +4.4c is the *announcement surprise*,
  a lower bound on the trade's total effect on Heat title odds.

## What this changes

Nothing in the confirmatory results — those are locked to the prereg rules.
What changes is the *reporting*: the sports-cell headline ("14 events, mean
−0.12c") must carry the footnote that the sample's largest trade was excluded
for lack of baseline history, and that its descriptive day-0 move (+4.4c on the
Heat contract, ~10x volume) is the largest single-contract repricing observed
in any sports event in this data cut. Including it descriptively does not
overturn H1c (one +4.4c contract inside a 15-event cell mean vs macro's
+4.8c), but omitting it silently — as the first draft did — was wrong.
