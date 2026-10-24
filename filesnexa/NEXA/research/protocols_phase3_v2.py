"""PHASE3_SIX_FAMILIES_V2 protocols. Building them evaluates NOTHING.

Changes vs V1 (see reports/AUDIT_PHASE3_CAMPAIGN_V1.md):
  * OOS is PROSPECTIVE: [2027-01-04T00:00Z, 2028-01-03T00:00Z). No historical period can be
    certified unseen (reports/OOS_DETERMINATION_V2.md). 2025-01-01 .. 2027-01-04 is EXCLUDED
    (contaminated by prior holdouts + unused buffer) and may be used for nothing.
  * all causal/leakage rules, purge/embargo, timezone semantics and sensitivity axes are
    INSIDE each protocol (hashed); sensitivity values are trial dimensions.
  * F3 has two primary claims (H3a, H3b); F1 uses prior-only baselines and first-print filters.
  * F6 and F4 are BLOCKED.
"""
from __future__ import annotations

PERIODS_UTC = {
    "DEV": ["2018-01-01T00:00:00Z", "2023-01-01T00:00:00Z"],
    "VAL": ["2023-01-01T00:00:00Z", "2025-01-01T00:00:00Z"],
    "WF_YEARS": [2020, 2021, 2022, 2023, 2024],
    "EXCLUDED": ["2025-01-01T00:00:00Z", "2027-01-04T00:00:00Z"],
    "OOS": ["2027-01-04T00:00:00Z", "2028-01-03T00:00:00Z"],
    "semantics": "half-open [start, end) in UTC; OOS is prospective (post-freeze); EXCLUDED may not be read "
                 "for selection, validation, promotion or reporting of any V2 claim",
}
TIMEZONE = {"period_bounds": "UTC", "bar_clock": "PEPPERSTONE_NY_CLOSE (server = New York local + 7 h; US DST)",
            "bar_conversion": "research/nexa_time.py only", "calendar_conversion":
            "research/nexa_calendar.py FIXED_EXPORT_OFFSET from export provenance, never the bar clock",
            "session_windows": "defined in UTC and converted per bar; never fixed server hours"}
COMMON_LEAKAGE = [
    "a decision at closed entry bar t uses only bars with open time <= t (start_pos=1 semantics)",
    "a higher-timeframe bar is visible only if open + len(tf) <= decision_ts + len(entry_tf)",
    "all rolling statistics are trailing; no full-sample normalisation, centring, z-scoring or quantiles",
    "thresholds/quantiles are fitted only on the training span: DEV for VAL; years < Y for WF year Y",
    "labels may use data after entry but never enter any feature",
    "every feature/signal builder must pass nexa_causality.certify and be registered BEFORE opening",
    "the EXCLUDED window and the OOS window are never read before the OOS result is recorded",
]
COSTS = {"commission_per_lot_side_usd": 3.50, "spread": "per-bar recorded spread (M1)",
         "slippage": {"points": 0.0, "spread_frac": 0.5, "event_multiplier": 3.0}, "latency_ms": 250,
         "swap": "contracts.json swap_long/short on positions crossing server 00:00"}
EXECUTION = {"engine": "research/nexa_execution.py", "limit_fill": "trade-through by through_points (touch is not a fill)",
             "ambiguous_bar": "STOP_FIRST", "gap": "fill at bar open", "latency": "next bar open (bar mode)"}
NULLS = ["timing", "direction", "circular_shift"]
TESTS = {"alpha": 0.05, "fdr_q": 0.10, "dsr_min": 0.95, "pbo_max": 0.5, "min_trades_report": 30,
         "min_trades_promote": 200, "val_queries_per_trial": 1, "wf_queries_per_trial_year": 1,
         "bootstrap": "stationary block (block = max hold), 5000 draws, seed 20260928",
         "null_permutations": 5000, "null_rule": "intersection-union: every declared null p <= alpha",
         "selection_rule": "per (experiment, claim, symbol): highest lower-95% bootstrap bound of VAL E[R] "
                           "among trials with >= min_trades_report VAL trades; ties -> fewer parameters "
                           "then lexicographic trial_id; sealed via OOS_SELECTED before OOS start"}
ROBUST = {"cost_shocks": {"spread_x": [1.5, 2, 3], "commission_x": [1.5]}, "latency_ms": [250, 500, 1000],
          "missed_fill_drop": [0.10, 0.25], "holdouts": ["leave-one-year-out", "leave-one-symbol-out"],
          "note": "robustness runs apply ONLY to the sealed trial and can never change the selection"}
CORE4 = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
LEGACY_TRIALS = 108


def _p(exp, family, hyp, symbols, grid, sensitivity, claims, max_label_min, leakage, **extra) -> dict:
    return {"experiment": exp, "version": 2, "status": extra.pop("status", "ACTIVE"), "family": family,
            "hypothesis": hyp, "symbols": symbols, "grid": grid, "sensitivity": sensitivity, "claims": claims,
            "periods_utc": extra.pop("periods", PERIODS_UTC), "timezone": TIMEZONE,
            "purge_embargo": {"max_label_minutes": max_label_min, "embargo_minutes": max(1440, 2 * max_label_min),
                              "rule": "a trade belongs to a period only if entry >= start + embargo (except DEV "
                                      "start) and exit/label end < end; trades straddling a boundary are PURGED"},
            "leakage_rules": COMMON_LEAKAGE + leakage, "costs": COSTS, "execution": EXECUTION,
            "nulls": NULLS + extra.pop("extra_nulls", []), "tests": TESTS, "robustness": ROBUST, **extra}


def build() -> list[dict]:
    tick_periods = {"DEV": ["2027-01-04T00:00:00Z", "2027-03-01T00:00:00Z"],
                    "VAL": ["2027-03-01T00:00:00Z", "2027-04-05T00:00:00Z"],
                    "OOS": ["2027-04-05T00:00:00Z", "2027-07-05T00:00:00Z"],
                    "WF_YEARS": [], "semantics": "placeholder: tick families are BLOCKED; dates only fix the "
                                                 "requirement that ALL tick data be collected after the freeze"}
    return [
        _p("F1_MACRO_EVENT", "macro_event",
           "H1b: after the initial spike, the sign of the post-release return follows the sign of the standardised "
           "surprise more often than chance, net of costs", CORE4,
           {"z_star": [0.5, 1.0, 1.5], "delta_min": [1, 2, 5], "hold_min": [15, 30, 60], "target_r": [1, 2]}, {},
           {"H1b_direction": {"params": ["z_star", "delta_min", "hold_min", "target_r"], "primary": True}},
           65, [
               ("event eligibility = nexa_calendar.f1_eligible: HIGH, MT5 type INDICATOR, exact DATETIME, "
                "first_print == CONFIRMED (REVISED_VALUE / UNDETERMINED excluded), forecast present, >= 12 prior "
                "releases, local clock == PRIOR-ONLY modal clock, prior-only surprise sd > 0"),
               "surprise = (actual - forecast) / prior_surprise_sd from STRICTLY EARLIER confirmed releases",
               "no statistic of an event uses that event's own or any later release",
               "H1a (volatility elevation) is descriptive only: not a claim, not recorded, not promotable",
               ("OOS: first prints must be captured live at release (calendar logger); historical next-release "
                "confirmation is not available for the latest release")],
           extra_nulls=["surprise_shuffled"],
           architecture_note="conflicts with NEXA news veto / FOMC gate: coexistence needs a human design"),
        _p("F2_XAU_SESSION_BREAKOUT", "session_breakout",
           "the first close beyond the UTC [00:00, asian_end) XAUUSD range + b*W during [asian_end, 10:00) UTC continues "
           "beyond matched random breaks, net of costs, for longs and shorts separately", ["XAUUSD"],
           {"buffer_b": [0.0, 0.1, 0.25], "target_r": [1.0, 1.5, 2.0, 3.0], "stop": ["range_mid", "atr_x10"]},
           {"asian_end_utc_hour": [5, 6, 7]},
           {"continuation": {"params": ["buffer_b", "target_r", "stop", "asian_end_utc_hour"], "primary": True}},
           600, ["range W uses only bars of day d inside [00:00, asian_end) UTC, complete before the first signal",
                 "W filter median uses the 60 STRICTLY EARLIER trading days",
                 "long and short must each show E[R] > 0 (gold drift control)"],
           extra_nulls=["random_range_same_width"]),
        _p("F3_FVG_RETRACEMENT", "fvg_retracement",
           "H3a: FVG zones are revisited more often than matched non-FVG zones. H3b: limit entries at FVG zones, "
           "when filled, earn E[R] > 0 net and beat matched zones (E[R] per PLACED order reported)", CORE4,
           {"min_size_atr": [0.1, 0.25, 0.5], "validity_bars": [12, 48], "target_r": [1, 2, 3],
            "entry": ["edge", "mid"], "timeframe": ["M5", "M15"]}, {"fill_rule": ["touch", "through_1pt", "through_2pt"]},
           {"H3a_revisit": {"params": ["min_size_atr", "validity_bars", "timeframe"], "primary": True},
            "H3b_limit_expectancy": {"params": ["min_size_atr", "validity_bars", "target_r", "entry", "timeframe",
                                                "fill_rule"], "primary": True}},
           1440, ["FVG at bar t uses closed bars t-2..t only; ATR trailing",
                  "matched-zone null draws zones using only data <= t",
                  "a pending limit is live only from bar close + latency; touch != fill unless fill_rule=='touch'"],
           extra_nulls=["matched_zone"]),
        _p("F4_CROSS_FEED_LATENCY", "latency_lead_lag", "L1 observed / L2 executable / L3 post-cost lead (never merged)",
           ["EURUSD", "XAUUSD"], {"sample_ms": [50, 100, 250, 1000], "threshold_q": [0.95, 0.99], "hold_s": [1, 5]}, {},
           {"L3_post_cost": {"params": ["sample_ms", "threshold_q", "hold_s"], "primary": True}}, 1, [],
           status="BLOCKED", periods=tick_periods,
           blocked_reason="no second synchronous tick feed with a common clock"),
        _p("F5_ASIAN_MEAN_REVERSION", "session_mean_reversion",
           "within the UTC Asian session (start = session_start_utc, end 06:00, broker rollover excluded) a stretched "
           "z versus the session anchor reverts beyond matched nulls, net of costs", CORE4,
           {"z_star": [1.5, 2.0, 2.5], "stop_k": [1.0, 1.5], "hold_bars": [30, 60, 120], "anchor": ["mean", "typical"]},
           {"session_start_utc_hour": [22, 23, 0]},
           {"reversion": {"params": ["z_star", "stop_k", "hold_bars", "anchor", "session_start_utc_hour"], "primary": True}},
           480, ["anchor = mean of session closes up to and including t", "sigma from the 60 bars strictly before t",
                 "D1 regime from the last COMPLETED server day",
                 "entries forbidden from 5 minutes before to 65 minutes after server 00:00 (rollover)"],
           extra_nulls=["same_rule_london_hours"]),
        _p("F6_TICK_QUOTE_IMBALANCE", "quote_microstructure",
           "broker QUOTE-update imbalance predicts the next mid move beyond a sign-shuffled null AND survives spread + "
           "commission + 250 ms latency (NOT institutional order flow)", CORE4 + ["XAGUSD"],
           {"window_updates": [50, 200, 1000], "quantile_q": [0.9, 0.95, 0.99], "hold_s": [1, 5, 30]}, {},
           {"executable_edge": {"params": ["window_updates", "quantile_q", "hold_s"], "primary": True}}, 1, [],
           status="BLOCKED", periods=tick_periods,
           blocked_reason="only 21 days of quote-only ticks exist and all were inspected; needs sufficient GENUINELY "
                          "NEW tick data logged after the freeze"),
    ]
