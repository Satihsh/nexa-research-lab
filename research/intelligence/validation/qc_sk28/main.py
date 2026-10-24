# NEXA H-SK28-OOS adapter. Pre-registration: PREREG_SK28_OOS.md.
# Runs the frozen s-k-28 pipeline (commit 0ee4392d, 25 files uploaded unchanged next to this file) on QuantConnect
# NQ minute bars for one half-year chunk: bars from the chunk start - 120 days to the chunk end, exactly as run_multi.py:
# load_csv -> build_daily_bars -> MultiModelGenerator.generate -> BacktestEngineV2.run. Keeps trades entered inside
# the chunk window, simulates each trade's mirror once (random-direction control) and logs one compact record per
# trade; statistics and the gate matching are computed locally (sk28_stats.py). Reads data only; no orders.
from AlgorithmImports import *
import io
import json
import time as _time
from dataclasses import replace
from datetime import date, datetime, timedelta

YEAR, HALF = 2023, 1        # the only line that changes between chunks (HALF 1 = Jan-Jun, 2 = Jul-Dec)
TICK = 0.25
WARMUP_DAYS = 120
P_FROM, P_TO = date(2010, 1, 4), date(2022, 12, 23)
IN_FROM, IN_TO = date(2023, 1, 3), date(2025, 11, 28)
MODELS = ['ou_rev', 'pd_rev', 'vwap_rev', 'or_rev', 'ou_lunch', 'vwap_scalp', 'open_drive', 'trend', 'pm_mom',
          'ema_rev', 'kalman_mom', 'sweep']
REASONS = ['target', 'stop', 'stop_ambiguous', 'breakeven', 'trail', 'time_stop', 'session_close', 'end_of_data']
B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
R_LIM = 2047                # R stored in hundredths, 12 bits signed (+-20.47R); clamps are counted
MATCH_MIN = 2


def window(year, half):
    """(first entry date, last entry date) kept for a half-year chunk."""
    lo, hi = (date(year, 1, 1), date(year, 6, 30)) if half == 1 else (date(year, 7, 1), date(year, 12, 31))
    if year <= P_TO.year:
        return max(lo, P_FROM), min(hi, P_TO)
    return max(lo, IN_FROM), min(hi, IN_TO)


def data_range(year, half):
    """Bars from 120 days before the chunk's first calendar day to its last entry date."""
    first = date(year, 1, 1) if half == 1 else date(year, 7, 1)
    return first - timedelta(days=WARMUP_DAYS), window(year, half)[1]


def bars_to_csv(rows):
    """rows: (bar end datetime ET, o, h, l, c, v) -> CSV text in their column layout (read by their load_csv)."""
    out = ['timestamp ET,open,high,low,close,volume']
    for t, o, h, l, c, v in rows:
        out.append('%s,%r,%r,%r,%r,%d' % (t.strftime('%Y-%m-%d %H:%M'), o, h, l, c, int(v)))
    return '\n'.join(out) + '\n'


def run_frozen(csv_text):
    """The run_multi.py pipeline on in-memory bars. Returns (trades, n_signals, raw df, engine)."""
    from config import Config
    from data.loader import load_csv, build_daily_bars
    from strategy.multi import MultiModelGenerator
    from backtest.engine_v2 import BacktestEngineV2
    import pandas as pd
    cfg = Config()
    raw = load_csv(io.StringIO(csv_text), 'NQ')
    daily = build_daily_bars(raw)
    daily['date'] = pd.to_datetime(daily['date']).dt.date
    signals = MultiModelGenerator(cfg).generate(raw, daily, None)
    eng = BacktestEngineV2(cfg)
    return eng.run(raw, signals), len(signals), raw, eng


def mirror_signal(sig):
    """Opposite direction, stop and target reflected around the signal's entry price, same risk profile."""
    e = sig.entry
    return replace(sig, direction='short' if sig.direction == 'long' else 'long',
                   stop=2 * e - sig.stop, target=2 * e - sig.target)


def ticks(x):
    return int(round(x / TICK))


def enc_r(r, clamps):
    v = int(round(r * 100))
    if abs(v) > R_LIM:
        clamps[0] += 1
        v = max(-R_LIM, min(R_LIM, v))
    return v + R_LIM + 1          # 0..4095


def encode(rec):
    """66 bits -> 11 chars: day offset 9, minute 11, model 4, dir 1, reason 3, R 12, risk ticks 7, mR 12, m risk 7."""
    fields = [(rec['doy'], 9), (rec['minute'], 11), (rec['model'], 4), (rec['dir'], 1), (rec['reason'], 3),
              (rec['r'], 12), (rec['risk_t'], 7), (rec['mr'], 12), (rec['mrisk_t'], 7)]
    x = 0
    for v, nb in fields:
        assert 0 <= v < (1 << nb), (v, nb)
        x = (x << nb) | v
    return ''.join(B64[(x >> (6 * (10 - i))) & 63] for i in range(11))


def decode(s):
    x = 0
    for ch in s:
        x = (x << 6) | B64.index(ch)
    out = {}
    for name, nb in reversed([('doy', 9), ('minute', 11), ('model', 4), ('dir', 1), ('reason', 3), ('r', 12),
                              ('risk_t', 7), ('mr', 12), ('mrisk_t', 7)]):
        out[name] = x & ((1 << nb) - 1)
        x >>= nb
    return out


def trade_record(t, m, year, clamps):
    """t: the real Trade; m: its mirror Trade or None (refused)."""
    et = t.entry_time.to_pydatetime() if hasattr(t.entry_time, 'to_pydatetime') else t.entry_time
    rec = {'doy': (et.date() - date(year, 1, 1)).days, 'minute': et.hour * 60 + et.minute,
           'model': MODELS.index(t.model), 'dir': 1 if t.direction == 'long' else 0,
           'reason': REASONS.index(t.exit_reason), 'r': enc_r(t.total_r, clamps),
           'risk_t': min(127, ticks(t.risk)), 'mr': R_LIM + 1, 'mrisk_t': 0}
    if m is not None:
        rec['mr'] = enc_r(m.total_r, clamps)
        rec['mrisk_t'] = max(1, min(127, ticks(m.risk)))
    return rec


def parse_ref(ref, lo, hi):
    """REF string -> [(entry datetime, model index, 'L'/'S')] inside [lo, hi]."""
    out = []
    for item in ref.split(';') if ref else []:
        ts, mi, side = item.split(',')
        t = datetime.strptime(ts, '%Y%m%d%H%M')
        if lo <= t.date() <= hi:
            out.append((t, int(mi), side))
    return out


def match_ref(ref_rows, qc_rows):
    """Greedy one-to-one matching: same model and side, entry within +-MATCH_MIN minutes (nearest first).
    qc_rows: [(entry datetime, model index, 'L'/'S')]. Returns (matched, per-model {model: [ref_n, matched]})."""
    used = set()
    per = {}
    matched = 0
    for t, mi, side in ref_rows:
        per.setdefault(mi, [0, 0])
        per[mi][0] += 1
        best, bd = None, None
        for j, (u, mj, sj) in enumerate(qc_rows):
            if j in used or mj != mi or sj != side:
                continue
            d = abs((u - t).total_seconds()) / 60.0
            if d <= MATCH_MIN and (bd is None or d < bd):
                best, bd = j, d
        if best is not None:
            used.add(best)
            matched += 1
            per[mi][1] += 1
    return matched, per


def first_eth_check(rows):
    """Sessions whose first bar at/after 18:00 ET is labelled 18:01 (end-labelled bars) vs others."""
    seen, ok, other = set(), 0, 0
    for t, *_ in rows:
        if t.hour >= 18 and t.date() not in seen:
            seen.add(t.date())
            if t.hour == 18 and t.minute == 1:
                ok += 1
            else:
                other += 1
    return ok, other


def rth_bitmap(rows, year):
    """Base64 bitmap of the days of the year (offset from 1 Jan) that have any 09:31-16:00 ET bar."""
    days = set()
    for t, *_ in rows:
        if t.year == year and ((t.hour == 9 and t.minute >= 31) or 10 <= t.hour < 16 or (t.hour == 16 and t.minute == 0)):
            days.add((t.date() - date(year, 1, 1)).days)
    bits = [1 if d in days else 0 for d in range(372)]           # 62 chars x 6 bits
    return ''.join(B64[int(''.join(map(str, bits[i:i + 6])), 2)] for i in range(0, 372, 6))


def chunk_result(rows, year, half, ref=None):
    """Everything one backtest logs, from its bars. Pure function (unit-tested locally on synthetic bars)."""
    t0 = _time.time()
    lo, hi = window(year, half)
    trades, n_sig, raw, eng = run_frozen(bars_to_csv(rows))
    kept = [t for t in trades if lo <= t.entry_time.date() <= hi]
    clamps = [0]
    recs, refused = [], 0
    for t in kept:
        m = eng._sim(raw, mirror_signal(t.signal))
        refused += m is None
        recs.append(trade_record(t, m, year, clamps))
    ok, other = first_eth_check(rows)
    out = {'year': year, 'half': half, 'window': [str(lo), str(hi)], 'bars': len(rows),
           'first_bar': str(rows[0][0]) if rows else None, 'last_bar': str(rows[-1][0]) if rows else None,
           'signals': n_sig, 'trades_all': len(trades), 'trades': len(kept), 'mirror_refused': refused,
           'r_clamped': clamps[0], 'eth_1801': [ok, other], 'rth_days': rth_bitmap(rows, year),
           'gross_mean': round(sum(t.total_r for t in kept) / len(kept), 4) if kept else None,
           'S1_mean': round(sum(t.total_r - 2.0 / t.risk for t in kept) / len(kept), 4) if kept else None,
           'tr': ''.join(encode(r) for r in recs)}
    if ref is not None:
        qc_rows = [(t.entry_time.to_pydatetime() if hasattr(t.entry_time, 'to_pydatetime') else t.entry_time,
                    MODELS.index(t.model), 'L' if t.direction == 'long' else 'S') for t in kept]
        ref_rows = parse_ref(ref, lo, hi)
        matched, per = match_ref(ref_rows, qc_rows)
        out['gate'] = {'ref_n': len(ref_rows), 'qc_n': len(qc_rows), 'matched': matched,
                       'per_model': {MODELS[k]: v for k, v in sorted(per.items())}}
    out['seconds'] = round(_time.time() - t0, 1)
    return out


def log_chunks(algo, tag, obj, size=7000):
    s = json.dumps(obj, separators=(',', ':'))
    parts = [s[i:i + size] for i in range(0, len(s), size)] or ['']
    for i, p in enumerate(parts):
        algo.log(f'{tag} {i + 1}/{len(parts)} {p}')


# ---------------------------------------------------------------- algorithm (reads data only, never trades)
class NexaSk28(QCAlgorithm):
    def initialize(self):
        a, b = data_range(YEAR, HALF)
        self.set_start_date(a.year, a.month, a.day)
        self.set_end_date(b.year, b.month, b.day)
        self.set_time_zone(TimeZones.NEW_YORK)
        self.set_cash(100000)
        f = self.add_future(Futures.Indices.NASDAQ_100_E_MINI, Resolution.MINUTE, fill_forward=False,
                            extended_market_hours=True,
                            data_normalization_mode=DataNormalizationMode.BACKWARDS_PANAMA_CANAL,
                            data_mapping_mode=DataMappingMode.OPEN_INTEREST, contract_depth_offset=0)
        self.sym = f.symbol
        self.rows = []

    def on_data(self, data):
        tb = data.bars.get(self.sym)
        if tb is not None:
            # self.time = bar END in New York time, the same labelling as their file (first ETH bar 18:01)
            self.rows.append((self.time, float(tb.open), float(tb.high), float(tb.low), float(tb.close),
                              float(tb.volume)))

    def on_end_of_algorithm(self):
        # gate matching is done locally from the per-trade records (DEVIATIONS D3); ref stays for offline checks
        log_chunks(self, 'NEXA_SK28', chunk_result(self.rows, YEAR, HALF))
