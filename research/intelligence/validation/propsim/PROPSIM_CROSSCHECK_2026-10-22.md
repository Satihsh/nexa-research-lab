# Cross-check of H-PROP-EV-TS with LuxAlgo prop-firm-sim (2026-10-22)

- **Tool:** `@luxalgo/prop-firm-sim-cli` 1.2.0 + `-core` 1.3.0 (MIT). Installed with the user's approval 2026-10-22 ("Proceed for LuxAlgo prop-firm-sim") into `tools/prop_firm_sim/`: pinned versions, `npm install --ignore-scripts`, 4 packages (+ commander, zod); `node_modules` is git-ignored.
- **Why a hand-written ruleset:** Topstep and Take Profit Trader are **not** in LuxAlgo's live directory, which lists 9 futures firms: Apex, Blue Guardian, Darwinex Zero, MFFU, The Trading Pit, Top One, TradeDay, Tradeify, Traders Launch. So `topstep_50k_standard_spec.json` was written by hand from `TOPSTEP_COMBINE_RULES_2026-10-18.md`:
  - $3,000 target, 55 % consistency, ≥ 2 days, 250-day cap;
  - $2,000 MLL trailing on EOD balance, locking at the start;
  - fees $49/month + $149 activation;
  - XFA: 90 % split, 5 winning days ≥ $150, 50 % of profit, cap $2,000.
- **Run (same cell as NEXA's "what a real edge buys" table):** $250 fixed risk, ±1R trades, 2 trades/day, win rate = (1 + μ)/2, one Combine per attempt (`--attempt-cap 1`), 250-day funded horizon, 10,000 paths, seed 20261018. Raw output: `ts_p*.json`.

## Result
| Net edge μ | LuxAlgo P(pass) | NEXA P(pass) | LuxAlgo P(≥ 1 payout) | NEXA | LuxAlgo cash / Combine | NEXA | LuxAlgo net / Combine | NEXA |
|---|---|---|---|---|---|---|---|---|
| 0 | 26 % | 26 % | 16 % | 16 % | $230 | $135 | +$98 | +$2 |
| +0.025R | 35 % | 35 % | 23 % | 23 % | $412 | $251 | +$263 | +$101 |
| +0.05R | 45 % | 45 % | 32 % | 33 % | $721 | $408 | +$556 | +$243 |
| +0.10R | 64 % | 63 % | 52 % | 54 % | $1,972 | $1,128 | +$1,781 | +$935 |
| +0.15R | 78 % | 79 % | 70 % | 71 % | $4,745 | $2,790 | +$4,538 | +$2,580 |

## Reading
- **The Combine stage is confirmed.** Two independent engines agree on pass probability and on the chance of at least one payout within 1–2 percentage points at every edge level.
- **Funded cash differs (LuxAlgo ≈ 1.7× NEXA).**
  - Likely cause: Topstep sets the XFA loss floor to **$0 after the first payout**. NEXA models this; LuxAlgo's spec format cannot express it, because its floors "carry across payouts" with a fixed lock offset. So its funded accounts survive longer.
  - NEXA's figure is the one that follows Topstep's written rule, and it is the more conservative one.
  - This explanation was not tested separately.
- **Conclusions unchanged:**
  - with no edge, a Topstep Combine is roughly break-even at sensible sizing;
  - the useful target stays ≈ +0.10R net per trade, where more than half of Combines pay out;
  - NEXA still has no strategy with a proven positive edge, so the $0 rule stands.

## Not modelled by either engine
Scaling plan (does not bind at $250 risk), $30 wire fee, Back2Funded, the DLL option, streaks (both runs use i.i.d. trades; LuxAlgo can block-bootstrap a real trade list once one exists).
