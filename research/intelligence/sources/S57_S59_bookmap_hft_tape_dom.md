# S57–S59: Bookmap & ATAS order-book education material (user upload 2026-10-16)

**Novelty check:** no earlier copy by sha256 and no prior citation. Bookmap was only mentioned generically in the order-flow KB, and "tape and DOM" only in the YT-083 description. All three were read in full.

| # | File (sha256 prefix) | What it is | Pages |
|---|---|---|---|
| S57 | `Bookmap presentation (BMT).pdf` (30d2e6f6) | **Bookmap sales deck**, "See through the markets with Bookmap Xray" | 29 slides |
| S58 | `hft_must_know_info.pdf` (7d8a49df) | "High Frequency Trading", **VeloxPro Ltd (a Bookmap partner) e-book**, ~2015. Mostly summarises Aldridge (2013) and Narang (2009) | 34 |
| S59 | `Tape_and_DOM.pdf` (9ceeb493) | **ATAS e-book**, "Searching for an entry point: the secrets of a tape and DOM", with Bitfinex / BitMEX Bitcoin examples (image PDF, rendered page by page) | 38 |

**Status:** all **VENDOR / PRACTITIONER MARKETING**. There are **no statistics, no samples, no out-of-sample tests and no costs**. The only trade shown (S59 pp. 35–37) is a single hand-picked winning Bitcoin long.

## Useful content (concepts, not edges)

- **S58, order mechanics:**
  - limit-order-book structure;
  - FIFO vs pro-rata matching;
  - aggressive (market) vs passive (limit) orders and the trade-off between paying the spread and the risk of not being filled;
  - iceberg / hidden orders;
  - Level I vs Level II data.
  - **Correction:** S58 says CME is pro-rata. In fact CME equity-index futures (ES / NQ / MNQ) match **FIFO**; pro-rata applies only to certain CME products (e.g. some interest-rate contracts).
- **S58, aggressor classification when the feed has no trade side:**
  - tick rule;
  - quote rule;
  - **Lee–Ready (1991)**;
  - **Bulk Volume Classification (Easley, López de Prado & O'Hara 2012)**.
  - Relevant if NEXA ever builds delta / CVD from QuantConnect L1 tick data, which has no aggressor flag.
- **S58, HFT taxonomy:**
  - statistical arbitrage;
  - directional / event;
  - automated market making;
  - **liquidity detection** (pinging, quote stuffing, **spoofing / layering**, momentum ignition). The book says "ignition" has no reliable evidence (Gregoriou 2015).
- **S57, Bookmap's own claims:**
  - "not an indicator, not a trading system, not a trading educator";
  - the value is visualising resting liquidity being added or pulled, plus aggressor-classified volume;
  - its main selling point: **replay at 16× ("104 hours of screen time per session") to build intuition**. That is a practice tool, not an edge.
- **S59, the ATAS DOM-levels method (discretionary):**
  - big resting limit orders that persist act as support or resistance;
  - short-term levels appear after breakouts;
  - "aggressive orders hit a level and price does not move" means absorption by the opposite side;
  - all major opposite levels broken means one side is in control;
  - two tapes (one filtered for big trades), Cluster Search, footprint;
  - entry on a bounce from a DOM level, stop beyond it.

## NEXA assessment

1. **No testable edge is stated.** These are descriptions of a workflow. Turning "large persistent resting order = support" into a rule would need **historical depth-of-book (Level 2 / MBP) data** for NQ:
   - Databento MBP-10 is metered (paid; the user's rule is $0);
   - QuantConnect provides L1 quotes and trades only.
   - So **under $0 it cannot be tested**.
2. **The method's own failure mode, documented in S58:** large visible resting orders can be **spoofed or layered** (placed to be pulled). Reading displayed liquidity as "support" is exactly what spoofers exploit. S58 Fig. 4.4: "algos entice retail traders with dangling orders".
3. **Consistent with the closed order-flow line** (user decisions E1–E12, 2026-10-11; OFC1 / OFC1R REJECTED; LC-1: intraday edges smaller than the round-trip cost) and with S55 (order-flow persistence is already priced). **No hypothesis registered.**
4. **Practical use for the user** if they later trade manually with ATAS:
   - replay / sim practice;
   - understanding fills (FIFO queue, limit vs market cost);
   - not mistaking a single displayed order for real support.
