# NEXA CFT / CFT-P: Core-Flow Trend on CME index futures. Pre-registration: PREREG_CFT.md (d8ba8ce4).
# Trend layer = Zarattini, Aziz & Barbon (2024) noise band + VWAP trailing stop; gate = self-normalised
# aggressor-signed flow Z = sum(x) / sqrt(sum(x^2)) > 1.96 in the trend direction. Reads data only; no orders.
from AlgorithmImports import *
import math
import json
import hashlib
from datetime import date, timedelta
import numpy as np

MODE = 'NQ'                 # 'F1' classifier check, 'ACHK' ES 2009-2024 port check, 'ES' / 'NQ' OOS (A, B, B-EVE, CFT-P)
DEC = list(range(600, 931, 30))           # decision times 10:00 .. 15:30 ET (minutes after midnight)
EVE_DEC = [600, 630, 660, 690, 720]       # evening variant: entries 10:00 .. 12:00 ET
EVE_EXIT_K = 749 - 570                    # forced exit at the close of the 12:29 bar
EXIT_K = 959 - 570                        # time exit at the close of the 15:59 bar
LOOK, ZCRIT = 14, 1.96
COST = {'ES': (0.30, 0.60, 1.20), 'NQ': (1.0, 2.0, 3.0)}     # S0, S1, S2 points per round trip
USD_PT = {'ES': 5.0, 'NQ': 2.0}                              # MES / MNQ dollars per point
SEED, B_BOOT, BLOCK = 20261017, 2000, 20
FALLBACK = True           # F1 failed (corr 0.717, sign 0.767 < 0.80) -> PREREG_CFT s.3 fallback: tick rule on 1-s trade close


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


# ---------------------------------------------------------------- engine (pure functions, unit-tested locally)
def classify(p, bid, ask, prev_px, prev_sign):
    """Quote rule with mid and tick-rule fallback (PREREG_CFT section 3). Returns +1 / -1 / 0."""
    if bid is not None and ask is not None and ask > bid:
        if p >= ask:
            return 1
        if p <= bid:
            return -1
        mid = (bid + ask) / 2.0
        if p > mid:
            return 1
        if p < mid:
            return -1
    if prev_px is not None and p > prev_px:
        return 1
    if prev_px is not None and p < prev_px:
        return -1
    return prev_sign


def sigma_at(prev, k):
    """Mean |close(bar k) / open - 1| over the last LOOK prior days (bar k ends at decision time)."""
    vals = [abs(d['c'][k] / d['o'][0] - 1.0) for d in prev[-LOOK:]]
    return sum(vals) / len(vals)


def simulate(day, prev, gate=False, eve=False, roll=False):
    """One RTH day. day: dict of 390-long lists o/h/l/c/v (+ 'x' signed flow per minute when gate).
    Returns a list of trades (gross points, before costs)."""
    o, h, l, c, v = day['o'], day['h'], day['l'], day['c'], day['v']
    O = o[0]
    cp = None if roll else prev[-1]['c'][389]
    hb = O if cp is None else max(O, cp)
    lb = O if cp is None else min(O, cp)
    pv = [0.0]
    sv = [0.0]
    for k in range(390):
        pv.append(pv[-1] + (h[k] + l[k] + c[k]) / 3.0 * v[k])
        sv.append(sv[-1] + v[k])
    cf = [0.0]
    cs = [0.0]
    if gate:
        for k in range(390):
            cf.append(cf[-1] + day['x'][k])
            cs.append(cs[-1] + day['x'][k] ** 2)
    pos, entry, trades, cur = 0, None, [], None
    for tau in (EVE_DEC if eve else DEC):
        k = tau - 570
        P = c[k - 1]
        s = sigma_at(prev, k - 1)
        UB, LB = hb * (1 + s), lb * (1 - s)
        vw = pv[k] / sv[k] if sv[k] > 0 else P
        D = 1 if P > UB else (-1 if P < LB else 0)
        exited = 0
        if pos:
            cur['mae'] = min(cur['mae'], (P - entry) * pos)
            stop = max(UB, vw) if pos == 1 else min(LB, vw)
            if (pos == 1 and P < stop) or (pos == -1 and P > stop):
                cur.update(exit=o[k], pts=(o[k] - entry) * pos, kind='stop', exit_tau=tau)
                trades.append(cur)
                exited, pos, cur = pos, 0, None
        z = (cf[k] / math.sqrt(cs[k])) if (gate and cs[k] > 0) else 0.0
        if pos == 0 and D != 0 and D != exited and (not gate or D * z > ZCRIT):
            entry, pos = o[k], D
            stop0 = max(UB, vw) if D == 1 else min(LB, vw)
            cur = {'dir': D, 'entry': entry, 'tau': tau, 'R': abs(entry - stop0), 'mae': 0.0, 'z': round(z, 3)}
    if pos:
        px = c[EVE_EXIT_K if eve else EXIT_K]
        cur.update(exit=px, pts=(px - entry) * pos, kind='time', exit_tau=0)
        trades.append(cur)
    return trades


def day_net(trades, cost):
    return sum(t['pts'] - cost for t in trades)


def overlay(trades, ov, cost):
    """CFT-P overlays: 0 none, 1 stop after first winner, 2 stop at -1R (first trade R), 3 both.
    Returns (day net points, worst intraday mark in points)."""
    cum, dmin, r1 = 0.0, 0.0, None
    for i, t in enumerate(trades):
        if i == 0:
            r1 = max(t['R'], 1e-9)
        dmin = min(dmin, cum + t['mae'] - cost)
        cum += t['pts'] - cost
        dmin = min(dmin, cum)
        if ov in (1, 3) and t['pts'] - cost > 0:
            break
        if ov in (2, 3) and cum <= -r1:
            break
    return cum, dmin


def combine_sim(pnl, dmin, n_paths=10000, horizon=60, seed=SEED):
    """Topstep 50K: +3000 target, trailing EOD 2000 MLL (intraday breach on worst mark), best day < 55 %."""
    rng = np.random.default_rng(seed)
    n = len(pnl)
    passed = breached = 0
    for _ in range(n_paths):
        idx = block_indices(max(n, horizon), rng)[:horizon] % n
        bal, peak, best = 0.0, 0.0, 0.0
        for d in idx:
            if bal + dmin[d] <= peak - 2000.0:
                breached += 1
                break
            bal += pnl[d]
            best = max(best, pnl[d])
            peak = max(peak, bal)
            if bal >= 3000.0 and best <= 0.55 * bal:
                passed += 1
                break
    return passed / n_paths, breached / n_paths


def green_month(pnl, n_paths=10000, seed=SEED):
    rng = np.random.default_rng(seed + 1)
    n = len(pnl)
    g = np.asarray(pnl) > 0
    hits = 0
    for _ in range(n_paths):
        idx = block_indices(max(n, 21), rng)[:21] % n
        hits += int(g[idx].sum() >= 20)
    return hits / n_paths


def cftp(day_trades, sym):
    cost, usd = COST[sym][1], USD_PT[sym]
    out = {}
    for ov in (0, 1, 2, 3):
        rows = [overlay(t, ov, cost) for t in day_trades]
        pts = np.array([r[0] for r in rows])
        mn = np.array([r[1] for r in rows])
        for k in (2, 4, 8):
            pnl, dm = pts * usd * k, mn * usd * k
            pp, pb = combine_sim(pnl, dm)
            out[f'V{ov}_k{k}'] = {'month_usd': _f(pnl.mean() * 21), 'p_green_day': _f((pnl > 0).mean()),
                                  'p_20green_of_21': _f(green_month(pnl)), 'p_pass_60d': _f(pp),
                                  'p_breach_60d': _f(pb)}
    ok = {k: v for k, v in out.items() if (v['month_usd'] or 0) > 0}
    best = max(ok, key=lambda k: ok[k]['p_pass_60d']) if ok else None
    return {'grid': out, 'choice': best}


def summarise(days, sets, sym):
    """days: list of (date, open, {set: trades}). Returns stats per set (bp of the 09:30 open)."""
    s0, s1, s2 = COST[sym]
    res = {}
    for name in sets:
        ser = {lvl: [] for lvl in ('S0', 'S1', 'S2')}
        tr = []
        for d, O, tt in days:
            t = tt[name]
            tr += t
            for lvl, cst in (('S0', s0), ('S1', s1), ('S2', s2)):
                ser[lvl].append(day_net(t, cst) / O * 1e4)
        x = np.array(ser['S1'])
        q = len(x) // 4
        blocks = [float(x[i * q:(i + 1) * q].mean()) for i in range(4)] if q else []
        cum = np.cumsum(x)
        nets = [t['pts'] - s1 for t in tr]
        wins = [n for n in nets if n > 0]
        loss = [-n for n in nets if n <= 0]
        res[name] = {'S1': boot(x), 'S0_mean': _f(np.mean(ser['S0'])), 'S2_mean': _f(np.mean(ser['S2'])),
                     'trades': len(tr), 'trades_per_day': _f(len(tr) / max(len(x), 1)),
                     'hit': _f(len(wins) / max(len(nets), 1)),
                     'payoff': _f(np.mean(wins) / np.mean(loss)) if wins and loss else None,
                     'blocks_S1': [_f(b) for b in blocks], 'blocks_pos': sum(b > 0 for b in blocks),
                     'long_pts': _f(sum(t['pts'] - s1 for t in tr if t['dir'] == 1)),
                     'short_pts': _f(sum(t['pts'] - s1 for t in tr if t['dir'] == -1)),
                     'sharpe_ann': _f(x.mean() / x.std(ddof=1) * math.sqrt(252)) if len(x) > 2 and x.std() > 0 else None,
                     'mdd_bp': _f(float(np.max(np.maximum.accumulate(cum) - cum))) if len(cum) else None,
                     'green_share': _f((x > 0).mean()), 'series': x}
    return res


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaCft(QCAlgorithm):
    def initialize(self):
        self.sym_name = 'NQ' if MODE == 'NQ' else 'ES'
        tick = Futures.Indices.NASDAQ_100_E_MINI if MODE == 'NQ' else Futures.Indices.SP_500_E_MINI
        if MODE == 'F1':
            self.set_start_date(2024, 1, 2)
            self.set_end_date(2024, 1, 5)
            res = Resolution.TICK
        elif MODE == 'ACHK':
            self.set_start_date(2009, 5, 1)
            self.set_end_date(2024, 5, 9)
            res = Resolution.MINUTE
        else:
            self.set_start_date(2024, 4, 1)
            res = Resolution.SECOND
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        f = self.add_future(tick, res, fill_forward=False, extended_market_hours=False,
                            data_normalization_mode=DataNormalizationMode.BACKWARDS_RATIO,
                            data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
        self.sym = f.symbol
        self.res = res
        self.day, self.roll, self.roll_pending = None, False, False
        self.prev, self.days, self.skipped = [], [], {'incomplete': 0, 'warmup': 0}
        self.new_day()
        self.f1 = {'x_tick': {}, 'sec': {}, 'nq': [0, 0, 0]}

    def new_day(self):
        self.bars = {}
        self.x = {}
        self.bid = self.ask = self.last_px = None
        self.last_sign = 0

    def on_data(self, data):
        for _ in data.symbol_changed_events.items():
            self.roll_pending = True
        if MODE == 'F1':
            return self.on_ticks(data)
        step = timedelta(seconds=1) if self.res == Resolution.SECOND else timedelta(minutes=1)
        t = self.time - step
        d = t.date()
        if d != self.day:
            if self.day is not None:
                self.close_day()
            self.roll, self.roll_pending = self.roll_pending, False
        self.day = d
        m = t.hour * 60 + t.minute
        qb = data.quote_bars.get(self.sym)
        if qb is not None and qb.bid is not None and qb.ask is not None:
            self.bid, self.ask = float(qb.bid.close), float(qb.ask.close)
        tb = data.bars.get(self.sym)
        if tb is None or not 570 <= m <= 959:
            return
        o, h, l, c, v = float(tb.open), float(tb.high), float(tb.low), float(tb.close), float(tb.volume)
        b = self.bars.get(m)
        self.bars[m] = [o, h, l, c, v] if b is None else [b[0], max(b[1], h), min(b[2], l), c, b[4] + v]
        if self.res == Resolution.SECOND and v > 0:
            qbid, qask = (None, None) if FALLBACK else (self.bid, self.ask)
            sg = classify(c, qbid, qask, self.last_px, self.last_sign)
            self.x[m] = self.x.get(m, 0.0) + sg * v
            if self.last_px is None or c != self.last_px:
                self.last_px = c
            self.last_sign = sg

    def on_ticks(self, data):
        ticks = data.ticks.get(self.sym)
        if ticks is None:
            return
        for tk in ticks:
            t = tk.time
            m = t.hour * 60 + t.minute
            if not 570 <= m <= 959:
                continue
            key = (t.date().isoformat(), m)
            if tk.tick_type == TickType.QUOTE:
                self.f1['nq'][0] += 1
                if tk.bid_price > 0:
                    self.bid = float(tk.bid_price); self.f1['nq'][1] += 1
                if tk.ask_price > 0:
                    self.ask = float(tk.ask_price); self.f1['nq'][2] += 1
                continue
            if tk.tick_type != TickType.TRADE or tk.quantity <= 0:
                continue
            p, q = float(tk.last_price), float(tk.quantity)
            sg = classify(p, self.bid, self.ask, self.last_px, self.last_sign)
            self.f1['x_tick'][key] = self.f1['x_tick'].get(key, 0.0) + sg * q
            if self.last_px is None or p != self.last_px:
                self.last_px = p
            self.last_sign = sg
            sk = key + (t.second,)
            self.f1['sec'][sk] = [p, self.f1['sec'].get(sk, [0, 0])[1] + q, self.bid, self.ask]

    def close_day(self):
        complete = len(self.bars) == 390 and all((570 + k) in self.bars for k in range(390))
        if not complete:
            if self.bars:
                self.skipped['incomplete'] += 1
            self.new_day()
            return
        cols = list(zip(*[self.bars[570 + k] for k in range(390)]))
        day = {'o': list(cols[0]), 'h': list(cols[1]), 'l': list(cols[2]), 'c': list(cols[3]), 'v': list(cols[4]),
               'x': [self.x.get(570 + k, 0.0) for k in range(390)]}
        if len(self.prev) >= LOOK and self.day.weekday() < 5:
            tt = {'A': simulate(day, self.prev, roll=self.roll)}
            if self.res == Resolution.SECOND:
                tt['B'] = simulate(day, self.prev, gate=True, roll=self.roll)
                tt['BEVE'] = simulate(day, self.prev, gate=True, eve=True, roll=self.roll)
            if MODE == 'ACHK' or self.day >= date(2024, 5, 10):
                self.days.append((self.day, day['o'][0], tt))
        else:
            self.skipped['warmup'] += 1
        self.prev = (self.prev + [{'o': day['o'], 'c': day['c']}])[-LOOK:]
        self.new_day()

    def f1_report(self):
        out = {'mode': 'F1', 'quote_ticks': self.f1['nq']}
        for name, use_q in (('quote', True), ('tickrule', False)):
            xs = {}
            prev_px, prev_sign = None, 0
            for sk in sorted(self.f1['sec']):
                p, q, bid, ask = self.f1['sec'][sk]
                sg = classify(p, bid if use_q else None, ask if use_q else None, prev_px, prev_sign)
                xs[sk[:2]] = xs.get(sk[:2], 0.0) + sg * q
                if prev_px is None or p != prev_px:
                    prev_px = p
                prev_sign = sg
            keys = sorted(set(xs) & set(self.f1['x_tick']))
            a = np.array([self.f1['x_tick'][k] for k in keys])
            b = np.array([xs[k] for k in keys])
            corr = float(np.corrcoef(a, b)[0, 1]) if len(keys) > 2 else None
            agree = float(np.mean(np.sign(a) == np.sign(b))) if keys else None
            out[name] = {'minutes': len(keys), 'corr': _f(corr), 'sign_agree': _f(agree),
                         'PASS': bool(corr is not None and corr >= 0.80 and agree >= 0.80)}
        return out

    def on_end_of_algorithm(self):
        if MODE == 'F1':
            self.log('NEXA_RESULT ' + json.dumps(self.f1_report(), separators=(',', ':')))
            return
        self.close_day()
        sets = ['A'] if MODE == 'ACHK' else ['A', 'B', 'BEVE']
        st = summarise(self.days, sets, self.sym_name)
        out = {'mode': MODE, 'n_days': len(self.days), 'skipped': self.skipped,
               'first_day': self.days[0][0].isoformat() if self.days else None,
               'last_day': self.days[-1][0].isoformat() if self.days else None}
        for k in sets:
            out[k] = {kk: vv for kk, vv in st[k].items() if kk != 'series'}
        if MODE != 'ACHK':
            dB = st['B']['series'] - st['A']['series']
            out['B_minus_A'] = boot(dB)
            a, b = out['A'], out['B']
            out['verdict'] = verdict(a, b, out['B_minus_A'])
            out['eve_pass'] = bool((st['BEVE']['S1']['theta'] or 0) > 0 and (st['BEVE']['S1']['ci95'][0] or -1) > 0)
            out['CFTP'] = cftp([tt['B'] for _, _, tt in self.days], self.sym_name)
            out['trades_sha256'] = hashlib.sha256(','.join(f"{d.isoformat()}:{t['tau']}:{t['pts']:.4f}"
                                                  for d, _, tt in self.days for t in tt['B']).encode()).hexdigest()
            self.log('NEXA_DAILY_B ' + ','.join(str(int(round(v))) for v in st['B']['series']))
        self.log('NEXA_RESULT ' + json.dumps(out, separators=(',', ':')))


def verdict(a, b, diff):
    nb = b['trades']
    if nb < 150:
        return 'INSUFFICIENT-N'
    if (b['S1']['theta'] or 0) <= 0:
        return 'REJECTED'
    b_ok = (b['S1']['ci95'][0] or -1) > 0
    d_ok = (diff['theta'] or 0) > 0 and (diff['p_one_sided'] or 1) <= 0.10
    a_ok = (a['S1']['theta'] or 0) > 0 and (a['S1']['ci95'][0] or -1) > 0 and a['blocks_pos'] >= 3 and a['trades'] >= 300
    if b_ok and d_ok:
        return 'CFT VALIDATED (G4)'
    if a_ok:
        return 'TREND-ONLY'
    return 'INCONCLUSIVE'
