# Databento access for NEXA research (set up 2026-10-11)

**Client:** the official `databento` Python package 0.87.0 (PyPI, publisher Databento).
- It is installed in a dedicated venv, `./.venv`. The shared root `.venv` and the frozen `filesnexa/NEXA/.venv-research` are untouched.
- Exact dependency pins: `requirements.lock.txt`.

**No MCP server.** The `@nice-wolf-studio/databento-mcp-server` npm package does not exist (npm 404). It must not be used.

## Rules (user, 2026-10-11)
- **Hard cap: USD 117.95 total (FINAL; user: no more spending)** (5.00 initially; raised 2026-10-11 by user approvals for 6E, then 6J/6B/GC; history in `db_guard.py`). It is enforced by `db_guard.py` (`CAP_USD`, with no override flag).
- **Before every download:** run `metadata.get_cost` → show the estimate → the user confirms → `fetch --token`.
- **The key is read only from `./.env`:**
  - mode 600;
  - gitignored here and at the repo root;
  - never printed, and scrubbed from error text.
- Historical streaming only. No batch jobs, no live data. No production EA, MT5, trading or orders.

## Use
```
.venv/bin/python -I db_guard.py auth        # free: list datasets
.venv/bin/python -I db_guard.py inspect     # free: GLBX.MDP3 range, schemas, unit prices, trade fields, symbology
.venv/bin/python -I db_guard.py estimate --schema trades --symbols 6E.v.0 --stype continuous --start YYYY-MM-DD --end YYYY-MM-DD
.venv/bin/python -I db_guard.py fetch --token <token>   # only after the user confirms the displayed cost
.venv/bin/python -I db_guard.py budget
```

## How the guard behaves
- **The token** is a hash of the request and its estimated cost. It is valid for 24 h and single-use.
  - An identical request at the same cost yields the same token, so the guard refuses to pay twice for the same data.
- **`fetch` re-runs `get_cost`.** It refuses if:
  - the price rose more than 1 %; or
  - committed spend + cost > USD 5.00.
- **Ledger:** spend is written to `ledger.json` *before* the request. A failed request stays counted (conservative).
- **The guard caps only spend that goes through it.** The key itself can spend the whole account balance in any other tool.
- **Downloaded files** go to `./data/` (gitignored).
- **Testing:** verified offline with a mock client on 2026-10-11 (cap boundary, token reuse, price rise, key scrubbing).
