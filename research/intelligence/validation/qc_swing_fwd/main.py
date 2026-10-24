# NEXA H-SWING-FWD: forward paper test of H-SWING + ES/NQ drift controls. Pre-registration: PREREG_SWING_FWD.md.
# Engine functions copied unchanged from qc_swing/main.py (e8cf492d); new code is in the FORWARD section.
# v2 (DEVIATIONS_SWING_FWD D-1): output logged in chunks (QC truncates a log line at ~8,192 chars); statistics unchanged from v1 be25c85c.
# Reads data only; no orders.
from AlgorithmImports import *
import math
import json
from datetime import date, timedelta
import numpy as np

SEED, B_BOOT, BLOCK = 20261018, 2000, 20
EVAL_FROM = date(2011, 1, 3)
LOOKBACK, WARM_EXTRA, COM = 252, 60, 60
TARGET_VOL, CAP = 0.40, 3.0
COMMISSION_RT = 2.50
TICKS = (1, 2, 4)                                    # S0, S1, S2 ticks per round trip
MARKETS = {
    'ES': ('Indices', 'SP_500_E_MINI', 'equity'), 'NQ': ('Indices', 'NASDAQ_100_E_MINI', 'equity'),
    'YM': ('Indices', 'DOW_30_E_MINI', 'equity'), 'RTY': ('Indices', 'RUSSELL_2000_E_MINI', 'equity'),
    'GC': ('Metals', 'GOLD', 'metals'), 'SI': ('Metals', 'SILVER', 'metals'), 'HG': ('Metals', 'COPPER', 'metals'),
    'CL': ('Energy', 'CRUDE_OIL_WTI', 'energy'), 'NG': ('Energy', 'NATURAL_GAS', 'energy'),
    '6E': ('Currencies', 'EUR', 'fx'), '6J': ('Currencies', 'JPY', 'fx'), '6B': ('Currencies', 'GBP', 'fx'),
    '6A': ('Currencies', 'AUD', 'fx'), '6C': ('Currencies', 'CAD', 'fx'),
    'ZN': ('Financials', 'Y_10_TREASURY_NOTE', 'rates'), 'ZB': ('Financials', 'Y_30_TREASURY_BOND', 'rates'),
    'ZF': ('Financials', 'Y_5_TREASURY_NOTE', 'rates'),
    'ZC': ('Grains', 'CORN', 'grains'), 'ZS': ('Grains', 'SOYBEANS', 'grains'), 'ZW': ('Grains', 'WHEAT', 'grains'),
}
VARIANTS = ('P', 'V-DON', 'V-MA', 'V-IDX', 'LONG')


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
    return round(x, 8) if np.isfinite(x) else None


def boot_mean(x, seed=SEED):
    x = np.asarray(x, float)
    n = len(x)
    if n == 0:
        return {'theta': None, 'ci95': [None, None], 'p_one_sided': None}
    rng = np.random.default_rng(seed)
    reps = np.array([x[block_indices(n, rng)].mean() for _ in range(B_BOOT)])
    return {'theta': _f(x.mean()), 'ci95': [_f(np.percentile(reps, 2.5)), _f(np.percentile(reps, 97.5))],
            'p_one_sided': _f((1 + np.sum(reps <= 0)) / (B_BOOT + 1))}


# ---------------------------------------------------------------- engine (pure functions, unit-tested locally)
def ewma_vol(c):
    """Annualised EWMA vol (centre of mass COM) of daily simple returns, data <= t. Array aligned to c (nan before 2 bars)."""
    c = np.asarray(c, float)
    n = len(c)
    out = np.full(n, np.nan)
    d = COM / (COM + 1.0)
    var = None
    for t in range(1, n):
        r = c[t] / c[t - 1] - 1.0
        var = r * r if var is None else d * var + (1 - d) * r * r
        out[t] = math.sqrt(252.0 * var)
    return out


def month_end_flags(dates):
    return np.array([i == len(dates) - 1 or dates[i + 1].month != dates[i].month for i in range(len(dates))])


def size(sig):
    return min(CAP, TARGET_VOL / sig) if (sig is not None and np.isfinite(sig) and sig > 0) else 0.0


def decisions(dates, h, l, c, variant):
    """Decided weight at each close t (nan = not yet valid / no decision change semantics: carries forward)."""
    n = len(c)
    c = np.asarray(c, float)
    vol = ewma_vol(c)
    me = month_end_flags(dates)
    w = np.full(n, np.nan)
    warm = LOOKBACK + WARM_EXTRA
    cur, mag, state = np.nan, None, 0
    for t in range(n):
        if t + 1 < warm:
            continue
        if me[t] or mag is None:
            mag = size(vol[t])
        if variant in ('P', 'V-IDX'):
            if me[t] or np.isnan(cur):
                lr = math.log(c[t]) - math.log(c[t - LOOKBACK])
                cur = float(np.sign(lr)) * size(vol[t])
        elif variant == 'LONG':
            if me[t] or np.isnan(cur):
                cur = size(vol[t])
        elif variant == 'V-MA':
            s = float(np.sign(np.mean(c[t - 49:t + 1]) - np.mean(c[t - 199:t + 1])))
            cur = s * mag
        elif variant == 'V-DON':
            hh55, ll55 = max(h[t - 55:t]), min(l[t - 55:t])
            hh20, ll20 = max(h[t - 20:t]), min(l[t - 20:t])
            if state == 0:
                if c[t] > hh55:
                    state = 1
                    mag = size(vol[t])
                elif c[t] < ll55:
                    state = -1
                    mag = size(vol[t])
            elif state == 1 and c[t] < ll20:
                state = 0
            elif state == -1 and c[t] > hh20:
                state = 0
            cur = state * mag
        w[t] = cur
    return w


def market_pnl(dates, c, rolls, w_dec, cost_pts):
    """Per-day net contribution of one market (before averaging). Returns dict date -> (gross, cost[3], active, abs_dw, roll_cost[3]).
    Decision at close t is executed at close t+1 (cost priced at C_{t+1}) and first earns r_{t+2} (DEVIATIONS_SWING C-1)."""
    n = len(c)
    out = {}
    for t in range(2, n):
        if np.isnan(w_dec[t - 2]) and np.isnan(w_dec[t - 1]):
            continue
        r = c[t] / c[t - 1] - 1.0
        prev_exec = 0.0 if np.isnan(w_dec[t - 2]) else w_dec[t - 2]   # executed at close t-1, held over day t
        gross = prev_exec * r
        # trade executed at close t: w_dec[t-1] replaces w_dec[t-2]
        new = w_dec[t - 1]
        dw = abs((0.0 if np.isnan(new) else new) - prev_exec)
        costs = [dw * (cp / 2.0) / c[t] for cp in cost_pts]
        rc = [abs(prev_exec) * cp / c[t] if rolls[t] else 0.0 for cp in cost_pts]
        out[dates[t]] = (gross, [a + b for a, b in zip(costs, rc)], dw, rc)
    return out


def portfolio(mkt_pnls, sectors, eval_from=EVAL_FROM):
    """mkt_pnls: name -> dict(date -> tuple). Returns chronological dates, R[3] arrays, per-sector sums, extras."""
    days = sorted({d for p in mkt_pnls.values() for d in p if d >= eval_from})
    R = np.zeros((3, len(days)))
    G = np.zeros(len(days))
    sec = {}
    dw_tot, roll_tot, cost_tot = 0.0, 0.0, 0.0
    for i, d in enumerate(days):
        act = [(k, p[d]) for k, p in mkt_pnls.items() if d in p]
        if not act:
            continue
        nact = len(act)
        for k, (g, cs, dw, rc) in act:
            for s in range(3):
                R[s, i] += (g - cs[s]) / nact
            G[i] += g / nact
            sec[sectors[k]] = sec.get(sectors[k], 0.0) + (g - cs[1]) / nact
            dw_tot += dw / nact
            roll_tot += rc[1] / nact
            cost_tot += cs[1] / nact
    return days, R, G, sec, {'turnover_per_year': dw_tot / max(len(days) / 252.0, 1e-9),
                             'roll_cost_share': roll_tot / cost_tot if cost_tot > 0 else None,
                             'cost_per_year': cost_tot / max(len(days) / 252.0, 1e-9)}


def series_stats(days, x):
    x = np.asarray(x, float)
    out = {'n_days': len(x), 'S1': boot_mean(x)}
    if len(x) == 0:
        return out
    sd = x.std(ddof=1)
    out['ann_return'] = _f(x.mean() * 252)
    out['ann_vol'] = _f(sd * math.sqrt(252))
    out['sharpe_ann'] = _f(x.mean() / sd * math.sqrt(252) if sd > 0 else None)
    out['skew'] = _f(((x - x.mean()) ** 3).mean() / sd ** 3 if sd > 0 else None)
    q = np.array_split(np.arange(len(x)), 4)
    out['blocks'] = [_f(x[ix].mean()) for ix in q]
    out['blocks_pos'] = int(sum(1 for ix in q if x[ix].mean() > 0))
    eq = np.cumsum(x)
    out['max_dd'] = _f(np.max(np.maximum.accumulate(np.concatenate([[0.0], eq])) - np.concatenate([[0.0], eq])))
    out['pos_day_share'] = _f(np.mean(x > 0))
    months = {}
    for d, v in zip(days, x):
        months.setdefault((d.year, d.month), 0.0)
        months[(d.year, d.month)] += v
    mv = np.array([months[k] for k in sorted(months)])
    out['n_months'] = len(mv)
    out['pos_month_share'] = _f(np.mean(mv > 0))
    run = best = 0
    for v in mv:
        run = run + 1 if v < 0 else 0
        best = max(best, run)
    out['longest_losing_month_streak'] = best
    years = {}
    for d, v in zip(days, x):
        years[d.year] = years.get(d.year, 0.0) + v
    out['per_year'] = {str(k): _f(v) for k, v in sorted(years.items())}
    no22 = np.array([v for d, v in zip(days, x) if d.year != 2022])
    out['mean_ex_2022'] = _f(no22.mean() if len(no22) else None)
    return out


def verdict(s):
    if s.get('n_months', 0) < 36:
        return 'INSUFFICIENT-N'
    th = s['S1']['theta']
    if th is None or th <= 0:
        return 'REJECTED'
    if (s['S1']['ci95'][0] or -1) > 0 and s['blocks_pos'] >= 3:
        return 'VALIDATED (G4)'
    return 'INCONCLUSIVE'


def run_all(data, props):
    """data: name -> dict(dates, o, h, l, c, rolls); props: name -> (tick, multiplier). Returns result dict."""
    sectors = {k: MARKETS[k][2] for k in MARKETS}
    res = {'markets': {}}
    pnl = {v: {} for v in VARIANTS}
    for k, d in data.items():
        if len(d['c']) < LOOKBACK + WARM_EXTRA + 3:
            res['markets'][k] = {'bars': len(d['c']), 'used': False}
            continue
        tick, mult = props[k]
        cpts = [kk * tick + COMMISSION_RT / mult for kk in TICKS]
        vol = ewma_vol(d['c'])
        res['markets'][k] = {'bars': len(d['c']), 'used': True, 'first': d['dates'][0].isoformat(),
                             'last_close': _f(d['c'][-1]), 'last_vol': _f(vol[-1]), 'tick': tick, 'mult': mult,
                             'rolls': int(sum(d['rolls']))}
        for v in VARIANTS:
            if v == 'V-IDX' and k not in ('ES', 'NQ'):
                continue
            w = decisions(d['dates'], d['h'], d['l'], d['c'], v)
            pnl[v][k] = market_pnl(d['dates'], d['c'], d['rolls'], w, cpts)
    series = {}
    for v in VARIANTS:
        days, R, G, sec, extra = portfolio(pnl[v], sectors)
        st = series_stats(days, R[1])
        st['S0_mean'] = _f(R[0].mean() if R.shape[1] else None)
        st['S2_mean'] = _f(R[2].mean() if R.shape[1] else None)
        st['gross_mean'] = _f(G.mean() if len(G) else None)
        st['by_sector'] = {s: _f(x) for s, x in sorted(sec.items())}
        st.update({k2: _f(v2) for k2, v2 in extra.items()})
        st['verdict'] = verdict(st)
        res[v] = st
        series[v] = dict(zip(days, R[1]))
    common = sorted(set(series['P']) & set(series['LONG']))
    diff = [series['P'][d] - series['LONG'][d] for d in common]
    res['P_minus_LONG'] = boot_mean(diff)
    res['first_eval_day'] = EVAL_FROM.isoformat()
    return res


# ---------------------------------------------------------------- FORWARD (PREREG_SWING_FWD.md)
HIST_END = date(2026, 7, 21)
FWD_START = date(2026, 7, 22)
FWD_END = date(2027, 12, 31)
WINDOWS = {'HIST': (EVAL_FROM, HIST_END), 'FWD': (FWD_START, FWD_END), 'POOLED': (EVAL_FROM, FWD_END)}
FWD_VARIANTS = ('P', 'V-IDX', 'LONG', 'LONG-IDX', 'BH-IDX')
IDX = ('ES', 'NQ')
REF = {'P': 0.00021849, 'V-IDX': 0.00075084, 'P_minus_LONG': 8.589e-05}   # H-SWING log, 8-decimal rounding
MIN_FWD_DAYS = 250
CONTROLS = (('V-IDX', 'LONG-IDX'), ('V-IDX', 'BH-IDX'), ('P', 'LONG'))


def decisions_fwd(dates, h, l, c, variant):
    """LONG-IDX = LONG sizing; BH-IDX = constant +1 notional from the same first valid day; others = H-SWING decisions."""
    if variant == 'LONG-IDX':
        return decisions(dates, h, l, c, 'LONG')
    if variant == 'BH-IDX':
        w = decisions(dates, h, l, c, 'LONG')
        return np.where(np.isnan(w), np.nan, 1.0)
    return decisions(dates, h, l, c, variant)


def windowed(days, x, lo, hi):
    ix = [i for i, d in enumerate(days) if lo <= d <= hi]
    return [days[i] for i in ix], np.asarray([x[i] for i in ix], float)


def window_stats(days, x):
    if len(x) < 2:
        return {'n_days': len(x)}
    st = series_stats(days, x)
    st['verdict'] = verdict(st)
    return st


def diff_stats(sa, sb, lo, hi):
    common = sorted(d for d in set(sa) & set(sb) if lo <= d <= hi)
    out = boot_mean([sa[d] - sb[d] for d in common])
    out['n_days'] = len(common)
    return out


def control_verdict(c):
    th, lo = c.get('theta'), (c.get('ci95') or [None])[0]
    if th is None:
        return None
    if th <= 0:
        return 'DRIFT ONLY'
    if lo is not None and lo > 0:
        return 'TIMING VALUE'
    return 'UNRESOLVED'


def fwd_verdict(r, mu_hist):
    f, p = r.get('FWD', {}), r.get('POOLED', {})
    if f.get('n_days', 0) < MIN_FWD_DAYS:
        return 'INSUFFICIENT-N'
    if p['S1']['theta'] <= 0 or f['S1']['ci95'][1] < mu_hist:
        return 'FAILED'
    if f['S1']['theta'] > 0 and verdict(p) == 'VALIDATED (G4)':
        return 'CONFIRMED'
    return 'INCONCLUSIVE'


def run_fwd(data, props):
    sectors = {k: MARKETS[k][2] for k in MARKETS}
    pnl = {v: {} for v in FWD_VARIANTS}
    ends = []
    for k, d in data.items():
        if d['dates']:
            ends.append(d['dates'][-1])
        if len(d['c']) < LOOKBACK + WARM_EXTRA + 3:
            continue
        tick, mult = props[k]
        cpts = [kk * tick + COMMISSION_RT / mult for kk in TICKS]
        for v in FWD_VARIANTS:
            if v in ('V-IDX', 'LONG-IDX', 'BH-IDX') and k not in IDX:
                continue
            w = decisions_fwd(d['dates'], d['h'], d['l'], d['c'], v)
            pnl[v][k] = market_pnl(d['dates'], d['c'], d['rolls'], w, cpts)
    data_end = max(ends) if ends else None
    res = {'data_end': data_end.isoformat() if data_end else None,
           'binding': bool(data_end and data_end >= FWD_END),
           'windows': {k: [a.isoformat(), b.isoformat()] for k, (a, b) in WINDOWS.items()}}
    series = {}
    for v in FWD_VARIANTS:
        days, R, G, sec, extra = portfolio(pnl[v], sectors)
        series[v] = dict(zip(days, R[1]))
        res[v] = {}
        for wn, (lo, hi) in WINDOWS.items():
            dd, x = windowed(days, R[1], lo, hi)
            res[v][wn] = window_stats(dd, x)
            if len(x):
                _, x0 = windowed(days, R[0], lo, hi)
                _, x2 = windowed(days, R[2], lo, hi)
                res[v][wn]['S0_mean'] = _f(x0.mean())
                res[v][wn]['S2_mean'] = _f(x2.mean())
    res['controls'] = {}
    for a, b in CONTROLS:
        for wn, (lo, hi) in WINDOWS.items():
            res['controls'][a + '_minus_' + b + '_' + wn] = diff_stats(series[a], series[b], lo, hi)
    res['A1_verdict'] = control_verdict(res['controls']['V-IDX_minus_LONG-IDX_HIST'])
    g0 = {}
    for v in ('P', 'V-IDX'):
        th = res[v]['HIST'].get('S1', {}).get('theta')
        g0[v] = {'hist_theta': th, 'ref': REF[v], 'match': th is not None and abs(th - REF[v]) < 5e-9}
    th = res['controls']['P_minus_LONG_HIST'].get('theta')
    g0['P_minus_LONG'] = {'hist_theta': th, 'ref': REF['P_minus_LONG'], 'match': th is not None and abs(th - REF['P_minus_LONG']) < 5e-9}
    res['A0'] = g0
    res['fwd_verdict'] = {}
    for v in ('P', 'V-IDX'):
        mu = res[v]['HIST'].get('S1', {}).get('theta')
        res['fwd_verdict'][v] = fwd_verdict(res[v], mu) if mu is not None else None
    return res


LOG_CHUNK = 7000


def log_chunks(text, size=LOG_CHUNK):
    """Split text into numbered chunks that each fit one QC log line: [(i, n, chunk)], 1-based."""
    parts = [text[i:i + size] for i in range(0, len(text), size)] or ['']
    return [(i + 1, len(parts), p) for i, p in enumerate(parts)]


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaSwing(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2009, 1, 1)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        self.syms, self.data = {}, {}
        for k, (grp, attr, _) in MARKETS.items():
            tk = getattr(getattr(Futures, grp), attr)
            f = self.add_future(tk, Resolution.DAILY, fill_forward=False, extended_market_hours=False,
                                data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
                                data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
            self.syms[f.symbol] = k
            self.data[k] = {'dates': [], 'o': [], 'h': [], 'l': [], 'c': [], 'rolls': []}
        self.pending_roll = set()

    def on_data(self, data):
        for sym, _ in data.symbol_changed_events.items():
            if sym in self.syms:
                self.pending_roll.add(self.syms[sym])
        for sym, k in self.syms.items():
            tb = data.bars.get(sym)
            if tb is None:
                continue
            d = (tb.end_time - timedelta(seconds=1)).date()
            rec = self.data[k]
            if rec['dates'] and d <= rec['dates'][-1]:
                continue
            rec['dates'].append(d)
            rec['o'].append(float(tb.open))
            rec['h'].append(float(tb.high))
            rec['l'].append(float(tb.low))
            rec['c'].append(float(tb.close))
            rec['rolls'].append(k in self.pending_roll)
            self.pending_roll.discard(k)

    def on_end_of_algorithm(self):
        props = {}
        for sym, k in self.syms.items():
            sp = self.securities[sym].symbol_properties
            props[k] = (float(sp.minimum_price_variation), float(sp.contract_multiplier))
        res = run_fwd(self.data, props)
        for i, n, part in log_chunks(json.dumps(res, separators=(',', ':'))):
            self.log('NEXA_SWING_FWD_PART %d/%d %s' % (i, n, part))
