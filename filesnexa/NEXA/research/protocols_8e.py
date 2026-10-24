"""RESEARCH_8E_V1: pre-registered protocol for the 8-engine investigation (NOT V2; never merged into V2).

Frozen in its own registry (research/registry_8e) with nexa_registry2 machinery. Periods (UTC):
  DEV  [2018-01-01, 2023-01-01)   development / exploration, unlimited DEV records
  VAL  [2023-01-01, 2026-09-25)   ONE query per trial; the pinned selection rule picks per group
  WF   2020, 2021, 2022
  OOS  [2026-10-12, 2027-04-12)   PROSPECTIVE (data does not exist yet); selection sealed before it.
No historical window is clean: 2017-2026 Pepperstone data was used by earlier NEXA work, so the VAL
window is "seen" data and VAL evidence is NOT out-of-sample evidence.
Disclosed pre-freeze exploration: XAUUSD M15 2021 (inside DEV) was run once as a harness smoke test.
NAS100 is BLOCKED: no NAS100 price history is held locally (only the spec probe).
"""
from __future__ import annotations

import nexa_8e_research as R

PERIODS = {"DEV": ["2018-01-01T00:00:00Z", "2023-01-01T00:00:00Z"],
           "VAL": ["2023-01-01T00:00:00Z", "2026-09-25T00:00:00Z"],
           "WF_YEARS": [2020, 2021, 2022],
           "OOS": ["2026-10-12T00:00:00Z", "2027-04-12T00:00:00Z"],
           "semantics": "half-open UTC; VAL is SEEN data (not clean OOS); OOS is prospective"}
GRID = {"tf": ["M15", "H1"], "dc_n": [20, 55], "entry_mode": ["close_next_open", "stop_at_channel"],
        "target_r": [2, 3, 5]}
MAX_LABEL_MIN = R.HOLD_BARS * 60                      # 48 H1 bars
COMMON = {
    "version": 1, "family": "eight_engine", "grid": GRID,
    "periods_utc": PERIODS, "timezone": {"period_bounds": "UTC", "bars": "UTC bins from nexa_time-canonical M1"},
    "purge_embargo": {"max_label_minutes": MAX_LABEL_MIN, "embargo_minutes": 2 * MAX_LABEL_MIN,
                      "rule": "entry >= start + embargo (not DEV); signal + max_label <= end; exit < end"},
    "leakage_rules": ["features from completed TF bars only (closed-bar rule); certified with nexa_causality",
                      "TF bars built only from M1 rows inside their interval",
                      "trailing statistics use strictly prior bars", "labels never enter features"],
    "costs": {"commission_per_lot_side_usd": R.COMMISSION_PER_LOT_SIDE, "spread": "first-minute M1 recorded spread",
              "slippage_spread_frac": R.SLIP_SPREAD_FRAC, "swap": "spec-probe swap, charges only, x3 Wednesday",
              "latency_ms": 250, "stress": "spread x2, x3 on the selected trials"},
    "execution": {"engine": "nexa_execution bar mode", "stop": f"{R.STOP_ATR} x ATR14 from fill",
                  "time_stop_bars": R.HOLD_BARS, "one_position_at_a_time": True},
    "nulls": ["random_subset_same_size"],
    "tests": {"alpha": 0.05, "fdr_q": 0.10, "dsr_min": 0.95, "pbo_max": 0.5, "min_trades_promote": 200,
              "min_trades_report": 30, "val_queries_per_trial": 1,
              "selection_rule": "per (experiment, claim, symbol): highest VAL one-sided 95% stationary-bootstrap lower "
                                "bound of net R among trials with >= 30 VAL trades; ties -> trial_id"},
}
SYMBOLS = ["XAUUSD", "EURUSD", "GBPUSD"]


def build() -> list[dict]:
    return [
        {**COMMON, "experiment": "E8_STACK", "status": "ACTIVE", "symbols": SYMBOLS,
         "hypothesis": "Each engine, added in the fixed order sq > vei > ema200 > mom > ofi_proxy > quote_burst > td "
                       "to a Donchian breakout, raises NET R per trade beyond a random subset of equal size",
         "sensitivity": {"variant": R.STACK + R.SINGLE},
         "claims": {"C_stack": {"params": ["tf", "dc_n", "entry_mode", "target_r", "variant"], "primary": True}}},
        {**COMMON, "experiment": "E8_THRESH", "status": "ACTIVE", "symbols": SYMBOLS,
         "hypothesis": "Threshold sensitivity of VEI, the OFI proxy ratio (incl. the proposed 3.0 = 300%) and the "
                       "quote-burst percentile as single add-ons",
         "sensitivity": {"variant": R.THRESH},
         "claims": {"C_thresh": {"params": ["tf", "dc_n", "entry_mode", "target_r", "variant"], "primary": False}}},
        {**COMMON, "experiment": "E8_NAS100", "status": "BLOCKED", "symbols": ["NAS100"],
         "blocked_reason": "no NAS100 price history held locally; acquiring it is a broker download needing approval",
         "hypothesis": "as E8_STACK on NAS100", "sensitivity": {"variant": R.STACK},
         "claims": {"C_stack": {"params": ["tf", "dc_n", "entry_mode", "target_r", "variant"], "primary": True}}},
    ]


LEGACY_TRIALS = 1740 + 108          # V2 universe + earlier factory trials share the same data
