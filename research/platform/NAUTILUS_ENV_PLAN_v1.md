# NautilusTrader v2 environment plan v1 (Phase 0, document only)

**Status:** PLAN, 2026-10-12. Nothing is installed by this document. The install in §6 needs a separate user "approved".

**Inputs:** user decision "Nautilus v2, Pepperstone + Dukascopy, free data, GitHub yes"; `RISK_ENGINE_SPEC_v1.md`; the Nautilus clone at `vendor/nautilus_trader`.

## 1. Verified facts (checked 2026-10-12, not assumed)

| Fact | Value | Source |
|---|---|---|
| Mac | arm64, macOS 26.5.1 | `uname -m`, `sw_vers` |
| Nautilus support | Python **3.13–3.14**; macOS **15+ ARM64** is an official platform | `vendor/.../docs/getting_started/installation.md`, `python/pyproject.toml` (`requires-python >=3.13,<3.15`) |
| Latest v2 on PyPI | **`2.0.0rc6`** (uploaded 2026-10-05) | PyPI JSON API |
| macOS arm64 wheels for rc6 | cp313 and cp314, 60.0 MB each | PyPI |
| sha256 prefixes of those wheels | cp313 `ec1a777efd507bb4…`, cp314 `465c056d57925b37…` | PyPI |
| The local clone | develop `5edd36e1`, labelled **rc7, which is unreleased** | `version.json` |
| Git tag | `v2.0.0rc6` = `d76a9032a7f7…` | `git ls-remote` |
| v2 runtime dependencies | **none** (`dependencies = []`); the Rust core is compiled into the wheel; optional `[visualization]` adds pandas / plotly | `python/pyproject.toml` |
| Install name clash | v1 and v2 both import as `nautilus_trader`; they must **never share an environment** | `MIGRATION_V2.md` |
| Python already on this Mac | 3.12.9 (research `.venv`, python.org framework), 3.14.8 (Homebrew), 3.9 (system) | `uv python list` |
| uv | 0.12.19 (Homebrew) | `uv --version` |
| License | LGPL-3.0: fine for private use as a library. Obligations apply only if a *modified* Nautilus is distributed. | Repository |
| Free disk | **≈ 16 GiB** on `/` | `df -h /` |

## 2. Decisions (recommended)

| # | Decision | Choice | Why |
|---|---|---|---|
| E1 | Version | **`nautilus_trader==2.0.0rc6` from PyPI, hash-pinned** | The newest *published* v2. Never `develop` / nightly wheels (the Nautilus docs advise against them for live use). rc7 is not released. |
| E2 | Python | **uv-managed CPython 3.13** (exact patch recorded in the lock) | Isolated from `brew upgrade` (a Homebrew 3.14 upgrade can silently break a venv). 3.13 has the widest third-party wheel coverage. The research env stays on 3.12. |
| E3 | Location | `NEXA-Agent-Lab/.venv-nautilus/` | Already excluded from git by the allow-list (`.venv*/`). Separate from `.venv` (research, 3.12) and from the Databento venv. |
| E4 | Lock | `research/platform/env/requirements-nautilus.txt` generated with `uv pip compile --generate-hashes`; install with `--require-hashes` | Reproducible on the Mac, on a future VM and in CI, byte-for-byte. |
| E5 | Extras | **none at first** (no `[visualization]`); pyarrow / pandas are added only when a step needs them, each pinned in the lock | Smallest attack surface and disk use. |
| E6 | Source reference | Pin the `vendor/nautilus_trader` clone to tag `v2.0.0rc6` (a local checkout only) | The code we read must equal the code we run. |
| E7 | Upgrades | Only by explicit decision. Each upgrade (rc6 → rc7 → 2.0.0) re-runs the full parity suite and records old and new hashes. | A framework update must never move results silently. |

## 3. Project layout (new code lives beside, never inside, the frozen trees)

```
NEXA-Agent-Lab/
  .venv-nautilus/              # env (gitignored)
  nexa_platform/               # NEW package (git-tracked)
    nexa_risk/                 # pure Python port of RISK_ENGINE_SPEC_v1 (no Nautilus import)
    nexa_venues/
      pepperstone/             # adapter choice: next Phase 0 doc
      dukascopy/               # historical datafeed client (free) + instrument specs
    nexa_data/                 # ingest -> validate -> Nautilus ParquetDataCatalog
    strategies/                # Nautilus Strategy classes (first: H-ORB-1, only after approval)
    tests/                     # parity + invariant tests
  data/catalog/                # Parquet catalog (gitignored; backed up to GCS)
  research/platform/           # these specs
```

**Untouched:** `filesnexa/`, `workspace/` and all pinned research files. `nexa_platform` may **read** frozen files (e.g. to extract golden vectors) but never writes into them.

## 4. Isolation and safety rules (binding for Phases 0–1)

1. **Backtest and sandbox only.** No live or paper execution client is configured in Phases 0–1. No credentials exist in this environment.
2. **No contact with S14:**
   - nothing in this env talks to MT5, the GCP VM or account <demo-account>;
   - meta-trader-mcp stays unused (it auto-launches the Mac MT5).
3. **Data is read-only from free public sources** (the Dukascopy datafeed) under `data/`. No paid feeds (the user chose free data only).
4. **No third-party "Dukascopy downloader" packages** unless audited first. The `.bi5` format is simple (LZMA plus fixed 20-byte records), so the client is ~150 lines using the standard library only.
   - **Superseded 2026-10-12 by `DUKASCOPY_DATA_PLAN_v1.md`:** Dukascopy's Terms of Use forbid scripted bulk access without written consent, so NEXA does **not** script the public datafeed. History comes from the JForex Historical Data Manager export (the sanctioned route) and Pepperstone MT5 exports.
5. **The research env is untouched.** A `pip freeze` hash of `.venv` is taken before and after the install and must be identical.

## 5. Disk budget (≈ 16 GiB free: tight)

| Item | Estimate | Rule |
|---|---|---|
| `.venv-nautilus` | ≈ 0.3–0.5 GB | — |
| uv cache | Already 0.48 GB; +≈ 0.1 GB | `uv cache prune` afterwards |
| Dukascopy **M1 bars** (bid + ask), ~10 instruments × 15–20 y, Parquet | ≈ 1–2 GB | Allowed locally |
| Dukascopy **ticks** | Tens of GB for majors over 20 y | **Not stored locally.** Ticks only for short validation windows; anything bulk goes to GCS. |
| **Floor** | Keep ≥ 8 GiB free at all times | Every ingest job checks free space first and stops below the floor |

**Recommendation to the user:** after the GCS backup is verified, consider moving cold data off the Mac (e.g. `filesnexa` CSV and log archives) to recover headroom. This is a separate decision; nothing is deleted without approval.

## 6. Install procedure (for approval; about 80 MB of downloads, about 2 minutes)

```bash
cd ~/NEXA-Agent-Lab
.venv/bin/pip freeze | shasum -a 256 > /tmp/research_env_before.sha      # 1. guard
uv python install 3.13                                                    # 2. isolated CPython (~20 MB)
uv venv .venv-nautilus --python 3.13                                      # 3. env
echo "nautilus_trader==2.0.0rc6" > research/platform/env/requirements-nautilus.src.txt
uv pip compile research/platform/env/requirements-nautilus.src.txt --generate-hashes \
   --python .venv-nautilus/bin/python -o research/platform/env/requirements-nautilus.txt   # 4. lock
uv pip install --python .venv-nautilus/bin/python --require-hashes \
   -r research/platform/env/requirements-nautilus.txt                     # 5. install (~60 MB wheel)
git -C vendor/nautilus_trader fetch --depth 1 origin tag v2.0.0rc6 && \
git -C vendor/nautilus_trader checkout v2.0.0rc6                         # 6. source = runtime
```

**Rollback:** `rm -rf .venv-nautilus`. Nothing else on the system changes.

## 7. Acceptance checks (all must pass; recorded in `research/platform/env/ENV_CHECK.md`)

1. `import nautilus_trader; nautilus_trader.__version__ == "2.0.0rc6"`, and the wheel sha256 matches PyPI.
2. A **synthetic smoke backtest:**
   - one hand-made instrument;
   - 1,000 generated bars;
   - a strategy that buys once and sells once;
   - expected P&L computed by hand;
   - the engine's result must equal it exactly.

   No market data is involved.
3. **Determinism:** the smoke backtest is run twice and the outputs are byte-identical.
4. **Research env unchanged:** the `pip freeze` hash is equal before and after.
5. **Repository hygiene:** `git status` shows only the new lock files and docs; nothing under `.venv-nautilus` is staged.

## 8. What comes after (still Phase 0, documents)

- **Pepperstone adapter choice:** cTrader Open API (native, no Wine, needs an app registration) vs the community `mt5-connector` (needs an audit; MT5 must run somewhere other than the S14 VM).
- **Dukascopy free-data plan:**
  - instrument list (incl. USATECH for H-ORB-1 and FX majors);
  - bid/ask M1 construction from ticks vs ready candles;
  - time base (Dukascopy = UTC; Pepperstone = NY + 7 h);
  - validation against Pepperstone M1 overlaps.
- **Instrument / cost master:** one table with per-venue point, contract size, min lot, commission, typical spread and swap. It feeds `InstrumentSpec` (risk spec §6).
