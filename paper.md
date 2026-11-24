# Do Prediction Markets Know Before the News Breaks? Pre-Report Price Drift on Kalshi

**Yuvan Krishnamurthy**

*Manuscript draft, 2026-11-24. Prepared as a Stage 1 Registered Report: introduction, methods, pilot data and a locked analysis plan, submitted before the confirmatory data exist.*

---

## Abstract

Prediction markets are supposed to turn scattered information into a price, but nobody has measured when that information shows up. I study Kalshi, a CFTC-regulated event-contract exchange, using two kinds of news: NBA and NFL transactions, where front offices, agents and players know the outcome before it's public, and scheduled CPI releases and FOMC decisions, where the data are embargoed until an exact, pre-announced second. In Study 1, a daily event study of 34 events from January to November 2026, I find that a star trade or signing moves the involved team's championship contract by about as much as surprise macro news moves Fed contracts (+2.5¢ vs. +2.1¢). Earlier versions of this analysis reported a large macro advantage, but it came from measuring the two sides differently and from counting the September 16 FOMC hike as three separate "surprises." Study 2 is a pilot using hourly prices. It measures how much of each repricing happened before the first Tier-1 report. It covers 11 summer 2026 sports transactions and 18 macro releases. The pilot is too small to answer the question, but it does two useful jobs. It found a clean example of the pattern I'm testing for: Philadelphia's title contract rose 6¢ in the 24 hours before LeBron James's trade was reported, almost five times its normal daily variation, and didn't move after the report. It also exposed two design problems that would have sunk the full study. Most involved sports contracts sit so close to the floor that they barely move hour to hour. And the week before a Fed decision usually contains another data release, so macro contracts look like they "move early" for reasons that have nothing to do with leaks. The confirmatory test runs on every qualifying event from December 2026 through June 2027, under a preregistration locked before the first event.

**Keywords:** prediction markets, Kalshi, information leakage, event study, sports betting, FOMC, CPI, market integrity

---

## 1. Introduction

When the Bucks traded Giannis Antetokounmpo to the Heat on June 23, 2026, the Heat's Kalshi championship contract went from about 3¢ to 7¢ within a day. That's the market doing what it's supposed to do. The harder question is when it did it. If the price had already started moving before Shams Charania posted the trade, then somebody trading on Kalshi knew first.

That question matters now for reasons that go beyond one trade. In October 2026 the NBA named Kalshi one of its preferred prediction-market exchanges, banned league and team personnel from trading NBA event contracts, and signed an information-sharing agreement with the CFTC on suspicious trading. Several states are suing Kalshi on the theory that its sports contracts are gambling, and the CFTC claims them as derivatives under its jurisdiction. Everyone in that fight is making assumptions about who trades on these markets and what they know, and there's very little data on it.

I came at this from the other direction. My first study (Study 1 here) asked a simpler question: does Kalshi react more to macro news or to sports news, and does it matter if the news was scheduled? The answer, once I measured it properly, was that a star trade moves the involved team about as much as a macro surprise moves the Fed contracts. But while I was building that study, the most interesting cases kept being the ones where the price moved before the official timestamp. Toronto's contract jumped from 0.5¢ to 4.5¢ on June 30, when the Kawhi Leonard framework was agreed, 76 days before the trade was officially completed. Boston's contract started falling 7 days before the Jaylen Brown trade was reported. Those cases weren't noise in my event study. They were a different and better question.

The paper has three parts:

1. **Study 1** reports the reaction-size study and shows how two measurement choices, both of which look harmless, created a false "macro beats sports" result.
2. **Study 2** is a pilot that measures the pre-report share of each repricing on hourly data, with embargoed macro releases as the comparison group.
3. **The confirmatory plan** (section 7) tests the leak hypothesis on events that haven't happened yet, using a mechanical inclusion rule and a preregistration locked before December 1, 2026.

## 2. Related work

Wolfers and Zitzewitz (2004) lay out why prediction-market prices can work as forecasts and what market design does to that. Gürkaynak and Wolfers (2005) study the closest predecessor to Kalshi's macro contracts, the "economic derivatives" auctions on U.S. data releases, and find that market-based expectations were at least as accurate as survey forecasts. On speed, Croxson and Reade (2014) show that betting prices absorb a goal in a soccer match within seconds, which is the benchmark for public sports information. On leakage, the closest literature is the pre-announcement run-up in merger targets: Keown and Pinkerton (1981) document target prices moving before the public announcement, and Meulbroek (1992) ties a large part of that run-up to illegal insider trading identified in SEC cases. Lucca and Moench (2015) show that stocks drift up before scheduled FOMC announcements, which is a reminder that pre-release movement can happen even when the data themselves are embargoed. Snowberg and Wolfers (2010) document the favorite-longshot bias in betting markets, which matters here because most championship contracts are longshots priced under 10¢.

As far as I can find, nobody has measured pre-report drift on regulated event contracts, or compared it across information environments with different leak risk.

*[Citations to be verified against the original articles before submission.]*

## 3. How Kalshi contracts work

A Kalshi contract pays $1 if an event happens and $0 if it doesn't, so its price in cents reads as a market probability. The championship contracts I use (series KXNBA and KXSB) list one contract per team for the next title. The Fed contracts (KXFED) are threshold contracts for each FOMC meeting, for example "the upper bound of the fed funds rate is above 3.75% after the October meeting." The CPI contracts (KXCPI and KXCPICORE) do the same for each monthly inflation print. I use the midpoint between the best bid and best ask rather than the last trade, because a single trade in a thin market can sit far from where the market actually is. All data come from Kalshi's public API, which serves daily, hourly and one-minute candles, including for settled markets.

## 4. Study 1: How much do prices react?

### 4.1 Design

I preregistered a 2×2 design on September 21, 2026: scheduled vs. unscheduled news, crossed with macro vs. sports. The sample covers 34 events from January to November 2026 on daily candles:

- **Unscheduled sports:** 20 trades, signings and extensions.
- **Scheduled sports:** 7 events, such as the NBA draft and the NFL trade deadline.
- **Unscheduled macro:** 7 shocks, such as Gulf pipeline strikes and tariff proclamations.
- **Scheduled macro:** FOMC decisions and CPI releases.

The abnormal move is the contract's midpoint at the end of a 3-day window, minus its average over days T−30 to T−5. For sports, I measure the involved team's contract, since a trade reprices two teams and not thirty. Several changes came after I'd seen results, every one of them is logged (deviations D1 to D24 in the repository), and because of that I treat Study 1 as exploratory.

### 4.2 Two measurement errors and what fixing them did

An earlier version of this study reported that surprise macro news moved prices +4.55¢ and sports trades only +1.79¢ (p = 0.077). Two problems produced that gap.

**The two sides were measured with different rulers.** The macro number was the price at the end of the window, measured from the exact news time. The sports number was the average of three daily prices starting at midnight on the news day, and one of those three prices was usually from before the news broke. Measured the same way as macro, the 76ers moved +6.4¢ on the Jaylen Brown trade instead of +3.2¢, and the Rams moved +4.7¢ on the Myles Garrett trade instead of +3.4¢.

**Three of the eight macro "surprises" were the Fed hike.** The EU tariff threat, the Russia sanctions bill and Trump's post about the Fed all happened on September 16, the day the FOMC raised rates, and they were measured on the same Fed contracts. Their moves (+8.1¢, +8.1¢ and +9.5¢) are the hike's own move (+9.3¢) counted three more times. I'd already dropped four Boston signings because their windows overlapped the Jaylen Brown trade, so I applied the same rule here.

| Comparison (3-day window) | Sports, involved team | Surprise macro | p (Welch / permutation) |
|---|---|---|---|
| Earlier version | +1.79¢ (n = 11) | +4.55¢ (n = 8) | 0.077 / 0.043 |
| Same measurement for both | +2.49¢ (11) | +4.55¢ (8) | 0.19 / 0.16 |
| Same measurement, Sept. 16 dropped | +2.49¢ (11) | +2.14¢ (5) | 0.77 / 0.80 |
| All events through Nov. 24 | +1.58¢ (20) | +0.94¢ (7) | 0.59 / 0.59 |
| Same, size of move only | 2.36¢ | 2.23¢ | 0.85 |

### 4.3 What Study 1 shows

A star trade moves the involved team's title odds by about as much as a macro surprise moves the Fed contracts. The biggest sports moves were the Heat on Giannis (+4.7¢), the 76ers on Jaylen Brown (+6.4¢) and LeBron James (+5.8¢), and the Rams on Garrett (+4.7¢). Scheduled vs. unscheduled news didn't make a measurable difference in either domain. Macro news barely spills into sports odds (+0.22¢ across 10 events). Sports news didn't move Fed contracts at all on minute data.

The study also has limits I can't fix with this design. The groups are small (5 to 20 events), so the confidence intervals are about ±2¢ wide. Scheduled Fed and CPI contracts settle at the release itself, so part of their "move" is the contract paying out. The 30-day-average baseline picks up slow drift as if it were news, which is why the Spurs' contract "fell" 3.4¢ around Victor Wembanyama's extension. Fall NFL trades happen during the season, when futures also move on every weekend's games, so I keep them in a separate in-season group.

The more useful result from Study 1 is where the moves happened. When I located the actual jump in each involved team's price, most landed within a day of the report, but some landed well before it: Toronto 76 days early on Kawhi, Boston 7 days early on Jaylen Brown, and Cleveland 6 days early on Donovan Mitchell's extension. Study 2 measures that directly.

## 5. Study 2 (pilot): How much of the move happens before the report?

### 5.1 Design

I use hourly candles over [T0 − 30 days, T0 + 3 days], where T0 is the minute of the first Tier-1 report for sports and the official release time for macro. For each event:

- **pre** = midpoint 1 hour before T0, minus the midpoint 7 days before
- **post** = midpoint 24 hours after T0, minus the midpoint 1 hour before
- **pre-report share (PRS)** = pre / (pre + post), computed only when the total move is at least 1¢
- **z24** = the move in the 24 hours before T0, in the direction of the eventual move, divided by the contract's normal 24-hour variation over days T−30 to T−8. A z24 near 0 means nothing unusual happened the day before the report. A large positive z24 means the price was already heading where the news would take it.

For sports, I measure the involved team's contract, using only the 11 summer events that have a minute-level report time. For macro, I measure 18 CPI releases and FOMC decisions from January to November 2026 on the next FOMC meeting's Fed contract, because that contract reprices on the news but doesn't settle at the release. Macro data are embargoed until release, so the macro group shows what pre-release drift looks like when there shouldn't be a leak.

### 5.2 Results

The 11 sports events gave me 6 involved-team contracts with a total move of at least 1¢. That's enough to compute a pre-report share, and it's 5 with a usable z24. The other contracts either didn't move at all or had no variation in the baseline period to scale by. All 18 macro releases had usable data.

| | Sports (involved team) | Macro (next-meeting Fed contract) | p (Mann-Whitney) |
|---|---|---|---|
| Median pre-report share | 0.10 (n = 6) | 0.49 (n = 17) | 0.62 |
| Median z24 | 0.00 (n = 5) | 0.11 (n = 18) | 0.56 |
| z24 above 0? (Wilcoxon) | p = 1.00 | p = 0.14 | |

The individual cases say more than the medians do:

- **LeBron James to the 76ers (July 24).** Philadelphia went from 7.5¢ a week out to 11.5¢ an hour before the report, with 6¢ of that coming in the last 24 hours (z24 = 4.9). It didn't move at all in the 24 hours after. Every cent of the repricing happened before the news was public.
- **Jaylen Brown to the 76ers (July 1).** The opposite case. Philadelphia sat at 1.5¢ until the report and then jumped 4.5¢, so the pre-report share is 0.
- **Giannis to the Heat (June 23).** Miami moved 1¢ in the week before and 4¢ after, a pre-report share of 0.2.
- **Myles Garrett to the Rams (June 1) and Aaron Donald's comeback (August 30).** The Rams' contract moved only after the report, 5¢ and 1¢.
- **Kawhi Leonard to the Raptors (September 14).** Toronto didn't move in the 7 days around the official report, because its jump happened on June 30, 76 days earlier. A 7-day window can't see a leak that early.

On the macro side, the largest last-day drift was before the November 10 CPI release, when the December Fed contract rose 15¢ in the 24 hours before the data came out (z24 = 3.8). The largest drift the wrong way came before the July 14 CPI, when the July contract climbed 12.5¢ and then fell 26.5¢ once the number was out.

### 5.3 What the pilot does and doesn't show

The pilot doesn't test the leak hypothesis. With 5 or 6 sports contracts, no test has a real chance of finding anything, so I'm not reading the medians as evidence either way. What the pilot did was show me where the design was weak before I locked it.

**Most sports contracts are too cheap to move.** Kalshi prices move in 1¢ steps. A team sitting at 1.5¢ or 2.5¢ can go a full day without its midpoint changing, so its z24 is either 0 or can't be computed. That's why the confirmatory study requires a contract to be at least 2¢ a week before the event and puts a floor under the noise estimate.

**The macro comparison group isn't clean over a full week.** A Fed contract reprices on every data release, not only the one I'm measuring. The 7 days before the September 16 FOMC decision included the September 11 CPI release, which moved the same contract 37¢ on its own. So a lot of what looks like "pre-report drift" in macro over 7 days is just the previous piece of news. The last 24 hours before a release are much cleaner, because Kalshi's scheduled releases are rarely a day apart. That's why the confirmatory plan makes z24 the primary measure, and it drops any macro event whose pre-window contains another scheduled release.

**The design only sees late leaks.** Toronto moved 76 days before the Kawhi trade was official. A window of a week or a day can't catch that, so the confirmatory study measures leaks in the last stretch before a report, not leaks of any kind. I report early moves like Toronto's descriptively, but they aren't part of the test.

The LeBron case is the reason the study is worth running. A 6¢ move in a day, on a contract that normally moves about 1¢, landing in the direction the news would take it, and then nothing after the report, is exactly what early information looks like in prices. The confirmatory study asks whether that's a one-off or a pattern.

## 6. Threats to validity

- **Rumors aren't leaks.** A price can drift before the report because of public rumors, not private information. I can't separate those with prices alone, so the confirmatory study logs every public rumor report with a timestamp and tests pre-report drift with and without events that had a public rumor in the prior 7 days.
- **Report times.** If my T0 is late, real post-report moves look like leaks. The confirmatory study uses the minute of the first Tier-1 post and drops events without one.
- **Floor contracts.** Contracts near 0¢ can't move, so the confirmatory study requires the involved team's contract to be at least 2¢ a week before the event.
- **In-season games.** NFL and NBA futures move after every game, so in-season events are flagged and analyzed both pooled and separately.
- **Macro drift.** Fed contracts drift before FOMC meetings for reasons that aren't leaks (Lucca and Moench, 2015). That's exactly why I compare the shape of the drift, especially the last 24 hours, and not just its size.

## 7. Confirmatory study (preregistered)

The full plan is in `LEAK_PREREG_DRAFT.md`, and it'll be signed and committed before December 1, 2026. In short:

- **Sample:** every NBA and NFL transaction from December 1, 2026 to June 30, 2027 that passes a mechanical size rule. That means All-Star, All-NBA, Pro Bowl or All-Pro in the last three seasons, an average salary of at least $15M (NBA) or $10M (NFL), a starting quarterback, or any head-coach change. Every CPI release and FOMC decision in the same window serves as the comparison.
- **Primary tests:**
  - L1: sports z24 is above 0, meaning involved contracts drift toward the news in the 24 hours before it breaks.
  - L2: sports z24 is higher than macro z24, with macro events dropped when another scheduled release falls in the prior 25 hours.
  - L3 (placebo): uninvolved teams show no drift, and it has to pass for L1 and L2 to count.
  - The 7-day pre-report share is reported as a secondary result.
- **Power:** with about 30 qualifying sports events, L1 has roughly 90% power to detect a median z24 of 0.75. If fewer than 15 events qualify, the results are reported as descriptive.
- **Strata:** offseason and in-season events are flagged and reported separately, and so are trades, signings and extensions.
- **Analysis date:** July 10, 2027, with every result reported, including nulls.

## 8. Conclusion

I started out asking whether Kalshi reacts more to macro news or sports news, and the honest answer is that once you measure both the same way, a star trade moves its team about as much as a macro surprise moves the Fed. The earlier "macro wins" result came from two measurement choices, and I've kept the old numbers next to the corrected ones so anyone can see what changed and why.

The more important question is timing. Sports transactions are known to a handful of people before they're reported, and Kalshi now lists contracts on exactly those events. The pilot shows that early movement does happen, at least once in a clean way, and it shows how to measure it without fooling myself: use the last 24 hours, scale by the contract's own noise, skip contracts sitting on the floor, and compare against macro releases with a clean pre-window. The confirmatory study runs on events that haven't happened yet, with every rule fixed in advance. If sports contracts drift toward the news before it breaks more than embargoed macro contracts do, that's direct evidence that private information is reaching these markets. If they don't, that's worth knowing too, because leagues and regulators are already making rules on the assumption that it does.

## Data and code

All code and data are public at github.com/yuvankrishnamurthy1-hue/kalshi-research-paper. Every deviation from the September 2026 preregistration is logged in `hidden_files/prereg_deviations.md`. Study 1 tables come from `analyze_d24.py`, and the Study 2 pilot from `leak_pilot.py`.

## References

- Croxson, K., and Reade, J. J. (2014). Information and efficiency: Goal arrival in soccer betting. *The Economic Journal*, 124(575), 62–91.
- Gürkaynak, R., and Wolfers, J. (2005). Macroeconomic derivatives: An initial analysis of market-based macro forecasts, uncertainty, and risk. *NBER International Seminar on Macroeconomics*.
- Keown, A. J., and Pinkerton, J. M. (1981). Merger announcements and insider trading activity: An empirical investigation. *The Journal of Finance*, 36(4), 855–869.
- Lucca, D. O., and Moench, E. (2015). The pre-FOMC announcement drift. *The Journal of Finance*, 70(1), 329–371.
- Meulbroek, L. K. (1992). An empirical analysis of illegal insider trading. *The Journal of Finance*, 47(5), 1661–1699.
- Snowberg, E., and Wolfers, J. (2010). Explaining the favorite–long shot bias: Is it risk-love or misperceptions? *Journal of Political Economy*, 118(4), 723–746.
- Wolfers, J., and Zitzewitz, E. (2004). Prediction markets. *Journal of Economic Perspectives*, 18(2), 107–126.
