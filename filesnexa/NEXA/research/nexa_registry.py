"""NEXA experiment registry: protocol freezing, trial accounting, multiple-testing hierarchy.

HIERARCHY
  Program     NEXA (all tests ever run; cumulative count kept for reporting)
  Campaign    one multiple-testing budget, one set of frozen protocols, one state machine
  Experiment  one hypothesis family, exactly one FROZEN protocol version
  Config      one point of the experiment's pre-declared grid  (= one TRIAL)
  Run         config x symbol x period (DEV | VAL | WF | OOS)

CORRECTION HIERARCHY (declared here, applied in Phase 3)
  Campaign   : Benjamini-Hochberg at q over ALL primary tests (one per experiment x symbol:
               walk-forward OOS of the WF-selected config). Deflated Sharpe uses the campaign's
               TOTAL declared trials PLUS legacy trials already spent (never fewer).
  Experiment : PBO (CSCV) across the config grid; parameter-surface stability rule.
  Config     : intersection-union over the three nulls (timing, direction, circular shift):
               pass only if EVERY null p <= alpha (no correction needed; conservative).
  A config is PROMOTABLE only if all three levels pass AND the experiment's failure criteria
  do not fire. Nothing here computes a p-value: this module enforces WHAT may be computed,
  WHEN, and how it is counted.

STATE MACHINE (campaign)
  DRAFT -> FROZEN -> EVALUATION_OPEN (explicit approval note required) -> CLOSED
  Results are rejected unless the campaign is EVALUATION_OPEN, the run was declared by a
  frozen protocol, and (for OOS) it has not been evaluated before. BLOCKED experiments can
  never be evaluated.

STORAGE (append-only)
  <root>/protocols/<experiment>@v<version>.json   frozen protocol (immutable once written)
  <root>/campaigns/<campaign>.json                campaign manifest (state, trial budget)
  <root>/ledger.jsonl                             hash-chained event log (tamper-evident)
  <root>/results.jsonl                            recorded run results
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import os
from datetime import UTC, datetime

PERIODS = ("DEV", "VAL", "WF", "OOS")
STATES = ("DRAFT", "FROZEN", "EVALUATION_OPEN", "CLOSED", "REJECTED")
REQUIRED_PROTOCOL_KEYS = ("experiment", "version", "family", "hypothesis", "status", "symbols", "grid",
                          "periods", "data", "costs", "execution", "nulls", "tests", "failure_criteria",
                          "labels", "metrics")


class RegistryError(RuntimeError):
    """Raised on any attempt to break the protocol: never caught silently."""


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def protocol_hash(protocol: dict) -> str:
    body = {k: v for k, v in protocol.items() if k not in ("sha256", "frozen_utc")}
    return sha256_text(canonical_json(body))


def grid_configs(grid: dict) -> list[dict]:
    """Deterministic expansion of a grid {param: [values]} in sorted-key order."""
    keys = sorted(grid)
    return [dict(zip(keys, vals, strict=True)) for vals in itertools.product(*(grid[k] for k in keys))]


def config_id(cfg: dict) -> str:
    return sha256_text(canonical_json(cfg))[:12]


def declared_trials(protocol: dict) -> int:
    return len(grid_configs(protocol["grid"])) * len(protocol["symbols"])


def validate_protocol(p: dict) -> None:
    missing = [k for k in REQUIRED_PROTOCOL_KEYS if k not in p]
    if missing:
        raise RegistryError(f"protocol {p.get('experiment')} missing keys: {missing}")
    if p["status"] not in ("ACTIVE", "BLOCKED"):
        raise RegistryError("protocol status must be ACTIVE or BLOCKED")
    if p["status"] == "BLOCKED" and not p.get("blocked_reason"):
        raise RegistryError("a BLOCKED protocol must state blocked_reason")
    if not p["symbols"] or not p["grid"]:
        raise RegistryError("symbols and grid must be non-empty")
    for name, vals in p["grid"].items():
        if not isinstance(vals, list) or not vals:
            raise RegistryError(f"grid axis {name} must be a non-empty list")
    per = p["periods"]
    for k in ("DEV", "VAL", "OOS"):
        if k not in per:
            raise RegistryError(f"periods must define {k}")
    order = [per["DEV"][0], per["DEV"][1], per["VAL"][0], per["VAL"][1], per["OOS"][0], per["OOS"][1]]
    if order != sorted(order) or per["DEV"][1] >= per["VAL"][0] or per["VAL"][1] >= per["OOS"][0]:
        raise RegistryError("periods must be ordered and non-overlapping: DEV < VAL < OOS")
    t = p["tests"]
    for k in ("alpha", "fdr_q", "dsr_min", "pbo_max", "min_trades_report", "min_trades_promote"):
        if k not in t:
            raise RegistryError(f"tests must define {k}")
    if set(p["nulls"]) < {"timing", "direction", "circular_shift"}:
        raise RegistryError("the three mandatory nulls must be declared")
    canonical_json(p)          # raises on NaN/inf: frozen protocols must be exactly serialisable


class Registry:
    def __init__(self, root: str):
        self.root = root
        for sub in ("protocols", "campaigns"):
            os.makedirs(os.path.join(root, sub), exist_ok=True)
        self.ledger_path = os.path.join(root, "ledger.jsonl")
        self.results_path = os.path.join(root, "results.jsonl")

    # ------------------------------------------------------------ ledger
    def _ledger(self) -> list[dict]:
        if not os.path.exists(self.ledger_path):
            return []
        with open(self.ledger_path) as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def _append(self, event: str, payload: dict) -> dict:
        prev = self._ledger()
        prev_hash = prev[-1]["entry_sha256"] if prev else "GENESIS"
        entry = {"seq": len(prev), "utc": datetime.now(UTC).isoformat(timespec="seconds"),
                 "event": event, "payload": payload, "prev_sha256": prev_hash}
        entry["entry_sha256"] = sha256_text(canonical_json({k: v for k, v in entry.items() if k != "utc"}))
        with open(self.ledger_path, "a") as fh:
            fh.write(canonical_json(entry) + "\n")
        return entry

    def verify_ledger(self) -> bool:
        """True only if every entry's hash recomputes and each links to its predecessor."""
        prev = "GENESIS"
        for i, e in enumerate(self._ledger()):
            body = {k: v for k, v in e.items() if k not in ("utc", "entry_sha256")}
            if e["seq"] != i or e["prev_sha256"] != prev or sha256_text(canonical_json(body)) != e["entry_sha256"]:
                return False
            prev = e["entry_sha256"]
        return True

    # ------------------------------------------------------------ protocols
    def protocol_path(self, experiment: str, version: int) -> str:
        return os.path.join(self.root, "protocols", f"{experiment}@v{version}.json")

    def freeze_protocol(self, protocol: dict) -> dict:
        p = copy.deepcopy(protocol)
        validate_protocol(p)
        h = protocol_hash(p)
        path = self.protocol_path(p["experiment"], p["version"])
        if os.path.exists(path):
            with open(path) as fh:
                existing = json.load(fh)
            if existing["sha256"] != h:
                raise RegistryError(f"{path} is frozen with a different hash; bump 'version' to change it")
            return existing
        p["sha256"] = h
        p["frozen_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
        with open(path, "w") as fh:
            json.dump(p, fh, indent=1, sort_keys=True)
        self._append("PROTOCOL_FROZEN", {"experiment": p["experiment"], "version": p["version"], "sha256": h,
                                         "status": p["status"], "declared_trials": declared_trials(p)})
        return p

    def load_protocol(self, experiment: str, version: int) -> dict:
        with open(self.protocol_path(experiment, version)) as fh:
            p = json.load(fh)
        if protocol_hash(p) != p["sha256"]:
            raise RegistryError(f"protocol {experiment}@v{version} was modified after freezing")
        return p

    # ------------------------------------------------------------ campaigns
    def campaign_path(self, name: str) -> str:
        return os.path.join(self.root, "campaigns", f"{name}.json")

    def _write_campaign(self, c: dict) -> None:
        with open(self.campaign_path(c["campaign"]), "w") as fh:
            json.dump(c, fh, indent=1, sort_keys=True)

    def load_campaign(self, name: str) -> dict:
        with open(self.campaign_path(name)) as fh:
            return json.load(fh)

    def create_campaign(self, name: str, experiments: list[tuple[str, int]], legacy_trials: int,
                        correction: dict) -> dict:
        if os.path.exists(self.campaign_path(name)):
            raise RegistryError(f"campaign {name} already exists")
        protos = [self.load_protocol(e, v) for e, v in experiments]
        c = {"campaign": name, "state": "DRAFT", "legacy_trials": int(legacy_trials), "correction": correction,
             "experiments": [{"experiment": p["experiment"], "version": p["version"], "sha256": p["sha256"],
                              "status": p["status"], "declared_trials": declared_trials(p)} for p in protos]}
        active = [e for e in c["experiments"] if e["status"] == "ACTIVE"]
        c["declared_trials_active"] = sum(e["declared_trials"] for e in active)
        c["dsr_trial_count"] = c["declared_trials_active"] + c["legacy_trials"]
        c["primary_tests"] = sum(len(self.load_protocol(e["experiment"], e["version"])["symbols"]) for e in active)
        self._write_campaign(c)
        self._append("CAMPAIGN_CREATED", {k: c[k] for k in ("campaign", "legacy_trials", "declared_trials_active",
                                                            "dsr_trial_count", "primary_tests")})
        return c

    def freeze_campaign(self, name: str) -> dict:
        c = self.load_campaign(name)
        if c["state"] != "DRAFT":
            raise RegistryError(f"campaign {name} is {c['state']}, not DRAFT")
        for e in c["experiments"]:                       # every protocol still matches its frozen hash
            if self.load_protocol(e["experiment"], e["version"])["sha256"] != e["sha256"]:
                raise RegistryError(f"{e['experiment']} hash changed")
        body = {k: v for k, v in c.items() if k not in ("state", "sha256")}
        c["sha256"] = sha256_text(canonical_json(body))
        c["state"] = "FROZEN"
        self._write_campaign(c)
        self._append("CAMPAIGN_FROZEN", {"campaign": name, "sha256": c["sha256"]})
        return c

    def reject_campaign(self, name: str, reason: str) -> dict:
        """Permanently reject a campaign (append-only; REJECTED can never be opened)."""
        c = self.load_campaign(name)
        if c["state"] == "EVALUATION_OPEN":
            raise RegistryError("an open campaign must be closed, not rejected")
        if not reason or len(reason.strip()) < 10:
            raise RegistryError("rejection requires a reason")
        c["state"] = "REJECTED"
        c["rejection_reason"] = reason
        self._write_campaign(c)
        self._append("CAMPAIGN_REJECTED", {"campaign": name, "reason": reason})
        return c

    def open_evaluation(self, name: str, approval_note: str) -> dict:
        c = self.load_campaign(name)
        if c["state"] != "FROZEN":
            raise RegistryError(f"campaign must be FROZEN before evaluation (is {c['state']})")
        if not approval_note or len(approval_note.strip()) < 10:
            raise RegistryError("opening evaluation requires an explicit human approval note")
        c["state"] = "EVALUATION_OPEN"
        c["approval_note"] = approval_note
        self._write_campaign(c)
        self._append("EVALUATION_OPENED", {"campaign": name, "approval_note": approval_note})
        return c

    # ------------------------------------------------------------ results
    def _results(self) -> list[dict]:
        if not os.path.exists(self.results_path):
            return []
        with open(self.results_path) as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def record_result(self, campaign: str, experiment: str, cfg: dict, symbol: str, period: str,
                      metrics: dict) -> dict:
        c = self.load_campaign(campaign)
        if c["state"] != "EVALUATION_OPEN":
            raise RegistryError(f"campaign {campaign} is {c['state']}: evaluation not permitted")
        entry = next((e for e in c["experiments"] if e["experiment"] == experiment), None)
        if entry is None:
            raise RegistryError(f"{experiment} is not part of campaign {campaign}")
        if entry["status"] == "BLOCKED":
            raise RegistryError(f"{experiment} is BLOCKED and cannot be evaluated")
        p = self.load_protocol(experiment, entry["version"])
        if symbol not in p["symbols"]:
            raise RegistryError(f"{symbol} not declared by {experiment}")
        if period not in PERIODS:
            raise RegistryError(f"unknown period {period}")
        cid = config_id(cfg)
        if cid not in {config_id(x) for x in grid_configs(p["grid"])}:
            raise RegistryError(f"config {cfg} was not pre-declared by {experiment}")
        if period == "OOS" and any(r["experiment"] == experiment and r["config_id"] == cid and
                                   r["symbol"] == symbol and r["period"] == "OOS" for r in self._results()):
            raise RegistryError("OOS for this config/symbol was already evaluated: OOS is one-shot")
        row = {"campaign": campaign, "experiment": experiment, "protocol_sha256": p["sha256"], "config_id": cid,
               "config": cfg, "symbol": symbol, "period": period, "metrics": metrics,
               "utc": datetime.now(UTC).isoformat(timespec="seconds")}
        with open(self.results_path, "a") as fh:
            fh.write(canonical_json(row) + "\n")
        self._append("RESULT_RECORDED", {k: row[k] for k in ("campaign", "experiment", "config_id", "symbol", "period")})
        return row
