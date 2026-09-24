# The statistics behind the paper

A working explainer for the Kalshi event study. Every example uses the study's real numbers.

---

## 1. How a Kalshi contract works

Each Kalshi contract is a yes/no question with a price between 1¢ and 99¢:

> "Will the Miami Heat win the 2027 NBA championship?"

The price **is** the market's probability estimate. A contract trading at 3¢ means the market thinks there's roughly a 3% chance. If the answer turns out to be yes, the contract pays out $1 (100¢). If no, it pays $0. So buying at 3¢ and being right earns 97¢ per contract.

Two mechanics matter for this study:

- **We use the midpoint, not the last trade.** Every contract has a bid (what buyers offer) and an ask (what sellers demand). The midpoint — (bid + ask) / 2 — is the fair-value estimate. On thinly traded contracts the last trade price can be hours old and misleading, so the midpoint is the honest number.
- **Prices move in cents, and a cent is a percentage point.** When we say the Heat contract moved +4.4¢ on trade day, that means the market's estimated title probability jumped about 4.4 percentage points (2.6% → 7%). "Cents" and "percentage points of probability" are the same thing here.

The real Giannis example: KXNBA-27-MIA sat at a 2.6¢ midpoint before June 23, 2026, printed 7¢ on trade day, with bid/ask moving 2/3¢ → 6/8¢ and roughly 10× normal volume. The market roughly tripled the Heat's title odds in a day.

---

## 2. The abnormal move — the one measurement everything rests on

This study is an **event study**, a standard finance design (it was invented for stocks: "what did earnings do to the share price?"). The logic has three steps, done separately for every contract around every event:

1. **Baseline ("the before").** Average the contract's midpoint over trading days T−30 through T−5, where T is the news day. This is "what the price was doing before anyone knew."
2. **Event window ("the after").** Average the midpoint over T through T+2 (3 trading days starting at the news). The headline results use 3 days; 1-day and 5-day windows are robustness checks.
3. **Abnormal move = after − before.** If the news did nothing, this should hover near zero. Whatever is left over is attributed to the news.

Why the gap? Days T−4 through T−1 are **excluded from the baseline** on purpose. Rumors leak — by the day before a trade, insiders and reporters have often moved the price already. Including those days in the "before" would pollute the comparison. (This is also why heavily-rumored moves like LeBron-to-76ers show small announcement moves: the repricing happened during the rumor phase, which we deliberately throw away. The measured effect understates the total repricing for anticipated events.)

Then we average: first across all contracts for an event (e.g., all 30 teams' title futures for a trade), then across events within a cell (e.g., all 15 unscheduled-sports events). That final average is the cell mean you see in the paper.

---

## 3. n — and why there are three of them

"n" (sample size) shows up at three levels, and they do different jobs:

- **n₁: contracts per event.** ~30 for sports (one title future per team), up to ~150 for macro events. More contracts = a more stable event average.
- **n₂: baseline days per contract.** Up to 26 trading days in [T−30, T−5]. This is what the D16 rule is about: the old rule demanded ≥5 baseline days per contract; D16 lowered it to ≥3 (flagged "thin") because demanding 5 was throwing out the most informative events.
- **n₃: events per cell.** This is the n that matters for hypothesis tests: 15 unscheduled-sports events, 8 unscheduled-macro events. Every p-value in the paper is computed over events, not contracts — because events are the independent observations. (Thirty contracts moving on the same trade day are not 30 independent pieces of evidence; they're one event seen 30 ways.)

Why n₃ rules everything: the **standard error** of a mean is sd / √n. Double the events, shrink the noise by ~41%. With n=8 macro events and an sd of 3.65¢, the standard error of the macro mean is 3.65/√8 ≈ 1.29¢. That's the price of a small sample — and it's why the preregistration's power rule says any cell with fewer than 5 events gets means only, no p-values. Below n=5, a significance test is theater.

---

## 4. From numbers to a verdict: the t-test, worked by hand

H1c asks: do surprise macro shocks move prices differently than surprise sports news? Here are the actual 3-day event means (cents):

**Macro (n=8):** +9.47, +8.12, +8.12, +4.30, +3.76, +1.56, +1.46, −0.37 → mean **+4.55¢**, sd 3.65¢

**Sports (n=15):** −0.58, −0.48, −0.42, −0.40, −0.40, −0.18, +0.07, +0.05, +0.03, +0.03, +0.02, +0.02, +0.02, −0.01, +0.00 → mean **−0.15¢**, sd 0.24¢

The gap is 4.70¢. But is it real, or could luck produce a gap this big? The **two-sample t-test** answers that:

- **t = (gap) / (standard error of the gap).** The SE of the gap combines both groups' noise: √(3.65²/8 + 0.24²/15) ≈ 1.29¢. So t = −4.70 / 1.29 ≈ **−3.64**. Read it as: "the gap is 3.6 standard errors away from zero."
- **Welch's version**, which the paper uses, doesn't assume the two groups have the same variance. That's essential here — macro's sd (3.65¢) is 15× sports' (0.24¢). Assuming equal variance would be nonsense. Welch also adjusts the degrees of freedom down (df ≈ 7 here, driven by the small, noisy macro group) which makes the test appropriately conservative.
- **p = 0.0082** is the tail probability of the t-distribution at |t| = 3.64 with df ≈ 7. Plain English: *if there were truly no difference between macro and sports shocks, random luck would produce a gap this large only about 0.8% of the time.* That's strong evidence the difference is real.

---

## 4b. Same machinery, fairer sample: why the verdict changed (D18)

Section 4 used the preregistered aggregation: every sports event averaged across all ~30 team contracts. That was the wrong aggregation — a trade mechanically reprices 2 teams, so the sports mean was diluted by construction (the macro cell has no such dilution: every FED contract bets on the same decision). Re-running the identical t-test on the **involved teams only** (acquiring/keeping team per event, both sides reported but not averaged together):

- **Sports (involved teams, n=11):** +4.25, +3.94, +3.36, +3.21, +2.83, +1.00, +0.67, +0.49, 0.00, 0.00, −0.04 → mean **+1.79¢**, sd 1.72¢
- **Macro (n=8):** mean **+4.55¢**, sd 3.65¢ (unchanged)
- Gap = −2.76¢, SE = 1.39¢, t = −1.99, **p = 0.077** — not significant at 5%. 95% CI for the gap: [−5.89¢, +0.37¢].

Same test, same data, different aggregation, different verdict. This is the most important lesson in the whole document: **the estimand — what you choose to average — is a bigger decision than the test statistic.** The p=0.008 in §4 wasn't fabricated, but it was partly bought by an aggregation choice that suppressed one side. Preregistration locks the *plan*, but when the plan contains a design error, the honest move is to amend it loudly (D18), show all versions side by side, and let the verdict follow the fair one — which is what the paper does.

---

## 4c. When did the market move? (D19)

The t-tests anchor on the news *report* time (T0), but the market often moves earlier (leaks) or a day later (our candles are stamped at midnight ET, so mid-day news prints the next morning). D19 locates the actual jump: for each involved team, the largest single-day price move in the 10 days before to 5 days after the report.

Most jumps land within ±2 days of the report, confirmed by 100–900× volume spikes (Jaylen-to-Philly: +4.0¢ on 963× volume the day after the report). Three leaked early — Boston started falling 7 days before the Jaylen report, Cleveland priced the Mitchell extension 6 days early at free-agency open — and Kawhi priced 76 days early, at the June framework agreement rather than the September "official" completion. That is why Kawhi's report-anchored abnormal move is −0.04¢ while its jump-anchored move is +3.5¢: the first is a timestamp error, the second is the economically true repricing.

The statistical caution: measuring around the observed jump mechanically selects the largest move, so jump-anchored numbers are *upper bounds* and report-anchored are *lower bounds*. The formal test stays report-anchored — re-testing on hand-picked maxima would be circular. Truth is between, nearer the jump when a clear one exists.

---

## 5. The p-value, honestly

The most misunderstood number in science. Three things it is, three it isn't:

**It is:**
- P(data this extreme | the null hypothesis is true) — a statement about the data *assuming* nothing is going on.
- A continuous measure of surprise. p=0.008 is more surprising than p=0.04; the 0.05 line is a convention, not a law of nature.
- Sensitive to n. With enough data, even a meaningless effect becomes "significant" (see §7).

**It isn't:**
- The probability the finding is true. p=0.008 does **not** mean "99.2% chance macro shocks really move prices more." That number (a posterior probability) needs prior beliefs the test doesn't have.
- A measure of size. A tiny effect with huge n and a huge effect with small n can have the same p.
- A guarantee. p=0.008 means roughly 1-in-120 flukes look like this. Run 120 studies and you'll see one.

The paper's convention: p < 0.05 = "statistically significant" (worth taking seriously), reported exactly otherwise. The macro placebo at p=0.036 is the uncomfortable case — technically "significant," which is why it's disclosed rather than waved away.

---

## 6. Confidence intervals — the p-value's more useful sibling

A 95% confidence interval is the range of true values compatible with the data. Rough rule: **mean ± 2 × standard error.**

- H1c's gap: −4.70¢ ± ~2.6¢ → roughly **[−7.3¢, −2.1¢]**. Zero is far outside → significant. But notice the interval is wide: the data are consistent with the true gap being anywhere from 2 to 7 cents. Small n = wide intervals = honest uncertainty.
- H2's macro→sports spillover: **+0.16¢, 95% CI [+0.07¢, +0.25¢]**. Zero is outside (p=0.0033), but the whole interval sits under a quarter of a cent. Real, and irrelevant.

Read CIs, not just p-values: the CI tells you *how big* the effect plausibly is, which is usually the actual question.

---

## 7. Why "significant" ≠ "important": the H2 lesson

The H2 falsification test produced the paper's best teaching example. Macro news moved sports futures by +0.16¢ with p=0.0033 — *highly* significant. It is also ~3% of the own-market macro effect and well within the −2.8¢ background drift (§9). Economically, it's nothing.

How can something be highly significant and meaningless? Because significance is about **signal vs. noise**, and noise shrinks with √n. H2 ran over hundreds of contract-event pairs, so the standard error got tiny, and even a 0.16¢ wobble cleared the bar. That's not a flaw — it's the test doing its job (the wobble is probably real). The flaw would be *stopping* at p=0.0033 and declaring victory. Always pair the p-value with the effect size and ask: "significant, but significant *of what*?"

The mirror image: H1c's gap is enormous (4.7¢) and significant with only 8+15 events, because the signal dwarfs the noise.

---

## 8. Multiple testing and the Holm correction

The paper tests H1a through H1d — four related hypotheses. Problem: run four tests at 5%, and the chance of *at least one* fluke is ~1 − 0.95⁴ ≈ 19%. The more you test, the luckier your luckiest result looks.

The **Holm correction** fixes this without being as brutal as the Bonferroni method: sort the p-values smallest-first, then test the smallest against α/4, the next against α/3, and so on — you stop at the first failure. In practice only H1c was testable (the other cells had n<5), so Holm changed nothing (reported Holm p = 0.0082, identical). It's there to show the machinery was honest about the multiple shots on goal.

---

## 9. Robustness checks — the statistics of "but does it hold up?"

A single p-value is a claim; robustness checks are the cross-examination. Each one re-runs the headline under different choices, asking whether the result survives:

- **1-day and 5-day windows** (vs. the headline 3-day): H1c gives p=0.0051 and p=0.0013. A real effect shouldn't depend on exactly where you draw the window.
- **Liquid-only**: re-run on contracts with enough trading activity to trust the quotes. H1c: p=0.0091. The result isn't driven by stub quotes on dead contracts.
- **Strict rule vs. D16 rule**: the headline under the old baseline rule (p=0.0086) and the amended rule that includes Giannis (p=0.0082). Reporting both is the antidote to rule-shopping: you can see the amendment didn't manufacture the finding.
- **Placebo**: run the identical machinery on 50 random quiet days per market type. If the method "finds" effects where nothing happened, the method is broken. Sports placebo: p=0.95 (clean). Macro placebo: −2.8¢ drift, p=0.036 (marginal fail — see below).

On the macro placebo, the honest reading: quiet macro days drift −2.8¢ on their own, and the drift survives under the strict baseline rule too, so it's a feature of the data (overlapping contracts, scheduled-decision repricing bleeding into "quiet" days), not a D16 artifact. It doesn't invalidate the +4.55¢ headline — a *negative* background drift can't manufacture a *positive* finding; if anything the true macro effect is larger than measured. But it does mean macro magnitudes carry a noise band of a few cents, and the paper says so in "What's shaky" instead of burying it.

---

## 10. Dilution: event-level vs. contract-level

The trickiest statistical idea in the paper, and the one behind your Giannis objection:

- **Contract-level:** KXNBA-27-MIA moved +4.4¢ on trade day. Huge.
- **Event-level:** the Giannis trade averaged across all 30 teams' title futures = −0.58¢. Nothing.

Both are true. When one team acquires a superstar, maybe 3 teams' odds move (Heat up, Bucks down, a rival slightly down) and 27 don't. Averaging 30 contracts dilutes the concentrated move into invisibility. The paper's "sports barely move" headline is a statement about the *average contract* — the contract-level story (Miami's odds tripling) is told separately and not hidden.

This is also why the Big/Medium/Small tiers show no gradient at the event level (−0.18¢/−0.12¢/−0.10¢): the tier describes the *player*, but the event average still dilutes across 30 teams. The gradient the paper *does* find (H3's contract tiers: longshots move more in absolute terms) is measured at the contract level, where dilution can't hide it.

---

## 11. What "descriptive-only" means

The preregistration's power rule: any comparison cell with fewer than 5 unique events gets means and no p-values. This isn't modesty — it's statistics. With n=2 (the confirmatory scheduled-macro cell), a t-test's answer would be driven almost entirely by the t-distribution's fat tails, not by evidence. Reporting "p=0.31, not significant" would imply a test happened; it didn't, really. So the paper shows the numbers (+2.21¢ vs +4.83¢, direction matches the prediction) and labels them what they are: suggestive, not tested. The supplementary January extension (15 scheduled macro events, p=0.17) is the closest thing to a real H1a test, and it's labeled supplementary because the data were collected after seeing results.

---

## 12. The one-paragraph version

Every result in the paper is an average of (after − before) price differences, where "before" is the month leading up to the news and "after" is the 3 days starting at the news. Averages get compared across groups with a t-test that accounts for each group's noisiness and size; the p-value says how often luck alone would produce a gap that big. Small samples mean wide uncertainty (wide confidence intervals), many tests need correction (Holm), significant doesn't mean important (H2's 0.16¢), and averages can hide concentrated effects (Giannis). And the D18 lesson: *what* you average is a bigger decision than *how* you test — the fair aggregation (involved teams: sports +1.79¢ vs macro +4.55¢, p=0.077) tells a more modest story than the diluted one (p=0.008). The paper reports the checks that could have killed each finding — different windows, liquid-only contracts, both baseline rules, all three aggregations, quiet-day placebos — and the ones that came back uncomfortable are in the text, not the footnotes.
