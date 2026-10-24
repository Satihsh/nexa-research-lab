# PRE-REGISTRATION H-DISC1-RULES: do "lose small on red days, let green days run" rules improve the user's own trades?

**Status: BINDING.** User request 2026-10-23 (chat): "add a red-day / green-day rule check to the H-DISC1 journal analysis (daily stop, stop after 2 losses, trailing on winners) and pre-register how it will be judged."
- **Written before any H-DISC1 trade exists** (warm-up not started). Companion to `PREREG_DISC1.md`; it **never changes the H-DISC1 verdict**.

**The user's idea (2026-10-23):** red days are normal, but lose less on them; on good days, take bigger profit.

**What can be tested:**
- **Daily stop / pause rules** cut losses mechanically, without predicting anything. They help only if losses cluster: a bad trade makes the next one more likely to be bad (tilt, a hostile market).
- **Trailing exits** change the shape of results. They help only if your winners tend to keep going.
- Both are measured on your own 100 counted trades.

## 1. Data
- The same 100 (or 200, after the pre-declared extension) counted H-DISC1 trades, in time order, from `trade_review.csv`: entry/exit time, side, quantity, average entry/exit, initial stop.
- **1-minute bars** for the trailing check:
  - first choice: the Mac NEXA recorder of the traded MNQ chart (`recorder/MNQ*_M1/bars_<session>.csv`);
  - else the VM recorder `recorder/NQ_M1/` (same index, same tick size).
  - Bar times are UTC (verified).
- **Costs, identical for every variant:**
  - net USD = side × (exit − entry) × qty × $2 (MNQ point value) − qty × $2.22 per round trip;
  - $2.22 = $1.22 commission + 1 tick ($0.50) slippage per side.
- **1R** = |entry − initial stop| × qty × $2. Net R = net USD ÷ 1R.

## 2. Variants (fixed now)
| Code | Rule | How it is applied to the same trades |
|---|---|---|
| **B** | Baseline: the trades as taken | Actual entries and exits |
| **V1** | **Daily stop −$250** (the H-DISC1 risk cap) | Once a session's cumulative net (in this variant) is ≤ −$250, that session's later trades are skipped |
| **V2** | **Two-loss pause** | After 2 losing trades in a row (net < 0, across sessions), skip the rest of that session **and** the whole next session; the count restarts after the pause |
| **V3** | **Trail winners, no fixed target** | Each trade keeps its real entry (time, price, qty) and initial stop. Bars are scanned from the minute after entry: (1) exit if the bar touches the current stop (fill at the stop, or the bar's open if it gaps through); (2) then update the best price; once the best price is ≥ entry + 1R (long; mirror for short), the stop trails 1R behind the best price, never loosening; (3) otherwise exit at the close of the 15:07 CT bar (flat by 15:08 CT). If the trade's day has no bars, the actual result is used (counted) |
| **V4** | V1 + V3 | V3 exits, then the V1 daily stop on those results |

- H-DISC1 already caps trading at 2 trades a day, so V1 mostly means "stop after a full first-trade loss". V2 is a streak rule across days, so it still bites under the cap.
- **Assumption, stated plainly:** the counterfactuals keep every other trade unchanged. In real life, following a rule may change how you trade. That is why a rule that helps is then tested forward (§5).

## 3. Judging (computed once, at the same time as the H-DISC1 verdict)
- **Unit: the trading session.** For each variant v and session d: Δ_v(d) = net R of v − net R of B (skipped trades = 0).
- **Statistic:** mean Δ_v over all evaluation sessions with ≥ 1 baseline trade. Moving-block bootstrap over sessions (block 5, B = 2,000, seed 20261023), one-sided p in each direction.
- **Verdict per variant** (Bonferroni over 4 variants, α = 0.05/4 = 0.0125):
  - **HELPS:** mean Δ > 0 and p(Δ ≤ 0) ≤ 0.0125;
  - **HURTS:** mean Δ < 0 and p(Δ ≥ 0) ≤ 0.0125;
  - **NO CLEAR DIFFERENCE:** otherwise.
- **Also reported (no verdict effect):** for B and each variant:
  - total and per-trade net R; trades kept;
  - **average red-day loss and average green-day gain (R)**, green-day share, worst day, max drawdown (R);
  - largest winner;
  - Topstep 50K check on the daily USD path ($2,000 trailing end-of-day loss limit, locking at the start balance): breached yes/no, lowest buffer;
  - **loss clustering:** P(loss | previous trade lost) vs P(loss), and the lag-1 autocorrelation of trade R. This is the evidence that tells whether V1/V2 can work at all.
- **V3 validity:** if more than 10 % of trades lack bars, V3 and V4 are reported as INVALID (no verdict).

## 4. Honest power statement
- 100 trades ≈ 50–70 sessions. A rule must change the average day by roughly 0.25–0.4R to reach HELPS/HURTS at this size. Smaller real effects will read NO CLEAR DIFFERENCE.
- V1/V2 only remove trades. If your losses do not cluster, they cut good and bad trades alike and cannot add an edge; they still reduce drawdown, which is reported.

## 5. Use of the result
- **HELPS:** the rule becomes your forward rule for the next block (the extension or the next 100 trades), declared before that block starts. Its forward result decides whether it stays.
- It is **never** applied backward to upgrade the H-DISC1 verdict.
- **HURTS or NO CLEAR DIFFERENCE:** no change; the NEXA panel's daily stop line stays as a risk limit (drawdown protection), not as an edge.

## 6. Code, tests, freeze
- `disc1_rules.py` (standard library only): reads `trade_review.csv` and recorder bars; drops the 20 warm-up trades; computes B and V1–V4, Δ, bootstrap, clustering and the Topstep check; writes JSON.
- `test_disc1_rules.py` (synthetic, `run_tests.py`):
  - costs and R;
  - the V1 daily stop;
  - the V2 pause across sessions;
  - V3: trailing, the 1R activation, stop-first, gaps, the 15:07 CT exit, no look-ahead (the entry bar is not used);
  - V4 composition; missing bars;
  - the session Δ and verdict thresholds;
  - clustering statistics; the Topstep breach.
- Tests pass before the hash. **Run once,** together with the H-DISC1 verdict.
