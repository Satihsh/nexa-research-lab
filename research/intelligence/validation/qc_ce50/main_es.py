# NEXA H-CE50 on CME index futures. Pre-registration: PREREG_CE50.md.
# "CE 50 % Model": range 08:30-09:29 ET, midline; the 09:30-09:32 candle close vs the midline picks the side; entry at
# the 09:33 open; stop 1 tick beyond the far side of the range, trailed to confirmed 15-minute swings (tighten only);
# exit at the stop or the 15:59 close. Binding set P = 2010-2015 (outside the creator's 2016-2026 backtest).
# 500 random-direction controls. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
from datetime import date, timedelta
import numpy as np

MODE = 'ES'                 # 'NQ' binding / 'ES'
TICK = 0.25
COST = {'NQ': (1.0, 2.0, 3.0), 'ES': (0.30, 0.60, 1.20)}   # S0, S1, S2 points round trip
SEED, B_BOOT, BLOCK, N_CTRL = 20261022, 2000, 20, 500
FIRST_DAY, IN_FROM = date(2010, 1, 4), date(2016, 1, 4)
M0, NB = 510, 450           # 08:30 ET; 450 bars to the 15:59 bar
K_RNG, K_SIG, K_ENTRY, K_LAST = 60, 62, 63, 449   # range bars 0..59; signal close = bar 62 (09:32); entry 63 (09:33)
K_OPEN, BLK = 60, 15        # 15-minute bars start at 09:30 (bar 60)
MIN_R_TICKS = 4
N_TRIALS = 2


# ---------------------------------------------------------------- statistics (as qc_orb5 / qc_hougaard)
def block_indices(n, rng, L=BLOCK):
    if n <= L:
        return rng.integers(0, n, n)
    nb = int(math.ceil(n / L))
    st = rng.integers(0, n - L + 1, nb)
    return (st[:, None] + np.arange(L)[None, :]).ravel()[:n]


def _f(x, nd=5):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, nd) if np.isfinite(x) else None


# ---------------------------------------------------------------- engine (pure functions, unit-tested locally)
def rng_mid(h, l):
    H, L = float(np.max(h[:K_RNG])), float(np.min(l[:K_RNG]))
    return H, L, (H + L) / 2.0


def signal(h, l, c):
    """+1 long / -1 short / 0 doji, from the 09:32 close vs the midline."""
    _, _, M = rng_mid(h, l)
    return 1 if c[K_SIG] > M else (-1 if c[K_SIG] < M else 0)


def blocks15(h, l):
    """15-minute highs and lows from 09:30 (26 blocks to 15:59)."""
    n = (K_LAST + 1 - K_OPEN) // BLK
    hh = np.array([np.max(h[K_OPEN + BLK * j:K_OPEN + BLK * (j + 1)]) for j in range(n)])
    ll = np.array([np.min(l[K_OPEN + BLK * j:K_OPEN + BLK * (j + 1)]) for j in range(n)])
    return hh, ll


def trade(o, h, l, c, d):
    """Trade in direction d (+1/-1) for one day, or a skip reason string."""
    H, L, _ = rng_mid(h, l)
    entry = o[K_ENTRY]
    stop = H + TICK if d < 0 else L - TICK
    if (d < 0 and entry >= stop) or (d > 0 and entry <= stop):
        return 'beyond'
    r = abs(entry - stop)
    if r < MIN_R_TICKS * TICK:
        return 'r_floor'
    hh, ll = blocks15(h, l)
    trail = 0
    for k in range(K_ENTRY, K_LAST + 1):
        # at the start of 15-min block b (b >= 3), the swing at block b-2 (confirmed by block b-1's close) applies
        if k >= K_OPEN and (k - K_OPEN) % BLK == 0:
            b = (k - K_OPEN) // BLK
            j = b - 2
            if j >= 1:
                if d < 0 and hh[j] > hh[j - 1] and hh[j] > hh[j + 1] and hh[j] + TICK < stop:
                    stop, trail = hh[j] + TICK, trail + 1
                if d > 0 and ll[j] < ll[j - 1] and ll[j] < ll[j + 1] and ll[j] - TICK > stop:
                    stop, trail = ll[j] - TICK, trail + 1
        if d < 0 and h[k] >= stop:
            ex = max(stop, o[k])
            return {'dir': d, 'R_pts': r, 'gross': d * (ex - entry), 'kind': 'stop', 'trail': trail}
        if d > 0 and l[k] <= stop:
            ex = min(stop, o[k])
            return {'dir': d, 'R_pts': r, 'gross': d * (ex - entry), 'kind': 'stop', 'trail': trail}
    return {'dir': d, 'R_pts': r, 'gross': d * (c[K_LAST] - entry), 'kind': 'time', 'trail': trail}


def net_r(t, cost):
    return (t['gross'] - cost) / t['R_pts']


def stats(day_trades, costs, dates, per_year=False):
    n = len(day_trades)
    s1 = costs[1]
    dsum = np.array([sum(net_r(t, s1) for t in tl) for tl in day_trades], float)
    dcnt = np.array([len(tl) for tl in day_trades], float)
    allt = [t for tl in day_trades for t in tl]
    nt = len(allt)
    out = {'days': n, 'trades': nt}
    if nt == 0:
        out['S1'] = {'mean': None}
        return out
    rng = np.random.default_rng(SEED)
    reps = np.empty(B_BOOT)
    for b in range(B_BOOT):
        idx = block_indices(n, rng)
        cc = dcnt[idx].sum()
        reps[b] = dsum[idx].sum() / cc if cc > 0 else np.nan
    r = reps[np.isfinite(reps)]
    out['S1'] = {'mean': _f(dsum.sum() / nt), 'ci': [_f(np.percentile(r, 2.5)), _f(np.percentile(r, 97.5))],
                 'p': _f((1 + np.sum(r <= 0)) / (len(r) + 1), 4)}
    rs = np.array([net_r(t, s1) for t in allt])
    out['win'] = _f(np.mean(rs > 0), 4)
    out['avg_win'] = _f(rs[rs > 0].mean() if (rs > 0).any() else None, 3)
    out['avg_loss'] = _f(rs[rs <= 0].mean() if (rs <= 0).any() else None, 3)
    out['max_win'] = _f(rs.max(), 2)
    out['S0'] = _f(np.mean([net_r(t, costs[0]) for t in allt]))
    out['S2'] = _f(np.mean([net_r(t, costs[2]) for t in allt]))
    out['stop_exit'] = _f(np.mean([t['kind'] == 'stop' for t in allt]), 4)
    out['trailed'] = _f(np.mean([t['trail'] > 0 for t in allt]), 4)
    out['long'] = [sum(1 for t in allt if t['dir'] > 0), _f(np.mean([net_r(t, s1) for t in allt if t['dir'] > 0] or [np.nan]))]
    out['short'] = [sum(1 for t in allt if t['dir'] < 0), _f(np.mean([net_r(t, s1) for t in allt if t['dir'] < 0] or [np.nan]))]
    out['R_pts'] = _f(np.mean([t['R_pts'] for t in allt]), 2)
    q = np.array_split(np.arange(n), 4)
    out['blocks'] = [_f(dsum[ix].sum() / dcnt[ix].sum(), 4) if dcnt[ix].sum() > 0 else None for ix in q]
    out['blocks_pos'] = int(sum(1 for v in out['blocks'] if (v or 0) > 0))
    td = dsum[dcnt > 0]
    out['green'] = _f(np.mean(td > 0), 4)
    eq = np.concatenate([[0.0], np.cumsum(dsum)])
    out['max_dd_R'] = _f(np.max(np.maximum.accumulate(eq) - eq), 2)
    run = best = 0
    for x in rs:
        run = run + 1 if x < 0 else 0
        best = max(best, run)
    out['lose_streak'] = best
    if per_year:
        py = {}
        for dd, tl in zip(dates, day_trades):
            for t in tl:
                py.setdefault(dd.year, []).append(net_r(t, s1))
        out['per_year'] = {str(y): [len(v), _f(np.mean(v), 3)] for y, v in sorted(py.items())}
    return out


def verdict(p, inn, ctrl_pct):
    if p['trades'] < 300:
        return 'INSUFFICIENT-N'
    m = p['S1']['mean']
    if m is None or m <= 0:
        return 'REJECTED'
    ok = (m >= 0.025 and (p['S1']['ci'][0] or -1) > 0 and p['S1']['p'] <= 0.05 / N_TRIALS
          and p['blocks_pos'] >= 3 and (inn.get('S1', {}).get('mean') or -1) > 0
          and ctrl_pct is not None and ctrl_pct >= 0.95)
    return 'VALIDATED' if ok else 'INCONCLUSIVE'


def run_all(days, mode):
    """days = chronological valid days: dict(date, o, h, l, c) with NB bars from 08:30 ET."""
    costs = COST[mode]
    days = [d for d in days if d['date'] >= FIRST_DAY]
    dates = [d['date'] for d in days]
    real, skipped = [], {'doji': 0, 'beyond': 0, 'r_floor': 0}
    for d in days:
        sg = signal(d['h'], d['l'], d['c'])
        if sg == 0:
            skipped['doji'] += 1
            real.append([])
            continue
        t = trade(d['o'], d['h'], d['l'], d['c'], sg)
        if isinstance(t, str):
            skipped[t] += 1
            real.append([])
        else:
            real.append([t])
    sets = {'P': [i for i, dd in enumerate(dates) if dd < IN_FROM],
            'IN': [i for i, dd in enumerate(dates) if dd >= IN_FROM],
            'FULL': list(range(len(days)))}
    out = {'mode': mode, 'n_days': len(days), 'first': dates[0].isoformat() if dates else None,
           'last': dates[-1].isoformat() if dates else None, 'skipped_signal': skipped}
    for w, ix in sets.items():
        out[w] = stats([real[i] for i in ix], costs, [dates[i] for i in ix], per_year=(w == 'FULL'))
    # random-direction control over P days with a real trade
    P = [i for i in sets['P'] if real[i]]
    nl, ns = [], []
    for i in P:
        d = days[i]
        for dr, acc in ((1, nl), (-1, ns)):
            t = trade(d['o'], d['h'], d['l'], d['c'], dr)
            acc.append(net_r(t, costs[1]) if isinstance(t, dict) else np.nan)
    pm = []
    if P:
        nl, ns = np.array(nl), np.array(ns)
        rng = np.random.default_rng(SEED)
        for _ in range(N_CTRL):
            pick = np.where(rng.random(len(P)) < 0.5, nl, ns)
            ok = np.isfinite(pick)
            pm.append(float(pick[ok].mean()) if ok.any() else np.nan)
    pv = np.array([x for x in pm if np.isfinite(x)])
    m = out['P']['S1'].get('mean')
    pct = float(np.mean(pv < m)) if (m is not None and len(pv)) else None
    out['control'] = {'n': N_CTRL, 'mean': _f(pv.mean() if len(pv) else None),
                      'p95': _f(np.percentile(pv, 95) if len(pv) else None), 'real_pct': _f(pct, 3)}
    out['verdict'] = verdict(out['P'], out['IN'], pct)
    return out


def log_chunks(algo, tag, obj, size=7000):
    s = json.dumps(obj, separators=(',', ':'))
    parts = [s[i:i + size] for i in range(0, len(s), size)] or ['']
    for i, p in enumerate(parts):
        algo.log(f'{tag} {i + 1}/{len(parts)} {p}')


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaCe50(QCAlgorithm):
    def initialize(self):
        fut = Futures.Indices.NASDAQ_100_E_MINI if MODE == 'NQ' else Futures.Indices.SP_500_E_MINI
        self.set_start_date(2009, 12, 1)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        f = self.add_future(fut, Resolution.MINUTE, fill_forward=False, extended_market_hours=True,
                            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
                            data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
        self.sym = f.symbol
        self.day, self.roll, self.roll_pending = None, False, False
        self.bars, self.days = {}, []
        self.skipped = {'incomplete': 0, 'roll': 0}

    def on_data(self, data):
        for _ in data.symbol_changed_events.items():
            self.roll_pending = True
        t = self.time - timedelta(minutes=1)
        d = t.date()
        if d != self.day:
            if self.day is not None:
                self.close_day()
            self.roll, self.roll_pending = self.roll_pending, False
        self.day = d
        tb = data.bars.get(self.sym)
        if tb is None:
            return
        m = t.hour * 60 + t.minute
        if M0 <= m < M0 + NB:
            self.bars[m] = (float(tb.open), float(tb.high), float(tb.low), float(tb.close))

    def close_day(self):
        bars, self.bars = self.bars, {}
        if not bars:
            return
        complete = all((M0 + k) in bars for k in range(NB)) and self.day.weekday() < 5
        if not complete:
            self.skipped['incomplete'] += 1
            return
        if self.roll:
            self.skipped['roll'] += 1
            return
        cols = list(zip(*[bars[M0 + k] for k in range(NB)]))
        o, h, l, c = (np.array(x, dtype=np.float64) for x in cols)
        self.days.append({'date': self.day, 'o': o, 'h': h, 'l': l, 'c': c})

    def on_end_of_algorithm(self):
        self.close_day()
        res = run_all(self.days, MODE)
        res['skipped_days'] = self.skipped
        log_chunks(self, 'NEXA_CE50', res)
