# 17: IMPLEMENTATION CANDIDATES (research tier only)

**Nothing here is approved for implementation.** "Implementation" means **research-tier code** (Python, under `research/`) to *run the tests* in 14/15. Each item needs its own approval. **No EA, schema or forward-test change is proposed.**

**Ranking:**
1. evidence prior;
2. data availability;
3. dependency (foundations first);
4. cost.

| Rank | Candidate | What it is | Unblocks | Data | Effort | Why this rank |
|---|---|---|---|---|---|---|
| **1** | **Proxy-validation study (full 2 y)** | Extend the 2026-10-04 probes to 2024-10 → 2026-09 and all four symbols (6B for GBP; 6J for JPY, inverted): hourly activity correlation, daily VA/POC/HVN agreement, causal basis error | HYP-001, HYP-034; decides whether spot-profile features are usable at all | ✓ Massive + MT5 | Small | **Foundation.** Cheap, decisive, no outcome peeking |
| **2** | **Volatility layer** (YZ + HAR + QLIKE/DM harness) | σ̂ estimators and forecast evaluation | HYP-001b, 002, 019, H-VOL-1..4 | ✓ | Small–medium | **Strongest evidence (original P2 + S48).** σ̂ is the unit of every other feature |
| **3** | **Fixed-entry exit/stop re-simulator** | Replays existing tester-DNA entries on M1 with alternative (U, D) and stop rules; cost model per EQ-025 | HYP-023 (H2, H3, H5), HYP-024, H-HIT-PROB | ✓ | Medium | Directly targets NEXA's measured failure mode (cost-in-R) |
| **4** | **Session-anchor and day-structure library** | UTC/DST anchors (06 §3); IB, REX, CL, ROT, open type, day type (EQ-016–018) | HYP-008–013 | ✓ | Small | Converts the new corpus's main contribution into testable objects |
| **5** | **Revealed-liquidity field library** | L(p,t), VA/POC (with fixed tie-break), HVN/LVN, g, κ, C; spot (tick volume) and futures (basis-mapped) variants | HYP-004–007, 014, 015, 016 | ✓ / ◐ | Medium | Core of the "WHERE" layer that NEXA *can* build |
| **6** | **Placebo-level and base-rate engine** | Generic matched-placebo generator and base-rate tables for level and day-type tests | All level/day-type hypotheses (mandatory null, 15 §2) | ✓ | Small | Without it, every level result is uninterpretable |
| **7** | **Regime module** | Observed 3×3 Markov (σ̂ × ER) plus Gaussian HMM (filtered only) | HYP-020, 036 | ✓ | Medium | Unifies practitioner "day type / regime" claims into one testable family |
| **8** | **Execution analytics on S14 demo data** | Slippage vs state (M-09), commission confirmation, tick-logger joins | HYP-035, H-NEWS-SLIP, H-STOP-SLIP, HYP-017b | ✓ (prospective) | Small | Already approved data collection. Analysis after ≥ 100 fills |
| **9** | **Futures activity features** | RVOL^F, V/N, Amihud from Massive; roll calendar | HYP-016, 002 | ✓ (2 y) | Small–medium | True volume is NEXA's only true microstructure input |
| **10** | **Flow-proxy research module** | Futures BVC (lagged), absorption (EVR/ABS), CVD divergence | HYP-003, 017, 018, 022 | ◐ | Medium | Low prior. Proxy-only conclusions |
| **11** | **GLD options proxy pipeline** | Chain enumeration (`expired=true`), daily volume by strike, local BS-IV inversion, VRP | HYP-028, 030 | ◐ | Medium–large | Weak proxy for gold. Do only if 1–7 are done |
| **12** | **GEX engine (S53/S54 standard)** | Model-A sign contract, repriced flip, walls, HPR | HYP-025–027, 029 | ✗ | Large + data cost | **Blocked** until COMEX OG OI/IV history (or prospective collection) is acquired (19) |

**Dependencies:**
- 1 → 5, 9, 10, 11 (proxy and basis validity);
- 2 → everything (σ̂ units);
- 4 → 5, 7 (session anchors);
- 6 → every level/day-type test;
- 3 depends on 2.

**What would change the production system (out of scope; listed for transparency):**
- schema v1.1 with NF features;
- replacing ATR with σ̂_YZ/HAR in the EA;
- a calibrated P_U/E[R] judge;
- broker DOM logging (XAU).

**Each would require:** a SUPPORTED registry status, the 15 §7 promotion rules, parity work and explicit human approval.
