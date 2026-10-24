# NEXA 8-engine experiment matrix (RESEARCH_8E_V1)

**Machine-readable registry:**
- `research/registry_8e/campaign.json`: protocol pins, counts and notes.
- `research/registry_8e/trial_universe.json`: all trials, each with an id and config.
- `research/registry_8e/protocols/*.json`: the protocols themselves.
- `research/registry_8e/ledger.jsonl`: the hash chain.
- `research/registry_8e/results.jsonl`: one VAL record per trial.

The campaign hash (anchor) is `6468fdea1eb4063e6658ade37fdc7c137693f8b626c6a641dcd29af885517ccf`; its external witness is under `~/.nexa_registry_witness/`.
Superseded before opening (archived, never opened): `834473f0…`.

This campaign is independent of V2 (`6090be68…`, still FROZEN and **not opened**).

**Trials:** 2160 active + 1848 legacy = **4008** for DSR.

**Primary groups:** 3: [['E8_STACK', 'C_stack', 'EURUSD'], ['E8_STACK', 'C_stack', 'GBPUSD'], ['E8_STACK', 'C_stack', 'XAUUSD']].

| Experiment | Status | Symbols | Grid | Variants | Trials |
|---|---|---|---|---|---|
| E8_NAS100 | BLOCKED | NAS100 | {'dc_n': [20, 55], 'entry_mode': ['close_next_open', 'stop_at_channel'], 'target_r': [2, 3, 5], 'tf': ['M15', 'H1']} | 8 | 0 |
| E8_STACK | ACTIVE | XAUUSD, EURUSD, GBPUSD | {'dc_n': [20, 55], 'entry_mode': ['close_next_open', 'stop_at_channel'], 'target_r': [2, 3, 5], 'tf': ['M15', 'H1']} | 15 | 1080 |
| E8_THRESH | ACTIVE | XAUUSD, EURUSD, GBPUSD | {'dc_n': [20, 55], 'entry_mode': ['close_next_open', 'stop_at_channel'], 'target_r': [2, 3, 5], 'tf': ['M15', 'H1']} | 15 | 1080 |

## Periods (UTC, half-open)

| Period | Window | Rule |
|---|---|---|
| DEV | 2018-01-01 → 2023-01-01 | development and exploration; unlimited, never recorded for selection |
| VAL | 2023-01-01 → 2026-09-25 | **one query per trial**; **seen data, not out-of-sample** |
| Walk-forward years | 2020, 2021, 2022 | within DEV |
| OOS | 2026-10-12 → 2027-04-12 | **prospective**: the data does not exist yet; selection is sealed before the start |

Embargo is 5,760 min and the maximum label is 2,880 min; trades straddling a period boundary are purged.

## Variant definitions

- **L0–L7:** the cumulative stack sq → vei → ema200 → mom → ofi proxy → quote burst → td.
- **A_\*:** single add-ons on the baseline.
- **vei_\*, ofi_\*, qb_\*:** threshold sensitivity, applied as single add-ons.

Full definitions are in `NEXA_8_ENGINE_SPECIFICATION.md`.

## Recorded pre-freeze exploration (disclosed)

- XAUUSD M15 2021 (DEV): harness smoke test.
- XAUUSD H1 dc20 close_next_open k3 (DEV): runner smoke test.

No VAL data was read before the freeze.

## Not run (with reason)

- **NAS100:** no local price history; registered as BLOCKED.
- **Tick-level OFI and quote bursts on years of data:** only 21 days of quote ticks exist, all already inspected, so they are used descriptively only.
- **Timeframes M1, M5 and M30, and the HTF-regime + LTF-execution combinations:** not in this universe. They need a new frozen campaign, and their trial counts would add to the multiple-testing count.
- **Exit families** (Donchian exit, trailing exit, volatility target): not in this universe, for the same reason.
