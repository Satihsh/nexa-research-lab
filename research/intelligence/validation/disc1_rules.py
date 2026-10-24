"""H-DISC1-RULES (PREREG_DISC1_RULES.md): red-day / green-day rule check on the user's counted H-DISC1 trades.

Usage: python disc1_rules.py <journal_dir> [<extra_recorder_dir> ...] > disc1_rules_result.json
Reads <journal_dir>/trade_review.csv and 1-minute bars from <journal_dir>/recorder/*_M1/ (+ any extra recorder dirs).
Standard library only. Computes B and V1-V4, the per-session differences with a block bootstrap, loss clustering
and a Topstep 50K trailing-loss check. Never changes the H-DISC1 verdict.
"""
import csv
import glob
import json
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

CT = ZoneInfo('America/Chicago')
POINT_USD, COST_RT_USD = 2.0, 2.22          # MNQ $2/point; $1.22 commission + 1 tick slippage per side
WARMUP = 20
DAILY_STOP_USD = -250.0
FLAT_BAR_CT = (15, 7)                         # last bar start used by V3 (flat by 15:08 CT)
SEED, B_BOOT, BLOCK, ALPHA = 20261023, 2000, 5, 0.05 / 4
MLL_USD = 2000.0


def ct_to_utc(s):
    t = datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=CT)
    return t.astimezone(timezone.utc).replace(tzinfo=None)


def load_trades(path):
    """Counted trades (warm-up dropped), oldest first."""
    rows = []
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            try:
                rows.append({'key': r['trip_key'], 'session': r['session'], 'entry_utc': ct_to_utc(r['entry_ct']),
                             'exit_utc': ct_to_utc(r['exit_ct']), 'side': 1 if r['side'].upper().startswith('L') else -1,
                             'qty': float(r['max_qty']), 'entry': float(r['avg_entry']), 'exit': float(r['avg_exit']),
                             'stop': float(r['initial_stop']) if r.get('initial_stop') not in (None, '') else None})
            except (KeyError, ValueError):
                continue
    rows.sort(key=lambda t: t['entry_utc'])
    return rows[WARMUP:]


def load_bars(dirs):
    """{bar_start_utc: (open, high, low, close)} from every bars_*.csv found (first source wins on duplicates)."""
    bars = {}
    for d in dirs:
        for p in sorted(glob.glob(os.path.join(d, '*_M1', 'bars_*.csv'))):
            with open(p, newline='') as f:
                for r in csv.DictReader(f):
                    try:
                        t = datetime.strptime(r['bar_time_utc'][:19], '%Y-%m-%d %H:%M:%S')
                        bars.setdefault(t, (float(r['open']), float(r['high']), float(r['low']), float(r['close'])))
                    except (KeyError, ValueError):
                        continue
    return bars


def risk_usd(t):
    return abs(t['entry'] - t['stop']) * t['qty'] * POINT_USD if t['stop'] is not None else None


def net_usd(t, exit_px):
    return t['side'] * (exit_px - t['entry']) * t['qty'] * POINT_USD - t['qty'] * COST_RT_USD


def trail_exit(t, bars):
    """V3 exit price, or None if no bars after entry up to 15:07 CT."""
    if t['stop'] is None:
        return None
    r_pts = abs(t['entry'] - t['stop'])
    d = t['side']
    stop, best = t['stop'], t['entry']
    k = t['entry_utc'].replace(second=0, microsecond=0) + timedelta(minutes=1)   # entry bar itself not used
    ct_day = k.replace(tzinfo=timezone.utc).astimezone(CT)
    last = ct_day.replace(hour=FLAT_BAR_CT[0], minute=FLAT_BAR_CT[1], second=0, microsecond=0).astimezone(timezone.utc).replace(tzinfo=None)
    seen, close = False, None
    while k <= last:
        b = bars.get(k)
        if b is not None:
            seen = True
            o, h, l, c = b
            if (d > 0 and l <= stop) or (d < 0 and h >= stop):
                return min(stop, o) if d > 0 else max(stop, o)
            best = max(best, h) if d > 0 else min(best, l)
            if d * (best - t['entry']) >= r_pts:
                cand = best - d * r_pts
                stop = max(stop, cand) if d > 0 else min(stop, cand)
            close = c
        k += timedelta(minutes=1)
    return close if seen else None


def session_order(trades):
    out = []
    for t in trades:
        if not out or out[-1] != t['session']:
            if t['session'] not in out:
                out.append(t['session'])
    return out


def apply_daily_stop(trades, nets):
    keep, day, cum = [], None, 0.0
    for t, n in zip(trades, nets):
        if t['session'] != day:
            day, cum = t['session'], 0.0
        if cum <= DAILY_STOP_USD:
            keep.append(None)
            continue
        keep.append(n)
        cum += n
    return keep


def apply_two_loss_pause(trades, nets):
    sessions = session_order(trades)
    keep, streak, blocked = [], 0, set()
    for t, n in zip(trades, nets):
        if t['session'] in blocked:
            keep.append(None)
            continue
        keep.append(n)
        streak = streak + 1 if n < 0 else 0
        if streak >= 2:
            i = sessions.index(t['session'])
            blocked.add(t['session'])
            if i + 1 < len(sessions):
                blocked.add(sessions[i + 1])
            streak = 0
    return keep


def by_session(trades, nets_r):
    d = {}
    for t, x in zip(trades, nets_r):
        d.setdefault(t['session'], 0.0)
        if x is not None:
            d[t['session']] += x
    return d


def block_boot(diffs, seed=SEED):
    n = len(diffs)
    if n == 0:
        return None, None, None
    rng = random.Random(seed)
    reps = []
    for _ in range(B_BOOT):
        idx = []
        while len(idx) < n:
            s = rng.randrange(0, max(1, n - BLOCK + 1))
            idx.extend(range(s, min(s + BLOCK, n)))
        reps.append(sum(diffs[i] for i in idx[:n]) / n)
    m = sum(diffs) / n
    p_le0 = (1 + sum(1 for r in reps if r <= 0)) / (B_BOOT + 1)
    p_ge0 = (1 + sum(1 for r in reps if r >= 0)) / (B_BOOT + 1)
    return m, p_le0, p_ge0


def verdict(m, p_le0, p_ge0):
    if m is None:
        return 'NO DATA'
    if m > 0 and p_le0 <= ALPHA:
        return 'HELPS'
    if m < 0 and p_ge0 <= ALPHA:
        return 'HURTS'
    return 'NO CLEAR DIFFERENCE'


def summary(trades, usd, risk):
    rs = [u / r if (u is not None and r) else None for u, r in zip(usd, risk)]
    kept = [x for x in rs if x is not None]
    days = by_session(trades, rs)
    dv = list(days.values())
    red, green = [x for x in dv if x < 0], [x for x in dv if x > 0]
    eq, peak, mdd = 0.0, 0.0, 0.0
    for x in dv:
        eq += x
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
    # Topstep 50K: trailing EOD loss limit $2,000, locking at the start balance
    bal, hi, breached, low_buf = 0.0, 0.0, False, MLL_USD
    for s in days:
        bal += sum(u for t, u in zip(trades, usd) if t['session'] == s and u is not None)
        floor = min(hi - MLL_USD, 0.0)
        low_buf = min(low_buf, bal - floor)
        breached = breached or bal <= floor
        hi = max(hi, bal)
    return {'trades_kept': len(kept), 'total_R': round(sum(kept), 3), 'mean_R_per_trade': round(sum(kept) / len(kept), 4) if kept else None,
            'sessions': len(dv), 'green_share': round(len(green) / len(dv), 3) if dv else None,
            'avg_red_day_R': round(sum(red) / len(red), 3) if red else None, 'avg_green_day_R': round(sum(green) / len(green), 3) if green else None,
            'worst_day_R': round(min(dv), 3) if dv else None, 'max_drawdown_R': round(mdd, 3),
            'largest_win_R': round(max(kept), 3) if kept else None, 'topstep50k_breached': breached, 'lowest_mll_buffer_usd': round(low_buf, 2)}, rs


def clustering(rs):
    x = [r for r in rs if r is not None]
    if len(x) < 3:
        return {}
    loss = [r < 0 for r in x]
    after = [loss[i] for i in range(1, len(x)) if loss[i - 1]]
    m = sum(x) / len(x)
    var = sum((v - m) ** 2 for v in x)
    ac = sum((x[i] - m) * (x[i - 1] - m) for i in range(1, len(x))) / var if var > 0 else None
    return {'p_loss': round(sum(loss) / len(loss), 3), 'p_loss_after_loss': round(sum(after) / len(after), 3) if after else None,
            'lag1_autocorr_R': round(ac, 3) if ac is not None else None}


def run(trades, bars):
    risk = [risk_usd(t) for t in trades]
    base = [net_usd(t, t['exit']) for t in trades]
    trail, missing = [], 0
    for t, b in zip(trades, base):
        px = trail_exit(t, bars)
        if px is None:
            missing += 1
            trail.append(b)
        else:
            trail.append(net_usd(t, px))
    variants = {'B': base, 'V1': apply_daily_stop(trades, base), 'V2': apply_two_loss_pause(trades, base),
                'V3': trail, 'V4': apply_daily_stop(trades, trail)}
    out = {'trades': len(trades), 'missing_bars_for_V3': missing}
    v3_invalid = len(trades) > 0 and missing / len(trades) > 0.10
    sums, rsets = {}, {}
    for k, usd in variants.items():
        sums[k], rsets[k] = summary(trades, usd, risk)
    base_days = by_session(trades, rsets['B'])
    sess = [s for s in base_days]
    for k in ('V1', 'V2', 'V3', 'V4'):
        vd = by_session(trades, rsets[k])
        diffs = [vd[s] - base_days[s] for s in sess]
        m, p1, p2 = block_boot(diffs)
        v = 'INVALID (bars missing)' if (k in ('V3', 'V4') and v3_invalid) else verdict(m, p1, p2)
        sums[k].update({'mean_delta_R_per_session': round(m, 4) if m is not None else None,
                        'p_delta_le0': round(p1, 4) if p1 is not None else None,
                        'p_delta_ge0': round(p2, 4) if p2 is not None else None, 'verdict': v})
    out['variants'] = sums
    out['clustering'] = clustering(rsets['B'])
    return out


if __name__ == '__main__':
    j = sys.argv[1]
    dirs = [os.path.join(j, 'recorder')] + [os.path.join(d, 'recorder') if os.path.isdir(os.path.join(d, 'recorder')) else d for d in sys.argv[2:]]
    print(json.dumps(run(load_trades(os.path.join(j, 'trade_review.csv')), load_bars(dirs)), indent=1))
