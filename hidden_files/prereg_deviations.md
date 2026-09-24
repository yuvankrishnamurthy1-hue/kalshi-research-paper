# Preregistration vs. code reconciliation

Date: 2026-09-23. Prereg: `preregistration.md` (LOCKED 2026-09-21 — never edit).
Code: `analyze_kalshi_fixed.py` (see `hidden_files/analysis_fixes_summary.md`).
Rule: prereg stays locked; for each deviation, recommendation is KEEP CODE or
CHANGE CODE, with rationale. No code changes made in this pass.

## D1 — Time-to-50% definition (MATERIAL — the known mismatch)
- Prereg §5: "time-to-50% = elapsed time from T=0 until the **cumulative abnormal
  move** first reaches 50% of the **total abnormal move measured over the event
  window**."
- Code (FIX 1): first timestamp where the abnormal **price** (mid − baseline)
  reaches 50% of the **eventual directional move (abnormal move at end of
  window)**, same direction.
- Two differences, not one: (a) cumulative-sum-of-deviations vs price level;
  (b) total-over-window vs end-of-window value.
- The prereg-literal version degenerates (a step-jump that stays flat hits 50%
  of the cumulative sum on the first bar, t50 ≈ 0 always) — this is exactly what
  FIX 1 fixed. The code version is the economically meaningful "speed of price
  discovery" estimand.
- Note: `analysis_fixes_summary.md` claims FIX 1 "match[es] the prereg" — that
  claim is inaccurate; the paper's methods section must not repeat it.
- RECOMMENDATION: **Keep code, document deviation.** Report the code's
  definition verbatim in the paper; note the prereg wording was ambiguous and
  the implemented version is the non-degenerate reading. Do NOT change the code
  (reverting reintroduces t50 ≈ 0 for step moves).

## D2 — Baseline fallback window
- Prereg §5: baseline = mean midpoint over T-30 → T-5.
- Code (FIX 7): if <5 baseline obs in T-30..T-5, retry T-45..T-5 and set
  `baseline_fallback=True`; if still <5, exclude with reason logged.
- RECOMMENDATION: **Keep code, document.** Strictly more inclusive than prereg,
  every fallback is flagged in output, exclusions are logged. No finding can
  hide behind the fallback.

## D3 — Holm correction scope
- Prereg §6.7: "Holm correction applied to the four H1 contrast p-values as a
  robustness check, uncorrected values shown alongside."
- Code (FIX 12): Holm applied separately to the 4 movement p-values
  (`p_abn_holm`) AND the 4 speed p-values (`p_t50_holm`); uncorrected shown.
- RECOMMENDATION: **Keep code, document.** Both legs are presented as findings,
  so both legs get the correction. Marginally more conservative than the
  prereg-literal reading; direction of any bias is toward fewer rejections.

## D4 — Placebo construction
- Prereg §6.6: "50 random non-event trading days per market type, identical
  machinery."
- Code (FIX 8): matched placebos — same weekday/time-of-day as a real event,
  date within ±30d of a real event (regime match), ticker drawn
  frequency-weighted from the registry, per-ticker contamination exclusion
  [t0−33d, t0+3d]. Verdict rule (|mean|<1c or p>0.05 → PASS) matches prereg.
- RECOMMENDATION: **Keep code, document as strengthening.** Harder for the
  method to pass by accident than under the prereg-literal random draw.

## D5 — H2 split into two directed cells
- Prereg §2/H2: "Cross-domain abnormal moves should be statistically
  indistinguishable from zero" (single pooled statement).
- Code (FIX 5): two directed falsification cells — macro news → sports markets,
  sports news → macro markets — each tested against zero with CIs.
- RECOMMENDATION: **Keep code, document.** Consistent with prereg intent, more
  informative; a failure in one direction is not averaged away.

## D6 — Scheduled-macro scope under-covered (MATERIAL — data, not code)
- Prereg §4: scheduled macro = "**every** FOMC rate decision and **every**
  CPI / core-CPI release from 2026-08-14 through the analysis cutoff, provided
  the corresponding Kalshi market was open."
- Data: only `fomc_sep_hike` was collected (1 event; 1 analyzable ticker).
  The July-CPI (released ~Aug 12 — just before the window), August-CPI
  (released ~Sep 11), and any other FOMC decisions in-window were NOT pulled.
- Consequence: the sched_macro cell has n=1 → descriptive only; H1a
  (unsched vs sched macro) and H1d (sched sports vs sched macro) contrasts are
  UNTESTABLE in this data cut. This was anticipated by the power rule but the
  prereg's "every" language is not satisfied.
- RECOMMENDATION: **Document as limitation; do not silently narrow the prereg.**
  Paper reports H1a/H1d as not-testable (insufficient scheduled-macro data),
  descriptive stats only. A follow-up pull adding the missing CPI releases
  would restore testability — flagged as future work, not done here.

## D7 — T=0 precision for date-only macro events
- Prereg §4: unscheduled macro T=0 = first credible report timestamp;
  scheduled macro T=0 = official release timestamp.
- Data: macro events carry date-only T0s (midnight UTC) except where research
  confirms intraday times. Intraday misalignment shifts which daily candle is
  "day 0" by up to one day.
- RECOMMENDATION: **Keep code; mitigate in registry.** Use confirmed intraday
  times where research verifies them; otherwise midnight UTC with
  t0_confidence=approx. The 3-day headline window is robust to ±1-day shift;
  note the limitation for the 1-day window.

## D8 — H3 also tests |abnormal| across tiers
- Prereg §6.3: "Time-to-50% compared across tiers within each cell (H3) via
  Kruskal-Wallis."
- Code: Kruskal-Wallis on t50 AND on |abnormal move| across tiers.
- RECOMMENDATION: **Keep code, document.** The |abnormal| leg is the natural
  "magnitude gradient" companion to the speed leg; both reported.

## D9 — Prereg §7 data-limitation notes are stale
- Prereg §7 references the OLD daily collector (KXFED 403s, 1-minute CPI
  candles "appended once"). Those refer to the Aug–Sep monitoring pull, not
  this summer pull. This analysis uses daily candles only; there is NO minute
  data, so intraday speed-of-adjustment is UNAVAILABLE (not merely restricted).
- RECOMMENDATION: **Document.** Paper's limitations section describes the
  summer pull's actual limitations (see `hidden_files/gap_analysis.txt`),
  not the §7 notes. Speed-of-adjustment = daily resolution throughout.

## Non-deviations (checked, consistent)
- N1: n<5 unique events → descriptive only: code counts `event_id.nunique()`
  per cell for both pooled tests and contrasts. Matches.
- N2: Event-level aggregation (FIX 3): prereg says "Per-event abnormal move"
  as the unit — code aggregates contracts to event×cell means. Matches (and
  required by the Sept 8–16 macro cluster's shared contracts).
- N3: Pooled cell×tier tests are NOT Holm-corrected in code — matches prereg
  (Holm specified only for the four H1 contrasts).
- N4: Liquidity filter (spread >8c or <5 trades excluded; both versions
  reported) — code matches prereg §6.5 exactly.
- N5: Price = quote midpoint; volume summed (flow), OI differenced (stock);
  windows 1/3/5d, headline 3d — all match.
- N6: Injuries excluded, variety taxonomy, T=0 = first report for unscheduled
  sports — registry implements; code is type-agnostic.
- N7: The 18 pre-2026-09-17 roster events labeled "exploratory" in prereg §4
  referred to the OLD pull's calibration set. This analysis uses only the new
  post-prereg summer pull (2026-06-01 onward) as confirmatory; the old data are
  not used at all. Interpretation documented here to avoid confusion.
- N8: `surprise` is carried in pair rows but no test conditions on it — prereg
  requires surprise to be RECORDED (scheduled macro, scheduled sports T-7),
  which the registry does; no prereg test uses it as a regressor.

## Open items for the registry build (not code deviations)
- O1: moneyness_steps for every macro pair = |bucket strike − consensus| in
  bucket steps, consensus = Bloomberg/WSJ survey median at T-1 (prereg §3).
  Missing → tier "M?", excluded from tier tests with warning (code handles).
- O2: kawhi_to_raptors T=0 = completion report (2026-09-14T18:56Z), not the
  ~June 30 framework — documented registry decision (prereg: T=0 = first
  report; the completion report is the first CONFIRMED report).

## D10 — Exclusion guard: registration-time precheck + fallback descriptive track (POST-PREREG process safeguard, added 2026-09-23)

- **Trigger:** `giannis_to_heat` — the sample's largest trade (KXNBA-27-MIA
  3c→8c on 2026-06-23, ~10x volume spike) — was FULLY excluded from
  confirmatory analysis because the KXNBA-27 contracts were listed only 8 days
  before T0 and failed the ≥5 baseline-obs rule, and the exclusion was buried
  in a footnote while the sports-cell headline ("14 events, −0.12c") was
  reported without it. A silent drop of a material event is a reporting
  failure regardless of whether the exclusion rule itself is correct.
- **What was added (none of this changes the prereg or any confirmatory
  result):**
  1. `hidden_files/coverage_precheck.py` — runs at registration time, after
     each event's pull lands. For every event in `event_registry.csv` it
     compares the earliest contract listing date in `kalshi_api_data_summer/`
     against T0−30 and prints a LOUD warning for any event whose confirmatory
     baseline will be thin. Zero tickers reaching ≥5 baseline obs = CRITICAL,
     with mandatory routing: extend the pull, use the fallback descriptive
     track, or document in `excluded_but_material.md`. Back-run on the
     current registry: 28 events → 7 OK, 20 warnings, 1 CRITICAL
     (giannis_to_heat, correctly caught). Report:
     `hidden_files/coverage_precheck_report.txt`.
  2. `hidden_files/analyze_fallback.py` — NON-CONFIRMATORY descriptive track
     reusing `analyze_kalshi_fixed.py`'s machinery. Any registered event with
     zero confirmatory pairs but ≥3 pre-T0 observations gets an abnormal-move
     computation on the maximum available pre-window (T−45..T−5 preferred,
     all pre-T0 data if thinner), labeled NON-CONFIRMATORY / POST-PREREG on
     every row. Output:
     `hidden_files/analysis_real/fallback_descriptive_3d.csv`.
     Current run: giannis_to_heat → 30 tickers (MIA +4.38c day-0 / +4.88c
     3d-window-end, vol 9.8x vs pre-mean); nba_opening_night and
     nfl_trade_deadline excluded from fallback too (future events, no
     post-T0 data).
  3. `hidden_files/excluded_but_material.md` — the register of fully excluded
     events with reasons and fallback results. `hidden_files/giannis_descriptive.md`
     + `giannis_descriptive.csv` — the Giannis per-ticker descriptive.
- **H3 supplementary tiers (also post-prereg):** prereg H3 was untestable as
  specified (sports pile into S1–S2; Sept-16 macro cluster all M?).
  `hidden_files/h3_tiers_supplementary.py` builds data-identified tiers —
  sports: within-cell terciles of pre-event midpoint; macro non-bucket:
  none exist (leg recorded empty); macro bucket: M0–M3 where consensus
  exists — and runs pair-level Kruskal-Wallis per cell (3d window), labeled
  POST-PREREG SUPPLEMENTARY / exploratory (within-event correlation noted).
  Output: `hidden_files/analysis_real/tier_supplementary_3d.csv`;
  note: `hidden_files/tier_supplementary_note.md`. Headline: |abnormal move|
  shows a strong monotone tier gradient in both cells (macro M0 11.6c → M3
  3.4c, p<0.0001; sports P3 1.73c → P1 0.22c, p<0.0001); signed moves show no
  sports gradient (p=0.13) and a hump-shaped macro gradient peaking at M1
  (full p=0.060, liquid-only p=0.005).
- RECOMMENDATION: **Keep as documented supplementary safeguards.** The
  confirmatory analysis and its exclusions are unchanged; what changes is
  that no material event can be excluded without a loud, pre-analysis
  warning and a labeled descriptive record. The paper's methods section
  should describe the guard and cite `excluded_but_material.md`.

## D11 — Summer data schema bug fixed (2026-09-24, pre-v2)

- **Bug:** `collect_kalshi_summer.py` parsed candles with live-endpoint keys
  only (`price.close_dollars`, `volume_fp`, `open_interest_fp`). Kalshi's
  `/historical` endpoint returns `price.close`, `volume`, `open_interest`
  (same dollar units). All 48 historical event-ticker pairs (17 distinct
  tickers, 176 candle rows) were written with empty bid/ask/last/volume.
  Affected: KXNBA-26-{CLE,DET,LAL,MIN,NYK,OKC,PHI,SAS} (May–Jun 2026 rows)
  and KXCPI-26JUN-T{±0.1..0.5} (Jul 12–15 rows). v1 analysis treated these
  as missing data (~1% of rows).
- **Fix:** backup at `kalshi_api_data_summer/market_data.csv.d11_bak`;
  re-parsed `kalshi_api_data_summer/raw/<ticker>.json` with the dual-schema
  reader (script: `hidden_files/fix_d11_summer.py`). Raw files had been
  overwritten by later narrower fetches for 5 tickers (101 rows: CLE/DET/NYK/
  OKC/SAS May–early-Jun), so those timestamps were re-fetched from the
  public Kalshi historical candlestick endpoint (same endpoint, read-only)
  and parsed identically. All 176 rows rewritten in place; row count
  unchanged (17,680); verification: **zero price-less rows**; spot-checked
  values match raw exactly; units confirmed dollars (max last 0.99).
- **Impact assessment:** the affected rows are settled/expired-contract
  history (2026 NBA championship contracts settled May–Jun 14; June-CPI
  contracts post-release) falling outside confirmatory baselines/windows,
  so v1→v2 headline deltas are expected to be ~zero. v2 re-runs everything
  on the corrected file regardless.
- **Guard added:** the exclusion-guard pipeline now includes a schema check
  (no price-less rows permitted in any ingested CSV).

## D12 — H2 sports→macro leg invalid as implemented; macro→sports leg significant-but-tiny (2026-09-24, v2 extended)

- **cross_sports_on_macro INVALID (design flaw, not a finding):** the A2
  batch used nearest-expiry macro contracts (2 KXFED + 2 KXCPI per sports
  event). Every large |abnormal move| in this leg is a CPI/Fed bucket
  expiring 7–25 days after T0 (e.g. KXCPI-26JUN-T-0.2: −0.40, −0.35, −0.35
  across the early-July sports events; KXCPI-26AUG-T1.0: −0.29 for
  von_miller_to_cowboys) — mechanical pull-to-par convergence as the
  release approaches, plus scheduled macro events inside the windows
  (Kawhi's KXFED window contains the 09-16 FOMC hike at T+2). The
  leg's headline (−8.2c, p=0.028, 3d) cannot be read as sports news moving
  macro markets. Verdict: **untestable with this contract selection.**
  Fix for a re-pull: far-expiry macro contracts (expiry > T0+60d), or
  expiry-filtered analysis. Documented, not hidden.
- **cross_macro_on_sports: technically rejects zero, economically nil.**
  8 macro events × 16-ticker sports baskets (far-expiry KXNBA-27/KXSB-27,
  no convergence issue): 1d +0.15c (p=0.0002), 3d +0.16c (p=0.0033, 95% CI
  [+0.07c, +0.25c]), 5d +0.16c (p=0.0041); liquid-only identical. The
  prereg prediction ("indistinguishable from zero") is formally rejected,
  but +0.16c is ~3% of the own-domain macro effect (+4.8c) — no
  economically meaningful cross-domain transmission. Possible contributors:
  market-wide risk drift on macro-news days; the 09-16 cluster window
  contains Kawhi-to-Raptors (09-14) for the sports baskets (small overlap,
  Kawhi's own measured effect ≈ 0).
- **Net H2 verdict:** one leg untestable-by-construction (A2), one leg a
  precise near-zero (+0.16c ± 0.09c). The falsification spirit holds —
  there is no economically meaningful cross-domain effect in either
  direction — but the prereg's literal "fail to reject" was not obtained
  on the macro→sports leg.

## D13 — v2 re-run on D11-corrected summer data (2026-09-24)

- All confirmatory tables re-run on the corrected
  `kalshi_api_data_summer/market_data.csv` (176 rows filled).
  Outputs: `hidden_files/analysis_real/*_v2.csv`.
- **Headline deltas vs v1: zero.** pooled/contrasts/event/pair results are
  byte-identical (diff-clean). H1c unchanged: p=0.00858 (3d), significant.
- Placebos shifted (filled rows entered placebo windows) but still PASS:
  macro_bucket p 0.221→0.062, sports_future p 0.176→0.952. The macro
  placebo at p=0.062 is closer to the 0.05 line than v1 — noted, not
  hidden; the method still passes its pre-registered validity gate.
- 27 giannis_to_heat KXNBA-26 pair-window exclusion reasons corrected:
  `insufficient_baseline_history` → `no_window_data` (with filled prices
  the baseline now builds, correctly revealing the contracts settled
  before T0). Exclusion itself unchanged and correct.

## D14 — Expanded scheduled samples (2026-09-24, batches B/C/D)

- **Batch B (prereg-mandated):** cpi_aug_release (2026-09-11T12:30Z, 26
  tickers, 20 usable pairs): abn −1.50c. scheduled_macro confirmatory is
  now n=2 (fomc_sep_hike +9.23c, cpi_aug_release −1.50c) — still
  descriptive-only per the n≥5 rule.
- **Batch C (prereg-definition-legit scheduled sports):** mlb_allstar_2026
  (30/30 usable, abn −0.03c); nba_draft_lottery_2026 (8/30 usable —
  22 KXNBA-26 contracts settled on playoff elimination, pre-only;
  abn +2.62c on the 8 survivors, **likely confounded by concurrent
  playoff games, NOT a clean lottery effect** — the lottery moves draft
  order → 2027 futures, but KXNBA-27 did not exist on 05-11; T0 date
  approximate); nba_draft_2026 **fully excluded** (KXNBA-27 listed 06-15,
  9 pre-days — Giannis-type; fallback descriptive: MIA +3.39c, 7.5x vol).
  scheduled_sports confirmatory = 4 usable events (mean +0.61c) — still
  n<5. H1b and H1d remain descriptive-only.
- **Batch D (SUPPLEMENTARY / POST-PREREG):** 5 FOMC + 8 CPI back to
  2026-01-01, all with complete data (Kalshi history reaches Dec 2025).
  sched_macro supplementary n=15: mean +2.21c overall (+1.71c on the 14
  M?-tier events, 95% CI [−0.83c, +4.25c], p=0.169 vs zero).
- **H1a supplementary** (unsched_macro n=8 vs sched_macro n=15):
  +4.83c vs +2.21c, t=1.43, **p=0.170 — not significant**. Direction
  matches the prereg prediction (unscheduled > scheduled) but the
  difference is not distinguishable from zero with these n's.
- **H1d supplementary** (sched_sports n=4 vs sched_macro n=15): still
  descriptive-only (sched_sports n<5).
- Outputs: `hidden_files/analysis_real/*_v2xd.csv` (extended
  confirmatory: H2 + scheduled), `*_v2supp.csv` (supplementary with
  batch D). Combined registry `hidden_files/pairs_combined.csv`
  (3,737 pairs; 2 Kawhi post-only KXCPI dropped); combined market data
  `hidden_files/market_data_combined.csv` (27,519 rows, 0 price-less).

## D15 — H2 sports→macro far-expiry re-pull: leg remains untestable (2026-09-24, POST-PREREG)

- **What was tried:** per D12's prescribed fix, re-pulled macro contracts
  around the same 15 unscheduled_sports events with far-expiry selection only
  (KXFED/KXCPI, close_time > T0+60d; `collect_h2farexpiry.py` →
  `kalshi_api_data_h2farexpiry/`: 15 events, 16 unique tickers, 737 rows,
  0 gaps). Falsification test re-run with identical machinery
  (`hidden_files/h2_farexpiry_test.py`), Kawhi excluded (09-11 CPI at T−3,
  09-16 FOMC at T+2 in window).
- **Result:** formal rejection (3d: −12.0c, 95% CI [−20.6c, −3.4c], p=0.011,
  n=10 events / 41 pairs; 1d p=0.005; 5d p=0.087) — but the rejection is
  SPURIOUS and the leg is UNTESTABLE as implemented:
  1. Every KXFED far-expiry leg failed FIX 7 (no daily candles most days;
     stub quotes bid=0.00/ask=0.99 when quoted) — far-expiry Fed buckets do
     not trade. The test rests entirely on KXCPI buckets.
  2. The 2026-06-17 FOMC repricing cliff (KXCPI-26AUG-T0.5: 24c→11c over
     06-17→06-20) sits inside 7 sports events' baselines, mechanically
     inflating baseline means (giannis −21.7c; the 07-01 trio −14.1c each —
     identical because same ticker/window, i.e. a common shock, not sports).
  3. The largest single move (von_miller −38.5c) is the hot 2026-08-12 CPI
     print (T−5) repricing October CPI buckets — macro news, not sports.
  4. Pseudo-T0 placebo (same machinery at T0−14d, no sports news) also shows
     large negative means (3d: −9.6c, p=0.119; 1d: −6.9c, p=0.058) —
     the test measures drift/macro news, not sports effects.
- **Verdict:** the far-expiry re-pull replaces pull-to-par bias (D12) with
  illiquidity + baseline contamination. H2 sports→macro remains UNTESTABLE
  with daily data; a valid test needs intraday candles around T0.
  Qualitatively consistent with H2's prediction: every large |move| traces
  to a dated macro cause; no sports-attributable move is visible.
- Outputs: `hidden_files/analysis_real/h2_farexpiry_{1d,3d,5d}.csv`,
  `h2_farexpiry_sensitivity.csv`, `h2_farexpiry_placebo.csv`,
  `h2_farexpiry_pairs.csv`, `h2_farexpiry_exclusions.csv`,
  `hidden_files/h2_farexpiry_verdict.md`.
