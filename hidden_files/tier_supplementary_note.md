# H3 supplementary tiers — short note

**POST-PREREG SUPPLEMENTARY / NON-CONFIRMATORY.** The preregistered H3
(contract-tier gradient via prereg tiers S1–S4 / M0–M3) was untestable as
specified: sports contracts pile into S1–S2 and the Sept-16 macro cluster
has no verified consensus (all M?). This note summarizes the supplementary
re-analysis in `hidden_files/analysis_real/tier_supplementary_3d.csv`
(script: `hidden_files/h3_tiers_supplementary.py`), which replaces the
unidentified prereg tier codings with data-identified ones:

- **Sports:** terciles of pre-event midpoint *within each cell*
  (P1 = cheapest third, P3 = most expensive third).
- **Macro non-bucket:** no such contracts exist in the analyzed sample
  (all macro pairs are macro_bucket) — leg recorded as empty by construction.
- **Macro bucket:** prereg M0–M3 where `moneyness_steps` exists (M? dropped).

Kruskal-Wallis across tiers per cell, 3-day window, pair-level observations.
Pairs within an event are correlated, so p-values are anti-conservative —
read magnitudes and monotone patterns, not exact p-values.

## Results (full sample; liquid-only in the CSV)

| Cell | Metric | H | p | Pattern |
|---|---|---|---|---|
| unsched_sports (14 ev) | signed abnormal | 4.13 | 0.127 | no signed gradient: P1 +0.03c, P2 −0.21c, P3 −0.23c |
| unsched_sports (14 ev) | \|abnormal\| | 91.84 | <0.0001 | **strong monotone gradient**: P1 0.22c → P2 0.49c → P3 1.73c |
| unsched_macro (8 ev) | signed abnormal | 7.40 | 0.060 | hump-shaped: M0 +1.7c, M1 +5.9c, M2 +4.4c, M3 +1.4c (liquid-only p=0.005) |
| unsched_macro (8 ev) | \|abnormal\| | 69.94 | <0.0001 | **strong monotone gradient**: M0 11.6c → M1 10.4c → M2 6.4c → M3 3.4c |
| sched_macro (1 ev) | — | — | — | not interpretable: single event; flagged, KW not run |
| sched_sports (2 ev) | — | — | — | terciles collapsed to one bin (degenerate prices); KW not run |

## Reading

1. **The tier gradient H3 hypothesized exists — just not in the prereg's
   tier coding.** In absolute movement, at-the-money macro buckets move ~3x
   more than tail buckets (11.6c vs 3.4c), and expensive sports contracts move
   ~8x more than cheap ones (1.73c vs 0.22c). The sports leg is partly
   mechanical (a 25c contract has more room to move than a 1c contract), but
   the macro leg is the textbook moneyness gradient and it is clean.
2. **Signed moves show no sports gradient** (p=0.13): expensive-team contracts
   don't systematically move *up* more — the gradient is in magnitude, not
   direction. For macro, signed moves hump at M1 (near-the-money), consistent
   with surprise repricing concentrating where probability mass is contested.
3. These are exploratory (pair-level, post-prereg tiers). They rehabilitate
   H3 from "untestable" to "untestable as preregistered, but the underlying
   gradient is visible under data-identified tiers."
