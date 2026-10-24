#!/usr/bin/env python3
"""H-ORB30L-REPL Part A-D: out-of-sample replication of the FROZEN H-ORB30L-NQ rule on free Dukascopy
USATECH.IDX/USD M1 bid/ask history (PREREG_HORB30L_REPL_DUKA.md). Read-only research; never trades.

Stages (each refuses to overwrite its output):
  manifest  hash the raw exports in data/raw/dukascopy/USATECH.IDX-USD/ -> MANIFEST.json (timestamps only)
  parity    IN-SAMPLE ONLY (2023-02-21..2023-12-29): Dukascopy mid vs the in-sample NQ file, same frozen engine;
            every Dukascopy row before NY 2023-02-18 is discarded at load time -> horb30l_duka_parity.json
  oos       ONCE, only if parity passed: NY days <= 2023-02-17 -> horb30l_duka_oos_results.json
Usage:  python3 horb30l_duka_oos.py --stage manifest|parity|oos
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import of_common as oc  # noqa: E402  (read-only: bootstrap, boot_summary)
import horb1_orb as hb  # noqa: E402  (read-only: clock, frozen calendar, event days)
import hivb1_nq as iv  # noqa: E402  (read-only: DV loader)
import horb30l_nq as orb  # noqa: E402  (FROZEN engine, sha 7d4095bc)
import forward_horb30l as fw  # noqa: E402  (executable variant, as Part B)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RAW = os.path.join(ROOT, 'data', 'raw', 'dukascopy', 'USATECH.IDX-USD')
MANIFEST = os.path.join(RAW, 'MANIFEST.json')
PARITY_OUT = os.path.join(HERE, 'horb30l_duka_parity.json')
OOS_OUT = os.path.join(HERE, 'horb30l_duka_oos_results.json')

CUTOFF_NY = pd.Timestamp('2023-02-18 00:00', tz='America/New_York')   # first in-sample NY day
OOS_LAST = date(2023, 2, 17)
PAR_LO, PAR_HI = date(2023, 2, 21), date(2023, 12, 29)
FROZEN_CAL_FROM = date(2017, 1, 1)
SEED = 20261015
B_BOOT = 2000
MIN_TRADES = 300
STALE_FRAC = 0.20
S1 = orb.COST['S1']
PARITY_RULES = {'P1_status_agree': 0.80, 'P2a_entry_min_agree': 0.75, 'P2b_exit_kind_agree': 0.75,
                'P3_R_corr': 0.75}
TIME_FORMATS = ('%d.%m.%Y %H:%M:%S.%f', '%d.%m.%Y %H:%M:%S', '%Y.%m.%d %H:%M:%S.%f', '%Y.%m.%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S')


# ----------------------------------------------------------------------------- raw files
def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def raw_files(raw: str = RAW) -> dict:
    """{path: 'bid'|'ask'} for every CSV export; the side must be named in the file name."""
    out = {}
    for p in sorted(glob.glob(os.path.join(raw, '*.csv')) + glob.glob(os.path.join(raw, '*.csv.gz'))):
        n = os.path.basename(p).lower()
        sides = [s for s in ('bid', 'ask') if s in n]
        if len(sides) != 1:
            raise SystemExit(f'REFUSED: cannot tell BID/ASK from file name {os.path.basename(p)!r}')
        out[p] = sides[0]
    if not out:
        raise SystemExit(f'REFUSED: no CSV exports in {raw}')
    if set(out.values()) != {'bid', 'ask'}:
        raise SystemExit('REFUSED: need both BID and ASK exports')
    return out


def read_raw(path: str) -> pd.DataFrame:
    """Dukascopy CSV (JForex Historical Data Manager / web export) -> DataFrame[t (UTC), open, high, low, close,
    volume]. The time column header must say UTC or GMT; the format must parse every row strictly."""
    df = pd.read_csv(path)
    tcol = df.columns[0]
    if 'utc' not in tcol.lower() and 'gmt' not in tcol.lower():
        raise SystemExit(f'REFUSED: {os.path.basename(path)}: time column {tcol!r} does not say UTC/GMT')
    s = df[tcol].astype(str).str.strip().str.replace(r'\s*(GMT|UTC)([+-]00:?00)?$', '', regex=True)
    t = None
    for fmt in TIME_FORMATS:
        x = pd.to_datetime(s, format=fmt, errors='coerce')
        if x.notna().all():
            t = x
            break
    if t is None:
        raise SystemExit(f'REFUSED: {os.path.basename(path)}: unknown time format, e.g. {s.iloc[0]!r}')
    cols = {c.lower().strip(): c for c in df.columns}
    for k in ('open', 'high', 'low', 'close'):
        if k not in cols:
            raise SystemExit(f'REFUSED: {os.path.basename(path)}: no {k} column')
    out = pd.DataFrame({'t': t.dt.tz_localize('UTC')} |
                       {k: df[cols[k]].astype(float) for k in ('open', 'high', 'low', 'close')})
    out['volume'] = df[cols['volume']].astype(float) if 'volume' in cols else 0.0
    return out


def write_manifest(raw: str = RAW) -> dict:
    if os.path.exists(os.path.join(raw, 'MANIFEST.json')):
        sys.exit('REFUSED: MANIFEST.json exists (raw exports are frozen)')
    files = {}
    for p, side in raw_files(raw).items():
        df = read_raw(p)
        files[os.path.basename(p)] = {'side': side, 'sha256': sha256(p), 'rows': int(len(df)),
                                      'first_utc': df.t.min().isoformat(), 'last_utc': df.t.max().isoformat()}
    m = {'instrument': 'USATECH.IDX/USD', 'timeframe': 'M1', 'files': files,
         'note': 'timestamps only were read to build this manifest; no price statistic computed'}
    with open(os.path.join(raw, 'MANIFEST.json'), 'w') as f:
        json.dump(m, f, indent=1)
    return m


def verify_manifest(raw: str = RAW) -> dict:
    mp = os.path.join(raw, 'MANIFEST.json')
    if not os.path.exists(mp):
        sys.exit('REFUSED: run --stage manifest first')
    m = json.load(open(mp))
    now = {os.path.basename(p): sha256(p) for p in raw_files(raw)}
    if now != {k: v['sha256'] for k, v in m['files'].items()}:
        sys.exit('REFUSED: raw exports differ from MANIFEST.json')
    return m


def load_side(paths: list, lo=None, hi=None) -> tuple:
    """Concatenate one side; keep rows with lo <= t < hi (UTC-aware Timestamps) BEFORE anything else is done."""
    parts = []
    for p in paths:
        df = read_raw(p)
        if lo is not None:
            df = df[df.t >= lo]
        if hi is not None:
            df = df[df.t < hi]
        parts.append(df)
    df = pd.concat(parts, ignore_index=True).sort_values('t', kind='stable')
    n = len(df)
    df = df.drop_duplicates('t', keep='first')
    return df.set_index('t'), {'rows': int(n), 'duplicates_dropped': int(n - len(df))}


def to_dv(df: pd.DataFrame):
    ny = df.index.tz_convert('America/New_York').tz_localize(None)
    f = df.reset_index(drop=True).assign(time_server=(ny + pd.Timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'))
    return iv.from_frame(f)


def load(raw: str = RAW, lo=None, hi=None) -> tuple:
    """-> (mid, bid, ask) DVs on minutes present on both sides, plus an audit."""
    files = raw_files(raw)
    bid, ab = load_side([p for p, s in files.items() if s == 'bid'], lo, hi)
    ask, aa = load_side([p for p, s in files.items() if s == 'ask'], lo, hi)
    common = bid.index.intersection(ask.index)
    bid, ask = bid.loc[common], ask.loc[common]
    mid = (bid + ask) / 2.0
    audit = {'bid': ab, 'ask': aa, 'minutes_both_sides': int(len(common)),
             'first_utc': common.min().isoformat() if len(common) else None,
             'last_utc': common.max().isoformat() if len(common) else None,
             'ask_below_bid_minutes': int((ask.close < bid.close).sum())}
    return to_dv(mid), to_dv(bid), to_dv(ask), audit


# ----------------------------------------------------------------------------- calendar and day quality (§2)
def easter(y: int) -> date:
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    return date(y, month, (h + l_ - 7 * m + 114) % 31 + 1)


def nth_weekday(y: int, month: int, wd: int, n: int) -> date:
    d = date(y, month, 1)
    d += timedelta(days=(wd - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def last_weekday(y: int, month: int, wd: int) -> date:
    d = date(y, month + 1, 1) - timedelta(days=1) if month < 12 else date(y, 12, 31)
    return d - timedelta(days=(d.weekday() - wd) % 7)


def observed(d: date, sat_to_fri: bool = True) -> date | None:
    if d.weekday() == 5:
        return d - timedelta(days=1) if sat_to_fri else None
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def rule_calendar(y: int) -> set:
    """§2 rule calendar (used only for dates before 2017-01-01)."""
    thanks = nth_weekday(y, 11, 3, 4)
    days = {observed(date(y, 1, 1), sat_to_fri=False), nth_weekday(y, 1, 0, 3), nth_weekday(y, 2, 0, 3),
            easter(y) - timedelta(days=2), last_weekday(y, 5, 0), observed(date(y, 7, 4)), nth_weekday(y, 9, 0, 1),
            thanks, observed(date(y, 12, 25)), nth_weekday(y, 10, 0, 2), observed(date(y, 11, 11)),
            thanks + timedelta(days=1)}
    for d in (date(y, 7, 3), date(y, 12, 24), date(y, 12, 31)):
        if d.weekday() < 5:
            days.add(d)
    if y == 2012:
        days |= {date(2012, 10, 29), date(2012, 10, 30)}
    return {d for d in days if d is not None}


def oos_calendar(years) -> set:
    frozen, _, _ = hb.calendar()
    rules = set().union(*(rule_calendar(y) for y in years if y < FROZEN_CAL_FROM.year)) if years else set()
    return {d for d in frozen if d >= FROZEN_CAL_FROM} | {d for d in rules if d < FROZEN_CAL_FROM}


def covered(D, d) -> bool:
    return all(D.at(hb.utc_of(d, m)) >= 0 for m in list(range(orb.RANGE_START, orb.RANGE_START + orb.RANGE_LEN))
               + [orb.EXIT_MIN])


def stale(D, d) -> bool:
    """>= 20 % of the 360 minutes 09:30-15:29 missing or flat repeats (O = H = L = C = previous close)."""
    k0 = D.at(hb.utc_of(d, orb.RANGE_START - 1))
    prev = float(D.c[k0]) if k0 >= 0 else None
    bad = 0
    for m in range(orb.RANGE_START, orb.EXIT_MIN + 1):
        k = D.at(hb.utc_of(d, m))
        if k < 0:
            bad, prev = bad + 1, None
            continue
        o, h, l_, c = float(D.o[k]), float(D.h[k]), float(D.l[k]), float(D.c[k])
        if prev is not None and o == h == l_ == c == prev:
            bad += 1
        prev = c
    return bad >= STALE_FRAC * (orb.EXIT_MIN + 1 - orb.RANGE_START)


def eligible(D, cal: set, lo: date | None, hi: date) -> tuple:
    days, aud, stale_by_year = [], {'weekdays': 0, 'calendar': 0, 'not_covered': 0, 'stale': 0}, {}
    for d in D.days():
        if d > hi or (lo is not None and d < lo):
            continue
        aud['weekdays'] += 1
        if d in cal:
            aud['calendar'] += 1
        elif not covered(D, d):
            aud['not_covered'] += 1
        elif stale(D, d):
            aud['stale'] += 1
            stale_by_year[d.year] = stale_by_year.get(d.year, 0) + 1
        else:
            days.append(d)
    return days, aud | {'stale_by_year': stale_by_year, 'used': len(days)}


# ----------------------------------------------------------------------------- statistics
def boot(x) -> dict:
    v = np.asarray(x, float)
    if len(v) < 2:
        return {'theta': float(v.mean()) if len(v) else None, 'ci95': [None, None], 'p_one_sided': None, 'n': len(v)}
    reps = oc.bootstrap(lambda idx: float(v[idx].mean()), len(v), B=B_BOOT, seed=SEED)
    return oc.boot_summary(float(v.mean()), reps) | {'n': int(len(v))}


def acceptance(n: int, m1: dict, diff, yc: dict) -> dict:
    checks = {
        '1_mean>0_ci_lo>0': bool((m1.get('theta') or 0) > 0 and (m1.get('ci95') or [None])[0] is not None
                                 and m1['ci95'][0] > 0),
        '2_primary_minus_N2>0': bool(diff is not None and diff > 0),
        '3_years_pos>=60%_and_no_year>25%': bool((yc.get('share_years_positive') or 0) >= 0.60
                                                 and yc.get('max_year_share') is not None
                                                 and yc['max_year_share'] <= 0.25),
    }
    if n < MIN_TRADES:
        verdict = 'INSUFFICIENT-N'
    elif (m1.get('theta') or 0) <= 0:
        verdict = 'FAILED'
    elif all(checks.values()):
        verdict = 'REPLICATED'
    else:
        verdict = 'NOT REPLICATED'
    return {'checks': checks, 'verdict': verdict, 'n_trades_S1': n}


# ----------------------------------------------------------------------------- stages
def parity(raw: str = RAW, nq=None) -> dict:
    if os.path.exists(PARITY_OUT):
        sys.exit('REFUSED: horb30l_duka_parity.json exists (opened once)')
    man = verify_manifest(raw)
    Dm, Db, Da, aud = load(raw, lo=CUTOFF_NY.tz_convert('UTC'))           # pre-cutoff rows never loaded
    Dn = nq if nq is not None else iv.load(iv.DATA)
    hol, _, _ = hb.calendar()
    days = [d for d in Dm.days() if PAR_LO <= d <= PAR_HI and d not in hol and covered(Dm, d)
            and not stale(Dm, d) and covered(Dn, d)]
    rows = []
    for d in days:
        a, b = orb.simulate(Dm, d, cost=S1), orb.simulate(Dn, d, cost=S1)
        ka, kn = Dm.at(hb.utc_of(d, 600)), Dn.at(hb.utc_of(d, 600))
        kb, kk = Db.at(hb.utc_of(d, 600)), Da.at(hb.utc_of(d, 600))
        kb2, kk2 = Db.at(hb.utc_of(d, orb.EXIT_MIN)), Da.at(hb.utc_of(d, orb.EXIT_MIN))
        rows.append({'day': d.isoformat(), 'st_d': a['status'], 'st_n': b['status'],
                     'em_d': a.get('entry_min'), 'em_n': b.get('entry_min'), 'x_d': a.get('exit_kind'),
                     'x_n': b.get('exit_kind'), 'R_d': a.get('R'), 'R_n': b.get('R'),
                     'offset_1000': float(Dm.o[ka] - Dn.o[kn]) if ka >= 0 and kn >= 0 else None,
                     'spread_1000': float(Da.o[kk] - Db.o[kb]) if kb >= 0 and kk >= 0 else None,
                     'spread_1529': float(Da.c[kk2] - Db.c[kb2]) if kb2 >= 0 and kk2 >= 0 else None})
    df = pd.DataFrame(rows)
    both = df[(df.st_d == 'trade') & (df.st_n == 'trade')] if len(df) else df
    m = {'P1_status_agree': float((df.st_d == df.st_n).mean()) if len(df) else None,
         'P2a_entry_min_agree': float((both.em_d == both.em_n).mean()) if len(both) else None,
         'P2b_exit_kind_agree': float((both.x_d == both.x_n).mean()) if len(both) else None,
         'P3_R_corr': float(np.corrcoef(both.R_d.astype(float), both.R_n.astype(float))[0, 1])
         if len(both) > 2 else None}
    passed = {k: bool(m[k] is not None and np.isfinite(m[k]) and m[k] >= thr) for k, thr in PARITY_RULES.items()}
    tr_d, tr_n = df[df.st_d == 'trade'], df[df.st_n == 'trade']
    out = {'stage': 'parity (in-sample only)', 'window': [PAR_LO.isoformat(), PAR_HI.isoformat()],
           'manifest_files': sorted(man['files']), 'load_audit': aud, 'n_days': int(len(df)),
           'n_both_trade': int(len(both)), 'metrics': m, 'thresholds': PARITY_RULES, 'checks': passed,
           'PASS': bool(len(df) and all(passed.values())),
           'descriptive': {'mean_R_S1_dukascopy': float(tr_d.R_d.mean()) if len(tr_d) else None,
                           'n_trades_dukascopy': int(len(tr_d)),
                           'mean_R_S1_nq': float(tr_n.R_n.mean()) if len(tr_n) else None,
                           'n_trades_nq': int(len(tr_n)),
                           'median_offset_mid_minus_nq_1000': float(df.offset_1000.dropna().median())
                           if len(df) and df.offset_1000.notna().any() else None,
                           'median_spread_1000': float(df.spread_1000.dropna().median())
                           if len(df) and df.spread_1000.notna().any() else None,
                           'median_spread_1529': float(df.spread_1529.dropna().median())
                           if len(df) and df.spread_1529.notna().any() else None,
                           'status_crosstab': (pd.crosstab(df.st_d, df.st_n).to_dict() if len(df) else {})}}
    with open(PARITY_OUT, 'w') as f:
        json.dump(out, f, indent=1, default=str)
    return out


def oos(raw: str = RAW, battery: bool = True) -> dict:
    if os.path.exists(OOS_OUT):
        sys.exit('REFUSED: horb30l_duka_oos_results.json exists (opened once)')
    if not os.path.exists(PARITY_OUT):
        sys.exit('REFUSED: run --stage parity first')
    par = json.load(open(PARITY_OUT))
    if not par.get('PASS'):
        sys.exit('REFUSED: parity FAILED -> Part A-D NOT EVALUABLE (no OOS day is read)')
    man = verify_manifest(raw)
    Dm, Db, Da, aud = load(raw, hi=CUTOFF_NY.tz_convert('UTC'))           # in-sample rows never loaded
    alld = Dm.days()
    cal = oos_calendar(sorted({d.year for d in alld}))
    days, day_aud = eligible(Dm, cal, None, OOS_LAST)
    per, counts, floor_by_year = [], {}, {}
    for d in days:
        r = orb.simulate(Dm, d, cost=S1)
        counts[r['status']] = counts.get(r['status'], 0) + 1
        if r['status'] == 'cost_floor':
            floor_by_year[d.year] = floor_by_year.get(d.year, 0) + 1
        if r['status'] == 'trade':
            per.append((d, r))
    out = {'stage': 'oos', 'manifest_files': sorted(man['files']), 'load_audit': aud, 'day_audit': day_aud,
           'first_day': days[0].isoformat() if days else None, 'last_day': days[-1].isoformat() if days else None,
           'rule_calendar_pre2017': sorted(x.isoformat() for x in cal if x < FROZEN_CAL_FROM),
           'counts_S1': counts, 'cost_floor_by_year': floor_by_year}
    fr = {}
    for lvl, cst in orb.COST.items():
        df, _ = orb.frame(Dm, days, cost=cst)
        fr[lvl] = df
        out[lvl] = {'mean_R': boot(df.R) if len(df) else None,
                    'mean_pts': float(df.pnl_pts.mean()) if len(df) else None,
                    'win_rate': float((df.R > 0).mean()) if len(df) else None,
                    'exits': df.exit_kind.value_counts().to_dict() if len(df) else {}}
    s1 = fr['S1']
    n2, n2c = orb.frame(Dm, days, cost=S1, n2=True)
    diff = (float(s1.R.mean()) - float(n2.R.mean())) if len(s1) and len(n2) else None
    out['N2_beta_control'] = (boot(n2.R) if len(n2) else {}) | {'counts': n2c, 'primary_minus_N2': diff}
    r2, _ = orb.frame(Dm, days, cost=S1, target_r=2.0)
    out['secondary_2R_S1'] = boot(r2.R) if len(r2) else None
    yc = orb.year_check(s1)
    out['year_check_S1'] = yc
    out['by_year_S1'] = ({int(y): {'n': int(len(g)), 'mean_R': float(g.R.mean()), 'sum_R': float(g.R.sum())}
                          for y, g in s1.groupby('year')} if len(s1) else {})
    out['median_R_pts'] = float(s1.R_pts.median()) if len(s1) else None
    out['user_goal_S1'] = orb.user_goal(s1, len(days))
    ex = []
    for d, _ in per:
        S = orb.setup(Dm, d)
        x = fw.exec_trade(Db, Da, d, S['entry_min'], S['B'])
        if x['status'] == 'trade':
            ex.append(x['R'])
    out['executable_variant_ask_entry_bid_exit'] = boot(ex) if ex else None
    out['acceptance'] = acceptance(int(counts.get('trade', 0)), out['S1']['mean_R'] or {}, diff, yc)
    out['trades_sha256'] = hashlib.sha256(','.join(f'{r.day}:{r.R:.6f}' for r in s1.itertuples())
                                          .encode()).hexdigest() if len(s1) else None
    if battery:
        try:
            out['descriptive_in_sample_battery'] = orb.analyse(Dm, days, hb.event_days())
        except Exception as e:  # noqa: BLE001
            out['descriptive_in_sample_battery'] = {'error': repr(e)}
    with open(OOS_OUT, 'w') as f:
        json.dump(out, f, indent=1, default=str)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['manifest', 'parity', 'oos'])
    a = ap.parse_args()
    if a.stage == 'manifest':
        print(json.dumps(write_manifest(), indent=1))
    elif a.stage == 'parity':
        r = parity()
        print(json.dumps({k: r[k] for k in ('n_days', 'n_both_trade', 'metrics', 'checks', 'PASS')}, indent=1))
    else:
        r = oos()
        print(json.dumps({'acceptance': r['acceptance'], 'S1': r['S1']['mean_R'],
                          'first_day': r['first_day'], 'last_day': r['last_day']}, indent=1, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
