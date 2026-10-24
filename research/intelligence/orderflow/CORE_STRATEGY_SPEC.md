# Core strategy: Value Area + Big Trades + Order Flow (v3, FOR YOUR CONFIRMATION)

**Date:** 2026-10-11.

**Status: DRAFT.** Not implemented, not tested, no data collected. Production NEXA, the Risk Engine and MT5 are unchanged.

**Parent:** `ORIGINAL_METHOD_SPEC.md` v2 (concept cards K1–K10, labels, process map).

## 0. Scope decisions (yours, 2026-10-11)

| Item | Decision | Effect |
|---|---|---|
| GEX (K8) | **Excluded** from the core | D29, D30 closed |
| Option Flow (K7) | **Excluded** from the core | D28 closed |
| ORB → IVB (K9, K10) | **Separate strategy**, independent of Big Trades | D19–D24 and D31 deferred to a future ORB spec. D32 (presenter chain) closed: the core = your notes plus the order-flow confirmations you asked to include |
| Core concepts | Volume Profile, VAH/VAL, Big Trades, Order Flow, Delta Profile, absorption, stacked imbalance, LVN, entry confirmation, stop-loss, take-profit | D25 closed: delta, absorption and stacked imbalance are **included** |

## 1. How each item is resolved

- **RESOLVED-NOTE:** your handwriting states it.
- **RESOLVED-SOURCE:** your notes are silent, but a cited source states it, and no source contradicts it.
- **RESOLVED-NEXA:** NEXA's standing research or risk convention (applies to any test; it is not part of your method).
- **ESSENTIAL DECISION Ex:** sources are silent, ambiguous or contradictory, so it needs your confirmation.

| Former # | Topic | Resolution | Basis |
|---|---|---|---|
| D2 | Value-area % | **70 %** | RESOLVED-SOURCE: DeepCharts (the platform in your source video) uses 70 % in its documentation example; consistent with S42/S45 and NEXA EQ-014. (68 % is NinjaTrader's default, not your platform's) |
| D3 | Context "balancing (ʌʌʌ)" | **Price trading inside the value area (between VAL and VAH) before the setup** | RESOLVED-NOTE (page 1 diagram: "The middle part where the market runs ʌʌʌ"). No rotation count exists in any source, so none is added |
| D6 | "Move above / break the bubble" | **A candle CLOSE beyond the bubble** (not a touch) | RESOLVED-SOURCE: CL-023 (close beyond the absorbed aggressors, "inversion"); CL-024 ("no candle closing below" the sellers' cluster); CL-040/042 (close-based breakout trigger; fill at the trigger candle close); CL-007 (wait for a reaction, do not act blindly). No source supports a touch |
| D11 | Trigger timeframe | **1-minute candles** | RESOLVED-SOURCE: presenter switched to 1-min "for more confirmation" (YT-001 10:36–10:50) |
| D9 | Checklist gating | **All five questions must be answered positively** (sequential) | RESOLVED-NOTE: the checklist ends "⑤ Do I have a valid trade idea?", and every source orders context → location → response → order flow (CL-001, K-11). A score or judgement mode appears in no source |
| D10 | Bubble side (Setup A) | **Seller-aggressor bubble** (DeepCharts Bid colour) | RESOLVED-NOTE: "Big trade for Sellers"; DOC: Bid colour = aggressive sellers |
| D13 | Setup A target | **VAH** | RESOLVED-NOTE: "Take Profit → at VAH" |
| D12 (part) | Setup A stop reference | **Below the bubble** (its lowest execution price). The notes add "and also around VAL" because the bubble sits near VAL | RESOLVED-NOTE + RESOLVED-SOURCE (CL-023: stop beyond the absorbed orders). The buffer size remains E6 |
| D16 | Setup B trigger | **A 1-min close below BOTH the bubble and VAL** | RESOLVED-NOTE ("breaks the bubble and break the VAL") + D6/D11 above |
| D5 (part) | Setup B target | **The LVN below VAL; the nearest one** | RESOLVED-NOTE ("TP at below VAL … at below got LVN", singular, reached first going down). The detection rule remains E9 |
| — | Absorption confirmation (Setup A) | **After the seller bubble prints, no 1-min candle closes below the bubble before the trigger** | RESOLVED-SOURCE: CL-024 (Andrea Cimi, DeepCharts team: "sellers clustering … no candle closing below = sign of passive buyers"); consistent with CL-021 (Axia "behind the elephant": selling exhausts, price returns through the level) and CL-023. Note: a close below the bubble **and** VAL is exactly Setup B's trigger, so the two setups are mutually exclusive by construction |
| — | Entry price | **At the close of the 1-min trigger candle** | RESOLVED-SOURCE: CL-042 ("fill occurs at the breakout candle close, not at the level") |
| D25 | Delta, absorption, stacked imbalance | **Included** as order-flow confirmation (your instruction). Roles and definitions are E4 and E5 | — |
| D8 | Cost / minimum-R rule | **For testing only:** a setup is skipped *ex ante* if round-trip cost > 20 % of the stop distance. Results are net of NEXA's measured costs | RESOLVED-NEXA (COMMON §C7). Not your rule. Your notes have no R:R minimum, and none is added |
| D14 (part) | Invalidation | **The stop.** In Setup A, a 1-min close below the bubble and VAL also invalidates the long (it is Setup B's trigger) | RESOLVED-NOTE (page 3 "If market breaks the bubble and break the VAL" switches the idea). A time limit remains E11 |
| Risk | Sizing, daily limits, caps | **NEXA's frozen controls**: 1 % risk to the stop; 2 % daily pre-trade budget; exposure/correlation caps; mandatory stop; news veto. **Scaling in is excluded** (it conflicts with fixed-risk sizing; not in your notes) | RESOLVED-NEXA |

## 2. The core strategy as resolved (remaining gaps marked Ex)

### Context and levels (every session)

1. Build the **volume profile of the prior completed session** (session = **E1**).
2. Compute **POC, VAL, VAH** at 70 %, and the **LVNs** (detection rule = **E9**).

### Setup A: LONG ("big trade for sellers" absorbed near VAL)

| Step | Rule | Basis |
|---|---|---|
| ① Context | Price is trading inside the prior value area | NOTE |
| ② Location | Price has moved down toward VAL. A **seller-aggressor big trade** (size threshold and input mode = **E3**) prints **near VAL** (tolerance = **E2**) | NOTE + DOC |
| ③ Price response / absorption | After the bubble, **no 1-min close below the bubble** | CL-024 (+ CL-021/023) |
| ④ Order-flow confirmation | On the trigger candle: **buy-side imbalance** (definition = **E4**) and **delta/volume confirmation** (definition = **E5**) | CL-023 ("plus an imbalance in the new direction"), CL-024 ("buyers take control with imbalance and volume"), YT-001 6:50 ("P and Delta and big confirmations") |
| ⑤ Trigger and entry | A **1-min candle closes above the bubble** (its highest execution price) → enter at that close | NOTE + CL-023/042 + YT-001 10:36 |
| Stop-loss | **Below the bubble's lowest price** − buffer (**E6**) | NOTE + CL-023 |
| Take-profit | **VAH** | NOTE |
| Invalidation | Stop hit; or before entry, a 1-min close below the bubble **and** VAL (→ Setup B); time limit (**E11**) | NOTE |

### Setup B: SHORT (bubble and VAL broken)

| Step | Rule | Basis |
|---|---|---|
| ①–② | As Setup A (inside value, seller bubble near VAL) | NOTE |
| ③ Price response | **A 1-min close below both the bubble and VAL** → enter at that close | NOTE + D6/D11 resolution |
| ④ Order-flow confirmation | Whether E4/E5 apply mirrored (sell-side imbalance, negative delta) = **E5b** | CL-030 (DOC blog: large sellers below support support continuation) |
| Stop-loss | "**at the top**": meaning = **E7** | NOTE |
| Take-profit | **The nearest LVN below VAL** (detection = **E9**) | NOTE |
| At the LVN | "once reach LVN, market will go up": exit only, or also a new long = **E8** | NOTE |
| Time limit | **E11** | — |

### Mirror setups (near VAH)
**Not in your notes = E10.** Testing only one side would be a selection bias, so it needs your explicit choice.

## 3. Remaining ESSENTIAL decisions (only what no note or source settles)

| # | Decision | Why it can't be resolved from sources | Source-backed options |
|---|---|---|---|
| **E1** | **Which session's profile defines value** for FX/gold | **DECIDED (user, 2026-10-11): prior NY block, 08:30–17:00 NY** (A2 anchor to CME close). It holds 58 % of 6E volume (CL-114) and is the analogue of the sources' prior RTH session | **Resolved.** The full-day and London alternatives are rejected for the core |
| **E2** | **"Near VAL" tolerance** for the bubble | **DECIDED (user, 2026-10-11): within 10 % of the prior NY value-area width** of VAL (mirrors: VAH); ≈ 2 pips at the median width (CL-115) | **Resolved** |
| **E3** | **Big-trade threshold and input** per instrument | **DECIDED (user, 2026-10-11).**<br>- **Unit:** aggressor order (6E trades aggregated by timestamp + side; CL-104).<br>- **Big** = size ≥ ceil(**99th percentile**) of that **session block's** orders over the **prior 60 sessions** (no look-ahead).<br>- **Blocks** reuse the frozen OF anchors A1/A2: Asia 18:00 NY–08:00 London · London 08:00 London–08:30 NY · NY 08:30–17:00 NY.<br>- Code: `databento/big_trades.py`. Behaviour: `big_trades_definition.json` (CL-111) | **Resolved.** Needs 60 sessions of warm-up history before first use. Other instruments (6J/6B/GC) use the same rule on their own data |
| **E4** | **Imbalance / stacked imbalance definition and role** | **DECIDED (user, 2026-10-11): diagonal comparison, ratio 300 %, minimum 10 contracts on the dominant (aggressor) level and > 0 on the compared level, ≥ 3 consecutive imbalanced tick levels on the trigger candle, role = entry confirmation only** | **Resolved** |
| **E5** | **Delta / volume confirmation on the trigger candle** | **DECIDED (user, 2026-10-11): 1-min trigger-candle delta in the trade direction AND volume > the mean volume of the same minute-of-day over the prior 20 sessions** | **Resolved** |
| **E5b** | Do the order-flow confirmations apply to Setup B (mirrored)? | Notes give Setup B no order-flow condition | yes (mirrored) · no (price trigger only) |
| **E6** | **Stop buffer** below the bubble | **DECIDED (user, 2026-10-11, re-asked after the venue choice): 1 tick** beyond the bubble's extreme, on CME prices (6E 0.5 pip; the same rule in ticks for 6J/6B/GC) | **Resolved** |
| **E7** | **Setup B "SL at the top"** | **DECIDED (user, 2026-10-11): bubble high** (+ the E6 buffer). Mirror: bubble low − buffer | **Resolved** |
| **E8** | **At the LVN** | **DECIDED (user, 2026-10-11): exit only** (no new long at the LVN) | **Resolved** |
| **E9** | **LVN detection rule** | **DECIDED (user, 2026-10-11): no smoothing (1-pip rows); a local minimum whose volume ≤ 50 % of the lower of the highest rows on each side.** On 6E: median 3 LVNs per profile; an LVN below VAL in 41 % of sessions (CL-115). **If Setup B (or its mirror) has no LVN beyond the edge → no trade** | **Resolved** |
| **E10** | **Mirror setups near VAH** | **DECIDED (user, 2026-10-11): INCLUDE.** Buyer big trade near VAH → short to VAL; break above VAH → long to the LVN above. Mirrors use the same rules reflected | **Resolved** |
| **E11** | **Time limit / session end** | **DECIDED (user, 2026-10-11): flat at the end of the NY block (17:00 NY)**; no overnight holding | **Resolved** |
| **E12** | **Instruments** | **DECIDED (user, 2026-10-11): all four, 6E, 6J, 6B, GC.** 6E on hand; 6J/6B/GC need purchases (quote + confirmation each) | **Resolved** (data pending) |

## 4. Data reality for the core (unchanged; no collection now)

| Element | Data required | NEXA today |
|---|---|---|
| Profile, VAH/VAL, POC, LVN | Traded volume at price | **Proxy**: tick volume (validated XAU/EUR/JPY; not GBP). **True**: CME futures (Massive 1-min, 2 y, not cached; collection needs approval) |
| **Big Trades, delta, imbalance, stacked imbalance, absorption** | **CME trades with aggressor side and size** (per-price bid/ask) | **None.** Candidate: DataBento `GLBX.MDP3` trades (aggressor side confirmed). **Purchase/credits need your approval** |
| Absorption via the passive book (CL-020 "reloading") | MBO | Not reproducible (no historical MBO exists) |
| Execution realism | Real fills | None (S14 forward test down) |

**Consequences:**
1. **Without aggressor-side trades, Setups A and B cannot be tested as written.** Steps ②, ③ and ④ all depend on them.
2. A volume-only version would be **OF-03P** (proxy). It is never reported as this strategy (v2 Part V).
3. Futures → spot mapping: the T1 basis map passed for EUR/GBP/JPY but **failed for XAU**. For gold, the setup would be evaluated in futures prices (GC), or the spot-mapped levels would carry a known error.

## 5. After your confirmation (no action taken yet)

1. You answer **E1–E12**.
2. I freeze them into a pre-registration **OF-03-ORIG** (Setups A/B; mirrors per E10), hashed before any data is opened.
3. **Data step (needs approval):** the CME aggressor-side trade source and history length.
4. The test design (as for OF-16/19/20, C1/C2):
   - driftless-barrier null for the VAL→VAH bracket;
   - placebo bubbles (same size, random location in value) and placebo levels;
   - NEXA costs; holdout opened once.


**Execution venue: DECIDED (user, 2026-10-11).** Evaluate on **CME futures prices** (research test of the method), not mapped to Pepperstone. Consequence: the E6 rationale (transfer error) no longer applies, so E6 is re-asked; a CME cost model (commission + slippage) is needed.

**Trading window: DECIDED (user, 2026-10-11).** Setups may trigger from the CME open (18:00 NY) after the prior NY profile completes, until 17:00 NY. Flat at 17:00 NY (E11).

**CME cost model: DECIDED (user, 2026-10-11).**
- **Per side:** exchange fee USD 1.60 (6E/6J/6B) or 1.65 (GC) + NFA USD 0.01 + an assumed broker commission of USD 1.00.
- **Source:** TradeStation's exchange-fee pass-through list, checked 2026-10-11.
- **Slippage:** 1 tick on entries (1-min close) and on stop exits. Targets fill at the target price only if the price trades through it.

**All E1–E12 decisions are resolved as of 2026-10-11.** Next: pre-registration (needs user approval).

**E5b: DECIDED (user, 2026-10-11): yes, mirrored.** The Setup B break candle (and its mirror) needs ≥ 3 stacked imbalances against the trade's opposite side, delta in the trade direction and volume above the same-minute baseline.

**Bubble multiplicity: DECIDED (user, 2026-10-11): the most recent qualifying big trade** replaces a pending one.

**Trades per day: DECIDED (user, 2026-10-11): one open position per instrument at a time; re-entry allowed after exit.**
