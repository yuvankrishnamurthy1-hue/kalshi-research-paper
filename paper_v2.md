# How Kalshi Prediction Markets React to News

**Yuvan Krishnamurthy — draft v3, 2026-09-24**

*Written strictly from computed results. The preregistration (locked 2026-09-21, `preregistration.md`) was never edited. Anything done after the lock is labeled plainly.*

---

## The one-page version

**The question.** When news breaks, how much do Kalshi prediction-market prices move — and does it matter whether the news was scheduled (like a Fed meeting) or a surprise (like a blockbuster trade), and whether it's about the economy or sports?

**What we did.** We collected daily Kalshi prices around 28 real events from summer 2026: 8 surprise macro shocks (tariff threats, a pipeline strike, an Nvidia earnings, …), 15 surprise sports moves (trades, signings, extensions), plus a few scheduled events (FOMC meeting, NFL kickoff, …). For each event we compared prices after the news to prices *before* the news, and tested whether the differences hold up statistically. The whole plan was written down and locked before we ran the numbers.

**What we found.**
1. **Surprise macro news moves Kalshi prices a lot; the fair sports comparison is underpowered.** Macro shocks averaged +4.55¢ across 8 events. The original test averaged all ~30 teams' futures per sports event (−0.15¢, p=0.008) — but that aggregation dilutes trades that mechanically reprice 2 teams. Re-tested fairly on involved teams only (D18): sports +1.79¢ vs macro +4.55¢, p=0.077 — the direction favors macro, but it's not statistically significant with 11 vs 8 events.
2. **The biggest trade in the sample is now included.** Giannis-to-Miami was thrown out by a technicality (its contracts were listed 8 days before the trade — one observation short of an arbitrary cutoff). We changed the rule so this can never happen again, re-ran everything, and the headline survived. The Heat's title price tripled on trade day (2.6¢ → 7¢, ~10× normal volume) — the single biggest repricing in the sports data.
3. **Big, medium, and small sports moves all look the same on average.** We graded the 15 sports events by player stature before looking at any price data. Event-level averages: Big −0.18¢, Medium −0.12¢, Small −0.10¢ — no gradient. The action is at the individual-contract level (Miami's odds, not the 30-team average).
3b. **At the team level, the market absolutely repriced the teams involved.** New supplementary analysis: acquiring teams gained **+1.8¢ on average (n=11)** — the Rams +3.4¢ on the Garrett trade (Super Bowl odds ~11% → ~16%), the 76ers +3.2¢ and +3.9¢ on the Jaylen Brown and LeBron moves, the Heat +4.3¢ on Giannis. Teams giving up stars lost −1.0¢ on average, muted because several were already priced near zero (you can't fall below 0¢). The "sports don't move" headline is about the average of 30 teams; the teams in the trade moved a lot.
4. **Scheduled vs. unscheduled is still an open question.** We don't have enough scheduled events for a clean test. The best available comparison (8 surprise vs 15 scheduled macro events, going back to January) points the predicted way but isn't significant (p = 0.17).
5. **Macro news barely leaks into sports markets** (+0.16¢ — real but ~3% of the own-market effect). Whether sports news leaks into macro markets can't be tested with daily data; we tried twice and both attempts failed for documented mechanical reasons.

**What it means.** Kalshi's macro markets reprice hard on surprises (+4.6¢). Sports trades reprice the involved teams hard too (+1.8¢ on average, +2.3¢ for the blockbusters: Rams +3.4¢, 76ers +3–4¢ twice, Heat +4.3¢). Macro looks bigger, but the study can't statistically prove the gap with the fair aggregation — 11 vs 8 events isn't enough. The original "significant" headline depended on an aggregation that was unfair to sports, and the paper now says so.

**What's shaky.** The macro result leans on a cluster of events that all hit on September 16 and share the same contracts — they're not truly independent observations. Our "quiet day" placebo test on macro markets is borderline: quiet days drift about −2.8¢ on their own, so macro magnitudes carry a noise band. And several sports moves were heavily rumored beforehand, which shrinks what the announcement itself can show.

---

## Words we use (read this once)

- **Abnormal move.** How much a price moved *because of the news* = actual price minus what the price was doing before the news. Measured in cents on the dollar (a "4.8-cent move" means the contract's implied probability moved ~4.8 percentage points).
- **Baseline.** The "before" — the average price over the 30-to-5 trading days before the event. The event itself and the 4 days right before it are excluded so anticipation doesn't pollute the comparison.
- **Event window.** The "after" — the 1, 3, or 5 trading days starting at the news. Headline results use 3 days.
- **P-value.** The probability of seeing a result this extreme if nothing were really happening. p = 0.008 means ~0.8% — strong evidence something real happened. p = 0.4 means "could easily be luck."
- **Confidence interval (CI).** The range where the true value probably sits. A 95% CI of [+0.07¢, +0.25¢] means we're fairly confident the true effect is small and positive.
- **Confirmatory vs. supplementary.** Confirmatory = the test we promised in the locked plan. Supplementary = extra analysis we did afterward, labeled honestly, never mixed into the confirmatory results.
- **Placebo test.** We run the exact same machinery on random quiet days with no news. If the method "finds" effects on quiet days, the method is broken.

---

## The setup

Earlier work had a confound: every scheduled event studied was macro, every surprise was sports — so nobody could tell whether markets react to *scheduleness* or to *domain*. We fixed that with a 2×2 design: scheduled vs. surprise, crossed with macro vs. sports.

**The four cells and what we asked about each comparison:**
- **H1a** — within macro: do surprises move prices more than scheduled releases?
- **H1b** — within sports: do surprise roster moves move prices more than scheduled sports events?
- **H1c** — holding "surprise" fixed: do macro and sports news move prices differently?
- **H1d** — holding "scheduled" fixed: same question for scheduled news.
- **H2** — falsification: macro news should move macro markets but *not* sports futures, and vice versa. If we saw big cross-domain moves, something would be wrong with the design.
- **H3** — within a market, do some contracts react more than others (e.g., favorites vs. longshots)?

**The power rule** (locked in advance): any cell with fewer than 5 events gets means only — no p-values presented as findings.

---

## The data

**Summer pull (the confirmatory sample):** 483 tickers, 17,680 daily price rows, 28 registered events, full windows from 45 days before to 10 days after each event. Prices are quote midpoints — the average of the bid and ask — not last-trade prices, so thin trading doesn't fake a move.

**Extended pull:** cross-domain tickers for H2, the August CPI release the original plan required but the first pull missed, new scheduled sports events (MLB All-Star Game, NBA draft lottery, NBA draft), and every FOMC/CPI release back to January 2026 as a supplementary sample.

**A bug we caught and fixed:** the collector misread Kalshi's historical data format and wrote 176 rows with no prices. We re-parsed them from the raw files, verified zero empty rows remained, and re-ran everything. The confirmatory tables came out byte-identical — the headline never depended on the bad rows.

---

## What we found

### 1. The headline, corrected: the prereg's aggregation was unfair to sports (H1c)

The locked plan averaged **all ~30 team contracts** per sports event. That's the wrong aggregation: a trade mechanically reprices 2 teams, not 30 — so the sports cell was diluted by construction in a way the macro cell (every FED contract bets on the same decision) was not. At Yuvan's direction we re-ran the headline test the fair way **(D18)**: the sports sample is the **involved teams' contracts** — one observation per event for the acquiring/keeping team (both sides are reported; they're not averaged together, and the give side is floor-muted, see §4).

| | Sample | Average abnormal move (3-day) |
|---|---|---|
| Surprise sports (involved teams, D18) | 11 events | **+1.79¢** |
| Surprise macro (all contracts) | 8 events | **+4.55¢** |

Welch t-test on the gap: t = −1.99, **p = 0.077** — not significant at the 5% level (95% CI for the gap: [−5.89¢, +0.37¢]).

Say it straight: **the fair version of the headline test does not reach significance.** The direction still favors macro (−2.76¢ gap), and the old diluted aggregation was significant (p = 0.008), but that significance was bought partly by an aggregation that suppressed the sports side. With the fair aggregation the study is underpowered (11 vs 8 events) and cannot statistically separate the two. The honest bottom line: *sports trades move the involved teams materially (+1.8¢ on average, +2.3¢ for the blockbusters); macro shocks move markets more on average; the data can't say the difference is statistically decisive.*

For the record, all three aggregations side by side:

| Aggregation | Sports | Macro | p |
|---|---|---|---|
| Prereg rule, strict (Giannis excluded) | −0.12¢ (n=14) | +4.83¢ (n=8) | 0.0086 |
| D16 (Giannis included, all teams) | −0.15¢ (n=15) | +4.55¢ (n=8) | 0.0082 |
| **D18 (involved teams only)** | **+1.79¢ (n=11)** | +4.55¢ (n=8) | **0.077** |

**Speed:** no reliable difference in how *fast* prices adjust (median 11 vs 28 hours to reach half the move, p = 0.085 — not significant, and daily data can't say much about speed anyway).

### 2. Giannis is in now — and the rule that excluded him is fixed (D16)

Here's the uncomfortable story, told straight. The original plan required 5 pre-event price observations to build a baseline. The Giannis-to-Miami trade — the biggest trade in the sample — had contracts listed only 8 days before the trade, giving 4 observations. One short of an arbitrary cutoff. So the machinery threw out the most informative event in the data, and the first draft reported "roster news barely moves markets" without mentioning it. That was wrong.

**D16 (the amendment, at Yuvan's direction):** the baseline window stays the same, but the minimum drops from 5 observations to 3 (flagged as "thin baseline" when under 5). Events with fewer than 3 in-window observations but at least 5 total pre-event trading days use the full 30-days-before window as baseline (flagged "extended"). Under 5 total pre-event days stays descriptive-only. The rule is mechanical — it admits events regardless of how they moved, never cherry-picked by outcome.

**What changed:** Giannis enters with 26 contracts under the thin-baseline flag. The NBA draft enters the extended sample the same way (29 of 38 contracts). The H1c headline barely moves (above). An exclusion guard now screams at registration time whenever a contract lists too close to an event, so nothing drops silently again.

**Giannis, the actual numbers:** the Heat's 2027 title contract sat flat at 2.6¢ for 8 days, then printed 7¢ on trade day (bid 6¢/ask 8¢) — **+4.4¢ on the day, +4.7¢ over the 3-day window**, on **~10× normal volume**, and the move stuck. The Bucks' contract sat at 0.5¢ and never moved (thin book, already near zero). Across all 26 Heat/Bucks/other-team contracts the average was −0.58¢ — because most teams had nothing to do with the trade. That's the thing about event-level averages: they dilute. The "big showing" lives at the contract level, and it's real: the Heat's title odds roughly tripled that day.

**One more honest caveat:** Giannis had been rumored on the market since February, so the 2.6¢ pre-price already baked in some chance of a Heat move. The +4.4¢ is the *announcement surprise* — a lower bound on the trade's total effect.

### 3. Variety of moves: trades, signings, extensions, comebacks — at the team level

We graded all 15 sports events by player stature **before looking at any price data** — never from the measured moves:

- **Big (8):** Giannis, Myles Garrett, A.J. Brown, Jaylen Brown, Kawhi Leonard, LeBron James, Aaron Donald, Donovan Mitchell — All-Stars, All-Pros, award winners, franchise players.
- **Medium (3):** D'Angelo Russell (former All-Star, now journeyman starter), Mitchell Robinson (starting-caliber center, $15.8M/yr deal), Brian O'Neill (starting tackle, $24M/yr extension).
- **Small (4):** Von Miller (37, rotational rusher now, $5.5M deal), Mike Conley (38, backup PG), Neemias Queta (rotation big), Jordan Walsh (deep bench).

Two assignments are genuinely uncertain: Russell (big name, medium current role) and Miller (Hall of Fame legacy, small current role). Both are flagged in the data file.

At the **event level** (all 30 teams averaged) the tiers showed no gradient — Big −0.18¢, Medium −0.12¢, Small −0.10¢, all near zero with overlapping CIs. That's dilution again, not a finding. At the **team level** (D18, involved teams only) the gradient appears:

| Tier | Involved-team moves | Mean |
|---|---|---|
| Big (8) | +4.25, +3.94, +3.36, +3.21, +2.83, +0.67, +0.49, −0.04 | **+2.34¢** |
| Medium (2) | 0.00, 0.00 | 0.00¢ |
| Small (1) | +1.00 | +1.00¢ |

Blockbusters reprice the involved teams ~2.3¢ on average; smaller names, smaller moves. (Medium/Small n is tiny — descriptive only.) And the **variety of move types** Yuvan asked for survives into the clean sample — all four kinds are represented, and every kind moved its team:

| Move type | Events (clean) | Acquiring-team mean | The moves |
|---|---|---|---|
| Trade (6) | Giannis, Garrett, A.J. Brown, Jaylen, DLO, Kawhi | **+1.91¢** | +4.25, +3.36, +3.21, +0.67, 0.00, −0.04 |
| Signing (2) | LeBron, Von Miller | **+2.47¢** | +3.94, +1.00 |
| Extension (2) | Mitchell, O'Neill | **+1.42¢** | +2.83, 0.00 |
| Comeback (1) | Donald | **+0.49¢** | +0.49 |

(Two Celtics signings and two Celtics extensions were dropped as contaminated — their windows read off the July-1 Jaylen Brown trade, not their own news. They're in the data file, flagged, not hidden.)

One cautionary tale inside the data: a 76ers contract swung +6¢ around the Jordan Walsh extension — a Celtics bench player's deal moving Philly's title odds makes no sense and is almost certainly unrelated noise, which is exactly why we average across contracts and don't chase single-contract spikes.

### 4. What actually happened on the sports side: the team-level story (supplementary)

The event-level average (−0.15¢) answers "how much does the *average championship future* move on roster news?" — and the honest answer to the obvious objection is that this is the wrong question for sports. A trade mechanically reprices 2 teams, not 30. So we ran a supplementary analysis (post-prereg, labeled as such): for each event, the abnormal move of the **involved teams'** contracts only — teams acquiring or keeping the player vs. teams giving him up. Involved teams were picked from the registry descriptions before computing anything; the numbers come from `hidden_files/analysis_real/involved_teams_3d.csv`.

| Type | What happened | Team | Before → after | Abnormal move |
|---|---|---|---|---|
| Trade | Giannis → Heat | MIA | 2.8¢ → 7.0¢ | **+4.3¢** |
| Trade | Jaylen Brown → 76ers | PHI | 1.6¢ → 4.8¢ | **+3.2¢** |
| Trade | Jaylen Brown → 76ers | BOS | 12.9¢ → 8.7¢ | **−4.2¢** |
| Signing | LeBron → 76ers | PHI | 5.6¢ → 9.5¢ | **+3.9¢** |
| Signing | LeBron → 76ers | LAL | 3.5¢ → 2.5¢ | −1.0¢ |
| Trade | Garrett → Rams | LAR | 10.8¢ → 14.2¢ | **+3.4¢** |
| Trade | A.J. Brown → Patriots | NE | 3.5¢ → 4.2¢ | +0.7¢ |
| Trade | A.J. Brown → Patriots | PHI (NFL) | 5.3¢ → 4.5¢ | −0.8¢ |
| Signing | Von Miller → Cowboys | DAL | 3.5¢ → 4.5¢ | +1.0¢ |
| Extension | Mitchell extends | CLE | — | +2.8¢ |

Averages over the clean set: **acquiring/keeping teams +1.79¢ (n=11); teams giving up the player −1.01¢ (n=6).**

**The D18 headline test** uses the acquiring/keeping side (one observation per event — both sides are in the table above, but they're not averaged together, and the give side is floor-muted). Against macro's +4.55¢ (n=8): Welch t = −1.99, **p = 0.077**, 95% CI for the gap [−5.89¢, +0.37¢]. Not significant at 5%. The direction favors macro, but with 11 vs 8 events the fair comparison is underpowered — the data can't statistically separate them.

**The size gradient and the move-type variety are in §3** — both appear once you look at involved teams instead of 30-team averages.

Three things the team-level data show:

1. **The market absolutely repriced the Rams.** Flat at 10.5¢ for weeks, then 16.5¢ the day after the Garrett news — Super Bowl odds jumping from ~11% to ~16%. The +0.03¢ event-level average buried it under 31 teams that had nothing to do with the trade. (One timing wrinkle: our daily candles are stamped at midnight ET and the news broke mid-day, so the move shows at T+1, not T0 — the 3-day window still catches it.)
2. **The give side is muted by a floor.** The Bucks, Browns, and Clippers were already priced near 0.5¢ — you can't fall below zero. So "loses a superstar" prints ~0 while "gains a superstar" prints +3 to +4¢. Asymmetric by construction.
3. **Anticipation is real and visible.** Kawhi → Raptors shows −0.0¢ at the official September completion — because Toronto's contract had already jumped 0.5¢ → 4.5¢ on **June 30**, when the trade framework was agreed. The market priced it 2.5 months before our T0. That "zero" is a timestamp artifact, not indifference. (Dropped from the clean averages: four Boston observations — the Mitchell Robinson and Conley signings, the Queta and Walsh extensions — whose windows read off the Celtics' post-Jaylen-trade collapse on/after July 1 rather than their own news.)

**The structural asymmetry, resolved by D18:** macro events reprice *every* contract in the market — all FED contracts are bets on the same decision. Sports trades reprice 2 of 32. The prereg's event-level aggregation was therefore the wrong estimand for sports, and the original "significant" H1c was partly an artifact of it. D18 re-tests with the fair aggregation: the gap shrinks (−2.76¢), the p-value rises to 0.077, and the honest verdict is "directional but not decisive." (See "What's shaky" §7.)

**When did the market actually move? (D19).** The "official" timestamps above are report times, not market times — so we let the price data locate the jump: for each involved team, the largest single-day midpoint move in [T0−10, T0+5] (data: `hidden_files/analysis_real/jump_timing_3d.csv`).

| Team | Reported T0 | Market jump | Move | Volume vs normal |
|---|---|---|---|---|
| MIA (Giannis) | Jun 23 | Jun 23 (+0d) | +4.5¢ | 7× |
| PHI (Jaylen) | Jul 1 | Jul 2 (+1d) | +4.0¢ | 963× |
| LAR (Garrett) | Jun 1 | Jun 2 (+1d) | +6.0¢ | 206× |
| NE (A.J. Brown) | Jun 1 | Jun 2 (+1d) | +1.0¢ | 160× |
| PHI (LeBron) | Jul 24 | Jul 25 (+1d) | +6.0¢ | 290× |
| DAL (Von Miller) | Aug 17 | Aug 15 (−2d) | +1.0¢ | 1× |
| LAR (Donald) | Aug 30 | Sep 1 (+2d) | +1.0¢ | 6× |
| BOS (give Jaylen) | Jul 1 | Jun 24 (−7d) | −3.0¢ | 2× |
| LAL (give LeBron) | Jul 24 | Jul 23 (−1d) | −1.0¢ | 4× |
| CLE (Mitchell ext) | Jul 7 | Jul 1 (−6d) | +3.0¢ | 194× |
| TOR (Kawhi) | Sep 14 | Jun 30 (−76d) | +2.0¢ that day (+4.0¢ within days) | 570× |

Three patterns. **(1) The market usually moves within a day of the report** — the +1d lag is a data artifact (candles are stamped at midnight ET; news breaks mid-day), and the 100–900× volume spikes confirm these are news-driven repricings, not noise. **(2) Leaks are visible in the price path**: Boston started falling 7 days before the Jaylen report; Cleveland priced the Mitchell extension at free-agency open, 6 days before the announcement. **(3) Kawhi is the extreme**: Toronto's contract jumped 0.5¢ → 4.5¢ on the June 30 framework agreement — 76 days before the "official" September completion our T0 used. The measured −0.04¢ at T0 isn't market indifference; it's a timestamp error, and the jump-anchored abnormal move (+3.5¢) is the economically true number. (Kawhi's jump was located manually — outside the mechanical detection window — and is flagged as such in the data file.)

Two honest caveats on D19. First, anchoring on the observed jump mechanically selects the largest move, so jump-anchored magnitudes (e.g., Garrett +5.1¢ vs T0-anchored +3.4¢) are **upper bounds**; T0-anchored are lower bounds (they include stale pre-news candles and miss leaked moves). The formal H1c test stays T0-anchored — re-testing on selected maxima would be circular. Second, "no detectable jump" (Bucks, Browns, Clippers, Grizzlies, Vikings) means what it says: those contracts never moved, mostly because they were already priced near zero.

### 5. Scheduled vs. unscheduled: still an open question (H1a, H1b, H1d)

The scheduled cells are too thin for clean confirmatory tests — that's a data fact, not a choice:
- **H1a** (macro): 8 surprise vs 1 scheduled event (+4.8¢ vs +9.2¢) — descriptive only. With the August CPI release added: 8 vs 2. Still descriptive.
- **H1b** (sports): 15 vs 2 (−0.15¢ vs −0.08¢) — descriptive only in the confirmatory sample.
- **H1d** (scheduled sports vs scheduled macro): 2 vs 1 — descriptive only.

**But D16 plus the extended sample makes H1b testable for the first time:** adding the draft, lottery, and All-Star Game takes scheduled sports to 5 events. Result: 15 surprise (−0.15¢) vs 5 scheduled (+0.38¢), p = 0.41 — **not significant**. The first real test of "do surprise roster moves move markets more than scheduled sports events" comes back null. (This uses post-plan data additions, so it's labeled accordingly — but the answer is now an actual answer, not a shrug.)

**H1a's best available shot** (8 surprise vs 15 scheduled macro events back to January, supplementary): +4.8¢ vs +2.2¢, p = 0.17 — the predicted direction, not significant. "Scheduled news is already priced in" is not established by this study.

### 6. Cross-domain check (H2): leakage is economically nil one way, untestable the other

- **Macro news → sports markets:** +0.16¢, 95% CI [+0.07¢, +0.25¢], p = 0.003. Formally nonzero — but it's ~3% of the own-market effect. There is no *meaningful* transmission from macro news into championship futures. (Part of it may just be market-wide drift on macro-news days.)
- **Sports news → macro markets: untestable with daily data.** We tried twice. First attempt used contracts expiring days after the events — their "moves" were just mechanical convergence to par plus a Fed meeting contaminating one window. Second attempt used far-expiry contracts — but those barely trade (stub quotes), and a June Fed repricing sitting inside the baselines manufactured fake negative moves. The formal test "rejects" (p = 0.011) but the rejection is spurious: every large move traces to a dated macro cause, and a placebo with no sports news shows the same drift. A real test needs intraday data. Qualitatively, no sports-attributable move is visible anywhere — consistent with the hypothesis, but not a statistical finding.

### 7. Which contracts react most (H3)

The original tier coding didn't discriminate (every sports contract landed in one tier), so no conclusion there. Under data-driven tiers (supplementary, exploratory): at-the-money macro contracts moved ~3× more than tail contracts (11.6¢ → 3.4¢, monotone), and expensive sports contracts moved ~8× more than cheap ones (1.7¢ → 0.2¢, monotone) — partly mechanical, since a 25¢ contract has more room to move than a 1¢ one. Direction-wise there's no sports gradient: expensive teams' contracts don't systematically move *up* more.

---

## What's shaky — read before citing

1. **The September cluster.** Three macro observations share a date, the same contracts, and the FOMC decision; they're not independent. The macro leg is effectively ~6 event-days, not 8 events. No cluster-collapsed sensitivity has been run.
2. **Contamination.** One "unscheduled" event's +9.3¢ is mostly the scheduled FOMC decision echoing (the post came after the decision). Another shares its day with a hot CPI print.
3. **The placebo gate is marginal.** Our quiet-day check on macro markets fails its own pass/fail line under the amended rule (−2.8¢ average drift, p = 0.036; the line is p > 0.05). This isn't caused by the new thin baselines — the strict-baseline placebo fails too. "Quiet" macro days just drift. The drift is *negative* while our headline effect is *positive* (it works against the finding, not for it), but treat macro magnitudes as carrying a ±2–3¢ noise band.
4. **Anticipation.** Giannis was rumored for months; LeBron and Garrett had weeks-long rumor trails. Rumors inside the baseline window shrink what the announcement can show. D19 measured the actual jump days: most moves land within ±2 days of the report (the +1d lag is the midnight-candle artifact), but Boston leaked 7 days early, Cleveland priced the Mitchell extension 6 days early, and Kawhi priced 76 days early at the framework agreement. Read every sports "zero" as "no *announcement-day* repricing," not "no effect."
5. **Coverage.** The draft lottery's +2.6¢ rests on 8 thin contracts and is likely confounded by concurrent playoff games. Two scheduled events (NBA opening night, NFL trade deadline) are in the future — no data yet.
6. **Resolution.** Daily candles only. Several macro events have date-only timestamps (±1 day on day-0). No intraday speed claims, no intraday H2 test.
7. **Structural asymmetry in H1c — found, fixed, and it changed the verdict.** Macro events reprice every contract in their market; sports trades reprice 2 of 32 teams. The prereg's event-level average therefore structurally understated sports, and the original p=0.008 was partly bought by that choice. D18 re-tests on involved teams only: +1.79¢ vs +4.55¢, p=0.077 — not significant. The direction still favors macro, but with 11 vs 8 events the fair test is underpowered. Anyone citing the "significant" version must cite the aggregation it depends on.

---

## Appendix: every deviation from the locked plan, in plain English

The preregistration (`preregistration.md`) was locked 2026-09-21 and never edited. Everything below is a documented deviation — the full technical text lives in `hidden_files/prereg_deviations.md`.

- **D1 — Speed measure.** The plan's wording for "time to reach half the move" degenerated on step-shaped price moves, so we used the non-degenerate reading: first time the price reaches half its eventual move.
- **D2 — Baseline fallback.** If the 30-to-5-day baseline was thin, the code retried 45-to-5 days, flagged. (Superseded by D16.)
- **D3 — Multiple testing.** The Holm correction is applied to both the size and speed legs of the four comparisons, not just size.
- **D4 — Placebo design.** Instead of purely random quiet days, placebos match the real events' weekday, time of day, and market regime, and can't overlap real events.
- **D5 — H2 split.** The cross-domain check runs as two separate one-way tests (macro→sports, sports→macro) instead of one pooled test.
- **D6 — Scheduled macro under-coverage.** The plan said "every" FOMC/CPI release from Aug 14; the first pull only got the FOMC. We added the missed CPI release afterward.
- **D7 — Fuzzy timestamps.** Several macro events only have date (not time) stamps, so "day 0" may be off by a day. The 3-day headline window is robust to this; the 1-day window less so.
- **D8 — Tier tests.** The contract-tier test also runs on absolute move size, not just speed — the natural companion the plan implied.
- **D9 — Stale notes.** Old plan text about minute-level data refers to an earlier data pull; this study is daily candles throughout.
- **D10 — Exclusion guard.** After the Giannis incident: a registration-time check that loudly flags events whose contracts list too close to T0, a fallback descriptive track so excluded events are still reported, and a public register of every exclusion with its reason.
- **D11 — Data bug.** The collector misread Kalshi's historical format, leaving 176 rows priceless. Fixed by re-parsing; the re-run reproduced every confirmatory table exactly.
- **D12 — H2 first attempt failed.** Nearest-expiry contracts made the sports→macro leg mechanical garbage; documented, not reported as a finding.
- **D13 — v2 re-run.** The full confirmatory re-run on corrected data (see D11).
- **D14 — Extended samples.** Cross-domain tickers, the missed CPI release, new scheduled sports events, and the January–September scheduled-macro window.
- **D15 — H2 second attempt failed.** Far-expiry contracts replaced one bias with illiquidity plus baseline contamination; the leg is untestable with daily data.
- **D16 — Giannis amendment.** Baseline minimum 5→3 observations (thin ones flagged); fallback to the full 30-day pre-window when needed (flagged). Exists because the old rule excluded the sample's most informative event over a 1-observation shortfall. The headline is reported under both rules; it survives both. Side effect: the macro placebo gate flips from marginal-pass to marginal-fail — a stable background drift, not a thin-baseline artifact (see "What's shaky" §3).
- **D17 — Involved-teams supplementary estimand.** The prereg's event-level average (all 30-odd teams) structurally dilutes sports trades, which mechanically reprice ~2 teams. Added a post-prereg supplementary analysis: abnormal moves of involved teams' contracts only (acquiring/keeping vs. giving), teams picked from registry descriptions before computing. Four Boston observations dropped as contaminated (they read off the July-1 Jaylen Brown trade, not their own news). Result: acquirers +1.8¢ (n=11), givers −1.0¢ (n=6). Data: `hidden_files/analysis_real/involved_teams_3d.csv`.
- **D18 — Involved-teams becomes the H1c estimand (2026-09-24, at Yuvan's direction).** Yuvan's objection stands: the all-teams average was the wrong aggregation, not a defensible choice — it biases the sports cell toward zero by construction. H1c re-tested with the D17 involved-teams sample (acquiring/keeping side, one observation per event; both sides reported, not averaged together): +1.79¢ (n=11) vs +4.55¢ (n=8), Welch t=−1.99, **p=0.077** — not significant at 5%. The original p=0.008 is still reported (it answers "did the average contract move?"), but the paper's verdict follows the fair aggregation: direction favors macro, evidence is not decisive. All three aggregations are shown side by side in §1. Numbers: `hidden_files/analysis_real/contrast_d18_involved.csv`.
- **D19 — Market-time anchoring / jump detection (2026-09-24, at Yuvan's direction).** Reported timestamps are report times, not market times. For each involved team, the jump day = largest single-day midpoint move in [T0−10, T0+5] (Kawhi located manually: the true jump was the 2026-06-30 framework agreement, 76 days before the "official" T0 — outside any mechanical window — verified 0.5¢→2.5¢ that day, 4.5¢ by Jul-02, on 570× volume). Findings: 7 of 11 acquiring-team jumps land within ±2 days of the report (the +1d lag is the midnight-ET candle artifact; 100–900× volume spikes confirm news-driven repricing); Boston leaked 7 days early, Cleveland priced the Mitchell extension 6 days early at free-agency open. Jump-anchored abnormal moves (baseline [J−30,J−5], window [J,J+2]) are reported as a labeled sensitivity — they are **upper bounds** (anchoring on the observed max selects the largest move); T0-anchored are lower bounds. The formal H1c test stays T0-anchored; re-testing on selected maxima would be circular. Data: `hidden_files/analysis_real/jump_timing_3d.csv`.

---

## Reproducibility

- Plan: `preregistration.md` (locked, unedited). Deviations: `hidden_files/prereg_deviations.md` (D1–D16).
- Events: `hidden_files/event_registry.csv` (+ `event_registry_extended.csv`). Expectations/rumor trails: `hidden_files/expectations.md`.
- Data: `kalshi_api_data_summer/` (confirmatory), `kalshi_api_data_extended/`, `kalshi_api_data_h2farexpiry/`, combined `hidden_files/market_data_combined.csv`.
- Code: `analyze_kalshi_fixed.py` (strict rule), `analyze_d16.py` (amended rule), collectors `collect_kalshi_summer.py` / `collect_extended.py` / `collect_h2farexpiry.py`, guard `hidden_files/coverage_precheck.py`, fallback `hidden_files/analyze_fallback.py`.
- Outputs: `hidden_files/analysis_real/` — `*_v2.csv` (strict confirmatory), `*_d16.csv` (D16 confirmatory), `*_v2xd.csv` / `*_d16xd.csv` (extended), `*_v2supp.csv` (supplementary), `size_tiers_3d.csv`, `tier_supplementary_3d.csv`, `giannis_descriptive.csv`, `exclusions*.csv`, run logs.
- Size tiers (ex-ante): `hidden_files/size_tiers.csv`. Exclusion register: `hidden_files/excluded_but_material.md`.
