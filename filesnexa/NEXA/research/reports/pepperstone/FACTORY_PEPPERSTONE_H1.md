# Strategy Factory: Pepperstone H1, 5 symbols (run 2026-09-27)

**Result: no candidate.** 0 of 25 family×symbol tests pass the frozen gate, and 0 survive Benjamini–Hochberg (q = 0.10) across all 25 hypotheses.

| Item | Value |
|---|---|
| Data | Pepperstone-Demo H1 bars exported by `NEXA_BarExport` in the MT5 Strategy Tester (open-prices mode), 2016-12-30 → 2026-09-25. 57.5k–60.6k bars per symbol. 3-year chunks; the 20 overlapping bars per join were verified identical (0 conflicts). |
| Protocol | `nexa_factory_run.py`, **unchanged**: sha `b1d8203b159fa2ef`. DEV 2018–22, VAL 2023–24, HOLDOUT 2025-01 → 2026-09 (evaluated once), walk-forward 2020–24 |
| Costs | The protocol's ASSUMED costs. BASE: 1.5 bp spread + 0.25 bp slippage per side. This is conservative against Pepperstone's measured costs: raw spread ≈ 0–0.2 pip on FX majors, plus a $3.50/lot/side commission observed in the tester. |
| Trials | 18 configs per symbol × 5 symbols = 90 configurations. DSR uses n=18 per symbol; the cross-symbol FDR below covers all 25 non-null families. |
| Machine output | `factory/factory_PEPPERSTONE_<SYM>_H1.json`, `factory/*_spec.json` |

## Walk-forward OOS and holdout

| Sym | Family | n | E[R] | 95% CI | STRESS E[R] | p | DSR | PBO | Holdout n | Holdout E[R] |
|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | trend_breakout | 472 | −0.112 | [−0.226, +0.005] | −0.169 | 0.97 | 0.00 | 0.24 | 139 | −0.006 |
| EURUSD | breakout | 672 | −0.092 | [−0.185, +0.003] | −0.178 | 0.97 | 0.00 | 0.68 | 220 | +0.106 |
| EURUSD | momentum | 379 | −0.013 | [−0.163, +0.130] | −0.087 | 0.57 | 0.00 | 0.53 | 137 | −0.073 |
| EURUSD | mean_reversion | 404 | −0.135 | [−0.231, −0.037] | −0.296 | 1.00 | 0.00 | 0.22 | 130 | −0.154 |
| EURUSD | camarilla | 1890 | −0.231 | [−0.284, −0.178] | −0.398 | 1.00 | 0.00 | 0.97 | 735 | −0.240 |
| EURUSD | NULL | 457 | −0.093 | [−0.216, +0.035] | −0.211 | 0.93 | – | – | 154 | −0.114 |
| GBPUSD | trend_breakout | 429 | −0.089 | [−0.203, +0.028] | −0.116 | 0.93 | 0.00 | 0.07 | 147 | −0.104 |
| GBPUSD | breakout | 951 | −0.171 | [−0.253, −0.089] | −0.232 | 1.00 | 0.00 | 0.66 | 237 | −0.036 |
| GBPUSD | momentum | 382 | −0.083 | [−0.216, +0.058] | −0.189 | 0.88 | 0.00 | 0.90 | 132 | −0.176 |
| GBPUSD | mean_reversion | 264 | −0.032 | [−0.151, +0.090] | −0.096 | 0.70 | 0.02 | 0.04 | 59 | −0.268 |
| GBPUSD | camarilla | 1512 | −0.170 | [−0.233, −0.110] | −0.329 | 1.00 | 0.00 | 0.46 | 706 | −0.180 |
| GBPUSD | NULL | 452 | −0.201 | [−0.323, −0.078] | −0.284 | 1.00 | – | – | 158 | +0.110 |
| USDJPY | trend_breakout | 422 | +0.080 | [−0.044, +0.210] | +0.003 | 0.11 | 0.00 | 0.06 | 151 | −0.133 |
| USDJPY | breakout | 787 | +0.037 | [−0.061, +0.136] | −0.027 | 0.23 | 0.00 | 0.78 | 236 | −0.020 |
| USDJPY | momentum | 349 | −0.005 | [−0.153, +0.148] | −0.079 | 0.53 | 0.00 | 0.81 | 127 | +0.144 |
| USDJPY | mean_reversion | 578 | −0.220 | [−0.298, −0.141] | −0.325 | 1.00 | 0.00 | 0.28 | 139 | −0.092 |
| USDJPY | camarilla | 1978 | −0.139 | [−0.192, −0.089] | −0.300 | 1.00 | 0.00 | 0.34 | 667 | −0.100 |
| USDJPY | NULL | 434 | −0.112 | [−0.242, +0.013] | −0.193 | 0.96 | – | – | 153 | −0.125 |
| XAUUSD | trend_breakout | 416 | +0.097 | [−0.028, +0.227] | +0.076 | 0.07 | 0.31 | 0.02 | 152 | +0.139 |
| XAUUSD | breakout | 515 | +0.018 | [−0.093, +0.136] | −0.003 | 0.38 | 0.03 | 0.52 | 232 | +0.151 |
| XAUUSD | momentum | 544 | −0.057 | [−0.170, +0.059] | −0.128 | 0.83 | 0.00 | 0.44 | 179 | +0.024 |
| XAUUSD | mean_reversion | 477 | −0.090 | [−0.185, −0.003] | −0.157 | 0.98 | 0.00 | 0.45 | 66 | −0.082 |
| XAUUSD | camarilla | 1916 | −0.055 | [−0.107, −0.000] | −0.148 | 0.98 | 0.00 | 0.25 | 648 | −0.090 |
| XAUUSD | **NULL** | 427 | **+0.112** | [−0.024, +0.244] | +0.057 | 0.05 | – | – | 139 | −0.077 |
| XAGUSD | trend_breakout | 438 | +0.069 | [−0.055, +0.192] | +0.052 | 0.14 | 0.04 | 0.00 | 144 | +0.189 |
| XAGUSD | breakout | 937 | −0.018 | [−0.107, +0.073] | −0.030 | 0.66 | 0.00 | 0.56 | 322 | +0.037 |
| XAGUSD | momentum | 256 | −0.037 | [−0.211, +0.132] | −0.029 | 0.67 | 0.01 | 0.57 | 82 | −0.300 |
| XAGUSD | mean_reversion | 337 | −0.186 | [−0.291, −0.078] | −0.194 | 1.00 | 0.00 | 0.22 | 170 | −0.159 |
| XAGUSD | camarilla | 1930 | −0.088 | [−0.141, −0.034] | −0.132 | 1.00 | 0.00 | 0.44 | 633 | −0.040 |
| XAGUSD | NULL | 435 | −0.048 | [−0.174, +0.081] | −0.066 | 0.77 | – | – | 139 | +0.097 |

## Adversarial reading

1. **Nothing is distinguishable from chance after multiple testing.** The best p-value in 25 tests is 0.07 (XAUUSD trend_breakout). BH at q=0.10 rejects nothing, and the best DSR is 0.31, far below 0.95.
2. **Gold again rewards drift, not rules.** On XAUUSD, coin-flip entries (+0.112R) beat the TrendLock trend rule (+0.097R) over the same walk-forward years. This replicates the Axiory finding on a second, independent data source.
3. **The only positive walk-forward families are trend rules on USDJPY and the metals**, the instruments with strong 2020–24 trends. None survives STRESS costs with a CI above zero.
4. **Mean reversion and Camarilla fading lose on all five symbols**, with CIs entirely below zero on most. They are reliably negative after costs at H1.
5. **Holdout numbers are noisy and must not be cherry-picked.** For example, XAGUSD trend_breakout shows +0.189 on 144 trades, but the same symbol's NULL shows +0.097. Holdouts decide nothing without a walk-forward pass first.

## What was NOT tested here, and why

- **SMC/ICT/liquidity-sweep and session behaviour** is NEXA's own EA logic (PDH/PDL/Asia liquidity state machine). It was tested in the MT5 Strategy Tester, not re-implemented in Python; see `PEPPERSTONE_FINAL_AUDIT.md`.
- **Intermarket, sentiment and news families**: no strategy of that kind exists in the repository, and no timestamped news/sentiment history is available. Inventing one would violate the directive not to add arbitrary strategies.
