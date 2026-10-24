"""Synthetic tests for disc1_rules.py (PREREG_DISC1_RULES.md s.6). No trades, no market data."""
import importlib.util
import os
import random
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('disc1_rules', os.path.join(HERE, 'disc1_rules.py'))
dr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dr)


def T(session, entry_utc, side, entry, exit_, stop, qty=1.0, key='k'):
    return {'key': key, 'session': session, 'entry_utc': entry_utc, 'exit_utc': entry_utc + timedelta(minutes=10),
            'side': side, 'qty': qty, 'entry': entry, 'exit': exit_, 'stop': stop}


E = datetime(2026, 11, 10, 15, 0)          # 09:00 CST (UTC-6 in November)


def test_costs_and_r():
    t = T('s1', E, 1, 100.0, 110.0, 90.0, qty=2)
    assert dr.risk_usd(t) == 40.0                                 # 10 pts x 2 x $2
    assert abs(dr.net_usd(t, 110.0) - (40.0 - 4.44)) < 1e-9


def test_ct_to_utc_dst():
    assert dr.ct_to_utc('2026-10-21 09:00:00.000') == datetime(2026, 10, 21, 14, 0)   # CDT
    assert dr.ct_to_utc('2026-11-10 09:00:00.000') == datetime(2026, 11, 10, 15, 0)   # CST


def test_daily_stop():
    tr = [T('s1', E, 1, 0, 0, 0), T('s1', E, 1, 0, 0, 0), T('s2', E, 1, 0, 0, 0)]
    assert dr.apply_daily_stop(tr, [-260.0, 100.0, -50.0]) == [-260.0, None, -50.0]
    assert dr.apply_daily_stop(tr, [-100.0, -200.0, 5.0]) == [-100.0, -200.0, 5.0]       # stop only after the cap is hit


def test_two_loss_pause_across_sessions():
    tr = [T('s1', E, 1, 0, 0, 0), T('s2', E, 1, 0, 0, 0), T('s2', E, 1, 0, 0, 0), T('s3', E, 1, 0, 0, 0), T('s4', E, 1, 0, 0, 0)]
    out = dr.apply_two_loss_pause(tr, [-1.0, -1.0, 5.0, 7.0, 9.0])
    assert out == [-1.0, -1.0, None, None, 9.0]                  # rest of s2 + all of s3 skipped


def bars_from(start, rows):
    return {start + timedelta(minutes=i): r for i, r in enumerate(rows)}


def test_trail_activation_and_exit():
    t = T('s', E, 1, 100.0, 0.0, 95.0)                           # 1R = 5 pts
    b = bars_from(E + timedelta(minutes=1), [(100, 103, 99, 102), (102, 108, 101, 107), (107, 112, 106, 111), (111, 111, 106.5, 107)])
    # best 112 after bar 3 -> stop 107; bar 4 low 106.5 <= 107 -> exit at 107
    assert dr.trail_exit(t, b) == 107


def test_trail_stop_first_and_gap():
    t = T('s', E, 1, 100.0, 0.0, 95.0)
    b = bars_from(E + timedelta(minutes=1), [(100, 106, 94, 101)])    # touches stop and +1R in the same bar: stop first
    assert dr.trail_exit(t, b) == 95
    b = bars_from(E + timedelta(minutes=1), [(93, 94, 92, 93)])       # gaps through the stop: fill at the open
    assert dr.trail_exit(t, b) == 93


def test_trail_short_mirror_and_no_lookahead():
    t = T('s', E, -1, 100.0, 0.0, 105.0)
    b = {E.replace(second=0): (100, 120, 80, 100)}                    # the entry bar is ignored
    b.update(bars_from(E + timedelta(minutes=1), [(100, 101, 94, 95), (95, 96, 89, 90), (90, 95, 89, 94)]))
    # best 89 -> stop 94; bar 3 high 95 >= 94 -> exit 94
    assert dr.trail_exit(t, b) == 94


def test_trail_time_exit_and_missing():
    t = T('s', E, 1, 100.0, 0.0, 95.0)
    last = datetime(2026, 11, 10, 21, 7)                             # 15:07 CST
    b = {E + timedelta(minutes=1): (100, 101, 99, 100), last: (100, 102, 99, 101.5), last + timedelta(minutes=1): (0, 999, 0, 0)}
    assert dr.trail_exit(t, b) == 101.5                              # bars after 15:07 CT are not used
    assert dr.trail_exit(t, {}) is None


def test_run_end_to_end_and_verdicts():
    rng = random.Random(5)
    trades, bars = [], {}
    d0 = datetime(2026, 11, 2, 15, 0)
    for i in range(200):
        day = d0 + timedelta(days=i // 2)
        e = day + timedelta(minutes=30 * (i % 2))
        win = rng.random() < 0.45
        trades.append(T(f's{i // 2}', e, 1, 100.0, 108.0 if win else 95.0, 95.0, key=str(i)))
    res = dr.run(trades, bars)
    assert res['missing_bars_for_V3'] == 200 and res['variants']['V3']['verdict'].startswith('INVALID')
    assert res['variants']['B']['trades_kept'] == 200
    assert res['variants']['V1']['trades_kept'] <= 200
    assert res['variants']['V1']['verdict'] in ('HELPS', 'HURTS', 'NO CLEAR DIFFERENCE')
    assert 'p_loss_after_loss' in res['clustering']


def test_clustered_losses_make_pause_help():
    # losses come in streaks: after two losses the next trades are also losses -> V2 should help
    trades = []
    d0 = datetime(2026, 11, 2, 15, 0)
    pattern = [1, -1, -1, -1, -1, 1, 1, 1] * 30
    for i, w in enumerate(pattern):
        e = d0 + timedelta(days=i)
        trades.append(T(f's{i}', e, 1, 100.0, 110.0 if w > 0 else 95.0, 95.0, key=str(i)))
    res = dr.run(trades, {})
    assert res['variants']['V2']['mean_delta_R_per_session'] > 0
    assert res['variants']['V2']['verdict'] == 'HELPS'
    assert res['clustering']['p_loss_after_loss'] > res['clustering']['p_loss']


def test_verdict_thresholds():
    assert dr.verdict(0.3, 0.001, 0.999) == 'HELPS'
    assert dr.verdict(0.3, 0.02, 0.98) == 'NO CLEAR DIFFERENCE'     # 0.02 > 0.0125
    assert dr.verdict(-0.3, 0.999, 0.001) == 'HURTS'
    assert dr.verdict(None, None, None) == 'NO DATA'


def test_topstep_breach():
    trades = [T(f's{i}', E + timedelta(days=i), 1, 100.0, 50.0, 0.0, qty=1, key=str(i)) for i in range(25)]   # -$102.22 each
    s, _ = dr.summary(trades, [dr.net_usd(t, t['exit']) for t in trades], [dr.risk_usd(t) for t in trades])
    assert s['topstep50k_breached'] is True and s['worst_day_R'] < 0


def test_warmup_dropped(tmp=None):
    import tempfile
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'trade_review.csv')
    with open(p, 'w') as f:
        f.write('trip_key,session,entry_ct,exit_ct,side,max_qty,avg_entry,avg_exit,initial_stop\n')
        for i in range(25):
            f.write(f'k{i},2026-11-{2 + i // 2:02d},2026-11-{2 + i // 2:02d} 09:{i % 2 * 30:02d}:00.000,2026-11-{2 + i // 2:02d} 10:00:00.000,LONG,1,100,101,95\n')
    tr = dr.load_trades(p)
    assert len(tr) == 5 and tr[0]['key'] == 'k20'
