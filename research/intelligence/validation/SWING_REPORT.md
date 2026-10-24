# H-SWING results: daily trend-following on 20 CME futures, 2026-10-18

- **Pre-registration:** `PREREG_SWING_TREND.md` (491912c2), clarifications `DEVIATIONS_SWING.md` C-1/C-2 (ce5d2450), both before any data.
- **Code:** `qc_swing/main.py` (e8cf492d), frozen after 9/9 G1 tests (`test_swing.py`). The QC editor hash was verified before the run.
- **Run (once, QuantConnect free node):** project 38032653 "NEXA/SWING", backtest "Virtual Red Parrot". Reads data only, never trades (so QC shows $100,000 equity and 0 orders).
- **Data:** 2009-01-02 → 2026-07-21 (the end of QC's futures data). **Evaluation 2011-01-03 → 2026-07-21**: 4,009 days, 187 months. All 20 markets used; RTY joins 2017-07, GC 2012-11, SI 2011-05, HG 2011-09.
- **Outputs:** raw log `qc_swing/logs_virtual_red_parrot.txt` (sha 9ac02a22), parsed `qc_swing/swing_results.json`, post-processing `qc_swing/swing_post.py` (descriptive DSR and capital table only).

## Verdict: INCONCLUSIVE (primary rule P)

Per §5 the verdict is set by **P at S1** (2-tick cost). Variants are "reported, never substituted".

| Rule | Ann. net return | Ann. vol | Sharpe | Mean daily net (S1) | 95 % CI | p (one-sided) | Blocks > 0 | Max DD* | Verdict (own) |
|---|---|---|---|---|---|---|---|---|---|
| **P: 12-month TSMOM, 20 markets** | **+5.5 %** | 12.7 % | **0.43** | +2.18 bp | **[−0.02, +4.65] bp** | 0.027 | **4/4** | 30 % | **INCONCLUSIVE** |
| V-DON: Turtle 55/20 | −0.2 % | 11.9 % | −0.01 | −0.07 bp | [−2.07, +2.01] | 0.51 | 2/4 | 43 % | REJECTED |
| V-MA: 50/200 cross | +0.5 % | 12.8 % | 0.04 | +0.18 bp | [−2.14, +2.40] | 0.46 | 2/4 | 46 % | INCONCLUSIVE |
| V-IDX: P on ES + NQ only | +18.9 % | **40.6 %** | 0.47 | +7.51 bp | [+0.32, +14.43] | 0.018 | 3/4 | **113 %** | VALIDATED (G4), secondary only |
| LONG benchmark (20 mkts) | +3.3 % | 16.3 % | 0.20 | +1.33 bp | [−1.82, +4.29] | 0.21 | 3/4 | 62 % | (control) |
| **P − LONG** | | | | +0.86 bp | [−2.86, +4.95] | 0.31 | | | not significant |

*Max DD is the peak-to-trough fall of the **summed** daily returns at the rule's own sizing (40 % vol per market). For V-IDX, 113 % means the rule as sized would have lost more than the whole account.

- **P misses VALIDATED by a hair.** The mean is positive, all 4 time blocks are positive and p = 0.027, but the 95 % CI lower bound is −0.0000024 (just below 0). By the binding rule this is INCONCLUSIVE.
- **Costs are not the problem.** At S0 (1 tick) +2.27 bp, S1 +2.18 bp, S2 (4 ticks) +2.01 bp, gross +2.38 bp. Costs are 0.49 %/yr, 81 % of them from rolls.
- **Without 2022** (a known trend year) the mean is +1.98 bp, nearly unchanged. P is not a one-year result.
- **P's years:** positive in 11 of 16 (2026 partial). Worst years 2016 −14.8 %, 2023 −12.0 %, 2018 −9.5 %.
- **P by sector** (summed net contribution): equity +0.44, FX +0.23, rates +0.15, energy +0.14, metals +0.03, grains −0.12.
- **P vs LONG:** not significant (p 0.31). We cannot say P adds anything beyond holding the same markets long. Equities, the strongest sector in both, rose through most of 2011–2026.
- **Descriptive DSR** (Bailey & López de Prado; trial variance from the 4 H-SWING rules; kurtosis not logged, normal assumed):
  - P: **0.75 at 4 trials, 0.16 at ~161 trials**;
  - V-IDX: 0.78 at 4 trials, 0.19 at ~161 trials;
  - all below the 0.95 bar.

## Why V-IDX's "VALIDATED" is not a result
1. **It is a declared secondary.** The pre-registration fixes P as the verdict rule; secondaries are reported, never substituted.
2. **Multiple testing.** p = 0.018 does not survive the 4 H-SWING trials (Bonferroni 0.0125), and DSR is 0.19 at the NEXA ledger's ~161 trials.
3. **No drift control for ES + NQ.** The pre-registered LONG control covers all 20 markets, not ES + NQ alone. TSMOM on two US indices that rose for most of 2011–2026 was mostly long, so timing skill cannot be separated from simply holding the index.
4. **The sizing is not survivable.** 40 % vol on each of two highly correlated indices gives ~40 % portfolio vol, a −18 % year in 2022, and a summed drawdown above 100 %.

## The user's questions
- **Green days:** P 52.6 % of days, V-IDX 54.6 %, LONG 51.4 %. **Green months:** P 50.3 %, V-IDX 59.9 %. The longest losing month streak is 6 (P) and 8 (V-IDX). Trend-following does not give 18/20 green days, as `NEXA_RESEARCH_LEDGER_2026-10-18.md` §2 predicted.
- **Capital (descriptive, §5).** This is the account at which 1 contract of the smallest CME size equals the rule's weight (current prices and vol). Micro multipliers marked ? are unverified; rates and grains use full size.

  | Market | Contract | Account for P (N = 20) | Account for V-IDX (N = 2) |
  |---|---|---|---|
  | ES | MES | $259k | $26k |
  | NQ | MNQ | $663k | $66k |
  | SI | SIL | $1.69M | — |
  | ZN / ZB / ZF | full size | $709k–$735k | — |
  | FX micros (M6E, M6B, M6A, MJY?, MCD?) | micro | $47k–$96k | — |

  - **P needs ≈ $1.7M** to hold every market at ≥ 1 contract (≈ $0.7M without silver, still with full-size rates).
  - V-IDX needs ≈ $66k for 1 MNQ + about 2–3 MES. That is at 40 % vol, i.e. a sizing that would have wiped the account at least once.
- **Prop route:** not applicable. Apex bans holding positions through the close (`APEX_RULES_SNAPSHOT_2026-10-18.md`).

## Consequence (binding, §7)
- **INCONCLUSIVE closes daily trend-following on this universe for now.** No forward check, no capital review and no trading follows from this run.
- **NEXA record:** this is the **closest any NEXA test has come to an edge** (positive in all 4 blocks, cost-robust, 11/16 years positive), and the only one where the problem is statistical power rather than a negative mean. It is still not validated, and it is not tradable at the user's capital.
- **Any follow-up is a new hypothesis that needs fresh user approval and a new pre-registration.** One example: a forward paper record of P from 2026-07-22 on, with an ES + NQ buy-and-hold control. NEXA law L2 applies: no re-tuning of vol target, lookback or universe on this data.
