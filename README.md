# Do Prediction Markets Know Before the News Breaks? Pre-Report Price Drift on Kalshi

**Yuvan Krishnamurthy**. Current paper: `paper.md` · Draft preregistration for the confirmatory study: `LEAK_PREREG_DRAFT.md` · Referee-style review of the earlier draft: `REVIEW.md`

This project started as a 2×2 event study of how Kalshi reacts to scheduled vs. unscheduled news, in macro vs. sports (`preregistration.md`, locked 2026-09-21, never edited; every later change is logged as deviations D1 to D24 in `hidden_files/prereg_deviations.md`). It's now a study of **when** prices move: how much of a repricing happens before the first public report, with sports transactions (known privately before they're reported) compared against embargoed CPI and FOMC releases.

## Where it stands (2026-11-24)

- **Study 1, reaction size (exploratory).** Once sports and macro are measured the same way and the September 16 Fed-hike day isn't counted three extra times, a star trade moves the involved team's title odds about as much as a macro surprise moves the Fed contracts (+2.5¢ vs. +2.1¢). The earlier "macro moves more" result (p = 0.077) came from those two measurement problems. Numbers: `hidden_files/analysis_real/d24_contrasts.csv`.
- **Study 2, leak pilot (exploratory).** Hourly prices around 11 summer 2026 sports transactions and 18 macro releases (`leak_pilot.py`). Too small to test anything, but it found one clean case (Philadelphia rose 6¢ in the 24 hours before the LeBron James trade was reported, z = 4.9, then didn't move) and two design problems that the confirmatory plan now fixes.
- **Confirmatory study.** Every qualifying NBA/NFL transaction and every CPI/FOMC release from 2026-12-01 to 2027-06-30, under `LEAK_PREREG_DRAFT.md`, which has to be signed and committed before 2026-12-01 00:00 UTC.

`paper_v2.md` is the older reaction-size draft, kept for the record.

## Layout

| Path | Contents |
|---|---|
| `paper.md` | Current paper (leak framing, Study 1 + pilot + confirmatory plan) |
| `LEAK_PREREG_DRAFT.md` | Draft preregistration for the confirmatory leak study (sign before 2026-12-01) |
| `leak_pilot.py` | Hourly leak pilot. Output: `hidden_files/analysis_real/leak_pilot_*.csv` |
| `paper_v2.md` | Earlier reaction-size draft (v4), kept for the record |
| `REVIEW.md` | Journal-style referee report, with suggested redesigns |
| `preregistration.md` | Locked preregistration (2026-09-21). Read-only history. |
| `collect_kalshi_summer.py` | Summer data pull (original confirmatory sample) |
| `collect_extended.py` | Extended pull: H2 baskets, CPI 2026-09-11, scheduled sports, Jan–Sep scheduled macro |
| `collect_h2farexpiry.py` | H2 far-expiry re-pull (D15) |
| `collect_d24.py` | D24 pull: cutoff extended to 2026-11-24 (Oct/Nov CPI + FOMC, NBA opening night, NFL deadline, fall trades, Wembanyama extension, Nov macro shocks) |
| `analyze_kalshi_fixed.py` / `analyze_d16.py` | Core event-study machinery (strict rule / D16 amended rule) |
| `analyze_d24.py` | Same-ruler involved-teams test, Sep-16 sensitivity, D24 extension, permutation p-values. Also reproduces the published D18 numbers. |
| `hidden_files/d23_h2_*.py` | Intraday (minute-candle) sports→macro test (D23) |
| `hidden_files/event_registry.csv` | Registered events with T0s, cells, sources |
| `hidden_files/size_tiers.csv`, `size_tiers_d24.csv` | Ex-ante Big/Medium/Small grades (graded before price data was pulled) |
| `hidden_files/prereg_deviations.md` | D1–D24: every deviation from the prereg |
| `hidden_files/excluded_but_material.md` | Excluded events with reasons and fallback results |
| `hidden_files/analysis_real/` | All computed outputs (`d24_*.csv` = current) |
| `kalshi_api_data_summer/`, `_extended/`, `_h2farexpiry/`, `_d24/` | Kalshi candle data (committed `market_data.csv` files are the record) |

Raw per-ticker API caches (`*/raw/`) are excluded from version control. Re-pull them with the collectors.

## Reproduce

```bash
pip install numpy pandas scipy
# 1. Pull data (Kalshi public API, no credentials; polite rate limiting)
python collect_kalshi_summer.py
python collect_extended.py
python collect_d24.py
# 2. Combine summer + extended pulls
python hidden_files/build_combined.py
# 3. Analyze
python analyze_d16.py        # 2x2 confirmatory machinery (set KALSHI_* env vars, see header)
python analyze_d24.py        # current headline tests -> hidden_files/analysis_real/d24_*.csv
```

## Data provenance

All market data comes from the Kalshi public API (no credentials). Event T0s come from
Tier-1 reporting (ESPN/Shams/Schefter, NFL.com, BLS, Federal Reserve, Reuters/CNBC)
and are logged per event in `event_registry.csv` and `expectations.md`.
