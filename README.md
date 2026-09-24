# How Kalshi Prediction Markets React to News: A 2×2 Event Study

**Yuvan Krishnamurthy** — research draft: `paper_v2.md`

Event study of Kalshi prediction-market reactions, crossing news **scheduleness**
(scheduled vs. unscheduled) with **domain** (macro vs. sports). Preregistration
locked 2026-09-21 (`preregistration.md`, never edited retroactively).

## Headline finding

Unscheduled macro shocks move Kalshi prices far more than sports roster news:
+4.83¢ mean abnormal move across 8 macro events vs −0.12¢ across 14 summer
roster events (H1c: Welch t = −3.61, p = 0.0086 raw and Holm-adjusted; robust
across 1/3/5-day windows and the liquidity filter). All other contrasts are
descriptive-only or supplementary — see `paper_v2.md` for the full,
no-spin accounting, including every caveat (Sep-16 cluster non-independence,
the excluded Giannis trade, placebo watch).

## Layout

| Path | Contents |
|---|---|
| `paper_v2.md` | Full draft (Abstract → Reproducibility), written strictly from computed results |
| `preregistration.md` | Locked preregistration (2026-09-21). Read-only history. |
| `collect_kalshi_summer.py` | Summer data pull (confirmatory sample) |
| `collect_extended.py` | Extended pull: H2 cross-domain baskets, CPI 2026-09-11, new scheduled sports, Jan–Sep scheduled-macro window |
| `collect_h2farexpiry.py` | H2 far-expiry re-pull |
| `collect_kalshi.py` | Legacy collector (superseded) |
| `analyze_kalshi.py` / `analyze_kalshi_fixed.py` | Analysis machinery (fixed = the version used for v1/v2) |
| `hidden_files/coverage_precheck.py` | Registration-time exclusion guard — warns when contracts list too close to T0 |
| `hidden_files/analyze_fallback.py` | Non-confirmatory descriptive track for excluded events |
| `hidden_files/event_registry.csv` | 28 registered events with T0s, cells, sources |
| `hidden_files/expectations.md` | T−7 expectations and rumor trails per event |
| `hidden_files/prereg_deviations.md` | D1–D15: every deviation from the prereg, documented |
| `hidden_files/excluded_but_material.md` | Register of excluded events with reasons + fallback results |
| `hidden_files/giannis_descriptive.md` | Giannis-to-Heat descriptive (excluded from confirmatory) |
| `hidden_files/analysis_real/` | All computed outputs (`*_v2.csv` confirmatory, `*v2xd`/`*v2supp` extended/supplementary) |
| `kalshi_api_data_summer/` | Confirmatory pull: 483 tickers, 17,680 rows |
| `kalshi_api_data_extended/` | Extended pull: 342 tickers, 13,523 rows |
| `kalshi_api_data_h2farexpiry/` | H2 far-expiry pull: 16 tickers, 737 rows |
| `tier_inventory_2026-09-17.csv` | Live contract tier inventory |

Raw per-ticker API caches (`*/raw/`) are excluded from version control (regenerable
via the collectors); the committed `market_data.csv` files are the analysis record.

## Reproduce

```bash
# 1. Pull data (Kalshi public API; respects rate limits; re-runs resume)
python3 collect_kalshi_summer.py     # confirmatory sample
python3 collect_extended.py         # H2 cross-domain + scheduled-event extensions

# 2. Guard: check baseline coverage before analysis
python3 hidden_files/coverage_precheck.py

# 3. Analyze
python3 analyze_kalshi_fixed.py
python3 hidden_files/analyze_fallback.py   # descriptive track for excluded events
```

## Data provenance

All market data from the Kalshi public API (no credentials). Event T0s from
Tier-1 reporting (ESPN/Shams/Woj/Schefter, Bloomberg/WSJ/CNBC, official PR),
logged per event in `event_registry.csv` and `expectations.md`.

## Status / limitations (abridged)

- H1a/H1b/H1d: descriptive-only (scheduled cells n < 5 in the confirmatory window).
- H2 sports→macro leg: untestable with daily data (two documented failed
  implementations); macro→sports leg: +0.16¢, statistically nonzero,
  economically negligible.
- H3 prereg tiers uninformative; supplementary tercile tiers show a strong
  |abnormal-move| gradient (exploratory).
- Macro result leans on a non-independent Sep-16 cluster overlapping the FOMC.
- Speed estimates are daily-resolution only.
