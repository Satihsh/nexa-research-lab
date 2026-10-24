"""NEXA experiment registry V2: externally anchored, fail-closed.

Threat model: accidental misuse and post-hoc tampering (editing protocols, campaign, trial
counts, dates, data or code after freezing; re-querying validation; reusing OOS). Every public
call re-verifies EVERYTHING and raises RegistryError on any mismatch. Nothing is repaired.

EXTERNAL ANCHOR
  The campaign hash is returned once at freeze and must be held OUTSIDE the registry (chat,
  PROGRESS.md, a git tag). Every call takes it as `anchor`. The registry never trusts a hash
  stored next to the thing it describes:
    campaign.json body       -> sha256 must equal `anchor`
    protocol files           -> sha256 must equal campaign.pins.protocols[exp]
    trial_universe.json      -> sha256 must equal campaign.pins.trial_universe_sha256, and must
                                equal the universe re-derived from the pinned protocols
    data / code / design     -> sha256 of each file must equal its pin
    ledger.jsonl             -> hash chain intact; CAMPAIGN_FROZEN payload == anchor;
                                every results.jsonl row hash appears in the ledger, in order
    external witness         -> an append-only head log kept OUTSIDE the registry and the repo
                                (default ~/.nexa_registry_witness/<anchor>.jsonl). Every ledger
                                entry is mirrored there; the ledger must equal the witness entry for
                                entry. Tail truncation (e.g. to reset a VAL budget) or appends made
                                outside this API fail closed.
    external CHECKPOINT      -> R1 control. An actor with write access to this machine can rewrite
                                BOTH the ledger and the witness consistently; local hashes cannot
                                stop that. Therefore every MUTATING call requires `checkpoint` =
                                {"seq", "entry_sha256"} of the ledger head as last PUBLISHED OFF this
                                machine (compare-and-swap), and verify(anchor, checkpoint) pins the
                                ledger to it: a rolled-back ledger no longer contains the checkpoint,
                                and a ledger extended without publication has entries beyond it.
                                Each mutation returns its ledger entry; its (seq, entry_sha256) must be
                                published off-machine before the next call (see
                                research/reports/V2_EXTERNAL_CHECKPOINT_PROCEDURE.md).

STATE (derived from the ledger only; campaign.json never changes after freeze)
  FROZEN -> OPEN (explicit approval note) ; REJECTED is terminal.

EVALUATION RULES (enforced in record/select; UTC everywhere)
  * trial must be in the pinned universe (grid x sensitivity x symbol x claim); ACTIVE only
  * result window must lie inside the declared period, start >= period start + embargo, and
    every label must end <= period end (purge). OOS dates cannot be recorded under DEV/VAL/WF.
  * VAL: at most ONE result per trial. WF: at most one per trial per WF year.
  * OOS selection: exactly one trial per (experiment, claim, symbol), sealed BEFORE the OOS
    start. From the OOS start onward no DEV/VAL/WF result and no selection is accepted.
  * OOS: only the sealed trial, only the full pinned OOS window, only after it has ended,
    at most once per (experiment, claim, symbol). OOS can never feed a later selection.
  * data_set_sha / code_set_sha declared by the result must equal the pinned digests.
  * every builder used must hold a passing causality certificate recorded in the ledger
    BEFORE opening, for its exact source hash (function + defining module). The registry runs
    nexa_causality.certify / certify_events ITSELF (callers pass the function, never a
    certificate), and results name builders by function, whose source hash the registry computes.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
from datetime import UTC, datetime, timedelta

import nexa_causality

ROOT_MARKER = "NEXA_EA.mq5"          # data/code paths are relative to the NEXA root
PERIOD_NAMES = ("DEV", "VAL", "WF", "OOS")
DEFAULT_WITNESS = os.path.join(os.path.expanduser("~"), ".nexa_registry_witness")
MIN_CERT_ROWS = 500
MIN_EVENT_CERT_ROWS = 200


class RegistryError(RuntimeError):
    pass


def _utcnow() -> datetime:
    """Single clock for the registry (tests monkeypatch this; production never injects time)."""
    return datetime.now(UTC)


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _norm(v):
    """Canonical scalar: integral floats become ints so 1 and 1.0 are the SAME trial."""
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        f = float(v)
        return int(f) if f.is_integer() else round(f, 12)
    raise RegistryError(f"unsupported config value {v!r}")


def normalize_config(cfg: dict) -> dict:
    return {k: _norm(cfg[k]) for k in sorted(cfg)}


def trial_id(experiment: str, claim: str, symbol: str, cfg: dict) -> str:
    return sha256_text(canonical_json({"e": experiment, "c": claim, "s": symbol, "cfg": normalize_config(cfg)}))[:20]


def parse_utc(s: str) -> datetime:
    if not isinstance(s, str) or not s.endswith("Z"):
        raise RegistryError(f"timestamps must be explicit UTC ISO-8601 ending in 'Z': {s!r}")
    try:
        dt = datetime.fromisoformat(s[:-1])
    except ValueError as exc:
        raise RegistryError(f"unparseable UTC timestamp {s!r}") from exc
    if dt.tzinfo is not None:
        raise RegistryError(f"timestamp carries an offset as well as 'Z': {s!r}")
    return dt.replace(tzinfo=UTC)


# ---------------------------------------------------------------- protocol + universe

REQUIRED = ("experiment", "version", "status", "family", "hypothesis", "claims", "grid", "sensitivity", "symbols",
            "periods_utc", "purge_embargo", "timezone", "leakage_rules", "costs", "execution", "nulls", "tests")


def validate_protocol(p: dict) -> None:
    miss = [k for k in REQUIRED if k not in p]
    if miss:
        raise RegistryError(f"{p.get('experiment')}: missing {miss}")
    if p["status"] not in ("ACTIVE", "BLOCKED"):
        raise RegistryError("status must be ACTIVE or BLOCKED")
    if p["status"] == "BLOCKED" and not p.get("blocked_reason"):
        raise RegistryError("BLOCKED requires blocked_reason")
    axes = {**p["grid"], **p["sensitivity"]}
    if set(p["grid"]) & set(p["sensitivity"]):
        raise RegistryError("an axis cannot be both grid and sensitivity")
    for name, vals in axes.items():
        if not isinstance(vals, list) or not vals or len({canonical_json(_norm(v)) for v in vals}) != len(vals):
            raise RegistryError(f"axis {name}: non-empty list of distinct values required")
    for cid, c in p["claims"].items():
        if not set(c["params"]) <= set(axes):
            raise RegistryError(f"claim {cid} uses undeclared axes")
    per = p["periods_utc"]
    for k in ("DEV", "VAL", "OOS"):
        a, b = parse_utc(per[k][0]), parse_utc(per[k][1])
        if not a < b:
            raise RegistryError(f"period {k} empty")
    if not (parse_utc(per["DEV"][1]) <= parse_utc(per["VAL"][0]) and parse_utc(per["VAL"][1]) <= parse_utc(per["OOS"][0])):
        raise RegistryError("periods must be ordered DEV < VAL < OOS")
    pe = p["purge_embargo"]
    if not (isinstance(pe.get("max_label_minutes"), int) and pe["max_label_minutes"] > 0
            and isinstance(pe.get("embargo_minutes"), int) and pe["embargo_minutes"] >= pe["max_label_minutes"]):
        raise RegistryError("purge_embargo: embargo_minutes must be >= max_label_minutes > 0")
    if p["timezone"].get("period_bounds") != "UTC":
        raise RegistryError("period bounds must be declared in UTC")
    if set(p["nulls"]) < {"timing", "direction", "circular_shift"}:
        raise RegistryError("the three mandatory nulls are required")
    for k in ("alpha", "fdr_q", "dsr_min", "pbo_max", "min_trades_promote", "val_queries_per_trial"):
        if k not in p["tests"]:
            raise RegistryError(f"tests.{k} required")
    canonical_json(p)


def protocol_sha(p: dict) -> str:
    return sha256_text(canonical_json(p))


def derive_universe(protocols: list[dict]) -> list[dict]:
    """Every (experiment, claim, symbol, config) of every ACTIVE protocol. Axes a claim does
    not depend on are NOT enumerated for it (no duplicate trials)."""
    out = []
    for p in sorted(protocols, key=lambda x: x["experiment"]):
        if p["status"] != "ACTIVE":
            continue
        axes = {**p["grid"], **p["sensitivity"]}
        for cid in sorted(p["claims"]):
            names = sorted(p["claims"][cid]["params"])
            for vals in itertools.product(*(axes[n] for n in names)):
                cfg = normalize_config(dict(zip(names, vals, strict=True)))
                for sym in p["symbols"]:
                    out.append({"experiment": p["experiment"], "claim": cid, "symbol": sym, "config": cfg,
                                "primary_claim": bool(p["claims"][cid]["primary"]),
                                "trial_id": trial_id(p["experiment"], cid, sym, cfg)})
    ids = [t["trial_id"] for t in out]
    if len(ids) != len(set(ids)):
        raise RegistryError("duplicate trial ids in universe")
    return out


# ---------------------------------------------------------------- registry

class RegistryV2:
    def __init__(self, root: str, nexa_root: str | None = None, witness_dir: str | None = None):
        self.root = root
        self.nexa_root = nexa_root or self._find_nexa_root(root)
        self.witness_dir = witness_dir or DEFAULT_WITNESS
        self._anchor: str | None = None
        self.ledger_path = os.path.join(root, "ledger.jsonl")
        self.results_path = os.path.join(root, "results.jsonl")
        self.campaign_path = os.path.join(root, "campaign.json")
        self.universe_path = os.path.join(root, "trial_universe.json")

    @staticmethod
    def _find_nexa_root(start: str) -> str:
        d = os.path.abspath(start)
        while d != os.path.dirname(d):
            if os.path.exists(os.path.join(d, ROOT_MARKER)):
                return d
            d = os.path.dirname(d)
        raise RegistryError("NEXA root not found above the registry")

    def protocol_path(self, exp: str, ver: int) -> str:
        return os.path.join(self.root, "protocols", f"{exp}@v{ver}.json")

    # ------------------------------------------------------------ ledger
    @staticmethod
    def _read_jsonl(path: str, what: str) -> list[dict]:
        if not os.path.exists(path):
            return []
        try:
            with open(path) as fh:
                rows = [json.loads(x) for x in fh if x.strip()]
        except (OSError, ValueError) as exc:
            raise RegistryError(f"{what} unreadable: {exc}") from exc
        if not all(isinstance(r, dict) for r in rows):
            raise RegistryError(f"{what} contains a non-object row")
        return rows

    def _ledger(self) -> list[dict]:
        return self._read_jsonl(self.ledger_path, "ledger")

    def witness_path(self, anchor: str) -> str:
        return os.path.join(self.witness_dir, f"{anchor}.jsonl")

    def _append(self, event: str, payload: dict) -> dict:
        if self._anchor is None:
            raise RegistryError("internal: append without a verified anchor")
        led = self._ledger()
        prev = led[-1]["entry_sha256"] if led else "GENESIS"
        e = {"seq": len(led), "utc": _utcnow().isoformat(timespec="seconds"), "event": event, "payload": payload,
             "prev_sha256": prev}
        e["entry_sha256"] = sha256_text(canonical_json(e))
        os.makedirs(self.witness_dir, exist_ok=True)
        with open(self.witness_path(self._anchor), "a") as fh:          # witness first: a crash leaves it AHEAD -> fail closed
            fh.write(canonical_json({"seq": e["seq"], "entry_sha256": e["entry_sha256"]}) + "\n")
        with open(self.ledger_path, "a") as fh:
            fh.write(canonical_json(e) + "\n")
        return e

    def _check_ledger(self, anchor: str) -> list[dict]:
        led = self._ledger()
        prev = "GENESIS"
        try:
            for i, e in enumerate(led):
                body = {k: v for k, v in e.items() if k != "entry_sha256"}
                if e["seq"] != i or e["prev_sha256"] != prev or sha256_text(canonical_json(body)) != e["entry_sha256"]:
                    raise RegistryError(f"ledger broken at entry {i}")
                prev = e["entry_sha256"]
            frozen = [e for e in led if e["event"] == "CAMPAIGN_FROZEN"]
            if len(frozen) != 1 or frozen[0]["payload"]["campaign_sha256"] != anchor:
                raise RegistryError("ledger does not record exactly one CAMPAIGN_FROZEN for this anchor")
            wit = self._read_jsonl(self.witness_path(anchor), "witness")
            if not wit:
                raise RegistryError("external witness missing for this anchor")
            if len(wit) != len(led) or any(w["seq"] != i or w["entry_sha256"] != led[i]["entry_sha256"]
                                           for i, w in enumerate(wit)):
                raise RegistryError(f"ledger ({len(led)} entries) disagrees with the external witness "
                                    f"({len(wit)} entries): truncation, rollback or out-of-API append")
        except (KeyError, TypeError, IndexError) as exc:
            raise RegistryError(f"ledger/witness malformed: {exc!r}") from exc
        return led

    # ------------------------------------------------------------ build + freeze (once)
    def create_and_freeze(self, name: str, protocols: list[dict], pins: dict, legacy_trials: int,
                          correction: dict, notes: dict) -> str:
        if os.path.exists(self.campaign_path):
            raise RegistryError("campaign already exists in this registry root")
        os.makedirs(os.path.join(self.root, "protocols"), exist_ok=True)
        psha = {}
        for p in protocols:
            validate_protocol(p)
            path = self.protocol_path(p["experiment"], p["version"])
            with open(path, "w") as fh:
                fh.write(canonical_json(p))
            psha[p["experiment"]] = protocol_sha(p)
        universe = derive_universe(protocols)
        with open(self.universe_path, "w") as fh:
            fh.write(canonical_json(universe))
        active = [p for p in protocols if p["status"] == "ACTIVE"]
        primary = sorted({(t["experiment"], t["claim"], t["symbol"]) for t in universe if t["primary_claim"]})
        body = {"campaign": name, "created_utc": _utcnow().isoformat(timespec="seconds"),
                "experiments": {p["experiment"]: {"version": p["version"], "status": p["status"]} for p in protocols},
                "pins": {"protocols": psha, "trial_universe_sha256": sha256_file(self.universe_path), **pins},
                "trial_counts": {"active_trials": len(universe), "legacy_trials": int(legacy_trials),
                                 "dsr_trial_count": len(universe) + int(legacy_trials),
                                 "by_experiment": {p["experiment"]: sum(1 for t in universe if t["experiment"] == p["experiment"])
                                                   for p in active},
                                 "primary_tests": len(primary),
                                 "primary_tests_list": [list(x) for x in primary]},
                "correction": correction, "notes": notes}
        text = canonical_json(body)
        with open(self.campaign_path, "w") as fh:
            fh.write(text)
        anchor = sha256_text(text)
        if os.path.exists(self.witness_path(anchor)):
            raise RegistryError("a witness for this anchor already exists")
        self._anchor = anchor
        with open(os.path.join(self.root, "ANCHOR.txt"), "w") as fh:
            fh.write(anchor + "\n")          # convenience copy only; callers must hold the anchor externally
        self._append("CAMPAIGN_FROZEN", {"campaign": name, "campaign_sha256": anchor})
        self.verify(anchor)
        return anchor

    # ------------------------------------------------------------ external checkpoint (R1)
    @staticmethod
    def head_of(led: list[dict]) -> dict:
        return {"seq": led[-1]["seq"], "entry_sha256": led[-1]["entry_sha256"]}

    @staticmethod
    def _check_checkpoint(led: list[dict], checkpoint) -> None:
        if not isinstance(checkpoint, dict) or set(checkpoint) != {"seq", "entry_sha256"}:
            raise RegistryError("an external checkpoint {seq, entry_sha256} of the published ledger head is required")
        seq = checkpoint["seq"]
        if (not isinstance(seq, int) or isinstance(seq, bool) or seq < 0 or seq >= len(led)
                or led[seq]["entry_sha256"] != checkpoint["entry_sha256"]):
            raise RegistryError("external checkpoint not found in the local ledger: rollback or rewrite")
        if seq != len(led) - 1:
            raise RegistryError("local ledger has entries beyond the external checkpoint: unpublished or forged events")

    def checkpoint_line(self, anchor: str, checkpoint=None) -> str:
        v = self.verify(anchor, checkpoint=checkpoint)
        h = self.head_of(v["ledger"])
        return (f"NEXA-CHECKPOINT campaign={v['campaign']['campaign']} anchor={anchor} seq={h['seq']} "
                f"head={h['entry_sha256']} state={self.state(v['ledger'])}")

    def _mutable(self, anchor: str, checkpoint) -> dict:
        return self.verify(anchor, checkpoint=checkpoint, _require_checkpoint=True)

    # ------------------------------------------------------------ verification
    def verify(self, anchor: str, checkpoint=None, _require_checkpoint: bool = False) -> dict:
        if not os.path.exists(self.campaign_path):
            raise RegistryError("no campaign")
        with open(self.campaign_path) as fh:
            text = fh.read()
        if sha256_text(text) != anchor:
            raise RegistryError("campaign.json does not match the external anchor")
        c = json.loads(text)
        led = self._check_ledger(anchor)
        if checkpoint is not None or _require_checkpoint:
            self._check_checkpoint(led, checkpoint)
        self._anchor = anchor
        protos = []
        try:
            for exp, meta in c["experiments"].items():
                path = self.protocol_path(exp, meta["version"])
                with open(path) as fh:
                    p = json.load(fh)
                if protocol_sha(p) != c["pins"]["protocols"][exp]:
                    raise RegistryError(f"protocol {exp} does not match the campaign pin")
                protos.append(p)
            if sha256_file(self.universe_path) != c["pins"]["trial_universe_sha256"]:
                raise RegistryError("trial universe file does not match its pin")
            with open(self.universe_path) as fh:
                universe = json.load(fh)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise RegistryError(f"registry state unreadable or incomplete: {exc!r}") from exc
        if canonical_json(universe) != canonical_json(derive_universe(protos)):
            raise RegistryError("trial universe does not match the pinned protocols")
        for group in ("data", "code", "design_artifacts"):
            for key, pin in c["pins"].get(group, {}).items():
                path = os.path.join(self.nexa_root, pin["path"])
                try:
                    ok = os.path.isfile(path) and sha256_file(path) == pin["sha256"]
                except OSError:
                    ok = False
                if not ok:
                    raise RegistryError(f"pinned {group} '{key}' changed or missing: {pin['path']}")
        res = self._results()
        chained = [e["payload"]["result_sha256"] for e in led if e["event"] == "RESULT_RECORDED"]
        if [sha256_text(canonical_json(r)) for r in res] != chained:
            raise RegistryError("results.jsonl does not match the ledger")
        return {"campaign": c, "protocols": {p["experiment"]: p for p in protos},
                "universe": {t["trial_id"]: t for t in universe}, "ledger": led}

    @staticmethod
    def state(led: list[dict]) -> str:
        ev = [e["event"] for e in led]
        if "CAMPAIGN_REJECTED" in ev:
            return "REJECTED"
        if "EVALUATION_OPENED" in ev:
            return "OPEN"
        return "FROZEN"

    @staticmethod
    def digest(pins: dict) -> str:
        return sha256_text(canonical_json({k: v["sha256"] for k, v in sorted(pins.items())}))

    def _results(self) -> list[dict]:
        return self._read_jsonl(self.results_path, "results")

    # ------------------------------------------------------------ pre-open actions
    def _register(self, anchor: str, checkpoint, builder, run, data_sha: str) -> dict:
        v = self._mutable(anchor, checkpoint)
        if self.state(v["ledger"]) != "FROZEN":
            raise RegistryError("builders can only be registered while FROZEN (before opening)")
        if not callable(builder):
            raise RegistryError("register_builder takes the builder function, not a certificate")
        try:
            certificate = run()
        except Exception as exc:  # any certification error = not certified (fail closed)
            raise RegistryError(f"certification error: {exc!r}") from exc
        if not certificate.get("passed"):
            raise RegistryError(f"builder {certificate.get('builder')} FAILED causality certification")
        return self._append("BUILDER_CERTIFIED", {"builder": certificate["builder"], "kind": certificate["kind"],
                                                  "source_sha256": certificate["source_sha256"],
                                                  "perturbed": certificate["perturbed"],
                                                  "certification_input_sha256": data_sha,
                                                  "certificate_sha256": sha256_text(canonical_json(certificate))})

    @staticmethod
    def _frame_sha(df) -> str:
        import pandas as pd
        return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes()).hexdigest()

    def register_builder(self, anchor: str, builder, bars, *, checkpoint, extra_cols: tuple = ()) -> dict:
        """Certify a bar builder HERE (a caller-supplied certificate is never trusted). extra_cols:
        time-stamped input columns that must also be perturbed (e.g. merged release values)."""
        if not callable(builder):
            raise RegistryError("register_builder takes the builder function, not a certificate")
        if not hasattr(bars, "columns") or len(bars) < MIN_CERT_ROWS:
            raise RegistryError(f"certification needs >= {MIN_CERT_ROWS} bars")
        return self._register(anchor, checkpoint, builder,
                              lambda: nexa_causality.certify(builder, bars, extra_cols=tuple(extra_cols)),
                              self._frame_sha(bars))

    def register_event_builder(self, anchor: str, builder, table, time_col: str, perturb_cols: tuple,
                               check_cols: tuple, *, checkpoint) -> dict:
        """Certify an event-table builder (e.g. calendar prior-only baselines) HERE."""
        if not callable(builder):
            raise RegistryError("register_event_builder takes the builder function, not a certificate")
        if not hasattr(table, "columns") or len(table) < MIN_EVENT_CERT_ROWS:
            raise RegistryError(f"event certification needs >= {MIN_EVENT_CERT_ROWS} rows")
        if not check_cols or not perturb_cols:
            raise RegistryError("event certification needs perturbed and checked columns")
        return self._register(anchor, checkpoint, builder,
                              lambda: nexa_causality.certify_events(builder, table, time_col, tuple(perturb_cols),
                                                                    tuple(check_cols)),
                              self._frame_sha(table))

    def open_evaluation(self, anchor: str, approval_note: str, *, checkpoint) -> dict:
        v = self._mutable(anchor, checkpoint)
        if self.state(v["ledger"]) != "FROZEN":
            raise RegistryError(f"cannot open from state {self.state(v['ledger'])}")
        if not approval_note or len(approval_note.strip()) < 20:
            raise RegistryError("opening requires an explicit human approval note")
        return self._append("EVALUATION_OPENED", {"approval_note": approval_note,
                                                  "sealed_ledger_head": v["ledger"][-1]["entry_sha256"]})

    def reject(self, anchor: str, reason: str, *, checkpoint) -> dict:
        v = self._mutable(anchor, checkpoint)
        if self.state(v["ledger"]) == "REJECTED":
            raise RegistryError("already rejected")
        return self._append("CAMPAIGN_REJECTED", {"reason": reason})

    # ------------------------------------------------------------ evaluation
    def _group(self, t: dict) -> tuple:
        return (t["experiment"], t["claim"], t["symbol"])

    def select_for_oos(self, anchor: str, tid: str, rationale: str, *, checkpoint) -> dict:
        v = self._mutable(anchor, checkpoint)
        led = v["ledger"]
        if self.state(led) != "OPEN":
            raise RegistryError("evaluation is not open")
        t = v["universe"].get(tid)
        if t is None:
            raise RegistryError("trial not in the pinned universe")
        p = v["protocols"][t["experiment"]]
        if _utcnow() >= parse_utc(p["periods_utc"]["OOS"][0]):
            raise RegistryError("OOS selection must be sealed BEFORE the OOS start")
        g = self._group(t)
        for e in led:
            if e["event"] == "OOS_SELECTED" and tuple(e["payload"]["group"]) == g:
                raise RegistryError("an OOS selection already exists for this experiment/claim/symbol")
        if not any(r["trial_id"] == tid and r["period"] == "VAL" for r in self._results()):
            raise RegistryError("a selected trial must have its (single) VAL result recorded first")
        return self._append("OOS_SELECTED", {"group": list(g), "trial_id": tid, "rationale": rationale})

    def record(self, anchor: str, tid: str, period: str, window_utc: list, first_entry_utc: str, max_label_end_utc: str,
               data_set_sha: str, code_set_sha: str, builders: list, metrics: dict,
               wf_year: int | None = None, *, checkpoint) -> dict:
        v = self._mutable(anchor, checkpoint)
        led, c = v["ledger"], v["campaign"]
        if self.state(led) != "OPEN":
            raise RegistryError(f"evaluation not permitted in state {self.state(led)}")
        if (not isinstance(window_utc, (list, tuple)) or len(window_utc) != 2
                or not all(isinstance(x, str) for x in (*window_utc, first_entry_utc, max_label_end_utc))):
            raise RegistryError("window_utc must be [start, end] and all timestamps explicit UTC strings")
        if not isinstance(metrics, dict):
            raise RegistryError("metrics must be a dict")
        t = v["universe"].get(tid)
        if t is None:
            raise RegistryError("trial not in the pinned universe (unregistered config/sensitivity/symbol)")
        p = v["protocols"][t["experiment"]]
        if p["status"] != "ACTIVE":
            raise RegistryError("experiment is BLOCKED")
        if period not in PERIOD_NAMES:
            raise RegistryError(f"unknown period {period}")
        if data_set_sha != self.digest(c["pins"]["data"]) or code_set_sha != self.digest(c["pins"]["code"]):
            raise RegistryError("result is not bound to the pinned data/code set")
        certified = {e["payload"]["source_sha256"] for e in led if e["event"] == "BUILDER_CERTIFIED"
                     and e["seq"] < next(x["seq"] for x in led if x["event"] == "EVALUATION_OPENED")}
        if not builders or not all(callable(b) for b in builders):
            raise RegistryError("results must name their builders as functions (source hash computed here)")
        builder_source_shas = [nexa_causality.source_sha256(b) for b in builders]
        if not set(builder_source_shas) <= certified:
            raise RegistryError("every builder must hold a causality certificate registered before opening")
        # ---- dates, purge, embargo (UTC)
        per = p["periods_utc"]
        ws, we = parse_utc(window_utc[0]), parse_utc(window_utc[1])
        fe, le = parse_utc(first_entry_utc), parse_utc(max_label_end_utc)
        if period == "WF":
            if wf_year not in per["WF_YEARS"]:
                raise RegistryError(f"wf_year {wf_year!r} is not one of the pinned WF_YEARS {per['WF_YEARS']}")
            ps, pe = parse_utc(f"{wf_year}-01-01T00:00:00Z"), parse_utc(f"{wf_year + 1}-01-01T00:00:00Z")
            if not (parse_utc(per["DEV"][0]) <= ps and pe <= parse_utc(per["VAL"][1])):
                raise RegistryError("WF year outside DEV..VAL")
        else:
            ps, pe = parse_utc(per[period][0]), parse_utc(per[period][1])
        emb = timedelta(minutes=p["purge_embargo"]["embargo_minutes"])
        if not (ps <= ws < we <= pe):
            raise RegistryError(f"window {window_utc} lies outside the {period} bounds")
        if fe < ws or fe < ps + (emb if period != "DEV" else timedelta(0)):
            raise RegistryError(f"first entry {first_entry_utc} violates the {period} embargo")
        if le > we or le > pe:
            raise RegistryError("a label ends after the window/period end (purge violation)")
        # ---- selection discipline
        g = self._group(t)
        results = self._results()
        sel = [e for e in led if e["event"] == "OOS_SELECTED" and tuple(e["payload"]["group"]) == g]
        oos_start = parse_utc(per["OOS"][0])
        if period in ("DEV", "VAL", "WF"):
            if _utcnow() >= oos_start:
                raise RegistryError("in-sample results are closed once the OOS period has started")
            if sel:
                raise RegistryError("selection for this group is sealed; no further in-sample results")
            if period == "VAL" and any(r["trial_id"] == tid and r["period"] == "VAL" for r in results):
                raise RegistryError("this trial's validation has already been queried (budget = 1)")
            if period == "WF" and any(r["trial_id"] == tid and r["period"] == "WF" and r.get("wf_year") == wf_year
                                      for r in results):
                raise RegistryError("this trial's WF year was already recorded")
        else:
            if not sel or sel[0]["payload"]["trial_id"] != tid:
                raise RegistryError("OOS is only for the trial sealed by OOS_SELECTED")
            if any(r["period"] == "OOS" and tuple(r["group"]) == g for r in results):
                raise RegistryError("OOS already observed for this experiment/claim/symbol")
            if [window_utc[0], window_utc[1]] != per["OOS"] or _utcnow() < parse_utc(per["OOS"][1]):
                raise RegistryError("OOS must cover the full pinned window and can only be recorded after it ends")
        row = {"trial_id": tid, "group": list(g), "period": period, "wf_year": wf_year, "window_utc": list(window_utc),
               "first_entry_utc": first_entry_utc, "max_label_end_utc": max_label_end_utc, "data_set_sha": data_set_sha, "code_set_sha": code_set_sha,
               "builders": sorted(builder_source_shas), "metrics": metrics,
               "utc": _utcnow().isoformat(timespec="seconds")}
        with open(self.results_path, "a") as fh:
            fh.write(canonical_json(row) + "\n")
        return self._append("RESULT_RECORDED", {"trial_id": tid, "period": period,
                                                "result_sha256": sha256_text(canonical_json(row))})
