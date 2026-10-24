# Strategy Factory: XAUUSD H1 (run 2026-09-27)

**Result: no candidate.** No strategy family meets the frozen promotion gate. Nothing from this run goes to the EA.

| Item | Value |
|---|---|
| Data | Axiory XAUUSD H1 (`XAUUSD_H1.csv`, sha256 `427a359c…`), 50,801 bars, 2018-01-02 → 2026-07-31, broker server time |
| Protocol | `nexa_factory_run.py` PROTOCOL sha `b1d8203b159fa2ef`, frozen and recorded in PROGRESS.md before the first run |
| Trials | 18 configurations across 6 families (every one counts toward deflated Sharpe) |
| Costs | **ASSUMED.** The source has no bid/ask. BASE spread 1.5 bp + 0.25 bp slippage per side; STRESS 3 + 0.5; SEVERE 5 + 1 |
| Fills | Next-bar open; bid bars; the stop wins an ambiguous bar; gaps through the stop fill at the open |
| Machine output | `factory_XAUUSD_H1.json`, `factory_XAUUSD_H1_spec.json` |

## Walk-forward OOS (2020–2024, config re-chosen each year on prior years only)

| Family | Source | n | E[R] | 95% CI | PF | Max DD | STRESS E[R] | p | PBO | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| trend_breakout (TrendLock synthesis) | Agent-Lab `TrendLock_Quantum_Synthesis.mq5` | 419 | +0.086 | [−0.042, +0.220] | 1.15 | 36.5R | +0.055 | 0.094 | 0.004 | EDGE_NOT_DEMONSTRATED |
| breakout (plain Donchian control) | Master §20 | 482 | +0.024 | [−0.092, +0.145] | 1.04 | 33.9R | −0.012 | 0.344 | 0.29 | EDGE_NOT_DEMONSTRATED |
| momentum (TSMOM) | Master §12 | 539 | −0.034 | [−0.149, +0.083] | 0.95 | 62.8R | −0.133 | 0.710 | 0.55 | EDGE_NOT_DEMONSTRATED |
| mean_reversion (z-score, ADX<20) | Master §12 | 536 | −0.098 | [−0.181, −0.016] | 0.82 | 56.8R | −0.156 | 0.989 | 0.65 | NEGATIVE_EXPECTANCY |
| camarilla (H3/L3, H4/L4 fade) | Master §11 | 1913 | −0.066 | [−0.121, −0.011] | 0.89 | 140.0R | −0.153 | 0.991 | 0.20 | NEGATIVE_EXPECTANCY |
| NULL_RANDOM (coin flip) | baseline | 415 | +0.021 | [−0.114, +0.155] | 1.03 | 32.1R | −0.002 | 0.380 | – | baseline |

## Holdout (2025-01 → 2026-07, evaluated once, config frozen on DEV+VAL)

| Family | Frozen config | n | E[R] | 95% CI |
|---|---|---|---|---|
| trend_breakout | TL_STDB_d20_s3.0 | 139 | +0.160 | [−0.063, +0.386] |
| breakout | DONCHIAN_d55_s3.0 | 163 | +0.208 | [+0.000, +0.413] |
| momentum | TSMOM_l48 | 172 | −0.004 | [−0.210, +0.209] |
| mean_reversion | MR_Z_l24_z2.0 | 163 | −0.117 | [−0.271, +0.037] |
| camarilla | CAM_REV_L3 | 586 | −0.082 | [−0.180, +0.016] |
| **NULL_RANDOM** | coin flip | 128 | **+0.151** | [−0.092, +0.406] |

## Adversarial reading ("why is this wrong?")

1. **The holdout rewards drift, not skill.** Random entries made +0.151R per trade in the holdout. TrendLock's +0.160R and Donchian's +0.208R cannot be told apart from the coin flip at these sample sizes. Gold's 2025–26 rally favours anything with a long bias.
2. **The TrendLock result is one-sided.** Walk-forward longs made +0.188R (n=229) and shorts −0.037R (n=190). A symmetric trend rule that works only in one direction, during a secular gold bull market, is showing beta.
3. **Year-to-year instability.** TrendLock by year: 2020 +0.33, 2021 −0.12, 2022 −0.08, 2023 +0.08, 2024 +0.26. Two of five walk-forward years are negative.
4. **Low PBO is not evidence of edge.** 0.004 means the same config ranked first on every look-back, so the choice among 4 near-identical configs was stable. It says nothing about whether any of them beats chance. The deflated Sharpe (0.29) does address that, and it fails.
5. **Costs are assumed.** Under SEVERE costs TrendLock falls to +0.014R. A broker-measured spread series (`NEXA_TickLogger`, or bar spreads from the MT5 tester) is needed before any cost claim.
6. **Mean reversion and Camarilla fading are reliably negative** (CI entirely below zero). That is informative: fading H3/L3 excursions on gold H1 loses money after costs.

## Decisions

- **No family is promoted.** TrendLock stays a non-NEXA, uncompiled-for-NEXA research idea.
- **Worth one more honest test, not a promotion:** TrendLock as a long/short-symmetric rule with a drift control (for example, excess return over a matched random-entry baseline, per direction) on a second instrument with broker data. That second test must be pre-registered with a new protocol hash.
- Adding more parameter configs to rescue a family is **not allowed** under this protocol; it would raise the trial count and must be declared.
