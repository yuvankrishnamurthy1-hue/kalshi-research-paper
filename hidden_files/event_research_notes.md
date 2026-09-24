# Event Registry Research Notes (DRAFT - 2026-09-21)

Draft registry: `event_registry_draft.csv` in this same directory.
Injuries/availability shocks EXCLUDED per Yuvan's 2026-09-21 decision.
All timestamps are best-estimate drafts; nothing here is final.

## What I found (web-verified at aggregator level, Tier-1 by attribution)

### Trades (6 candidates)
- **Giannis Antetokounmpo to Heat (2026-06-23)** — best-documented. Shams Charania first report late Monday night June 22 / early June 23; Palm Beach Post + Hot Hot Hoops + NBC Sports Bay Area all attribute to Shams' tweet. Need the exact tweet timestamp for T=0.
- **Myles Garrett to Rams (2026-06-01)** — FOX Sports: "In a move that felt like it came out of nowhere" Monday; Garrett for Jared Verse + 3 picks. Date of Monday = June 1, 2026. Need Schefter tweet timestamp.
- **A.J. Brown to Patriots (2026-06-01)** — same Monday; Eagles received 2027 1st + 2028 5th. Need Schefter tweet timestamp.
- **Jaylen Brown to 76ers (2026-07-01)** — Shams tweet July 1; official July 6. T=0 = July 1 report (per prereg rule). Exact tweet time TBD.
- **D'Angelo Russell six-team trade (July 2026)** — Fox Sports AU describes deal combining post-moratorium moves; needs exact completion/report date from Shams.
- **Kawhi Leonard to Raptors (~2026-09-14)** — trickiest case: agreement framework since June 30, but league investigation ($30M Clippers fine, $700k Leonard fine) delayed completion. Shams reported finalized completion "on Monday" per Archysport (~Sep 14). Needs exact Shams timestamp + decision on whether T=0 = completion report or the June 30 framework.
- **Dexter Lawrence trade** — only mentioned in one aggregator headline; no details. Drop unless Tier-1 found.

### Signings (4 candidates)
- **Von Miller to Cowboys (2026-08-16/17)** — Sunday evening Aug 16 signing; ESPN story + Rapoport tweet Aug 17. 1yr/$5.5M.
- **LeBron James to 76ers (late July 2026)** — two-year deal per The Lead/Daily Campus; timing described as "a few weeks after" the July 1 Brown trade. NO Tier-1 source captured yet — needs Shams/ESPN first report before inclusion. High priority to verify.
- **Mitchell Robinson to Celtics (2026-07-01)** and **Mike Conley to Celtics (2026-07-01)** — Shams per NESN offseason tracker. Both small-market-move null cases.

### Extensions (4 candidates)
- **Donovan Mitchell 4yr/$273M with Cavs (2026-07-07)** — Shams morning tweet; officially announced July 9. Best-documented extension; killed months of Knicks rumors.
- **Neemias Queta 4yr/$56M (2026-07-03)**, **Jordan Walsh 3yr/$15M (2026-07-23)** — Shams per NESN.
- **Brian O'Neill 4yr/$96M (Vikings, date TBD)** — mentioned in injury-report article; needs Tier-1 date.

### Other roster news (1 weak candidate)
- **Aaron Donald comeback** — only a passing mention in an Athlon article (Von Miller referencing "If Aaron can do it..."). HIGH uncertainty; likely drop unless a Tier-1 source confirms.

### Scheduled sports (4)
- NBA schedule release 2026-08-14 (confirmed), NFL kickoff ~2026-09-10 (verify exact date), NBA opening night 2026-10-20, NFL trade deadline 2026-11-10 4pm ET. T-7 snapshot dates per prereg.

## Still uncertain / needs work
1. **Exact Tier-1 timestamps** for nearly every event — Shams/Schefter/Rapoport tweet times. This needs a browser task (logged-in X/ESPN) or manual lookup; web search snippets don't carry times.
2. **LeBron-to-76ers** and **Kawhi completion** need Tier-1 verification before confirmatory inclusion.
3. **June 1 NFL trades** (Garrett, A.J. Brown) need Schefter timestamps; FOX Sports date inference (Monday=June 1) should be cross-checked.
4. **Aaron Donald comeback** and **Dexter Lawrence trade** — likely drops.
5. **Expectation baselines**: for each event, need T-7 published odds + KXNBA/KXSB snapshot prices. The laptop collector data (daily snapshots) covers Aug 14+; June/July events need API historical pull.
6. **Variety balance check**: currently trade-heavy on big names; signings/extensions include small null-case events (Conley, Robinson, Walsh) which is good for H3 tier gradient but the registry should note that these may not move title odds — that's fine, prereg says log everything.

## Counts vs prereg rules
- Unscheduled trades: 6 candidates (5 Tier-1-attributed).
- Signings: 4 (1 needing Tier-1).
- Extensions: 4 (1 needing Tier-1).
- Other: 1 (weak).
- Scheduled sports: 4.
- If the n>=5 confirmatory rule is applied per *cell* (unscheduled sports overall, not per type), the cell is well above 5. If applied per type, trades qualify; signings/extensions/other are borderline and should be pooled or reported descriptively per the variety note in prereg.

## Suggested next actions for Dash/parent
1. Browser task: pull exact Shams/Schefter/Rapoport first-report timestamps for the Tier-1 events.
2. Historical API pull for June/July windows (needs historical-market discovery work).
3. Yuvan review: drop/keep calls on Donald comeback, Dexter Lawrence, Kawhi T=0 treatment.
