#!/usr/bin/env python3
"""Shared implementation of PREREG_OF_COMMON.md (OF-16 / OF-19 / OF-20).

Research only. Reads Pepperstone M1 canonical files already on disk; writes nothing outside
research/intelligence/validation/ (and a parse cache in the session scratchpad).
Section references (§Cn) point to PREREG_OF_COMMON.md.
"""
from __future__ import annotations

import math
import os
import pickle
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
M1 = '~/NEXA-Agent-Lab/filesnexa/NEXA/data/pepperstone/m1_canonical/PEPPERSTONE_{}_M1_canonical.csv.gz'
CACHE = os.environ.get('OF_CACHE', '/private/tmp/claude-501/-Users-<user>-NEXA-Agent-Lab/'
                       'b7761295-0bbc-412a-840f-c599b9bfa132/scratchpad/of_cache')   # parse cache only

SYMBOLS = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY']
FIRST_DAY = {'EURUSD': '2017-07-03', 'GBPUSD': '2017-07-03', 'USDJPY': '2017-07-03', 'XAUUSD': '2018-01-02'}   # §C2
LAST_DAY = '2026-09-25'
POINT = {'EURUSD': 1e-5, 'GBPUSD': 1e-5, 'USDJPY': 1e-3, 'XAUUSD': 1e-2}                                 # §C2
BINW = {'XAUUSD': 1.0, 'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDJPY': 0.01}                                # §C6
PROFILE_PROXY_VALID = {'XAUUSD': True, 'EURUSD': True, 'GBPUSD': False, 'USDJPY': True}                   # T1
SPLITS = [('discovery', None, '2022-12-31'), ('validation', '2023-01-01', '2024-12-31'),
          ('holdout', '2025-01-01', LAST_DAY)]                                                              # §C8
SPLIT_NAMES = [s[0] for s in SPLITS]
SEED = 20261011
B_BOOT = 2000
BLOCK = 20

NY = ZoneInfo('America/New_York')
LDN = ZoneInfo('Europe/London')
UTC = ZoneInfo('UTC')

# §C3 anchors: primary / secondary per symbol. Values: ('A1', None) = 08:00 London; ('A2', (h, m)) = h:m New York
A2_TIME = {'XAUUSD': (8, 20), 'EURUSD': (8, 30), 'GBPUSD': (8, 30), 'USDJPY': (8, 30)}
PRIMARY_ANCHOR = {'XAUUSD': 'A2', 'EURUSD': 'A1', 'GBPUSD': 'A1', 'USDJPY': 'A1'}


def secondary_anchor(sym: str) -> str:
    return 'A1' if PRIMARY_ANCHOR[sym] == 'A2' else 'A2'


# ----------------------------------------------------------------------------- clocks (§C3)
def server_minute_of_local(d: date, hh: int, mm: int, tz: ZoneInfo) -> int:
    """Minute of server day d (0 = server midnight = 17:00 NY of d-1) at local time hh:mm on calendar date d in tz."""
    loc = datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz)
    ny_local = loc.astimezone(NY).replace(tzinfo=None)
    server = ny_local + timedelta(hours=7)              # server = NY local + 7 h, exactly
    base = datetime(d.year, d.month, d.day)
    return int((server - base).total_seconds() // 60)


def anchor_smin(sym: str, anchor: str, d: date) -> int:
    if anchor == 'A1':
        return server_minute_of_local(d, 8, 0, LDN)
    h, m = A2_TIME[sym]
    return server_minute_of_local(d, h, m, NY)


def split_of(day_str: str) -> int:
    if day_str <= '2022-12-31':
        return 0
    if day_str <= '2024-12-31':
        return 1
    return 2


# ----------------------------------------------------------------------------- data (§C2, §C4)
@dataclass
class Sym:
    sym: str
    smin: np.ndarray      # minute of server day per bar
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    tv: np.ndarray
    spr: np.ndarray       # spread in price units
    days: list            # 'YYYY-MM-DD' per server day (all weekdays present, incl. thin)
    start: np.ndarray     # bar slice start per day
    end: np.ndarray       # bar slice end (exclusive)
    valid: np.ndarray     # §C4 valid server day
    C: np.ndarray         # last close per day
    sig: np.ndarray       # §C5 sigma-hat for day d (needs d-1 valid); nan if undefined
    sprd: np.ndarray      # §C7 spread cost s_d (price units); nan if undefined
    split: np.ndarray     # 0/1/2 per day
    audit: dict

    def bars(self, i: int) -> slice:
        return slice(int(self.start[i]), int(self.end[i]))


def _parse(sym: str) -> dict:
    d = pd.read_csv(M1.format(sym), usecols=['time_server', 'open', 'high', 'low', 'close', 'tick_volume', 'spread',
                                             'time_status', 'time_utc'], dtype={'time_status': str, 'time_utc': str})
    audit = {'rows_raw': int(len(d))}
    ok = d.time_status == 'OK'
    audit['rows_status_not_ok'] = int((~ok).sum())
    d = d[ok]
    n0 = len(d)
    d = d.drop_duplicates('time_server', keep='first')
    audit['rows_duplicate_time_server'] = int(n0 - len(d))
    ts = pd.to_datetime(d.time_server, format='%Y-%m-%d %H:%M:%S')
    d = d.assign(ts=ts.values).sort_values('ts')
    ts = pd.DatetimeIndex(d.ts)
    # clock check vs file time_utc where present (§C3)
    ny = ts - pd.Timedelta(hours=7)
    utc_calc = ny.tz_localize('America/New_York', ambiguous='NaT', nonexistent='NaT').tz_convert('UTC')
    has = d.time_utc.notna().to_numpy() & (d.time_utc.astype(str).str.len() > 5).to_numpy()
    fu = pd.to_datetime(d.time_utc[has], utc=True, format='ISO8601')
    a = utc_calc[has].as_unit('ns').asi8
    b = pd.DatetimeIndex(fu).as_unit('ns').asi8
    mism = a != b
    audit['utc_check_rows'] = int(has.sum())
    audit['utc_mismatch_rows'] = int(mism.sum())
    audit['utc_mismatch_rate'] = float(mism.mean()) if has.sum() else None
    audit['utc_nat_rows'] = int(pd.isna(utc_calc).sum())
    sday = ts.normalize()
    wd = sday.dayofweek
    wk = wd < 5
    audit['rows_weekend_server_day'] = int((~wk).sum())
    d = d[wk]; ts = ts[wk]; sday = sday[wk]
    smin = ((ts - sday) // pd.Timedelta(minutes=1)).astype(np.int64)
    return {'ts_day': sday.strftime('%Y-%m-%d').to_numpy(), 'smin': np.asarray(smin),
            'o': d.open.to_numpy(float), 'h': d.high.to_numpy(float), 'l': d.low.to_numpy(float),
            'c': d.close.to_numpy(float), 'tv': d.tick_volume.to_numpy(float),
            'spr': d.spread.to_numpy(float) * POINT[sym], 'audit': audit}


def load(sym: str) -> Sym:
    os.makedirs(CACHE, exist_ok=True)
    cp = os.path.join(CACHE, f'{sym}.pkl')
    if os.path.exists(cp):
        with open(cp, 'rb') as f:
            raw = pickle.load(f)
    else:
        raw = _parse(sym)
        with open(cp, 'wb') as f:
            pickle.dump(raw, f)
    audit = dict(raw['audit'])
    # keep 45 calendar days of warm-up before FIRST_DAY for sigma/spread (not evaluated)
    warm = (raw['ts_day'] >= (pd.Timestamp(FIRST_DAY[sym]) - pd.Timedelta(days=45)).strftime('%Y-%m-%d')) & (raw['ts_day'] <= LAST_DAY)
    idx = np.where(warm)[0]
    tday = raw['ts_day'][idx]
    smin, o, h, l, c, tv, spr = (raw[k][idx] for k in ('smin', 'o', 'h', 'l', 'c', 'tv', 'spr'))
    days, start = np.unique(tday, return_index=True)
    end = np.r_[start[1:], len(tday)]
    nb = end - start
    med = float(np.median(nb[(days >= FIRST_DAY[sym])]))
    thin = nb < 0.8 * med
    fin = np.array([np.isfinite(o[s:e]).all() and np.isfinite(h[s:e]).all() and np.isfinite(l[s:e]).all()
                    and np.isfinite(c[s:e]).all() and (h[s:e] >= l[s:e]).all() for s, e in zip(start, end)])
    valid = ~thin & fin
    C = c[end - 1]
    n = len(days)
    sig = np.full(n, np.nan)
    sprd = np.full(n, np.nan)
    p90 = np.array([np.percentile(spr[s:e], 90) for s, e in zip(start, end)])
    vidx = np.where(valid)[0]
    lr = np.full(len(vidx), np.nan)
    lr[1:] = np.diff(np.log(C[vidx]))
    pos_of = {int(v): k for k, v in enumerate(vidx)}
    for i in range(1, n):
        if not valid[i - 1]:
            continue                                     # §C5 needs d-1 valid
        k = pos_of[i - 1]
        if k >= 20:
            r = lr[k - 19:k + 1]
            if np.isfinite(r).all():
                sig[i] = C[i - 1] * float(np.std(r, ddof=1))
        if k >= 19:
            sprd[i] = float(np.median(p90[vidx[k - 19:k + 1]]))
    split = np.array([split_of(x) for x in days])
    evalmask = days >= FIRST_DAY[sym]
    audit.update({'server_days': int(evalmask.sum()), 'thin_days': int((thin & evalmask).sum()),
                  'nonfinite_or_bad_hl_days': int((~fin & evalmask).sum()), 'median_bars': med})
    return Sym(sym, smin, o, h, l, c, tv, spr, list(days), start, end, valid,
               C, sig, sprd, split, audit | {'first_eval_day': FIRST_DAY[sym], 'evalmask_start': int(np.argmax(evalmask))})


def is_eval_day(S: Sym, i: int) -> bool:
    return S.days[i] >= FIRST_DAY[S.sym]


def prev_ok(S: Sym, i: int) -> bool:
    """d-1 is the previous weekday server day present (index i-1); both must be valid (§C4)."""
    return i >= 1 and bool(S.valid[i]) and bool(S.valid[i - 1])


def weekday(day: str) -> int:
    return date.fromisoformat(day).weekday()


# ----------------------------------------------------------------------------- sessions (§C3)
def session(S: Sym, i: int, anchor_min: int):
    """Return (slice indices array of bars in [a, E), anchor bar index or None)."""
    sl = S.bars(i)
    sm = S.smin[sl]
    k0 = int(np.searchsorted(sm, anchor_min, side='left'))
    if k0 >= len(sm) or sm[k0] >= anchor_min + 5:
        return None, None
    return np.arange(sl.start + k0, sl.stop), sl.start + k0


def ib_window(S: Sym, idx: np.ndarray, anchor_min: int):
    sm = S.smin[idx]
    m = sm < anchor_min + 60
    if m.sum() < 54:
        return None
    ii = idx[m]
    return float(S.h[ii].max()), float(S.l[ii].min()), int(m.sum())


# ----------------------------------------------------------------------------- profile (§C6)
def va_greedy(v: np.ndarray, alpha: float = 0.70) -> tuple[int, int, int]:
    """Identical to t1_tickvol_proxy.va_greedy (EQ-014; ties upper side first; POC ties -> lowest bin)."""
    poc = int(np.argmax(v))
    lo = hi = poc
    tot = v.sum()
    acc = v[poc]
    n = len(v)
    while acc < alpha * tot and (lo > 0 or hi < n - 1):
        up = v[hi + 1:hi + 3].sum() if hi < n - 1 else -1
        dn = v[max(lo - 2, 0):lo].sum() if lo > 0 else -1
        if up >= dn:
            k = min(2, n - 1 - hi); acc += v[hi + 1:hi + 1 + k].sum(); hi += k
        else:
            k = min(2, lo); acc += v[lo - k:lo].sum(); lo -= k
    return poc, lo, hi


def value_area(h: np.ndarray, l: np.ndarray, c: np.ndarray, tv: np.ndarray, w: float):
    """Return (VAL, VAH, POC_price) with bins [k*w, (k+1)*w) on typical price; None if no volume."""
    if len(c) == 0 or tv.sum() <= 0:
        return None
    tp = (h + l + c) / 3.0
    k = np.floor(tp / w + 1e-9).astype(np.int64)
    k0 = int(k.min())
    n = int(k.max()) - k0 + 1
    if n > 20000:
        return None
    v = np.bincount(k - k0, weights=tv, minlength=n)
    poc, lo, hi = va_greedy(v)
    return (k0 + lo) * w, (k0 + hi + 1) * w, (k0 + poc + 0.5) * w


# ----------------------------------------------------------------------------- costs (§C7)
def commission(sym: str, price: float) -> float:
    if sym == 'XAUUSD':
        return 0.07
    if sym == 'USDJPY':
        return 0.00007 * price
    return 0.00007


# ----------------------------------------------------------------------------- statistics (§C8)
def block_indices(n: int, rng: np.random.Generator, L: int = BLOCK) -> np.ndarray:
    if n <= L:
        return rng.integers(0, n, n)
    nb = int(math.ceil(n / L))
    st = rng.integers(0, n - L + 1, nb)
    return (st[:, None] + np.arange(L)[None, :]).ravel()[:n]


def bootstrap(stat, n: int, B: int = B_BOOT, seed: int = SEED) -> np.ndarray:
    """stat(idx) -> float; idx = resampled positions into the day-ordered unit arrays."""
    rng = np.random.default_rng(seed)
    out = np.empty(B)
    for b in range(B):
        out[b] = stat(block_indices(n, rng))
    return out


def boot_summary(theta: float, reps: np.ndarray) -> dict:
    r = reps[np.isfinite(reps)]
    if len(r) == 0 or not np.isfinite(theta):
        return {'theta': _f(theta), 'ci95': [None, None], 'p_one_sided': None, 'B_finite': int(len(r))}
    return {'theta': _f(theta), 'ci95': [_f(np.percentile(r, 2.5)), _f(np.percentile(r, 97.5))],
            'p_one_sided': _f((1 + np.sum(r <= 0)) / (len(r) + 1)), 'B_finite': int(len(r))}


def bh(pvals: list) -> list:
    """Benjamini-Hochberg adjusted p-values (None passes through)."""
    idx = [i for i, p in enumerate(pvals) if p is not None]
    m = len(idx)
    adj = [None] * len(pvals)
    if m == 0:
        return adj
    order = sorted(idx, key=lambda i: pvals[i])
    prev = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        val = min(prev, pvals[i] * m / rank)
        prev = val
        adj[i] = min(1.0, val)
    return adj


def verdict(disc_theta, disc_p_adj, val_theta, hold_theta, pooled_ci_lo, pooled_theta, extra_ok: bool = True) -> str:
    """§C8 per-symbol rule."""
    def pos(x):
        return x is not None and np.isfinite(x) and x > 0
    if pooled_theta is None or not np.isfinite(pooled_theta) or pooled_theta <= 0:
        return 'REJECTED'
    if disc_theta is not None and hold_theta is not None and np.isfinite(disc_theta) and np.isfinite(hold_theta) \
            and np.sign(disc_theta) != 0 and np.sign(hold_theta) != 0 and np.sign(disc_theta) != np.sign(hold_theta):
        return 'REJECTED'
    if pos(disc_theta) and disc_p_adj is not None and disc_p_adj < 0.10 and pos(val_theta) and pos(hold_theta) \
            and pooled_ci_lo is not None and pooled_ci_lo > 0 and extra_ok:
        return 'SUPPORTED'
    return 'INCONCLUSIVE'


def year_shares(years: np.ndarray, contrib: np.ndarray) -> dict:
    """Share of the pooled effect contributed by each calendar year (contrib sums to the pooled numerator)."""
    tot = float(np.nansum(contrib))
    out = {}
    for y in sorted(set(years.tolist())):
        out[str(y)] = _f(float(np.nansum(contrib[years == y])) / tot) if tot != 0 else None
    mx = max((abs(v) for v in out.values() if v is not None), default=None)
    return {'shares': out, 'max_abs_share': _f(mx), 'flag_year_gt_50pct': bool(mx is not None and mx > 0.5)}


def _f(x):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if np.isfinite(x) else None


def stage_max_split(stage: str) -> int:
    return {'disc': 0, 'val': 1, 'full': 2}[stage]


def norm_cdf(x):
    from scipy.stats import norm
    return norm.cdf(x)
