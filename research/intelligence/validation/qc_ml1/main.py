# NEXA H-ML1: walk-forward gradient-boosting intraday direction model, NQ primary / ES secondary.
# Pre-registration: PREREG_ML1.md; clarifications DEVIATIONS_ML1.md. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
from datetime import date, timedelta
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

SEED, B_BOOT, BLOCK = 20261018, 2000, 20
NBARS, LAST, HOLD = 390, 389, 60
DEC_K = list(range(29, 330, 15))                      # 10:00 ... 15:00 ET decision bars (21)
LOOK, REGIME_N, REGIME_MIN = 20, 250, 60
MAX_TRADES = 2
DELTA_Q = 0.90
COST = {'NQ': (1.0, 2.0, 3.0), 'ES': (0.30, 0.60, 1.20)}   # S0, S1, S2 points round trip
VAL_YEARS = list(range(2013, 2023))
FIRST_DAY = date(2010, 1, 4)
HOLD_FROM = date(2023, 1, 1)
N_PLACEBO = 20
PROP_TARGET = 0.10
HGB_PARAMS = dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=200,
                  l2_regularization=1.0, early_stopping=False, random_state=SEED)
FEATURES = ['tod', 'dow', 'r5', 'r15', 'r30', 'r60', 'r_open', 'gap', 'prev_ret', 'pos_prev', 'pos_today',
            'vwap_dist', 'or_hi', 'or_lo', 'vol_ratio', 'rv_ratio', 'range_ratio', 'sd_regime', 'x_ropen', 'x_r30']
LOG_CHUNK = 7000


# ---------------------------------------------------------------- statistics
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


def boot_mean(x, seed=SEED):
    x = np.asarray(x, float)
    n = len(x)
    if n == 0:
        return {'n': 0, 'mean': None, 'ci95': [None, None], 'p_one_sided': None}
    rng = np.random.default_rng(seed)
    reps = np.array([x[block_indices(n, rng)].mean() for _ in range(B_BOOT)])
    return {'n': n, 'mean': _f(x.mean()), 'ci95': [_f(np.percentile(reps, 2.5)), _f(np.percentile(reps, 97.5))],
            'p_one_sided': _f((1 + np.sum(reps <= 0)) / (B_BOOT + 1))}


def blocks4(x):
    x = np.asarray(x, float)
    if len(x) < 4:
        return [], 0
    q = np.array_split(np.arange(len(x)), 4)
    m = [_f(x[ix].mean()) for ix in q]
    return m, int(sum(1 for ix in q if x[ix].mean() > 0))


def longest_losing(x):
    run = best = 0
    for v in x:
        run = run + 1 if v < 0 else 0
        best = max(best, run)
    return best


# ---------------------------------------------------------------- per-day engine (pure functions)
def bracket(h, l, c, k, stop_pts, direction):
    """Gross outcome in R of a ±1R bracket from close k; stop assumed first if a bar hits both. Returns (R, exit_bar)."""
    entry = c[k]
    up, dn = entry + stop_pts, entry - stop_pts
    end = min(k + HOLD, LAST)
    for j in range(k + 1, end + 1):
        hit_up, hit_dn = h[j] >= up, l[j] <= dn
        if direction > 0:
            if hit_dn:
                return -1.0, j
            if hit_up:
                return 1.0, j
        else:
            if hit_up:
                return -1.0, j
            if hit_dn:
                return 1.0, j
    return direction * (c[end] - entry) / stop_pts, end


def day_stats(d):
    """Per-day summary values used as 'history' for later days."""
    o, h, l, c, v = d['o'], d['h'], d['l'], d['c'], d['v']
    r60 = [math.log(c[min(k + HOLD, LAST)] / c[k]) for k in DEC_K]
    lr = np.diff(np.log(c))
    return {'r60': r60, 'close': float(c[LAST]), 'high': float(h.max()), 'low': float(l.min()),
            'range': float(h.max() - l.min()), 'cumvol': np.cumsum(v), 'rv': float(lr.std()), 'open': float(o[0])}


def history(stats, i):
    """Rolling values for day i from previous kept days only (None if fewer than LOOK previous days)."""
    if i < LOOK:
        return None
    prev = stats[i - LOOK:i]
    r60 = np.array([x for s in prev for x in s['r60']])
    closes = np.array([s['close'] for s in stats[max(0, i - LOOK - 1):i]])
    dret = np.diff(np.log(closes))[-LOOK:]
    return {'sig60': float(r60.std()), 'sigd': float(dret.std()) if len(dret) else float('nan'),
            'cumvol': np.mean([s['cumvol'] for s in prev], axis=0), 'rv': float(np.mean([s['rv'] for s in prev])),
            'range': float(np.mean([s['range'] for s in prev])), 'prev': stats[i - 1]}


def regime(sigd_hist, sigd_now):
    past = [x for x in sigd_hist[-REGIME_N:] if np.isfinite(x)]
    if len(past) < REGIME_MIN:
        return float('nan')
    return sigd_now / float(np.mean(past))


def _ret(c, o0, k, n):
    base = c[k - n] if k - n >= 0 else o0
    return math.log(c[k] / base)


def features(d, x, hist, xhist, regime_val, wd):
    """Feature rows (one per decision bar) for target day d, other instrument day x."""
    o, h, l, c, v = d['o'], d['h'], d['l'], d['c'], d['v']
    s60, sd = hist['sig60'], hist['sigd']
    xs60 = xhist['sig60']
    pv = hist['prev']
    or_hi, or_lo = float(h[:30].max()), float(l[:30].min())
    tp = (h + l + c) / 3.0
    cpv, cv = np.cumsum(tp * v), np.cumsum(v)
    lr = np.diff(np.log(c))
    rows = []
    for k in DEC_K:
        p = c[k]
        hi_k, lo_k = float(h[:k + 1].max()), float(l[:k + 1].min())
        rng_k = hi_k - lo_k
        vw = cpv[k] / cv[k] if cv[k] > 0 else p
        pr = pv['high'] - pv['low']
        den_v = hist['cumvol'][k]
        rows.append([
            k + 1, wd,
            _ret(c, o[0], k, 5) / s60, _ret(c, o[0], k, 15) / s60, _ret(c, o[0], k, 30) / s60, _ret(c, o[0], k, 60) / s60,
            math.log(p / o[0]) / s60,
            math.log(o[0] / pv['close']) / sd if sd > 0 else float('nan'),
            hist['prev_ret'] / sd if sd > 0 else float('nan'),
            (p - pv['low']) / pr if pr > 0 else float('nan'),
            (p - lo_k) / rng_k if rng_k > 0 else 0.5,
            math.log(p / vw) / s60 if cv[k] > 0 else 0.0,
            math.log(p / or_hi) / s60, math.log(p / or_lo) / s60,
            cv[k] / den_v if den_v > 0 else float('nan'),
            float(lr[:k].std()) / hist['rv'] if (k >= 2 and hist['rv'] > 0) else float('nan'),
            rng_k / hist['range'] if hist['range'] > 0 else float('nan'),
            regime_val,
            math.log(x['c'][k] / x['o'][0]) / xs60, _ret(x['c'], x['o'][0], k, 30) / xs60,
        ])
    return rows


def _f64(d):
    return {key: np.asarray(val, dtype=np.float64) for key, val in d.items()}


def build_rows(days, target):
    """All decision rows for target ('NQ'/'ES'). days: list of dict(date, NQ:{o,h,l,c,v}, ES:{...})."""
    other = 'ES' if target == 'NQ' else 'NQ'
    st_t = [day_stats(_f64(dd[target])) for dd in days]
    st_x = [day_stats(_f64(dd[other])) for dd in days]
    sigd_hist = []
    rows = []
    for i, dd in enumerate(days):
        ht, hx = history(st_t, i), history(st_x, i)
        if ht is None:
            continue
        ht['prev_ret'] = math.log(st_t[i - 1]['close'] / st_t[i - 2]['close']) if i >= 2 else float('nan')
        reg = regime(sigd_hist, ht['sigd'])
        sigd_hist.append(ht['sigd'])
        d, x = _f64(dd[target]), _f64(dd[other])
        fr = features(d, x, ht, hx, reg, dd['date'].weekday())
        for j, k in enumerate(DEC_K):
            stop = ht['sig60'] * d['c'][k]
            gl, el = bracket(d['h'], d['l'], d['c'], k, stop, +1)
            gs, es = bracket(d['h'], d['l'], d['c'], k, stop, -1)
            rows.append({'date': dd['date'], 'k': k, 'x': fr[j], 'long': gl, 'short': gs,
                         'exit_long': el, 'exit_short': es, 'stop': stop})
    return rows


# ---------------------------------------------------------------- model, threshold, trading
def fit(X, y, seed=SEED):
    params = dict(HGB_PARAMS)
    params['random_state'] = seed
    return HistGradientBoostingClassifier(**params).fit(X, y)


def labelled(rows):
    keep = [r for r in rows if r['long'] != 0]
    X = np.array([r['x'] for r in keep], float)
    y = np.array([1 if r['long'] > 0 else 0 for r in keep], int)
    return keep, X, y


def permute_within_day(rows, y, seed):
    rng = np.random.default_rng(seed)
    y = y.copy()
    idx_by_day = {}
    for i, r in enumerate(rows):
        idx_by_day.setdefault(r['date'], []).append(i)
    for d in sorted(idx_by_day):
        ix = np.array(idx_by_day[d])
        y[ix] = y[ix][rng.permutation(len(ix))]
    return y


def day_shift_labels(rows, seed):
    """Placebo (DEVIATIONS_ML1 D-1): row (day i, k) gets the label of (day (i+m) mod n, k); m from default_rng(seed)."""
    days = sorted({r['date'] for r in rows})
    n = len(days)
    m = int(np.random.default_rng(seed).integers(n // 10, n - n // 10))
    pos = {d: i for i, d in enumerate(days)}
    src = {(r['date'], r['k']): (1 if r['long'] > 0 else 0) for r in rows}
    keep, ys = [], []
    for r in rows:
        key = (days[(pos[r['date']] + m) % n], r['k'])
        if key in src:
            keep.append(r)
            ys.append(src[key])
    return keep, np.array([r['x'] for r in keep], float), np.array(ys, int)


def train_with_delta(rows, placebo_seed=None):
    """Fit calibration model on training years except the last 2, delta = 90th pct of |p-0.5| on those 2, refit on all."""
    if placebo_seed is None:
        keep, X, y = labelled(rows)
    else:
        keep, X, y = day_shift_labels(rows, placebo_seed)
    years = sorted({r['date'].year for r in keep})
    if len(years) < 3:
        raise ValueError('need >= 3 training years')
    yr = np.array([r['date'].year for r in keep])
    cal_fit = yr <= years[-3]
    cal_eval = yr >= years[-2]
    m0 = fit(X[cal_fit], y[cal_fit])
    pc = m0.predict_proba(X[cal_eval])[:, 1]
    delta = float(np.quantile(np.abs(pc - 0.5), DELTA_Q))
    return fit(X, y), delta


def trade_day(day_rows, p, delta, costs):
    """Select up to MAX_TRADES non-overlapping trades in time order. Returns list of trade dicts."""
    out, busy_until = [], -1
    for r, pi in zip(day_rows, p):
        if len(out) >= MAX_TRADES:
            break
        if r['k'] < busy_until or abs(pi - 0.5) < delta:
            continue
        dirn = 1 if pi > 0.5 else -1
        g = r['long'] if dirn > 0 else r['short']
        ex = r['exit_long'] if dirn > 0 else r['exit_short']
        busy_until = ex
        out.append({'date': r['date'], 'k': r['k'], 'dir': dirn, 'gross': g, 'long_gross': r['long'],
                    'net': [g - cpt / r['stop'] for cpt in costs]})
    return out


def simulate(rows, model, delta, costs):
    rows = sorted(rows, key=lambda r: (r['date'], r['k']))
    if not rows:
        return [], 0
    p = model.predict_proba(np.array([r['x'] for r in rows], float))[:, 1]
    trades, n_days, i = [], 0, 0
    while i < len(rows):
        j = i
        while j < len(rows) and rows[j]['date'] == rows[i]['date']:
            j += 1
        trades.extend(trade_day(rows[i:j], p[i:j], delta, costs))
        n_days += 1
        i = j
    return trades, n_days


def trade_stats(trades, n_days):
    if not trades:
        return {'n_trades': 0, 'n_days': n_days}
    s1 = np.array([t['net'][1] for t in trades])
    out = {'n_trades': len(trades), 'n_days': n_days, 'trades_per_day': _f(len(trades) / max(n_days, 1)),
           'S1': boot_mean(s1), 'S0_mean': _f(np.mean([t['net'][0] for t in trades])),
           'S2_mean': _f(np.mean([t['net'][2] for t in trades])), 'gross_mean': _f(np.mean([t['gross'] for t in trades])),
           'win_rate': _f(np.mean(s1 > 0)), 'longest_losing_streak': longest_losing(s1),
           'B1_long_same_times_S1': _f(np.mean([t['long_gross'] - (t['gross'] - t['net'][1]) for t in trades])),
           'share_long': _f(np.mean([t['dir'] > 0 for t in trades]))}
    out['blocks'], out['blocks_pos'] = blocks4(s1)
    days, months, years, tod = {}, {}, {}, {}
    for t, x in zip(trades, s1):
        days[t['date']] = days.get(t['date'], 0.0) + x
        mk = (t['date'].year, t['date'].month)
        months[mk] = months.get(mk, 0.0) + x
        years.setdefault(t['date'].year, []).append(x)
        tod.setdefault(t['k'] + 1, []).append(x)
    out['green_day_share'] = _f(np.mean([v > 0 for v in days.values()]))
    out['green_month_share'] = _f(np.mean([v > 0 for v in months.values()]))
    out['per_year'] = {str(y): [_f(np.mean(v)), len(v)] for y, v in sorted(years.items())}
    out['by_tod'] = {str(k): [_f(np.mean(v)), len(v)] for k, v in sorted(tod.items())}
    return out


def verdict(v_stats, h_stats, p_rank):
    hs, vs = h_stats.get('S1'), v_stats.get('S1')
    if not hs or hs['mean'] is None:
        return 'INSUFFICIENT-N'
    if hs['mean'] <= 0:
        return 'REJECTED'
    ok = (hs['ci95'][0] is not None and hs['ci95'][0] > 0 and vs and vs['mean'] is not None and vs['mean'] > 0
          and vs['ci95'][0] is not None and vs['ci95'][0] > 0 and h_stats.get('blocks_pos', 0) >= 3
          and p_rank is not None and p_rank <= 0.05)
    if not ok:
        return 'INCONCLUSIVE'
    return 'PROP-READY' if hs['mean'] >= PROP_TARGET else 'VALIDATED (G4)'


def run_target(days, target, n_placebo=N_PLACEBO):
    rows = build_rows(days, target)
    costs = COST[target]
    res = {'n_rows': len(rows), 'folds': {}}
    val_trades, val_days = [], 0
    for Y in VAL_YEARS:
        train = [r for r in rows if r['date'].year < Y]
        test = [r for r in rows if r['date'].year == Y]
        if not test or len({r['date'].year for r in train}) < 3:
            continue
        m, delta = train_with_delta(train)
        tr, nd = simulate(test, m, delta, costs)
        val_trades += tr
        val_days += nd
        res['folds'][str(Y)] = {'delta': _f(delta), 'n_train_rows': len(train), 'n_trades': len(tr)}
    train = [r for r in rows if r['date'] < HOLD_FROM]
    test = [r for r in rows if r['date'] >= HOLD_FROM]
    m, delta = train_with_delta(train)
    h_trades, h_days = simulate(test, m, delta, costs)
    res['holdout_delta'] = _f(delta)
    res['V'] = trade_stats(val_trades, val_days)
    res['H'] = trade_stats(h_trades, h_days)
    pl = []
    for s in range(1, n_placebo + 1):
        mp, dp = train_with_delta(train, placebo_seed=s)
        tp, _ = simulate(test, mp, dp, costs)
        pl.append(float(np.mean([t['net'][1] for t in tp])) if tp else float('nan'))
    hm = res['H'].get('S1', {}).get('mean')
    res['placebo_H_means'] = [_f(x) for x in pl]
    res['p_rank'] = _f(np.mean([x >= hm for x in pl if np.isfinite(x)])) if (hm is not None and pl) else None
    res['verdict'] = verdict(res['V'], res['H'], res['p_rank'])
    return res


def run_all(days, n_placebo=N_PLACEBO):
    days = [d for d in days if d['date'] >= FIRST_DAY]
    out = {'n_days': len(days), 'first_day': days[0]['date'].isoformat() if days else None,
           'last_day': days[-1]['date'].isoformat() if days else None}
    for target in ('NQ', 'ES'):
        out[target] = run_target(days, target, n_placebo)
    return out


def log_chunks(text, size=LOG_CHUNK):
    parts = [text[i:i + size] for i in range(0, len(text), size)] or ['']
    return [(i + 1, len(parts), p) for i, p in enumerate(parts)]


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaMl1(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2009, 12, 1)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        self.syms = {}
        for name, fut in (('NQ', Futures.Indices.NASDAQ_100_E_MINI), ('ES', Futures.Indices.SP_500_E_MINI)):
            f = self.add_future(fut, Resolution.MINUTE, fill_forward=False, extended_market_hours=False,
                                data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
                                data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
            self.syms[f.symbol] = name
        self.day, self.roll_today, self.roll_pending = None, False, False
        self.bars = {'NQ': {}, 'ES': {}}
        self.days = []
        self.skipped = {'incomplete': 0, 'roll': 0}

    def on_data(self, data):
        for sym, _ in data.symbol_changed_events.items():
            if sym in self.syms:
                self.roll_pending = True
        t = self.time - timedelta(minutes=1)
        d = t.date()
        if d != self.day:
            if self.day is not None:
                self.close_day()
            self.roll_today, self.roll_pending = self.roll_pending, False
        self.day = d
        m = t.hour * 60 + t.minute
        if not (570 <= m <= 959):
            return
        for sym, name in self.syms.items():
            tb = data.bars.get(sym)
            if tb is not None:
                self.bars[name][m - 570] = (float(tb.open), float(tb.high), float(tb.low), float(tb.close), float(tb.volume))

    def close_day(self):
        bars, self.bars = self.bars, {'NQ': {}, 'ES': {}}
        if not bars['NQ'] and not bars['ES']:
            return
        complete = self.day.weekday() < 5 and all(len(bars[n]) == NBARS and all(k in bars[n] for k in range(NBARS))
                                                  for n in ('NQ', 'ES'))
        if not complete:
            self.skipped['incomplete'] += 1
            return
        if self.roll_today:
            self.skipped['roll'] += 1
            return
        rec = {'date': self.day}
        for n in ('NQ', 'ES'):
            cols = list(zip(*[bars[n][k] for k in range(NBARS)]))
            rec[n] = {key: np.array(col, dtype=np.float32) for key, col in zip(('o', 'h', 'l', 'c', 'v'), cols)}
        self.days.append(rec)

    def on_end_of_algorithm(self):
        self.close_day()
        res = run_all(self.days)
        res['skipped'] = self.skipped
        for i, n, part in log_chunks(json.dumps(res, separators=(',', ':'))):
            self.log('NEXA_ML1_PART %d/%d %s' % (i, n, part))
