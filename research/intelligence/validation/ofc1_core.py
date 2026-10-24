#!/usr/bin/env python3
"""OFC1: the user's core order-flow method on CME futures (PREREG_OFC1_CORE_ORDERFLOW.md, sha ede1bc8d...).

Research only. Reads Databento trades files already on disk (orderflow/databento/data); writes results JSON in
research/intelligence/validation/. Section references (§n) point to the pre-registration; Dn to
DEVIATIONS_OFC1.md (fixed before discovery opened).

Usage: python ofc1_core.py --stage disc|val|full
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DBDIR = os.path.join(HERE, '..', 'orderflow', 'databento')
sys.path.insert(0, HERE)
sys.path.insert(0, '~/NEXA-Agent-Lab/filesnexa/NEXA/research')
import of_common as oc  # noqa: E402  (va_greedy, bh; read-only)

NS = 1_000_000_000
MIN = 60 * NS
HOUR = 3600 * NS
DAY = 86400 * NS
FIX = 1_000_000_000            # Databento fixed-point price scale (1e-9)

# §2 instrument constants: tick (price units), USD per tick, profile row in ticks, fee per side (§5)
INSTR = {
    '6E': dict(tick=0.00005, usd_tick=6.25, row=2, fee=2.61),
    '6J': dict(tick=0.0000005, usd_tick=6.25, row=1, fee=2.61),
    '6B': dict(tick=0.0001, usd_tick=6.25, row=1, fee=2.61),
    'GC': dict(tick=0.10, usd_tick=10.00, row=10, fee=2.66),
}
SPLITS = [('discovery', '2025-12-01', '2026-04-30'), ('validation', '2026-05-01', '2026-07-31'),
          ('holdout', '2026-08-01', '2026-09-30')]
STAGE_END = {'disc': '2026-04-30', 'val': '2026-07-31', 'full': '2026-09-30'}
SEED = 20261011
B_BOOT = 2000
BLOCK_SESS = 5
N_PLACEBO = 200
Q_BIG, L_BIG, L_BASE = 99.0, 60, 20
SETUPS = ('A', 'B', 'A_m', 'B_m')          # A_m = A' (mirror short at VAH), B_m = B' (mirror long above VAH)


# ----------------------------------------------------------------------------- clocks
def tz_offset_ns(t: np.ndarray, tz: str) -> np.ndarray:
    """UTC offset (ns) of zone tz at each UTC ns timestamp (DST transitions fall on whole UTC hours)."""
    h = t // HOUR
    u, inv = np.unique(h, return_inverse=True)
    z = ZoneInfo(tz)
    offs = np.array([z.utcoffset(datetime.fromtimestamp(int(x) * 3600, tz=timezone.utc)).total_seconds()
                     for x in u], dtype=np.int64) * NS
    return offs[inv]


def block_code(ny_mod: np.ndarray, ldn_mod: np.ndarray) -> np.ndarray:
    """0 Asia / 1 London / 2 NY (big_trades.session_block; A1 08:00 London, A2 08:30 NY)."""
    asia = (ny_mod >= 17 * 60) | (ldn_mod < 8 * 60)
    london = ~asia & (ny_mod < 8 * 60 + 30)
    return np.where(asia, 0, np.where(london, 1, 2)).astype(np.int8)


def day_str(sday: int) -> str:
    return datetime.fromtimestamp(sday * 86400, tz=timezone.utc).strftime('%Y-%m-%d')


# ----------------------------------------------------------------------------- data
@dataclass
class Data:
    sym: str
    t: np.ndarray          # ts_event ns (sorted with side, sequence)
    px: np.ndarray         # price in ticks (int64)
    sz: np.ndarray         # size
    sd: np.ndarray         # 0 = N, 1 = B (buy aggressor, at ask), 2 = A (sell aggressor, at bid)
    iid: np.ndarray
    sday: np.ndarray       # server day (days since epoch)
    umin: np.ndarray       # absolute UTC minute
    nymod: np.ndarray      # NY minute of day
    blk: np.ndarray        # session block code
    sess: list = field(default_factory=list)       # sorted unique server days
    s0: np.ndarray = None
    s1: np.ndarray = None


def load(sym: str, files: list | None = None) -> Data:
    tickfix = int(round(INSTR[sym]['tick'] * FIX))
    import databento as db
    if files is None:
        files = sorted(f for f in os.listdir(os.path.join(DBDIR, 'data')) if f.startswith(f'GLBX.MDP3_trades_{sym}.v.0_'))
        files = [os.path.join(DBDIR, 'data', f) for f in files]
    parts = []
    for f in files:
        for a in db.DBNStore.from_file(f).to_ndarray(count=2_000_000):
            pr = a['price'].astype(np.int64)
            if np.any(pr % tickfix):
                raise ValueError(f'{sym}: price not a multiple of the tick (prereg §2 constant wrong)')
            side = a['side']
            parts.append((a['ts_event'].astype(np.int64), (pr // tickfix).astype(np.int32), a['size'].astype(np.int32),
                          np.where(side == b'B', 1, np.where(side == b'A', 2, 0)).astype(np.int8),
                          a['instrument_id'].astype(np.int32), a['sequence'].astype(np.uint32)))
    t, px, sz, sd, iid, seq = (np.concatenate([p[k] for p in parts]) for k in range(6))
    del parts
    # de-duplicate exact repeats (overlapping files), then sort by (t, side, sequence)
    order = np.lexsort((seq, sd, t))
    t, px, sz, sd, iid, seq = t[order], px[order], sz[order], sd[order], iid[order], seq[order]
    dup = np.zeros(len(t), bool)
    dup[1:] = (t[1:] == t[:-1]) & (seq[1:] == seq[:-1]) & (px[1:] == px[:-1]) & (sz[1:] == sz[:-1]) & (sd[1:] == sd[:-1])
    keep = ~dup
    t, px, sz, sd, iid = t[keep], px[keep], sz[keep], sd[keep], iid[keep]
    nyo = tz_offset_ns(t, 'America/New_York')
    ldo = tz_offset_ns(t, 'Europe/London')
    sday = (t + nyo + 7 * HOUR) // DAY
    nymod = ((t + nyo) // MIN) % 1440
    blk = block_code(nymod, ((t + ldo) // MIN) % 1440)
    d = Data(sym, t, px, sz, sd, iid, sday, t // MIN, nymod.astype(np.int16), blk)
    u, s0 = np.unique(sday, return_index=True)
    d.sess = u.tolist()
    d.s0 = s0
    d.s1 = np.r_[s0[1:], len(t)]
    return d


# ----------------------------------------------------------------------------- statistics helpers
def pct_from_hist(hist: np.ndarray, q: float) -> float:
    """np.percentile(x, q) (linear) for integer data given hist[v] = count of value v."""
    n = int(hist.sum())
    pos = (n - 1) * q / 100.0
    lo = int(math.floor(pos))
    frac = pos - lo
    cum = np.cumsum(hist)
    v_lo = int(np.searchsorted(cum, lo + 1))
    v_hi = int(np.searchsorted(cum, min(lo + 2, n)))
    return v_lo + frac * (v_hi - v_lo)


def orders_of(t, sd, iid, sz, px):
    """Aggressor orders: consecutive records with equal (iid, t, side) (data sorted by t, side, seq)."""
    if len(t) == 0:
        z = np.zeros(0, np.int64)
        return z, z, z, z, z, z
    br = np.ones(len(t), bool)
    br[1:] = (t[1:] != t[:-1]) | (sd[1:] != sd[:-1]) | (iid[1:] != iid[:-1])
    st = np.flatnonzero(br)
    osz = np.add.reduceat(sz, st)
    opmin = np.minimum.reduceat(px, st)
    opmax = np.maximum.reduceat(px, st)
    return st, t[st], sd[st], osz, opmin, opmax


# ----------------------------------------------------------------------------- profile (§3.1, §3.2)
@dataclass
class Profile:
    VAL: int
    VAH: int
    lvn: np.ndarray        # LVN prices in ticks (row midpoints, float)


def profile_of(px: np.ndarray, sz: np.ndarray, row: int):
    if len(px) == 0:
        return None
    k = px // row
    k0 = int(k.min())
    v = np.bincount(k - k0, weights=sz.astype(float))
    poc, lo, hi = oc.va_greedy(v)
    lv = []
    for i in range(1, len(v) - 1):
        if v[i] < v[i - 1] and v[i] <= v[i + 1] and v[i] <= 0.5 * min(v[:i].max(), v[i + 1:].max()):
            lv.append((k0 + i) * row + (row - 1) / 2.0)
    return Profile((k0 + lo) * row, (k0 + hi + 1) * row, np.array(lv, float))


# ----------------------------------------------------------------------------- footprint (§3.6, §3.7)
def stacks(px, sz, sd, ratio=3.0, minvol=10, nt_form=False, min_stack=3):
    """Return (has_buy_stack, has_sell_stack) for one candle's trades."""
    if len(px) == 0:
        return False, False
    p0 = int(px.min())
    n = int(px.max()) - p0 + 3
    ask = np.bincount(px[sd == 1] - p0 + 1, weights=sz[sd == 1], minlength=n)   # index i <-> price p0 - 1 + i
    bid = np.bincount(px[sd == 2] - p0 + 1, weights=sz[sd == 2], minlength=n)
    bi = np.zeros(n, bool)
    si = np.zeros(n, bool)
    if nt_form:
        bi[1:] = (ask[1:] - bid[:-1]) >= minvol
        bi[1:] &= ask[1:] >= ratio * bid[:-1]
        si[:-1] = (bid[:-1] - ask[1:]) >= minvol
        si[:-1] &= bid[:-1] >= ratio * ask[1:]
    else:
        bi[1:] = (ask[1:] >= ratio * bid[:-1]) & (ask[1:] >= minvol) & (bid[:-1] >= 1)
        si[:-1] = (bid[:-1] >= ratio * ask[1:]) & (bid[:-1] >= minvol) & (ask[1:] >= 1)
    return _run(bi) >= min_stack, _run(si) >= min_stack


def _run(m: np.ndarray) -> int:
    best = cur = 0
    for x in m:
        cur = cur + 1 if x else 0
        best = max(best, cur)
    return best


# ----------------------------------------------------------------------------- session engine (§4)
@dataclass
class Params:
    confirm: bool = True
    e2: float = 0.10
    min_stack: int = 3
    nt_form: bool = False
    first_bubble: bool = False
    cost_floor: bool = True
    exit_on_close: bool = False


def simulate_exit(px, umin, i0, direction, entry, stop, target, close_px=None, close_idx=None):
    """Trade-by-trade exit from index i0 (§4). Returns (fill, kind, index)."""
    seg = px[i0:]
    if direction > 0:
        hs, ht = seg <= stop, seg > target
    else:
        hs, ht = seg >= stop, seg < target
    js = int(np.argmax(hs)) if hs.any() else None
    jt = int(np.argmax(ht)) if ht.any() else None
    if js is None and jt is None:
        if len(seg) == 0:
            return entry, 'time', i0
        return int(seg[-1]) - direction, 'time', len(px) - 1
    if jt is None or (js is not None and js <= jt):
        return int(seg[js]) - direction, 'stop', i0 + js
    return target, 'target', i0 + jt


def simulate_exit_close(cclose, k0, direction, stop, target):
    """Robustness: exits on 1-min closes after candle k0."""
    for k in range(k0 + 1, len(cclose)):
        c = cclose[k]
        if (direction > 0 and c <= stop) or (direction < 0 and c >= stop):
            return int(c) - direction, 'stop', k
        if (direction > 0 and c > target) or (direction < 0 and c < target):
            return target, 'target', k
    return int(cclose[-1]) - direction, 'time', len(cclose) - 1


def run_session(S: dict, prof: Profile, thr: dict, base: np.ndarray, p: Params, spec: dict,
                rng: np.random.Generator | None = None, n_placebo: int = 0):
    """S: one session's sorted arrays t, px, sz, sd, umin, nymod, blk (+ orders). Returns (trades, skips, placebo)."""
    px, sz, sd, um = S['px'], S['sz'], S['sd'], S['umin']
    usd, fee = spec['usd_tick'], spec['fee']
    # candles
    cb = np.ones(len(um), bool)
    cb[1:] = um[1:] != um[:-1]
    cst = np.flatnonzero(cb)
    cend = np.r_[cst[1:], len(um)]
    cmin = um[cst]
    cclose = px[cend - 1]
    cvol = np.add.reduceat(sz, cst)
    sgn = np.where(sd == 1, 1, np.where(sd == 2, -1, 0))
    cdelta = np.add.reduceat(sz.astype(np.int64) * sgn, cst)
    cny = S['nymod'][cst]
    # big orders near either edge, grouped by candle
    ost, ot, osd, osz, opmin, opmax = S['orders']
    oblk = S['blk'][ost]
    othr = np.array([thr[0], thr[1], thr[2]], dtype=float)[oblk.astype(np.int64)] if len(oblk) else np.zeros(0)
    big = osz >= othr
    width = prof.VAH - prof.VAL
    near_lo = big & (osd == 2) & (np.abs(opmin - prof.VAL) <= p.e2 * width)
    near_hi = big & (osd == 1) & (np.abs(opmax - prof.VAH) <= p.e2 * width)
    cand = np.flatnonzero(near_lo | near_hi)
    ocandle = np.searchsorted(cst, ost[cand], side='right') - 1
    by_candle: dict = {}
    for j, kc in zip(cand, ocandle):
        by_candle.setdefault(int(kc), []).append(int(j))
    lvn = np.sort(prof.lvn)
    trades, skips, placebo = [], {'cost_floor': 0, 'no_target': 0, 'target_not_beyond': 0, 'stop_wrong_side': 0}, []

    def confirm(k, direction):
        if not p.confirm:
            return True
        a, b = cst[k], cend[k]
        bs, ss = stacks(px[a:b], sz[a:b], sd[a:b], nt_form=p.nt_form, min_stack=p.min_stack)
        vol_ok = cvol[k] > base[int(cny[k])]
        return (bs and cdelta[k] > 0 and vol_ok) if direction > 0 else (ss and cdelta[k] < 0 and vol_ok)

    def enter(k, direction, stop, target, setup):
        """Returns 'trade' | 'skip_floor' | 'no_target' | 'not_beyond' | 'stop_wrong'."""
        entry = int(cclose[k]) + direction
        if target is None:
            skips['no_target'] += 1
            return 'no_target', None
        if (direction > 0 and target <= entry) or (direction < 0 and target >= entry):
            skips['target_not_beyond'] += 1
            return 'not_beyond', None
        risk = (entry - stop) * direction
        if risk <= 0:
            skips['stop_wrong_side'] += 1
            return 'stop_wrong', None
        if p.cost_floor and (2 * fee + 2 * usd) > 0.20 * risk * usd:
            skips['cost_floor'] += 1
            return 'skip_floor', None
        if p.exit_on_close:
            fill, kind, kx = simulate_exit_close(cclose, k, direction, stop, target)
            xmin = cmin[kx]
        else:
            i0 = int(cend[k])
            fill, kind, ix = simulate_exit(px, um, i0, direction, entry, stop, target)
            xmin = um[min(ix, len(um) - 1)]
        gross = (fill - entry) * direction * usd
        net = gross - 2 * fee
        r0 = net / (risk * usd)
        r1 = (net - usd * (1 + (kind in ('stop', 'time')))) / (risk * usd)
        tr = dict(setup=setup, dir=direction, k=int(k), minute=int(cmin[k]), nymod=int(cny[k]),
                  blk=int(S['blk'][cst[k]]), entry=entry, stop=int(stop), target=float(target), exit=float(fill),
                  kind=kind, risk=int(risk), R0=float(r0), R1=float(r1))
        trades.append(tr)
        if rng is not None and n_placebo:
            placebo.append(_placebo(tr, rng, n_placebo))
        return 'trade', xmin

    def _placebo(tr, rng, n):
        last_ok = np.flatnonzero(cmin <= cmin[-1] - 1)
        ks = rng.choice(last_ok, size=n) if len(last_ok) else np.zeros(0, int)
        out = np.empty(len(ks))
        dist_s = tr['risk']
        dist_t = abs(tr['target'] - tr['entry'])
        dr = tr['dir']
        for i, kk in enumerate(ks):
            e = int(cclose[kk]) + dr
            st = e - dr * dist_s
            tg = e + dr * dist_t
            fill, kind, _ = simulate_exit(px, um, int(cend[kk]), dr, e, st, tg)
            net = (fill - e) * dr * usd - 2 * fee
            out[i] = net / (dist_s * usd)
        return out

    pend_lo = pend_hi = None
    resume = -1
    for k in range(len(cst)):
        if cmin[k] < resume:
            continue
        for j in by_candle.get(k, []):
            if k == 0:
                continue
            ctx = cclose[k - 1]
            if not (prof.VAL <= ctx <= prof.VAH):
                continue
            if near_lo[j] and not (p.first_bubble and pend_lo is not None):
                pend_lo = {'lo': int(opmin[j]), 'hi': int(opmax[j]), 'a': True}
            if near_hi[j] and not (p.first_bubble and pend_hi is not None):
                pend_hi = {'lo': int(opmin[j]), 'hi': int(opmax[j]), 'a': True}
        c = int(cclose[k])
        res = None
        if pend_lo is not None:
            pl = pend_lo
            if c < min(pl['lo'], prof.VAL):
                if confirm(k, -1):
                    entry = c - 1
                    below = lvn[(lvn < prof.VAL) & (lvn < entry)]
                    tgt = math.ceil(below.max()) if len(below) else None
                    res = enter(k, -1, pl['hi'] + 1, tgt, 'B')
                pend_lo = None
            elif c < pl['lo']:
                pl['a'] = False
            elif c > pl['hi'] and pl['a']:
                if confirm(k, +1):
                    res = enter(k, +1, pl['lo'] - 1, prof.VAH, 'A')
                    if res[0] in ('trade', 'skip_floor', 'stop_wrong'):
                        pend_lo = None
        if (res is None or res[0] != 'trade') and pend_hi is not None:
            ph = pend_hi
            if c > max(ph['hi'], prof.VAH):
                if confirm(k, +1):
                    entry = c + 1
                    above = lvn[(lvn > prof.VAH) & (lvn > entry)]
                    tgt = math.floor(above.min()) if len(above) else None
                    res = enter(k, +1, ph['lo'] - 1, tgt, 'B_m')
                pend_hi = None
            elif c > ph['hi']:
                ph['a'] = False
            elif c < ph['lo'] and ph['a']:
                if confirm(k, -1):
                    res = enter(k, -1, ph['hi'] + 1, prof.VAL, 'A_m')
                    if res[0] in ('trade', 'skip_floor', 'stop_wrong'):
                        pend_hi = None
        if res is not None and res[0] == 'trade':
            pend_lo = pend_hi = None
            resume = int(res[1]) + 1
    return trades, skips, placebo


# ----------------------------------------------------------------------------- instrument run
def degraded_touch() -> set:
    with open(os.path.join(DBDIR, 'dataset_condition_2025-09_2026-09.json')) as f:
        deg = {d for d, _ in json.load(f)}
    out = set(deg)
    for d in deg:
        dd = datetime.strptime(d, '%Y-%m-%d').toordinal() + 1
        out.add(datetime.fromordinal(dd).strftime('%Y-%m-%d'))
    return out


def prepare(sym: str, D: Data) -> dict:
    spec = INSTR[sym]
    touch = degraded_touch()
    days = [day_str(s) for s in D.sess]
    nminutes = np.array([len(np.unique(D.umin[a:b])) for a, b in zip(D.s0, D.s1)])
    med = float(np.median(nminutes))
    qvalid = np.array([i > 0 and nminutes[i] >= 0.8 * med and days[i] not in touch for i in range(len(days))])
    dom = [int(np.bincount(D.iid[a:b] - D.iid[a:b].min()).argmax() + D.iid[a:b].min()) for a, b in zip(D.s0, D.s1)]
    # per-session aggregates for history: order-size histograms per block, NY-minute volume, NY profile
    hists, vols, profs = [], [], []
    orders = []
    for i, (a, b) in enumerate(zip(D.s0, D.s1)):
        m = D.iid[a:b] == dom[i]
        idx = np.flatnonzero(m) + a
        o = orders_of(D.t[idx], D.sd[idx], D.iid[idx], D.sz[idx], D.px[idx])
        orders.append((idx, o))
        ob = D.blk[idx][o[0]] if len(o[0]) else np.zeros(0, np.int8)
        hists.append([np.bincount(o[3][ob == bc]) if np.any(ob == bc) else np.zeros(1, np.int64) for bc in range(3)])
        vols.append(np.bincount(D.nymod[idx].astype(np.int64), weights=D.sz[idx], minlength=1440))
        ny = idx[D.blk[idx] == 2]
        profs.append(profile_of(D.px[ny], D.sz[ny], spec['row']) if len(ny) else None)
    split_of = {}
    for name, a, b in SPLITS:
        for i, d in enumerate(days):
            if a <= d <= b:
                split_of[i] = name
    return dict(sym=sym, spec=spec, D=D, days=days, qvalid=qvalid, dom=dom, hists=hists, vols=vols, profs=profs,
                orders=orders, split_of=split_of)


def run_pass(C: dict, stage_end: str, params: Params, with_placebo: bool):
    sym, spec, D, days, qvalid, dom = C['sym'], C['spec'], C['D'], C['days'], C['qvalid'], C['dom']
    hists, vols, profs, orders, split_of = C['hists'], C['vols'], C['profs'], C['orders'], C['split_of']
    rng = np.random.default_rng(SEED)
    trades, skips, plac, counts = [], {}, [], {'warmup': 0, 'roll': 0, 'no_prior_profile': 0, 'excluded': 0, 'scored': 0}
    qv_idx = np.flatnonzero(qvalid)
    for i, d in enumerate(days):
        if i not in split_of or d > stage_end:
            continue
        if not qvalid[i]:
            counts['excluded'] += 1
            continue
        prior_q = qv_idx[qv_idx < i]
        if len(prior_q) < L_BIG:
            counts['warmup'] += 1
            continue
        pj = int(prior_q[-1])                       # D1: prior profile = most recent prior Q-valid session
        if profs[pj] is None:
            counts['no_prior_profile'] += 1
            continue
        if dom[pj] != dom[i]:
            counts['roll'] += 1
            continue
        hist_ids = prior_q[-L_BIG:]
        thr = {}
        for bc in range(3):
            hs = [hists[h][bc] for h in hist_ids]
            mx = max(len(h) for h in hs)
            tot = np.zeros(mx, np.int64)
            for h in hs:
                tot[:len(h)] += h
            thr[bc] = math.ceil(pct_from_hist(tot, Q_BIG)) if tot.sum() else np.inf
        base = np.mean([vols[h] for h in prior_q[-L_BASE:]], axis=0)
        idx, o = orders[i]
        S = {'px': D.px[idx], 'sz': D.sz[idx], 'sd': D.sd[idx], 'umin': D.umin[idx], 'nymod': D.nymod[idx],
             'blk': D.blk[idx], 'orders': (o[0], o[1], o[2], o[3], o[4], o[5])}
        tr, sk, pl = run_session(S, profs[pj], thr, base, params, spec, rng if with_placebo else None,
                                 N_PLACEBO if with_placebo else 0)
        counts['scored'] += 1
        for x in tr:
            x.update(sym=sym, day=d, split=split_of[i], month=_month(D, idx, x))
        trades += tr
        plac += pl
        for kk, v in sk.items():
            skips[kk] = skips.get(kk, 0) + v
    return trades, skips, plac, counts


def _month(D, idx, tr):
    tmin = tr['minute'] * MIN
    off = tz_offset_ns(np.array([tmin]), 'America/New_York')[0]
    return datetime.fromtimestamp((tmin + off) / NS, tz=timezone.utc).strftime('%Y-%m')


# ----------------------------------------------------------------------------- statistics (§6, §7)
def sess_units(trs: list, key='R0'):
    """Per calendar session date (all instruments): sum R and count, in date order."""
    days = sorted({t['day'] for t in trs})
    pos = {d: i for i, d in enumerate(days)}
    s = np.zeros(len(days))
    n = np.zeros(len(days))
    for t in trs:
        s[pos[t['day']]] += t[key]
        n[pos[t['day']]] += 1
    return days, s, n


def boot_mean(trs: list, key='R0', all_days: list | None = None) -> dict:
    if not trs:
        return {'n': 0, 'mean': None, 'ci95': [None, None], 'p_one_sided': None}
    days = all_days or sorted({t['day'] for t in trs})
    pos = {d: i for i, d in enumerate(days)}
    s = np.zeros(len(days))
    n = np.zeros(len(days))
    for t in trs:
        s[pos[t['day']]] += t[key]
        n[pos[t['day']]] += 1
    theta = s.sum() / n.sum()
    rng = np.random.default_rng(SEED)
    reps = np.empty(B_BOOT)
    for b in range(B_BOOT):
        ix = oc.block_indices(len(days), rng, BLOCK_SESS)
        nn = n[ix].sum()
        reps[b] = s[ix].sum() / nn if nn else np.nan
    r = reps[np.isfinite(reps)]
    sd = float(np.std([t[key] for t in trs], ddof=1)) if len(trs) > 1 else None
    return {'n': len(trs), 'mean': float(theta), 'ci95': [float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))],
            'p_one_sided': float((1 + np.sum(r <= 0)) / (len(r) + 1)), 'sd_R': sd,
            'mde80': (2.5 * sd / math.sqrt(len(trs))) if sd else None}


def boot_delta(a: list, b: list, all_days: list) -> dict:
    pos = {d: i for i, d in enumerate(all_days)}
    sa, na, sb, nb = (np.zeros(len(all_days)) for _ in range(4))
    for t in a:
        sa[pos[t['day']]] += t['R0']; na[pos[t['day']]] += 1
    for t in b:
        sb[pos[t['day']]] += t['R0']; nb[pos[t['day']]] += 1
    if na.sum() == 0 or nb.sum() == 0:
        return {'delta': None}
    theta = sa.sum() / na.sum() - sb.sum() / nb.sum()
    rng = np.random.default_rng(SEED)
    reps = []
    for _ in range(B_BOOT):
        ix = oc.block_indices(len(all_days), rng, BLOCK_SESS)
        if na[ix].sum() and nb[ix].sum():
            reps.append(sa[ix].sum() / na[ix].sum() - sb[ix].sum() / nb[ix].sum())
    r = np.array(reps)
    return {'delta': float(theta), 'ci95': [float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))],
            'p_one_sided': float((1 + np.sum(r <= 0)) / (len(r) + 1))}


def placebo_p(trs: list, plac: list) -> dict:
    if not trs:
        return {'p': None}
    obs = float(np.mean([t['R0'] for t in trs]))
    P = np.vstack(plac)                       # trades x draws
    means = P.mean(axis=0)
    return {'observed_mean': obs, 'placebo_mean_of_means': float(means.mean()),
            'p': float((1 + np.sum(means >= obs)) / (len(means) + 1))}


def summarize(trs, n2, plac, opened, all_days):
    out = {}
    sub = {'P1': trs}
    for s in SETUPS:
        sub[s] = [t for t in trs if t['setup'] == s]
    for s in INSTR:
        sub[s if s not in SETUPS else s + '_i'] = [t for t in trs if t['sym'] == s]
    for name, tl in sub.items():
        out[name] = {'pooled': boot_mean(tl, 'R0', None), 'pooled_S1': boot_mean(tl, 'R1', None),
                     'by_split': {sp: boot_mean([t for t in tl if t['split'] == sp], 'R0', None) for sp in opened}}
    out['N2_no_confirmation'] = {'pooled': boot_mean(n2, 'R0', None),
                                 'by_split': {sp: boot_mean([t for t in n2 if t['split'] == sp]) for sp in opened}}
    out['N2_delta'] = {'pooled': boot_delta(trs, n2, all_days),
                       'by_split': {sp: boot_delta([t for t in trs if t['split'] == sp],
                                                   [t for t in n2 if t['split'] == sp], all_days) for sp in opened}}
    idx = {id(t): i for i, t in enumerate(trs)}
    out['N1_placebo'] = {'pooled': placebo_p(trs, plac)}
    for sp in opened:
        sel = [i for i, t in enumerate(trs) if t['split'] == sp]
        out['N1_placebo'][sp] = placebo_p([trs[i] for i in sel], [plac[i] for i in sel]) if sel else {'p': None}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['disc', 'val', 'full'], required=True)
    ap.add_argument('--symbols', default='6E,6J,6B,GC')
    a = ap.parse_args()
    end = STAGE_END[a.stage]
    opened = [s[0] for s in SPLITS if s[1] <= end]
    trs, n2, plac, meta = [], [], [], {}
    robust = {}
    rob_params = {'cost_floor_off': Params(cost_floor=False), 'imbalance_nt_form': Params(nt_form=True),
                  'e2_5pct': Params(e2=0.05), 'e2_20pct': Params(e2=0.20), 'first_bubble': Params(first_bubble=True),
                  'stack_ge2': Params(min_stack=2), 'exits_on_close': Params(exit_on_close=True)}
    for sym in a.symbols.split(','):
        C = prepare(sym, load(sym))
        t1, sk, pl, cnt = run_pass(C, end, Params(), True)
        t2, sk2, _, _ = run_pass(C, end, Params(confirm=False), False)
        trs += t1; plac += pl; n2 += t2
        meta[sym] = {'skips': sk, 'counts': cnt, 'n2_skips': sk2, 'trades': len(t1), 'n2_trades': len(t2)}
        if a.stage == 'full':
            for name, prm in rob_params.items():
                tr_r, _, _, _ = run_pass(C, end, prm, False)
                robust.setdefault(name, []).extend(tr_r)
        del C
        print(sym, meta[sym], flush=True)
    all_days = sorted({t['day'] for t in trs} | {t['day'] for t in n2})
    out = {'prereg_sha256': 'ede1bc8da8aa187982e0c4981af8bedc3489172dbc3ed60699ecca72cb3fd00f',
           'stage': a.stage, 'splits_opened': opened, 'meta': meta,
           'results': summarize(trs, n2, plac, opened, all_days),
           'trades': trs}
    # BH over secondaries on the latest opened split's p (disc stage) or pooled p (full)
    sec = list(SETUPS) + [s if s not in SETUPS else s + '_i' for s in INSTR]
    key = 'pooled'
    pv = [out['results'][s][key]['p_one_sided'] for s in sec] + [out['results']['N2_delta']['pooled'].get('p_one_sided')]
    out['BH_secondaries'] = dict(zip(sec + ['N2_delta'], oc.bh(pv)))
    disc_pv = [out['results'][s]['by_split']['discovery']['p_one_sided'] for s in sec]
    out['BH_secondaries_discovery'] = dict(zip(sec, oc.bh(disc_pv)))
    # DSR (n_trials = 10)
    try:
        from nexa_robust import deflated_sharpe
        series = {'P1': [t['R0'] for t in trs]}
        for s in SETUPS:
            series[s] = [t['R0'] for t in trs if t['setup'] == s]
        for s in INSTR:
            series['i_' + s] = [t['R0'] for t in trs if t['sym'] == s]
        series['N2'] = [t['R0'] for t in n2]
        srs = [np.mean(v) / np.std(v, ddof=1) for v in series.values() if len(v) > 2 and np.std(v, ddof=1) > 0]
        var_sr = float(np.var(srs, ddof=1)) if len(srs) > 1 else 0.0
        out['DSR'] = {'P1': float(deflated_sharpe(np.array(series['P1']), 10, var_sr)) if len(series['P1']) > 2 else None,
                      'var_sr_trials': var_sr, 'n_trials': 10}
    except Exception as e:  # noqa: BLE001
        out['DSR'] = {'error': repr(e)}
    if a.stage == 'full':
        out['robustness'] = {k: {'pooled': boot_mean(v), 'by_setup': {s: boot_mean([t for t in v if t['setup'] == s]) for s in SETUPS}}
                             for k, v in robust.items()}
        out['by_block'] = {b: boot_mean([t for t in trs if t['blk'] == bc]) for bc, b in enumerate(('Asia', 'London', 'NY'))}
        out['by_setup_instrument'] = {f'{s}|{i}': boot_mean([t for t in trs if t['setup'] == s and t['sym'] == i])
                                      for s in SETUPS for i in INSTR}
        out['acceptance'] = acceptance(out, trs)
    fn = os.path.join(HERE, 'ofc1_results.json' if a.stage == 'full' else f'ofc1_results_{a.stage}.json')
    with open(fn, 'w') as f:
        json.dump(out, f, indent=1, default=lambda x: float(x) if isinstance(x, (np.floating,)) else int(x) if isinstance(x, np.integer) else str(x))
    r = out['results']['P1']
    print(json.dumps({'stage': a.stage, 'P1_pooled': r['pooled'], 'P1_by_split': r['by_split']}, indent=1, default=str))
    return 0


def acceptance(out: dict, trs: list) -> dict:
    R = out['results']
    P = R['P1']
    d, v, h = (P['by_split'].get(s, {}) for s in ('discovery', 'validation', 'holdout'))
    pooled = P['pooled']
    n_ok = (pooled['n'] or 0) >= 150 and (h.get('n') or 0) >= 30
    inst_means = {s: R[s]['pooled']['mean'] for s in INSTR}
    avail = [s for s in INSTR if R[s]['pooled']['n']]
    pos_inst = sum(1 for s in avail if (inst_means[s] or 0) > 0)
    tot = sum(t['R0'] for t in trs)
    inst_share = {s: (sum(t['R0'] for t in trs if t['sym'] == s) / tot if tot else None) for s in avail}
    months = sorted({t['month'] for t in trs})
    month_share = {m: (sum(t['R0'] for t in trs if t['month'] == m) / tot if tot else None) for m in months}
    crit = {
        '1_discovery_p<0.05': bool(d.get('mean') is not None and d['mean'] > 0 and (d.get('p_one_sided') or 1) < 0.05),
        '2_val_and_holdout_>0': bool((v.get('mean') or -1) > 0 and (h.get('mean') or -1) > 0),
        '3_pooled_ci_lo>0': bool(pooled['ci95'][0] is not None and pooled['ci95'][0] > 0),
        '4_placebo_p<=0.05': bool((R['N1_placebo']['pooled'].get('p') or 1) <= 0.05),
        '5_N2_delta>0': bool((R['N2_delta']['pooled'].get('delta') or -1) > 0),
        '6_stability': bool(pos_inst >= max(len(avail) - 1, 1) and all((x or 0) <= 0.60 for x in inst_share.values())
                            and all((x or 0) <= 0.35 for x in month_share.values()) and tot > 0),
        '7_DSR>=0.95': bool((out.get('DSR', {}).get('P1') or 0) >= 0.95),
    }
    if not n_ok:
        verdict = 'INSUFFICIENT-N'
    elif pooled['mean'] is None or pooled['mean'] <= 0 or (
            d.get('mean') is not None and h.get('mean') is not None and np.sign(d['mean']) * np.sign(h['mean']) < 0):
        verdict = 'REJECTED'
    elif all(crit.values()):
        verdict = 'RESEARCH CANDIDATE (G4)'
    else:
        verdict = 'INCONCLUSIVE'
    return {'criteria': crit, 'min_n_ok': n_ok, 'instrument_means': inst_means, 'instrument_share': inst_share,
            'month_share': month_share, 'verdict': verdict}


if __name__ == '__main__':
    sys.exit(main())
