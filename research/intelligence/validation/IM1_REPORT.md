# IM1 results: market intraday momentum (last half-hour) on Pepperstone FX and gold (2026-10-11)

- **Pre-registration:** `PREREG_IM1_INTRADAY_MOMENTUM.md` (sha aee2e870…).
- **Code, tests 7/7, calendar and deviations D1–D9:** hashed before discovery (`PREREG_HASHES.txt`, 10:40 UTC).
- **Splits:** discovery → validation → holdout, each opened once.
- **Raw output:** `im1_results_disc.json`, `im1_results_val.json`, `im1_results.json`.
- **Rule** (Baltussen et al. 2021, η(r_ROD)): 30 minutes before the close (FX 15:00 ET, XAU 13:30 ET), go long if the return since the previous close is positive, short if negative; exit at the close.
- **Data:** EURUSD, GBPUSD, USDJPY, XAUUSD, 2017-07 → 2026-09-25; 8,660 trades.

## Verdict: **REJECTED** (net); **the gross effect is confirmed**. Same pattern as C1: real but not tradable at retail cost

| Pooled P (equal weight per trade) | Discovery | Validation | Holdout | **Pooled** |
|---|---|---|---|---|
| Trades | 5,005 | 1,955 | 1,700 | 8,660 |
| **Gross** (before spread, commission, stress) | +0.42 bp | — | — | **+0.35 bp** [+0.10, +0.60] |
| Net S0 (commission + spread) | −0.58 [−0.87, −0.25] | −0.30 [−0.83, +0.09] | −0.91 [−1.61, −0.31] | **−0.58** [−0.83, −0.33] |
| **Net S1 (decides)** | −1.08 | −0.80 | −1.41 | **−1.08** [−1.33, −0.83] |
| Net S2 | −1.58 | −1.30 | −1.91 | −1.58 |

**Acceptance criteria:** 6 of 8 failed; criteria 5 and 8 passed.

| # | Criterion | Result |
|---|---|---|
| 1 | Discovery | ✗ |
| 2 | Validation / holdout | ✗ |
| 3 | Pooled CI | ✗ |
| 4 | Placebo (pooled p_tod 0.088) | ✗ |
| 5 | **Mechanism (gross β CI > 0)** | **✓** |
| 6 | Stability (0 of 10 years positive net) | ✗ |
| 7 | DSR ≈ 0 | ✗ |
| 8 | Stop / cost ≥ 5 (median 25–37×) | ✓ |

## By instrument (S1 net; gross; N2 slope; placebo)

| | Net S1 (bp) | Gross (bp) | β (r_LH on r_ROD, bp/bp) 95 % CI | Placebo p_tod (33 times) |
|---|---|---|---|---|
| EURUSD | −0.83 | +0.47 | 0.012 [0.004, 0.019] | **0.029** |
| GBPUSD | −0.78 | +0.55 | 0.013 [0.004, 0.023] | **0.029** |
| USDJPY | −0.87 | +0.50 | 0.016 [0.007, 0.025] | 0.118 |
| XAUUSD | −1.88 | **−0.16** | 0.010 [−0.006, 0.028] | 0.765 |
| **Pooled** | −1.08 | +0.35 | 0.012 [0.001, 0.022], R² 0.66 % | 0.088 |

**Reading:**
- **FX shows the published effect on Pepperstone data.** The slope is positive in all three pairs, and for EUR/GBP the true close beats almost all placebo times (p 0.029).
- Pepperstone's R² (≈ 0.7 %) is of the same order as the paper's currency R² (0.19 % in-sample, 0.26 % out-of-sample).
- The paper reports β in its own regression scaling, so slopes are compared by sign and significance only.
- **The gross edge, about +0.5 bp per FX trade, is half the round-trip cost** (≈ 0.9–1.0 bp: USD 7/lot commission ≈ 0.7 bp + spread ≥ 0.2 pip).
- **Gold shows no effect** on this feed (gross −0.16 bp; placebo p 0.77). The COMEX settlement hour does not transfer to spot XAU.

## Robustness (S1 net, reported only)

- **All variants are negative:**
  - FX close 14:00 ET −1.38;
  - Gao predictor (r_ONFH) −0.93;
  - entry at the C − 31 close −1.08;
  - spread floor 0.1 / 0.3 pip −0.78 / −0.89;
  - stop 3σ / 6σ −1.08 / −1.07.
- **Largest-move days** (top 20 % |r_ROD|): −0.63, the least negative. This is consistent with the hedging story (larger moves, larger hedging flow), but still a loss.
- **Every calendar year is net negative** (2017 −1.16 … 2026 −2.04).

## Conclusion (evidence class: NEXA, pre-registered)

1. **Market intraday momentum exists in Pepperstone FX** (gross, statistically clear, close-specific for EUR and GBP). This is a successful replication of a peer-reviewed effect on NEXA's own feed.
2. **It is not tradable with market orders at NEXA's cost.** The effect is about +0.5 bp, the round trip about 1 bp. No year, split, instrument or variant is net positive.
3. **The binding constraint is again cost, not signal**, as in C1 (Tokyo fix: gross +2.17 bp vs net −0.58 bp).
   - The only levers that could change this are **execution-cost reductions**: limit / passive entries, a lower commission tier, or larger-move-day filtering decided in advance.
   - **Each would be a new hypothesis.** It must be pre-registered and tested on data not used here (prospective, or another instrument). It is **not** a re-run of IM1.
4. **No re-run with altered windows under IM1.**
