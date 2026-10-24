# DEVIATIONS / INTERPRETATIONS — H-IVB1-NQ and H-IM-NQ

**Written 2026-10-14, BEFORE either run.**
- No IVB or IM statistic has been computed on NQ.
- The code, the tests (16/16 passing on synthetic bars only) and this file are hashed into `PREREG_HASHES.txt` before the run.
- Binding pre-registrations: `PREREG_HIVB1_NQ.md` (3ef68268…) and `PREREG_HIM_NQ.md` (1113e2ee…).
- Interpretations (I-n) resolve wording the pre-registration leaves open. Deviations (D-n) change something the pre-registration states.

## H-IVB1-NQ (`hivb1_nq.py`)

| # | Point | Interpretation |
|---|---|---|
| I-1 | Placebo breakout/fill deadline (§5 "shifted equally") | Deadline = min(anchor + 5 h 30 min, 15:00). Early anchors keep the primary's 5.5 h window. The 11:00–14:00 anchors are capped at 15:00, so a placebo trade can never be armed after the primary's own cut-off. The time exit is 15:59 for every anchor. |
| I-2 | The fill bar | On the 1-min bar that fills the limit, only the hard stop and (on a 5-min candle end) the invalidation are checked, **never the target**. The order of prices inside the fill bar is unknown, so the target is not credited on that bar (conservative). |
| I-3 | Exit fills | The target and the entry limit need a 1-tick trade-through and fill at the level, with no improvement. A stop touched intrabar fills at the stop level. If the bar **opens** beyond the stop (a gap), it fills at the open. |
| I-4 | Pre-fill invalidation | If a 5-min candle closes beyond the far VA edge before the limit fills, the setup is cancelled → `no_fill` (§3.4 "no trade"). |
| I-5 | Breakout candle with a missing last bar | The 5-min candle close = the close of its last 1-min bar (minute +4). If that bar is missing, the candle is skipped and the next candle is examined. |
| I-6 | 5-min grid | Candles start at range end (10:00, 10:05, …). Invalidation is checked on the same grid after the fill. |
| I-7 | Day completeness | Any missing 1-min bar inside the range, or a missing 15:59 bar → `missing` (no trade, counted). |
| I-8 | N2 fade | Same retrace touch of the same level (the fill condition uses the breakout direction). The trade goes the opposite way. Stop = entry ∓ R (same R), target = entry ± 2R. There is no VA invalidation, because the far VA edge lies on the fade's profit side. |
| I-9 | Re-entries (robustness only) | The setup re-arms only after a **target** exit, and at most 3 trades per day. Any stop, invalidation or time exit ends the day ("break and reload… 1:2, 1:2"). |
| I-10 | POC-entry robustness | Limit at the POC. R = POC − VAL (long) / VAH − POC (short). Same hard stop, invalidation and cost floor. |
| I-11 | Cost floor | Checked on R before scanning for a fill (R < 10 points → `cost_floor`, counted). |
| I-12 | Volume data | `NQ_v0_ohlcv1m_2023-02-18_2026-10-10_volume.csv.gz` (sha 35d1c3f5…). Written by `nq_volume_convert.py` from the **same frozen DBN** (bf5b20b4…) as the H-ORB-1 canonical CSV: same clock and rows, plus `volume`. 1,289,540 rows, 0 zero-volume rows. |
| I-13 | Days | `horb1_orb.eligible_days` with the frozen calendar. The latest NY date is excluded (it may be incomplete), as in H-ORB-1. |
| I-14 | Sizing figure | Account for 1 % risk at the median R, on 1 MNQ ($2/point). Reported only. |

## H-IM-NQ (`him_nq.py`)

| # | Point | Interpretation |
|---|---|---|
| I-15 | Previous close (§2) | The previous **weekday** must itself be an eligible day. If it is a holiday or early close, the signal is undefined → no trade (§2's second sentence). There is no skipping back past a holiday. |
| I-16 | Bars | Signal = close of bar 15:29. Entry = open of bar 15:30. Exit = close of bar 15:59. A placebo with window end t uses signal bar t−31, entry bar t−30 (open) and exit bar t−1 (close). A missing bar → `missing`. |
| I-17 | Robustness "entry at the 15:30 close" | Entry = close of bar 15:30; same exit. |
| I-18 | bp | Net points ÷ entry price × 10⁴. Year stability uses the bp sums. |
| I-19 | "Strong move" robustness | \|r\| > the median \|r\| of the S1 trades. |
| I-20 | N3 | Unconditional long, 15:30 open → 15:59 close, on the same days. Mean gross points; reported only. |

## Both

| # | Point | Interpretation |
|---|---|---|
| I-21 | DSR | `nexa_robust.deflated_sharpe(primary S1 series, n_trials = 69, var_sr)`. var_sr = the variance of the per-trade Sharpe ratios over this hypothesis's **own** series: IVB 22 (primary, long, short, 19 placebos); IM 24 (primary, Gao, long, short, 20 placebos). This follows each pre-registration's §6. |
| I-22 | One stage | Each results file (`hivb1_results.json`, `him_results.json`) is written once. The script refuses to run if the file already exists. |

| # | Deviation | Why |
|---|---|---|
| D-1 | The tests are one file, `test_hivb1_him.py`, not `test_hivb1.py` + `test_him.py` (§9). | Naming only. It covers every §9 item plus two end-to-end smoke tests of `analyse()` on synthetic random walks. |
