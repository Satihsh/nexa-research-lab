# NEXA H-FLOW-PRED: walk-forward "Market Predicted" order-flow probability engine, NQ primary / ES secondary.
# Pre-registration: PREREG_FLOW_PRED.md. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
import time
from datetime import date, timedelta
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

MODE = 'ES'                                            # 'NQ' | 'ES' | 'PROBE'
RUNG = 3                                               # PREREG s.1a: 1 tick 2024, 2 tick 2025, 3 second-resolution fallback
SEED, B_BOOT, BLOCK, DAY_BLOCK = 20261021, 2000, 20, 5
NSEC, NMIN = 23400, 390
DEC_K = np.arange(29, 360)                             # 10:00 ... 15:30 ET decision bars (331)
H_SEC = (30, 300, 600, 900)
LOOK, TICK, FLOOR_TICKS = 20, 0.25, 4
COST = {'NQ': (1.0, 2.0, 3.0), 'ES': (0.30, 0.60, 1.20)}  # S0, S1, S2 points round trip
BIG = {'NQ': 10, 'ES': 50}
DELTA_Q, MAX_TRADES, N_PLACEBO = 0.98, 3, 20
PASS_MEAN, P_MAX = 0.025, 0.0125
CLIP = 20.0
FEATURES = ['tod', 'tod2', 'r1', 'r5', 'r15', 'r30', 'rv', 'rng',
            'poc_p', 'vah_p', 'val_p', 'pdh', 'pdl', 'orh', 'orl', 'dpoc', 'shape', 'node',
            'imb1', 'imb5', 'imb15', 'cvd', 'big15', 'div15', 'part5',
            'book', 'book5', 'absorb5', 'qrate5']
FAMILIES = {'D': list(range(0, 8)), 'A': list(range(8, 18)), 'B': list(range(18, 25)), 'C': list(range(25, 29))}
LOG_CHUNK = 7000


# ---------------------------------------------------------------- statistics
def _f(x, nd=5):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, nd) if np.isfinite(x) else None


def block_indices(n, rng, L):
    if n <= L:
        return rng.integers(0, n, n)
    nb = int(math.ceil(n / L))
    st = rng.integers(0, n - L + 1, nb)
    return (st[:, None] + np.arange(L)[None, :]).ravel()[:n]


def boot_mean(x, L=BLOCK, seed=SEED):
    x = np.asarray(x, float)
    n = len(x)
    if n == 0:
        return {'n': 0, 'mean': None, 'ci': [None, None], 'p': None}
    rng = np.random.default_rng(seed)
    reps = np.array([x[block_indices(n, rng, L)].mean() for _ in range(B_BOOT)])
    return {'n': n, 'mean': _f(x.mean()), 'ci': [_f(np.percentile(reps, 2.5)), _f(np.percentile(reps, 97.5))],
            'p': _f((1 + np.sum(reps <= 0)) / (B_BOOT + 1), 4)}


# ---------------------------------------------------------------- tick store
def classify(p, bid, ask, last_px, last_sign):
    """Quote rule; at the mid (or without quotes) the tick rule; 0 if undetermined."""
    if bid is not None and ask is not None and ask > bid:
        if p >= ask:
            return 1
        if p <= bid:
            return -1
        mid = 0.5 * (bid + ask)
        if p > mid:
            return 1
        if p < mid:
            return -1
    if last_px is None:
        return 0
    if p > last_px:
        return 1
    if p < last_px:
        return -1
    return last_sign


class DayStore:
    """Per-second arrays for one RTH session."""
    def __init__(self):
        self.hi = np.full(NSEC, np.nan)
        self.lo = np.full(NSEC, np.nan)
        self.last = np.full(NSEC, np.nan)
        for k in ('vol', 'buy', 'sell', 'bbuy', 'bsell', 'ntr', 'nq'):
            setattr(self, k, np.zeros(NSEC))
        self.bsz = np.full(NSEC, np.nan)
        self.asz = np.full(NSEC, np.nan)
        self.bid = self.ask = self.last_px = None
        self.last_sign = 0
        self.bid_sz = self.ask_sz = 0.0

    def quote(self, s, bid=0.0, ask=0.0, bid_sz=None, ask_sz=None):
        """One-sided updates allowed: each side changes only when its price is > 0."""
        if bid > 0:
            self.bid = bid
            if bid_sz is not None:
                self.bid_sz = bid_sz
        if ask > 0:
            self.ask = ask
            if ask_sz is not None:
                self.ask_sz = ask_sz
        self.nq[s] += 1
        self.bsz[s], self.asz[s] = self.bid_sz, self.ask_sz

    def trade(self, s, p, q, big, use_quotes=True):
        sg = classify(p, self.bid if use_quotes else None, self.ask if use_quotes else None, self.last_px, self.last_sign)
        if self.last_px is None or p != self.last_px:
            self.last_px = p
        self.last_sign = sg
        self.hi[s] = p if np.isnan(self.hi[s]) else max(self.hi[s], p)
        self.lo[s] = p if np.isnan(self.lo[s]) else min(self.lo[s], p)
        self.last[s] = p
        self.vol[s] += q
        self.ntr[s] += 1
        if sg > 0:
            self.buy[s] += q
            if q >= big:
                self.bbuy[s] += q
        elif sg < 0:
            self.sell[s] += q
            if q >= big:
                self.bsell[s] += q


def ffill(a):
    """Forward-fill NaNs (leading NaNs stay NaN)."""
    idx = np.where(np.isnan(a), 0, np.arange(len(a)))
    np.maximum.accumulate(idx, out=idx)
    return a[idx]


def finish_day(st):
    """Per-second store -> day dict (None if not every minute has a trade)."""
    ntr_m = st.ntr.reshape(NMIN, 60).sum(1)
    if (ntr_m == 0).any():
        return None
    last = ffill(st.last)
    bsz, asz = np.nan_to_num(ffill(st.bsz)), np.nan_to_num(ffill(st.asz))
    tot = bsz + asz
    book_s = np.where(tot > 0, (bsz - asz) / np.where(tot > 0, tot, 1), 0.0)
    m = lambda a: a.reshape(NMIN, 60).sum(1)
    hi_m = np.nanmax(st.hi.reshape(NMIN, 60), 1)
    lo_m = np.nanmin(st.lo.reshape(NMIN, 60), 1)
    d = {'hi': st.hi, 'lo': st.lo, 'last': last, 'vol_s': st.vol,
         'c': last[59::60].copy(), 'h': hi_m, 'l': lo_m, 'v': m(st.vol), 'buy': m(st.buy), 'sell': m(st.sell),
         'bbuy': m(st.bbuy), 'bsell': m(st.bsell), 'ntr': ntr_m, 'nq': m(st.nq), 'book': book_s[59::60].copy()}
    d['stats'] = day_stats(d)
    return d


# ---------------------------------------------------------------- profiles
def price_bins(p):
    return np.round(np.asarray(p, float) / TICK).astype(np.int64)


def value_area(bins, vols, share=0.70):
    """POC and value area (70 %, grown from the POC, larger neighbour first). bins sorted ascending, unique."""
    bins, vols = np.asarray(bins), np.asarray(vols, float)
    i = int(np.argmax(vols))
    lo = hi = i
    acc, target = vols[i], share * vols.sum()
    while acc < target and (lo > 0 or hi < len(vols) - 1):
        up = vols[hi + 1] if hi < len(vols) - 1 else -1.0
        dn = vols[lo - 1] if lo > 0 else -1.0
        if up >= dn:
            hi += 1
            acc += up
        else:
            lo -= 1
            acc += dn
    return bins[i] * TICK, bins[hi] * TICK, bins[lo] * TICK


def day_profile(d):
    ok = d['vol_s'] > 0
    b = price_bins(d['last'][ok])
    ub, inv = np.unique(b, return_inverse=True)
    vols = np.bincount(inv, weights=d['vol_s'][ok])
    return ub, vols


def day_stats(d):
    ub, vols = day_profile(d)
    poc, vah, val = value_area(ub, vols)
    return {'sd1': float(np.std(np.diff(d['c']))), 'range': float(np.nanmax(d['h']) - np.nanmin(d['l'])),
            'vbar': float(d['v'].mean()), 'poc': poc, 'vah': vah, 'val': val,
            'high': float(np.nanmax(d['h'])), 'low': float(np.nanmin(d['l']))}


def history(stats, i):
    """Values for kept day i from the previous LOOK kept days only."""
    if i < LOOK:
        return None
    prev = stats[i - LOOK:i]
    return {'sig1': float(np.mean([s['sd1'] for s in prev])), 'vbar': float(np.mean([s['vbar'] for s in prev])),
            'rbar': float(np.mean([s['range'] for s in prev])), 'prev': stats[i - 1]}


def dev_profile(d):
    """Cumulative per-minute profile: (bins, cum[390, nb])."""
    ok = d['vol_s'] > 0
    b = price_bins(d['last'][ok])
    b0 = int(b.min())
    nb = int(b.max()) - b0 + 1
    mins = np.nonzero(ok)[0] // 60
    prof = np.zeros((NMIN, nb))
    np.add.at(prof, (mins, b - b0), d['vol_s'][ok])
    return b0, np.cumsum(prof, axis=0)


# ---------------------------------------------------------------- features and labels
def _imb(b, s):
    t = b + s
    return np.where(t > 0, (b - s) / np.where(t > 0, t, 1), 0.0)


def _win(a, n):
    """Sum over the last n minutes ending at each minute (inclusive)."""
    c = np.concatenate([[0.0], np.cumsum(a)])
    i = np.arange(NMIN)
    return c[i + 1] - c[np.maximum(i + 1 - n, 0)]


def day_features(d, hist):
    """Feature matrix (331, 29) for one day; only data at or before each decision minute."""
    s1, vb, rb, pv = hist['sig1'], hist['vbar'], hist['rbar'], hist['prev']
    c, K = d['c'], DEC_K
    p = c[K]
    dc = np.diff(c, prepend=c[0])
    sq = np.concatenate([[0.0], np.cumsum(dc ** 2)])
    sm = np.concatenate([[0.0], np.cumsum(dc)])
    n = K.astype(float)                                # changes 1..k (dc[0] = 0 excluded)
    rv = np.sqrt(np.maximum((sq[K + 1] - sq[1]) / n - ((sm[K + 1] - sm[1]) / n) ** 2, 0.0)) / s1
    hi_run, lo_run = np.fmax.accumulate(d['h']), np.fmin.accumulate(d['l'])
    rng_k = hi_run[K] - lo_run[K]
    orh, orl = np.nanmax(d['h'][:30]), np.nanmin(d['l'][:30])
    b0, cum = dev_profile(d)
    ck = cum[K]
    dpoc = (np.argmax(ck, 1) + b0) * TICK
    shape = np.where(rng_k > 0, (dpoc - lo_run[K]) / np.where(rng_k > 0, rng_k, 1), 0.5)
    ib = price_bins(p) - b0
    csum = np.concatenate([np.zeros((len(K), 1)), np.cumsum(ck, 1)], 1)
    nbins = ck.shape[1]
    lo_i, hi_i = np.clip(ib - 2, 0, nbins), np.clip(ib + 3, 0, nbins)
    near = csum[np.arange(len(K)), hi_i] - csum[np.arange(len(K)), lo_i]
    mean_px = ck.sum(1) / np.maximum((ck > 0).sum(1), 1)
    node = np.log((near + 1) / (5 * mean_px + 1))
    b1, s1m = d['buy'], d['sell']
    imb1, imb5, imb15 = _imb(b1, s1m), _imb(_win(b1, 5), _win(s1m, 5)), _imb(_win(b1, 15), _win(s1m, 15))
    cb, cs = np.cumsum(b1), np.cumsum(s1m)
    cv = np.cumsum(d['v'])
    cvd = np.where(cv > 0, (cb - cs) / np.where(cv > 0, cv, 1), 0.0)
    v15, v5 = _win(d['v'], 15), _win(d['v'], 5)
    big15 = np.where(v15 > 0, (_win(d['bbuy'], 15) - _win(d['bsell'], 15)) / np.where(v15 > 0, v15, 1), 0.0)
    o0 = d['last'][int(np.argmax(~np.isnan(d['last'])))]
    r = lambda m: (p - np.where(K - m >= 0, c[np.maximum(K - m, 0)], o0)) / (s1 * math.sqrt(m))  # before 09:30 -> open
    r15 = r(15)
    book5 = _win(d['book'], 5) / 5.0
    X = np.column_stack([
        K / 389.0, (K / 389.0) ** 2, r(1), r(5), r15, r(30), rv, rng_k / rb,
        (p - pv['poc']) / s1, (p - pv['vah']) / s1, (p - pv['val']) / s1, (p - pv['high']) / s1, (p - pv['low']) / s1,
        (p - orh) / s1, (p - orl) / s1, (p - dpoc) / s1, shape, node,
        imb1[K], imb5[K], imb15[K], cvd[K], big15[K], r15 * imb15[K], np.log((v5[K] + 1) / (5 * vb + 1)),
        d['book'][K], book5[K], np.log1p(v5[K] / vb) - np.log1p(np.abs(p - c[K - 5]) / s1),
        np.log1p(_win(d['nq'], 5)[K]) - np.log1p(_win(d['ntr'], 5)[K]),
    ])
    return np.clip(X, -CLIP, CLIP)


def barrier(d, k, h, u, direction):
    """Gross R and exit second of a +-u bracket entered at the close of minute k; stop first within a second."""
    s0 = 60 * (k + 1)
    entry = d['c'][k]
    s1 = min(s0 + h, NSEC)
    hi, lo = d['hi'][s0:s1], d['lo'][s0:s1]
    with np.errstate(invalid='ignore'):
        up, dn = hi >= entry + u, lo <= entry - u
    stop, tgt = (dn, up) if direction > 0 else (up, dn)
    i_s = int(np.argmax(stop)) if stop.any() else None
    i_t = int(np.argmax(tgt)) if tgt.any() else None
    if i_s is not None and (i_t is None or i_s <= i_t):
        return -1.0, s0 + i_s
    if i_t is not None:
        return 1.0, s0 + i_t
    return direction * (d['last'][s1 - 1] - entry) / u, s1 - 1


def unit(sig1, h):
    return max(sig1 * math.sqrt(h / 60.0), FLOOR_TICKS * TICK)


def day_labels(d, sig1):
    """Per horizon: long R, short R, long exit sec, short exit sec, u. Arrays of length 331."""
    out = {}
    for h in H_SEC:
        u = unit(sig1, h)
        L = np.array([barrier(d, k, h, u, 1) for k in DEC_K])
        S = np.array([barrier(d, k, h, u, -1) for k in DEC_K])
        out[h] = {'gl': L[:, 0], 'el': L[:, 1], 'gs': S[:, 0], 'es': S[:, 1], 'u': u}
    return out


def process_day(prev_stats, dd):
    """Features and labels for one kept day from the previous kept days' stats (None during warm-up)."""
    hist = history(prev_stats, len(prev_stats))
    if hist is None:
        return None
    return day_features(dd, hist), day_labels(dd, hist['sig1'])


def stack(dates, X, labs):
    return {'dates': dates, 'X': np.array(X, float).reshape(len(X), len(DEC_K), len(FEATURES)),
            'lab': {h: {key: np.array([lb[h][key] for lb in labs], float) for key in ('gl', 'el', 'gs', 'es', 'u')}
                    for h in H_SEC}}


def build_dataset(days):
    """days: list of (date, day dict) for kept days (tests; the algorithm builds rows day by day)."""
    stats, dates, X, labs = [], [], [], []
    for dt, dd in days:
        r = process_day(stats, dd)
        stats.append(dd['stats'])
        if r is not None:
            dates.append(dt)
            X.append(r[0])
            labs.append(r[1])
    return stack(dates, X, labs)


# ---------------------------------------------------------------- walk-forward
def quarter(dt):
    return dt.year * 4 + (dt.month - 1) // 3


def folds(dates):
    """List of (train_day_idx, test_day_idx, quarter_id). Test quarters need >= 4 earlier quarters of rows."""
    q = np.array([quarter(d) for d in dates])
    uq = sorted(set(q))
    out = []
    for j, tq in enumerate(uq):
        if j < 4:
            continue
        te = np.nonzero(q == tq)[0]
        if j == len(uq) - 1 and len(te) < 20:
            continue
        out.append((np.nonzero(q < tq)[0], te, int(tq)))
    return out


def labels_y(gl):
    y = np.where(gl > 0, 1, np.where(gl < 0, 0, -1))
    return y


def fit(X, y):
    sc = StandardScaler().fit(X)
    m = LogisticRegression(C=1.0, solver='lbfgs', max_iter=1000).fit(np.nan_to_num(sc.transform(X)), y)
    return sc, m


def predict(model, X):
    sc, m = model
    return m.predict_proba(np.nan_to_num(sc.transform(X)))[:, 1]


def flat(X3, y2, cols):
    X = X3[:, :, cols].reshape(-1, len(cols))
    y = y2.reshape(-1)
    ok = y >= 0
    return X[ok], y[ok]


def train_with_delta(X3, Y, tr_idx, dates, cols):
    """Calibration fit on training minus its last 2 quarters -> delta; then refit on all training days."""
    q = np.array([quarter(dates[i]) for i in tr_idx])
    last2 = sorted(set(q))[-2:]
    cal_fit, cal_ev = tr_idx[~np.isin(q, last2)], tr_idx[np.isin(q, last2)]
    m0 = fit(*flat(X3[cal_fit], Y[cal_fit], cols))
    pc = predict(m0, X3[cal_ev][:, :, cols].reshape(-1, len(cols)))
    delta = float(np.quantile(np.abs(pc - 0.5), DELTA_Q))
    return fit(*flat(X3[tr_idx], Y[tr_idx], cols)), delta


def trade_day(p, lab_day, delta, costs):
    """Up to MAX_TRADES non-overlapping trades in time order for one day. lab_day: dict of 331-arrays + u."""
    out, busy = [], -1
    for j in np.nonzero(np.abs(p - 0.5) >= delta)[0]:
        if len(out) >= MAX_TRADES:
            break
        if busy >= 60 * (DEC_K[j] + 1):
            continue
        dirn = 1 if p[j] > 0.5 else -1
        g = lab_day['gl'][j] if dirn > 0 else lab_day['gs'][j]
        busy = lab_day['el'][j] if dirn > 0 else lab_day['es'][j]
        u = lab_day['u']
        out.append({'j': int(j), 'dir': dirn, 'gross': float(g), 'long': float(lab_day['gl'][j]),
                    'net': [float(g - cp / u) for cp in costs]})
    return out


def day_lab(lab, i):
    return {'gl': lab['gl'][i], 'el': lab['el'][i], 'gs': lab['gs'][i], 'es': lab['es'][i], 'u': lab['u'][i]}


def day_shift(Y, tr_idx, seed):
    """Placebo: training day i gets the labels (same minutes) of training day (i + m) mod n."""
    n = len(tr_idx)
    m = int(np.random.default_rng(seed).integers(max(n // 10, 1), max(n - n // 10, 2)))
    Ys = Y.copy()
    Ys[tr_idx] = Y[tr_idx[(np.arange(n) + m) % n]]
    return Ys


def run_model(data, h, costs, cols, fl, Y_override=None):
    """Walk-forward one configuration at horizon h. Returns trades (with day idx), per-day Brier list, deltas."""
    X3, dates, lab = data['X'], data['dates'], data['lab'][h]
    Y = labels_y(lab['gl'])
    trades, brier_days, deltas, clim = [], {}, [], []
    for tr, te, tq in fl:
        Ytr = Y if Y_override is None else Y_override(Y, tr)
        model, delta = train_with_delta(X3, Ytr, tr, dates, cols)
        deltas.append(delta)
        base = float(np.mean(flat(X3[tr], Ytr[tr], cols)[1]))
        for i in te:
            p = predict(model, X3[i][:, cols])
            ok = Y[i] >= 0
            if ok.any():
                brier_days[i] = (float(np.mean((p[ok] - Y[i][ok]) ** 2)), float(np.mean((base - Y[i][ok]) ** 2)))
            for t in trade_day(p, day_lab(lab, i), delta, costs):
                t['i'], t['q'] = int(i), tq
                trades.append(t)
    return trades, brier_days, deltas


def summarise(trades, n_days, fl):
    if not trades:
        return {'n': 0}
    s1 = np.array([t['net'][1] for t in trades])
    days = {}
    for t, x in zip(trades, s1):
        days[t['i']] = days.get(t['i'], 0.0) + x
    qm = {}
    for t, x in zip(trades, s1):
        qm.setdefault(t['q'], []).append(x)
    qmeans = [float(np.mean(qm[tq])) if tq in qm else None for _, _, tq in fl]
    return {'S1': boot_mean(s1), 'S0': _f(np.mean([t['net'][0] for t in trades])),
            'S2': _f(np.mean([t['net'][2] for t in trades])), 'gross': _f(np.mean([t['gross'] for t in trades])),
            'win': _f(np.mean(s1 > 0), 3), 'tpd': _f(len(trades) / max(n_days, 1), 3),
            'green': _f(np.mean([v > 0 for v in days.values()]), 3),
            'B1': _f(np.mean([t['long'] - (t['gross'] - t['net'][1]) for t in trades])),
            'long_share': _f(np.mean([t['dir'] > 0 for t in trades]), 3),
            'q': [_f(x, 4) for x in qmeans], 'q_pos': int(sum(1 for x in qmeans if x is not None and x > 0)),
            'n_q': len(fl)}


def verdict(st, p_rank):
    s = st.get('S1')
    if not s or s['n'] < 100:
        return 'INSUFFICIENT-N'
    if s['mean'] <= 0:
        return 'REJECTED'
    ok = (s['mean'] >= PASS_MEAN and s['ci'][0] is not None and s['ci'][0] > 0 and s['p'] <= P_MAX
          and st['q_pos'] >= math.ceil(2 * st['n_q'] / 3) and p_rank is not None and p_rank <= 0.05)
    return 'VALIDATED' if ok else 'INCONCLUSIVE'


def overall(verdicts):
    v = list(verdicts)
    if 'VALIDATED' in v:
        return 'VALIDATED'
    if all(x in ('REJECTED', 'INSUFFICIENT-N') for x in v):
        return 'REJECTED'
    return 'INCONCLUSIVE'


def final_coefs(data, h, cols):
    """Model fitted on all rows (for the ATAS panel if not REJECTED): scaler mean, scale, coef, intercept."""
    sc, m = fit(*flat(data['X'], labels_y(data['lab'][h]['gl']), cols))
    r = lambda a: [float('%.4g' % x) for x in a]
    return {'mu': r(sc.mean_), 'sd': r(sc.scale_), 'w': r(m.coef_[0]), 'b': float('%.4g' % m.intercept_[0])}


def run_all(data, target, n_placebo=N_PLACEBO):
    fl = folds(data['dates'])
    costs = COST[target]
    allc = list(range(len(FEATURES)))
    out = {'target': target, 'n_days': len(data['dates']),
           'first': data['dates'][0].isoformat() if data['dates'] else None,
           'last': data['dates'][-1].isoformat() if data['dates'] else None,
           'test_q': ['%dQ%d' % (tq // 4, tq % 4 + 1) for _, _, tq in fl], 'H': {}}
    if not fl:
        out['overall'] = 'INSUFFICIENT-N'
        return out
    n_test_days = sum(len(te) for _, te, _ in fl)
    for h in H_SEC:
        tr, bd, deltas = run_model(data, h, costs, allc, fl)
        st = summarise(tr, n_test_days, fl)
        keys = sorted(bd)
        b_full = np.array([bd[i][0] for i in keys])
        b_clim = np.array([bd[i][1] for i in keys])
        res = {'delta': [_f(x, 4) for x in deltas], 'base': _f(np.mean(labels_y(data['lab'][h]['gl']) == 1), 4),
               'u_mean': _f(np.mean(data['lab'][h]['u']), 3), 'stats': st,
               'brier': _f(b_full.mean()), 'bss': _f(1 - b_full.mean() / b_clim.mean()) if len(keys) else None, 'abl': {}}
        for fam, fcols in FAMILIES.items():
            cols = [c for c in allc if c not in fcols]
            trd, bdd, _ = run_model(data, h, costs, cols, fl)
            diff = np.array([bdd[i][0] for i in keys]) - b_full
            bm = boot_mean(diff, L=DAY_BLOCK)
            res['abl'][fam] = {'dB': _f(bm['mean'], 7), 'ci': [_f(x, 7) for x in bm['ci']],
                               'adds': bool(bm['ci'][0] is not None and bm['ci'][0] > 0),
                               'net': _f(np.mean([t['net'][1] for t in trd])) if trd else None}
        pl = []
        for s in range(1, n_placebo + 1):
            tp, _, _ = run_model(data, h, costs, allc, fl, Y_override=lambda Y, tri, s=s: day_shift(Y, tri, s))
            pl.append(float(np.mean([t['net'][1] for t in tp])) if tp else float('nan'))
        hm = st.get('S1', {}).get('mean')
        fin = [x for x in pl if np.isfinite(x)]
        res['p_rank'] = _f(np.mean([x >= hm for x in fin]), 3) if (hm is not None and fin) else None
        res['pl_mean'] = _f(np.mean(fin)) if fin else None
        res['verdict'] = verdict(st, res['p_rank'])
        if res['verdict'] != 'REJECTED':
            res['coef'] = final_coefs(data, h, allc)
        out['H'][str(h)] = res
    out['overall'] = overall(r['verdict'] for r in out['H'].values())
    return out


def log_chunks(text, size=LOG_CHUNK):
    parts = [text[i:i + size] for i in range(0, len(text), size)] or ['']
    return [(i + 1, len(parts), p) for i, p in enumerate(parts)]


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaFlowPred(QCAlgorithm):
    def initialize(self):
        self.t0 = time.time()
        self.name = 'ES' if MODE == 'ES' else 'NQ'
        fut = Futures.Indices.SP_500_E_MINI if self.name == 'ES' else Futures.Indices.NASDAQ_100_E_MINI
        if MODE == 'PROBE':
            self.set_start_date(2024, 1, 2)
            self.set_end_date(2024, 1, 8)
        else:
            self.set_start_date(2025, 1, 2) if RUNG == 2 else self.set_start_date(2024, 1, 2)
        self.res = Resolution.SECOND if (RUNG == 3 and MODE != 'PROBE') else Resolution.TICK
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        f = self.add_future(fut, self.res, fill_forward=False, extended_market_hours=False,
                            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
                            data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
        self.sym = f.symbol
        self.big = BIG[self.name]
        self.day, self.roll_today, self.roll_pending = None, False, False
        self.store = DayStore()
        self.stats, self.dates, self.X, self.labs = [], [], [], []
        self.skipped = {'incomplete': 0, 'roll': 0}
        self.probe = {'trade': 0, 'quote': 0, 'days': set()}

    def on_data(self, data):
        for _ in data.symbol_changed_events.items():
            self.roll_pending = True
        t = self.time - timedelta(seconds=1) if self.res == Resolution.SECOND else self.time
        d = t.date()
        if d != self.day:
            if self.day is not None and MODE != 'PROBE':
                self.close_day()
            self.roll_today, self.roll_pending = self.roll_pending, False
            self.store = DayStore()
        self.day = d
        s = t.hour * 3600 + t.minute * 60 + t.second - 34200
        if not 0 <= s < NSEC:
            return
        if self.res == Resolution.SECOND:
            qb = data.quote_bars.get(self.sym)
            if qb is not None:
                self.store.quote(s, float(qb.bid.close) if qb.bid is not None else 0.0,
                                 float(qb.ask.close) if qb.ask is not None else 0.0,
                                 float(qb.last_bid_size), float(qb.last_ask_size))
            tb = data.bars.get(self.sym)
            if tb is not None and tb.volume > 0:
                self.store.trade(s, float(tb.close), float(tb.volume), float('inf'), use_quotes=False)
            return
        ticks = data.ticks.get(self.sym)
        if ticks is None:
            return
        st = self.store
        for tk in ticks:
            if tk.tick_type == TickType.QUOTE:
                st.quote(s, float(tk.bid_price), float(tk.ask_price), float(tk.bid_size), float(tk.ask_size))
                if MODE == 'PROBE':
                    self.probe['quote'] += 1
            elif tk.tick_type == TickType.TRADE and tk.quantity > 0:
                st.trade(s, float(tk.last_price), float(tk.quantity), self.big)
                if MODE == 'PROBE':
                    self.probe['trade'] += 1
                    self.probe['days'].add(d)

    def close_day(self):
        st, self.store = self.store, DayStore()
        if self.day.weekday() >= 5 or not st.ntr.any():
            return
        dd = finish_day(st)
        if dd is None:
            self.skipped['incomplete'] += 1
            return
        if self.roll_today:
            self.skipped['roll'] += 1
            return
        r = process_day(self.stats, dd)                # per-second arrays are dropped after this day
        self.stats.append(dd['stats'])
        if r is not None:
            self.dates.append(self.day)
            self.X.append(r[0])
            self.labs.append(r[1])

    def on_end_of_algorithm(self):
        if MODE == 'PROBE':
            nd = len(self.probe['days'])
            self.log('NEXA_FP_PROBE ' + json.dumps({'days': nd, 'trade_ticks': self.probe['trade'],
                                                    'quote_ticks': self.probe['quote'],
                                                    'wall_s': round(time.time() - self.t0, 1),
                                                    'wall_s_per_day': round((time.time() - self.t0) / max(nd, 1), 1)}))
            return
        self.close_day()
        res = run_all(stack(self.dates, self.X, self.labs), self.name)
        res['skipped'], res['rung'], res['wall_s'] = self.skipped, RUNG, round(time.time() - self.t0)
        for i, n, part in log_chunks(json.dumps(res, separators=(',', ':'))):
            self.log('NEXA_FP_PART %d/%d %s' % (i, n, part))
