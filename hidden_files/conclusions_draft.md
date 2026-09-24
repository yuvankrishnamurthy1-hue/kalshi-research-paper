# Conclusions draft — Kalshi event study, summer 2026 (REAL DATA)

Written 2026-09-23 from computed results in `hidden_files/analysis_real/`.
Headline window = 3 trading days (prereg §5); 1-day and 5-day robustness
reported where they differ. NOTHING below is asserted beyond what the
tables show. Placebo check PASSED for both market kinds
(macro_bucket p=0.221, sports_future p=0.176) — results are reportable as
findings per prereg.

## 1. Per-cell results (n≥5 rule applied)

| Cell | n events | Mean abnormal move (3d) | p | Status |
|---|---|---|---|---|
| unsched_sports | 14 | −0.0012 | 0.058 | TESTED — marginal, tiny negative |
| unsched_macro | 8 | +0.0483 | 0.0096 (cell-level t-test over event means) | TESTED — positive |
| sched_sports | 2 | −0.0008 | — | descriptive-only |
| sched_macro | 1 | +0.0923 | — | descriptive-only |

Note: the analysis code splits unsched_macro into (cell, tier) groups of 4+4
(M3 = verified moneyness, M? = missing moneyness), each descriptive-only by the
n≥5 rule. The cell itself has 8 unique events ≥ 5, so the cell-level mean and
t-test above are computed directly from the 8 event means; the prereg rule is
about cells, not code-internal tier splits.

## 2. H1 contrasts (prereg §3)

- **H1a** (unsched vs sched macro): descriptive-only — sched_macro has 1 event.
- **H1b** (unsched vs sched sports): descriptive-only — sched_sports has 2 events.
- **H1c** (unsched sports vs unsched macro): **SIGNIFICANT.** Welch t = −3.61,
  p_raw = 0.0086, p_Holm = 0.0086 (3-day). Robust across windows:
  1-day p = 0.0063, 5-day p = 0.0011, all Holm-significant. Liquid-only
  sensitivity: p = 0.0091. Direction: unscheduled macro events produce larger
  abnormal moves (+0.048) than unscheduled sports events (−0.0012).
  Speed leg (t50): p = 0.085, NOT significant — no reliable difference in
  speed of adjustment (and t50 is daily-resolution; see intraday_check.txt).
- **H1d** (sched sports vs sched macro): descriptive-only — 2 vs 1 events.

So of the four H1 contrasts, exactly one is confirmatory-testable, and it
rejects the null in the predicted direction for magnitude.

## 3. H2 (directed cross-domain falsification)

**UNTESTABLE.** Both H2 cells have 0 events in the analysis registry
(cross_macro_on_sports: 0 pairs; cross_sports_on_macro: 0 pairs) because the
registry was built with same-domain tickers only. The falsification was not
performed. This is a design-coverage failure, not a null result.

## 4. H3 (contract-tier gradient)

**UNTESTABLE as preregistered.** The prereg M1/M2/M3 gradient requires verified
T−1 consensus; only 4 macro events (the Sept 8–11 CPI-referencing set) have
verified moneyness, all landing in a single tier, and the code's Kruskal test
compares M3 vs M? (H = 1.35, p = 0.245) — i.e. "has moneyness" vs "missing
moneyness," which is NOT the prereg gradient. Sports have a single tier.
No tier-gradient conclusion can be drawn.

## 5. Event-level anatomy (3-day, non-preregistered descriptives)

Unscheduled macro, sorted by abnormal move:
| Event | n_pairs | Mean abn |
|---|---|---|
| trump_truth_fed | 82 | +0.093 |
| russia_sanctions_bill | 118 | +0.091 |
| tariff_eu_threat | 118 | +0.091 |
| perim_island_seized | 136 | +0.042 |
| hormuz_strike_pipeline_shutdown | 135 | +0.038 |
| canada_proclamations | 49 | +0.018 |
| hormuz_retaliation_threat | 131 | +0.017 |
| nvda_earnings | 117 | −0.004 |

Unscheduled sports: all 14 events between −0.0048 (jordan_walsh_extension)
and +0.0007 (neemias_queta_extension); cell mean −0.0012, p = 0.058.
giannis_to_heat fully excluded (114 pair-window attempts, all
insufficient_baseline_history — its KXNBA-26 contracts were too thin/close
to expiry). nfl_trade_deadline and nba_opening_night fully excluded (no
data / future event).

## 6. Contamination and robustness (non-preregistered, must be disclosed)

- **The Sept-16 cluster drives the macro result.** The three largest macro
  movers (trump_truth_fed, russia_sanctions_bill, tariff_eu_threat, all
  ~+0.09) are dated the SAME day, share the same KXFED contracts, and their
  windows overlap each other AND the FOMC decision (18:00 UTC Sept 16). They
  are not independent observations; the effective macro n is closer to 6
  event-days than 8 events.
- **trump_truth_fed is confounded by construction.** Its event window contains
  the FOMC's 25-bp hike decision (2:00 PM ET); the Truth Social post came
  hours later. Its measured +0.093 move is largely the FOMC reaction, not the
  post. It is the scheduled-decision echo inside the "unscheduled" cell.
- **perim_island_seized shares Sept 11 with the August CPI release**, whose
  core print came in hot (+0.3% vs +0.2% expected) — a same-day scheduled
  shock in the same contracts.
- **Leave-one-out:** dropping any single macro event keeps the cell mean
  positive with p < 0.05 (range 0.0057–0.0246). But no leave-one-out removes
  the Sept-16 cluster as a whole; a cluster-collapsed sensitivity was not run.
- **The genuine shocks still move prices.** perim_island_seized (+0.042) and
  hormuz_strike_pipeline_shutdown (+0.038) — the two cleanest "massive waves"
  events — move ~4 cents, an order of magnitude above any sports event.
- **nvda_earnings is a clean null.** A +4.4% revenue / +6% EPS beat with an
  above-consensus guide produced essentially zero abnormal move (−0.004) in
  the KXFED/KXCPI buckets tracked. Not every "massive wave" registers in
  these contracts.
- **tariff_eu_threat was a conditional threat** (no goods, rates, or
  timetable announced), yet it sits at +0.091 — indistinguishable in the data
  from the enacted russia_sanctions_bill (+0.091) on the same day, same
  contracts. Talk and action are not separable here.

## 7. What the results actually say (plain language)

1. Championship-futures markets barely react to individual roster news:
   14 summer roster events average −0.1 cents of abnormal move, p = 0.058 —
   a marginal, tiny negative, i.e. effectively no positive repricing.
2. Macro-bucket markets react strongly to the September shock cluster:
   +4.8 cents average abnormal move across 8 events, p = 0.0096.
3. The difference between the two domains is statistically significant
   (H1c, p = 0.0086 Holm) and robust across 1/3/5-day windows and the
   liquid-only filter.
4. The macro result is heavily concentrated in three same-day, same-contract
   September 16 observations that overlap the FOMC decision; the cleanest
   individual shocks (Perim, pipeline strike) move ~4 cents.
5. Speed of adjustment does not differ significantly between domains
   (p = 0.085), and is measured at daily resolution only.
6. H2 was not testable (no cross-domain pairs collected); H3 was not
   testable as preregistered (consensus verified for only 4 events, one tier);
   H1a/H1b/H1d are descriptive-only (n < 5).

## 8. Limitations to carry into the paper

- Intraday data were never collected; t50 is daily-resolution.
- The `trades` column in the pull was unusable; liquidity filtering fell back
  to spread-only (per code design).
- Newly-listed far-dated macro contracts lacked baseline history, selecting
  the Sept macro events toward older/near-term contracts (see gap_analysis.txt).
- Date-only macro T0s (day-0 indexing) for 5 of 9 macro events.
- Scheduled cells are descriptive-only: the study cannot confirm anything
  about scheduled-vs-unscheduled within either domain.
- The Sept 8–16 macro events share contracts and overlapping windows; the
  H1c macro leg is effectively a 6-event-day sample, not 8 independent shocks.
