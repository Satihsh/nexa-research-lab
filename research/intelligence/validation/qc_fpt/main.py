# NEXA H-FPT-REV on CME index futures. Pre-registration: PREREG_FPT_REV.md (JJ Simon "fair pricing theory", SRC-YT-113).
# Primary P = reversion toward the 09:30 open on 1-minute displacement / break-of-structure signals, 09:31-10:58,
# volatility-scaled 25/38 bracket, 80 % distance filter, 3-consecutive-loss session stop. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
from datetime import date, timedelta
import numpy as np

MODE = 'NQ'                 # 'NQ' primary / 'ES' transfer
F_FROM_NQ = None            # ES run only: F logged by the NQ run (NEXA_FPT_F); None in the NQ run
TICK = 0.25
COST = {'ES': (0.30, 0.60, 1.20), 'NQ': (1.0, 2.0, 3.0)}     # S0, S1, S2 points per round trip
SEED, B_BOOT, BLOCK = 20261018, 2000, 20
FIRST_DAY = date(2010, 1, 4)
REF_FROM = date(2025, 4, 1)
FIX_FROM = date(2023, 1, 3)
K_LAST, K_W, LAST_SIG = 389, 90, 88          # 15:59 bar; RNG window bars 0..89 (09:30-10:59); last signal bar 10:58
LOOK = 20
BASE_STOP, TGT_MULT, MIN_STOP, DIST_SHARE = 25.0, 1.52, 1.0, 0.8
H_REF = 0.397                                # driftless hit rate 1/(1+1.52)


# ---------------------------------------------------------------- statistics (as qc_asm)
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


def is_disp(o, h, l, c, i, d):
    """Displacement in direction d at bar i (PREREG_FPT_REV s.3)."""
    if i < 1:
        return False
    prev_up, prev_dn = c[i - 1] > o[i - 1], c[i - 1] < o[i - 1]
    bigger = abs(c[i] - o[i]) > abs(c[i - 1] - o[i - 1])
    if d < 0:
        return prev_up and c[i] < o[i] and bigger and c[i] < l[i - 1]
    return prev_dn and c[i] > o[i] and bigger and c[i] > h[i - 1]


def fpt_day(o, h, l, c, fp, s, t, cost=0.0, use80=True, last_sig=LAST_SIG):
    """Rule P trades for one day. Returns list of trade dicts (gross in points; R_pts = s)."""
    trades, consec, stopped, free_from = [], 0, False, 1
    act_lo = act_hi = None
    for i in range(1, last_sig + 1):
        j = i - 1
        if j >= 1:                                              # fractal at j confirmed by bar i
            if l[j] < l[j - 1] and l[j] < l[i]:
                act_lo = l[j]
            if h[j] > h[j - 1] and h[j] > h[i]:
                act_hi = h[j]
        bos_s = act_lo is not None and c[i] < act_lo
        bos_l = act_hi is not None and c[i] > act_hi
        if bos_s:
            act_lo = None
        if bos_l:
            act_hi = None
        if stopped or i < free_from:
            continue
        d = -1 if c[i] > fp else (1 if c[i] < fp else 0)
        if d == 0:
            continue
        disp = is_disp(o, h, l, c, i, d)
        bos = bos_s if d < 0 else bos_l
        if not (disp or bos):
            continue
        if use80 and abs(c[i] - fp) < DIST_SHARE * t - 1e-9:
            continue
        k = i + 1
        entry = o[k]
        stop, tgt = entry - d * s, entry + d * t
        ex, kind, kx = scan_exit(h, l, c, k, d, stop, tgt)
        gross = d * (ex - entry)
        trades.append({'dir': d, 'k': k, 'entry': entry, 'R_pts': s, 'exit': ex, 'kind': kind, 'k_exit': kx,
                       'gross': gross, 'trig': 'both' if (disp and bos) else ('disp' if disp else 'bos')})
        free_from = kx + 1
        consec = consec + 1 if (gross - cost) < 0 else 0
        if consec >= 3:
            stopped = True
    return trades


def open_day(o, h, l, c, pre_hi, pre_lo, eve_ref, s, t):
    """V-OPEN continuation trade (PREREG_FPT_REV s.5). Returns list with 0 or 1 trade."""
    d = 1 if c[0] > o[0] else (-1 if c[0] < o[0] else 0)
    if d == 0 or pre_hi is None or pre_lo is None or eve_ref is None:
        return []
    if (d > 0 and not c[0] > pre_hi) or (d < 0 and not c[0] < pre_lo):
        return []
    hb = 1 if o[0] > eve_ref else (-1 if o[0] < eve_ref else 0)
    if hb == 0 or d != -hb:
        return []
    if h[0] - l[0] > s:
        s, t = 2 * s, 2 * t
    entry = o[1]
    stop, tgt = entry - d * s, entry + d * t
    ex, kind, kx = scan_exit(h, l, c, 1, d, stop, tgt)
    return [{'dir': d, 'k': 1, 'entry': entry, 'R_pts': s, 'exit': ex, 'kind': kind, 'k_exit': kx,
             'gross': d * (ex - entry), 'trig': 'open'}]


def scale_series(rngs, dates, f=None):
    """rngs/dates chronological over candidate days. Returns (F, s list with None during warm-up)."""
    if f is None:
        ref = [r for r, dd in zip(rngs, dates) if dd >= REF_FROM]
        f = BASE_STOP / float(np.mean(ref)) if ref else None
    out = []
    for i in range(len(rngs)):
        if i < LOOK or f is None:
            out.append(None)
        else:
            out.append(max(f * float(np.mean(rngs[i - LOOK:i])), MIN_STOP))
    return f, out


def net_r(t, cost):
    return (t['gross'] - cost) / t['R_pts']


def stats(day_trades, costs, years):
    n = len(day_trades)
    s1 = costs[1]
    dsum = np.array([sum(net_r(t, s1) for t in tl) for tl in day_trades], float)
    dcnt = np.array([len(tl) for tl in day_trades], float)
    allt = [t for tl in day_trades for t in tl]
    nt = len(allt)
    out = {'days': n, 'trades': nt, 'trades_per_day': _f(nt / n if n else None)}
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
    out['hit_target'] = _f(np.mean([t['kind'] == 'target' for t in allt]))
    out['hit_ref'] = H_REF
    out['share_time_exit'] = _f(np.mean([t['kind'] == 'time' for t in allt]))
    w = [r for r in rs if r > 0]
    lz = [-r for r in rs if r <= 0]
    out['payoff'] = _f(np.mean(w) / np.mean(lz) if w and lz else None)
    out['long'] = [sum(1 for t in allt if t['dir'] > 0), _f(_mean([net_r(t, s1) for t in allt if t['dir'] > 0]))]
    out['short'] = [sum(1 for t in allt if t['dir'] < 0), _f(_mean([net_r(t, s1) for t in allt if t['dir'] < 0]))]
    out['by_trigger'] = {g: [sum(1 for t in allt if t['trig'] == g), _f(_mean([net_r(t, s1) for t in allt if t['trig'] == g]))]
                         for g in ('disp', 'bos', 'both', 'open')}
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
    peak = np.maximum.accumulate(np.concatenate([[0.0], eq]))
    out['max_dd_R'] = _f(np.max(peak - np.concatenate([[0.0], eq])))
    run = best = 0
    for r in rs:
        run = run + 1 if r < 0 else 0
        best = max(best, run)
    out['longest_losing_streak'] = best
    sd = dsum.std(ddof=1)
    out['daily'] = {'n': n, 'mean': _f(dsum.mean()), 'sd': _f(sd), 'sharpe_ann': _f(dsum.mean() / sd * math.sqrt(252) if sd > 0 else None),
                    'skew': _f(((dsum - dsum.mean()) ** 3).mean() / sd ** 3 if sd > 0 else None),
                    'kurt': _f(((dsum - dsum.mean()) ** 4).mean() / sd ** 4 if sd > 0 else None)}
    out['vs_prop_threshold_0p025'] = bool(dsum.sum() / nt >= 0.025)
    return out


def verdict(s):
    if s['trades'] < 300:
        return 'INSUFFICIENT-N'
    th = s['S1']['theta']
    if th is None or th <= 0:
        return 'REJECTED'
    if (s['S1']['ci95'][0] or -1) > 0 and s['blocks_pos'] >= 3:
        return 'VALIDATED (G4)'
    return 'INCONCLUSIVE'


def run_all(days, mode, f_given=None):
    """days = chronological candidate days: dict(date, o, h, l, c, rng, pre_hi, pre_lo, eve). Returns result dict."""
    rngs = [d['rng'] for d in days]
    dates = [d['date'] for d in days]
    f, sc = scale_series(rngs, dates, f_given)
    costs = COST[mode]
    streams = {'P': [], 'V-NO80': [], 'V-OPEN': []}
    if mode == 'NQ':
        streams['V-FIX'] = []
    years, fix_years = [], []
    for d, s in zip(days, sc):
        if s is None or d['date'] < FIRST_DAY:
            continue
        t = TGT_MULT * s
        o, h, l, c = d['o'], d['h'], d['l'], d['c']
        fp = o[0]
        years.append(d['date'].year)
        streams['P'].append(fpt_day(o, h, l, c, fp, s, t, costs[1], True))
        streams['V-NO80'].append(fpt_day(o, h, l, c, fp, s, t, costs[1], False))
        streams['V-OPEN'].append(open_day(o, h, l, c, d['pre_hi'], d['pre_lo'], d['eve'], s, t))
        if mode == 'NQ' and d['date'] >= FIX_FROM:
            streams['V-FIX'].append(fpt_day(o, h, l, c, fp, BASE_STOP, BASE_STOP * TGT_MULT, costs[1], True))
            fix_years.append(d['date'].year)
    out = {'mode': mode, 'F': _f(f), 'n_days': len(years)}
    for k, v in streams.items():
        st = stats(v, costs, fix_years if k == 'V-FIX' else years)
        out[k] = st | {'verdict': verdict(st)}
    return out


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaFpt(QCAlgorithm):
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
        self.bars, self.pre, self.eve = {}, {}, {}
        self.days = []
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
        elif 565 <= m <= 569:
            self.pre[m] = (float(tb.high), float(tb.low))
        elif 1260 <= m <= 1289:
            self.eve[d] = float(tb.close)

    def close_day(self):
        bars, pre, self.bars, self.pre = self.bars, self.pre, {}, {}
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
        full_pre = all(m in pre for m in range(565, 570))
        self.days.append({'date': self.day, 'o': o, 'h': h, 'l': l, 'c': c,
                          'rng': float(h[:K_W].max() - l[:K_W].min()),
                          'pre_hi': max(pre[m][0] for m in range(565, 570)) if full_pre else None,
                          'pre_lo': min(pre[m][1] for m in range(565, 570)) if full_pre else None,
                          'eve': self.eve.get(self.day - timedelta(days=1))})
        if len(self.eve) > 10:
            for k in sorted(self.eve)[:-5]:
                del self.eve[k]

    def on_end_of_algorithm(self):
        self.close_day()
        res = run_all(self.days, MODE, F_FROM_NQ)
        res['skipped'] = self.skipped
        res['first_day'] = FIRST_DAY.isoformat()
        res['last_day'] = self.days[-1]['date'].isoformat() if self.days else None
        self.log('NEXA_FPT_F ' + json.dumps({'mode': MODE, 'F': res['F']}))
        self.log('NEXA_FPT_RESULT ' + json.dumps(res, separators=(',', ':')))
