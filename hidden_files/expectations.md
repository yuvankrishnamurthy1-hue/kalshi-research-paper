# Expectations audit — Kalshi event study, summer 2026

Compiled 2026-09-23. All web research dated 2026-09-23; Kalshi price snapshots
computed from the summer pull (`kalshi_api_data_summer/market_data.csv`).
Labels below distinguish exactly-on-T-7 evidence from bracketing/context evidence.

---

## Part A — Scheduled sports (T-7 expectations)

### A1. nba_schedule_release (2026–27 schedule released 2026-08-13 ~19:08 UTC; T-7 = 2026-08-06)

**T-7 Kalshi snapshot (2026-08-06, first candle of day, bid/ask midpoint; NaN = no
usable bid/ask or last that day):**

| Ticker | T-7 mid | Ticker | T-7 mid | Ticker | T-7 mid |
|---|---|---|---|---|---|
| KXNBA-27-ATL | 0.010 | KXNBA-27-BKN | NaN | KXNBA-27-BOS | 0.045 |
| KXNBA-27-CHA | NaN | KXNBA-27-CHI | NaN | KXNBA-27-CLE | 0.025 |
| KXNBA-27-DAL | 0.010 | KXNBA-27-DEN | 0.035 | KXNBA-27-DET | 0.025 |
| KXNBA-27-GSW | 0.015 | KXNBA-27-HOU | 0.015 | KXNBA-27-IND | 0.015 |
| KXNBA-27-LAC | NaN | KXNBA-27-LAL | 0.025 | KXNBA-27-MEM | NaN |
| KXNBA-27-MIA | 0.035 | KXNBA-27-MIL | NaN | KXNBA-27-MIN | 0.035 |
| KXNBA-27-NOP | NaN | KXNBA-27-NYK | 0.085 | KXNBA-27-OKC | 0.215 |
| KXNBA-27-ORL | 0.010 | KXNBA-27-PHI | 0.105 | KXNBA-27-PHX | 0.010 |
| KXNBA-27-POR | 0.010 | KXNBA-27-SAC | 0.010 | KXNBA-27-SAS | 0.245 |
| KXNBA-27-TOR | 0.035 | KXNBA-27-UTA | NaN | KXNBA-27-WAS | 0.010 |

(22/30 tickers with a usable mid; 8 thin.) Note: these are championship-futures
contracts, not "will this team appear on opening night" contracts — so the
T-7 mid table records baseline sentiment, not a point expectation for the
schedule itself.

**Media expectations as of T-7:** NONE FOUND. No Tier-1 source dated on/before
2026-08-06 reported expected opening-night or Christmas Day matchups. The
earliest concrete pre-release reporting is Aug 10 (after T-7): the league would
roll out opening-week/Christmas slates Aug 11, the NBA Cup schedule Aug 12, and
the full 82-game schedule Aug 13 at 3 p.m. ET (USA Today OKC Thunder Wire;
Cavaliers Nation, both Aug 10). Specific matchups leaked via Shams Charania on
Aug 11 — after T-7. Commissioner Adam Silver told CNBC in July 2026 that the
league could not finalize opening week/Christmas until LeBron James made his
free-agency decision (Awful Announcing recap).

Actual (Aug 13): Opening Night tripleheader Oct 20 — Celtics @ Pistons,
76ers @ Knicks, Thunder @ Spurs; Christmas Day five games — Spurs @ Knicks,
Heat @ Celtics, 76ers @ Lakers, Thunder @ Timberwolves, Nuggets @ Warriors.

- https://okcthunderwire.usatoday.com/story/sports/nba/thunder/2026/08/10/nba-announces-release-dates-for-2026-27-regular-season-schedule/91242299007/
- https://cavaliersnation.com/2026/08/10/cavs-schedule-2026-27-release-date-lebron-games-loom/
- https://awfulannouncing.com/nba/2026-27-opening-night-christmas-day-schedule-lebron-sixers.html
- https://www.espn.ph/nba/story/_/id/49471934/nba-full-schedule-2026-2027-games-watch-faq-rivalries-matchups

**GAP (explicit):** no valid on/before-T-7 matchup expectation evidence exists in
Tier-1 sources; later reports are NOT backfilled as T-7 evidence.

### A2. nfl_kickoff (Patriots at Seahawks, 2026-09-09, 8:20 PM ET; T-7 = 2026-09-02)

**T-7 Kalshi snapshot (2026-09-02, bid/ask midpoint; Super Bowl-winner contracts):**

| Ticker | T-7 mid | Ticker | T-7 mid | Ticker | T-7 mid |
|---|---|---|---|---|---|
| KXSB-27-ARI | 0.010 | KXSB-27-ATL | 0.010 | KXSB-27-BAL | 0.065 |
| KXSB-27-BUF | 0.075 | KXSB-27-CAR | 0.010 | KXSB-27-CHI | 0.035 |
| KXSB-27-CIN | 0.045 | KXSB-27-CLE | 0.010 | KXSB-27-DAL | 0.045 |
| KXSB-27-DEN | 0.045 | KXSB-27-DET | 0.035 | KXSB-27-GB | 0.035 |
| KXSB-27-HOU | 0.045 | KXSB-27-IND | 0.015 | KXSB-27-JAC | 0.025 |
| KXSB-27-KC | 0.055 | KXSB-27-LAC | 0.045 | KXSB-27-LAR | 0.155 |
| KXSB-27-LV | 0.010 | KXSB-27-MIA | 0.010 | KXSB-27-MIN | 0.025 |
| KXSB-27-NE | 0.045 | KXSB-27-NO | 0.010 | KXSB-27-NYG | 0.015 |
| KXSB-27-NYJ | 0.010 | KXSB-27-PHI | 0.045 | KXSB-27-PIT | 0.010 |
| KXSB-27-SEA | 0.075 | KXSB-27-SF | 0.045 | KXSB-27-TB | 0.015 |
| KXSB-27-TEN | 0.010 | KXSB-27-WAS | 0.015 |

(32/32 tickers with a usable mid.) Note: these are Super Bowl-winner futures, not
game-spread contracts — they record baseline sentiment, not the game expectation.

**Media expectations as of T-7:** NO ODDS DATED EXACTLY SEPT 2 FOUND. Bracketing
snapshots (flagged as such, NOT T-7 readings):
- Opening lines, May 13–15, 2026 (after NFL schedule release May 14): FanDuel —
  Seahawks −4.5, ML −210/+176, total 45.5 (SportsBookReview). DraftKings —
  Seahawks −3.5, ML −205/+170, total 44.5 (FOX Sports).
- Nearest pre-game snapshot ~Sept 6–7 (SI.com, via DraftKings): Seahawks −3.5,
  ML −175/+145, total 44.5.
- Game-day (Sept 9) consensus: Seahawks −3, ML −166/+140, total 44.5 (NBC Sports).

Context: first Week 1 Super Bowl rematch since 2016 (defending-champion Seahawks
14-3 hosting Patriots 14-3; Super Bowl LX 29-13). Money drifted toward the
visitor: −4.5 (May) → −3.5 → −3 by kickoff. (Game since played: Seahawks won
13-10.)

- https://www.sportsbookreview.com/picks/nfl/patriots-vs-seahawks-odds-prediction-picks-preview-week-1-2026/
- https://foxsports.com/stories/nfl/2026-nfl-odds-week-1-lines-spreads-all-16-games
- https://www.si.com/betting/patriots-vs-seahawks-prediction-odds-spread-injuries-trends-for-nfl-week-1
- https://www.nbcsports.com/nfl/live/new-england-patriots-vs-seattle-seahawks-live-updates-score-highlights-results-2026-nfl-kickoff-game

**GAP (explicit):** no odds-outlet article dated Sept 2 found; Sept 6 figures are
reported as of that date, not as a T-7 reading.

### A3. nba_opening_night (Oct 20, 2026; T-7 = 2026-10-13)

**T-7 UNOBSERVABLE.** The T-7 date (2026-10-13) is in the future relative to
today (2026-09-23): neither the Kalshi snapshot nor media expectations as of
that date can be captured yet. No odds published as of Sept 23.

Currently known (context, NOT T-7 evidence): NBC/Peacock tripleheader Oct 20 —
Celtics @ Pistons 3:00 p.m. ET; 76ers @ Knicks 7:00 p.m. ET (Knicks' championship
banner ceremony, first since 1973); Thunder @ Spurs 9:30 p.m. ET. Matchups leaked
by Shams Charania Aug 11, confirmed Aug 11, full schedule Aug 13.

- https://www.espn.ph/nba/story/_/id/49471934/nba-full-schedule-2026-2027-games-watch-faq-rivalries-matchups
- https://www.sportsbusinessjournal.com/Articles/2026/08/11/nba-unveils-season-opening-tripleheader-on-nbc/

**GAP (explicit):** re-run on/after 2026-10-13 to capture the true T-7 snapshot.

---

## Part B — Macro events: consensus vs actual (all verified 2026-09-23)

Consensus sources are Dow Jones surveys via CNBC coverage unless noted. Kalshi
bucket "moneyness" in the analysis registry is computed against these consensus
figures only where verified; pairs whose reference release/meeting lacks a
verified consensus carry moneyness NaN (documented exclusion from H3 tiers).

### B1. nvda_earnings — CONFIRMED 2026-08-26 (after US market close; date confirmed,
exact wire time not found in Tier-1 sources)

NVIDIA Q2 FY2027:
- Revenue: consensus $92.17B (LSEG via CNBC) → actual **$96.22B** (+4.4%)
- Non-GAAP EPS: consensus $2.10 → actual **$2.22** (+~6%)
- Data center revenue: est. $86.33B (StreetAccount) → actual $89.0B
- Q3 FY2027 guidance: $108B ±2% vs ~$104.2B est.
- https://www.zacks.com/stock/news/2980648/nvidia-nvda-surpasses-q2-earnings-and-revenue-estimates
- Note: one aggregator (marketmojo.net) carried wildly inconsistent NVDA figures —
  discarded as unreliable.

### B2. hormuz_retaliation_threat — CONFIRMED (first Tier-1 report Sept 7, 2026;
Thomson Reuters wire bylined 9:53 PM Singapore)

Iran threatened retaliation for any new US attacks, warning Gulf energy
infrastructure was vulnerable; Hormuz commodity-vessel traffic slowed (7 vessels
vs 8 prior day, Kpler); Goldman raised Brent/WTI forecasts. Working date 09-08
reflected the Singapore dateline; T0 corrected to first report Sept 7.
- https://wncy.com/2026/09/07/hormuz-traffic-slows-after-iran-threatens-retaliation-for-us-attacks/
- Next scheduled data point: August CPI (released Sept 11): headline m/m
  consensus +0.4%, core m/m +0.2%.

### B3. canada_proclamations — CONFIRMED 2026-09-08 (signed, evening)

Five proclamations (11061–11065) under Section 338, Tariff Act of 1930:
import bans on certain Canadian dairy, molasses, non-alcoholic beer, alcoholic
beverages, motorcycles (effective Sept 29, 12:01 a.m. ET); added 50% duties on
Canadian cheeses, motorboats, wood/paper/furniture (effective Sept 15); removed
rock salt and cement. GSA directed to remove ~$50B of Canadian-origin products
from Multiple Award Schedules. Same day Canada's retaliatory tariffs on ~$27.6B
of US goods took effect.
- https://www.federalregister.gov/documents/2026/09/14/2026-18835/excluding-certain-canadian-products-from-importation-into-the-united-states-in-response-to-continued
- Next scheduled data point: August CPI (released Sept 11): headline m/m
  consensus +0.4%, core m/m +0.2%.

### B4. hormuz_strike_pipeline_shutdown — CONFIRMED (drone strikes Sept 10, 2026;
pipeline shutdown confirmed Sept 11)

Drone strikes on Saudi East-West (Petroline) pipeline pump stations (Riyadh,
Medina regions), blamed by Saudi Arabia on Iranian-backed militias in Iraq;
the ~4–7 mbpd line shut Sept 11 as a precaution; repairs expected 3–5 weeks
(two regional officials, via AP); Brent above $105/bbl. Working collector date
09-13 was ~2–3 days late vs first Tier-1 coverage; T0 corrected to Sept 10.
- https://en.wikipedia.org/wiki/2026_East%E2%80%93West_Crude_Oil_Pipeline_attack
- Next scheduled data point: August CPI (released Sept 11): headline m/m
  consensus +0.4%, core m/m +0.2%.

### B5. perim_island_seized — CONFIRMED 2026-09-11 (government forces withdrew Sept 10)

Houthi movement seized Perim Island (Mayyun) in the Bab el-Mandeb Strait after
Saudi-backed forces withdrew Sept 10, capping an offensive that took Mocha
(Sept 10), Dhubab, and the Hanish islands — effective Houthi control of the
strait's Yemeni side. First Tier-1 reports: Reuters, AFP, AP, all Sept 11.
- https://en.sedaily.com/international/2026/09/12/houthis-complete-control-of-red-sea-chokepoint-as-iran-gulf
- Same-day scheduled data point: August CPI (released Sept 11, 8:30 AM ET):
  headline m/m consensus +0.4% → actual +0.4% (match); core m/m +0.2% →
  actual +0.3% (hot surprise). THIS IS A MAJOR CONTAMINATION FACTOR for the
  Sept 8–16 macro cluster: the hot core CPI print hit the same calendar day as
  the seizure news.

### B6. tariff_eu_threat — CONFIRMED 2026-09-16 (afternoon ET)

Trump, responding to von der Leyen's Sept 16 State of the EU proposal to make
Canada the EU's first "associate member" (with Canadian PM Mark Carney present),
called it "laughable" and threatened "very heavy tariffs on Europe" if done with
"bad intention." NO ACTUAL TARIFF ANNOUNCED: no goods, rates, or timetable — a
conditional threat, not an enacted measure.
- https://www.tbsnews.net/worldbiz/usa/trump-derides-eu-pitch-canada-laughable-threatens-more-tariffs-1545296

### B7. russia_sanctions_bill — CONFIRMED (House passage Sept 16, 2026, evening)

House passed H.R. 5334 (Lindsey O. Graham Sanctioning Russia and Iran Act of
2026) 262–159: tariffs up to 100% on the largest purchasers of Russian
crude/gas, sanctions on Russian banks/oligarchs and the shadow fleet, US persons
barred from Russian sovereign debt, five-year extension of Iran sanctions. Senate
had passed 86–11 on Aug 7; Trump signed Sept 18.
- https://www.lemonde.fr/en/international/article/2026/09/19/trump-signs-graham-bill-imposing-new-sanctions-against-russia_6757703_4.html

### B8. trump_truth_fed — CONFIRMED 2026-09-16 (evening, hours after the 2:00 PM ET
FOMC decision; exact post timestamp not found in Tier-1 sources)

Trump's Truth Social post attacked the 25-bp hike, demanding rates of "1%, or
less"; to reporters the same day he called the Fed board "very hostile" and
"very political" while saying he still had confidence in Chair Warsh.
- https://economy.ac/news/2026/09/202609295655

### B9. fomc_sep_hike — CONFIRMED 2026-09-16, ~18:00 UTC (2:00 PM ET; two-day
meeting Sept 15–16, chaired by Kevin Warsh)

FOMC voted 12–0 to raise the federal funds target range 25 bp to 3.75%–4.00%,
the first hike since July 2023; statement cited "inflation remains elevated."
Markets had priced >90% odds of the hike (Bloomberg via swaps data) — direction
fully anticipated; unanimity the modest surprise. Prior range 3.50%–3.75% (in
place since the December 2025 cut, five consecutive holds in 2026). Dot plot:
16/18 projected at least one more 2026 hike; median year-end 2026 rate 4.1%
(vs 3.8% in June).
- https://www.livemint.com/market/stock-market-news/us-fed-meeting-2026-live-updates-interest-rate-decision-today-us-economy-fed-interest-rate-kevin-warsh-16-september-11789571646644.html

### B10. CPI/Fed reference data (for moneyness and contamination notes)

| Release | Date/time | Headline m/m (cons→actual) | Headline y/y | Core m/m (cons→actual) | Core y/y |
|---|---|---|---|---|---|
| July 2026 CPI | Aug 12, 2026, 8:30 AM ET | +0.1% → +0.1% (match) | 3.4% → 3.4% | +0.2% → +0.2% (match) | 2.5% → 2.5% |
| August 2026 CPI | Sept 11, 2026, 8:30 AM ET | +0.4% → +0.4% (match) | 3.4% → 3.4% | +0.2% → +0.3% (hot) | 2.4% → 2.4% |
| September 2026 CPI | Oct 14, 2026, 8:30 AM ET (scheduled; NOT Oct 13) | — | — | — | — |

(July release precedes the prereg window start of Aug 14 — included for
completeness only.) BLS schedule: https://www.bls.gov/schedule/news_release/cpi.htm

**Fed funds target range just before Sept 16: 3.50%–3.75%.**

---

## Method note

- T-7 media expectations for the two scheduled sports events with observable
  windows: no on-date evidence found; bracketing snapshots are reported as such.
- Macro first-report times: Tier-1 source date given; where sources gave only a
  date (nvda, tariff_eu_threat, trump_truth_fed, canada_proclamations,
  perim_island_seized), T0 is date-only (day 0 = that date), per prereg §6
  handling of approximate event times.
- All figures above are from September 2026 web reporting, not training memory.
  One fabricated-looking aggregator page was excluded; exact T-7 matchup/odds
  evidence that could not be found is flagged as a gap rather than backfilled.
