"""G1 unit tests for prop_ev.py (PREREG_PROP_EV.md §6)."""
import numpy as np

import prop_ev as pe


def test_p_formula_reproduces_mu():
    for mu in pe.MU_GRID:
        for b in pe.B_GRID:
            p = pe.p_win(mu, b, pe.COST_R)
            assert abs(p * (b - pe.COST_R) - (1 - p) * (1 + pe.COST_R) - mu) < 1e-12
            assert 0 < p < 1


def _rw_excursions(b, n=3000, step=0.02, seed=1):
    rng = np.random.default_rng(seed)
    lo, hi = -1.0, b
    peaks_loss, dips_win = [], []
    for _ in range(n):
        x, mx, mn = 0.0, 0.0, 0.0
        while lo < x < hi:
            x += step if rng.random() < 0.5 else -step
            mx, mn = max(mx, x), min(mn, x)
        if x <= lo:
            peaks_loss.append(mx)
        else:
            dips_win.append(-mn)
    return np.array(peaks_loss), np.array(dips_win)


def test_excursion_samplers_match_random_walk():
    b = 1.52
    pl, dw = _rw_excursions(b)
    u = np.random.default_rng(2).random(200_000)
    m = pe.loss_peak(u, b)
    k = pe.win_dip(u, b)
    for q in (0.25, 0.5, 0.75):
        assert abs(np.quantile(m, q) - np.quantile(pl, q)) < 0.06
        assert abs(np.quantile(k, q) - np.quantile(dw, q)) < 0.06
    # analytic win probability for a driftless walk = 1/(1+b)
    assert abs(len(dw) / (len(dw) + len(pl)) - 1 / (1 + b)) < 0.03


def test_eod_threshold_apex_example():
    thr = np.array([48_000.0])
    peak = np.array([50_000.0])
    for close, want in [(50_800, 48_800), (51_600, 49_600), (50_900, 49_600), (52_000, 50_000)]:
        peak = np.maximum(peak, close)
        thr = pe.eod_threshold(thr, peak, pe.EVAL_CAP)
        assert thr[0] == want


def test_pa_threshold_locks_at_50100():
    thr = np.array([48_000.0])
    for close in [51_000, 52_100, 53_500, 55_000]:
        thr = pe.eod_threshold(thr, np.array([close], float), pe.PA_CAP)
    assert thr[0] == 50_100


def test_consistency_apex_example_table():
    pnl = [0, 500, 200, 0, -200, -600, 1000, 600, 500]
    net, mx, ok_days = 0.0, 0.0, []
    for d, x in enumerate(pnl, 1):
        net += x
        if x > 0:
            mx = max(mx, x)
        if pe.consistency_ok(np.array([mx]), np.array([net]))[0]:
            ok_days.append(d)
    assert ok_days == [9]


def test_payout_caps_and_minimum():
    assert pe.payout_amount(52_600, 0, 'EOD') == 500
    assert pe.payout_amount(52_500, 0, 'EOD') == 0
    assert pe.payout_amount(60_000, 0, 'EOD') == 1500
    assert pe.payout_amount(60_000, 5, 'EOD') == 3000
    assert pe.payout_amount(60_000, 1, 'INTRA') == 2000


def test_zero_drift_pass_rate_sane():
    # driftless, no costs, 1 trade/day: pass prob must be between 0 and the gambler's-ruin bound 2000/5000
    r = pe.cell('EOD', 1.0, 500.0, 1, 0.0, n=4000, c=0.0)
    assert 0.15 < r['p_pass'] < 0.45
    assert r['pa_e_payouts'] >= 0


def test_pa_payout_flow_sanity_offgrid():
    # off-grid strong edge (mu = 0.6): payouts must occur, respect the cap total and the 6-payout limit
    rng = np.random.default_rng(7)
    tot, npay, days = pe.run_pa(rng, 2000, 'EOD', 1.52, 500.0, 1, 0.6, pe.COST_R)
    assert (npay <= 6).all() and (tot <= sum(pe.CAPS['EOD']) + 1e-9).all()
    assert (npay > 0).mean() > 0.5
    assert ((npay == 0) | (tot >= 500 * npay)).all()
