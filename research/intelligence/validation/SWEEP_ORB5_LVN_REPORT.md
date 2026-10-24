# Results: H-SWEEP, H-ORB5, H-LVN-SPEED (2026-10-21)

- **Pre-registrations:** `PREREG_SWEEP.md`, `PREREG_ORB5.md`, `PREREG_LVN_SPEED.md` (commit da6dd7e, before any data).
- **Code:** frozen after 24/24 synthetic tests (commit 47ad59c): `qc_sweep/main.py` bb1ac624, `qc_orb5/main.py` bb219a99, `qc_lvn/main.py` 8e50dfbb; ES files differ only in MODE (ebd458ee, f84f7397, 2f6874f9).
- **Runs:** once each, QuantConnect free node, via the website with the user's login (deviations D-1…D-3 in `DEVIATIONS_SWEEP_ORB5_LVN.md`). Before every run, the sha256 of the file on QuantConnect's server was computed in the page and matched the frozen hash.
- **Data:** QC continuous futures, minute bars, 2010-01-04 → 2026-07-23 (the last day QC had). Roll days (64) and incomplete days excluded.
- **Raw outputs** (fingerprint-checked copies of the log JSON): `qc_sweep/sweep_{nq_results,es_raw}.json`, `qc_orb5/orb5_{nq,es}_raw.json`, `qc_lvn/lvn_{nq,es}_raw.json`, each with a `.source.txt` naming the backtest id.

## Verdicts

| Test | Instrument | Trades | Mean net R (S1) | 95 % CI | Gross R | Cost per trade (S1) | Blocks > 0 | Placebo pct | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| H-SWEEP Arm A (continuation, Osler) | NQ | 2,117 | **−0.223** | [−0.290, −0.156] | +0.052 | 0.276 | 1/4 | 0.90 | **REJECTED** |
| H-SWEEP Arm B (reclaim fade, video claim) | NQ | 1,667 | **−0.386** | [−0.469, −0.301] | +0.050 | 0.436 | 0/4 | 1.00 | **REJECTED** |
| H-SWEEP Arm A | ES | 1,978 | **−0.152** | [−0.209, −0.089] | +0.091 | 0.243 | 0/4 | 0.95 | **REJECTED** |
| H-SWEEP Arm B | ES | 1,388 | **−0.314** | [−0.389, −0.244] | −0.057 | 0.256 | 0/4 | 0.40 | **REJECTED** |
| H-ORB5 (5-min ORB), primary set P | NQ | 2,170 | **−0.201** | [−0.314, −0.086] | +0.070 | 0.270 | 1/4 | 1.00* | **REJECTED** |
| H-ORB5, primary set P | ES | 2,100 | **−0.178** | [−0.293, −0.066] | +0.035 | 0.212 | 0/4 | 0.85* | **REJECTED** |

- **Gross R** = the edge before any cost: S0 mean + S0 cost × mean(1/R), with mean(1/R) recovered exactly from the S0/S1 gap. **Cost per trade** = the S1 round trip (NQ 2 points, ES 0.6 points) as a share of each trade's risk, averaged.
- **Five of the six streams are slightly positive before costs (+0.035 to +0.091R), and costs of 0.21–0.44R per trade turn every one negative.** The stops these rules use are small (median a few ES points), so a fixed round-trip cost is a large share of R. This is the ledger's most common failure: a real effect smaller than the cost of trading it.
- **No test reaches the +0.025R prop threshold** (H-PROP-EV) on its primary set.
- DSR is not meaningful: every primary mean is negative with its CI below 0.

**Break-even round-trip cost** (gross R ÷ mean(1/R); above this the rule loses):

| Stream | Break-even cost | In ticks | E-mini $ |
|---|---|---|---|
| SWEEP A NQ | 0.38 pt | 1.5 ticks | $8 per contract |
| SWEEP B NQ | 0.23 pt | 0.9 ticks | $5 per contract |
| SWEEP A ES | 0.22 pt | 0.9 ticks | $11 per contract |
| ORB5 P NQ | 0.52 pt | 2.1 ticks | $10 per contract |
| ORB5 P ES | 0.10 pt | 0.4 ticks | $5 per contract |

- A realistic retail round trip is commission ≈ $4–5 on an E-mini plus at least 1 tick of slippage each side on stop exits: about 0.6–0.8 NQ points ($12–16) or 0.6 ES points ($30). **Every stream's break-even is below that** (ES ones are below 1 tick), so the verdicts do not depend on the cautious S1 assumption. The S0 means (NQ 1 point, ES 0.3 point) are also all negative.

## H-SWEEP (stop runs at the prior-day high/low)
- **Both directions lose on both instruments after costs.** Before costs, three of the four streams are +0.05 to +0.09R (ES Arm B is −0.06R).
  - **Fading the sweep (the "manipulation" story) is the worse arm** everywhere (NQ −0.39R, ES −0.31R).
  - Continuation is closer to zero gross. On NQ it beat 18 of 20 distance-matched fake levels; on ES 19 of 20. So the real prior-day level is slightly special (consistent with Osler's stop clusters), but far too weakly to pay a 2R bracket after costs.
- Hit rates: Arm A 34.6 % (NQ) / 36.0 % (ES) vs 33.3 % for a random walk; Arm B 34.2 % / 30.8 %.
- **Post-hoc observation, not a candidate (NEXA law L2):** NQ Arm A was positive in 2023–2026 (+0.103R, 466 trades). ES Arm A in the same years is −0.052R. A new hypothesis would need its own pre-registration and unseen data.

## H-ORB5 (Zarattini & Aziz 5-minute opening range breakout)

| Set | NQ trades | NQ net R | ES trades | ES net R |
|---|---|---|---|---|
| **P = outside the paper's window (primary)** | 2,170 | **−0.201** | 2,100 | **−0.178** |
| PRE 2010–2015 | 1,342 | −0.365 | 1,279 | −0.240 |
| IN 2016-01 → 2023-02-17 (paper's window) | 1,723 | +0.035 [−0.07, +0.15] | 1,662 | −0.051 |
| POST 2023-03 → 2026-07 | 828 | +0.065 [−0.06, +0.20] | 821 | −0.081 |

- On NQ the paper's own window and the post-paper years are slightly positive and match the independent replications (ripbacktest NQ 2020–26 +0.079R). **Neither is distinguishable from zero**, and 2010–2015 is clearly negative. On ES no period is positive.
- Shape: 22 % winners on NQ (19 % ES), 2 % of trades reach 10R, losing streaks up to 34 (NQ) and 46 (ES) trades.
- **Placebo caveat (*, found when reading the result):** the random-direction placebo is biased against itself. A trade against the first candle's direction usually has its stop very close (the candle closed near that extreme), so costs are a much larger share of R. The NQ placebo mean (−0.44R) is therefore not a fair "zero information" baseline, and "beats 100 % of placebos" partly reflects that mechanics. A fair control would size the random trade's stop to the real trade's R. **This changes nothing in the verdict** (the primary mean is negative on its own), but the placebo percentile must not be read as evidence that the first candle predicts direction.

## H-LVN-SPEED (do prices move faster through low-volume zones?)

| Instrument | S = speed thin ÷ thick | 95 % CI | Mirror placebo S | D = S − mirror (CI) | Blocks > 1 | Verdict |
|---|---|---|---|---|---|---|
| NQ | **1.019** | [0.994, 1.043] | 0.974 | +0.045 [+0.010, +0.079] | 3/4 | **INCONCLUSIVE** |
| ES | **1.035** | [1.014, 1.056] | 0.999 | +0.036 [+0.004, +0.069] | 4/4 | **INCONCLUSIVE** |

- NQ: price moves about **2 % faster** in yesterday's thinnest 20 % of price bins than in the thickest 20 %. The location matters a little (the mirrored profile gives 0.97, and D's CI is above 0), but the pre-registered bar was ≥ 10 % (S ≥ 1.10) and the CI of S includes 1. - ES: **3.5 % faster**, every block above 1 and the CI of S above 1, so on ES the effect is statistically real; it fails only the pre-registered size bar (S ≥ 1.10).
- Reading: thin zones of yesterday's profile carry a small, location-specific speed-up (2–4 %), stronger after 10:30 than in the first hour. As a trading idea, "volume vacuums make price shoot through" is **not supported at any useful size**: a 3.5 % faster move does not pay a round trip. It may be kept only as a descriptive context feature.

## What this means for NEXA
- Two more ideas from the user's "institutional pattern" list (idea 1 ORB, idea 5 stop runs) are **REJECTED on 16 years of CME data, on both NQ and ES**; idea 2's "volume vacuum" speed effect is real but tiny.
- The same pattern as the rest of the ledger: effects that are visible in charts and videos are either absent or a fraction of the round-trip cost.
- Ledger: +6 trading-rule trials (H-SWEEP ×4, H-ORB5 ×2) → ≈ 169; +2 descriptive (H-LVN).
- H-ICE-FEAS (iceberg feasibility on the recorder tape) is pre-registered and frozen; it runs once 10 qualifying sessions exist (≈ 2026-11-04).

- The three QuantConnect projects are left with MODE = 'ES' (the last runs). Each backtest on QuantConnect keeps its own code snapshot.
