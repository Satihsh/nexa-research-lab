"""DATA-AVAILABILITY PROBE (not research evidence of edge), 2026-10-04.

Question: does a daily volume profile (POC, 70 % value area) built from Pepperstone XAUUSD M1 tick_volume
locate the same levels as one built from real COMEX GCZ6 1-min volume?
GC profile: per UTC date, 1-min bars binned at $1 by typical price (h+l+c)/3, computed in the Massive workspace
(gc_daily_profile.csv). Futures-spot basis: median over the day of GC close minus XAU close at hh:59 UTC
(gc_hourly_close.csv vs Pepperstone M1 close). XAU profile: identical construction on tick_volume, then
shifted by the basis. Days with < 50k GC contracts (Sunday opens) are excluded.
"""
import numpy as np
import pandas as pd

ROOT = '~/NEXA-Agent-Lab/filesnexa/NEXA/data/pepperstone/m1_canonical/'
d = pd.read_csv(ROOT + 'PEPPERSTONE_XAUUSD_M1_canonical.csv.gz', usecols=['time_utc', 'high', 'low', 'close', 'tick_volume'])
d['t'] = pd.to_datetime(d.time_utc, utc=True)
d = d[(d.t >= '2026-08-31') & (d.t < '2026-09-26')].copy()
d['sec'] = (d.t - pd.Timestamp(0, tz='UTC')) // pd.Timedelta('1s')
d['day'] = d.t.dt.strftime('%Y-%m-%d')
gcc = pd.read_csv('gc_hourly_close.csv').rename(columns={'minute_s': 'sec'})
b = gcc.merge(d[['sec', 'day', 'close']], on='sec')
basis = (b.gc_close - b.close).groupby(b.day).median()


def profile(g: pd.DataFrame, shift: float) -> pd.Series:
    px = np.round((g.high + g.low + g.close) / 3.0 + shift).astype(int)
    v = g.tick_volume.groupby(px).sum()
    order = v.sort_values(ascending=False, kind='mergesort')
    order = order.loc[sorted(order.index, key=lambda p: (-order[p], p))]
    cum = order.cumsum()
    va = order[(cum - order) < 0.7 * v.sum()].index
    return pd.Series({'poc': order.index[0], 'val': va.min(), 'vah': va.max()})


gp = pd.read_csv('gc_daily_profile.csv').set_index('d')
gp = gp[gp.vol >= 50000]
rows = []
for day, g in d.groupby('day'):
    if day not in gp.index or day not in basis.index:
        continue
    x = profile(g, basis[day])
    r = gp.loc[day]
    rows.append({'day': day, 'basis': round(basis[day], 1), 'gc_poc': r.poc, 'xau_poc_adj': x.poc,
                 'poc_diff': x.poc - r.poc, 'gc_va': f'{r.val}-{r.vah}', 'xau_va_adj': f'{x.val}-{x.vah}',
                 'va_jaccard': round(max(0, min(r.vah, x.vah) - max(r.val, x.val)) / (max(r.vah, x.vah) - min(r.val, x.val)), 3),
                 'gc_range_va_width': r.vah - r.val})
out = pd.DataFrame(rows)
out.to_csv('profile_proxy_check_results.csv', index=False)
print(out.to_string(index=False))
print('days', len(out), '| median |POC diff| $', out.poc_diff.abs().median(), '| share |POC diff|<=2$',
      round((out.poc_diff.abs() <= 2).mean(), 3), '| median VA Jaccard', out.va_jaccard.median(),
      '| median GC VA width $', out.gc_range_va_width.median())
