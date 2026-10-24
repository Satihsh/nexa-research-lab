# Prop-firm fit for the user's goal (2026-10-21, official pages only)

Goal (memory): CME futures MNQ/NQ/ES, ATAS + NEXA Monitor on screen, manual clicks (no bots), Malaysia, NY-open evening, $0 until an edge is proven.

| Firm | Malaysia | ATAS in funded stage | Manual-only rule | Funded drawdown | Verdict |
|---|---|---|---|---|---|
| Topstep | allowed (10-18 check) | **No**: ATAS licence covers the Combine only; funded = TopstepX | yes | EOD trailing (Topstep rules 10-18) | Misaligned (NEXA Monitor not usable when funded) |
| Take Profit Trader | **allowed** (help centre 08-25) | **Yes** (Rithmic; own ATAS licence) | "No bots or algos" | **Intraday trailing on peak incl. unrealized** (PRO, 10-20) | Fits; strict funded drawdown |
| Apex (EOD account) | **allowed** (restricted list 09-10) | **Yes** (official ATAS/Rithmic guide) | bans automated trading (memory 10-13/10-18) | **EOD**: threshold set at the close, enforced intraday incl. unrealized; tier DLL pauses the session (PA page 04-28) | Fits; gentlest funded drawdown of the three |
| Tradeify | **RESTRICTED** (official list, 65 countries) | **No**: ATAS not on its platform list; L2 only via Tradovate, Rithmic = Level 1 only | — | — | Not possible |
| MyFundedFutures | **RESTRICTED** (Malaysia on the official list) | — | — | — | Not possible |

Not yet verified: Apex prices and payout-eligibility rules (incl. its risk/reward and "disproportionate risk" rules noted 10-18), other firms (Lucid, Tradeify, Bulenox, Alpha Futures).
Google AI Mode errors confirmed: MFFU "Malaysia fully supported" (false); TPT "10 PRO accounts" (false, 5 active).

## User's core goal (stated 2026-10-21) vs official rules
| Goal element | Reality (official pages / NEXA evidence) |
|---|---|
| Claude + ATAS X Ultra/MBO + prop firm in one pipeline | Possible only at firms with ATAS on Rithmic in the funded stage: Apex, TPT. MBO is not documented by either (TPT: Level 2 free for one exchange). |
| Claude writes C# indicators / API / MCP | Indicators and read-only tools: yes (NEXA Monitor). Anything that places orders: banned (TPT UTP #1, Apex automation ban). |
| Unfiltered CME L2/MBO into ATAS | Depends on the firm's Rithmic data package; to be confirmed with the firm before buying. Value unproven: H-ICE-FEAS pending (~11-04). |
| Claude alerts, user clicks; "millisecond fast" | Manual clicking is allowed. Human reaction is ~150–300 ms and Malaysia→Chicago network round trip is ~200 ms+, so a strategy that needs millisecond speed is not achievable manually; it must not depend on speed. |
| $400–600/day/account, 5–10 accounts via copier = $4–6k/day | TPT: max 5 active funded accounts, approved copiers between own accounts only. A copier copies losses too: one bad day hits every account together. No tested intraday rule in NEXA (~169 tests) is positive after costs. |

- 2026-10-21 later: Apex details in `APEX_OFFICIAL_RULES_2026-10-21.md` (20 PA accounts, 100 % split, payout caps $1,500→$3,000, L2 $10–30, MBO not documented).
