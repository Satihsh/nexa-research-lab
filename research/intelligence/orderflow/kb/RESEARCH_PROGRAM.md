# ORDER-FLOW METHODOLOGY RESEARCH PROGRAMME (persistent backlog and coverage tracker)

**Started:** 2026-10-11.

**Mandate (user, 2026-10-11):** build a deep, evidence-based understanding of the 12 concepts before any implementation:
- Order Flow, Option Flow, VAH, VAL, Delta Profile, Big Trades, Volume Profile, GEX, ORB, IVB, LVN, Value Area.

Research each concept individually and then how they interact. Reconstruct complete strategies (12 process elements each). Keep contradictions as alternatives. Connect to NEXA.

**Final deliverable:** `../NEXA_ORDERFLOW_METHODOLOGY_MASTER.md`.

**Evidence classes** (README, extended):
- **VERIFIED-DOC** (technical definition);
- **VERIFIED-LIT** (published academic finding);
- **PRACTITIONER** (explanation);
- **LIVE-EXAMPLE** (demonstrated live trade, n small);
- **VERIFIED-PERFORMANCE** (independently audited results, e.g. contest-verified or broker-audited);
- **UNVERIFIED-CLAIM** / **HYPOTHESIS**.

**Rules:**
- Process sources in batches.
- Register every source in `SOURCES.md` before extracting claims.
- Deduplicate (check IDs and URLs).
- When a source is blocked, record it and move on.
- Never purchase data or use paid credits without approval.

## Batch plan and coverage

| Batch | Theme | Status | Output |
|---|---|---|---|
| B0 | Existing material (notes, YT-001…029, DOC-001…008, LIT, corpus S01–S53, NEXA tests) | DONE (2026-10-11, earlier sessions) | KB, CLAIMS CL-001…086 |
| **B1** | **Academic foundations:** volume-at-price, value area, S/R; trade size and informed trading; order-flow imbalance and trade-sign persistence; icebergs/hidden liquidity; ORB / intraday momentum; option flow and gamma | IN PROGRESS | `research_program/B1_ACADEMIC.md` |
| B2 | Platform documentation: Sierra Chart, ATAS, Jigsaw, Quantower, NinjaTrader (done), Bookmap (done), DeepCharts (done), CME Market Profile handbook | QUEUED | `research_program/B2_PLATFORMS.md` |
| B3 | Professional methodologies with complete processes: Dalton (S42), Steidlmayer (S46), Trader Dale (S44), Axia, Jigsaw, Fabio Valentini (audited contest results?), Michael Valtos, Peter Reznicek, others found | QUEUED | `research_program/B3_PRACTITIONERS.md` |
| B4 | Independently verifiable performance evidence (audited contests, published track records, academic backtests of these setups) | QUEUED | in B1/B3 files |
| B5 | Data sources and costs for aggressor-side CME data (DataBento, Rithmic, dxFeed, CQG, CME DataMine, Massive trades tier, AlgoSeek) | QUEUED | `research_program/B5_DATA.md` |
| B6 | Open-source implementations (footprint, volume profile, imbalance, absorption detectors) | QUEUED | `research_program/B6_CODE.md` |
| B7 | Video transcripts | **DONE 2026-10-11**: 30 transcripts via Tavily extract (YouTube had blocked this IP); Fabio primary YT-031…042 read in full; CL-118…134 | `kb/SOURCES.md` batch 6 |
| B8 | Strategy synthesis: complete strategies × 12 process elements; contradiction map | **v1 FINAL (2026-10-11)** incl. OFC1/OFC1R results; B7 still pending (YouTube block) | `../NEXA_ORDERFLOW_METHODOLOGY_MASTER.md` |

## Coverage log
| Date | Batch | Sources added | Notes |
|---|---|---|---|
| 2026-10-11 | B1, B3 (part), B5 (part) | LIT-003…012, WEB-001…003, DOC-009, CH-004, YT-030, CODE-007 | Key: no controlled tests of profile/footprint rules exist; base rate 97 % lose; Valentini contest placings verified; Databento pricing documented; Fabio primary videos queued first in the guard |
