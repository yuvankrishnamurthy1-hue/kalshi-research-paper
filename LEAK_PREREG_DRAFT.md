# Preregistration (DRAFT, not locked): Do Kalshi markets know before the news breaks?

**Researcher:** Yuvan Krishnamurthy
**Status:** DRAFT. It becomes binding only when I sign and date it below and commit it to the public repo before **2026-12-01 00:00 UTC**. Every event in the confirmatory sample happens after that timestamp, so no confirmatory data exist yet when this is locked.
**Pilot:** the design was calibrated on past events (`leak_pilot.py`, results in `hidden_files/analysis_real/leak_pilot_*.csv`). The pilot is exploratory and is reported separately. None of its events can enter the confirmatory sample.

---

## 1. Question

When a sports transaction or a scheduled macro release reprices a Kalshi contract, how much of that repricing happens before the first credible public report? Sports front offices, agents and players know about a trade or signing before it's reported. Macro data like CPI and the FOMC decision are embargoed until an exact, pre-announced second. If Kalshi prices drift toward the eventual move before the report, that's information getting into the market early, and the size of that drift should be much bigger for sports than for embargoed macro data.

## 2. Hypotheses

- **L1 (primary).** In the 24 hours before the first report, the involved sports contract drifts toward its eventual move more than its own normal day-to-day noise: the median of z24 (section 5) is above 0. One-sided.
- **L2 (primary).** The median z24 is higher for sports transactions than for scheduled macro releases. One-sided.
- **Why z24 and not the 7-day pre-report share.** In the pilot, the 7 days before a Fed decision usually contained another data release that moved the same contract (the September 11 CPI sits inside the window for the September 16 FOMC decision), so the 7-day share mixes in earlier public news. The last 24 hours are clean. The 7-day pre-report share (PRS) is still computed and reported under L4(d).
- **L3 (placebo, must hold for L1 and L2 to count).** Contracts of teams that aren't involved in the transaction show no such drift: the median z24 for uninvolved teams, signed by the involved team's eventual move direction, is indistinguishable from 0 (two-sided, p > 0.05). If it fails, L1 and L2 aren't reported as findings.
- **L4 (secondary, reported whatever the result).** Pre-report share and z24 compared across (a) trades vs. signings vs. extensions, (b) the offseason stratum vs. the in-season stratum, and (c) NBA vs. NFL, and (d) the 7-day pre-report share (PRS), sports vs. macro. Descriptive when a group has fewer than 8 events.

## 3. Sample window and cutoff

- Events from **2026-12-01 00:00 UTC through 2027-06-30 23:59 UTC**.
- Data pull and analysis start on **2027-07-10**, after every event has its full post-report window.
- No events are added or removed after the lock except under the exclusion rules in section 4.4, applied by script.

## 4. Event inclusion (mechanical, no hand-picking)

### 4.1 Sports transactions (NBA and NFL)

Every transaction that meets **all** of these:

1. It's a trade, free-agent signing, contract extension, head-coach hire or firing, or retirement/un-retirement, involving an NBA or NFL team.
2. Size rule (any one is enough):
   - NBA: the player made an All-Star or All-NBA team in any of the last three seasons, **or** the contract's average annual value is at least $15M.
   - NFL: the player made a Pro Bowl or All-Pro team in any of the last three seasons, **or** the contract's average annual value is at least $10M, **or** the player is a quarterback who started at least 4 games in the current or previous season.
   - Head-coach changes always qualify.
3. It's first reported by a Tier-1 source (Shams Charania, Adam Schefter, Ian Rapoport, another ESPN/NFL Network insider, or an official team release) with a timestamp to the minute. **T0 = timestamp of the first such report.** The post on X counts if it comes before the article.
4. The involved team's Kalshi championship contract (KXNBA or KXSB, next season resolving) is open and has a midpoint of at least 2¢ at T0 − 7 days. Below that, the contract sits on the floor and can't show a move.

The transaction list is built from the ESPN NBA and NFL transaction pages for the window, filtered by a script against the size rule. Every candidate is logged with a pass or fail reason, including the ones that fail.

**Stratum flag.** Every sports event gets `season_stratum = in_season` when it happens between the team's first and last regular-season or playoff game, and `offseason` otherwise. Both strata are analyzed. The primary tests (L1, L2) pool them, and L4(b) reports them separately. In-season events also get a `game_in_window` flag when the team plays inside [T0 − 24h, T0 + 24h].

### 4.2 Scheduled macro releases (comparison group)

Every FOMC rate decision and every CPI release in the window. T0 = the official release time (CPI 8:30 AM ET; FOMC statement 2:00 PM ET), converted to UTC with the correct daylight-saving offset.

**Contract:** the KXFED contract for the **next** FOMC meeting after T0 (it reprices on the news but doesn't settle at the release). Strike = the one whose midpoint at T0 − 7 days is closest to 50¢, chosen from pre-release prices only.

### 4.3 Placebo contracts (L3)

For each sports event, every other team in the same league whose championship contract has a midpoint of at least 2¢ at T0 − 7 days.

### 4.4 Exclusions (applied by script, every one logged)

- **Overlap:** the same team has another qualifying event inside [T0 − 7d, T0 + 24h]. Both events are dropped from L1 and L2 and reported separately.
- **No data:** fewer than 48 hourly candles with a valid quote in [T0 − 30d, T0 − 8d].
- **Timestamp:** no minute-level first-report time can be found.
- **Macro window overlap:** another CPI release, FOMC decision or employment report falls inside [T0 − 25h, T0). The event is dropped from L1 and L2. For the PRS analysis in L4(d), the event is also dropped if one falls inside [T0 − 7d, T0).

## 5. Measurement

Hourly Kalshi candles over [T0 − 30d, T0 + 3d]. Midpoint = (bid + ask) / 2. When bid is 0 and ask is above 0, ask / 2. Empty hours are filled forward from the last quote.

With s = the sign of the total move:

- pre = mid(T0 − 1h) − mid(T0 − 7d)
- pre24 = mid(T0 − 1h) − mid(T0 − 25h)
- post = mid(T0 + 24h) − mid(T0 − 1h)
- total = pre + post
- **PRS = pre / total**, computed only when |total| ≥ 1¢ (smaller totals are logged as "no move")
- **z24 = s × pre24 / max(SD(24-hour changes over [T0 − 30d, T0 − 8d]), 0.5¢)**. The 0.5¢ floor is half of Kalshi's 1¢ tick. Without it, a contract that never moved in the baseline period gives an undefined or infinite z24, which happened for several contracts in the pilot.
- Secondary: pre-report abnormal volume = volume in [T0 − 24h, T0 − 1h] divided by the average 23-hour volume over [T0 − 30d, T0 − 8d].

## 6. Tests

- L1: one-sided Wilcoxon signed-rank, median sports z24 > 0. A sign test (share of events with z24 > 0, excluding zeros) is reported alongside, because hourly prices in 1¢ steps produce many exact zeros.
- L2: one-sided Mann-Whitney U, sports z24 > macro z24. Permutation test on the difference in medians reported alongside.
- L3: two-sided Wilcoxon signed-rank on placebo z24, median = 0.
- Holm correction across L1 and L2. α = 0.05.
- Robustness, always shown: a 3-day pre-window instead of 7 days; a 2¢ movement threshold for PRS; offseason only; dropping events with `game_in_window`.

## 7. Power

The pilot (section 8) gives the spread of PRS and z24 in each group. The macro group will have about 12 releases (7 CPI and 5 FOMC in the window). The sports group is expected to be much larger, because the window covers the NBA trade deadline, NFL free agency and the start of the NBA offseason. **Pilot spreads.** Across the 18 pilot macro releases, z24 had a standard deviation of 1.34. Across the pilot sports contracts it was 1.88, but only 7 sports contracts had a usable z24, so I use the macro figure as the noise estimate.

**L1 (sports z24 > 0).** Simulated power of a one-sided Wilcoxon test at α = 0.05, with z24 drawn from a normal distribution with SD 1.34:

| True median z24 | 15 events | 20 events | 30 events | 40 events |
|---|---|---|---|---|
| 0.50 | 0.36 | 0.47 | 0.61 | 0.73 |
| 0.75 | 0.62 | 0.75 | 0.89 | 0.96 |
| 1.00 | 0.84 | 0.93 | 0.99 | 1.00 |

With the sign test, detecting 70% of events drifting the right way (vs. 50% by chance) takes about 40 non-zero events for 80% power (0.81 at 40, 0.73 at 30).

**What this means.** About 30 qualifying sports events give roughly 90% power to detect a median z24 of 0.75, which is a moderate leak signal. They give about 60% to detect a median of 0.5. For comparison, the one clear pilot case (LeBron James) had z24 = 4.9. L2 compares against only about 12 macro releases, so it has noticeably less power than L1, and a null on L2 alongside a positive L1 will be reported as exactly that. If fewer than 15 sports events qualify by June 30, 2027, the results are reported as descriptive and the window is not extended.

## 8. What the pilot is and isn't

The pilot measures the same quantities on summer 2026 sports events and Jan–Nov 2026 macro releases. It was run before this plan was locked, and it shaped the window lengths and the 1¢ threshold, so it's labeled exploratory everywhere. The confirmatory result is whatever the post-lock events show, including a null.

---

**Signed:** ______________________ **Date (UTC):** __________
