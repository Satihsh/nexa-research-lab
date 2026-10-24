# NEXA H-SWEEP on CME index futures. Pre-registration: PREREG_SWEEP.md.
# Prior-day RTH high/low swept by >= 2 ticks (09:31-14:59): Arm A = continuation (Osler 2005), Arm B = close back
# inside within 15 min, then fade (video claim). Distance-matched placebo levels. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
from datetime import date, timedelta
import numpy as np

MODE = 'ES'                 # 'NQ' primary / 'ES' transfer
TICK = 0.25
COST = {'ES': (0.30, 0.60, 1.20), 'NQ': (1.0, 2.0, 3.0)}     # S0, S1, S2 points per round trip
SEED, B_BOOT, BLOCK = 20261021, 2000, 20
FIRST_DAY = date(2010, 1, 4)
HOLD_FROM = date(2023, 1, 3)
K_LAST, LAST_SIG = 389, 329                  # 15:59 bar; last signal bar 14:59
LOOK = 20
S_SHARE, MIN_S, SWEEP, RECLAIM, TGT, MIN_R = 0.10, 1.0, 2 * TICK, 15, 2.0, 1.0
N_PLAC = 20
H_REF = 1.0 / 3.0


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


def first_sweep(h, l, o0, level, side):
    """First bar k in 1..LAST_SIG sweeping the level by >= 2 ticks; None if gapped beyond it or never swept."""
    if side > 0:
        if o0 >= level:
            return None
        hit = np.nonzero(h[1:LAST_SIG + 1] >= level + SWEEP - 1e-9)[0]
    else:
        if o0 <= level:
            return None
        hit = np.nonzero(l[1:LAST_SIG + 1] <= level - SWEEP + 1e-9)[0]
    return int(hit[0]) + 1 if len(hit) else None


def candidates(o, h, l, c, levels, s, arm):
    """Candidate trades (entry bar, dir, stop, target, R_pts, side) for one arm; levels = {+1: high, -1: low}."""
    out, skipped_r = [], 0
    for side, lev in levels.items():
        if lev is None:
            continue
        k = first_sweep(h, l, o[0], lev, side)
        if k is None:
            continue
        if arm == 'A':
            e = k + 1
            d = side
            entry = o[e]
            out.append((e, d, entry - d * s, entry + d * TGT * s, s, side))
        else:
            j = None
            for jj in range(k, min(k + RECLAIM, LAST_SIG) + 1):
                if (c[jj] < lev) if side > 0 else (c[jj] > lev):
                    j = jj
                    break
            if j is None:
                continue
            e = j + 1
            d = -side
            entry = o[e]
            if side > 0:
                stop = float(np.max(h[k:j + 1])) + TICK
                r = stop - entry
            else:
                stop = float(np.min(l[k:j + 1])) - TICK
                r = entry - stop
            if r <= 0 or r < MIN_R:
                skipped_r += 1
                continue
            out.append((e, d, stop, entry + d * TGT * r, r, side))
    return sorted(out), skipped_r


def sweep_day(o, h, l, c, levels, s, arm):
    """Trades for one day and arm, one position at a time. Returns (trades, skipped_open, skipped_r)."""
    cands, skipped_r = candidates(o, h, l, c, levels, s, arm)
    trades, busy_until, skipped_open = [], -1, 0
    for e, d, stop, tgt, rp, side in cands:
        if e <= busy_until:
            skipped_open += 1
            continue
        ex, kind, kx = scan_exit(h, l, c, e, d, stop, tgt)
        trades.append({'dir': d, 'side': side, 'k': e, 'entry': o[e], 'R_pts': rp, 'exit': ex, 'kind': kind,
                       'k_exit': kx, 'gross': d * (ex - o[e])})
        busy_until = kx
    return trades, skipped_open, skipped_r


def placebo_levels(o0, pdh, pdl, rng):
    def m():
        while True:
            x = rng.uniform(0.7, 1.3)
            if not (0.95 <= x <= 1.05):
                return x
    hi = o0 + m() * (pdh - o0) if o0 < pdh else None
    lo = o0 - m() * (o0 - pdl) if o0 > pdl else None
    return {1: hi, -1: lo}


def prepare(days):
    """Attach s(d), PDH, PDL to usable days (PREREG_SWEEP s.1-2). days chronological; each has seq, date, o,h,l,c."""
    out = []
    for i, d in enumerate(days):
        if i < LOOK or d['date'] < FIRST_DAY:
            continue
        p = days[i - 1]
        if p['seq'] != d['seq'] - 1 or (d['date'] - p['date']).days > 4:
            continue
        rng20 = float(np.mean([x['h'].max() - x['l'].min() for x in days[i - LOOK:i]]))
        out.append(dict(d, s=max(S_SHARE * rng20, MIN_S), pdh=float(p['h'].max()), pdl=float(p['l'].min())))
    return out


def net_r(t, cost):
    return (t['gross'] - cost) / t['R_pts']


def stats(day_trades, costs, dates):
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
    out['hit_ref'] = _f(H_REF)
    out['share_time_exit'] = _f(np.mean([t['kind'] == 'time' for t in allt]))
    w = [r for r in rs if r > 0]
    lz = [-r for r in rs if r <= 0]
    out['payoff'] = _f(np.mean(w) / np.mean(lz) if w and lz else None)
    out['long'] = [sum(1 for t in allt if t['dir'] > 0), _f(_mean([net_r(t, s1) for t in allt if t['dir'] > 0]))]
    out['short'] = [sum(1 for t in allt if t['dir'] < 0), _f(_mean([net_r(t, s1) for t in allt if t['dir'] < 0]))]
    out['high_side'] = [sum(1 for t in allt if t['side'] > 0), _f(_mean([net_r(t, s1) for t in allt if t['side'] > 0]))]
    out['low_side'] = [sum(1 for t in allt if t['side'] < 0), _f(_mean([net_r(t, s1) for t in allt if t['side'] < 0]))]
    out['mean_R_pts'] = _f(np.mean([t['R_pts'] for t in allt]))
    q = np.array_split(np.arange(n), 4)
    out['blocks'] = [_f(dsum[ix].sum() / dcnt[ix].sum()) if dcnt[ix].sum() > 0 else None for ix in q]
    out['blocks_pos'] = int(sum(1 for v in out['blocks'] if (v or 0) > 0))
    hold = np.array([dd >= HOLD_FROM for dd in dates])
    out['holdout'] = [int(dcnt[hold].sum()), _f(dsum[hold].sum() / dcnt[hold].sum() if dcnt[hold].sum() > 0 else None)]
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
    sd = dsum.std(ddof=1)
    out['daily_sharpe_ann'] = _f(dsum.mean() / sd * math.sqrt(252) if sd > 0 else None)
    out['vs_prop_threshold_0p025'] = bool(dsum.sum() / nt >= 0.025)
    return out


def verdict(s, plac_pct):
    if s['trades'] < 300:
        return 'INSUFFICIENT-N'
    th = s['S1']['theta']
    if th is None or th <= 0:
        return 'REJECTED'
    if ((s['S1']['ci95'][0] or -1) > 0 and s['blocks_pos'] >= 3 and (s['holdout'][1] or -1) > 0
            and plac_pct is not None and plac_pct >= 0.95):
        return 'VALIDATED (G4)'
    return 'INCONCLUSIVE'


def run_all(days, mode):
    use = prepare(days)
    costs = COST[mode]
    dates = [d['date'] for d in use]
    out = {'mode': mode, 'n_days': len(use)}
    prng = np.random.default_rng(SEED)
    plac_levels = [[placebo_levels(d['o'][0], d['pdh'], d['pdl'], prng) for d in use] for _ in range(N_PLAC)]
    for arm in ('A', 'B'):
        stream, sk_open, sk_r = [], 0, 0
        for d in use:
            tr, a, b = sweep_day(d['o'], d['h'], d['l'], d['c'], {1: d['pdh'], -1: d['pdl']}, d['s'], arm)
            stream.append(tr)
            sk_open += a
            sk_r += b
        st = stats(stream, costs, dates)
        pm = []
        for rep in plac_levels:
            tot = cnt = 0
            for d, lv in zip(use, rep):
                tr, _, _ = sweep_day(d['o'], d['h'], d['l'], d['c'], lv, d['s'], arm)
                tot += sum(net_r(t, costs[1]) for t in tr)
                cnt += len(tr)
            pm.append(tot / cnt if cnt else float('nan'))
        th = st['S1']['theta']
        pv = [x for x in pm if np.isfinite(x)]
        pct = float(np.mean([x < th for x in pv])) if (th is not None and pv) else None
        st['placebo'] = {'means': [_f(x) for x in pm], 'real_percentile': _f(pct)}
        st['skipped_open'], st['skipped_r_floor'] = sk_open, sk_r
        out['arm_' + arm] = st | {'verdict': verdict(st, pct)}
    return out


def log_chunks(algo, tag, obj, size=7000):
    s = json.dumps(obj, separators=(',', ':'))
    parts = [s[i:i + size] for i in range(0, len(s), size)] or ['']
    for i, p in enumerate(parts):
        algo.log(f'{tag} {i + 1}/{len(parts)} {p}')


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaSweep(QCAlgorithm):
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
            self.bars[m] = (float(tb.open), float(tb.high), float(tb.low), float(tb.close))

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
        o, h, l, c = (np.array(x, dtype=np.float64) for x in cols)
        self.days.append({'seq': self.seq, 'date': self.day, 'o': o, 'h': h, 'l': l, 'c': c})

    def on_end_of_algorithm(self):
        self.close_day()
        res = run_all(self.days, MODE)
        res['skipped'] = self.skipped
        res['first_day'] = FIRST_DAY.isoformat()
        res['last_day'] = self.days[-1]['date'].isoformat() if self.days else None
        log_chunks(self, 'NEXA_SWEEP_RESULT', res)
