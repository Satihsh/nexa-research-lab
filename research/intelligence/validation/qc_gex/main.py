# NEXA H-GEX-RANGE data run. Pre-registration: PREREG_GEX_RANGE.md.
# One backtest per calendar year (QC free logs are 10 KB). Each trading day it records, before the open, the prior-close
# SPX (SPX + SPXW) and NDX (NDX + NDXP) option chains reduced to naive net GEX and absolute gamma, plus the prior VIX
# close; during the day it records the NQ and ES RTH range (bars ending 09:31-16:00 ET). One compact 17-byte record per
# day is logged; every statistic is computed locally by gex_stats.py. Reads data only; no orders.
from AlgorithmImports import *
import base64
import json
import math
import struct
import time as _time
from datetime import date, datetime, timedelta

YEAR = 2015                 # the only line that changes between chunks; 0 = one-month probe
PROBE = (date(2015, 1, 2), date(2015, 1, 31))
TICK = 0.25
REC = struct.Struct('<HHHhHhHHB')    # day offset, NQ range ticks, ES range ticks, SPX gex, SPX abs, NDX gex, NDX abs, VIX x100, flags
LOG_SCALE = 2000.0          # gamma values stored as round(log10(|x|) * 2000), sign kept for net GEX
MIN_BARS = 300


def enc_log(x, signed):
    """Signed/unsigned log10 code; 0 means missing or zero."""
    if x is None or not math.isfinite(x) or x == 0:
        return 0
    v = int(round(math.log10(abs(x)) * LOG_SCALE))
    v = max(1, min(32767 if signed else 65535, v))
    return -v if (signed and x < 0) else v


def dec_log(v, signed):
    if v == 0:
        return None
    x = 10 ** (abs(v) / LOG_SCALE)
    return -x if (signed and v < 0) else x


def gex_from_rows(rows, spot):
    """rows: iterable of (is_call, open_interest, gamma). Naive dealer convention: +calls, -puts.
    Returns (net GEX in $ per 1 % move, absolute gamma in the same units, contracts used)."""
    if not spot or spot <= 0:
        return None, None, 0
    k = 100.0 * spot * spot * 0.01
    net = ab = 0.0
    n = 0
    for is_call, oi, g in rows:
        if oi is None or g is None or not math.isfinite(oi) or not math.isfinite(g) or oi <= 0:
            continue
        v = oi * g * k
        net += v if is_call else -v
        ab += abs(v)
        n += 1
    return (net, ab, n) if n else (None, None, 0)


def rth_index(t):
    """True for minute bars whose END time lies in 09:31-16:00 ET."""
    m = t.hour * 60 + t.minute
    return 9 * 60 + 31 <= m <= 16 * 60


def pack(day_off, nq_r, es_r, spx_g, spx_a, ndx_g, ndx_a, vix, flags):
    return REC.pack(day_off, min(65535, nq_r), min(65535, es_r), enc_log(spx_g, True), enc_log(spx_a, False),
                    enc_log(ndx_g, True), enc_log(ndx_a, False), min(65535, int(round((vix or 0) * 100))), flags)


def unpack(b):
    d, nq, es, sg, sa, ng, na, vx, fl = REC.unpack(b)
    return {'day': d, 'nq_ticks': nq, 'es_ticks': es, 'spx_gex': dec_log(sg, True), 'spx_abs': dec_log(sa, False),
            'ndx_gex': dec_log(ng, True), 'ndx_abs': dec_log(na, False), 'vix': vx / 100.0 if vx else None,
            'nq_ok': bool(fl & 1), 'es_ok': bool(fl & 2), 'spx_ok': bool(fl & 4), 'ndx_ok': bool(fl & 8),
            'vix_ok': bool(fl & 16)}


def flags_of(nq_bars, es_bars, spx_n, ndx_n, vix):
    return ((nq_bars >= MIN_BARS) * 1 | (es_bars >= MIN_BARS) * 2 | (spx_n > 0) * 4 | (ndx_n > 0) * 8
            | (bool(vix) and vix > 0) * 16)


def log_chunks(algo, tag, obj, size=7000):
    s = json.dumps(obj, separators=(',', ':'))
    parts = [s[i:i + size] for i in range(0, len(s), size)] or ['']
    for i, p in enumerate(parts):
        algo.log(f'{tag} {i + 1}/{len(parts)} {p}')


def _col(df, *names):
    low = {str(c).lower().replace('_', ''): c for c in df.columns}
    for n in names:
        if n in low:
            return low[n]
    return None


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaGexRange(QCAlgorithm):
    def initialize(self):
        a, b = PROBE if YEAR == 0 else (date(YEAR, 1, 1), date(YEAR, 12, 31))
        self.set_start_date(a.year, a.month, a.day)
        self.set_end_date(b.year, b.month, b.day)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        self.year0 = a.year
        self.fut = {}
        for key, f in (('NQ', Futures.Indices.NASDAQ_100_E_MINI), ('ES', Futures.Indices.SP_500_E_MINI)):
            s = self.add_future(f, Resolution.MINUTE, fill_forward=False, extended_market_hours=True,
                                data_normalization_mode=DataNormalizationMode.BACKWARDS_PANAMA_CANAL,
                                data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
            self.fut[key] = s.symbol
        self.spx = self.add_index('SPX', Resolution.DAILY).symbol
        self.ndx = self.add_index('NDX', Resolution.DAILY).symbol
        self.vix = self.add_index('VIX', Resolution.DAILY).symbol
        self.opts = {}
        for key, idx, tickers in (('SPX', self.spx, (None, 'SPXW')), ('NDX', self.ndx, (None, 'NDXP'))):
            syms = []
            for tk in tickers:
                o = self.add_index_option(idx, Resolution.DAILY) if tk is None else self.add_index_option(idx, tk, Resolution.DAILY)
                o.set_filter(lambda u: u.strikes(0, 0).expiration(0, 0))   # we read the full chain via option_chain
                syms.append(o.symbol)
            self.opts[key] = syms
        self.days = {}          # date -> dict
        self.cur = None
        self.diag = {'chain_sizes': [], 'probe': [], 'opt_seconds': 0.0, 'errors': []}
        self.schedule.on(self.date_rules.every_day(self.spx), self.time_rules.at(9, 25), self.morning)

    def chain_rows(self, canon_list):
        rows, seen, spot, cols = [], set(), None, None
        for canon in canon_list:
            df = self.option_chain(canon, flatten=True).data_frame
            if df is None or len(df) == 0:
                continue
            c_oi = _col(df, 'openinterest')
            c_g = _col(df, 'gamma')
            c_r = _col(df, 'right')
            c_u = _col(df, 'underlyinglastprice')
            cols = [str(c) for c in df.columns]
            if c_oi is None or c_g is None or c_r is None:
                self.diag['errors'].append(['columns', cols[:30]])
                continue
            if spot is None and c_u is not None:
                try:
                    spot = float(df[c_u].iloc[0])
                except Exception:
                    spot = None
            for sym, oi, g, r in zip(df.index, df[c_oi].values, df[c_g].values, df[c_r].values):
                k = str(sym)
                if k in seen:
                    continue
                seen.add(k)
                try:
                    is_call = (int(r) == 0) if not isinstance(r, str) else r.lower().startswith('c')
                    rows.append((is_call, float(oi), float(g)))
                except Exception:
                    continue
        return rows, spot, cols

    def morning(self):
        t0 = _time.time()
        d = self.time.date()
        rec = self.days.setdefault(d, {'hi': {}, 'lo': {}, 'n': {}})
        vix = self.securities[self.vix].price
        rec['vix'] = float(vix) if vix else None
        for key, idx in (('SPX', self.spx), ('NDX', self.ndx)):
            try:
                rows, spot, cols = self.chain_rows(self.opts[key])
                if not spot:
                    spot = float(self.securities[idx].price) or None
                net, ab, n = gex_from_rows(rows, spot)
                rec[key] = (net, ab, n)
                if key == 'SPX':
                    self.diag['chain_sizes'].append(n)
                if YEAR == 0 and len(self.diag['probe']) < 12:
                    hist = self.history(idx, 3, Resolution.DAILY)
                    closes = [[str(i[-1] if isinstance(i, tuple) else i), float(v)] for i, v in hist['close'].items()] if len(hist) else []
                    self.diag['probe'].append({'algo_time': str(self.time), 'root': key, 'contracts': n, 'chain_spot': spot,
                                               'index_price': float(self.securities[idx].price), 'last_closes': closes,
                                               'gex': net, 'abs': ab, 'cols': cols[:40] if cols else None})
            except Exception as e:
                rec[key] = (None, None, 0)
                if len(self.diag['errors']) < 10:
                    self.diag['errors'].append([str(d), key, str(e)[:200]])
        self.diag['opt_seconds'] += _time.time() - t0

    def on_data(self, data):
        t = self.time
        if not rth_index(t):
            return
        rec = self.days.setdefault(t.date(), {'hi': {}, 'lo': {}, 'n': {}})
        for key, sym in self.fut.items():
            tb = data.bars.get(sym)
            if tb is None:
                continue
            h, l = float(tb.high), float(tb.low)
            rec['hi'][key] = max(rec['hi'].get(key, h), h)
            rec['lo'][key] = min(rec['lo'].get(key, l), l)
            rec['n'][key] = rec['n'].get(key, 0) + 1

    def on_end_of_algorithm(self):
        out = bytearray()
        nd = 0
        for d in sorted(self.days):
            r = self.days[d]
            if 'SPX' not in r and not r['n']:
                continue
            rng = {k: int(round((r['hi'][k] - r['lo'][k]) / TICK)) if k in r['hi'] else 0 for k in ('NQ', 'ES')}
            spx = r.get('SPX', (None, None, 0))
            ndx = r.get('NDX', (None, None, 0))
            fl = flags_of(r['n'].get('NQ', 0), r['n'].get('ES', 0), spx[2], ndx[2], r.get('vix'))
            out += pack((d - date(self.year0, 1, 1)).days, rng['NQ'], rng['ES'], spx[0], spx[1], ndx[0], ndx[1],
                        r.get('vix'), fl)
            nd += 1
        cs = self.diag['chain_sizes']
        res = {'year': YEAR, 'year0': self.year0, 'days': nd, 'rec': base64.b64encode(bytes(out)).decode(),
               'spx_contracts_mean': round(sum(cs) / len(cs), 1) if cs else 0, 'spx_contracts_min': min(cs) if cs else 0,
               'opt_seconds': round(self.diag['opt_seconds'], 1), 'errors': self.diag['errors'][:10]}
        if YEAR == 0:
            res['probe'] = self.diag['probe']
        log_chunks(self, 'NEXA_GEX', res)
