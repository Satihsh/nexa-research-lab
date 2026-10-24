# Decision brief: the open items of the core strategy (2026-10-11)

**Purpose:** E3 (Big Trades) is resolved. Eleven decisions remain (E1, E2, E4–E12) before the core Setup A / Setup B can be pre-registered and tested on true 6E data.

- Each item below shows what the sources and NEXA's own measurements say, and the options.
- **Nothing here is decided until you choose.** No option is a recommendation of profitability; none has been tested.
- References: claims (CL-) in `kb/CLAIMS.md`; setups in `CORE_STRATEGY_SPEC.md` §2.

| # | Decision | Evidence | Options |
|---|---|---|---|
| **E1** | Which session's profile defines value (FX has no cash session) | Sources: "prior RTH/cash session" (CL-002/005/006). **6E: NY block holds 58 % of volume, London 27 %, Asia 14 % (CL-114).** The OF tests used the prior full server day | (a) prior full day 17:00–17:00 NY · (b) prior NY block 08:30–17:00 NY (the "cash-like" session) · (c) prior London block |
| **E2** | "Near VAL" tolerance for the bubble | No source gives a number (diagram only). Scale: median VA width 27 pips (CL-109); 6E tick 0.5 pip | (a) fixed pips · (b) a fraction of the VA width · (c) inside the lowest part of value (e.g. bottom X % of the VA) · (d) your value |
| **E4** | Imbalance / stacked imbalance | **All platforms compare diagonally (CL-112).** Ratio defaults 150–300 %; ATAS Learn: 200 % = imbalance, 400 % = strong; Trader Dale 300 %. Stack ≥ 3 levels is the common default. Role: entry confirmation (CL-023/024) vs "super target" (ambiguous) | Ratio: 150 / 200 / **300** % · stack: 1 or ≥ 3 · min volume per level: none or a filter · role: confirmation only / target only / both |
| **E5** | Delta / volume on the trigger candle | Named but not quantified (YT-001, CL-024) | (a) trigger-candle delta > 0 · (b) delta > 0 **and** volume above its recent average · (c) nothing beyond E4 |
| **E6** | Stop buffer below the bubble | None in any source. Practitioners: "1–2 ticks beyond the print" (B3). **Transfer error to Pepperstone with yesterday's basis: p95 2.2 pips (CL-108)** | (a) 1 tick (0.5 pip) on futures prices · (b) fixed pips on spot · (c) buffer ≥ transfer error (≈ 2 pips) if executed on Pepperstone |
| **E7** | Setup B "SL at the top" | Ambiguous in the notes | bubble high · VAL · VAH · session high |
| **E8** | At the LVN (Setup B target) | Notes: "market will go up" | exit only · exit + a new long (would need its own rules) |
| **E9** | LVN detection rule | **No standard (CL-113)**; DeepCharts (your platform) does not publish its rule | (a) local minimum lower than N rows on each side (N = 1, 2, 3) · (b) smoothed profile + minimum depth vs neighbouring peaks · (c) your visual criterion in words |
| **E10** | Mirror setups near VAH | Not in your notes. Testing one side only is a selection choice | include · exclude |
| **E11** | Time limit | No source | none (stop/target only) · flat at session end · flat after N minutes |
| **E12** | Instruments | **6E on hand** (13 months). 6J ≈ USD 9.4/yr, 6B 5.1, GC 36.5 (CL-107; B5) | 6E only first · 6E + 6J + 6B · all four incl. GC |

**Execution venue** (master doc §5) is a separate project decision:
- **(a)** evaluate on CME prices only, a research question;
- **(b)** signals on CME, execution on Pepperstone. This must absorb the transfer error (CL-108) and the proxy is not a substitute (CL-109).

## Decisions taken (2026-10-11)
- **E1:** prior NY block, 08:30–17:00 NY.
- **E4:** diagonal comparison, 300 %. Stack count, minimum volume and role are still open.
- **E9:** smoothed profile + minimum depth. Smoothing and depth are still open.
- **E10:** include mirrors.
- **E2:** a fraction of the VA width (fraction still open).
- **E5:** delta in the trade direction + volume above its recent average (window still open).
- **E6:** buffer ≥ the transfer error, ≈ 2 pips. Exact value still open; implies Pepperstone execution.
- **E7:** bubble high.
- **E8:** exit only.
- **E11:** flat at 17:00 NY.
- **E12:** 6E, 6J, 6B and GC. Purchases are pending quotes and confirmation.
- **Venue:** evaluate on CME prices. E6 is re-asked; a CME cost model is needed.
- **E6 (re-asked):** 1 tick.
- **E4:** ≥ 3 stacked, confirmation only.
- **E2:** 10 % of the VA width.
- **E9:** no smoothing, depth ≤ 50 %; no LVN beyond the edge → no trade.
- **E5:** same minute-of-day, prior 20 sessions.

**Still open:** E4 minimum volume per level · trading window (when setups may trigger) · CME cost model.
- **Window:** whole next day.
- **E4 minimum volume:** 10.
- **Costs:** USD 2.61 per side (1.66 for GC + broker); slippage 1 tick on entries and stops.
- **All decisions are closed.**
