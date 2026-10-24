# NEXA H-LVN-SPEED (HYP-004) on CME index futures. Pre-registration: PREREG_LVN_SPEED.md. Descriptive, not a rule.
# Does price move faster (next-minute |move| / sigma) where yesterday's minute-bar volume profile was thin than where
# it was thick? Mirror-profile placebo. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
from datetime import date, timedelta
import numpy as np

MODE = 'NQ'                 # 'NQ' primary / 'ES' report
TICK = 0.25
SEED, B_BOOT, BLOCK = 20261021, 2000, 20
FIRST_DAY = date(2010, 1, 4)
LOOK, BIN_SHARE, Q, MIN_BINS, EARLY_LAST = 20, 0.02, 0.20, 10, 59   # minutes 0..59 = 09:30-10:29


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


# ---------------------------------------------------------------- engine (pure functions, unit-tested locally)
def bin_width(rng20):
    return max(math.floor(BIN_SHARE * rng20 / TICK + 1e-9) * TICK, TICK)


def profile(h, l, v, pdl, pdh, w):
    """Prior-day volume per bin over [pdl, pdh], each bar's volume spread uniformly over its [low, high]."""
    n = int(math.floor((pdh - pdl) / w + 1e-9)) + 1
    prof = np.zeros(n)
    for hi, lo, vol in zip(h, l, v):
        if vol <= 0:
            continue
        b0 = min(int((lo - pdl) / w + 1e-9), n - 1)
        b1 = min(int((hi - pdl) / w + 1e-9), n - 1)
        if hi <= lo or b0 == b1:
            prof[b0] += vol
            continue
        span = hi - lo
        for b in range(b0, b1 + 1):
            x0, x1 = max(lo, pdl + b * w), min(hi, pdl + (b + 1) * w)
            if b == n - 1:
                x1 = hi
            if x1 > x0:
                prof[b] += vol * (x1 - x0) / span
    return prof


def tags(prof):
    """Per-bin tag: -1 thin (lowest 20 %), +1 thick (highest 20 %), 0 middle. Ties: lower density, then lower price."""
    n = len(prof)
    k = int(math.floor(Q * n))
    t = np.zeros(n, dtype=int)
    idx = np.arange(n)
    asc = np.lexsort((idx, prof))
    desc = np.lexsort((idx, -prof))
    t[desc[:k]] = 1
    t[asc[:k]] = -1
    return t


def day_sums(c, pdl, pdh, w, tag, sigma):
    """Sums of normalised next-minute moves by group for one day. Returns dict of (sum, count) for all/early."""
    n = len(tag)
    res = {g: [0.0, 0] for g in ('thin', 'thick', 'mid', 'thin_e', 'thick_e')}
    for k in range(len(c) - 1):
        p = c[k]
        if p < pdl or p > pdh:
            continue
        b = min(int((p - pdl) / w + 1e-9), n - 1)
        m = abs(c[k + 1] - p) / sigma
        g = {-1: 'thin', 1: 'thick', 0: 'mid'}[int(tag[b])]
        res[g][0] += m
        res[g][1] += 1
        if k <= EARLY_LAST and g != 'mid':
            res[g + '_e'][0] += m
            res[g + '_e'][1] += 1
    return res


def prepare(days):
    out, skipped = [], {'few_bins': 0, 'gap': 0}
    for i, d in enumerate(days):
        if i < LOOK or d['date'] < FIRST_DAY:
            continue
        p = days[i - 1]
        if p['seq'] != d['seq'] - 1 or (d['date'] - p['date']).days > 4:
            skipped['gap'] += 1
            continue
        prior = days[i - LOOK:i]
        rng20 = float(np.mean([x['h'].max() - x['l'].min() for x in prior]))
        sigma = float(np.mean(np.concatenate([np.abs(np.diff(x['c'])) for x in prior])))
        w = bin_width(rng20)
        pdh, pdl = float(p['h'].max()), float(p['l'].min())
        prof = profile(p['h'], p['l'], p['v'], pdl, pdh, w)
        if len(prof) < MIN_BINS or sigma <= 0:
            skipped['few_bins'] += 1
            continue
        tg = tags(prof)
        real = day_sums(d['c'], pdl, pdh, w, tg, sigma)
        mirror = day_sums(d['c'], pdl, pdh, w, tg[::-1], sigma)
        out.append({'date': d['date'], 'real': real, 'mirror': mirror})
    return out, skipped


def ratio(rows, key, a='thin', b='thick'):
    sa = sum(r[key][a][0] for r in rows)
    na = sum(r[key][a][1] for r in rows)
    sb = sum(r[key][b][0] for r in rows)
    nb = sum(r[key][b][1] for r in rows)
    return (sa / na) / (sb / nb) if na and nb and sb > 0 else float('nan')


def run_all(days, mode):
    rows, skipped = prepare(days)
    n = len(rows)
    out = {'mode': mode, 'n_days': n, 'skipped': skipped}
    if n == 0:
        return out
    S, Sm = ratio(rows, 'real'), ratio(rows, 'mirror')
    rng = np.random.default_rng(SEED)
    rs, rms, rd = [], [], []
    for _ in range(B_BOOT):
        sub = [rows[i] for i in block_indices(n, rng)]
        a, b = ratio(sub, 'real'), ratio(sub, 'mirror')
        rs.append(a)
        rms.append(b)
        rd.append(a - b)
    ci = lambda v: [_f(np.nanpercentile(v, 2.5)), _f(np.nanpercentile(v, 97.5))]
    q = np.array_split(np.arange(n), 4)
    blocks = [_f(ratio([rows[i] for i in ix], 'real')) for ix in q]
    cnt = {g: int(sum(r['real'][g][1] for r in rows)) for g in ('thin', 'thick', 'mid')}
    mean_m = {g: _f(sum(r['real'][g][0] for r in rows) / cnt[g]) if cnt[g] else None for g in cnt}
    by_year = {}
    for r in rows:
        by_year.setdefault(r['date'].year, []).append(r)
    out.update({
        'S': _f(S), 'S_ci95': ci(rs), 'S_mirror': _f(Sm), 'S_mirror_ci95': ci(rms),
        'D': _f(S - Sm), 'D_ci95': ci(rd), 'blocks': blocks,
        'blocks_gt1': int(sum(1 for v in blocks if (v or 0) > 1)),
        'minutes': cnt, 'mean_move_sigma': mean_m,
        'S_early_0930_1029': _f(ratio(rows, 'real', 'thin_e', 'thick_e')),
        'S_late_1030_1559': _f(_late_ratio(rows)),
        'S_by_year': {str(y): _f(ratio(v, 'real')) for y, v in sorted(by_year.items())},
    })
    lo_s, lo_d = out['S_ci95'][0], out['D_ci95'][0]
    if S <= 1.0:
        out['verdict'] = 'REFUTED'
    elif S >= 1.10 and (lo_s or 0) > 1 and out['blocks_gt1'] >= 3 and (lo_d or -1) > 0:
        out['verdict'] = 'CONFIRMED'
    else:
        out['verdict'] = 'INCONCLUSIVE'
    return out


def _late_ratio(rows):
    def part(g):
        s = sum(r['real'][g][0] - r['real'][g + '_e'][0] for r in rows)
        c = sum(r['real'][g][1] - r['real'][g + '_e'][1] for r in rows)
        return s / c if c else float('nan')
    a, b = part('thin'), part('thick')
    return a / b if b and np.isfinite(a) and np.isfinite(b) else float('nan')


def log_chunks(algo, tag, obj, size=7000):
    s = json.dumps(obj, separators=(',', ':'))
    parts = [s[i:i + size] for i in range(0, len(s), size)] or ['']
    for i, p in enumerate(parts):
        algo.log(f'{tag} {i + 1}/{len(parts)} {p}')


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaLvn(QCAlgorithm):
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
        self.bars, self.days, self.seq = {}, [], 0
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
            self.bars[m] = (float(tb.open), float(tb.high), float(tb.low), float(tb.close), float(tb.volume))

    def close_day(self):
        bars, self.bars = self.bars, {}
        if not bars:
            return
        self.seq += 1
        complete = len(bars) == 390 and all((570 + k) in bars for k in range(390)) and self.day.weekday() < 5
        if not complete:
            self.skipped['incomplete'] += 1
            return
        if self.roll:
            self.skipped['roll'] += 1
            return
        cols = list(zip(*[bars[570 + k] for k in range(390)]))
        o, h, l, c, v = (np.array(x, dtype=np.float64) for x in cols)
        self.days.append({'seq': self.seq, 'date': self.day, 'h': h, 'l': l, 'c': c, 'v': v})

    def on_end_of_algorithm(self):
        self.close_day()
        res = run_all(self.days, MODE)
        res['skipped_days'] = self.skipped
        res['last_day'] = self.days[-1]['date'].isoformat() if self.days else None
        log_chunks(self, 'NEXA_LVN_RESULT', res)
