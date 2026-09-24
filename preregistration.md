# Pre-registration: Kalshi Prediction-Market Event Study

**Researcher:** Yuvan Krishnamurthy
**Date locked:** 2026-09-21 (revised and approved by Yuvan 2026-09-21)
**Status:** LOCKED. Confirmatory analysis has NOT been run as of this date. Everything below is fixed before results are computed.

---

## 1. Research question

How fast and how strongly do Kalshi prediction markets react to news? The design is a **2×2 factorial**: news scheduleness (scheduled vs. unscheduled) crossed with domain (macro vs. sports). The old scheduled-vs-unscheduled comparison confounded the two — every scheduled event was macro and every unscheduled event was sports — so this design unconfounds them: compare scheduleness *within* each domain, and compare domains *holding scheduleness fixed*.

## 2. Hypotheses (fixed)

- **H1a — Scheduleness within macro.** Unscheduled macro news produces larger abnormal moves and shorter time-to-50% than scheduled macro news (scheduled releases are partially priced in).
- **H1b — Scheduleness within sports.** Unscheduled sports news produces larger abnormal moves and shorter time-to-50% than scheduled sports news.
- **H1c — Domain, holding scheduleness fixed (unscheduled).** Unscheduled sports news and unscheduled macro news produce different reaction magnitudes/speeds (two-sided — the comparison is the point, not the direction).
- **H1d — Domain, holding scheduleness fixed (scheduled).** Scheduled sports news and scheduled macro news produce different reaction magnitudes/speeds (two-sided).
- **H2 — Domain specificity (falsification built in).** Macro news moves macro markets but not sports futures; sports news moves sports futures but not macro markets. Cross-domain abnormal moves should be statistically indistinguishable from zero.
- **H3 — Contract-level gradient.** Reaction magnitude and speed differ across contract levels within a market type (price tiers for sports futures; moneyness tiers for macro buckets). Tested, not assumed: every tier is reported even if the gradient is flat.

**Power rule:** any cell with n < 5 events is reported descriptively only (means and confidence intervals, no hypothesis-test p-values presented as findings).

## 3. Contract levels — tier definitions (NEW)

Raw price is not comparable across market types (verified 2026-09-17 from the live Kalshi API: all 32 open KXSB and 30 open KXNBA contracts sit below 25c; 62 of 76 open KXFED contracts sit above 50c). Tiers are therefore defined **within market type**:

**Sports futures (KXNBA, KXSB) — by pre-event quote midpoint:**
| Tier | Range | Label |
|------|-------|-------|
| S1 | < 5c | Deep longshot |
| S2 | 5c – 15c | Longshot |
| S3 | 15c – 30c | Contender |
| S4 | > 30c | Co-favorite (expected to be empty; reported as N/A, never dropped) |

**Macro bucket markets (KXFED, KXCPI, KXCPICORE) — by moneyness:**
Probability in these markets concentrates in 1–2 buckets by construction, so raw price is meaningless. Level = distance of the bucket's strike from the consensus expectation, in bucket steps:
| Tier | Definition | Label |
|------|-----------|-------|
| M0 | Consensus bucket | At-the-money |
| M1 | ±1 bucket from consensus | Near-the-money |
| M2 | ±2 buckets | Off-the-money |
| M3 | 3+ buckets | Tails |

Consensus = Bloomberg/WSJ survey median mapped to the nearest bucket, fixed at T-1 day. Every tier is reported for every test. Empty tiers are marked N/A — tiers are never silently dropped.

## 4. Event inclusion criteria (fixed)

**Scheduled macro:** every FOMC rate decision and every CPI / core-CPI release from 2026-08-14 through the analysis cutoff, provided the corresponding Kalshi market was open. Surprise = actual release minus consensus (Bloomberg/WSJ survey median), in native units. T=0 = official release timestamp.

**Unscheduled macro:** macro shocks with no pre-announced date, first reported by a Tier-1 source (ESPN/Shams/Woj/Schefter for sports-adjacent; Bloomberg/WSJ/CNBC/Fed wire for macro; official team or government PR). Examples: emergency FOMC actions, surprise tariff/trade announcements, major bank failures, geopolitical shocks. T=0 = first credible report timestamp. Expected to be rare (a handful per year) — this cell is descriptive unless n ≥ 5.

**Scheduled sports:** sports events with a known date and unknown outcome that move championship futures. Examples: NFL season kickoff week, NBA schedule release, NBA draft lottery results, NBA draft, trade deadline day. T=0 = event start (or results announcement for lottery/draft). **Expectation rule:** for each scheduled sports event, log the documented expectation at T−7 days — published odds, major-media reporting/rumors, and the market's own price from the daily snapshots. Surprise = outcome − T−7 expectation, recorded in the event log with its source. The rumor snapshot is part of the data, not optional color.

**Unscheduled sports:** every major transaction from **2026-06-01 (whole summer) → cutoff** that (a) is first reported by a Tier-1 source (ESPN/Shams/Woj/Schefter or official team PR), AND (b) falls into one of the prespecified variety types below. One example per type is the *minimum* — we collect *all* qualifying events in each type, not just one cherry-picked example. **T=0 is the timestamp of the first report, not the official signing date.** Every qualifying event is logged, including ones where the market does not move. Injuries / availability shocks are **excluded** per Yuvan's decision 2026-09-21.

Prespecified unscheduled-sports types (variety requirement per Yuvan 2026-09-21):
- Trade involving a star / starter
- Major free-agent signing
- Contract extension / re-signing
- Other major roster news (coach/front-office change affecting title odds, retirement, etc.)

The All-Star/Pro Bowl filter from the earlier draft is dropped — replaced by this variety taxonomy to avoid cherry-picking.

The 18 roster events collected before 2026-09-17 are labeled **exploratory** and are used for method calibration only. Confirmatory results use the full summer window (2026-06-01 onward) with the variety taxonomy above.

## 5. Measurement (fixed)

- **Price:** quote midpoint (bid+ask)/2, not last-trade price. (Unchanged from current method.)
- **Baseline:** mean midpoint over trading days T-30 → T-5 relative to event. Abnormal move = actual − baseline.
- **Reaction speed:** time-to-50% = elapsed time from T=0 until the cumulative abnormal move first reaches 50% of the total abnormal move measured over the event window.
- **Event windows:** 1-day, 3-day, 5-day. Headline results use the 3-day window; the other two are robustness checks and are always shown.
- **Volume/liquidity (secondary):** trade count, volume, average spread, open interest in the window vs. baseline.

## 6. Statistical tests (fixed)

Cell = one of {sched_macro, unsched_macro, sched_sports, unsched_sports} (+ cross_domain falsification cells).

1. Per-event abnormal move; pooled t-test of mean abnormal move = 0 within each (cell × tier).
2. **Factorial contrasts (H1a–H1d),** two-sample t-tests on abnormal moves and on time-to-50%:
   - H1a: unsched_macro vs. sched_macro
   - H1b: unsched_sports vs. sched_sports
   - H1c: unsched_sports vs. unsched_macro
   - H1d: sched_sports vs. sched_macro
   Cells with n < 5 contribute descriptively only (no p-value presented as a finding).
3. Time-to-50% compared across tiers within each cell (H3) via Kruskal-Wallis.
4. H2: cross-domain cells tested against zero; failure to reject is the predicted outcome (report confidence intervals, not just p-values).
5. **Liquidity-filter robustness:** re-run (1)–(4) excluding event-market pairs with average spread > 8c or fewer than 5 trades in the window. Both versions reported.
6. **Placebo:** 50 random non-event trading days per market type, identical machinery. Expected: no significant abnormal moves (|mean| < 1c or p > 0.05). If the placebo fires beyond that, the method is invalid and results are not reported as findings.
7. **Multiple testing:** all events and all tiers reported; Holm correction applied to the four H1 contrast p-values as a robustness check, uncorrected values shown alongside.

## 7. Known data limitations (fixed, disclosed in paper)

- KXFED API endpoint returned HTTP 403 over [dates TBD from collector log]; zero market rows appended on those days. Verified: no outage day overlaps any macro event window. Documented, not hidden.
- CPI release-window 1-minute candles were appended once; minute-level analysis is restricted to windows with confirmed complete candle coverage.
- Thin markets: mitigated by midpoint pricing + liquidity-filter robustness (test 4).

## 8. What changes vs. the previous draft

- Conclusions will be rewritten from computed results; no claim survives that the numbers don't support, including nulls.
- Tier analysis (H3) is new.
- Placebo test is new.
- Pre-registration itself is new — this document.

---

**Signed:** ______________________ **Date:** __________
