# B3: Practitioner methodologies with complete processes (batch 1, 2026-10-11)

**Purpose:** reconstruct complete strategies from credible practitioners and rate the evidence behind each.
- Primary-source status is stated per item.
- **Pages written by third parties about a trader are SECONDARY**, even if they quote him.

## P1. Fabio Valentini ("Fabervaale"): DeepCharts co-founder (Volumetrica Trading S.r.l., Rovigo; co-founded with **Andrea Cimitan**, very likely the "Andrea Cimi" of SRC-YT-007)

### Independently checked performance (VERIFIED-PERFORMANCE, contest level)

Official Robbins World Cup historical standings (`worldcupchampionships.com/world-cup-trading-championship-historical-standings`, checked 2026-10-11):

| Year | Division | Rank | "Percentage" |
|---|---|---|---|
| 2023 | Quarterly Futures Day Trading Championship Q4 | 2nd | 68.60 |
| 2024 | Quarterly Futures Day Trading Championship Q1 | 3rd | 89.50 |
| 2024 | Quarterly Futures Day Trading Championship Q4 | 2nd | 218.30 |
| 2025 | Quarterly Futures Day Trading Championship Q1 | 3rd | 169.70 |

**Caveats (from the standings page itself):**
- Entrants may trade more than one account, and "accounts do not necessarily represent all the trading accounts" a competitor controls.
- No entrant counts, starting balances (quarterly minimum USD 2,500) or audit method are shown.
- The standings show podium placings only, so losing quarters and other accounts are invisible.
- **Selection effect:** contests reward variance.
- **What this proves:** real-money, real-time results on at least these accounts and quarters. **It does not prove a repeatable edge or any specific rule.**

**Other claims not verified:**
- "500 % in a single year";
- "#1 scalper in the world";
- "three-time champion" (a secondary page itself calls this an overstatement);
- a CME Equity Cup ranking.

### Methodology: SECONDARY sources only

Sources: TradeZella and ChartFanatics strategy pages, attributed to him; the PickMyTrade blog (summarises interviews; mixes in its own script parameters); FuturesHive profile. **No primary Valentini publication was found.** His YouTube interviews ("Trading LIVE with the #1 Scalper in the World", etc.) are queued behind the transcript guard.

**Framework:** three conditions must align, or stay flat:
1. **Market state:** balance vs imbalance (auction market theory).
2. **Location:** an LVN or POC (also VA edges in some summaries).
3. **Aggression:** order flow in the trade direction: "big prints, imbalances, or strong CVD pressure"; "big sell/buy bubbles or footprint imbalance". "No aggression = no trade."

**Instrument and session:** NQ (and ES). Trend model in the New York session; mean-reversion model in London or compressed (summer) conditions. Avoid the London open for trend trades ("fake breakouts").

**Model A: Trend continuation (out of balance → new balance)**

| Element | Rule (secondary) |
|---|---|
| Context | Displacement/momentum away from prior value; skip if price is merely rotating |
| Profile | Volume profile **of the impulse leg** (from the start of the impulse to the extreme) → mark its LVNs |
| Location | Pullback into an LVN of that leg; set alerts, not blind limits |
| Confirmation | Aggression in the trend direction at the LVN (big bubbles / footprint imbalance / CVD) |
| Stop | Just beyond the aggressive print + 1–2 ticks beyond the obvious swing. *(One breakdown says "just below the LVN": inconsistent.)* |
| Management | Move to break-even early if CVD shows strong pressure |
| Target | **Previous balance POC**; full exit; trail only on rare strong trend days |
| Risk | 0.25–0.5 % of account per trade; stop trading after 3 losses in a day (interview summary); minimum 2:1 |

**Model B: Mean reversion (failed breakout → back into balance)**

| Element | Rule (secondary) |
|---|---|
| Context | Market in balance (the previous day's profile = the balance reference); a push out of balance that **fails** |
| Location | Do **not** take the first move back. Wait for a clear reclaim inside balance, then a pullback into the reclaim leg; profile the reclaim leg and mark its LVNs |
| Confirmation | Aggression in the snap-back direction (big buy prints after a downside failure; big sell prints after an upside failure) |
| Stop | Beyond the aggressive print + 1–2 ticks (or beyond the failed extreme); "never widen the stop" |
| Target | **Balance POC**; not the opposite edge unless conditions are exceptional |
| Risk | As Model A |

**Unverified statistics:** "70 % of the time the market stays in balance / reverses from balance"; "1:2.5 to 1:5 reward-to-risk".

**Relation to your notes (NOTE-001):**
- **Same family as Model B:** price below or at value, aggression appears, and a reclaim, so long back into value.
- **Differences:**
  - Your notes target **VAH**; Valentini targets the **POC**.
  - Your bubble is "**for Sellers**" (trapped/absorbed sellers), whereas his trigger is **aggression in the trade direction** (big **buy** prints for a long).
  - These are **two different order-flow readings** of the same location (see the contradiction register).

## P2. James Dalton: *Mind over Markets* (corpus S42) and Value-Area Rule
- **Primary (book).** Value area 70 %; open types; day types; the Value-Area Rule ("a good possibility" to traverse VA after re-entry with double TPO prints; better with a narrow VA and an open near value).
- **Evidence:** the authors' own T-bond 1986–87 statistics for 3-1 and neutral-extreme days; **none for the VA rule**. The "80 %" label is not Dalton's statistic (B1 §1).
- **Complete process:** context (open type, day type, value migration) → location (VA edges, prior extremes) → acceptance/rejection (TPO time) → trade. No order-flow component (pit era).

## P3. Peter Steidlmayer: *Steidlmayer on Markets* (corpus S46)
- Primary (book). Day-structure taxonomy (IB, range extension, OTF participation); 68 % first standard deviation; "after a trend day some 90 % sideways or reverse" (unsourced; NEXA OF-20b could not evaluate it).

## P4. "Trader Dale": *Volume Profile: The Insider's Guide* (S49) and *Order Flow Trading Setups* (S44)
- **Primary (books). All trades hypothetical** (his disclosure).
- **Definitions that became conventions:**
  - **imbalance = diagonal Ask(p) ≥ 300 % × Bid(p−1)**;
  - **stacked = ≥ 3 adjacent**;
  - "unfinished business" (bid ≠ 0 at a bar high);
  - **trades filter ≥ 25 contracts on 6E**.
- **Process:** a volume-profile zone (accumulation cluster, POC of a rotation) → order-flow confirmation (absorption by limit orders, or aggressive orders with delta in the trade direction) → **analyse currency futures, execute spot FX, transfer levels visually** (the inverse quote for JPY/CHF/CAD). This is the closest published analogue to NEXA's situation.
- **Evidence:** none (hypothetical trades; a signal service claims a "70 %" strike rate).

## P5. Axia Futures (SRC-CH-002; YT-006/011–014, in the KB)
- Professional prop training. Profile first (RTH profile), relative initial balance, "behind the elephant" break-and-reclaim, absorption = repeated reloading (ladder), CVD divergence as a warning only.
- No published statistics. NEXA OF-19 rejected their relative-IB rule for spot FX/XAU.

## P6. Vishaal Fx (SRC-YT-001): your notes' source
- Profile + Big Trades bubble at VAL; ORB → IVB; delta profile; stacked-imbalance target.
- **One live trade; no statistics.**

## Cross-practitioner synthesis (to be extended in later batches)

| Element | Consensus | Disagreement |
|---|---|---|
| Order of analysis | Context → location → order-flow trigger (all) | — |
| Location | VA edges, POC, LVN, prior extremes | LVN as a **pullback entry** (Valentini Model A, Andrea Cimi) vs LVN as a **target that is traversed** (your Setup B, auction theory) vs LVN as **support** (your note "market will go up", CL-016) |
| Trigger | Some order-flow event at the location | **Aggression *with* the trade** (Valentini, Trader Dale "aggressive orders", CL-030) vs **absorption of aggression *against* the trade** (your "big trade for Sellers" then reclaim; Axia "behind the elephant"; Andrea CL-024; Trader Dale "limit absorption") |
| Target | Inside value | **POC** (Valentini Model B; Flow Zone CL-006 first target) vs **opposite VA edge** (your notes; Dalton VA rule) |
| Stop | Beyond the order-flow event, a few ticks | Beyond the LVN / failed extreme (secondary inconsistencies) |
| Risk | Small fixed fraction (0.25–0.5 %); daily loss stop | — |
| Evidence | Only Valentini has verified contest placings; none publishes trade-level statistics | — |
