"""ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE (D-PARTIAL-AFTER-BE fix, 2026-10-03).

Compares the PRE-fix and FIXED EA runs written by run_engfix_regression.sh (GBPUSD, production inputs,
$200 deposit, twelve windows) and checks the end-to-end requirements a decision-level harness cannot:
partial closes really happen after breakeven, exactly once per trade, journaled correctly (Trade DNA
PARTIAL_CLOSE + whole-position CLOSE result_r), the balance reconciles to the cent with partial legs,
the Python ingest accepts the journal, and nothing changes for trades that never reach the partial /
the time exit. No edge statistic is computed.

    python research/engfix/engfix_regression.py      # writes research/engfix/regression/regression_evidence.json
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.dirname(HERE)
ROOT = os.path.dirname(RESEARCH)
for p in (RESEARCH, os.path.join(RESEARCH, "capneutral")):
    if p not in sys.path:
        sys.path.insert(0, p)

import capn_analysis as CA  # read-only reuse of the pairing / reconciliation code

import nexa_ingest

REG = os.path.join(HERE, "regression")
SYM = "GBPUSD"
CMP_COLS = ["event", "decision_ts", "fill_ts", "direction", "entry_intended", "entry_actual", "sl_price", "tp_price",
            "target_r", "risk_dist", "lots", "commission", "swap", "result_r", "reason"]
R_TOL_REL, R_TOL_ABS = 0.03, 0.01      # DNA prints risk_dist / prices at 5 dp; the EA's R uses unrounded values


def sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def dna_path(run_dir: str) -> str:
    """dna.csv, or a temporary decompressed copy of dna.csv.gz (the logs were compressed losslessly on
    2026-10-03; see regression/DNA_COMPRESSION_MANIFEST.json). Temporary copies live in the system temp dir."""
    plain = os.path.join(run_dir, "dna.csv")
    if os.path.exists(plain):
        return plain
    tmp = os.path.join(tempfile.gettempdir(), "engfix_" + os.path.basename(run_dir) + "_dna.csv")
    if not os.path.exists(tmp):
        with gzip.open(plain + ".gz", "rb") as src, open(tmp, "wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
    return tmp


def execution_rows(path: str) -> pd.DataFrame:
    d = pd.read_csv(path, dtype=str, keep_default_na=False)
    return d[d["event"] != "DECISION"].reset_index(drop=True)


def first_divergence(pre: str, post: str) -> dict:
    a = pd.read_csv(pre, dtype=str, keep_default_na=False, usecols=CMP_COLS)
    b = pd.read_csv(post, dtype=str, keep_default_na=False, usecols=CMP_COLS)
    n = min(len(a), len(b))
    diff = np.nonzero((a.iloc[:n].to_numpy() != b.iloc[:n].to_numpy()).any(axis=1))[0]
    if len(diff) == 0 and len(a) == len(b):
        return {"identical": True, "rows": len(a)}
    i = int(diff[0]) if len(diff) else n
    return {"identical": False, "rows_pre": len(a), "rows_post": len(b), "first_diff_row": i,
            "pre_event": a.iloc[i]["event"] if i < len(a) else None, "post_event": b.iloc[i]["event"] if i < len(b) else None,
            "post_reason": b.iloc[i]["reason"] if i < len(b) else None, "post_decision_ts": b.iloc[i]["decision_ts"] if i < len(b) else None}


def whole_position_r(tr_rows: list[dict], intended: float, risk_dist: float, d: float) -> float:
    vol = sum(float(x["lots"]) for x in tr_rows)
    return sum(d * (float(x["entry_actual"]) - intended) / risk_dist * float(x["lots"]) for x in tr_rows) / vol


def analyse_run(build: str, window: str) -> dict:
    run = os.path.join(REG, f"REG_{build}_{SYM}_{window}")
    dna = dna_path(run)
    rows, n_dec, _ = CA.read_events(dna)
    rows = [r for r in rows if r["event"] in ("OPEN", "FILL", "PARTIAL_CLOSE", "CLOSE")]
    rejected = sum(1 for r in CA.read_events(dna)[0] if r["event"] == "REJECTED")
    tr = CA.pair_trades(rows, SYM, window)
    ev = CA.tester_evidence(run, SYM)
    exp = CA.expected_inputs()
    exp["InpMaxSameCurrencyNet"] = "2"                       # production value: no override in this regression
    bad = [k for k in exp if k in ev["inputs"] and not CA._same(ev["inputs"][k], exp[k])]
    missing = [k for k in exp if k not in ev["inputs"]]
    costs = float(tr["commission_usd"].sum() + tr["swap_usd"].sum()) if len(tr) else 0.0
    rebuilt, left = CA.rebuild_balance(SYM, ev["deals"], costs, start=200.0)
    dna_bal = 200.0 + (float(tr["realised_pnl_usd"].sum()) if len(tr) else 0.0)
    out = {"decisions": n_dec, "trades": len(tr), "rejected_rows": rejected, "deals": len(ev["deals"]),
           "partials": int((tr["legs"] > 1).sum()) if len(tr) else 0, "test_passed": ev["test_passed"],
           "inputs_exact_production": not bad and not missing, "inputs_bad": bad, "inputs_missing": missing,
           "final_balance": ev["final_balance"], "rebuilt_from_deals": rebuilt, "rebuilt_from_dna": dna_bal,
           "open_left": left,
           "reconciles": ev["final_balance"] is not None and abs(rebuilt - ev["final_balance"]) <= 0.01 * max(1, len(ev["deals"]))
           and abs(dna_bal - ev["final_balance"]) <= 0.01 * max(1, len(tr))}
    out["deals_match_legs"] = out["deals"] == len(tr) + int(tr["legs"].sum()) if len(tr) else out["deals"] == 0
    out["max_one_partial_per_trade"] = bool((tr["legs"] <= 2).all()) if len(tr) else True
    # partial legs: R at the partial vs the INITIAL risk (actual fill, DNA risk_dist), and the CLOSE row's R
    chk, r_at_partial, r_close_err = [], [], []
    ex = pd.DataFrame(rows)
    i_open = [k for k, r in enumerate(rows) if r["event"] == "OPEN"]
    for k, t in tr.iterrows():
        if t["legs"] < 2:
            continue
        o = rows[i_open[k]]
        seq = [r for r in rows[i_open[k]:] if r["event"] in ("PARTIAL_CLOSE", "CLOSE")][:2]
        if [r["event"] for r in seq] != ["PARTIAL_CLOSE", "CLOSE"] or \
                abs(sum(float(r["lots"]) for r in seq) - t["lots"]) > 1e-9:
            chk.append(False)                 # legs not attributable unambiguously: reported as a failed check
            continue
        rp = t["direction"] * (float(seq[0]["entry_actual"]) - t["fill"]) / t["risk_dist"]
        r_at_partial.append(rp)
        r_expect = whole_position_r(seq, float(o["entry_intended"]), t["risk_dist"], t["direction"])
        r_close_err.append(abs(float(seq[1]["result_r"]) - r_expect) / max(1.0, abs(r_expect)))
        chk.append(rp >= 1.5 * (1 - R_TOL_REL) - R_TOL_ABS)
    out["partial_deal_r_vs_initial_risk"] = [round(x, 3) for x in r_at_partial]   # deal price: includes exit delay
    out["partial_deal_r_check"] = all(chk)
    # the EA's own trigger R (logged when the partial is sent) is the authoritative decision evidence
    trig, fails, unsplit, noref, unread = [], 0, 0, 0, 0
    # tester.log mirrors every agent-log line: de-duplicate identical messages (each carries its own
    # simulated timestamp, so distinct events never collapse)
    for msg in dict.fromkeys(CA.run_log_lines(run)):
        m = re.search(r"NEXA: partial close sent for \d+ vol=([\d.]+) at R=([\d.\-]+)", msg)
        if m:
            trig.append(float(m.group(2)))
        fails += "NEXA WARNING: partial close failed" in msg
        unsplit += "cannot be split for the" in msg
        noref += "has no initial-risk reference" in msg
        unread += "deal history of position" in msg and "unreadable" in msg
    out["partial_trigger_r_logged"] = trig
    out["partials_sent_logged"] = len(trig)
    out["all_partial_triggers_at_or_after_1_5R"] = all(x >= 1.495 for x in trig)   # printed with 2 decimals
    out["partial_send_failures_logged"] = fails
    out["unsplittable_positions_logged"] = unsplit
    out["no_risk_reference_warnings"] = noref
    out["history_unreadable_warnings"] = unread
    out["close_result_r_volume_weighted_max_rel_err"] = max(r_close_err) if r_close_err else None
    ing = nexa_ingest.load_trade_dna(dna)
    fr = ing.frame
    epi = fr[fr["event"].isin(["OPEN", "FILL", "PARTIAL_CLOSE", "CLOSE"])]
    linked = bool((epi.groupby("episode_id")["event"].apply(lambda s: s.iloc[0] == "OPEN" and s.iloc[-1] == "CLOSE")).all()) if len(epi) else True
    out["ingest_ok"] = ing.ok
    out["ingest_errors"] = [str(f) for f in ing.errors()]
    out["ingest_partial_rows"] = int((fr["event"] == "PARTIAL_CLOSE").sum())
    out["ingest_episodes_linked_open_to_close"] = linked
    del ex
    return out


def main() -> int:
    windows = list(CA.WINDOWS)
    res = {"label": "ENGINEERING REGRESSION -- NOT RESEARCH EVIDENCE", "symbol": SYM, "deposit": 200.0,
           "post_sources": {"NEXA_EA.mq5": sha256(os.path.join(ROOT, "NEXA_EA.mq5")),
                            "NEXA_PositionMgmt.mqh": sha256(os.path.join(ROOT, "NEXA_PositionMgmt.mqh"))},
           "provenance": CA.read_text(os.path.join(REG, "PROVENANCE.txt")),
           "windows": {}}
    for w in windows:
        pre, post = analyse_run("PRE", w), analyse_run("PMFIX", w)
        div = first_divergence(dna_path(os.path.join(REG, f"REG_PRE_{SYM}_{w}")), dna_path(os.path.join(REG, f"REG_PMFIX_{SYM}_{w}")))
        res["windows"][w] = {"pre": pre, "post": post, "divergence": div}
    W = res["windows"]
    res["summary"] = {
        "runs": 2 * len(W),
        "all_test_passed": all(v[b]["test_passed"] for v in W.values() for b in ("pre", "post")),
        "all_inputs_exact_production": all(v[b]["inputs_exact_production"] for v in W.values() for b in ("pre", "post")),
        "all_reconcile": all(v[b]["reconciles"] for v in W.values() for b in ("pre", "post")),
        "pre_partials": sum(v["pre"]["partials"] for v in W.values()),
        "post_partials": sum(v["post"]["partials"] for v in W.values()),
        "post_trades": sum(v["post"]["trades"] for v in W.values()),
        "pre_trades": sum(v["pre"]["trades"] for v in W.values()),
        "all_deals_match_legs": all(v[b]["deals_match_legs"] for v in W.values() for b in ("pre", "post")),
        "post_max_one_partial_per_trade": all(v["post"]["max_one_partial_per_trade"] for v in W.values()),
        "post_partials_sent_logged": sum(v["post"]["partials_sent_logged"] for v in W.values()),
        "post_all_partial_triggers_at_or_after_1_5R": all(v["post"]["all_partial_triggers_at_or_after_1_5R"] for v in W.values()),
        "post_min_partial_trigger_r": min((min(v["post"]["partial_trigger_r_logged"]) for v in W.values() if v["post"]["partial_trigger_r_logged"]), default=None),
        "post_partial_deal_r_min": min((min(v["post"]["partial_deal_r_vs_initial_risk"]) for v in W.values() if v["post"]["partial_deal_r_vs_initial_risk"]), default=None),
        "post_partial_send_failures": sum(v["post"]["partial_send_failures_logged"] for v in W.values()),
        "post_unsplittable_positions": sum(v["post"]["unsplittable_positions_logged"] for v in W.values()),
        "post_no_risk_reference_warnings": sum(v["post"]["no_risk_reference_warnings"] for v in W.values()),
        "post_history_unreadable_warnings": sum(v["post"]["history_unreadable_warnings"] for v in W.values()),
        "post_close_result_r_max_rel_err": max((v["post"]["close_result_r_volume_weighted_max_rel_err"] or 0.0) for v in W.values()),
        "all_ingest_ok": all(v[b]["ingest_ok"] for v in W.values() for b in ("pre", "post")),
        "all_episodes_linked": all(v[b]["ingest_episodes_linked_open_to_close"] for v in W.values() for b in ("pre", "post")),
        "windows_identical_pre_post": [w for w, v in W.items() if v["divergence"]["identical"]],
        "windows_diverging": {w: {k: v["divergence"].get(k) for k in ("first_diff_row", "pre_event", "post_event", "post_reason")}
                              for w, v in W.items() if not v["divergence"]["identical"]},
    }
    with open(os.path.join(REG, "regression_evidence.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(json.dumps(res["summary"], indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
