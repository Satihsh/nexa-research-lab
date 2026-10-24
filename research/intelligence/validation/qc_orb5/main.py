# NEXA H-ORB5 on CME index futures. Pre-registration: PREREG_ORB5.md.
# Zarattini & Aziz (2023) 5-minute ORB: direction of the 09:30-09:34 candle, entry 09:35, stop at the other side of
# the candle, target 10R or the 15:59 close. Primary set = days outside the paper's 2016-01 .. 2023-02-17 window.
# 500 random-direction placebos. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
from datetime import date, timedelta
import numpy as np

MODE = 'NQ'                 # 'NQ' primary / 'ES' transfer
TICK = 0.25
COST = {'ES': (0.30, 0.60, 1.20), 'NQ': (1.0, 2.0, 3.0)}     # S0, S1, S2 points per round trip
SEED, B_BOOT, BLOCK = 20261021, 2000, 20
FIRST_DAY = date(2010, 1, 4)
IN_FROM, IN_TO = date(2016, 1, 4), date(2023, 2, 17)
POST_FROM = date(2023, 3, 1)
K_LAST, K_ENTRY, TGT_R, MIN_R = 389, 5, 10.0, 1.0
N_PLAC = 500


# ---------------------------------------------------------------- statistics (as qc_fpt)
def block_indices(n, rng, L=BLOCK):
    if n <= L:
        return rng.integers(0, n, n)
    nb = int(math.ceil(n / L))
    st = rng.integers(0, n - L + 1, nb)
    return (st[:, None] + np.arange(L)[None, :]).ravel()[:n]


def _f(x):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, 6) if np.isfinite(x) else None


def summary(theta, reps, wrong):
    r = reps[np.isfinite(reps)]
    if len(r) == 0 or theta is None or not np.isfinite(theta):
        return {'theta': _f(theta), 'ci95': [None, None], 'p_one_sided': None, 'B_finite': int(len(r))}
    return {'theta': _f(theta), 'ci95': [_f(np.percentile(r, 2.5)), _f(np.percentile(r, 97.5))],
            'p_one_sided': _f((1 + np.sum(wrong(r))) / (len(r) + 1)), 'B_finite': int(len(r))}


def _mean(v):
    return float(np.mean(v)) if len(v) else float('nan')


# ---------------------------------------------------------------- engine (pure functions, unit-tested locally)
def scan_exit(h, l, c, k0, d, stop, tgt):
    """First touch from bar k0; stop first on ties; else 15:59 close. Returns (exit, kind, k_exit)."""
    for k in range(k0, K_LAST + 1):
        if (l[k] <= stop) if d > 0 else (h[k] >= stop):
            return stop, 'stop', k
        if (h[k] >= tgt) if d > 0 else (l[k] <= tgt):
            return tgt, 'target', k
    return c[K_LAST], 'time', K_LAST


def candle(o, h, l, c):
    return o[0], float(np.max(h[:K_ENTRY])), float(np.min(l[:K_ENTRY])), c[K_ENTRY - 1]


def orb_trade(o, h, l, c, d):
    """The paper's trade in direction d (+1/-1) for one day, or None if the R floor fails."""
    _, H, L, _ = candle(o, h, l, c)
    entry = o[K_ENTRY]
    stop = L if d > 0 else H
    r = d * (entry - stop)
    if r <= 0 or r < MIN_R:
        return None
    ex, kind, kx = scan_exit(h, l, c, K_ENTRY, d, stop, entry + d * TGT_R * r)
    return {'dir': d, 'entry': entry, 'R_pts': r, 'exit': ex, 'kind': kind, 'k_exit': kx, 'gross': d * (ex - entry)}


def real_dir(o, h, l, c):
    O, _, _, C = candle(o, h, l, c)
    return 1 if C > O else (-1 if C < O else 0)


def in_primary(dd):
    return dd >= FIRST_DAY and (dd < IN_FROM or dd >= POST_FROM)


def net_r(t, cost):
    return (t['gross'] - cost) / t['R_pts']


def stats(day_trades, costs, dates):
    n = len(day_trades)
    s1 = costs[1]
    dsum = np.array([sum(net_r(t, s1) for t in tl) for tl in day_trades], float)
    dcnt = np.array([len(tl) for tl in day_trades], float)
    allt = [t for tl in day_trades for t in tl]
    nt = len(allt)
    out = {'days': n, 'trades': nt}
    if nt == 0:
        out['S1'] = {'theta': None}
        return out
    rng = np.random.default_rng(SEED)
    reps = np.empty(B_BOOT)
    for b in range(B_BOOT):
        idx = block_indices(n, rng)
        cc = dcnt[idx].sum()
        reps[b] = dsum[idx].sum() / cc if cc > 0 else np.nan
    out['S1'] = summary(dsum.sum() / nt, reps, lambda r: r <= 0)
    rs = [net_r(t, s1) for t in allt]
    out['S0_mean'] = _f(np.mean([net_r(t, costs[0]) for t in allt]))
    out['S2_mean'] = _f(np.mean([net_r(t, costs[2]) for t in allt]))
    out['hit_rate'] = _f(np.mean([r > 0 for r in rs]))
    out['share_10R'] = _f(np.mean([t['kind'] == 'target' for t in allt]))
    out['share_time_exit'] = _f(np.mean([t['kind'] == 'time' for t in allt]))
    out['long'] = [sum(1 for t in allt if t['dir'] > 0), _f(_mean([net_r(t, s1) for t in allt if t['dir'] > 0]))]
    out['short'] = [sum(1 for t in allt if t['dir'] < 0), _f(_mean([net_r(t, s1) for t in allt if t['dir'] < 0]))]
    out['mean_R_pts'] = _f(np.mean([t['R_pts'] for t in allt]))
    q = np.array_split(np.arange(n), 4)
    out['blocks'] = [_f(dsum[ix].sum() / dcnt[ix].sum()) if dcnt[ix].sum() > 0 else None for ix in q]
    out['blocks_pos'] = int(sum(1 for v in out['blocks'] if (v or 0) > 0))
    py = {}
    for dd, tl in zip(dates, day_trades):
        for t in tl:
            py.setdefault(dd.year, []).append(net_r(t, s1))
    out['per_year'] = {str(y): [len(v), _f(np.mean(v))] for y, v in sorted(py.items())}
    td = dsum[dcnt > 0]
    out['green_day_share'] = _f(np.mean(td > 0) if len(td) else None)
    eq = np.cumsum(dsum)
    peak = np.maximum.accumulate(np.concatenate([[0.0], eq]))
    out['max_dd_R'] = _f(np.max(peak - np.concatenate([[0.0], eq])))
    run = best = 0
    for r in rs:
        run = run + 1 if r < 0 else 0
        best = max(best, run)
    out['longest_losing_streak'] = best
    out['vs_prop_threshold_0p025'] = bool(dsum.sum() / nt >= 0.025)
    return out


def verdict(s, plac_pct):
    if s['trades'] < 300:
        return 'INSUFFICIENT-N'
    th = s['S1']['theta']
    if th is None or th <= 0:
        return 'REJECTED'
    if (s['S1']['ci95'][0] or -1) > 0 and s['blocks_pos'] >= 3 and plac_pct is not None and plac_pct >= 0.95:
        return 'VALIDATED (G4)'
    return 'INCONCLUSIVE'


def run_all(days, mode):
    """days = chronological valid days: dict(date, o, h, l, c)."""
    costs = COST[mode]
    days = [d for d in days if d['date'] >= FIRST_DAY]
    both, real, skipped = [], [], {'doji': 0, 'r_floor': 0}
    for d in days:
        lt = orb_trade(d['o'], d['h'], d['l'], d['c'], 1)
        st = orb_trade(d['o'], d['h'], d['l'], d['c'], -1)
        both.append((lt, st))
        rd = real_dir(d['o'], d['h'], d['l'], d['c'])
        if rd == 0:
            skipped['doji'] += 1
            real.append([])
            continue
        t = lt if rd > 0 else st
        if t is None:
            skipped['r_floor'] += 1
        real.append([t] if t else [])
    dates = [d['date'] for d in days]
    sets = {'P': [i for i, dd in enumerate(dates) if in_primary(dd)],
            'IN': [i for i, dd in enumerate(dates) if IN_FROM <= dd <= IN_TO],
            'PRE': [i for i, dd in enumerate(dates) if dd < IN_FROM],
            'POST': [i for i, dd in enumerate(dates) if dd >= POST_FROM]}
    out = {'mode': mode, 'n_days': len(days), 'skipped': skipped}
    for name, ix in sets.items():
        out[name] = stats([real[i] for i in ix], costs, [dates[i] for i in ix])
    # random-direction placebo over set P (every primary day gets a random direction)
    rng = np.random.default_rng(SEED)
    P = sets['P']
    nl = np.array([net_r(both[i][0], costs[1]) if both[i][0] else np.nan for i in P])
    ns = np.array([net_r(both[i][1], costs[1]) if both[i][1] else np.nan for i in P])
    pm = []
    for _ in range(N_PLAC):
        pick = np.where(rng.random(len(P)) < 0.5, nl, ns)
        ok = np.isfinite(pick)
        pm.append(float(pick[ok].mean()) if ok.any() else float('nan'))
    th = out['P']['S1']['theta']
    pv = np.array([x for x in pm if np.isfinite(x)])
    pct = float(np.mean(pv < th)) if (th is not None and len(pv)) else None
    out['placebo'] = {'n': N_PLAC, 'mean': _f(pv.mean() if len(pv) else None), 'p95': _f(np.percentile(pv, 95) if len(pv) else None),
                      'p50': _f(np.percentile(pv, 50) if len(pv) else None), 'real_percentile': _f(pct)}
    out['verdict'] = verdict(out['P'], pct)
    return out


def log_chunks(algo, tag, obj, size=7000):
    s = json.dumps(obj, separators=(',', ':'))
    parts = [s[i:i + size] for i in range(0, len(s), size)] or ['']
    for i, p in enumerate(parts):
        algo.log(f'{tag} {i + 1}/{len(parts)} {p}')


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaOrb5(QCAlgorithm):
    def initialize(self):
        fut = Futures.Indices.NASDAQ_100_E_MINI if MODE == 'NQ' else Futures.Indices.SP_500_E_MINI
        self.set_start_date(2009, 12, 1)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        f = self.add_future(fut, Resolution.MINUTE, fill_forward=False, extended_market_hours=False,
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
        if 570 <= m <= 959:
            self.bars[m] = (float(tb.open), float(tb.high), float(tb.low), float(tb.close))

    def close_day(self):
        bars, self.bars = self.bars, {}
        if not bars:
            return
        complete = len(bars) == 390 and all((570 + k) in bars for k in range(390)) and self.day.weekday() < 5
        if not complete:
            self.skipped['incomplete'] += 1
            return
        if self.roll:
            self.skipped['roll'] += 1
            return
        cols = list(zip(*[bars[570 + k] for k in range(390)]))
        o, h, l, c = (np.array(x, dtype=np.float64) for x in cols)
        self.days.append({'date': self.day, 'o': o, 'h': h, 'l': l, 'c': c})

    def on_end_of_algorithm(self):
        self.close_day()
        res = run_all(self.days, MODE)
        res['skipped_days'] = self.skipped
        res['last_day'] = self.days[-1]['date'].isoformat() if self.days else None
        log_chunks(self, 'NEXA_ORB5_RESULT', res)
