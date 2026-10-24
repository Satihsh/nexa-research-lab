#!/usr/bin/env python3
"""H-ORB30L-REPL Part A-H: out-of-sample replication of the FROZEN H-ORB30L-NQ rule on free HistData NSXUSD M1
bid data (PREREG_HORB30L_REPL_HISTDATA.md). Read-only research; never trades.

Raw input: data/raw/histdata/NSXUSD/HISTDATA_COM_ASCII_NSXUSD_M1_<year>.zip, each holding
DAT_ASCII_NSXUSD_M1_<year>.csv with rows `YYYYMMDD HHMMSS;open;high;low;close;volume` (BID, EST = UTC-5 fixed).

Stages (each refuses to overwrite its output):
  manifest  hash the zips and their CSVs -> MANIFEST.json (timestamps only)
  parity    IN-SAMPLE ONLY (2023-02-21..2023-12-29) vs the in-sample NQ file; rows before NY 2023-02-18 are
            discarded at load time -> horb30l_histdata_parity.json
  oos       ONCE, only if parity passed: NY days <= 2023-02-17 -> horb30l_histdata_oos_results.json
Usage:  python3 horb30l_histdata_oos.py --stage manifest|parity|oos
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
import os
import sys
import zipfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import horb1_orb as hb  # noqa: E402  (read-only: clock, frozen calendar, event days)
import hivb1_nq as iv  # noqa: E402  (read-only: in-sample NQ loader)
import horb30l_nq as orb  # noqa: E402  (FROZEN engine, sha 7d4095bc)
import horb30l_duka_oos as dk  # noqa: E402  (frozen helpers, sha 95a89207)

RAW = os.path.join(dk.ROOT, 'data', 'raw', 'histdata', 'NSXUSD')
PARITY_OUT = os.path.join(HERE, 'horb30l_histdata_parity.json')
OOS_OUT = os.path.join(HERE, 'horb30l_histdata_oos_results.json')
EST_TO_UTC = pd.Timedelta(hours=5)
S1 = orb.COST['S1']


# ----------------------------------------------------------------------------- raw files
def raw_zips(raw: str = RAW) -> list:
    z = sorted(glob.glob(os.path.join(raw, 'HISTDATA_COM_ASCII_NSXUSD_M1_*.zip')))
    if not z:
        raise SystemExit(f'REFUSED: no HistData NSXUSD zips in {raw}')
    return z


def inner_csv(zf: zipfile.ZipFile) -> str:
    names = [n for n in zf.namelist() if n.upper().startswith('DAT_ASCII_NSXUSD_M1') and n.lower().endswith('.csv')]
    if len(names) != 1:
        raise SystemExit(f'REFUSED: expected one DAT_ASCII_NSXUSD_M1 csv, found {names}')
    return names[0]


def read_zip(path: str) -> tuple:
    """-> (DataFrame[t (UTC), open, high, low, close, volume], inner name, inner sha256)."""
    with zipfile.ZipFile(path) as zf:
        name = inner_csv(zf)
        data = zf.read(name)
    df = pd.read_csv(io.BytesIO(data), sep=';', header=None,
                     names=['ts', 'open', 'high', 'low', 'close', 'volume'], dtype={'ts': str})
    t = pd.to_datetime(df.ts.str.strip(), format='%Y%m%d %H%M%S', errors='coerce')
    if t.isna().any():
        raise SystemExit(f'REFUSED: {os.path.basename(path)}: {int(t.isna().sum())} unparsable timestamps')
    out = pd.DataFrame({'t': (t + EST_TO_UTC).dt.tz_localize('UTC')} |
                       {k: df[k].astype(float) for k in ('open', 'high', 'low', 'close', 'volume')})
    return out, name, hashlib.sha256(data).hexdigest()


def write_manifest(raw: str = RAW) -> dict:
    mp = os.path.join(raw, 'MANIFEST.json')
    if os.path.exists(mp):
        sys.exit('REFUSED: MANIFEST.json exists (raw files are frozen)')
    files = {}
    for p in raw_zips(raw):
        df, name, inner_sha = read_zip(p)
        files[os.path.basename(p)] = {'sha256': dk.sha256(p), 'inner_csv': name, 'inner_sha256': inner_sha,
                                      'rows': int(len(df)), 'first_utc': df.t.min().isoformat(),
                                      'last_utc': df.t.max().isoformat()}
    m = {'source': 'HistData.com generic ASCII M1, NSXUSD, BID, EST without DST', 'files': files,
         'note': 'timestamps only were read to build this manifest; no price statistic computed'}
    with open(mp, 'w') as f:
        json.dump(m, f, indent=1)
    return m


def verify_manifest(raw: str = RAW) -> dict:
    mp = os.path.join(raw, 'MANIFEST.json')
    if not os.path.exists(mp):
        sys.exit('REFUSED: run --stage manifest first')
    m = json.load(open(mp))
    now = {os.path.basename(p): dk.sha256(p) for p in raw_zips(raw)}
    if now != {k: v['sha256'] for k, v in m['files'].items()}:
        sys.exit('REFUSED: raw zips differ from MANIFEST.json')
    return m


def load(raw: str = RAW, lo=None, hi=None) -> tuple:
    """Bid DV with lo <= t < hi applied to every file BEFORE anything else is done."""
    parts = []
    for p in raw_zips(raw):
        df, _, _ = read_zip(p)
        if lo is not None:
            df = df[df.t >= lo]
        if hi is not None:
            df = df[df.t < hi]
        parts.append(df)
    df = pd.concat(parts, ignore_index=True).sort_values('t', kind='stable')
    n = len(df)
    df = df.drop_duplicates('t', keep='first').set_index('t')
    audit = {'rows': int(n), 'duplicates_dropped': int(n - len(df)),
             'first_utc': df.index.min().isoformat() if len(df) else None,
             'last_utc': df.index.max().isoformat() if len(df) else None}
    return dk.to_dv(df), audit


# ----------------------------------------------------------------------------- stages
def parity(raw: str = RAW, nq=None) -> dict:
    if os.path.exists(PARITY_OUT):
        sys.exit('REFUSED: horb30l_histdata_parity.json exists (opened once)')
    man = verify_manifest(raw)
    Dh, aud = load(raw, lo=dk.CUTOFF_NY.tz_convert('UTC'))              # pre-cutoff rows never loaded
    Dn = nq if nq is not None else iv.load(iv.DATA)
    hol, _, _ = hb.calendar()
    days = [d for d in Dh.days() if dk.PAR_LO <= d <= dk.PAR_HI and d not in hol and dk.covered(Dh, d)
            and not dk.stale(Dh, d) and dk.covered(Dn, d)]
    rows = []
    for d in days:
        a, b = orb.simulate(Dh, d, cost=S1), orb.simulate(Dn, d, cost=S1)
        ka, kn = Dh.at(hb.utc_of(d, 600)), Dn.at(hb.utc_of(d, 600))
        rows.append({'day': d.isoformat(), 'st_h': a['status'], 'st_n': b['status'],
                     'em_h': a.get('entry_min'), 'em_n': b.get('entry_min'), 'x_h': a.get('exit_kind'),
                     'x_n': b.get('exit_kind'), 'R_h': a.get('R'), 'R_n': b.get('R'),
                     'offset_1000': float(Dh.o[ka] - Dn.o[kn]) if ka >= 0 and kn >= 0 else None})
    df = pd.DataFrame(rows)
    both = df[(df.st_h == 'trade') & (df.st_n == 'trade')] if len(df) else df
    m = {'P1_status_agree': float((df.st_h == df.st_n).mean()) if len(df) else None,
         'P2a_entry_min_agree': float((both.em_h == both.em_n).mean()) if len(both) else None,
         'P2b_exit_kind_agree': float((both.x_h == both.x_n).mean()) if len(both) else None,
         'P3_R_corr': float(np.corrcoef(both.R_h.astype(float), both.R_n.astype(float))[0, 1])
         if len(both) > 2 else None}
    passed = {k: bool(m[k] is not None and np.isfinite(m[k]) and m[k] >= thr) for k, thr in dk.PARITY_RULES.items()}
    tr_h, tr_n = df[df.st_h == 'trade'] if len(df) else df, df[df.st_n == 'trade'] if len(df) else df
    out = {'stage': 'parity (in-sample only)', 'window': [dk.PAR_LO.isoformat(), dk.PAR_HI.isoformat()],
           'manifest_files': sorted(man['files']), 'load_audit': aud, 'n_days': int(len(df)),
           'n_both_trade': int(len(both)), 'metrics': m, 'thresholds': dk.PARITY_RULES, 'checks': passed,
           'PASS': bool(len(df) and all(passed.values())),
           'descriptive': {'mean_R_S1_histdata': float(tr_h.R_h.mean()) if len(tr_h) else None,
                           'n_trades_histdata': int(len(tr_h)),
                           'mean_R_S1_nq': float(tr_n.R_n.mean()) if len(tr_n) else None,
                           'n_trades_nq': int(len(tr_n)),
                           'median_offset_bid_minus_nq_1000': float(df.offset_1000.dropna().median())
                           if len(df) and df.offset_1000.notna().any() else None,
                           'entry_min_diff_counts': (both.em_h - both.em_n).value_counts().to_dict()
                           if len(both) else {},
                           'status_crosstab': pd.crosstab(df.st_h, df.st_n).to_dict() if len(df) else {}}}
    with open(PARITY_OUT, 'w') as f:
        json.dump(out, f, indent=1, default=str)
    return out


def oos(raw: str = RAW, battery: bool = True) -> dict:
    if os.path.exists(OOS_OUT):
        sys.exit('REFUSED: horb30l_histdata_oos_results.json exists (opened once)')
    if not os.path.exists(PARITY_OUT):
        sys.exit('REFUSED: run --stage parity first')
    if not json.load(open(PARITY_OUT)).get('PASS'):
        sys.exit('REFUSED: parity FAILED -> Part A-H NOT EVALUABLE (no OOS day is read)')
    man = verify_manifest(raw)
    Dh, aud = load(raw, hi=dk.CUTOFF_NY.tz_convert('UTC'))              # in-sample rows never loaded
    cal = dk.oos_calendar(sorted({d.year for d in Dh.days()}))
    days, day_aud = dk.eligible(Dh, cal, None, dk.OOS_LAST)
    counts, floor_by_year = {}, {}
    for d in days:
        r = orb.simulate(Dh, d, cost=S1)
        counts[r['status']] = counts.get(r['status'], 0) + 1
        if r['status'] == 'cost_floor':
            floor_by_year[d.year] = floor_by_year.get(d.year, 0) + 1
    out = {'stage': 'oos', 'source': 'HistData NSXUSD bid', 'manifest_files': sorted(man['files']),
           'load_audit': aud, 'day_audit': day_aud,
           'first_day': days[0].isoformat() if days else None, 'last_day': days[-1].isoformat() if days else None,
           'rule_calendar_pre2017': sorted(x.isoformat() for x in cal if x < dk.FROZEN_CAL_FROM),
           'counts_S1': counts, 'cost_floor_by_year': floor_by_year}
    fr = {}
    for lvl, cst in orb.COST.items():
        df, _ = orb.frame(Dh, days, cost=cst)
        fr[lvl] = df
        out[lvl] = {'mean_R': dk.boot(df.R) if len(df) else None,
                    'mean_pts': float(df.pnl_pts.mean()) if len(df) else None,
                    'win_rate': float((df.R > 0).mean()) if len(df) else None,
                    'exits': df.exit_kind.value_counts().to_dict() if len(df) else {}}
    s1 = fr['S1']
    n2, n2c = orb.frame(Dh, days, cost=S1, n2=True)
    diff = (float(s1.R.mean()) - float(n2.R.mean())) if len(s1) and len(n2) else None
    out['N2_beta_control'] = (dk.boot(n2.R) if len(n2) else {}) | {'counts': n2c, 'primary_minus_N2': diff}
    r2, _ = orb.frame(Dh, days, cost=S1, target_r=2.0)
    out['secondary_2R_S1'] = dk.boot(r2.R) if len(r2) else None
    yc = orb.year_check(s1)
    out['year_check_S1'] = yc
    out['by_year_S1'] = ({int(y): {'n': int(len(g)), 'mean_R': float(g.R.mean()), 'sum_R': float(g.R.sum())}
                          for y, g in s1.groupby('year')} if len(s1) else {})
    out['median_R_pts'] = float(s1.R_pts.median()) if len(s1) else None
    out['user_goal_S1'] = orb.user_goal(s1, len(days))
    out['acceptance'] = dk.acceptance(int(counts.get('trade', 0)), out['S1']['mean_R'] or {}, diff, yc)
    out['trades_sha256'] = hashlib.sha256(','.join(f'{r.day}:{r.R:.6f}' for r in s1.itertuples())
                                          .encode()).hexdigest() if len(s1) else None
    if battery:
        try:
            out['descriptive_in_sample_battery'] = orb.analyse(Dh, days, hb.event_days())
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
        print(json.dumps({k: r[k] for k in ('n_days', 'n_both_trade', 'metrics', 'checks', 'PASS', 'descriptive')},
                         indent=1, default=str))
    else:
        r = oos()
        print(json.dumps({'acceptance': r['acceptance'], 'S1': r['S1']['mean_R'], 'N2': r['N2_beta_control'],
                          'by_year_S1': r['by_year_S1'], 'first_day': r['first_day'], 'last_day': r['last_day']},
                         indent=1, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
