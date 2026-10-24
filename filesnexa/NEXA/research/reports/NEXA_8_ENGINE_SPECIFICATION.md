# NEXA 8-engine specification (RESEARCH_8E_V1, frozen before VAL)

**Scope.** This is research only.
- It is **not** part of V2 (anchor `6090be68…`, still FROZEN and not opened).
- It is **not** in the live EA. Nothing is deployed.

**Code:**
- `research/nexa_8e_engines.py`: features;
- `research/nexa_8e_research.py`: signals, simulation, metrics;
- `research/protocols_8e.py`: protocol;
- `research/nexa_8e_costs.py` and `research/nexa_8e_capital.py`: cost and capital modules.

## 0. Data truth: what Pepperstone MT5 actually provides (measured)
| Item | Available? | Evidence | Consequence |
|---|---|---|---|
| M1 bid OHLC + recorded spread + tick_volume | **yes**, 2017-06…2026-09 (EURUSD, GBPUSD, USDJPY, XAUUSD, XAGUSD) | `data/pepperstone/m1_canonical` | engines 1–5, 8 and the proxies of 6–7 |
| `tick_volume` meaning | **quote-update count**, not traded volume | MT5 OTC CFD; ticks have `volume = 0` | it is never called volume |
| Ticks | bid/ask quotes only, 2026-08-28…09-25 (21 days), `last = 0`, `volume = 0` | `data/pepperstone/*_ticks_recent.csv.gz` | no trade prints, no aggressor side |
| Real / exchange volume, aggressor flags, trade direction | **no** | tick `flags` carry only bid/ask-change bits | **true order-flow delta cannot be computed** |
| Depth of market / market-by-order | **no** (`DOM available = false`) | earlier audit | — |
| Trade size / block trades | **no** | OTC CFD feed | **"Big Trades" cannot detect trade size** |
| NAS100 history | **no** local bars; spec only | spec probe 2026-10-01 | **NAS100 research BLOCKED** pending a data decision |

## 1. Engines (version 1; all causal, certified by `nexa_causality`)
All features are computed on **completed** UTC bars built only from the M1 rows inside each bar (`resample_m1`). A bar's values are decided at its close.

| # | Engine | Definition | Outputs |
|---|---|---|---|
| E1 | **Bollinger Squeeze** | BB(20, 2.0 σ population, SMA mid) inside KC(EMA20 mid ± 1.5 × Wilder ATR20). **On** = BB_upper < KC_upper ∧ BB_lower > KC_lower. **Fire** = on at t−1 ∧ off at t. Compression, **not** direction. | `sq_on`, `sq_dur`, `sq_depth`, `bb_bandwidth`, `kc_width`, `sq_compression_pct` (trailing 252-bar rank), `sq_fire`, `sq_bars_since_fire`, `sq_fire_dir` |
| E2 | **VEI** | Wilder ATR(14) / Wilder ATR(50) | `vei`, `vei_slope` (3-bar), `vei_accel`, `vei_pct` (trailing rank), `tickvol_z` (quote count vs prior 100 bars) |
| E3 | **Donchian** | upper/lower = max high / min low of the **N bars before** the current bar | `dc_upper/lower`, `brk_close_up/dn` (close **strictly** beyond), `brk_touch_up/dn`, `brk_mag_atr`, `close_location`, `range_exp`, `atr14` |
| E4 | **EMA200 trend** | EMA(200) of close, a **trend/regime feature**, not "institutional flow" | `above_ema200`, `ema200_slope_atr` (10-bar), `ema200_dist_atr` |
| E5 | **EMA9 + MACD(5,13,4)** | MACD = EMA5 − EMA13, signal = EMA4(MACD), hist = MACD − signal | `mom_long_score` = #{close > EMA9, MACD > signal, hist > 0, hist slope > 0} (0–4); short mirror |
| E6 | **Order-flow PROXY** | buy_q = Σ quote counts of M1 bars closing above their open; sell_q mirror. ratio = (buy_q + 1)/(sell_q + 1). A 1-minute **tick-rule split of quote activity**, **not aggressor order flow**. | `ofi_ratio_up/dn`, `ofi_z`, `ofi_buy_q`, `ofi_sell_q` |
| E7 | **Abnormal quote activity** ("Big Trades" request) | bar quote count / median of the prior 100 bars; trailing 500-bar percentile; max M1 burst. **Quote activity, not trade size.** | `qb_score`, `qb_pct`, `qb_m1_burst` |
| E8 | **TD Sequential** (DeMark classic, v1) | Buy setup = consecutive close < close[4] begun by a bearish price flip, complete at 9. Sell mirror. Countdown after a completed setup: close ≤ low[2] (buy) / close ≥ high[2] (sell), complete at 13, cancelled by an opposite completed setup. **Simplifications:** no TDST, perfection or recycling. | setup and countdown counts, 9/13 flags, `td_bull/bear_exhaust` (setup ≥ 8, or 9/13 within the last 3 bars), soft scores |

## 2. Baseline and filters
**Baseline: Donchian breakout.** Two entry modes:
- **`close_next_open`** (user modes C and D): close beyond the channel, market entry at the next bar open.
- **`stop_at_channel`** (user modes A and B): stop order at the channel that applies to the next bar, valid for one bar. A touch is a trade-through of the stop. Both sides are placed when both are allowed; ordering bias on bars that touch both sides is disclosed.

**Exits:** stop = 1.0 × ATR14 (at the signal bar) from the fill; target = k × stop with k ∈ {2, 3, 5}; time stop 48 bars. Fixed-pip targets are never used.

**Filters** are evaluated at the signal bar, i.e. decision-time information only:

| Filter | Pass condition |
|---|---|
| SQ | squeeze fired within the last 5 bars |
| VEI | VEI ≥ 1.2 |
| EMA200 | direction agrees with the side of EMA200 |
| MOM | all 4 momentum conditions in the trade direction |
| OFI proxy | ratio in the trade direction ≥ 3.0 (the proposed **300 %**) |
| Quote burst | trailing percentile ≥ 97.5 |
| TD | **veto** LONG on bullish exhaustion, SHORT on bearish exhaustion |

**Variants:**
- **Cumulative stack** L0…L7 in the order sq → vei → ema200 → mom → ofi → quote-burst → td.
- **Single add-ons** A_* on the baseline.
- **Threshold family** (single add-ons): VEI ∈ {1.0, 1.1, 1.2, 1.3, 1.5}; OFI proxy ∈ {1.25, 1.5, 2, 3, 4, 5}; quote-burst percentile ∈ {0.95, 0.975, 0.99, 0.995}.

## 3. Execution and costs (`nexa_execution`, bar mode)
- **Fills:** next-bar fills; latency < 1 bar.
- **Bid/ask:** derived from the recorded spread of the bar's first minute.
- **Ambiguity:** the stop wins on a bar that hits both; gaps fill at the open.
- **Commission:** observed $4/lot/side.
- **Slippage:** 0.5 × spread on market and stop fills.
- **Swap:** spec-probe swaps charged only, never credited; Wednesday counts × 3.
- **Stress:** spread × 2 and × 3 on the selected trials.

## 4. Evaluation design (pre-registered)
- **Periods.** DEV 2018–2022; VAL 2023-01-01 → 2026-09-25 (**seen data**, one query per trial); OOS **prospective** 2026-10-12 → 2027-04-12.
- **Trial universe.** **2,160 trials**: E8_STACK and E8_THRESH, each 2 TF × 2 N × 2 modes × 3 targets × 15 variants × 3 symbols (XAUUSD, EURUSD, GBPUSD). NAS100 is registered as BLOCKED. DSR uses all trials plus the 1,848 earlier NEXA trials on the same data.
- **Information analysis (DEV and VAL).** Per engine, the signal-level net R of filtered vs unfiltered baseline signals. The **random-subset null** draws random baseline subsets of equal size, 2,000 draws. Also: engine-to-engine correlation (redundancy) and mutual information with the win/loss outcome.
- **Selection.** Per (experiment, claim, symbol): the highest VAL one-sided 95 % stationary-bootstrap lower bound with ≥ 30 VAL trades. It is sealed before the prospective OOS start.
- **Capital Velocity.** The selected trade streams are replayed with real broker sizing from $200: 1 % risk, round down, minimum lot, 2 % daily halt, 10-trade cap, +24.5 % daily lock.
