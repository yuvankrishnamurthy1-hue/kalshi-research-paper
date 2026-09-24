# How Kalshi Prediction Markets React to News: A 2×2 Event Study

**Yuvan Krishnamurthy — draft v2, 2026-09-24**

*This draft is written strictly from computed results. Confirmatory results follow the preregistration locked 2026-09-21 (`preregistration.md`, never edited). Post-preregistration analyses are labeled POST-PREREG SUPPLEMENTARY / NON-CONFIRMATORY throughout and are never pooled with confirmatory results.*

---

## Abstract

We measure how Kalshi prediction-market prices react to news in a 2×2 event study crossing scheduleness (scheduled vs. unscheduled) with domain (macro vs. sports). Confirmatory sample: 25 events, 1,460 event–contract pairs, daily quote midpoints, 1/3/5-day windows (headline: 3-day). The single confirmatory-testable contrast, **H1c** (unscheduled sports vs. unscheduled macro), rejects the null: unscheduled macro shocks average **+4.83c** abnormal move across 8 events while 14 summer roster events average **−0.12c** (Welch t = −3.61, p = 0.0086 raw and Holm; robust across windows and the liquid-only filter). The other three H1 contrasts are descriptive-only: the scheduled cells never reached the preregistered n≥5. A post-prereg supplementary scheduled-macro sample (15 FOMC/CPI events, Jan–Sep 2026) gives H1a direction-as-predicted but non-significant (+4.83c vs +2.21c, p = 0.170). H2 (cross-domain falsification): macro news moves sports futures by +0.16c (p = 0.0033) — statistically nonzero but ~3% of the own-domain effect, economically negligible; the sports→macro leg is untestable with daily data (two documented failed implementations: expiring-bucket pull-to-par, then far-expiry illiquidity plus baseline contamination) and is not reported as a finding — qualitatively, every large move in it traces to a dated macro cause. H3 (contract-tier gradient) was untestable in its preregistered coding; under data-identified tercile tiers the |abnormal-move| gradient is strong and monotone in both domains (exploratory). The sample's largest trade — Giannis to Miami, Heat title contract 2.6c→7c on trade day with ~10x volume — was fully excluded from confirmatory analysis (contracts listed 8 days pre-T0); it is reported descriptively, and an exclusion guard now prevents silent drops. The macro result is concentrated in a same-day, same-contract September-16 cluster overlapping the FOMC decision: effective independence is closer to 6 event-days than 8 events, and the cleanest individual shocks (Perim Island, Hormuz pipeline strike) move ~4c.

---

## 1. Design and preregistration

**Research question.** How fast and how strongly do Kalshi prediction markets react to news — and does it depend on whether the news was scheduled and on its domain? Earlier work confounded the two: every scheduled event was macro, every unscheduled event was sports. The 2×2 design unconfounds them.

**Cells.** {scheduled, unscheduled} × {macro, sports}. **Hypotheses** (prereg §2):

- **H1a** — scheduleness within macro: unscheduled macro > scheduled macro (magnitude; shorter time-to-50%).
- **H1b** — scheduleness within sports: unscheduled sports > scheduled sports.
- **H1c** — domain holding scheduleness fixed (unscheduled): sports vs. macro differ (two-sided).
- **H1d** — domain holding scheduleness fixed (scheduled): sports vs. macro differ (two-sided).
- **H2** — domain specificity (falsification): macro news moves macro markets but not sports futures; sports news moves sports futures but not macro markets. Cross-domain abnormal moves ≈ 0.
- **H3** — contract-level gradient: reaction magnitude/speed differ across contract tiers within a market type.

**Power rule** (prereg §2): any cell with n < 5 unique events is reported descriptively only — means and confidence intervals, no p-values presented as findings.

**Expectations.** Scheduled sports: documented T−7 expectation (odds, media, market price); surprise = outcome − expectation. Scheduled macro: surprise = actual − consensus (Bloomberg/WSJ survey median). Unscheduled macro: "massive waves" bar — the shock must move expectations materially. Unscheduled sports: whole summer 2026-06-01 onward, Tier-1-reported, variety taxonomy (star trade / major signing / extension / other major roster news); injuries excluded.

## 2. Data

**Summer pull (confirmatory).** 483 tickers, 17,680 daily candle rows, 2,259 metadata rows, 28 registered events, full [T−45, T+10] windows. Price = quote midpoint (bid+ask)/2. A schema bug in the collector (D11) wrote 176 historical rows price-less; fixed by re-parsing raw files (backup: `market_data.csv.d11_bak`), verified zero price-less rows. **The v2 re-run on corrected data is byte-identical to v1 for every confirmatory table** (pooled, contrasts, event, pair, tier Kruskal) — the headline numbers do not depend on the fix. Placebo draws shifted (macro p 0.221→0.062; sports p 0.176→0.952) but still PASS.

**Extended pull (batches A–D, `kalshi_api_data_extended/`).**
- **A (H2):** cross-domain tickers — 16-ticker sports baskets (far-expiry KXNBA-27/KXSB-27) around the 8 macro events; nearest-expiry KXFED/KXCPI around the 14 sports events.
- **B (prereg-mandated):** the August CPI release (2026-09-11T12:30Z), which prereg §4 required but the first pull never registered — 26 tickers, 20 usable pairs, abnormal move −1.50c.
- **C (prereg-definition-legit scheduled sports):** MLB All-Star Game 2026 (30/30 usable, −0.03c), NBA draft lottery 2026 (8/30 usable, +2.62c on survivors — likely confounded by concurrent playoff games, see §8), NBA draft 2026 (fully excluded — Giannis-type thin baseline; fallback descriptive: MIA +3.39c, 7.5x volume). T0 dates for batch C are approximate (web search was down at pull time); windows are 55 days wide, so this is immaterial for daily candles but must be confirmed before publication.
- **D (POST-PREREG SUPPLEMENTARY):** 15 FOMC decisions and CPI/core-CPI releases 2026-01-01→2026-09-24. All complete — Kalshi history reaches Dec 2025. Scheduled-macro supplementary n = 15, mean +2.21c.

Combined: 27,519 market-data rows, 3,737 pairs, 0 price-less rows (`hidden_files/market_data_combined.csv`, `hidden_files/pairs_combined.csv`).

## 3. Methods

**Measurement** (prereg §5). Baseline = mean midpoint over trading days T−30→T−5 (fallback T−45→T−5 if <5 obs, flagged; D2). Abnormal move = actual − baseline. Event windows 1/3/5 trading days; headline = 3-day. Reaction speed = time-to-50%: first time the abnormal *price* reaches 50% of the eventual directional window move (D1 — see deviations). Volume/liquidity secondary. Liquidity-filter robustness: exclude pairs with avg spread > 8c or < 5 trades; both versions reported.

**Tests** (prereg §6). Per-event abnormal moves (contracts aggregated to event means — required by the Sept macro cluster's shared contracts, N2). Pooled t-test of mean = 0 within each cell×tier. Factorial contrasts H1a–H1d: two-sample t-tests (Welch) on event-level abnormal moves and on time-to-50%. H2: each directed cross-domain cell tested against zero with 95% CIs (D5). H3: Kruskal-Wallis across tiers. Holm correction on the four H1 contrast p-values (movement and speed legs separately, D3); uncorrected shown alongside. Placebo: 50 matched non-event days per market type (same weekday/time-of-day, ±30d regime match, contamination exclusion); verdict PASS if |mean| < 1c or p > 0.05 (D4 strengthens the prereg-literal random draw).

**Preregistration deviations (D1–D14; full text in `hidden_files/prereg_deviations.md`; `preregistration.md` itself untouched).** Material ones: **D1** — time-to-50% implemented as first attainment of 50% of the eventual directional price move (the prereg's cumulative-sum wording degenerates to t50≈0 for step moves; the code version is the non-degenerate reading). **D6** — scheduled macro under-covered in the first pull (prereg said "every" FOMC/CPI from 2026-08-14; only the FOMC was pulled) — partially repaired by batch B. **D9** — no intraday data exist, so speed is daily-resolution throughout (prereg §7's minute-candle notes refer to an older pull). **D10** — exclusion guard (below). **D11** — the schema fix; byte-identical confirmatory re-run. **D12** — H2 sports→macro leg invalid by construction (nearest-expiry pull-to-par); macro→sports leg significant-but-tiny. **D15** — far-expiry re-pull also invalid (illiquidity + baseline contamination); leg untestable with daily data, qualitative evidence consistent with H2. **D13** — v2 re-run record. **D14** — expanded scheduled samples (batches B/C/D). Remainder (D2–D5, D7, D8) are documented strengthenings/clarifications with no effect on findings.

**Exclusion guard (D10).** After the Giannis incident (§6), the pipeline adds: (1) `coverage_precheck.py` — registration-time loud warning when an event's contracts list after T0−30 (back-run: 7 OK, 20 warnings, 1 CRITICAL = Giannis, correctly caught); (2) `analyze_fallback.py` — NON-CONFIRMATORY descriptive track for zero-confirmatory-pair events with ≥3 pre-T0 observations, labeled on every row; (3) `excluded_but_material.md` — the register of fully excluded events with reasons and fallback results. Nothing drops silently again.

## 4. Results

### 4.1 H1c (confirmatory): unscheduled sports vs. unscheduled macro — SIGNIFICANT

| Cell | n events | n pairs | Mean abnormal (3d) | Cell p (mean=0) |
|---|---|---|---|---|
| unscheduled sports | 14 | 430 | **−0.12c** | 0.058 (marginal) |
| unscheduled macro | 8 | 886 | **+4.83c** | 0.0096 |

Welch t-test on event-level abnormal moves: **t = −3.61, raw p = 0.0086, Holm p = 0.0086** (only one of the four contrasts was testable, so the Holm adjustment changes nothing). Robustness: 1-day window t = −3.83, **p = 0.0063**; 5-day window t = −5.30, **p = 0.0011**; liquid-only filter p = 0.0091. Direction: unscheduled macro shocks produce substantially larger abnormal moves than unscheduled sports roster news.

**Speed leg:** median time-to-50% 10.8h (sports) vs 28.0h (macro), p = 0.085 — **not significant**. No reliable difference in speed of adjustment; measured at daily resolution only.

### 4.2 H1a / H1b / H1d — descriptive-only (confirmatory)

The scheduled cells never reached n≥5, so no confirmatory test is presented — per the power rule, means only:

- **H1a** (unsched vs sched macro): +4.83c (n=8) vs +9.23c (n=1, FOMC Sep hike). With batch B's CPI release added: scheduled macro n=2 (+9.23c, −1.50c). Still descriptive-only.
- **H1b** (unsched vs sched sports): −0.12c (n=14) vs −0.08c (n=2). With batch C: scheduled sports n=4 usable (All-Star −0.03c; lottery +2.62c on 8 thin survivors, confounded — §8), mean +0.61c. Still n<5.
- **H1d** (sched sports vs sched macro): −0.08c (n=2) vs +9.23c (n=1); with batches B+C: +0.61c (n=4) vs n=2. Still descriptive-only.

**POST-PREREG SUPPLEMENTARY — H1a with the extended scheduled-macro window** (batch D, n=15 FOMC/CPI events Jan–Sep 2026): unscheduled macro +4.83c (n=8) vs scheduled macro **+2.21c** (n=15), t = 1.43, **p = 0.170 — not significant**. The direction matches the prereg prediction (unscheduled > scheduled), but the difference is not distinguishable from zero at these n's. This is the closest the data get to testing H1a, and it does not confirm it. Reaching n≥5 in the confirmatory window would require a formal prereg amendment extending the scheduled-macro window — a decision for the researcher, not taken here.

### 4.3 H2 — cross-domain falsification: precise near-zero in one leg, invalid in the other

- **Macro news → sports markets** (8 events × 16-ticker far-expiry sports baskets, 128 pairs): 3-day mean abnormal **+0.16c**, 95% CI **[+0.07c, +0.25c]**, t = 4.37, **p = 0.0033** (1-day +0.15c p=0.0002; 5-day +0.16c p=0.0041; liquid-only identical). The prereg's literal prediction ("indistinguishable from zero") is formally rejected — but +0.16c is ~3% of the own-domain macro effect (+4.83c). **Statistically nonzero, economically negligible.** There is no meaningful transmission from macro news into championship futures. (Possible contributors: market-wide risk drift on macro-news days; the 09-16 cluster window contains Kawhi-to-Raptors at 09-14, whose own measured effect is ≈ 0.)
- **Sports news → macro markets**: **UNTESTABLE with daily data — not reported as a finding** (D12, D15). Two implementations failed for documented reasons. First, the batch-A2 selection (nearest-expiry KXFED/KXCPI) put expiring buckets 7–25 days from expiry in the windows; every large |abnormal move| was mechanical pull-to-par convergence (e.g., KXCPI-26JUN-T-0.2: −40c across early-July sports events) plus scheduled macro events inside the windows (Kawhi's KXFED window contains the 09-16 FOMC hike at T+2). Second, the far-expiry re-pull (expiry > T0+60d, 15 events × 4 tickers, `kalshi_api_data_h2farexpiry/`) replaced pull-to-par bias with illiquidity (far-expiry Fed buckets carry stub quotes most days; the leg rests on KXCPI) and baseline contamination: the 06-17 FOMC repricing cliff sits inside 7 sports events' baselines (manufacturing negative "abnormal" moves, e.g. Giannis −21.7c), and the largest single move (von_miller −38.5c) is the hot 08-12 CPI print at T−5 — macro news, not sports news. A pseudo-T0 placebo (same machinery, no sports news) shows the same negative drift, confirming the test measures macro drift, not sports effects. Formally the far-expiry headline rejects (−12.02c, p=0.011), but the rejection is spurious. Qualitatively the evidence is consistent with H2's prediction: every large |move| in this leg traces to a dated macro cause, and no sports-attributable move is visible in any event. A valid test needs intraday candles around T0. Kawhi's cross-domain row is documented in `excluded_but_material.md` §5.
- **Net H2:** the falsification spirit holds — no economically meaningful cross-domain effect in either direction — but the prereg's literal "fail to reject" was not obtained on the macro→sports leg, and the reverse leg is untestable with daily data (two documented failed implementations).

### 4.4 H3 — contract-tier gradient: untestable as preregistered; visible under data-identified tiers (supplementary)

The prereg tier coding does not discriminate in this sample: all 14 sports events' contracts land in one tier (S1), and macro consensus was verifiable for only 4 events (prereg Kruskal on the rest compares M3 vs M? — "has moneyness" vs "missing moneyness," H = 1.35, p = 0.245 — not the prereg gradient). **No tier-gradient conclusion can be drawn from the preregistered coding.**

**POST-PREREG SUPPLEMENTARY** (`hidden_files/analysis_real/tier_supplementary_3d.csv`, exploratory, pair-level — pairs within an event are correlated, so p-values are anti-conservative; read magnitudes and monotone patterns):

| Cell | Metric | Gradient | Kruskal-Wallis |
|---|---|---|---|
| unsched_macro (8 ev) | \|abnormal\| | **M0 11.6c → M1 10.4c → M2 6.4c → M3 3.4c** (monotone) | H = 69.9, p < 0.0001 |
| unsched_sports (14 ev) | \|abnormal\| | **P3 1.73c → P2 0.49c → P1 0.22c** (monotone, within-cell pre-price terciles) | H = 91.8, p < 0.0001 |
| unsched_macro | signed | hump-shaped, peaks at M1 (+5.9c; liquid-only p = 0.005, full p = 0.060) | — |
| unsched_sports | signed | no gradient (p = 0.13) | — |

The gradient H3 hypothesized exists — at-the-money macro buckets move ~3x more than tails (the textbook moneyness gradient), and expensive sports contracts move ~8x more than cheap ones (partly mechanical: a 25c contract has more room to move than a 1c contract). Signed moves show no sports gradient: expensive-team contracts don't systematically move *up* more. Scheduled cells are not interpretable (1 event / degenerate terciles); KW not run there.

### 4.5 Event-level anatomy (3-day, descriptive)

Unscheduled macro, sorted: trump_truth_fed +9.3c · russia_sanctions_bill +9.1c · tariff_eu_threat +9.1c · perim_island_seized +4.2c · hormuz_strike_pipeline_shutdown +3.8c · canada_proclamations +1.8c · hormuz_retaliation_threat +1.7c · nvda_earnings −0.4c.

Unscheduled sports: all 14 events between −0.48c (jordan_walsh_extension) and +0.07c (neemias_queta_extension); cell mean −0.12c, p = 0.058.

**Leave-one-out (macro):** dropping any single macro event keeps the cell mean positive and significant (p range 0.0057–0.0246). But no leave-one-out removes the September-16 cluster *as a whole* — a cluster-collapsed sensitivity was not run, and the cluster is the result's load-bearing wall (see §7).

### 4.6 Robustness and validity checks

- **Placebo:** 50 matched non-event days per market type. Macro_bucket: mean −2.35c, p = 0.062 — **PASS** by the prereg gate (p > 0.05) but close to the line; v1 had p = 0.221 and the D11 data fill moved it. Sports_future: p = 0.952 — clean PASS. The method's validity gate holds, but the macro placebo bears watching: a −2.35c mean drift on "quiet" macro days is not nothing, and it rhymes with the small positive drift seen in the H2 macro→sports leg.
- **Windows:** H1c significant at 1d, 3d, 5d. **Liquid-only:** H1c p = 0.0091; H2 macro→sports identical; H3 macro signed leg sharpens (p = 0.005).
- **V2 byte-identity:** the D11-corrected re-run reproduces every confirmatory table exactly — the findings do not hinge on the 1% of rows the bug emptied.

## 5. The Giannis case (NON-CONFIRMATORY descriptive)

giannis_to_heat — the sample's largest trade — was **fully excluded from confirmatory analysis**: all 38 tickers failed the ≥5 baseline-obs rule because KXNBA-27 contracts were listed 2026-06-15, 8 days before T0, while the KXNBA-26 contracts had settled with the Finals. The trade fell in the dead zone between contract generations. The first draft reported the sports-cell headline without this exclusion. That was a reporting failure; the exclusion guard (§3) now makes this class loud.

Fallback descriptive (8-day pre-window, max available; `hidden_files/giannis_descriptive.md`):

- **KXNBA-27-MIA (Heat title):** baseline 2.63c flat (bid 2c/ask 3c, 06-15→06-22) → day-0 midpoint 7.0c (bid 6c/ask 8c, last 8c): **+4.38c day-0, +4.88c at 3-day-window end**, volume 186k vs 18.9k/day pre-mean (**9.8x**; 4.2x vs prior day). The Heat's title price roughly tripled on trade day with a ~10x volume spike, and the move persisted — repricing, not a one-candle artifact. It is the largest single-contract repricing in any sports event in this data cut.
- KXNBA-27-MIL (Bucks): flat at 1c, 0.00c — thin book, never left the minimum tick. Asymmetric liquidity, not evidence of "no effect" on Milwaukee.
- Mean day-0 move across all 30 fallback tickers: −0.11c — unaffected teams barely moved, as expected.
- **Anticipation caveat:** Giannis had been on the market since the February deadline (registry expectation note). The 2.63c pre-price already embedded some probability of a Heat move, so +4.38c is the *announcement surprise* — a lower bound on the trade's total effect.

Including Giannis descriptively does not overturn H1c (one +4.4c contract inside a 15-event sports cell vs macro's +4.8c cell mean), but the confirmatory sports headline (−0.12c, 14 events) **must** carry this footnote: the biggest trade in the sample is not in it.

## 6. Discussion

**What the numbers support.** (1) Unscheduled macro shocks move Kalshi macro-bucket prices an order of magnitude more than summer roster news moves championship futures (+4.83c vs −0.12c, H1c p = 0.0086, robust). (2) The cross-domain falsification holds economically: macro news leaks at most +0.16c into sports futures. (3) Reaction magnitude scales with contract moneyness/price in both domains (supplementary). (4) The single biggest sports repricing in the data (Giannis, +4.38c descriptive) is invisible to the confirmatory machinery — a measurement-coverage fact, not a market-efficiency fact.

**What the numbers do not support.** Scheduled-vs-unscheduled comparisons within either domain (H1a/H1b) and the scheduled cross-domain contrast (H1d): the scheduled cells never reached testable size, and the supplementary H1a (p = 0.170) does not confirm the predicted direction. Any claim that "scheduled news is priced in" on Kalshi is not established by this study. Speed-of-adjustment differences: not significant (p = 0.085), daily resolution only.

**The anticipation problem.** Event studies measure surprise relative to baseline, not total effect. Giannis was rumored since February; LeBron-to-76ers and Garrett-to-Rams had weeks-long rumor trails. Part of every "zero" in the sports cell is anticipation priced into the baseline window — the correct reading is "no *announcement-day* repricing," not "no effect." The Giannis descriptive (+4.38c on an 8-day baseline) is itself a lower bound for the same reason.

**The independence problem.** The macro cell's effective sample is smaller than n=8. Three observations share a date, contracts, and the FOMC decision; Perim shares 9/11 with a hot CPI print; trump_truth_fed's window *is* the FOMC reaction wearing an unscheduled costume. The honest description: a September shock *cluster* moved macro buckets ~4–9c, and the two cleanest isolated shocks (Perim Island +4.2c, Hormuz pipeline strike +3.8c) moved ~4c — still an order of magnitude above any confirmatory sports event, and above Giannis's +4.38c descriptive only at the cluster's peak, not at its clean edge.

## 7. Limitations

1. **Cluster dependence (§6):** the Sept-16 observations are not independent; no cluster-collapsed sensitivity was run. H1c's macro leg is effectively ~6 event-days.
2. **Contamination:** trump_truth_fed post-dates the FOMC decision (its +9.3c is largely the scheduled-decision echo); perim_island_seized shares 09-11 with the August CPI release (core +0.3% vs +0.2% expected); the H2 sports→macro leg is invalid by contract selection (D12).
3. **Thin scheduled cells:** H1a/H1b/H1d untestable confirmatorily; supplementary H1a n=8 vs 15, p=0.170.
4. **Anticipation:** rumor run-ups inside baseline windows attenuate announcement effects, especially in sports.
5. **Coverage gaps:** Giannis and the NBA draft fully excluded from confirmatory (dead-zone contract listings); NBA opening night and NFL trade deadline are future events; the lottery's +2.62c rests on 8 thin survivors and is likely confounded by concurrent playoff games.
6. **Resolution:** daily candles only — no intraday speed inference; date-only T0s for several macro events (±1-day day-0 indexing; the 3-day headline window is robust to this, the 1-day window less so); batch-C T0s approximate.
7. **Placebo proximity:** macro placebo p = 0.062 passes the prereg gate but is close; the −2.35c mean drift on quiet macro days deserves a larger placebo sample in follow-up work.
8. **Prereg tier coding (H3)** did not discriminate; the reported gradient is supplementary and exploratory (pair-level, within-event correlation).

## 8. Conclusion

Kalshi's macro-bucket markets reprice sharply on unscheduled macro shocks (+4.83c average, p = 0.0096 over 8 events); its championship-futures markets barely budge on summer roster news (−0.12c average over 14 events, p = 0.058) — and the difference is significant (H1c, p = 0.0086, robust). Cross-domain leakage is economically nil. Reaction size scales with moneyness. Those are the findings.

Everything else is either descriptive or untested: scheduleness effects within each domain, the scheduled cross-domain contrast, and the preregistered tier gradient. The study's two wounds are stated plainly: (i) the macro result leans on a non-independent September cluster, and (ii) the confirmatory machinery excluded the sample's largest trade while reporting the average without it — now documented, measured descriptively (+4.38c, ~10x volume), and guarded against by construction. The next version needs: a cluster-collapsed H1c sensitivity, a formal prereg amendment (or longer window) to reach n≥5 in the scheduled cells, and intraday data before any speed claim — and before any valid H2 sports→macro test, which daily data cannot support.

---

## Reproducibility

- Preregistration: `preregistration.md` (locked 2026-09-21, unedited).
- Registry: `hidden_files/event_registry.csv` (+ `event_registry_extended.csv` for batches A–D).
- Data: `kalshi_api_data_summer/` (confirmatory), `kalshi_api_data_extended/` (batches A–D), combined `hidden_files/market_data_combined.csv`.
- Analysis: `analyze_kalshi_fixed.py`; v2 outputs `hidden_files/analysis_real/*_v2.csv`; extended `*_v2xd.csv`; supplementary `*_v2supp.csv`; fallback `fallback_descriptive_3d.csv`, `giannis_descriptive.csv`; H3 supplementary `tier_supplementary_3d.csv`.
- Deviations D1–D14: `hidden_files/prereg_deviations.md`. Exclusions: `hidden_files/excluded_but_material.md`, `analysis_real/exclusions*.csv`. Guard: `hidden_files/coverage_precheck.py`, `hidden_files/analyze_fallback.py`.
