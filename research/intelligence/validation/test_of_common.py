#!/usr/bin/env python3
"""G1 synthetic unit tests for of_common / of16 / of19 / of20 building blocks. Run: python test_of_common.py"""
from __future__ import annotations

from datetime import date

import numpy as np

import of_common as oc
import t1_tickvol_proxy as t1


def test_anchors():
    # 2026-07-01: London BST (UTC+1), NY EDT (UTC-4): 08:00 London = 03:00 NY = server 10:00 -> 600
    assert oc.anchor_smin('EURUSD', 'A1', date(2026, 7, 1)) == 600
    # 2026-03-16: US already on DST (since 03-08), UK not (until 03-29): 08:00 GMT = 04:00 EDT -> server 11:00 -> 660
    assert oc.anchor_smin('EURUSD', 'A1', date(2026, 3, 16)) == 660
    # 2026-01-15: GMT vs EST: 08:00 GMT = 03:00 EST -> 600
    assert oc.anchor_smin('EURUSD', 'A1', date(2026, 1, 15)) == 600
    # A2 is NY-local: 08:30 NY -> server 15:30 -> 930; gold 08:20 -> 920 (DST-invariant in server minutes)
    assert oc.anchor_smin('EURUSD', 'A2', date(2026, 1, 15)) == 930
    assert oc.anchor_smin('XAUUSD', 'A2', date(2026, 7, 1)) == 920
    assert oc.PRIMARY_ANCHOR['XAUUSD'] == 'A2' and oc.secondary_anchor('XAUUSD') == 'A1'


def test_va_identical_to_t1():
    rng = np.random.default_rng(1)
    for _ in range(300):
        v = rng.gamma(0.7, 1.0, rng.integers(3, 80))
        assert oc.va_greedy(v) == t1.va_greedy(v)


def test_value_area_edges():
    # uniform volume on 10 bins of width 1 (prices 100..109.9): VA = 7-8 bins around the POC (lowest bin on ties)
    tp = np.repeat(np.arange(100.5, 110.5, 1.0), 5)
    tv = np.ones_like(tp)
    val, vah, poc = oc.value_area(tp, tp, tp, tv, 1.0)
    assert poc == 100.5 and val == 100.0
    assert abs((vah - val) - 7.0) < 1e-9          # 7 bins hold 70 %
    # single spike: VA collapses near the spike
    tv2 = tv.copy(); tv2[25] = 1000
    val2, vah2, poc2 = oc.value_area(tp, tp, tp, tv2, 1.0)
    assert val2 <= tp[25] < vah2 and vah2 - val2 <= 1.0 + 1e-9


def test_bh_and_verdict():
    adj = oc.bh([0.01, 0.04, 0.03, None])
    assert adj[3] is None and abs(adj[0] - 0.03) < 1e-12 and abs(adj[1] - 0.04) < 1e-12 and abs(adj[2] - 0.04) < 1e-12
    assert oc.verdict(0.05, 0.02, 0.01, 0.02, 0.01, 0.03) == 'SUPPORTED'
    assert oc.verdict(0.05, 0.02, 0.01, 0.02, 0.01, 0.03, extra_ok=False) == 'INCONCLUSIVE'
    assert oc.verdict(0.05, 0.02, 0.01, -0.02, 0.01, 0.03) == 'REJECTED'      # disc/holdout opposite signs
    assert oc.verdict(0.05, 0.02, 0.01, 0.02, -0.01, -0.001) == 'REJECTED'    # pooled <= 0
    assert oc.verdict(0.05, 0.20, 0.01, 0.02, 0.01, 0.03) == 'INCONCLUSIVE'


def test_bootstrap_reproducible_and_calibrated():
    rng = np.random.default_rng(5)
    x = rng.normal(0.0, 1.0, 1500)
    r1 = oc.bootstrap(lambda i: x[i].mean(), len(x), B=400)
    r2 = oc.bootstrap(lambda i: x[i].mean(), len(x), B=400)
    assert np.array_equal(r1, r2)
    s = oc.boot_summary(float(x.mean()), r1)
    assert s['ci95'][0] < 0 < s['ci95'][1] or abs(x.mean()) > 0.05
    y = x + 0.3
    s2 = oc.boot_summary(float(y.mean()), oc.bootstrap(lambda i: y[i].mean(), len(y), B=400))
    assert s2['ci95'][0] > 0 and s2['p_one_sided'] < 0.01


def test_rotation_and_daytype():
    import of20
    # 30-min period highs/lows: strictly rising -> all +1 -> ROT 0
    Hs = np.array([1, 2, 3, 4, 5.0]); Ls = np.array([0, 1, 2, 3, 4.0])
    assert of20.rot_count(Hs, Ls) == 0
    # up, down, up, down -> 3 sign changes
    Hs = np.array([1, 2, 1.5, 2.5, 2.0]); Ls = np.array([0, 0.5, 0.2, 0.6, 0.3])
    assert of20.rot_count(Hs, Ls) == 3
    # inside/outside periods are 0 and ignored
    Hs = np.array([1, 2, 1.9, 3.0]); Ls = np.array([0, 0.5, 0.6, 0.7])
    assert of20.rot_count(Hs, Ls) == 0
    # trend-day classifier on a synthetic up-trend session
    st = of20.classify(O=100, H=110, L=100, C=109.5, IBH=103, IBL=100, ROT=1)
    assert st['TD'] == 1 and st['TDlite'] == 1
    st = of20.classify(O=100, H=110, L=99, C=109.5, IBH=103, IBL=100, ROT=1)   # down-extension too -> not TD
    assert st['TD'] == 0 and st['TDlite'] == 1
    st = of20.classify(O=100, H=104, L=96, C=100.2, IBH=102, IBL=98, ROT=4)
    assert st['BAL1'] == 1 and st['TD'] == 0


def test_break_acceptance():
    import of19
    # IB [100, 101]; bars after IB: close 101.2 (break up) then lows stay >= 101 for 30 bars -> accepted
    sm = np.arange(0, 200)
    h = np.full(200, 100.8); l = np.full(200, 100.2); c = np.full(200, 100.5); o = c.copy()
    a = 0
    h[60] = 101.3; c[60] = 101.2; l[60] = 100.9
    h[61:91] = 101.5; l[61:91] = 101.05; c[61:91] = 101.3
    h[91:] = 101.6; l[91:] = 101.1; c[91:] = 101.4
    ev = of19.find_break(sm, o, h, l, c, a, IBH=101.0, IBL=100.0, m=30, end_min=200)
    assert ev is not None and ev['beta'] == 1 and ev['accepted'] and ev['t_a_pos'] == 90
    # same but one bar trades back inside -> failed
    l2 = l.copy(); l2[70] = 100.99
    ev2 = of19.find_break(sm, o, h, l2, c, a, IBH=101.0, IBL=100.0, m=30, end_min=200)
    assert ev2 is not None and not ev2['accepted']
    # a break too late for the acceptance window is ignored
    ev3 = of19.find_break(sm, o, h, l, c, a, IBH=101.0, IBL=100.0, m=30, end_min=80)
    assert ev3 is None


def test_trade_math():
    import of19
    # long: entry 101.2 (bid open 101.19 + spread 0.01), stop at IBH 101.0 -> D = 0.2; exit at close 101.6 bid
    sm = np.arange(0, 10); o = np.array([101.19] * 10); h = np.array([101.7] * 10); l = np.array([101.1] * 10)
    c = np.array([101.6] * 10)
    r = of19.trade_outcome(sm, o, h, l, c, entry_pos=0, beta=1, level=101.0, spread=0.01, comm=0.0)
    assert abs(r['D'] - 0.2) < 1e-12 and abs(r['R'] - (101.6 - 101.2) / 0.2) < 1e-9 and r['exit'] == 'E'
    # stop hit: a bar with low below IBH -> exit at IBH
    l2 = l.copy(); l2[4] = 100.9
    r2 = of19.trade_outcome(sm, o, h, l2, c, entry_pos=0, beta=1, level=101.0, spread=0.01, comm=0.0)
    assert abs(r2['R'] - (-1.0)) < 1e-9 and r2['exit'] == 'stop'
    # short mirror with spread paid on exit
    o3 = np.array([99.0] * 10); h3 = np.array([99.05] * 10); l3 = np.array([98.5] * 10); c3 = np.array([98.6] * 10)
    r3 = of19.trade_outcome(sm, o3, h3, l3, c3, entry_pos=0, beta=-1, level=100.0, spread=0.02, comm=0.0)
    assert abs(r3['D'] - 1.0) < 1e-12 and abs(r3['R'] - (99.0 - 98.62) / 1.0) < 1e-9


def test_of16_hits():
    import of16
    assert of16.bias(105, val=100, vah=104) == 1 and of16.bias(99, 100, 104) == -1 and of16.bias(102, 100, 104) == 0
    # barrier: favourable first -> 1; both in one bar -> 0; none -> unresolved
    h = np.array([100.2, 100.6]); l = np.array([99.9, 99.8])
    assert of16.barrier(h, l, O=100.0, b=1, dist=0.5) == (1, True)
    h = np.array([100.6]); l = np.array([99.4])
    assert of16.barrier(h, l, O=100.0, b=1, dist=0.5) == (0, True)
    h = np.array([100.1]); l = np.array([99.9])
    assert of16.barrier(h, l, O=100.0, b=1, dist=0.5) == (0, False)


def test_of20b_normalised_periods():
    import of20b
    # 8 h 40 m session (gold A2: server 920 -> 1440, T = 520): period length 40 min
    a, T = 920, 520
    sm = np.arange(a, 1440)
    j = of20b.partition13(sm, a, T)
    assert j[0] == 0 and j[39] == 0 and j[40] == 1 and j[-1] == 12 and len(set(j.tolist())) == 13
    assert all((j == k).sum() == 40 for k in range(13))
    # 14 h session (FX A1 winter: 600 -> 1440, T = 840): 840*13 not integral per period; all 13 present, sizes 64-65
    a2, T2 = 600, 840
    sm2 = np.arange(a2, 1440)
    j2 = of20b.partition13(sm2, a2, T2)
    sizes = [(j2 == k).sum() for k in range(13)]
    assert j2[-1] == 12 and sum(sizes) == 840 and min(sizes) >= 64 and max(sizes) <= 65
    # usable / valid: drop all bars of 2 periods -> 11 usable (valid); drop 3 -> 10 (invalid)
    keep = ~np.isin(j, [3, 7])
    u = of20b.usable_periods(j[keep], T)
    assert u.sum() == 11
    keep3 = ~np.isin(j, [3, 7, 9])
    assert of20b.usable_periods(j[keep3], T).sum() == 10
    # a period with < 50 % of its minutes having bars is unusable
    thin = ~((j == 5) & (np.arange(len(j)) % 3 != 0))      # keep ~1/3 of period 5
    assert not of20b.usable_periods(j[thin], T)[5]
    # IB_b = first 2/13 of the session (80 min here)
    h = np.where(sm - a < 80, 101.0, 105.0); l = np.where(sm - a < 80, 99.0, 104.0)
    h[10] = 102.0; l[79] = 98.5
    assert of20b.ib_b(sm, h, l, a, T) == (102.0, 98.5)
    assert of20b.ib_b(sm[sm - a >= 20], h[sm - a >= 20], l[sm - a >= 20], a, T) is None   # < 90 % coverage
    # theta_A
    assert of20b.theta_A(13) == 2 and of20b.theta_A(17) == 2 and of20b.theta_A(28) == 4
    # ROT13 on a constructed monotone-up path -> 0; classify_b trend day with thr 2
    Hs = np.arange(1, 14, dtype=float); Ls = Hs - 1
    import of20
    assert of20.rot_count(Hs, Ls) == 0
    st = of20b.classify_b(O=100, H=110, L=100, C=109.5, IBH=103, IBL=100, ROT=0, thr=2)
    assert st['TD'] == 1 and st['dir'] == 1 and st['BAL1'] == 0
    st = of20b.classify_b(O=100, H=104, L=96, C=100.2, IBH=102, IBL=98, ROT=5, thr=4)
    assert st['TD'] == 0 and st['BAL1'] == 1


def test_c1_calendar_clock_costs_stops():
    from datetime import date
    import c1_tokyo_fix as c1
    hol = {date(2019, 4, 29), date(2019, 4, 30), date(2019, 5, 1), date(2019, 5, 2), date(2019, 5, 3), date(2019, 5, 6)}
    bd = c1.business_days(date(2019, 4, 1), date(2019, 6, 30), hol)
    got, me = c1.gotobi_days(bd, roll=True)
    # May 5 2019 (Sunday) rolls back past Golden Week to Fri Apr 26; May 10 (Fri) is itself; ME = Fri May 31
    assert date(2019, 4, 26) in got and date(2019, 5, 10) in got and date(2019, 5, 31) in me
    assert date(2019, 5, 7) not in got
    got_nr, _ = c1.gotobi_days(bd, roll=False)
    assert date(2019, 4, 26) in me and date(2019, 4, 26) in got_nr          # Apr 26 is also April's last business day (ME)
    assert date(2019, 6, 14) in got and date(2019, 6, 14) not in got_nr      # Sat Jun 15 rolls to Fri Jun 14 only with roll
    # clock: server 03:55 in US DST and 02:55 in winter are both 00:55 UTC
    um = c1.server_to_utc_min(np.array(['2026-07-01', '2026-01-15'], dtype=object), np.array([235, 175]))
    assert list(um) == [c1.utc_min_of(date(2026, 7, 1), 0), c1.utc_min_of(date(2026, 1, 15), 0)]
    assert c1.utc_min_of(date(2026, 7, 1), -115) == c1.utc_min_of(date(2026, 6, 30), 0) + 24 * 60 - 115  # 23:00 prev day
    # cost arithmetic: long 150.000 -> 150.030 bid, spread 0.002, S1 stress -> net = 1.8667 - 0.7 - 0.5 bp
    o = np.array([150.000, 150.010]); h = np.array([150.02, 150.04]); l = np.array([149.99, 150.0]); c = np.array([150.01, 150.030])
    r = c1.leg(1, o, h, l, c, 0, 1, 0.002, 0.001, 0.25)
    assert abs(r['net_bp'] - ((150.030 - 150.002) / 150.0 * 1e4 - 0.7 - 0.5)) < 1e-9 and r['exit'] == 'time'
    # stop: sig 0.00015 -> stop dist 6bp*150 = 0.09; low 149.90 triggers -> exit at stop (149.912)
    l2 = np.array([149.99, 149.90]); r2 = c1.leg(1, o, h, l2, c, 0, 1, 0.002, 0.00015, 0.0)
    assert r2['exit'] == 'stop' and abs(r2['R'] - ((149.912 - 150.002 - 0.00007 * 150) / 0.09)) < 1e-9
    # gap through stop -> fill at the open
    o3 = np.array([150.000, 149.900]); r3 = c1.leg(1, o3, h, l2, c, 0, 1, 0.002, 0.00015, 0.0)
    assert abs(r3['R'] - ((149.900 - 150.002 - 0.0105) / 0.09)) < 1e-9
    # short leg pays spread on the buy-back
    o4 = np.array([150.0, 149.99]); h4 = np.array([150.0, 150.0]); l4 = np.array([149.98, 149.97]); c4 = np.array([149.99, 149.98])
    r4 = c1.leg(-1, o4, h4, l4, c4, 0, 1, 0.002, 0.001, 0.0)
    assert abs(r4['net_bp'] - ((150.0 - 149.982) / 150.0 * 1e4 - 0.7)) < 1e-9
    # cost floor: tiny sigma -> skipped
    assert c1.leg(1, o, h, l, c, 0, 1, 0.002, 0.000005, 0.0) == {'skip': 'cost_floor'}
    assert len(c1.PLACEBO_OFFSETS) == 44 and 0 not in c1.PLACEBO_OFFSETS and -10 not in c1.PLACEBO_OFFSETS


def test_c2_tsmom_components():
    import pandas as pd
    import c2_tsmom as c2
    # (2) EWMA: constant |r| -> sigma = sqrt(261)*|r| once 60 returns exist; NaN before
    close = 100 * np.exp(0.001 * np.arange(200))
    sg = c2.ewma_sigma(close)
    assert np.isnan(sg[59]) and abs(sg[150] - np.sqrt(261) * 0.001) < 1e-12
    # (3) rollover weights: Wed x3, no weekend nights, 7 per week
    assert c2.ROLL_W == {0: 1, 1: 1, 2: 3, 3: 1, 4: 1} and sum(c2.ROLL_W.values()) == 7
    # (4) charges-only swap: positive points -> 0; negative -> charge; sym gives credit; x2 doubles
    pr = np.array([150.0])
    assert c2.swap_charge_frac(3.01, 0.001, pr, 'charges')[0] == 0.0
    assert abs(c2.swap_charge_frac(-15.62, 0.001, pr, 'charges')[0] - 15.62 * 0.001 / 150) < 1e-15
    assert c2.swap_charge_frac(3.01, 0.001, pr, 'sym')[0] < 0 and c2.swap_charge_frac(-1.0, 0.001, pr, 'none')[0] == 0
    assert abs(c2.swap_charge_frac(-1.0, 0.001, pr, 'x2')[0] - 2 * c2.swap_charge_frac(-1.0, 0.001, pr, 'charges')[0]) < 1e-15
    # synthetic one-instrument panel (100 days: the short opened on day 91 stays inside its 1.37 % stop)
    T = 100
    idx = pd.bdate_range('2020-01-01', periods=T)
    C = 100 * np.exp(0.001 * np.arange(T)); O = np.r_[C[0], C[:-1]]
    def panel(O, H, L, C):
        return {'O': O[:, None], 'H': H[:, None], 'L': L[:, None], 'C': C[:, None], 'dates': idx,
                'symbols': ['USDJPY'], 'valid': np.ones((T, 1), bool)}
    P = panel(O, np.maximum(O, C) * 1.0001, np.minimum(O, C) * 0.9999, C)
    specs = {'USDJPY': {'swap_long': 0.0, 'swap_short': 0.0, 'point': 0.001}}
    # (1) signal causality: signal at a decision equals the signal computed on data truncated at that decision
    dec = np.array([70, 90])
    s_full = c2.signals_at(P, dec, 21)
    Pt = {k: (v[:91] if isinstance(v, np.ndarray) else v) for k, v in P.items()}; Pt['dates'] = idx[:91]
    assert np.array_equal(s_full[1], c2.signals_at(Pt, np.array([90]), 21)[0]) and s_full[1, 0] == 1
    # (5) turnover cost: +1 then -1 with leverage cap 3 -> turnover 3 + 6 = 9; zero-cost run has no stops
    S = np.array([[[1.0], [-1.0]]])
    sim = c2.simulate(P, specs, dec, S, slip='S0', swap='none', cost_mult=0.0)
    assert abs(sim['turnover'][0] - 9.0) < 1e-9 and sim['stops'] == 0
    side = c2.side_cost_frac('USDJPY', np.array([150.0]), 0.5)[0]
    assert abs(side - (0.35 + 0.005 / 2 / 150 * 1e4 + 0.5) / 1e4) < 1e-15
    # (6) catastrophe stop with a gap: long from day 71; day 80 opens 20 % lower -> fill at the open
    O2, C2_, H2, L2 = O.copy(), C.copy(), np.maximum(O, C) * 1.0001, np.minimum(O, C) * 0.9999
    O2[80] = C2_[79] * 0.8; L2[80] = O2[80] * 0.999; C2_[80] = O2[80]; H2[80] = O2[80] * 1.001
    P2 = panel(O2, H2, L2, C2_)
    sim2 = c2.simulate(P2, specs, np.array([70]), np.array([[[1.0]]]), slip='S0', swap='none', cost_mult=0.0)
    assert sim2['stops'] == 1 and abs(sim2['daily'][0, 80] - 3.0 * (O2[80] / C2_[79] - 1)) < 1e-12
    assert sim2['daily'][0, 85] == 0.0                         # flat after the stop
    # (7) circular shift keeps valid months and flip count within 1 (wrap junction)
    rng = np.random.default_rng(1)
    base = np.r_[[np.nan] * 5, np.sign(np.sin(np.arange(100) / 7.0))]
    rot = c2.circular_shift(base[:, None], rng, 20)
    flips = lambda v: int(np.sum(v[1:] != v[:-1]))
    for r in range(20):
        v = rot[r, :, 0]
        assert np.isnan(v[:5]).all() and np.isfinite(v[5:]).all()
        assert abs(flips(v[5:]) - flips(base[5:])) <= 1


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for f in tests:
        f()
        print('PASS', f.__name__)
    print(f'{len(tests)} tests passed')
