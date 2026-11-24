# Referee report: "How Kalshi Prediction Markets React to News" (draft v3, 2026-09-24)

*Written as if for a peer-reviewed economics or finance journal. Reviewed 2026-11-24 against the repo at commit `8ad9cad` (D23), plus the re-analysis in `analyze_d24.py`.*

**Recommendation: Reject in current form, encourage resubmission as a redesigned study.** The data work is careful and the transparency is far above what most student (and plenty of professional) work shows. The deviation log, the exclusion register, and the willingness to publish nulls are real strengths. But once two measurement problems are fixed, the paper's main comparison has no result left. And the design as it stands can't produce one at this sample size. The good news: the project already holds the pieces of a much stronger paper (see §4).

---

## 1. What the paper claims

1. Surprise macro news moves Kalshi prices more than surprise sports news: +4.55¢ vs +1.79¢ (D18), p = 0.077, "directional but not decisive."
2. Scheduled vs unscheduled news makes no detectable difference (H1a p = 0.17, H1b p = 0.40).
3. Cross-domain leakage is economically nil in both directions (H2).
4. Methodological lessons: averaging 30 teams dilutes a 2-team trade (D18), and a mechanical baseline filter silently dropped the biggest event (Giannis, D16).

## 2. Major issues

### M1. The headline comparison measured sports and macro with different rulers. *(Fixed in D24.)*
The macro cell's "abnormal move" comes from `analyze_d16.analyze_pair`: the midpoint **at the end** of the 3-day window, minus the T−30…T−5 baseline, with the window anchored at the **exact T0 timestamp**. The sports involved-team numbers in D17/D18 were computed separately, with no committed script. They take the **average** of three daily midpoints starting at **midnight of the T0 date**, so one of the three candles is usually from *before* the news.

| Team | Legacy (paper) | Same rule as macro |
|---|---|---|
| PHI (Jaylen Brown) | +3.21¢ | **+6.38¢** |
| PHI (LeBron) | +3.94¢ | **+5.78¢** |
| LAR (Garrett) | +3.36¢ | **+4.72¢** |
| CLE (Mitchell) | +2.83¢ | **+3.67¢** |
| MIA (Giannis) | +4.25¢ | **+4.67¢** |

The legacy rule understates sports by about a third. Measured like-for-like, sports involved teams average **+2.49¢** (n = 11, with floor-pinned Memphis counted as 0) vs macro **+4.55¢**, p = 0.19 (Welch), 0.16 (permutation).

### M2. Three of the eight "surprise macro" events are the scheduled Fed hike.
`tariff_eu_threat`, `russia_sanctions_bill` and `trump_truth_fed` are all dated 2026-09-16, the day of the FOMC hike. They are measured on the same KXFED contracts over the same window. Their moves (+8.12, +8.12, +9.47¢) are the hike's own move (+9.26¢). Two of them are numerically identical because they are literally the same calculation. D22 collapsed them into one observation, but even one observation is still the FOMC hike, sitting in the *unscheduled* cell. The paper already drops four Boston sports events for exactly this kind of contamination (D17). Applying the same rule to macro:

| Comparison (3-day, same ruler) | Sports | Macro | p (Welch / perm) |
|---|---|---|---|
| As published (D18) | +1.79¢ (11) | +4.55¢ (8) | 0.077 / 0.043 |
| Same ruler | +2.49¢ (11) | +4.55¢ (8) | 0.19 / 0.16 |
| Same ruler, Sep-16 collapsed | +2.49¢ | +3.21¢ (6) | 0.64 / 0.61 |
| **Same ruler, Sep-16 dropped** | **+2.49¢** | **+2.14¢ (5)** | **0.77 / 0.80** |
| D24: data through Nov 24, Sep-16 dropped | +1.58¢ (20) | +0.94¢ (7) | 0.59 / 0.59 |
| D24, size of move only | 2.36¢ | 2.23¢ | 0.85 |

(Source: `hidden_files/analysis_real/d24_contrasts.csv`.)

**After both corrections, sports moves are as large as or larger than macro moves.** "Macro reprices harder" was mostly the Fed hike counted three or four times, compared against an understated sports number. The honest headline is now *"no detectable difference between domains."*

### M3. The cells are defined by the calendar, not by information.
- **Nvidia earnings are scheduled.** The date is announced weeks ahead, yet the event sits in the *unscheduled* macro cell (both Aug 26 and the D24 Nov 17 addition).
- **"Scheduled vs unscheduled" is the wrong variable.** The prereg's theory is that scheduled news is *priced in*. That's a claim about **surprise size**, not about the calendar. A CPI print that exactly matches consensus should move nothing, and one that misses by 0.3pp should move a lot. You have the CPI consensus data (`extended_macro_consensus.csv`) but never use it. The paper defines `surprise` for every event and then leaves the column empty.
- **Sports surprises are never measured.** The T−7 "expectation rule" from the prereg was logged as text but never turned into a number.

**Fix:** regress |Δp| on a measured |surprise| (CPI: actual − consensus; FOMC: decision vs pre-meeting Kalshi probability; trades: the market's own pre-report probability of the move, or a rumor/no-rumor flag). That directly tests "priced in."

### M4. Cents aren't comparable across these contracts.
A 1¢ move on a 3¢ championship longshot is a 33% change in odds. On a 60¢ Fed threshold contract it's under 2%. The paper reports log-odds (FIX 4) but never uses them in a test. And the "30 teams vs 2 teams" debate (D18) is a symptom of having no market-level measure at all.

**Fix:** treat each market as a probability *distribution*. Championship futures spread 100% across ~30 teams, and CPI/Fed buckets spread it across outcomes. Then measure news as the **distance the whole distribution moved**, for example total-variation distance ½·Σ|p_post − p_pre| (or Hellinger / KL). This:
- settles the aggregation fight cleanly: a trade that moves MIA +4¢ and the rest −4¢ in total scores 4¢, not 4/30;
- works identically for sports and macro;
- needs no hand-picked "involved teams" (which is itself a researcher degree of freedom).

### M5. The baseline is a price *level*, so drift reads as news.
Abnormal move = window price − mean price over T−30…T−5. Any trend shows up as an "effect": longshot decay, in-season game results, the steady repricing of Fed paths. The placebo already says so. Quiet macro days drift −2.8¢ (p = 0.036), and **the method fails its own validity gate** (prereg §6.6: "if the placebo fires … results are not reported as findings"). The paper notes this but still reports the macro magnitudes.

**Fix:** use a change measure. Price at T+k minus price just before T0, net of the same change for matched control contracts or placebo days (a difference-in-differences). Report the placebo distribution next to every effect.

### M6. Daily candles can't see news that lands in minutes.
Kalshi serves 1-minute candles (D23 proved it). Daily candles stamped at midnight ET put the news day's pre-news hours and post-news hours in the same bar. That causes the "+1 day lag" artifacts, makes every speed claim impossible, and forces date-only T0s for most macro events.

**Fix:** make ±6-hour minute windows the primary design and keep daily as a robustness check.

### M7. Power.
After corrections, the between-event SD is about 2–3¢ in both cells. With 5–11 events per cell, the smallest difference you could reliably detect (80% power, α = .05) is about 3–4¢. That's bigger than any plausible true gap. Detecting a 1.5¢ difference needs roughly **35–50 independent events per cell**. No amount of re-analysis of this sample fixes that; only more events can.

### M8. Confirmatory status is gone. Say so.
There are 24 deviations, and several were made *after seeing results* and in the direction the author wanted: D16 (to admit Giannis), D18 (to change the estimand after the sports null), D19, D20. Each is honestly labeled, which is good, but together the study is now **exploratory**. Leaving "confirmatory" language in the paper invites a forking-paths critique. The right move is to call this a pilot and preregister a clean confirmatory study (see §4) on data that doesn't exist yet. Your daily collector is already producing it.

### M9. The sample isn't "all qualifying events."
The prereg says "we collect *all* qualifying events in each type." Victor Wembanyama's $252M extension (Jul 10, Shams) and Amen Thompson's $208M extension are inside the window and missing. The registry was built from what was memorable, which selects on newsworthiness. **Fix:** an objective, mechanical inclusion rule (e.g., every transaction involving a player above a value threshold such as prior-season VORP/AV, or every move reported by Shams/Schefter with a dollar value ≥ $X), applied with a script to a complete transaction log.

### M10. Scheduled-macro contracts settle at the event they're measuring.
The scheduled cell uses release-specific contracts (KXFED-26SEP, KXFED-26OCT, KXCPI-26OCT…), which **resolve at the release itself**. Their "abnormal move" over the 3-day window includes the price collapsing to 0¢ or 100¢ at settlement, which has nothing to do with surprise. Unscheduled-macro contracts aren't tied to the event, so they don't do this. H1a and H1d are therefore biased toward big scheduled moves. In D24, scheduled releases moved *more* by size (4.1¢ vs 2.2¢), the opposite of H1a. That's the same trap D12 hit for H2. **Fix:** measure scheduled releases on the price path *up to the final pre-settlement quote*, or on the *next* meeting's or month's contract (which the news reprices but which doesn't settle).

## 3. Minor issues

1. **Midpoint rule.** `midpoint()` requires bid > 0. Floor contracts (bid 0 / ask 1¢) silently fall back to last trade, or to nothing (Memphis was dropped this way). That affects far-tail macro buckets too. Use (0 + ask)/2 or flag explicitly.
2. **README contradicts the paper.** It still leads with the superseded p = 0.0082 "statistically solid" headline and says H2 sports→macro is untestable. *(Fixed in this pass.)*
3. **Reproducibility.** The involved-teams, jump-timing (D19) and cluster-collapse (D22) numbers had no committed script, and `build_combined.py` hard-codes `/home/hatch/...`. *(Involved teams and D22 now reproduced by `analyze_d24.py`; the path is fixed.)*
4. **No literature review.** At minimum, engage with Wolfers & Zitzewitz (2004, *JEP*) on prediction markets; Gürkaynak & Wolfers (2005) on macro-release derivatives ("economic derivatives"), the closest prior work on the macro side; Snowberg, Wolfers & Zitzewitz on prediction markets and macro news; Croxson & Reade (2014, *Economic Journal*) on how fast betting markets absorb goals (seconds); Lucca & Moench (2015) on pre-FOMC drift; and the favorite-longshot bias literature, which directly affects how longshot futures move.
5. **Voice and structure.** The paper reads like a lab notebook (D-numbers inline, "at Yuvan's direction," "say it straight"). A journal version needs the standard order: Abstract → Introduction (question, contribution, preview of results) → Related work → Institutional background (how Kalshi contracts work) → Data → Method → Results → Robustness → Conclusion, with deviations in an appendix.
6. **"Unscheduled sports" timing.** First-report T0 is right, but Kawhi (priced 76 days early) and Boston (7 days early) show that the first *Tier-1* report is often not the first *public information*. Report the share of the move that happened before T0 as an outcome, not a nuisance.
7. **In-season sports.** The D24 NFL trades happen during the season, when futures also move on game results every weekend. Their 3-day windows contain games. Either control with same-week non-involved teams or keep them in a separate cell.

## 4. Should the idea change? Yes. Two strong options.

### Option A (recommended): "Do prediction markets know before the news breaks?"
Your best findings are already this paper: Kawhi priced 76 days before completion, Boston falling 7 days before the Jaylen report, Cleveland pricing the Mitchell extension 6 days early. Turn that into the question:

> *What share of the eventual repricing of a Kalshi contract happens **before** the first Tier-1 public report, and is that share larger for sports transactions (where team insiders exist) than for macro releases (where data are embargoed)?*

- **Outcome:** pre-report share = (p at T0 − p at T−k) / (p at T+k − p at T−k), on minute candles.
- **Why it matters:** this is the integrity question regulators are fighting over *right now*. Examples: the NBA's personnel trading ban and its CFTC information-sharing MOU (Oct 2026), the New York subpoenas, and the CFTC's swap rule. It's publishable, and it ties straight into your college-essay thesis.
- **Why it's feasible:** the macro side is a clean placebo, because BLS embargoes make pre-release leakage illegal and rare. Kalshi minute data exist, and your collector is running.
- **Literature hook:** insider trading and information leakage before M&A announcements (the classic pre-announcement run-up studies). You'd be the first to do it on event contracts.

### Option B: keep the 2×2, but run it properly as a prospective, preregistered study
- New prereg, locked **before** Dec 1, 2026, covering events Dec 2026 → Jun 2027 (NBA trade deadline in February, NFL offseason in March, six FOMC meetings, six CPI releases).
- Estimand: distribution-shift (TV distance) on minute windows, change-based with placebo controls (M4–M6).
- Main regressor: measured surprise, not the calendar (M3).
- Mechanical, exhaustive event inclusion (M9), with a power target of ≥ 35 events per cell (M7).
- The current paper becomes the pilot that motivates every one of those design choices. That's a strong story in itself.

### Also viable, smaller
- **C.** Are Kalshi CPI/Fed markets better forecasters than the economist consensus? (A Gürkaynak & Wolfers replication on Kalshi; settled outcomes back to 2021, so a large n.)
- **D.** Favorite-longshot bias in Kalshi championship futures, using settled seasons.

## 5. What the author should keep no matter what
- The deviation log and exclusion register (rare and valuable).
- The Giannis and aggregation stories, reframed as *why* the redesign uses distribution-level, minute-level measures.
- The D23 intraday machinery: it's the seed of Option A.
