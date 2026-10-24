"""Unit tests for ofc1_core.py (PREREG_OFC1 §9). Synthetic data only; no market outcomes."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ofc1_core as of  # noqa: E402

MIN = of.MIN
SPEC = of.INSTR['6E']
FEE, USD = SPEC['fee'], SPEC['usd_tick']


def session(trades, blk=2):
    """trades: list of (minute, price_ticks, size, side 1=B/2=A, sub_ns). Returns the S dict for run_session."""
    trades = sorted(trades, key=lambda x: (x[0], x[4]))
    t = np.array([m * MIN + s for m, _, _, _, s in trades], np.int64)
    px = np.array([p for _, p, _, _, _ in trades], np.int32)
    sz = np.array([q for _, _, q, _, _ in trades], np.int32)
    sd = np.array([d for _, _, _, d, _ in trades], np.int8)
    iid = np.zeros(len(t), np.int32)
    um = t // MIN
    S = {'px': px, 'sz': sz, 'sd': sd, 'umin': um, 'nymod': (um % 1440).astype(np.int16),
         'blk': np.full(len(t), blk, np.int8)}
    S['orders'] = of.orders_of(t, sd, iid, sz, px)
    return S


def buy_stack(minute, p0, close, sub=1000):
    """Candle with a 3-level buy stack at p0..p0+2 (ask 30 vs bid 5 one tick below), closing at `close`."""
    out = []
    for i in range(3):
        out.append((minute, p0 - 1 + i, 5, 2, sub + i))
        out.append((minute, p0 + i, 30, 1, sub + 10 + i))
    out.append((minute, close, 1, 1, sub + 50))
    return out


def sell_stack(minute, p0, close, sub=1000):
    """3-level sell stack at p0..p0+2 (bid 30 vs ask 5 one tick above), closing at `close`."""
    out = []
    for i in range(3):
        out.append((minute, p0 + 1 + i, 5, 1, sub + i))
        out.append((minute, p0 + i, 30, 2, sub + 10 + i))
    out.append((minute, close, 1, 2, sub + 50))
    return out


PROF = of.Profile(VAL=1000, VAH=1200, lvn=np.array([950.0, 1300.0]))
THR = {0: 50, 1: 50, 2: 50}
BASE = np.zeros(1440)


def test_pct_from_hist_matches_numpy():
    rng = np.random.default_rng(1)
    for _ in range(20):
        x = rng.integers(1, 200, rng.integers(5, 3000))
        h = np.bincount(x)
        for q in (50, 90, 99, 99.9):
            assert abs(of.pct_from_hist(h, q) - np.percentile(x, q)) < 1e-9


def test_imbalance_and_stack_rules():
    px = np.array([99, 100, 100, 101, 101, 102], np.int32)
    sz = np.array([5, 30, 5, 30, 5, 30], np.int32)
    sd = np.array([2, 1, 2, 1, 2, 1], np.int8)
    assert of.stacks(px, sz, sd) == (True, False)
    sz2 = sz.copy(); sz2[1] = 9                                           # ask below min volume 10
    assert not of.stacks(px, sz2, sd)[0]
    keep = np.array([False, True, True, True, True, True])                # bid at p-1 = 0 -> excluded
    assert not of.stacks(px[keep], sz[keep], sd[keep])[0]
    assert of.stacks(px, sz, sd, min_stack=2)[0]
    sz3 = sz.copy(); sz3[1] = 14                                          # 14 < 3*5 ratio fails at level 100
    assert not of.stacks(px, sz3, sd)[0]


def test_profile_va_and_lvn():
    v = np.array([1, 5, 9, 5, 1, 0.5, 1, 6, 10, 6, 1], float)            # bimodal; trough at index 5
    px = np.repeat(np.arange(len(v)) * 2, (v * 10).astype(int)).astype(np.int32)
    pr = of.profile_of(px, np.ones(len(px), np.int32), row=2)
    assert pr.VAL % 2 == 0 and pr.VAH % 2 == 0 and pr.VAL < pr.VAH
    assert np.any(np.isclose(pr.lvn, 5 * 2 + 0.5))                       # row 5 midpoint (row = 2 ticks)


def test_exit_order_and_fills():
    px = np.array([110, 112, 105, 99, 130], np.int32)
    f, k, _ = of.simulate_exit(px, None, 0, +1, 108, 100, 120)
    assert (f, k) == (98, 'stop')                                         # 99 <= stop 100 -> fill 99 - 1
    px2 = np.array([110, 121, 99], np.int32)
    assert of.simulate_exit(px2, None, 0, +1, 108, 100, 120)[:2] == (120, 'target')   # 121 > 120 strictly
    px3 = np.array([110, 120, 115], np.int32)
    assert of.simulate_exit(px3, None, 0, +1, 108, 100, 120)[:2] == (114, 'time')     # 120 not beyond target
    assert of.simulate_exit(np.array([95, 99], np.int32), None, 0, -1, 98, 101, 90)[:2] == (100, 'time')


def _setup_a(confirm_ok=True):
    # context candle inside value; big seller order (60 lots, 1005-1006) near VAL; bubble candle closes at 1006
    tr = [(0, 1100, 1, 1, 0), (1, 1006, 40, 2, 5), (1, 1005, 20, 2, 5), (1, 1006, 1, 1, 9)]
    tr += buy_stack(2, 1015, 1020) if confirm_ok else [(2, 1020, 1, 2, 0)]
    tr += [(3, 1100, 1, 1, 0), (4, 1201, 1, 1, 0)]
    return session(tr)


def test_setup_a_long_to_vah_with_costs():
    trs, sk, _ = of.run_session(_setup_a(), PROF, THR, BASE, of.Params(), SPEC)
    assert len(trs) == 1 and trs[0]['setup'] == 'A' and trs[0]['kind'] == 'target'
    t = trs[0]
    assert t['entry'] == 1021 and t['stop'] == 1004 and t['risk'] == 17 and t['exit'] == 1200
    r0 = ((1200 - 1021) * USD - 2 * FEE) / (17 * USD)
    assert math.isclose(t['R0'], r0)
    assert math.isclose(t['R1'], r0 - USD / (17 * USD))                    # S1: +1 tick on entry only (target exit)


def test_bubble_own_candle_can_trigger_and_floor_ends_pending():
    tr = [(0, 1100, 1, 1, 0), (1, 1006, 40, 2, 5), (1, 1005, 20, 2, 5), (1, 1008, 1, 1, 9)]
    tr += [(2, 1020, 1, 2, 0), (3, 1201, 1, 1, 0)]
    trs, sk, _ = of.run_session(session(tr), PROF, THR, BASE, of.Params(confirm=False), SPEC)
    assert trs == [] and sk['cost_floor'] == 1                            # own candle 1008 > 1006 -> risk 5 -> skip, pending ends


def test_setup_a_needs_confirmation_but_n2_does_not():
    S = _setup_a(confirm_ok=False)
    assert of.run_session(S, PROF, THR, BASE, of.Params(), SPEC)[0] == []
    assert len(of.run_session(S, PROF, THR, BASE, of.Params(confirm=False), SPEC)[0]) == 1


def test_context_outside_value_blocks_pending():
    tr = [(0, 1250, 1, 1, 0), (1, 1006, 40, 2, 5), (1, 1005, 20, 2, 5), (1, 1008, 1, 1, 9)]
    tr += buy_stack(2, 1015, 1020) + [(3, 1201, 1, 1, 0)]
    assert of.run_session(session(tr), PROF, THR, BASE, of.Params(), SPEC)[0] == []


def test_setup_b_short_to_lvn_and_no_lvn_no_trade():
    tr = [(0, 1100, 1, 1, 0), (1, 1010, 40, 2, 5), (1, 1005, 20, 2, 5), (1, 1007, 1, 1, 9)]
    tr += sell_stack(2, 993, 995) + [(3, 960, 1, 2, 0), (4, 949, 1, 2, 0)]
    trs, _, _ = of.run_session(session(tr), PROF, THR, BASE, of.Params(), SPEC)
    assert len(trs) == 1 and trs[0]['setup'] == 'B' and trs[0]['dir'] == -1
    assert trs[0]['entry'] == 994 and trs[0]['stop'] == 1011 and trs[0]['exit'] == 950 and trs[0]['kind'] == 'target'
    nolvn = of.Profile(1000, 1200, np.array([1300.0]))
    trs2, sk2, _ = of.run_session(session(tr), nolvn, THR, BASE, of.Params(), SPEC)
    assert trs2 == [] and sk2['no_target'] == 1


def test_a_invalidated_by_close_below_bubble_above_val():
    prof = of.Profile(VAL=990, VAH=1200, lvn=np.array([900.0]))
    tr = [(0, 1100, 1, 1, 0), (1, 1000, 40, 2, 5), (1, 995, 20, 2, 5), (1, 998, 1, 1, 9)]
    tr += [(2, 992, 1, 2, 0)]                                             # close below bubble low (995), above VAL
    tr += buy_stack(3, 1010, 1015) + [(4, 1201, 1, 1, 0)]
    assert of.run_session(session(tr), prof, THR, BASE, of.Params(), SPEC)[0] == []


def test_mirror_a_short_to_val():
    tr = [(0, 1100, 1, 1, 0), (1, 1190, 40, 1, 5), (1, 1196, 20, 1, 5), (1, 1193, 1, 2, 9)]
    tr += sell_stack(2, 1176, 1178) + [(3, 1050, 1, 2, 0), (4, 999, 1, 2, 0)]
    trs, _, _ = of.run_session(session(tr), PROF, THR, BASE, of.Params(), SPEC)
    assert len(trs) == 1 and trs[0]['setup'] == 'A_m' and trs[0]['stop'] == 1197 and trs[0]['exit'] == 1000


def test_cost_floor_skip_counted():
    tr = [(0, 1100, 1, 1, 0), (1, 1006, 40, 2, 5), (1, 1005, 20, 2, 5), (1, 1008, 1, 1, 9)]
    tr += buy_stack(2, 1006, 1009) + [(3, 1201, 1, 1, 0)]                 # risk = 1010 - 1004 = 6 ticks
    trs, sk, _ = of.run_session(session(tr), PROF, THR, BASE, of.Params(), SPEC)
    assert trs == [] and sk['cost_floor'] == 1
    assert len(of.run_session(session(tr), PROF, THR, BASE, of.Params(cost_floor=False), SPEC)[0]) == 1


def test_most_recent_vs_first_bubble():
    tr = [(0, 1100, 1, 1, 0), (1, 1006, 60, 2, 5), (1, 1007, 1, 1, 9),
          (2, 1012, 60, 2, 5), (2, 1013, 1, 1, 9)]                        # second bubble higher (still near VAL)
    tr += buy_stack(3, 1015, 1030) + [(4, 1201, 1, 1, 0)]
    recent = of.run_session(session(tr), PROF, THR, BASE, of.Params(cost_floor=False), SPEC)[0]
    first = of.run_session(session(tr), PROF, THR, BASE, of.Params(cost_floor=False, first_bubble=True), SPEC)[0]
    assert recent[0]['stop'] == 1011 and first[0]['stop'] == 1005


def test_clock_blocks_and_server_day():
    from datetime import datetime, timezone
    def ns(s):
        return int(datetime.strptime(s, '%Y-%m-%d %H:%M').replace(tzinfo=timezone.utc).timestamp()) * of.NS
    t = np.array([ns('2026-01-15 14:00'), ns('2026-01-15 07:30'), ns('2026-01-15 08:30'),
                  ns('2026-07-15 12:00'), ns('2026-07-15 12:45'), ns('2026-01-15 23:00')], np.int64)
    nyo = of.tz_offset_ns(t, 'America/New_York')
    ldo = of.tz_offset_ns(t, 'Europe/London')
    b = of.block_code(((t + nyo) // MIN) % 1440, ((t + ldo) // MIN) % 1440)
    assert b.tolist() == [2, 0, 1, 1, 2, 0]
    sday = (t + nyo + 7 * of.HOUR) // of.DAY
    assert of.day_str(int(sday[-1])) == '2026-01-16'                      # 18:00 NY -> next server day


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for f in fns:
        f()
        print('PASS', f.__name__)
    print(f'{len(fns)}/{len(fns)} PASS')
