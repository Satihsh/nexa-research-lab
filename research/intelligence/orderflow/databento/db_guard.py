"""Spend-guarded access to Databento historical data for NEXA research.

The only sanctioned way to touch the Databento API from NEXA research.

Rules enforced here (user, 2026-10-11):
  * Hard cap: USD 5.00 total across all downloads (CAP_USD; no override flag).
  * Every download is preceded by metadata.get_cost; the estimate is shown and
    a confirmation token is issued. `fetch` requires that token, re-checks the
    cost, and refuses if the cap would be exceeded or the price moved.
  * Spend is written to ledger.json BEFORE the request (a failed request stays
    counted; conservative).
  * Historical streaming only (timeseries.get_range). No batch jobs, no live.
  * The API key is read from ./.env (gitignored, mode 600) and never printed;
    any error text is scrubbed of it.

Commands (run with the dedicated venv):
  .venv/bin/python -I db_guard.py auth
  .venv/bin/python -I db_guard.py inspect [--dataset GLBX.MDP3] [--symbols 6E.v.0,...] [--date YYYY-MM-DD]
  .venv/bin/python -I db_guard.py estimate --schema trades --symbols 6E.v.0 --stype continuous --start 2026-09-14 --end 2026-09-15
  .venv/bin/python -I db_guard.py fetch --token <token>
  .venv/bin/python -I db_guard.py budget
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV_FILE = HERE / ".env"
LEDGER = HERE / "ledger.json"
PENDING = HERE / "pending"
DATA = HERE / "data"

# Cap history (each change needs explicit user approval in chat):
#   2026-10-11 5.00  initial hard cap (user)
#   2026-10-11 12.44 user approved option A: + 6E trades 2025-09-01..2026-09-01 quoted USD 11.6340 (0.7973 + 11.6340)
#   2026-10-11 68.07 user approved: + 6J/6B/GC trades 2025-09-01..2026-10-01 quoted USD 10.1713 + 5.5213 + 39.9403 = 55.6330
#   2026-10-11 117.95 user approved FINAL run: + 6E trades 2022-10-01..2025-09-01 quoted USD 49.8828 (free credit only; user: "final run, no more spending")
#   2026-10-13 122.66 user approved "approve Databento $4.71 (option 1)": + NQ.v.0 ohlcv-1m 2023-02-18..2026-10-10 quoted USD 4.7078 (H-ORB-1 holdout; user credit USD 7.06)
CAP_USD = 122.66          # hard total cap; do not add an override flag
PRICE_TOLERANCE = 0.01    # refuse fetch if the re-checked cost rises > 1 %
TOKEN_TTL_H = 24
DEFAULT_DATASET = "GLBX.MDP3"

_KEY: str | None = None


# ---------------------------------------------------------------- key handling
def _load_key() -> str:
    global _KEY
    if _KEY:
        return _KEY
    if not ENV_FILE.exists():
        sys.exit(f"missing {ENV_FILE} (put DATABENTO_API_KEY=... there; never in chat)")
    if ENV_FILE.stat().st_mode & 0o077:
        os.chmod(ENV_FILE, 0o600)
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("DATABENTO_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key and key != "PASTE_YOUR_KEY_HERE":
                _KEY = key
                return key
    sys.exit(f"DATABENTO_API_KEY not set in {ENV_FILE}")


def scrub(text: str) -> str:
    return text.replace(_KEY, "***") if _KEY else text


def client():
    import databento as db
    return db.Historical(key=_load_key())


# ---------------------------------------------------------------- ledger
def _read_ledger() -> list[dict]:
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else []


def _write_ledger(rows: list[dict]) -> None:
    tmp = LEDGER.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(rows, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(LEDGER)


def committed_usd(rows: list[dict] | None = None) -> float:
    rows = _read_ledger() if rows is None else rows
    return round(sum(r["cost_usd_est"] for r in rows if r["status"] in ("reserved", "done", "failed")), 6)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- commands
def cmd_auth(_a) -> None:
    ds = client().metadata.list_datasets()
    print(f"auth OK | {len(ds)} datasets visible | GLBX.MDP3 present: {'GLBX.MDP3' in ds}")


def cmd_inspect(a) -> None:
    c = client()
    ds = a.dataset
    rng = c.metadata.get_dataset_range(ds)
    print(f"== {ds} range: {rng.get('start')} -> {rng.get('end')}")
    print("== schemas:", ", ".join(c.metadata.list_schemas(ds)))
    for row in c.metadata.list_unit_prices(ds):
        prices = row.get("unit_prices", {})
        print(f"== unit prices USD/GB [{row.get('mode')}]:",
              ", ".join(f"{k}={v}" for k, v in sorted(prices.items())))
    trade_fields = [f["name"] for f in c.metadata.list_fields("trades", "dbn", ds)]
    print("== trades fields:", ", ".join(trade_fields))
    end = a.date or rng.get("end", "")[:10]
    start = (datetime.fromisoformat(end) - timedelta(days=7)).date().isoformat()
    cond = c.metadata.get_dataset_condition(ds, start, end)
    bad = [r for r in cond if r.get("condition") != "available"]
    print(f"== condition {start}..{end}: {len(cond)} days, not-available: {bad or 'none'}")
    syms = [s for s in a.symbols.split(",") if s]
    res = c.symbology.resolve(ds, syms, a.stype, "instrument_id", start, end)
    print("== symbology (", a.stype, ")")
    for s in syms:
        maps = res.get("result", {}).get(s, [])
        last = maps[-1] if maps else None
        print(f"   {s}: {len(maps)} mapping(s); last={last}")
    print("   not_found:", res.get("not_found"), "| partial:", res.get("partial"))


def _req_from_args(a) -> dict:
    return {
        "dataset": a.dataset, "schema": a.schema, "stype_in": a.stype,
        "symbols": sorted(s for s in a.symbols.split(",") if s),
        "start": a.start, "end": a.end,
    }


def _estimate(c, req: dict) -> tuple[float, int, int]:
    kw = dict(dataset=req["dataset"], start=req["start"], end=req["end"],
              symbols=req["symbols"], schema=req["schema"], stype_in=req["stype_in"])
    cost = float(c.metadata.get_cost(**kw))  # default mode = historical streaming
    size = int(c.metadata.get_billable_size(**kw))
    count = int(c.metadata.get_record_count(**kw))
    return cost, size, count


def cmd_estimate(a) -> None:
    c = client()
    req = _req_from_args(a)
    cost, size, count = _estimate(c, req)
    spent = committed_usd()
    left = round(CAP_USD - spent, 6)
    fits = cost <= left
    print(f"request : {json.dumps(req)}")
    print(f"estimate: USD {cost:.4f} | billable {size/1e6:.2f} MB | {count:,} records (metadata.get_cost, historical-streaming)")
    print(f"budget  : cap USD {CAP_USD:.2f} | committed USD {spent:.4f} | remaining USD {left:.4f} | fits: {fits}")
    if not fits:
        print("REFUSED: would exceed the hard cap. No token issued.")
        return
    token = hashlib.sha256(json.dumps([req, round(cost, 6)], sort_keys=True).encode()).hexdigest()[:12]
    PENDING.mkdir(exist_ok=True)
    (PENDING / f"{token}.json").write_text(json.dumps(
        {"token": token, "req": req, "cost_usd_est": cost, "billable_bytes": size,
         "records": count, "estimated_at": _now()}, indent=2))
    print(f"token   : {token}  (valid {TOKEN_TTL_H} h; download only after the user confirms this cost)")


def cmd_fetch(a) -> None:
    p = PENDING / f"{a.token}.json"
    if not p.exists():
        sys.exit("unknown token: run `estimate` first and show the cost")
    pend = json.loads(p.read_text())
    age = datetime.now(timezone.utc) - datetime.fromisoformat(pend["estimated_at"])
    if age > timedelta(hours=TOKEN_TTL_H):
        sys.exit("token expired: re-run `estimate`")
    req = pend["req"]
    c = client()
    cost, size, count = _estimate(c, req)
    if cost > pend["cost_usd_est"] * (1 + PRICE_TOLERANCE) + 1e-6:
        sys.exit(f"REFUSED: cost changed {pend['cost_usd_est']:.4f} -> {cost:.4f}; re-estimate and re-confirm")
    rows = _read_ledger()
    spent = committed_usd(rows)
    if spent + cost > CAP_USD + 1e-9:
        sys.exit(f"REFUSED: committed {spent:.4f} + {cost:.4f} > cap {CAP_USD:.2f}")
    if any(r["token"] == a.token and r["status"] in ("reserved", "done") for r in rows):
        sys.exit("REFUSED: this token was already used (avoid paying twice)")

    DATA.mkdir(exist_ok=True)
    fname = f"{req['dataset']}_{req['schema']}_{'+'.join(req['symbols'])}_{req['start']}_{req['end']}.dbn.zst"
    out = DATA / fname.replace("/", "-").replace(":", "")
    entry = {"token": a.token, "req": req, "cost_usd_est": cost, "billable_bytes": size,
             "records_est": count, "status": "reserved", "reserved_at": _now(), "path": str(out)}
    rows.append(entry)
    _write_ledger(rows)
    print(f"reserved USD {cost:.4f} (committed now {spent + cost:.4f} / {CAP_USD:.2f}); downloading ...")
    try:
        c.timeseries.get_range(dataset=req["dataset"], start=req["start"], end=req["end"],
                               symbols=req["symbols"], schema=req["schema"],
                               stype_in=req["stype_in"], path=str(out))
        entry.update(status="done", done_at=_now(), file_bytes=out.stat().st_size)
        print(f"done: {out} ({out.stat().st_size/1e6:.2f} MB on disk)")
    except Exception as e:  # keep the reservation counted
        entry.update(status="failed", failed_at=_now(), error=scrub(f"{type(e).__name__}: {e}")[:500])
        print("FAILED (reservation kept in ledger):", entry["error"])
    finally:
        _write_ledger(rows)
        p.unlink(missing_ok=True)


def cmd_budget(_a) -> None:
    rows = _read_ledger()
    for r in rows:
        print(f"{r['reserved_at']} {r['status']:8s} USD {r['cost_usd_est']:.4f} {r['req']['schema']} "
              f"{','.join(r['req']['symbols'])} {r['req']['start']}..{r['req']['end']}")
    spent = committed_usd(rows)
    print(f"committed USD {spent:.4f} of cap {CAP_USD:.2f}; remaining USD {CAP_USD - spent:.4f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    sp = sub.add_parser("inspect")
    sp.add_argument("--dataset", default=DEFAULT_DATASET)
    sp.add_argument("--symbols", default="6E.v.0,6J.v.0,6B.v.0,GC.v.0,ES.v.0,NQ.v.0")
    sp.add_argument("--stype", default="continuous")
    sp.add_argument("--date", default=None)
    for name in ("estimate",):
        e = sub.add_parser(name)
        e.add_argument("--dataset", default=DEFAULT_DATASET)
        e.add_argument("--schema", required=True)
        e.add_argument("--symbols", required=True)
        e.add_argument("--stype", default="continuous")
        e.add_argument("--start", required=True)
        e.add_argument("--end", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--token", required=True)
    sub.add_parser("budget")
    a = ap.parse_args()
    try:
        {"auth": cmd_auth, "inspect": cmd_inspect, "estimate": cmd_estimate,
         "fetch": cmd_fetch, "budget": cmd_budget}[a.cmd](a)
    except SystemExit:
        raise
    except Exception as e:
        sys.exit("error: " + scrub(f"{type(e).__name__}: {e}")[:800])


if __name__ == "__main__":
    main()
