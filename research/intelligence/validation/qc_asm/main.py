# NEXA ASM T1 / T2a on CME index futures. Pre-registrations: PREREG_T1_STATE.md (3a162810), PREREG_T2A_VAR.md (b65cfc41).
# T1 = is the auction state (prior-day value area at 11:00 ET) predictive of rest-of-day continuation vs reversion?
# T2a = value-area re-entry (Data Trader S2 / Dalton 80 % rule), 15-min bars, 2R. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
from datetime import date, timedelta
import numpy as np

MODE = 'NQ'                 # 'ES' primary / 'NQ' transfer; the only line that differs between runs
TICK = 0.25
COST = {'ES': (0.30, 0.60, 1.20), 'NQ': (1.0, 2.0, 3.0)}     # S0, S1, S2 points per round trip
SEED, B_BOOT, BLOCK = 20261018, 2000, 20
FIRST_DAY = date(2010, 1, 4)
K11, K_IB, K_LAST = 89, 60, 389            # bar index (minute - 570) of the 10:59 bar, IB = bars 0..59, 15:59 bar
IB_LOOK, VA_SHARE = 20, 0.70
VARIANTS = {'P': (15, '2R', 900), 'V5M': (5, '2R', 900), 'VVA': (15, 'VA', 900), 'VEVE': (15, '2R', 720)}
# variant -> (bar minutes, target, latest signal-bar end in minutes after midnight ET)


# ---------------------------------------------------------------- statistics (as in qc_cft)
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
    """wrong(reps) -> boolean array of replicates on the wrong side of 0 for the hypothesis."""
    r = reps[np.isfinite(reps)]
    if len(r) == 0 or theta is None or not np.isfinite(theta):
        return {'theta': _f(theta), 'ci95': [None, None], 'p_one_sided': None, 'B_finite': int(len(r))}
    return {'theta': _f(theta), 'ci95': [_f(np.percentile(r, 2.5)), _f(np.percentile(r, 97.5))],
            'p_one_sided': _f((1 + np.sum(wrong(r))) / (len(r) + 1)), 'B_finite': int(len(r))}


def _mean(v):
    return float(np.mean(v)) if len(v) else float('nan')


# ---------------------------------------------------------------- engine (pure functions, unit-tested locally)
def volume_at_price(bars, tick=TICK):
    """bars = [(high, low, volume)]; each bar's volume spread uniformly over every tick low..high inclusive.
    Returns (base_tick_index, volume array)."""
    his = [int(round(h / tick)) for h, _, _ in bars]
    los = [int(round(l / tick)) for _, l, _ in bars]
    base, top = min(los), max(his)
    d = np.zeros(top - base + 2)
    for hi, lo, (_, _, v) in zip(his, los, bars):
        n = hi - lo + 1
        d[lo - base] += v / n
        d[hi - base + 1] -= v / n
    return base, np.cumsum(d)[:-1]


def value_area(bars, tick=TICK, share=VA_SHARE):
    """Dalton (Mind over Markets, App. 1) value area on the uniformly spread profile. Returns (poc, val, vah) prices."""
    base, vol = volume_at_price(bars, tick)
    n = len(vol)
    mx = vol.max()
    cand = np.flatnonzero(vol >= mx - 1e-9 * max(mx, 1.0))
    mid = (n - 1) / 2.0
    poc = int(min(cand, key=lambda i: (abs(i - mid), i)))
    lo = hi = poc
    total, inc = vol.sum(), vol[poc]
    while inc < share * total:
        up = vol[hi + 1:hi + 3].sum() if hi + 1 < n else None
        dn = vol[max(lo - 2, 0):lo].sum() if lo > 0 else None
        if up is None and dn is None:
            break
        if dn is None or (up is not None and up >= dn):
            hi = min(hi + 2, n - 1)
        else:
            lo = max(lo - 2, 0)
        inc = vol[lo:hi + 1].sum()
    return (base + poc) * tick, (base + lo) * tick, (base + hi) * tick


def loc(x, val, vah):
    return 'above' if x > vah else ('below' if x < val else 'inside')


def t1_day(day, val, vah):
    """T1 features and outcome for one valid day (PREREG_T1 s.3-5)."""
    o, c = day['o'][0], day['c'][K_LAST]
    p11 = day['c'][K11]
    l11, lo_ = loc(p11, val, vah), loc(o, val, vah)
    dm = int(np.sign(p11 - o))
    rr = math.log(c / p11) * 1e4
    if l11 == 'inside':
        st, d, y = 'R', 0, (dm * rr if dm != 0 else None)
        sub = 'R-failed' if lo_ != 'inside' else 'R-inside'
    else:
        d = 1 if l11 == 'above' else -1
        st, y = ('I+' if d > 0 else 'I-'), d * rr
        sub = 'I-migration' if lo_ == l11 else 'I-breakout'
    return {'state': st, 'sub': sub, 'D': d, 'Dm': dm, 'Rr': rr, 'Y': y,
            'Yb': (dm * rr if dm != 0 else None), 'ibw': (max(day['h'][:K_IB]) - min(day['l'][:K_IB])) / o}


def agg_bars(day, m):
    """m-minute bars aligned to 09:30 from the 390 minute bars: list of (k_start, k_end, high, low, close)."""
    out = []
    for s in range(0, 390, m):
        e = s + m - 1
        out.append((s, e, max(day['h'][s:e + 1]), min(day['l'][s:e + 1]), day['c'][e]))
    return out


def t2a_day(day, val, vah, m=15, target='2R', last_end=900, cost=0.0, tick=TICK):
    """T2a trades for one day whose prior session closed inside its VA (PREREG_T2A s.3-4).
    Returns (trades, skipped_small_r, skipped_va_target)."""
    trades, sk_r, sk_va = [], 0, 0
    bars = agg_bars(day, m)
    exc, ext, free_after = None, None, -1          # excursion side (+1 up / -1 down), its extreme, earliest new start
    j = 0
    while j < len(bars):
        s, e, bh, bl, bc = bars[j]
        if exc is None:
            if s > free_after and (bc < val or bc > vah):
                exc = -1 if bc < val else 1
                ext = bl if exc < 0 else bh
            j += 1
            continue
        ext = min(ext, bl) if exc < 0 else max(ext, bh)
        if val < bc < vah:                                     # re-entry close -> signal
            if 570 + e + 1 > last_end:
                break
            k = e + 1
            if k > K_LAST:
                break
            dr = -exc                                          # back toward value
            entry = day['o'][k]
            stop = ext - tick if dr > 0 else ext + tick
            r = (entry - stop) * dr
            if r < 2 * tick - 1e-9:
                sk_r += 1
                exc, free_after = None, e
                j += 1
                continue
            tgt = entry + dr * 2 * r if target == '2R' else (vah if dr > 0 else val)
            if target == 'VA' and (tgt - entry) * dr <= 0:
                sk_va += 1
                exc, free_after = None, e
                j += 1
                continue
            ex, kind, kx = day['c'][K_LAST], 'time', K_LAST
            for kk in range(k, K_LAST + 1):
                hit_stop = day['l'][kk] <= stop if dr > 0 else day['h'][kk] >= stop
                hit_tgt = day['h'][kk] >= tgt if dr > 0 else day['l'][kk] <= tgt
                if hit_stop:
                    ex, kind, kx = stop, 'stop', kk
                    break
                if hit_tgt:
                    ex, kind, kx = tgt, 'target', kk
                    break
            gross = dr * (ex - entry)
            trades.append({'dir': dr, 'k': k, 'entry': entry, 'stop': stop, 'tgt': tgt, 'R_pts': r,
                           'exit': ex, 'kind': kind, 'k_exit': kx, 'gross': gross})
            exc, free_after = None, kx
            while j < len(bars) and bars[j][0] <= kx:
                j += 1
            continue
        if (exc < 0 and bc > vah) or (exc > 0 and bc < val):  # jumped across value: new excursion on the other side
            exc = 1 if bc > vah else -1
            ext = bh if exc > 0 else bl
        j += 1
    return trades, sk_r, sk_va


def net_r(t, cost):
    return (t['gross'] - cost) / t['R_pts']


# ---------------------------------------------------------------- statistics per test
def t1_stats(rows):
    """rows = chronological list of t1_day dicts for valid days."""
    n = len(rows)
    y = np.array([r['Y'] if r['Y'] is not None else np.nan for r in rows], float)
    gi = np.array([r['state'] != 'R' for r in rows])
    gr = ~gi
    rng = np.random.default_rng(SEED)
    mi, mr = np.empty(B_BOOT), np.empty(B_BOOT)
    for b in range(B_BOOT):
        idx = block_indices(n, rng)
        yi, yr = y[idx][gi[idx]], y[idx][gr[idx]]
        mi[b], mr[b] = np.nanmean(yi) if np.isfinite(yi).any() else np.nan, np.nanmean(yr) if np.isfinite(yr).any() else np.nan
    th_i, th_r = np.nanmean(y[gi]), np.nanmean(y[gr])
    out = {'n_days': n, 'n_I': int(gi.sum()), 'n_R': int(gr.sum()),
           'H1_I_cont': summary(th_i, mi, lambda r: r <= 0),
           'H2_R_cont': summary(th_r, mr, lambda r: r >= 0),
           'H3_delta': summary(th_i - th_r, mi - mr, lambda r: r <= 0)}
    yb = np.array([r['Yb'] for r in rows if r['Yb'] is not None], float)
    out['Y_base_mean'] = _f(yb.mean() if len(yb) else None)
    out['hit_I'] = _f(np.mean(y[gi][np.isfinite(y[gi])] > 0))
    out['hit_R'] = _f(np.mean(y[gr][np.isfinite(y[gr])] > 0))
    out['mean_abs_Rr'] = _f(np.mean([abs(r['Rr']) for r in rows]))
    q = np.array_split(np.arange(n), 4)
    out['blocks'] = [[_f(np.nanmean(y[ix][gi[ix]])), _f(np.nanmean(y[ix][gr[ix]])),
                      _f(np.nanmean(y[ix][gi[ix]]) - np.nanmean(y[ix][gr[ix]]))] for ix in q]
    out['blocks_delta_pos'] = int(sum(1 for bl in out['blocks'] if (bl[2] or 0) > 0))
    out['sub'] = {}
    for s in ('I-migration', 'I-breakout', 'R-failed', 'R-inside'):
        v = [r['Y'] for r in rows if r['sub'] == s and r['Y'] is not None]
        out['sub'][s] = [len(v), _f(_mean(v))]
    ib = [r['ibpct'] for r in rows]
    out['by_ib_tercile'] = {}
    for name, lo_, hi_ in (('low', -1, 1 / 3), ('mid', 1 / 3, 2 / 3), ('high', 2 / 3, 2)):
        vi = [r['Y'] for r, p in zip(rows, ib) if lo_ < p <= hi_ and r['state'] != 'R']
        vr = [r['Y'] for r, p in zip(rows, ib) if lo_ < p <= hi_ and r['state'] == 'R' and r['Y'] is not None]
        out['by_ib_tercile'][name] = [len(vi), _f(_mean(vi)), len(vr), _f(_mean(vr))]
    return out


def t1_verdict(s):
    if s['n_I'] < 300 or s['n_R'] < 300:
        return 'INSUFFICIENT-N'
    h1, h2, h3 = s['H1_I_cont'], s['H2_R_cont'], s['H3_delta']
    p3 = (h3['p_one_sided'] if h3['p_one_sided'] is not None else 1) <= 0.05
    ok1 = (h1['ci95'][0] if h1['ci95'][0] is not None else -1) > 0
    ok2 = (h2['ci95'][1] if h2['ci95'][1] is not None else 1) < 0
    if p3 and ok1 and ok2 and s['blocks_delta_pos'] >= 3:
        return 'STATE PREDICTABLE'
    if p3 and (ok1 or ok2):
        return 'PARTIAL'
    return 'NOT PREDICTABLE'


def t2a_stats(day_trades, costs, years):
    """day_trades = chronological list (one entry per valid day) of trade lists; costs = (S0, S1, S2)."""
    n = len(day_trades)
    s1 = costs[1]
    dsum = np.array([sum(net_r(t, s1) for t in tl) for tl in day_trades], float)
    dcnt = np.array([len(tl) for tl in day_trades], float)
    allt = [t for tl in day_trades for t in tl]
    nt = len(allt)
    out = {'trades': nt, 'trades_per_day': _f(nt / n if n else None)}
    if nt == 0:
        out['S1'] = {'theta': None}
        return out
    rng = np.random.default_rng(SEED)
    reps = np.empty(B_BOOT)
    for b in range(B_BOOT):
        idx = block_indices(n, rng)
        c = dcnt[idx].sum()
        reps[b] = dsum[idx].sum() / c if c > 0 else np.nan
    out['S1'] = summary(dsum.sum() / nt, reps, lambda r: r <= 0)
    out['S0_mean'] = _f(np.mean([net_r(t, costs[0]) for t in allt]))
    out['S2_mean'] = _f(np.mean([net_r(t, costs[2]) for t in allt]))
    out['hit_target'] = _f(np.mean([t['kind'] == 'target' for t in allt]))
    out['share_time_exit'] = _f(np.mean([t['kind'] == 'time' for t in allt]))
    w = [net_r(t, s1) for t in allt if net_r(t, s1) > 0]
    lz = [-net_r(t, s1) for t in allt if net_r(t, s1) <= 0]
    out['payoff'] = _f(np.mean(w) / np.mean(lz) if w and lz else None)
    out['long'] = [sum(1 for t in allt if t['dir'] > 0), _f(_mean([net_r(t, s1) for t in allt if t['dir'] > 0]))]
    out['short'] = [sum(1 for t in allt if t['dir'] < 0), _f(_mean([net_r(t, s1) for t in allt if t['dir'] < 0]))]
    out['mean_R_pts'] = _f(np.mean([t['R_pts'] for t in allt]))
    q = np.array_split(np.arange(n), 4)
    out['blocks'] = [_f(dsum[ix].sum() / dcnt[ix].sum()) if dcnt[ix].sum() > 0 else None for ix in q]
    out['blocks_pos'] = int(sum(1 for v in out['blocks'] if (v or 0) > 0))
    py = {}
    for y, tl in zip(years, day_trades):
        for t in tl:
            py.setdefault(y, []).append(net_r(t, s1))
    out['per_year'] = {str(y): [len(v), _f(np.mean(v))] for y, v in sorted(py.items())}
    td = dsum[dcnt > 0]
    out['green_day_share'] = _f(np.mean(td > 0) if len(td) else None)
    eq = np.cumsum(dsum)
    out['max_dd_R'] = _f(np.max(np.maximum.accumulate(np.concatenate([[0.0], eq])) - np.concatenate([[0.0], eq])))
    sd = dsum.std(ddof=1)
    out['daily'] = {'n': n, 'mean': _f(dsum.mean()), 'sd': _f(sd), 'sharpe_ann': _f(dsum.mean() / sd * math.sqrt(252) if sd > 0 else None),
                    'skew': _f(((dsum - dsum.mean()) ** 3).mean() / sd ** 3 if sd > 0 else None),
                    'kurt': _f(((dsum - dsum.mean()) ** 4).mean() / sd ** 4 if sd > 0 else None)}
    return out


def t2a_verdict(s):
    if s['trades'] < 300:
        return 'INSUFFICIENT-N'
    th = s['S1']['theta']
    if th is None or th <= 0:
        return 'REJECTED'
    if (s['S1']['ci95'][0] or -1) > 0 and s['blocks_pos'] >= 3:
        return 'VALIDATED (G4)'
    return 'INCONCLUSIVE'


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaAsm(QCAlgorithm):
    def initialize(self):
        self.sym_name = MODE
        tick = Futures.Indices.NASDAQ_100_E_MINI if MODE == 'NQ' else Futures.Indices.SP_500_E_MINI
        self.set_start_date(2009, 12, 1)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        f = self.add_future(tick, Resolution.MINUTE, fill_forward=False, extended_market_hours=False,
                            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
                            data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
        self.sym = f.symbol
        self.day, self.roll, self.roll_pending = None, False, False
        self.bars, self.prev, self.ibw_hist = {}, None, []
        self.t1_rows, self.t2_days, self.years = [], {v: [] for v in VARIANTS}, []
        self.skipped = {'incomplete': 0, 'no_prev': 0, 'roll': 0, 'warmup': 0, 'setup_no': 0,
                        'small_r': {v: 0 for v in VARIANTS}, 'va_tgt': {v: 0 for v in VARIANTS}}

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
        m = t.hour * 60 + t.minute
        if tb is None or not 570 <= m <= 959:
            return
        self.bars[m] = [float(tb.open), float(tb.high), float(tb.low), float(tb.close), float(tb.volume)]

    def close_day(self):
        bars, self.bars = self.bars, {}
        complete = len(bars) == 390 and all((570 + k) in bars for k in range(390)) and self.day.weekday() < 5
        if not complete:
            if bars:
                self.skipped['incomplete'] += 1
            self.prev = None
            return
        cols = list(zip(*[bars[570 + k] for k in range(390)]))
        day = {'o': list(cols[0]), 'h': list(cols[1]), 'l': list(cols[2]), 'c': list(cols[3]), 'v': list(cols[4])}
        prev, self.prev = self.prev, day
        ibw = (max(day['h'][:K_IB]) - min(day['l'][:K_IB])) / day['o'][0]
        hist = list(self.ibw_hist)
        self.ibw_hist = (self.ibw_hist + [ibw])[-IB_LOOK:]
        if prev is None:
            self.skipped['no_prev'] += 1
            return
        if self.roll:
            self.skipped['roll'] += 1
            return
        if len(hist) < IB_LOOK or self.day < FIRST_DAY:
            self.skipped['warmup'] += 1
            return
        poc, val, vah = value_area(list(zip(prev['h'], prev['l'], prev['v'])))
        row = t1_day(day, val, vah)
        row['ibpct'] = sum(1 for x in hist if x < ibw) / len(hist)
        self.t1_rows.append(row)
        self.years.append(self.day.year)
        setup = val <= prev['c'][K_LAST] <= vah
        if not setup:
            self.skipped['setup_no'] += 1
        for v, (mm, tgt, last_end) in VARIANTS.items():
            if setup:
                tr, sr, sv = t2a_day(day, val, vah, mm, tgt, last_end)
                self.skipped['small_r'][v] += sr
                self.skipped['va_tgt'][v] += sv
            else:
                tr = []
            self.t2_days[v].append(tr)

    def on_end_of_algorithm(self):
        self.close_day()
        head = {'mode': MODE, 'n_days': len(self.t1_rows), 'skipped': self.skipped,
                'first_day': FIRST_DAY.isoformat(), 'last_day': self.day.isoformat() if self.day else None}
        s1 = t1_stats(self.t1_rows)
        self.log('NEXA_T1_RESULT ' + json.dumps(head | {'T1': s1, 'verdict': t1_verdict(s1)}, separators=(',', ':')))
        out = {'mode': MODE}
        for v in VARIANTS:
            st = t2a_stats(self.t2_days[v], COST[MODE], self.years)
            out[v] = st | {'verdict': t2a_verdict(st)}
        self.log('NEXA_T2A_RESULT ' + json.dumps(out, separators=(',', ':')))
