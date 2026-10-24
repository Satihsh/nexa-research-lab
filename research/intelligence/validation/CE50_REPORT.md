# H-CE50 results: the "CE 50 % Model" on NQ (binding) and ES (2026-10-23)

- **Pre-registration:** `PREREG_CE50.md` (361a2e63, approved before any data). Notes: `DEVIATIONS_CE50.md`.
- **Code:** `qc_ce50/main.py` 9a1ae51e (ES 20e3b454; MODE line only), frozen after 12/12 synthetic tests. The QC editor hash was verified before each run.
- **Runs:** once each; QC free node; project NEXA/CE50 38292473; 2010-01-04 → 2026-07-24.
- **Raw logs** (sha equal to the in-page hash of the QC log): `qc_ce50/logs_nq_cb463b32.txt` (a843c0f7), `qc_ce50/logs_es_75787582.txt` (b5388156).

## Verdict: REJECTED (NQ, binding) and REJECTED (ES)

| Instrument | Set | Trades | **Net R/trade (S1)** | 95 % CI | Win rate | Avg win / loss (R) | Mean 1R | Random-direction control | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **NQ** | **P 2010–2015 (outside the creator's sample)** | 1,300 | **−0.173** | [−0.291, −0.056] | 28.9 % | +2.23 / −1.15 | 10.8 pts | −0.362 (real beats 100 % of controls) | **REJECTED** |
| NQ | IN 2016–2026 (the creator's window) | 2,563 | **+0.072** | [+0.001, +0.133] | 33.7 % | +2.12 / −0.97 | 54.7 pts | — | (reported) |
| NQ | FULL | 3,863 | −0.011 | [−0.074, +0.054] | 32.1 % | — | 39.9 pts | — | — |
| ES | P 2010–2015 | 1,405 | **−0.196** | [−0.283, −0.119] | 29.4 % | +1.81 / −1.03 | 4.7 pts | −0.265 (92.6 %) | **REJECTED** |
| ES | IN 2016–2026 | 2,556 | −0.019 | [−0.086, +0.045] | 32.8 % | +1.89 / −0.95 | 12.5 pts | — | — |

- **Binding rule:** the P mean ≤ 0 ⇒ REJECTED, on both instruments.

## What the numbers say
1. **The rule works only inside the window the creator backtested, and only on NQ.**
   - NQ 2016–2026: +0.072R; all four sub-blocks positive; p = 0.023.
   - NQ 2010–2015: −0.17R; all four sub-blocks negative.
   - ES: negative in both periods.
   - A rule that is real should not flip sign the year before its backtest starts. This is the pattern of a rule fitted to (or chosen on) one period: H-ORB30L, the FYP IFVG study (S78) and the Zarattini replication (S76) all looked like this.
2. **The direction signal is not random.** The midline-plus-first-3-minute-close direction beats a random direction by ≈ 0.19R (NQ) and 0.07R (ES) in 2010–2015.
   - But the trade structure itself loses even with the right side. The random-direction control is very negative (−0.36R NQ): wide stops, ~70 % losers and costs.
3. **Costs matter more in the early years.** The pre-open range was small in 2010–2015 (NQ 1R ≈ 11 points vs ≈ 55 after 2016), so 2 points of cost was ≈ 0.19R per trade then and ≈ 0.04R later.
   - Even at S0 (1 point) NQ 2010–2015 is −0.045R; at 0 cost it is ≈ +0.01R.
   - So the 2016+ profit is mostly a bigger-ranges era plus a small directional tilt, not a robust edge.
4. **Profile, as the creator describes:** ~67–71 % losers, average winner ≈ +2.1R. Exits are by stop 95 % of the time; 43–50 % of trades trailed at least once.
5. **For a prop account:** even NQ's best window (+0.072R) is above the +0.025R bar, but the rule fails its out-of-sample period and ES. It is not a candidate. NEXA law L2: no re-tuning (e.g., "only after 2016" or "only when the range is wide") on these data.

## What this closes
- The opening-range / pre-open family on NQ/ES: H-ORB5, H-ORB30L, H-ORB-1, H-HOUGAARD and now H-CE50. All rejected or inconclusive out of sample.
- The Instagram claim "2016–2026, 2,625 trades, 59 % a year" is consistent with NQ's 2016–2026 in-sample result (positive, small per trade, large with leverage and compounding). It does not hold before 2016, or on ES.

## Multiple testing
2 trials. Ledger ≈ 185.
