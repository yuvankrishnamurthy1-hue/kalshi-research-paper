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

## D16 — Baseline rule amendment: Giannis-type events admitted (2026-09-24, POST-PREREG, at Yuvan's explicit direction)

- **The uncomfortable origin, stated plainly:** this amendment exists because
  the prereg's ≥5-observation baseline rule excluded the sample's single most
  informative event. Giannis-to-Miami — the biggest trade in the sample —
  produced the biggest single-contract repricing in the sample (Heat title
  contract 2.6c→7c on trade day, ~10x volume), and the confirmatory machinery
  threw it out because its contracts were listed 8 days before T0, one or two
  baseline observations short of an arbitrary cutoff. Reporting an average
  "roster news barely moves markets" without the biggest roster move is
  defensible as prereg compliance and indefensible as science. Yuvan ordered
  the rule changed so this can never happen again. The 5-observation minimum
  was never derived from anything; discarding the most informative events
  over a 1–2 observation shortfall is worse than including them transparently.
- **The amended rule (D16):** the baseline window stays [T−30, T−5], but the
  minimum in-window observation count drops 5→3; pairs with 3–4 obs are
  flagged `thin_baseline`. Events with <3 in-window obs but ≥5 total pre-T0
  trading days use the full [T−30, T−1] pre-window as baseline, flagged
  `extended_baseline` (nearer-event days can carry rumor run-up — the flag
  is the disclosure). Events with <5 total pre-T0 obs remain
  descriptive-only. D16 supersedes FIX 7's [T−45, T−5] retry.
- **Admission rule:** D16 admits events *regardless of their measured move* —
  the rule is mechanical (observation counts), never conditioned on outcomes.
- **What changes:** in the confirmatory summer sample, `giannis_to_heat`
  enters with 26 pairs under `thin_d16` (baseline 4 obs); every other event
  stays `strict`. unsched_sports goes 14→15 events. In the extended sample,
  `nba_draft_2026` enters with 26 pairs under `thin_d16`, taking
  sched_sports to 5 events — which makes H1b testable there for the first
  time (still descriptive in the pure confirmatory sample, n=2).
- **Headline contrast under BOTH rules (reported, not chosen):**
  - H1c strict (14 vs 8): −0.12c vs +4.83c, t=−3.61, p=0.00858 (raw & Holm).
  - H1c D16 (15 vs 8): −0.15c vs +4.55c, t=−3.64, p=0.00819 (raw & Holm).
  - The headline survives. Giannis's *event-level* abnormal move is −0.58c —
    the event average dilutes MIA's +4.67c across 26 contracts (unaffected
    teams, as expected). The prereg's event-level averaging is doing exactly
    what it was designed to do; it just means the "big showing" lives at the
    contract level, which is why it is reported there too.
  - H1b extended+D16 (15 vs 5): −0.15c vs +0.38c, t=−0.92, p=0.409 — tested,
    null. First testable scheduleness-within-sports result; does not confirm
    H1b. (Confirmatory-sample H1b remains descriptive-only.)
- **New analysis:** size tiers for the 15 unsched_sports events, coded
  EX-ANTE from pre-event facts only (Big/Medium/Small; never from measured
  moves): `hidden_files/size_tiers.csv`. 3-day event-level means: Big (n=8)
  −0.18c [−0.39, +0.03]; Medium (n=3) −0.12c [−0.71, +0.46]; Small (n=4)
  −0.10c [−0.50, +0.31]. No event-level size gradient — the averaging
  dilutes; the involved-team contract moves (MIA +4.7c for Giannis) are
  reported at contract level. Tier table:
  `hidden_files/analysis_real/size_tiers_3d.csv`.
- **Outputs:** `hidden_files/analysis_real/*_d16.csv` (confirmatory sample
  under D16), `*_d16xd.csv` (extended sample under D16); machinery
  `analyze_d16.py`; run logs `run_log_d16.txt`, `run_log_d16xd.txt`.
- **Guard update:** `coverage_precheck.py` thresholds should be re-tuned to
  D16 (3-obs minimum) — logged as a to-do, not yet done.

### D16 addendum — placebo validity gate under D16 (2026-09-24)

- **The D16 run trips the prereg's placebo gate on macro buckets, and the
  reason is NOT thin baselines.** D16 placebo: macro_bucket mean −2.79c,
  p=0.036 → FAIL by the prereg's binary gate (|mean|<1c or p>0.05). The v2
  strict run had passed (mean −2.35c, p=0.062). Diagnosis: restricting the
  D16 placebo pairs to strict-baseline only still fails (n=43, mean −2.77c,
  p=0.042) — the admitted thin-baseline pairs are not the driver. The driver
  is a stable background drift: macro placebo means sit at −2.4c to −2.8c
  across draw sets and rules, with p hovering 0.036–0.062. "Quiet" macro
  days are not quiet — bucket markets drift (likely pull-to-par / regime
  drift over the window), and 50 draws are too few to stabilize a binary
  gate sitting exactly on the boundary.
- **Consequence, stated without spin:** the prereg's literal gate
  ("results are not reported as findings") was written for the strict
  method, under which it passes. Under D16 it marginally fails. The drift
  is NEGATIVE while the headline macro effect is POSITIVE (+4.8c) — it
  works against the finding, not for it — and H1c is a cross-market-kind
  contrast, but the honest reading is: macro absolute magnitudes carry a
  ±2–3c background-noise band, and the method's validity on macro buckets
  is marginal. Both rules' results are reported; nothing is hidden.
  Follow-up: larger placebo sample (prereg says 50; changing n would be a
  further deviation) and intraday placebo days.

## D17 — Involved-teams supplementary estimand (2026-09-24, post-prereg, at Yuvan's direction)

Prompt: Yuvan challenged the sports-side headline ("you think Myles Garrett didn't
affect how people bet on the Rams at all?"). He was right to. The prereg's
event-level aggregation averages ~30 team contracts per sports event, but a trade
mechanically reprices ~2 teams — so the sports cell mean is structurally diluted in
a way the macro cell (all FED contracts bet on the same decision) is not.

What was done: supplementary (NOT confirmatory) analysis of involved teams'
contracts only. Teams picked ex-ante from registry descriptions before any
computation: acquiring team + team trading away (trades), signing team + old team
(signings), extending team (extensions), team (comeback). Same 3-day abnormal-move
machinery, strict baseline rule. Four Boston observations dropped as contaminated:
Mitchell Robinson / Conley signings and Queta / Walsh extensions all read off the
Celtics' post-2026-07-01 Jaylen Brown trade collapse (same team, overlapping
windows) rather than their own news. Kawhi kept with a note: TOR repriced 0.5c ->
4.5c on the 2026-06-30 framework agreement; the 2026-09-14 T0 completion shows
~0 because the market priced it 2.5 months early (anticipation, not indifference).

Result (hidden_files/analysis_real/involved_teams_3d.csv): acquiring/keeping teams
+1.79c mean (n=11); teams giving up the player -1.01c mean (n=6; muted by the
0.5c price floor — MIL/CLE/LAC were already near zero and cannot fall further).
Blockbuster moves: MIA +4.25c, PHI +3.21c / +3.94c (Jaylen, LeBron), LAR +3.36c
(Garrett; T+1 print 16.5c vs 10.5c flat baseline — daily candle stamped midnight
ET, news broke mid-day), BOS -4.21c (gave Jaylen).

Interpretation: the H1c headline (-0.15c vs +4.55c) compares a diluted sports
number against an undiluted macro number. The fairer sports number is +1.8c for
acquirers. Macro still wins; the margin is narrower than the headline suggests.
Paper §4 and "What's shaky" §7 state this plainly.

## D18 — Involved-teams becomes the H1c estimand (2026-09-24, at Yuvan's direction)

Yuvan's objection, sustained: averaging all ~30 team contracts per sports event is
the wrong aggregation, not a defensible alternative. A trade mechanically reprices
~2 teams, so the prereg's sports cell mean is biased toward zero BY CONSTRUCTION
in a way the macro cell (every FED contract bets on the same decision) is not.
The original H1c significance (p=0.008) was partly purchased by this choice.

New primary estimand for H1c: the D17 involved-teams sample, acquiring/keeping
side, one observation per event (n=11). Both sides remain reported (give side
-1.01c, n=6, floor-muted); they are not averaged together, per Yuvan's "observe
that it was both." Same 3-day abnormal-move machinery, strict baseline rule.

Result (hidden_files/analysis_real/contrast_d18_involved.csv): sports +1.79c
(sd 1.72) vs macro +4.55c (sd 3.65), Welch t=-1.99, p=0.077, 95% CI for the gap
[-5.89c, +0.37c]. NOT significant at 5%. The direction favors macro, but with
11 vs 8 events the fair test is underpowered and cannot separate the two.

Paper verdict follows the fair aggregation: "sports trades move the involved
teams materially (+1.8c, blockbusters +2.3c); macro shocks move markets more on
average; the difference is not statistically decisive." The original p=0.008
result is still shown (it answers "did the average contract move?") with the
aggregation dependence stated explicitly. All three aggregations side by side
in paper §1. The team-level size gradient also appears under D18 (Big +2.34c,
n=8; Medium 0.00c, n=2; Small +1.00c, n=1 — descriptive, tiny n below Big).

## D19 — Market-time anchoring / jump detection (2026-09-24, at Yuvan's direction)

Prompt: Yuvan — "find when the price jumps up for the news, that's more important
than the technical day it happened." Reported T0s are news-report times; the
market often moves earlier (leaks) or a day later (midnight-ET candle artifact).

Method: for each involved team (D17/D18 sample, contaminated Boston obs excluded),
jump day = largest single-day midpoint move in [T0-10, T0+5]. Kawhi handled
manually: true jump was the 2026-06-30 framework agreement (0.5c -> 2.5c that day,
4.5c by Jul-02, 570x volume), 76 days before the "official" 2026-09-14 completion
T0 — outside any mechanical window; flagged in the data file. Detection threshold:
max |daily| < 0.75c within the window = "no clear jump" (MIL/CLE-give/MEM/LAC/MIN).

Results (hidden_files/analysis_real/jump_timing_3d.csv): 7 of 11 acquiring-team
jumps within ±2d of report — MIA +0d (+4.5c, 7x vol), PHI(JB) +1d (+4.0c, 963x),
LAR(Garrett) +1d (+6.0c, 206x), NE +1d (+1.0c, 160x), PHI(LBJ) +1d (+6.0c, 290x),
DAL -2d (+1.0c, 1x — weak, possible leak), LAR(Donald) +2d (+1.0c, 6x). Leaks:
BOS -7d (-3.0c), LAL -1d (-1.0c), CLE(Mitchell ext) -6d (+3.0c, 194x — priced at
free-agency open, not the announcement). The +1d lag on the big ones is the
midnight-candle artifact (news breaks mid-day ET, candle stamped midnight).

Jump-anchored abnormal moves (baseline [J-30,J-5], window [J,J+2]) reported as a
LABELED SENSITIVITY only, e.g. Garrett +5.06c vs T0-anchored +3.36c, Kawhi +3.48c
vs -0.04c. They are UPPER BOUNDS by construction (anchoring on the observed
maximum selects the largest move); T0-anchored are lower bounds (stale candles,
missed leaks). The formal H1c test stays T0-anchored — re-testing on selected
maxima would be circular. Paper §4 carries the timing table; "What's shaky" §4
updated with measured lead/lag.

## D20 — Post-prereg scheduled-macro extension packaged as supplementary (2026-09-24/25, at Yuvan's explicit direction)

Yuvan approved (2026-09-24) analyzing scheduled macro releases from Jan–Sep 2026
— 5 pre-window FOMC decisions (Jan 28, Mar 18, Apr 29, Jun 17, Jul 29) and 8
pre-window CPI releases (Jan 13 – Aug 12) — as SUPPLEMENTARY/EXPLORATORY only.
This is exploratory rather than confirmatory because the Jan–Aug events were
selected after confirmatory results were already observed (D14 had already run
the numbers). The preregistration window (FOMC Sep 16 + CPI Sep 11, batch B)
stands unchanged; preregistration.md and paper_v2.md untouched.

Packaging completed 2026-09-25:
- 14 registry rows added to hidden_files/event_registry.csv: 13 exploratory
  (fomc_2026_01_supp, fomc_2026_03_supp, fomc_2026_04_supp, fomc_2026_06_supp,
  fomc_2026_07_supp, cpi_2026_01_supp–cpi_2026_08_supp) + cpi_aug_release kept
  CONFIRMATORY (batch B; was missing from the registry — added, not relabelled).
- T0s verified against official schedules: Fed fomccalendars.htm (2:00 PM ET ->
  18:00Z), BLS cpi.htm schedule (8:30 AM ET -> 12:30Z). Feb-2026 CPI released
  Feb 13 (delayed 2 days by brief government shutdown); a stale search snippet
  showed Feb 11 — the live official schedule confirms Feb 13.
- Consensus recorded in hidden_files/extended_macro_consensus.csv (12 new rows,
  native m/m). UNVERIFIED after two search rounds: Dec-2025 CPI (Jan 13) and
  Mar-2026 CPI (Apr 10) headline consensus — surprise not recorded for those.
- D16 coverage precheck: all 13 events usable. 4 KXCPICORE-25DEC pairs excluded
  for insufficient_baseline_history (guard worked); 1 thin/fallback pair in
  cpi_2026_07_supp retained and flagged.
- No re-pull: reused D14 artifacts (pairs/market_data combined, 2026-09-24).
  Spot-check: independently recomputed 3-day abnormal moves for cpi_2026_07_supp
  (-0.63c) and fomc_2026_04_supp (-0.14c) from raw candles — match to <1e-12.
  Reporting convention: n_pairs = pairs passing baseline filter; event mean
  drops pairs with no window data; both counts reported per event.

Results (hidden_files/analysis_real/scheduled_macro_supp_3d.csv; 3-day,
event-level, exploratory):
- Supplementary-only (13 events): mean +1.96c, SD 4.30c
- Confirmatory-only (2 events):   mean +3.86c, SD 5.36c
- Combined (15 events):           mean +2.21c, SD 4.50c (matches D14)
- H1a supplementary: unscheduled macro +4.55c (n=8) vs scheduled macro +2.21c
  (n=15) — direction as predicted, Welch p~0.170, not significant.
- Run log: hidden_files/analysis_real/run_log_supp_3d.txt

## D20-fix — unverified CPI consensus rows resolved (2026-09-24)

Three headline-consensus gaps left by the D20 pass are now filled from fresh
searches (all values m/m, rounded): Dec-2025 CPI (rel. Jan 13): headline +0.3%
actual vs +0.3% FactSet consensus (0.0pp), core +0.2% vs +0.3% (-0.1pp). Mar-2026
CPI (rel. Apr 10, Iran-war energy shock): headline +0.9% vs +0.9% (0.0pp), core
+0.2% vs +0.3% (-0.1pp). Apr-2026 CPI (rel. May 12): headline +0.6% matched
consensus (0.0pp; was "unverified"). extended_macro_consensus.csv now 21 rows,
0 unverified. No analysis changes (D20 used abnormal moves, not surprise-scaled
moves); this is documentation completeness.

## D21 — batch-C T0 corrections + registry completion (2026-09-24)

- **Snag:** the D14 batch-C pull ran while web search was down and used
  approximate T0s for all three added scheduled-sports events. Verified
  2026-09-24 against USA Today / NBC Sports / ESPN:
  - `nba_draft_lottery_2026`: was 2026-05-11 → **2026-05-10** (Sun, 3pm ET).
  - `nba_draft_2026`: was 2026-06-24 (round 2) → **2026-06-23** (round 1,
    8pm ET — the news night for futures).
  - `mlb_allstar_2026`: 2026-07-14 confirmed correct.
- **Fix:** re-ran all three events through the pipeline's own
  `analyze_d16.analyze_pair` (same D16 baseline rules) with corrected T0s
  (`hidden_files/rerun_d21_t0fix.py`). Results: lottery +2.62¢ (8 pairs,
  strict), draft −0.54¢ (26 pairs, thin_d16), all-star −0.00¢ (30 pairs,
  strict) — the all-star moved from −0.03¢ to −0.00¢ on time-of-day only.
  **H1b extended is unchanged in substance:** 15 surprise (−0.15¢) vs 5
  scheduled (+0.38¢), Welch p = 0.40 (was 0.41) — still not significant.
- **Registry gap closed:** the three batch-C events were analyzed in D14 but
  never added to `event_registry.csv`. Added now with verified T0s,
  `t0_confidence=verified`, exploratory designation, and the lottery's
  playoff-confound flag in `expectation_note`.

## D22 — September-16 cluster-collapsed sensitivity (2026-09-24)

- **What:** tariff_eu_threat, russia_sanctions_bill, trump_truth_fed all hit
  2026-09-16 on the same contracts, overlapping the scheduled FOMC decision —
  not independent observations. Collapsed the three into one observation at
  their mean (+8.57c) and re-ran both macro contrasts on event-level means.
- **Results** (`hidden_files/analysis_real/cluster_collapsed_sensitivity.csv`):
  - H1c involved-teams: macro +3.21c (n=6, sd 3.12) vs sports +1.79c (n=11),
    Welch p = 0.338 (was p = 0.077 uncollapsed).
  - H1a: unsched macro +3.21c (n=6) vs sched macro +2.21c (n=15),
    Welch p = 0.571 (was p = 0.170 uncollapsed).
- **Reading:** the sensitivity goes the *wrong way* for the headline — the
  macro edge was partly triple-counted September 16. Paper's "What's shaky"
  section updated; verdict unchanged (not decisive), now with less room for
  a generous reading.
