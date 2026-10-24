# NEXA H-HOUGAARD on CME index futures. Pre-registration: PREREG_HOUGAARD.md.
# Tom Hougaard's pre-open breakout: high/low of the 59 minutes 08:30-09:28 ET; buy stop at the high, sell stop at the
# low, active 09:29-10:29; first fill cancels the other; stop 0.0257 % / target 0.0171 % of entry (A) or 1:1 (B);
# stop first on ties; time exit at the 11:29 bar close. 500 random-direction controls. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
from datetime import date, timedelta
import numpy as np

MODE = 'ES'                 # 'NQ' binding / 'ES' / 'YM' (Dow futures, the source instrument)
TICKS = {'NQ': 0.25, 'ES': 0.25, 'YM': 1.0}
COST = {'NQ': (1.0, 2.0, 3.0), 'ES': (0.30, 0.60, 1.20), 'YM': (2.0, 3.0, 5.0)}   # S0, S1, S2 points round trip
SEED, B_BOOT, BLOCK, N_CTRL = 20261022, 2000, 20, 500
FIRST_DAY, POST_FROM = date(2010, 1, 4), date(2021, 8, 10)
M0, NB = 510, 180           # 08:30 ET, 180 bars to the 11:29 bar
K_WIN, K_ON, K_OFF, K_LAST = 59, 59, 119, 179   # window bars 0..58; orders active 59..119; time exit at 179
STOP_PCT, TGT_PCT = 9 / 35000, 6 / 35000
N_TRIALS = 6


# ---------------------------------------------------------------- statistics (as qc_orb5)
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
def rtick(x, tick):
    return round(x / tick) * tick


def distances(entry, tick, variant, fixed=None):
    """(stop_pts, target_pts). fixed = (stop, target) in points for the YM literal cut."""
    if fixed:
        return fixed
    stop = max(rtick(STOP_PCT * entry, tick), 2 * tick)
    tgt = stop if variant == 'B' else max(rtick(TGT_PCT * entry, tick), tick)
    return stop, tgt


def window(h, l):
    return float(np.max(h[:K_WIN])), float(np.min(l[:K_WIN]))


def bracket(h, l, c, k0, d, entry, stop_pts, tgt_pts):
    """Exit from bar k0 (the entry bar included), stop first on ties, else the 11:29 close. Returns (gross_R, kind)."""
    stop, tgt = entry - d * stop_pts, entry + d * tgt_pts
    for k in range(k0, K_LAST + 1):
        if (l[k] <= stop) if d > 0 else (h[k] >= stop):
            return -1.0, 'stop'
        if (h[k] >= tgt) if d > 0 else (l[k] <= tgt):
            return tgt_pts / stop_pts, 'target'
    return d * (c[K_LAST] - entry) / stop_pts, 'time'


def side_trigger(o, h, l, d, H, L):
    """First bar in the active window where side d triggers, and its fill price (gap -> bar open)."""
    for k in range(K_ON, K_OFF + 1):
        if d > 0 and h[k] >= H:
            return k, max(H, o[k])
        if d < 0 and l[k] <= L:
            return k, min(L, o[k])
    return None, None


def real_trade(o, h, l, c, tick, variant, fixed=None):
    """The OCO trade of one day, or None if neither level traded. A bar touching both levels first = -1R."""
    H, L = window(h, l)
    for k in range(K_ON, K_OFF + 1):
        up, dn = h[k] >= H, l[k] <= L
        if up and dn:
            s, _ = distances(H, tick, variant, fixed)
            return {'dir': 0, 'k': k, 'stop_pts': s, 'gross': -1.0, 'kind': 'both'}
        if up or dn:
            d = 1 if up else -1
            entry = max(H, o[k]) if up else min(L, o[k])
            s, t = distances(entry, tick, variant, fixed)
            g, kind = bracket(h, l, c, k, d, entry, s, t)
            return {'dir': d, 'k': k, 'stop_pts': s, 'tgt_pts': t, 'gross': g, 'kind': kind}
    return None


def control_trade(o, h, l, c, tick, variant, d, k_real):
    """Random-direction control: side d at its own trigger, or at the real trigger bar's open if it never traded."""
    H, L = window(h, l)
    k, entry = side_trigger(o, h, l, d, H, L)
    if k is None:
        k, entry = k_real, o[k_real]
    s, t = distances(entry, tick, variant)
    g, _ = bracket(h, l, c, k, d, entry, s, t)
    return g, s


def net_r(t, cost):
    return t['gross'] - cost / t['stop_pts']


def stats(day_trades, costs, dates, per_year=False):
    """day_trades: one list (0 or 1 trade) per valid day, chronological."""
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
    mean = dsum.sum() / nt
    out['S1'] = {'mean': _f(mean), 'ci': [_f(np.percentile(r, 2.5)), _f(np.percentile(r, 97.5))],
                 'p': _f((1 + np.sum(r <= 0)) / (len(r) + 1), 4)}
    rs = np.array([net_r(t, s1) for t in allt])
    tr = [t for t in allt if t['kind'] != 'both']
    out['fill'] = _f(nt / n, 4)
    out['win'] = _f(np.mean(rs > 0), 4)
    out['be_win'] = _f(np.mean([(t['stop_pts'] + s1) / (t['stop_pts'] + t['tgt_pts']) for t in tr]), 4) if tr else None
    out['S0'] = _f(np.mean([net_r(t, costs[0]) for t in allt]))
    out['S2'] = _f(np.mean([net_r(t, costs[2]) for t in allt]))
    out['gross'] = _f(np.mean([t['gross'] for t in allt]))
    out['long'] = [sum(1 for t in allt if t['dir'] > 0), _f(np.mean([net_r(t, s1) for t in allt if t['dir'] > 0] or [np.nan]))]
    out['short'] = [sum(1 for t in allt if t['dir'] < 0), _f(np.mean([net_r(t, s1) for t in allt if t['dir'] < 0] or [np.nan]))]
    out['time_exit'] = _f(np.mean([t['kind'] == 'time' for t in allt]), 4)
    out['both'] = sum(1 for t in allt if t['kind'] == 'both')
    out['stop_pts'] = _f(np.mean([t['stop_pts'] for t in allt]), 3)
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


def verdict(full, post, ctrl_pct):
    if full['trades'] < 300:
        return 'INSUFFICIENT-N'
    m = full['S1']['mean']
    if m is None or m <= 0:
        return 'REJECTED'
    ok = (m >= 0.025 and (full['S1']['ci'][0] or -1) > 0 and full['S1']['p'] <= 0.05 / N_TRIALS
          and full['blocks_pos'] >= 3 and (post.get('S1', {}).get('mean') or -1) > 0
          and ctrl_pct is not None and ctrl_pct >= 0.95)
    return 'VALIDATED' if ok else 'INCONCLUSIVE'


def control(days, real, tick, variant, cost):
    """500 replicates: every day with a real trade gets a random direction; mean net R at S1 per replicate."""
    ix = [i for i, tl in enumerate(real) if tl]
    if not ix:
        return {'n': N_CTRL, 'mean': None, 'p95': None}, None
    nl, ns = [], []
    for i in ix:
        d = days[i]
        k_real = real[i][0]['k']
        for dr, acc in ((1, nl), (-1, ns)):
            g, s = control_trade(d['o'], d['h'], d['l'], d['c'], tick, variant, dr, k_real)
            acc.append(g - cost / s)
    nl, ns = np.array(nl), np.array(ns)
    rng = np.random.default_rng(SEED)
    pm = np.array([np.where(rng.random(len(ix)) < 0.5, nl, ns).mean() for _ in range(N_CTRL)])
    return {'n': N_CTRL, 'mean': _f(pm.mean()), 'p95': _f(np.percentile(pm, 95))}, pm


def run_all(days, mode):
    """days = chronological valid days: dict(date, o, h, l, c) with NB bars from 08:30 ET."""
    tick, costs = TICKS[mode], COST[mode]
    days = [d for d in days if d['date'] >= FIRST_DAY]
    dates = [d['date'] for d in days]
    sets = {'FULL': list(range(len(days))),
            'POST': [i for i, dd in enumerate(dates) if dd >= POST_FROM],
            'PRE': [i for i, dd in enumerate(dates) if dd < POST_FROM]}
    out = {'mode': mode, 'n_days': len(days), 'first': dates[0].isoformat() if dates else None,
           'last': dates[-1].isoformat() if dates else None}
    for v in ('A', 'B'):
        real = []
        for d in days:
            t = real_trade(d['o'], d['h'], d['l'], d['c'], tick, v)
            real.append([t] if t else [])
        res = {w: stats([real[i] for i in ix], costs, [dates[i] for i in ix], per_year=(w == 'FULL'))
               for w, ix in sets.items()}
        cs, pm = control(days, real, tick, v, costs[1])
        m = res['FULL']['S1'].get('mean')
        pct = float(np.mean(pm < m)) if (pm is not None and m is not None) else None
        res['control'] = dict(cs, real_pct=_f(pct, 3))
        res['verdict'] = verdict(res['FULL'], res['POST'], pct)
        out[v] = res
    if mode == 'YM':
        lit = [[t] if t else [] for t in (real_trade(d['o'], d['h'], d['l'], d['c'], tick, 'A', fixed=(9.0, 6.0))
                                          for d in days)]
        s = stats(lit, costs, dates)
        out['YM_literal_9_6'] = {k: s.get(k) for k in ('trades', 'S1', 'win', 'gross', 'both')}
    out['overall'] = out['A']['verdict']
    return out


def log_chunks(algo, tag, obj, size=7000):
    s = json.dumps(obj, separators=(',', ':'))
    parts = [s[i:i + size] for i in range(0, len(s), size)] or ['']
    for i, p in enumerate(parts):
        algo.log(f'{tag} {i + 1}/{len(parts)} {p}')


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaHougaard(QCAlgorithm):
    def initialize(self):
        fut = {'NQ': Futures.Indices.NASDAQ_100_E_MINI, 'ES': Futures.Indices.SP_500_E_MINI,
               'YM': Futures.Indices.DOW_30_E_MINI}[MODE]
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
        res['skipped'] = self.skipped
        log_chunks(self, 'NEXA_HOUGAARD', res)
