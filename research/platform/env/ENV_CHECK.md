# Nautilus v2 environment — acceptance record (NAUTILUS_ENV_PLAN_v1 §7)

**Install approved by the user 2026-10-12:** "approved, install Nautilus". Installed and checked the same day.

## What was installed

| Item | Value |
|---|---|
| Python | uv-managed CPython **3.13.15** (`~/.local/share/uv/python/cpython-3.13-macos-aarch64-none`) |
| Env | `NEXA-Agent-Lab/.venv-nautilus` (138 MB, gitignored) |
| Package | `nautilus_trader==2.0.0rc6` from PyPI, installed with `--require-hashes` from `requirements-nautilus.txt` |
| Wheel used (cp313 macOS arm64) | sha256 `ec1a777efd507bb4834d641d88779407957e6323a40eaec78610738aa2646cf2` (matches PyPI) |
| Other packages in the env | none (v2 has zero runtime dependencies) |
| Source reference | `vendor/nautilus_trader` checked out at tag `v2.0.0rc6` (tag object `d76a9032…`, commit `7b766f8825b2539c5b2ac1375e9d97b41c509edb`) |

## Checks

| # | Check | Result |
|---|---|---|
| 1 | Import + version == 2.0.0rc6; wheel hash enforced by `--require-hashes` | **PASS** |
| 2 | Synthetic smoke backtest (`nexa_platform/tests/env_smoke.py`). Hand-calculated in advance: BUY 2 @ 1.10000, SELL 2 @ 1.10500, ×125,000, fees 4 × 2 × 2.50 → balance **1,001,240.00 USD** | **PASS** (fills and balance exact) |
| 3 | Determinism: two runs byte-identical (fills, fill timestamps, balance) | **PASS** |
| 4 | Research `.venv` unchanged: `pip freeze` sha256 `358450bc8ad3a486…` before = after | **PASS** |
| 5 | Repository hygiene: `.venv-nautilus` ignored; only the lock files, docs and the smoke test are new | **PASS** |

**Full output:** `env_smoke_result.json`.

**Not done:** `uv cache prune` (slow; optional, can be run any time). Free disk after the install: ≈ 16 GiB.

**Untouched:** S14, the GCP VM, MT5, NEXA_Risk, schema v1 and the research env. No credentials and no market data are involved.

**Rollback:** `rm -rf .venv-nautilus` (plus `uv python uninstall 3.13` if desired).
