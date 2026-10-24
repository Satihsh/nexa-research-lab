# NEXA H-ORB30L-REPL Part A: QuantConnect out-of-sample replication of the FROZEN H-ORB30L-NQ rule.
# Pre-registration: PREREG_HORB30L_REPL.md (758f8a31) + DEVIATIONS_HORB30L_REPL.md. Engine = line-for-line port of
# horb30l_nq.py (7d4095bc) setup/run_trade/simulate; statistics = verbatim port of of_common.block_indices /
# bootstrap / boot_summary. No orders are placed; the algorithm only reads NQ minute bars and logs results.
from AlgorithmImports import *
import math
import json
import hashlib
import numpy as np

MODE = 'SMOKE'            # 'SMOKE' = 2023-03-01..07 (in-sample parity check), 'OOS' = first data .. 2023-02-17
TICK = 0.25
MIN_R = 10.0
RS, RL = 570, 30          # 09:30, 30 minutes
DEADLINE = 690            # breakout candle closes by 11:30
EXIT_MIN = 929            # time exit = close of the 15:29 bar
COST = {'S0': 1.0, 'S1': 2.0, 'S2': 3.0}
SEED, B_BOOT, BLOCK = 20261015, 2000, 20


# ---------------------------------------------------------------- frozen engine (port of horb30l_nq.py)
def setup(bars, t0=RS, deadline=DEADLINE, tf=5):
    for j in range(RL):
        if t0 + j not in bars:
            return 'missing', None
    A = max(bars[t0 + j][1] for j in range(RL))
    B = min(bars[t0 + j][2] for j in range(RL))
    m = t0 + RL
    while m + tf <= deadline:
        b = bars.get(m + tf - 1)
        if b is not None and b[3] > A:
            return 'ok', (A, B, m + tf)
        m += tf
    return 'no_breakout', (A, B, None)


def run_trade(bars, entry_min, exit_min, dirn, stop, target_r=1.0):
    em = None
    for m in range(entry_min, exit_min):
        if m in bars:
            em = m
            break
    if em is None:
        return {'s': 'no_entry_bar'}
    entry = bars[em][0]
    R = (entry - stop) * dirn
    if R <= 0:
        return {'s': 'invalid'}
    if R < MIN_R:
        return {'s': 'cost_floor'}
    tgt = entry + dirn * target_r * R
    for m in range(em, exit_min + 1):
        b = bars.get(m)
        if b is None:
            continue
        o, h, l, c = b
        first = m == em
        px = how = None
        if (l <= stop) if dirn == 1 else (h >= stop):
            gap = (not first) and ((o <= stop) if dirn == 1 else (o >= stop))
            px, how = (o if gap else stop), 'stop'
        elif (not first) and ((h >= tgt + TICK) if dirn == 1 else (l <= tgt - TICK)):
            px, how = tgt, 'target'
        elif m == exit_min:
            px, how = c, 'time'
        if px is not None:
            return {'s': 'trade', 'g': (px - entry) * dirn, 'R': R, 'x': how, 'em': em}
    return {'s': 'missing'}


def simulate(bars, target_r=1.0, n2=False):
    if EXIT_MIN not in bars:
        return {'s': 'missing'}
    st, info = setup(bars)
    if st == 'missing':
        return {'s': 'missing'}
    A, B, em = info
    if n2:
        return run_trade(bars, RS + RL, EXIT_MIN, 1, B, target_r)
    if st != 'ok':
        return {'s': st}
    return run_trade(bars, em, EXIT_MIN, 1, B, target_r)


# ---------------------------------------------------------------- statistics (verbatim port of of_common)
def block_indices(n, rng, L=BLOCK):
    if n <= L:
        return rng.integers(0, n, n)
    nb = int(math.ceil(n / L))
    st = rng.integers(0, n - L + 1, nb)
    return (st[:, None] + np.arange(L)[None, :]).ravel()[:n]


def bootstrap(stat, n, B=B_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    out = np.empty(B)
    for b in range(B):
        out[b] = stat(block_indices(n, rng))
    return out


def _f(x):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, 6) if np.isfinite(x) else None


def boot_summary(theta, reps):
    r = reps[np.isfinite(reps)]
    if len(r) == 0 or not np.isfinite(theta):
        return {'theta': _f(theta), 'ci95': [None, None], 'p_one_sided': None, 'B_finite': int(len(r))}
    return {'theta': _f(theta), 'ci95': [_f(np.percentile(r, 2.5)), _f(np.percentile(r, 97.5))],
            'p_one_sided': _f((1 + np.sum(r <= 0)) / (len(r) + 1)), 'B_finite': int(len(r))}


def boot(x):
    v = np.asarray(x, float)
    if len(v) < 2:
        return {'theta': _f(v.mean()) if len(v) else None, 'n': int(len(v))}
    reps = bootstrap(lambda idx: float(v[idx].mean()), len(v))
    return boot_summary(float(v.mean()), reps) | {'n': int(len(v))}


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaHorb30lOos(QCAlgorithm):
    def initialize(self):
        if MODE == 'SMOKE':
            self.set_start_date(2023, 3, 1)
            self.set_end_date(2023, 3, 7)
        else:
            self.set_start_date(2009, 1, 1)
            self.set_end_date(2023, 2, 17)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        f = self.add_future(Futures.Indices.NASDAQ_100_E_MINI, Resolution.MINUTE, fill_forward=False,
                            extended_market_hours=True, data_normalization_mode=DataNormalizationMode.RAW,
                            data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
        self.sym = f.symbol
        self.day = None
        self.bars = {}
        self.rows = []

    def on_data(self, data):
        bar = data.bars.get(self.sym)
        if bar is None:
            return
        t = self.time - timedelta(minutes=1)          # bar start, America/New_York
        d = t.date()
        if self.day is not None and d != self.day:
            self.close_day()
        self.day = d
        m = t.hour * 60 + t.minute
        if RS <= m <= 959:
            self.bars[m] = (float(bar.open), float(bar.high), float(bar.low), float(bar.close))

    def close_day(self):
        if self.bars and self.day is not None and self.day.weekday() < 5:
            self.rows.append((self.day, simulate(self.bars, 1.0), simulate(self.bars, 2.0),
                              simulate(self.bars, 1.0, n2=True)))
        self.bars = {}

    def on_end_of_algorithm(self):
        self.close_day()
        if MODE == 'SMOKE':
            for d, r1, r2, n2 in self.rows:
                self.log('SMOKE ' + d.isoformat() + ' ' + json.dumps(r1, separators=(',', ':')))
            return
        out = {'mode': MODE, 'days': len(self.rows),
               'first_day': self.rows[0][0].isoformat() if self.rows else None,
               'last_day': self.rows[-1][0].isoformat() if self.rows else None}
        counts = {}
        for _, r1, _, _ in self.rows:
            counts[r1['s']] = counts.get(r1['s'], 0) + 1
        out['counts'] = counts
        tr = [(d, r1) for d, r1, _, _ in self.rows if r1['s'] == 'trade']
        for lvl, c in COST.items():
            out[lvl] = boot([(r['g'] - c) / r['R'] for _, r in tr])
        s1 = np.array([(r['g'] - COST['S1']) / r['R'] for _, r in tr])
        out['S1_mean_pts'] = _f(np.mean([r['g'] - COST['S1'] for _, r in tr])) if tr else None
        out['S1_win_rate'] = _f(np.mean(s1 > 0)) if len(s1) else None
        out['exits'] = {k: sum(1 for _, r in tr if r['x'] == k) for k in ('stop', 'target', 'time')}
        out['median_R_pts'] = _f(np.median([r['R'] for _, r in tr])) if tr else None
        r2 = [(r['g'] - COST['S1']) / r['R'] for _, _, r, _ in self.rows if r['s'] == 'trade']
        out['secondary_2R_S1'] = boot(r2)
        n2 = [(r['g'] - COST['S1']) / r['R'] for _, _, _, r in self.rows if r['s'] == 'trade']
        out['N2_beta_S1'] = boot(n2)
        out['primary_minus_N2'] = _f(float(np.mean(s1)) - float(np.mean(n2))) if len(s1) and n2 else None
        years = {}
        for (d, _), x in zip(tr, s1):
            years[d.year] = years.get(d.year, 0.0) + float(x)
        tot = sum(years.values())
        out['years_sumR'] = {str(k): _f(v) for k, v in sorted(years.items())}
        out['max_year_share'] = _f(max(years.values()) / tot) if years and tot > 0 else None
        out['share_years_positive'] = _f(np.mean([v > 0 for v in years.values()])) if years else None
        floor_by_year = {}
        for d, r1, _, _ in self.rows:
            if r1['s'] == 'cost_floor':
                floor_by_year[str(d.year)] = floor_by_year.get(str(d.year), 0) + 1
        out['cost_floor_by_year'] = floor_by_year
        usd, months = [], {}
        for d, r in tr:
            k = max(1, math.floor(100.0 / (r['R'] * 2.0)))
            v = k * (r['g'] - COST['S1']) * 2.0
            usd.append(v)
            months[d.strftime('%Y-%m')] = months.get(d.strftime('%Y-%m'), 0.0) + v
        mv = list(months.values())
        out['user_goal_mnq'] = {'usd_per_trade_mean': _f(np.mean(usd)) if usd else None,
                                'usd_per_month_mean': _f(np.mean(mv)) if mv else None,
                                'usd_per_month_median': _f(np.median(mv)) if mv else None,
                                'share_months_positive': _f(np.mean([x > 0 for x in mv])) if mv else None,
                                'worst_month': _f(min(mv)) if mv else None, 'n_months': len(mv)}
        m1 = out['S1']
        checks = {
            '1_mean>0_ci_lo>0': bool((m1.get('theta') or 0) > 0 and (m1.get('ci95') or [None])[0] is not None
                                     and m1['ci95'][0] > 0),
            '2_primary_minus_N2>0': bool((out['primary_minus_N2'] or 0) > 0),
            '3_years_pos>=60%_and_no_year>25%': bool((out['share_years_positive'] or 0) >= 0.60 and
                                                     out['max_year_share'] is not None and out['max_year_share'] <= 0.25),
        }
        n = counts.get('trade', 0)
        if n < 300:
            verdict = 'INSUFFICIENT-N'
        elif (m1.get('theta') or 0) <= 0:
            verdict = 'FAILED'
        elif all(checks.values()):
            verdict = 'REPLICATED'
        else:
            verdict = 'NOT REPLICATED'
        out['checks'] = checks
        out['verdict'] = verdict
        out['trades_sha256'] = hashlib.sha256(','.join(f'{d.isoformat()}:{x:.6f}' for (d, _), x in zip(tr, s1))
                                              .encode()).hexdigest()
        self.log('NEXA_RESULT ' + json.dumps(out, separators=(',', ':')))
