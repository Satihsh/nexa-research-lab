"""G1 unit tests for prop_ev_ts.py (PREREG_PROP_EV_TS.md s.6). No market data."""
import numpy as np

import prop_ev as pe
import prop_ev_ts as ts


# 1. Combine MLL trails EOD and locks at 50,000 (Topstep MLL article example)
def test_combine_mll_trails_and_locks():
    thr = np.array([48_000.0])
    peak = np.array([50_000.0])
    for close, want in [(50_500, 48_500), (50_000, 48_500), (51_700, 49_700), (53_000, 50_000), (56_000, 50_000)]:
        peak = np.maximum(peak, close)
        thr = ts.combine_mll(thr, peak)
        assert thr[0] == want


# 2. XFA MLL starts -2,000, locks at 0 (Topstep example), and is 0 after a payout
def test_xfa_mll_locks_at_zero():
    thr = np.array([-2_000.0])
    peak = np.array([0.0])
    for close, want in [(500, -1_500), (2_000, 0), (5_000, 0)]:
        peak = np.maximum(peak, close)
        thr = ts.xfa_mll(thr, peak)
        assert thr[0] == want


def test_xfa_mll_zero_after_first_payout_in_sim():
    rng = np.random.default_rng(3)
    cash, npay, days = ts.run_xfa(rng, 3000, 'STD', 1.52, 500.0, 1, 0.6, ts.COST_R)
    assert (npay > 0).mean() > 0.5          # strong off-grid edge: payouts happen
    assert (cash <= npay * (ts.SPLIT * ts.STD_CAP - ts.WIRE_FEE) + 1e-9).all()


# 3. Combine pass rule with the 55 % consistency target (Topstep examples)
def test_combine_pass_rule():
    assert ts.combine_passed(np.array([3_000.0]), np.array([1_600.0]))[0]          # 53 % -> pass
    assert not ts.combine_passed(np.array([3_000.0]), np.array([1_800.0]))[0]      # needs 3,273
    assert not ts.combine_passed(np.array([3_272.0]), np.array([1_800.0]))[0]
    assert ts.combine_passed(np.array([3_273.0]), np.array([1_800.0]))[0]
    assert not ts.combine_passed(np.array([2_999.0]), np.array([500.0]))[0]


# 4. Standard payout rule
def test_standard_payout_rule():
    amt = ts.payout_amount(np.array([6_000.0, 3_000.0, 200.0]), 'STD')
    assert list(amt) == [2_000.0, 1_500.0, 100.0]
    a = np.array([2_000.0])
    assert ts.std_eligible(np.array([5]), np.array([-10.0]), np.array([0]), a)[0]       # first payout: net exempt
    assert not ts.std_eligible(np.array([5]), np.array([-10.0]), np.array([1]), a)[0]   # later: needs net > 0
    assert ts.std_eligible(np.array([5]), np.array([0.01]), np.array([1]), a)[0]
    assert not ts.std_eligible(np.array([4]), np.array([500.0]), np.array([0]), a)[0]
    assert not ts.std_eligible(np.array([5]), np.array([500.0]), np.array([0]), np.array([100.0]))[0]  # < $125


# 5. Consistency payout rule (Topstep XFA examples: 1,000 / 400 OK, 1,000 / 450 not OK)
def test_consistency_payout_rule():
    a = np.array([500.0])
    assert ts.con_eligible(np.array([3]), np.array([1_000.0]), np.array([400.0]), a)[0]
    assert not ts.con_eligible(np.array([3]), np.array([1_000.0]), np.array([450.0]), a)[0]
    assert not ts.con_eligible(np.array([2]), np.array([1_000.0]), np.array([300.0]), a)[0]
    assert ts.con_eligible(np.array([3]), np.array([9_500.0]), np.array([3_600.0]), a)[0]   # 37.9 %
    assert list(ts.payout_amount(np.array([10_000.0, 4_000.0]), 'CON')) == [3_000.0, 2_000.0]


# 6. Monthly fee blocks
def test_fee_months():
    assert list(ts.fee_months(np.array([1, 21, 22, 42, 43]))) == [1, 1, 2, 2, 3]


# 7. Zero-drift sanity: pass rate bounded by the gambler's-ruin value 2,000/5,000 (trailing MLL only lowers it)
def test_zero_drift_combine_sane():
    rng = np.random.default_rng(5)
    passed, days = ts.run_combine(rng, 4000, 1.0, 500.0, 1, 0.0, 0.0)
    assert 0.10 < passed.mean() < 0.45
    assert (days >= 2)[passed].all()                       # cannot pass in one day


def test_cell_outputs_consistent():
    r = ts.cell('STD', 1.52, 500.0, 2, 0.10, n=2000)
    assert 0 <= r['p_pass'] <= 1 and r['fee_months_mean'] >= 1
    assert abs(r['e_cash_per_attempt'] - r['p_pass'] * r['xfa_e_cash']) < 1e-9
    assert abs(r['net_F-STD'] - (r['e_cash_per_attempt'] - (49 * r['fee_months_mean'] + r['p_pass'] * 149))) < 1e-6


# 8. Engine imported unchanged from H-PROP-EV
def test_engine_is_prop_ev():
    assert ts.p_win is pe.p_win and ts.loss_peak is pe.loss_peak and ts.win_dip is pe.win_dip
    assert ts._trade is pe._trade and ts.eod_threshold is pe.eod_threshold and ts.DD == 2_000.0
