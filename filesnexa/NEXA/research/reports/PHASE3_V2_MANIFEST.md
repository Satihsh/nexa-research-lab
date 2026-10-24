# PHASE3_SIX_FAMILIES_V2: final freeze manifest

**State: FROZEN / NOT OPENED / NOT EVALUATED.** V1 is permanently REJECTED. Four earlier V2 freezes were superseded before opening; see `V2_EXTERNAL_ANCHOR_VERIFICATION.md`.

## Identity
| Item | Value |
|---|---|
| Campaign | PHASE3_SIX_FAMILIES_V2 |
| **Anchor** | `6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c` |
| Published ledger head | seq 6 `bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b` |
| Registry | `research/registry_v2/` (tree sha256 `de0c101accf58655e0de38f7a835ba701bccfe5c3a01dd03c96ad54c6e8ef504`) |
| Witness | `~/.nexa_registry_witness/6090be68…9324c.jsonl` (sha256 `05d4544b4c86340d…`) |
| Trial universe | `368ee5743e8d1b15e49585e08068f656824f95e1e38658fc5a65c0ad679bc8bf` |
| Data digest (14) | `f236cdf3b878ceafeb0a45ec600208e5f2c014286f12af46309896abba81170d` |
| Code digest (23) | `4c38cf5debfab32995113f320c5b04458331d62793e630d07ba8191939b7d339` |
| Design digest (5) | `8f7c808519e1c82330f87a437bfbe3ba1f6ab399e3631a58b83588eb8ad5d0a9` |

## Protocols
| Experiment | Status | sha256 |
|---|---|---|
| F1_MACRO_EVENT | ACTIVE | `c15966607f0ea00eb0939c83f8300af928c772989ba5d5da5b44cb61af9732a1` |
| F2_XAU_SESSION_BREAKOUT | ACTIVE | `6dcf96c566e7c0c21fe6b740b3213698eeddbbdf4f7aa50abf09e23eb1bf4e2d` |
| F3_FVG_RETRACEMENT | ACTIVE | `c2e16136e9b2cca6bc0e858a0843ad6b9a121b9bd0c5a77b962b77afa5183ea0` |
| F4_CROSS_FEED_LATENCY | BLOCKED | `f1a128df9244d680a38301776889b837aac081e7b4242ce097eaaad58b7debd9` |
| F5_ASIAN_MEAN_REVERSION | ACTIVE | `d4d748330b7a9abc6ceae1e507237e76263a50b1a127ffaae6b915b87276fc7f` |
| F6_TICK_QUOTE_IMBALANCE | BLOCKED | `03d0f208725a12ea01c7efe6e72280b919774d6d8269d12901d7aff6b4564fed` |

## Periods (UTC, half-open)
| Period | Window |
|---|---|
| DEV | [2018-01-01, 2023-01-01) |
| VAL | [2023-01-01, 2025-01-01), one query per trial |
| Walk-forward | 2020–2024, one query per trial-year |
| EXCLUDED | [2025-01-01, 2027-01-04), never used |
| **OOS** | **[2027-01-04T00:00:00Z, 2028-01-03T00:00:00Z), PROSPECTIVE** |

## Counts
| Measure | Count |
|---|---|
| Active trials | **1,632** |
| — F1 | 216 |
| — F2 | 72 |
| — F3 H3a | 48 |
| — F3 H3b | 864 |
| — F5 | 432 |
| DSR trial count | **1,740** (incl. 108 legacy) |
| BH-FDR primary tests | **17** |

## Pinned code (23 files)
- **Registry and causality:** `nexa_registry2`, `nexa_causality`
- **V2 builders, trials and driver:** `nexa_v2_features`, `nexa_v2_trials`, `nexa_v2_runner`
- **Protocols:** `protocols_phase3_v2`
- **Execution and statistics:** `nexa_execution`, `nexa_stats`, `nexa_robust`
- **Data and time layer:** `nexa_time`, `nexa_calendar`, `nexa_m1_history`, `build_calendar_v2`
- **Freeze and registration scripts:** `freeze_phase3_v2`, `register_builders_v2`
- **Tests:** `test_nexa_registry2`, `test_nexa_causality`, `test_nexa_calendar`, `test_nexa_execution`, `test_nexa_time`, `test_nexa_v2_features`, `test_nexa_v2_trials`, `test_nexa_v2_runner`

## Pinned data (14 files)
- 4 core M1 canonical files and their 4 manifests;
- calendar canonical v2 and its manifest;
- raw calendar values, events and provenance;
- `contracts.json`.

## Pinned design documents (5 files)
- `RESEARCH_DESIGN_SIX_FAMILIES.md`
- `AUDIT_PHASE3_CAMPAIGN_V1.md`
- `TIME_CONVENTION_EVIDENCE.json`
- `OOS_DETERMINATION_V2.md`
- `V2_EXTERNAL_CHECKPOINT_PROCEDURE.md`

## Certified builders (registered while FROZEN)
- `f1_features`
- `f2_features`
- `f2_null_random_range`
- `f3_features`
- `f5_features`
- `calendar_prior_baselines` (event builder)
