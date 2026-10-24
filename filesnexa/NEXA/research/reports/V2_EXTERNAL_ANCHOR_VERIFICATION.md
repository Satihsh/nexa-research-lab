# PHASE3_SIX_FAMILIES_V2: external anchor and checkpoint verification record (FINAL)

Verified 2026-09-29 (UTC) with `RegistryV2.verify(anchor, checkpoint)` plus independent recomputation.

| Item | Value | Check |
|---|---|---|
| Campaign | PHASE3_SIX_FAMILIES_V2 | — |
| **Anchor** = sha256(`research/registry_v2/campaign.json`) | **`6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c`** | recomputed = anchor; `ANCHOR.txt` = anchor |
| State | **FROZEN**: not opened, not evaluated | derived from ledger |
| Ledger | 7 events: CAMPAIGN_FROZEN + 6 BUILDER_CERTIFIED | hash chain intact |
| External witness | `~/.nexa_registry_witness/6090be68…9324c.jsonl`, 7 entries (sha256 `05d4544b4c86340d21c5efd8ab444cb1b9ba66eb04a3ea2830091e14f1722f45`) | equals ledger entry for entry |
| Registry directory tree sha256 | `de0c101accf58655e0de38f7a835ba701bccfe5c3a01dd03c96ad54c6e8ef504` | unchanged by the scratch attacks |
| Trial universe sha | `368ee5743e8d1b15e49585e08068f656824f95e1e38658fc5a65c0ad679bc8bf` | file = pin = re-derived from protocols |
| Data digest (14 files) | `f236cdf3b878ceafeb0a45ec600208e5f2c014286f12af46309896abba81170d` | every file hash = pin |
| Code digest (23 files) | `4c38cf5debfab32995113f320c5b04458331d62793e630d07ba8191939b7d339` | every file hash = pin |
| Design digest (5 files) | `8f7c808519e1c82330f87a437bfbe3ba1f6ab399e3631a58b83588eb8ad5d0a9` | every file hash = pin |
| Results / OOS rows | 0 / 0 | — |

## Published ledger heads (compare-and-swap chain)
```
NEXA-CHECKPOINT campaign=PHASE3_SIX_FAMILIES_V2 anchor=6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c seq=0 head=f2914c8e4f69cea04ba4dfa3256db9677a951e4c98b18218eafeb2876b08b57a state=FROZEN
seq=1 head=8a7802031344961865be6c24a9960ced2af66e5ada67ba14cb7c0a0cfc4b1ad5  BUILDER_CERTIFIED f1_features
seq=2 head=ca4f035f859fe5b078f5b1804899a8cf293ecbc744d88315fc88ef94a7e19e17  BUILDER_CERTIFIED f2_null_random_range
seq=3 head=585b706cbec6565e61775f5d512219b79f60dab52cb3fcf4e0432c259c6a9a94  BUILDER_CERTIFIED f2_features
seq=4 head=c719075a63387280206b7b2d7ec02fe16ff217272c67f7171d3a4f7be2454cf1  BUILDER_CERTIFIED f3_features
seq=5 head=a5529e17444b688d5f65e338a49a5064549a4f7086e5bdaf6601d7568c36f6eb  BUILDER_CERTIFIED f5_features
NEXA-CHECKPOINT campaign=PHASE3_SIX_FAMILIES_V2 anchor=6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c seq=6 head=bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b state=FROZEN
```
**Current authoritative head: seq 6 `bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b`.** The next mutating call, `open_evaluation`, must present exactly this checkpoint, copied from an off-machine record.

These values were reported in the Claude conversation of 2026-09-29, which is an off-machine record. **Human action required:** also record them somewhere this machine cannot rewrite. There is no Git repository or remote yet.

## Protocol hashes (identical across every V2 freeze)
| Experiment | Status | sha256 |
|---|---|---|
| F1_MACRO_EVENT | ACTIVE | `c15966607f0ea00eb0939c83f8300af928c772989ba5d5da5b44cb61af9732a1` |
| F2_XAU_SESSION_BREAKOUT | ACTIVE | `6dcf96c566e7c0c21fe6b740b3213698eeddbbdf4f7aa50abf09e23eb1bf4e2d` |
| F3_FVG_RETRACEMENT | ACTIVE | `c2e16136e9b2cca6bc0e858a0843ad6b9a121b9bd0c5a77b962b77afa5183ea0` |
| F4_CROSS_FEED_LATENCY | BLOCKED | `f1a128df9244d680a38301776889b837aac081e7b4242ce097eaaad58b7debd9` |
| F5_ASIAN_MEAN_REVERSION | ACTIVE | `d4d748330b7a9abc6ceae1e507237e76263a50b1a127ffaae6b915b87276fc7f` |
| F6_TICK_QUOTE_IMBALANCE | BLOCKED | `03d0f208725a12ea01c7efe6e72280b919774d6d8269d12901d7aff6b4564fed` |

## Builder certificates (registered while FROZEN, before any opening)
| Builder | Kind | Source sha (function + module) prefix | Perturbed inputs |
|---|---|---|---|
| nexa_v2_features.f1_features | bars | `dedbf90675f8c71e` | OHLC, f1_score (release values), spread |
| nexa_v2_features.f2_features | bars | `23413d91e31d84d3` | OHLC, spread |
| nexa_v2_features.f2_null_random_range | bars | `bfdf5de0e1f380b8` | OHLC, spread |
| nexa_v2_features.f3_features | bars | `fa4b59b4084ddcf8` | OHLC, spread |
| nexa_v2_features.f5_features | bars | `c1e30107337e07f7` | OHLC, spread |
| nexa_v2_features.calendar_prior_baselines | events | `f68b4070f954992d` | actual, forecast, prev, revised_prev |

All registered certificate hashes equal the current builder source hashes.

## Superseded pre-opening freezes
All are archived byte-for-byte, were never opened, and **must never be opened**. Their old code pins no longer verify.

| Anchor | Archive | Reason |
|---|---|---|
| `27b3463f…8485b` | `registry_v2_superseded_27b3463f/` | registry defects A6d / A10b / X1 (2026-09-27 UTC) |
| `f2dc4ffb…105e` | `registry_v2_superseded_f2dc4ffb/` + `.SUPERSEDED.txt` | builders, trial layer, execution hardening, sensitive-cut certification, R1 checkpoint |
| `faac4c86…33c0` | `registry_v2_superseded_faac4c86/` + `.SUPERSEDED.txt` | final audit A30b: a raw exception; registry hardened |
| `88b7688b…7197` | `registry_v2_superseded_88b7688b/` + `.SUPERSEDED.txt` | evaluation driver pinned before opening (its audit was clean) |

The final `campaign.json` lists all four in `notes.superseded_pre_opening_freezes`. **There is exactly one authoritative V2 identity: `6090be68…9324c`.**
