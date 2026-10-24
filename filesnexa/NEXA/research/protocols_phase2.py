"""The six Phase-3 hypothesis protocols, transcribed from reports/RESEARCH_DESIGN_SIX_FAMILIES.md.

Building these dicts evaluates NOTHING. `freeze_all` binds each protocol to the exact data
hashes it may use, freezes it in the registry, creates the campaign and freezes the campaign.
The campaign is left FROZEN: opening evaluation requires a separate, explicit human approval.
"""
from __future__ import annotations

import json
import os

import nexa_registry as reg

BAR_PERIODS = {"DEV": ["2018-01-01", "2022-12-31"], "VAL": ["2023-01-01", "2024-12-31"],
               "OOS": ["2025-01-01", "2026-08-27"], "WF_YEARS": [2020, 2021, 2022, 2023, 2024],
               "REAL_TICK_EXECUTION_CHECK": ["2026-08-28", "2026-09-25"], "FORWARD": "data after freeze via NEXA_TickLogger"}
TICK_PERIODS = {"DEV": ["2026-08-28", "2026-09-11"], "VAL": ["2026-09-14", "2026-09-18"],
                "OOS": ["2026-09-21", "2026-09-25"], "FORWARD": ">= 4 weeks logged after freeze (true OOS)"}
CORE4 = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
LEGACY_TRIALS = 108            # 18 Axiory XAUUSD + 90 Pepperstone factory configurations (all failed)

COSTS = {"commission_per_lot_side_usd": 3.50, "spread": "per-bar recorded spread (M1) or tick ask-bid",
         "slippage": {"points": 0.0, "spread_frac": 0.5, "event_multiplier": 3.0},
         "latency_ms": 250, "swap": "contracts.json swap_long/short on positions crossing server 00:00"}
EXECUTION = {"engine": "nexa_execution", "limit_fill": "trade-through by 1 point (touch is not a fill)",
             "ambiguous_bar": "STOP_FIRST", "gap": "fill at bar open", "bar_latency": "next bar open"}
NULLS = ["timing", "direction", "circular_shift"]
TESTS = {"alpha": 0.05, "fdr_q": 0.10, "dsr_min": 0.95, "pbo_max": 0.5, "min_trades_report": 30,
         "min_trades_promote": 200, "bootstrap": "stationary block, block = max hold, 5000 draws, seeded",
         "null_permutations": 5000, "null_rule": "intersection-union: every null p <= alpha"}
ROBUST = {"cost_shocks": {"spread_x": [1.5, 2, 3], "commission_x": [1.5], "slippage_plus_spread": [1]},
          "latency_ms": [250, 500, 1000], "missed_fill_drop": [0.10, 0.25],
          "holdouts": ["leave-one-year-out", "leave-one-symbol-out"],
          "sensitivity_rule": ">= 70% of neighbouring grid cells keep E[R] > 0 and CI sign"}
FAILURE = ["OOS E[R] CI includes 0", "fails any null after BH-FDR", "E[R] < 0 at spread x2 or latency 500 ms",
           "PBO >= 0.5", "DSR < 0.95", "unstable parameter surface", "OOS/IS degradation < 0.5 or sign flip",
           "leave-one-out flips sign", "fewer than 200 OOS-eligible trades"]
METRICS = ["win_rate", "loss_rate", "expectancy_r_ci", "median_r", "profit_factor", "max_drawdown_r", "mae_r", "mfe_r",
           "sharpe_per_trade_if_n>=100_nonoverlap", "sortino", "trades_per_week", "exposure", "spread_cost_r",
           "commission_r", "slippage_r", "latency_ms", "fill_probability", "regime_stability", "parameter_stability",
           "oos_expectancy", "degradation_oos_over_is"]


def _base(exp: str, family: str, hyp: str, symbols, grid, periods, data, labels, status="ACTIVE", **extra) -> dict:
    p = {"experiment": exp, "version": 1, "family": family, "hypothesis": hyp, "status": status, "symbols": symbols,
         "grid": grid, "periods": periods, "data": data, "costs": COSTS, "execution": EXECUTION, "nulls": NULLS,
         "tests": TESTS, "robustness": ROBUST, "failure_criteria": FAILURE, "labels": labels, "metrics": METRICS,
         "design_doc": "research/reports/RESEARCH_DESIGN_SIX_FAMILIES.md", "time_convention": "PEPPERSTONE_NY_CLOSE via nexa_time"}
    p.update(extra)
    return p


def build(data_refs: dict) -> list[dict]:
    m1, cal, ticks = data_refs["m1_canonical"], data_refs["calendar"], data_refs["ticks"]
    env = {"time_convention": data_refs.get("time_convention"),
           "execution_module_sha256": data_refs.get("execution_module_sha256")}
    protos = _protocols(m1, cal, ticks, data_refs)
    for p in protos:
        p["environment"] = env
    return protos


def _protocols(m1, cal, ticks, data_refs) -> list[dict]:
    return [
        _base("F1_MACRO_EVENT", "macro_event",
              "H1b: after the initial spike, sign of post-release return follows sign of standardized surprise, net of costs "
              "(H1a volatility elevation reported, not tradable)", CORE4,
              {"z_star": [0.5, 1.0, 1.5], "delta_min": [1, 2, 5], "hold_min": [15, 30, 60], "target_r": [1, 2]},
              BAR_PERIODS, {"m1": m1, "calendar": cal},
              {"type": "triple_barrier", "from": "tau+delta", "barriers": "stop / target_r / hold"},
              extra_nulls=["surprise_shuffled"], extra_robustness=["timestamp_jitter_pm1min"],
              event_filter={"mt5_event_type": "INDICATOR (type==1); speeches/events excluded",
                            "importance": "HIGH", "time_mode": "DATETIME only (no DATE/TENTATIVE)",
                            "exclude": "rows flagged local_clock_off_mode (e.g. NFP 2025-11-20)",
                            "time_basis": "calendar FIXED_EXPORT_OFFSET -> UTC (nexa_calendar), never the bar clock"},
              architecture_note="conflicts with NEXA news veto / FOMC gate; coexistence needs human design, never bypass"),
        _base("F2_XAU_SESSION_BREAKOUT", "session_breakout",
              "first close beyond the UTC 00:00-06:00 XAUUSD range + b*W in 06:00-10:00 UTC continues beyond matched random breaks",
              ["XAUUSD"], {"buffer_b": [0.0, 0.1, 0.25], "target_r": [1.0, 1.5, 2.0, 3.0], "stop": ["range_mid", "atr_x10"]},
              BAR_PERIODS, {"m1": m1, "calendar": cal},
              {"type": "triple_barrier", "time_exit_utc": "16:00"},
              extra_nulls=["random_range_same_width"], sensitivity={"asian_end_utc": [5, 6, 7]},
              mandatory_split="long and short must each have E[R] > 0 (gold drift control)"),
        _base("F3_FVG_RETRACEMENT", "fvg_retracement",
              "H3a: FVG zones are revisited more than matched non-FVG zones; H3b: filled limit entries at FVG zones earn "
              "E[R]>0 net and beat matched zones (E[R] per PLACED order reported)", CORE4,
              {"min_size_atr": [0.1, 0.25, 0.5], "validity_bars": [12, 48], "target_r": [1, 2, 3],
               "entry": ["edge", "mid"], "timeframe": ["M5", "M15"]},
              BAR_PERIODS, {"m1": m1, "nexa_dna_f13_f14": data_refs.get("dna_audit")},
              {"type": "H3a touched-within-N; H3b triple_barrier on filled orders"},
              extra_nulls=["matched_zone"], sensitivity={"fill_rule": ["touch", "through_1pt", "through_2pt"]}),
        _base("F4_CROSS_FEED_LATENCY", "latency_lead_lag",
              "L1 observed lead / L2 executable lead / L3 post-cost edge (never merged)", ["EURUSD", "XAUUSD"],
              {"sample_ms": [50, 100, 250, 1000], "threshold_q": [0.95, 0.99], "hold_s": [1, 5]},
              TICK_PERIODS, {"second_feed": None}, {"type": "executable P/L at hold"},
              status="BLOCKED",
              blocked_reason="no second synchronous tick feed with a common clock; needs a second broker login + parallel logging"),
        _base("F5_ASIAN_MEAN_REVERSION", "session_mean_reversion",
              "in UTC 23:00-06:00 (rollover excluded), stretched z vs session anchor reverts beyond matched nulls, net of costs",
              CORE4, {"z_star": [1.5, 2.0, 2.5], "stop_k": [1.0, 1.5], "hold_bars": [30, 60, 120], "anchor": ["mean", "typical"]},
              BAR_PERIODS, {"m1": m1, "calendar": cal},
              {"type": "triple_barrier", "target": "session anchor (dynamic)"},
              extra_nulls=["same_rule_london_hours"], sensitivity={"session_start_utc": [22, 23, 0]},
              effective_n="sessions (cluster bootstrap by session)"),
        _base("F6_TICK_QUOTE_IMBALANCE", "quote_microstructure",
              "broker QUOTE-update imbalance predicts next mid move beyond sign-shuffled null AND survives spread+commission+"
              "250 ms latency (NOT institutional order flow)", CORE4 + ["XAGUSD"],
              {"window_updates": [50, 200, 1000], "quantile_q": [0.9, 0.95, 0.99], "hold_s": [1, 5, 30]},
              TICK_PERIODS, {"ticks": ticks}, {"type": "executable P/L sign at hold; mid-only result never reported as edge"},
              extra_nulls=["sign_shuffled_1min_blocks", "time_shifted"],
              data_caveat="quote-only ticks: volume=0, last=0, no aggressor flags, DOM unavailable"),
    ]


def freeze_all(registry_root: str, data_refs: dict, campaign: str = "PHASE3_SIX_FAMILIES_V1") -> dict:
    r = reg.Registry(registry_root)
    frozen = [r.freeze_protocol(p) for p in build(data_refs)]
    r.create_campaign(campaign, [(p["experiment"], p["version"]) for p in frozen], legacy_trials=LEGACY_TRIALS,
                      correction={"campaign": "Benjamini-Hochberg q=0.10 over all primary tests (experiment x symbol)",
                              "dsr_trials": "declared_trials_active + legacy_trials",
                              "experiment": "PBO (CSCV) across grid + parameter-surface stability",
                              "config": "intersection-union over timing/direction/circular-shift nulls (+ family nulls)"})
    c = r.freeze_campaign(campaign)
    return {"campaign": c, "protocols": {p["experiment"]: {"sha256": p["sha256"], "status": p["status"],
                                                          "declared_trials": reg.declared_trials(p)} for p in frozen},
            "ledger_valid": r.verify_ledger()}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--data-refs", required=True, help="json file with m1_canonical/calendar/ticks/dna_audit hashes")
    a = ap.parse_args(argv)
    with open(a.data_refs) as fh:
        refs = json.load(fh)
    out = freeze_all(a.registry, refs)
    with open(os.path.join(a.registry, "PHASE2_FREEZE_SUMMARY.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
