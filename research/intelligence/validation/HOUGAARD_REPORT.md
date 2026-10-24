# H-HOUGAARD results: Tom Hougaard's pre-open range breakout on NQ (binding), ES and YM (2026-10-22)

- **Pre-registration:** `PREREG_HOUGAARD.md` (597c2a5c, approved before any data). Notes: `DEVIATIONS_HOUGAARD.md`.
- **Code:** `qc_hougaard/main.py` 230660be (ES 27afa20d, YM 003df236; MODE line only), frozen after 13/13 synthetic tests. The QC editor hash was verified before each run.
- **Runs:** once each; QC free node; project NEXA/HOUGAARD 38279481; 2010-01-04 → 2026-07-24 (≈ 3–3.5 minutes each).
- **Raw logs** (sha equal to the in-page hash of the QC log): `qc_hougaard/logs_nq_7906f2ba.txt` (f273f431), `logs_es_26a4b172.txt` (ae9b52a3), `logs_ym_54c24b66.txt` (286f1222).

## Verdict: REJECTED on every instrument and variant (binding: NQ variant A)

| Instrument | Variant | Trades | Fill rate | Mean stop | **Net R/trade (S1)** | 95 % CI | Gross R | Win rate | Post-publication net R | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **NQ** | **A (6 vs 9)** | 3,932 | 98 % | 2.8 pts | **−2.16** | [−2.28, −2.02] | −0.91 | 1.9 % | −1.32 | **REJECTED** |
| NQ | B (1:1) | 3,932 | 98 % | 2.8 pts | −2.15 | [−2.28, −2.01] | −0.90 | 2.3 % | −1.31 | REJECTED |
| ES | A | 4,035 | 98 % | 0.9 pts | −1.69 | [−1.74, −1.63] | −0.87 | 4.2 % | −1.23 | REJECTED |
| ES | B | 4,035 | 98 % | 0.9 pts | −1.68 | [−1.74, −1.63] | −0.87 | 5.6 % | −1.22 | REJECTED |
| YM (Dow) | A | 3,869 | 99 % | 7.2 pts | −1.34 | [−1.38, −1.30] | −0.82 | 7.0 % | −1.11 | REJECTED |
| YM (Dow) | B | 3,869 | 99 % | 7.2 pts | −1.33 | [−1.37, −1.29] | −0.81 | 8.7 % | −1.10 | REJECTED |
| YM literal 9 / 6 Dow points (descriptive) | — | 3,869 | — | 9 pts | −0.97 | [−1.01, −0.94] | −0.64 | 21.6 % | — | — |

- The binding rule (FULL mean ≤ 0 ⇒ REJECTED) applies to all six cells. No block, year or window is positive.

## What this result can and cannot say (important)
- **The 1-minute data cannot resolve this bracket.** Hougaard's stop and target are tiny:
  - 0.0257 % / 0.0171 % of price; on NQ about 2–5 points, on ES 0.7–1.5 points (3–6 ticks), on YM 5–11 points;
  - the first minutes after the US open often have a 1-minute range far bigger than that.
- The pre-registered tie rule ("if a candle touches both stop and target, count the stop first, also in the entry candle") is conservative. With brackets smaller than one candle, it turns most trades into stops.
  - Hence the absurdly low win rates (2–9 %) and the gross ≈ −0.8 to −0.9R.
  - **The true win rate is unknown from these data.** The gross numbers are a pessimistic bound, not Hougaard's real gross.
- **Why it still fails, even with perfect data:** costs alone are a large share of the stop.
  - The break-even win rate after costs is (stop + cost) / (stop + target):
    - NQ after 2021: **84 %** (A) / 70 % (B);
    - ES after 2021: 85 % / 71 %;
    - YM after 2021: 77 % / 64 %.
  - Before 2021 the scaled stops were even smaller, so the break-even win rate was above 100 % (unwinnable) on NQ/ES.
  - Hougaard's own 16 sample sessions mixed 6-point wins with 9-point losses. Nothing in them suggests 77–85 % winners at futures costs.
- So: as published, the rule is a micro-scalp whose costs (commission + 1 tick of slippage each way) are too big for its bracket. A tick-data re-test could measure the real win rate, but it cannot make up for the costs. A separate, new pre-registration would be needed, and it is not recommended.

## What this closes
- With H-ORB5, H-ORB30L and H-ORB-1, the opening-range / pre-open breakout family is closed on NQ/ES with free data. No re-tuning (NEXA law L2).
- The user's saved reel IG-01 is answered: Hougaard's free document is honest about slippage, but at futures costs the 9 / 6 bracket cannot pay.

## Multiple testing
6 trials (3 instruments × 2 variants). Ledger ≈ 183.
