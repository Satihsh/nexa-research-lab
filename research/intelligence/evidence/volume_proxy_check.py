"""DATA-AVAILABILITY PROBE (not research evidence of edge), 2026-10-04.

Question: is Pepperstone CFD tick volume (MT5 tick_volume) a usable proxy for exchange volume?
Inputs (hourly, UTC, 2026-08-31 .. 2026-09-25):
  - CME/COMEX futures 1-min aggregates from Massive (GCZ6; 6EZ6 after the Sep roll), summed per hour
    (extracted to gc_hourly.csv / e6_hourly.csv, columns: hour epoch s, volume, transactions);
  - Massive C:EURUSD 1-min aggregates (n = quote-update count, v == n);
  - Pepperstone M1 canonical bars (tick_volume), summed per UTC hour.
Reported: log-log Pearson, Spearman, correlation after removing the hour-of-week mean (i.e. the shared
intraday seasonality), and the correlation of the hour-of-day profiles.
"""
import sys
import numpy as np
import pandas as pd

ROOT = '~/NEXA-Agent-Lab/filesnexa/NEXA/data/pepperstone/m1_canonical/'
HERE = sys.argv[1] if len(sys.argv) > 1 else '.'


def pep(sym: str) -> pd.Series:
    d = pd.read_csv(f'{ROOT}PEPPERSTONE_{sym}_M1_canonical.csv.gz', usecols=['time_utc', 'tick_volume'])
    d['t'] = pd.to_datetime(d.time_utc, utc=True)
    d = d[(d.t >= '2026-08-31') & (d.t < '2026-09-26')]
    h = (d.t.dt.floor('h') - pd.Timestamp(0, tz='UTC')) // pd.Timedelta('1s')
    return d.groupby(h)['tick_volume'].sum()


def show(name: str, a: pd.Series, b: pd.Series) -> dict:
    j = pd.concat({'a': a, 'b': b}, axis=1, join='inner')
    j = j[(j.a > 0) & (j.b > 0)]
    la, lb = np.log(j.a), np.log(j.b)
    how = (j.index // 3600) % 168
    hod = (j.index // 3600) % 24
    ra, rb = la - la.groupby(how).transform('mean'), lb - lb.groupby(how).transform('mean')
    out = {'pair': name, 'n_hours': len(j), 'pearson_log': round(float(np.corrcoef(la, lb)[0, 1]), 3),
           'spearman': round(float(j.a.rank().corr(j.b.rank())), 3),
           'resid_corr_ex_hour_of_week': round(float(np.corrcoef(ra, rb)[0, 1]), 3),
           'hour_of_day_profile_corr': round(float(np.corrcoef(la.groupby(hod).mean(), lb.groupby(hod).mean())[0, 1]), 3)}
    print(out)
    return out


gc = pd.read_csv(f'{HERE}/gc_hourly.csv').set_index('h')
e6 = pd.read_csv(f'{HERE}/e6_hourly.csv').set_index('e6h')
xau, eur = pep('XAUUSD'), pep('EURUSD')
rows = [show('COMEX GCZ6 volume vs Pepperstone XAUUSD tick_volume', gc.vol, xau),
        show('COMEX GCZ6 transactions vs Pepperstone XAUUSD tick_volume', gc.tx, xau),
        show('CME 6EZ6 volume vs Pepperstone EURUSD tick_volume (Sep 15-25)', e6.vol, eur),
        show('Massive C:EURUSD quote count vs Pepperstone EURUSD tick_volume', e6.fx_ticks, eur),
        show('CME 6EZ6 volume vs Massive C:EURUSD quote count', e6.vol, e6.fx_ticks)]
pd.DataFrame(rows).to_csv(f'{HERE}/volume_proxy_check_results.csv', index=False)
