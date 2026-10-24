"""H-SK28-OOS gate step G1 (PREREG_SK28_OOS.md s.3): run the frozen s-k-28 pipeline on their own NQ file.

Usage: python -I sk28_ref.py <Dataset_NQ_1min_2022_2025.csv> <out_dir>
Writes <out_dir>/ref_trades.csv, <out_dir>/ref_summary.json and qc_sk28/ref_trades.py (the IN-window module for QC).
The frozen files are imported unchanged from qc_sk28/frozen (hashes checked first).
"""
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = os.path.join(HERE, 'qc_sk28', 'frozen')
IN_FROM, IN_TO = '2023-01-03', '2025-11-28'
COSTS = (1.0, 2.0, 3.0)
MODELS = ['ou_rev', 'pd_rev', 'vwap_rev', 'or_rev', 'ou_lunch', 'vwap_scalp', 'open_drive', 'trend', 'pm_mom',
          'ema_rev', 'kalman_mom', 'sweep']


def check_frozen():
    bad = []
    with open(os.path.join(FROZEN, 'FROZEN_SHA256.txt')) as f:
        for line in f:
            h, p = line.split()
            with open(os.path.join(FROZEN, p), 'rb') as g:
                if hashlib.sha256(g.read()).hexdigest() != h:
                    bad.append(p)
    if bad:
        raise SystemExit(f'frozen files changed: {bad}')


def run_pipeline(csv_path):
    """Exactly run_multi.py without --history/--nq-daily/--es/--tier."""
    sys.path.insert(0, FROZEN)
    from config import Config
    from data.loader import load_csv, build_daily_bars
    from strategy.multi import MultiModelGenerator
    from backtest.engine_v2 import BacktestEngineV2
    import pandas as pd
    cfg = Config()
    raw = load_csv(csv_path, 'NQ')
    daily = build_daily_bars(raw)
    daily['date'] = pd.to_datetime(daily['date']).dt.date
    signals = MultiModelGenerator(cfg).generate(raw, daily, None)
    return BacktestEngineV2(cfg).run(raw, signals), len(signals), raw


def stats(rows):
    out = {'n': len(rows)}
    if not rows:
        return out
    for k, c in zip(('S0', 'S1', 'S2'), COSTS):
        v = [r['gross_r'] - c / r['risk_pts'] for r in rows]
        out[k] = round(sum(v) / len(v), 4)
    out['gross'] = round(sum(r['gross_r'] for r in rows) / len(rows), 4)
    out['win_rate_S1'] = round(sum(1 for r in rows if r['gross_r'] - 2.0 / r['risk_pts'] > 0) / len(rows), 3)
    out['median_risk_pts'] = sorted(r['risk_pts'] for r in rows)[len(rows) // 2]
    return out


def main(csv_path, out_dir):
    check_frozen()
    t0 = time.time()
    trades, n_sig, raw = run_pipeline(csv_path)
    rows = [{'model': t.model, 'dir': t.direction, 'signal_ts': str(t.signal.ts), 'entry_ts': str(t.entry_time),
             'exit_ts': str(t.exit_time), 'entry': t.entry_price, 'stop': t.stop_price, 'target': t.target_price,
             'risk_pts': t.risk, 'gross_r': t.total_r, 'exit_reason': t.exit_reason} for t in trades]
    os.makedirs(out_dir, exist_ok=True)
    import csv
    with open(os.path.join(out_dir, 'ref_trades.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    inn = [r for r in rows if IN_FROM <= r['entry_ts'][:10] <= IN_TO]
    summ = {'bars': len(raw), 'first_bar': str(raw['datetime'].min()), 'last_bar': str(raw['datetime'].max()),
            'signals': n_sig, 'all': stats(rows), 'IN': stats(inn),
            'per_model_IN': {m: stats([r for r in inn if r['model'] == m]) for m in MODELS},
            'per_year': {y: stats([r for r in rows if r['entry_ts'][:4] == y]) for y in ('2022', '2023', '2024', '2025')},
            'seconds': round(time.time() - t0, 1)}
    with open(os.path.join(out_dir, 'ref_summary.json'), 'w') as f:
        json.dump(summ, f, indent=1)
    # compact module for QC: "YYYYMMDDHHMM,model_index,dir" per IN trade (entry time), sorted
    recs = ['%s,%d,%s' % (r['entry_ts'][:16].replace('-', '').replace(' ', '').replace(':', ''),
                          MODELS.index(r['model']), 'L' if r['dir'] == 'long' else 'S') for r in inn]
    with open(os.path.join(HERE, 'qc_sk28', 'ref_trades.py'), 'w') as f:
        f.write('# H-SK28-OOS gate reference (sk28_ref.py on their own data, IN window): entry YYYYMMDDHHMM ET, model index, side\n')
        f.write("REF = '" + ';'.join(recs) + "'\n")
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
