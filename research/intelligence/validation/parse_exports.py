"""Parse Massive query_data exports (extracted verbatim from the session transcript into raw/*.txt) into the CSVs
consumed by t1_tickvol_proxy.py. Compact encodings (to limit transfer size):

raw/<PAIR>_H_<k>.txt : header 'xh,d,items' ; items = 'hourIndex:vol:closeInBins;...'  (d = UTC date)
raw/<PAIR>_P_<k>.txt : header 'xp,d,front,b0,items' ; items = 'binOffset:vol;...'   (d = server day)
closeInBins = round(close / CBIN) for hourly closes; profile bins use BIN per pair (prereg section 4).
"""
import calendar
import glob
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = {'XAUUSD': 1.0, 'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDJPY': 0.000001}
# hourly-close encoding scale (exact for the FX futures tick; gold was exported at 1.0 = +-0.5 USD, ~+-0.01 sigma_day)
CBIN = {'XAUUSD': 1.0, 'EURUSD': 0.00001, 'GBPUSD': 0.00001, 'USDJPY': 0.0000001}


def parse(pair: str) -> None:
    raw = os.path.join(HERE, 'raw')
    out = os.path.join(HERE, 'data')
    os.makedirs(out, exist_ok=True)
    bw = BIN[pair]
    rows = {}
    for f in sorted(glob.glob(os.path.join(raw, f'{pair}_H_*.txt'))):
        for line in open(f).read().strip().split('\n')[1:]:
            parts = line.split(',', 2)
            if len(parts) < 3 or not parts[2]:
                continue
            day0 = calendar.timegm(time.strptime(parts[1], '%Y-%m-%d'))
            for it in parts[2].split(';'):
                hi, v, cx = it.split(':')
                rows[day0 + int(hi) * 3600] = (int(float(v)), round(int(float(cx)) * CBIN[pair], 10))
    with open(os.path.join(out, f'{pair}_fut_hourly.csv'), 'w') as fh:
        fh.write('utc_hour,vol,close\n')
        for h in sorted(rows):
            v, c = rows[h]
            fh.write(f'{h},{v},{c}\n')
    prof = {}
    for f in sorted(glob.glob(os.path.join(raw, f'{pair}_P_*.txt'))):
        for line in open(f).read().strip().split('\n')[1:]:
            parts = line.split(',', 4)
            if len(parts) < 5 or not parts[4]:
                continue
            d, front, b0 = parts[1], parts[2], int(parts[3])
            kv = {}
            for it in parts[4].split(';'):
                b, v = it.split(':')
                kv[b0 + int(b)] = kv.get(b0 + int(b), 0) + int(float(v))
            lo, hi = min(kv), max(kv)
            prof[d] = (front, lo, ';'.join(str(kv.get(b, 0)) for b in range(lo, hi + 1)))
    with open(os.path.join(out, f'{pair}_fut_profile.csv'), 'w') as fh:
        fh.write('server_day,front,bin0,vols\n')
        for d in sorted(prof):
            fr, b0, vs = prof[d]
            fh.write(f'{d},{fr},{b0},{vs}\n')
    print(pair, 'hours', len(rows), 'profile days', len(prof))


if __name__ == '__main__':
    for p in sys.argv[1:]:
        parse(p)
