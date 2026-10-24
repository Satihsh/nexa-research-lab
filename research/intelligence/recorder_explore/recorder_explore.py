"""Descriptive look at the NEXA recorder tape/DOM for the two complete sessions (10-21, 10-22).
Exploratory only (not a test). Deliberately does NOT compute the H-ICE-FEAS iceberg statistic
(volume > displayed size at a level), which is pre-registered and sealed."""
import json
import os
import sys

import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
DAYS = ['2026-10-21', '2026-10-22']
TICK = 0.25
OUT = {}


def rth(df, col):
    t = pd.to_datetime(df[col])
    m = t.dt.hour * 60 + t.dt.minute
    return df[(m >= 13 * 60 + 30) & (m < 20 * 60)].assign(_t=t[(m >= 13 * 60 + 30) & (m < 20 * 60)])


def load(sym, day):
    tp = pd.read_csv(f'{D}/{sym}_M1/tape_{day}.csv')
    tp = rth(tp, 'trade_time')
    tp = tp[tp['_t'].dt.date.astype(str) == day]
    dm = pd.read_csv(f'{D}/{sym}_M1/dom_{day}.csv', usecols=['time_utc', 'best_bid', 'best_ask', 'cum_bids', 'cum_asks'])
    # DOM rows are stamped on receipt; the feed is 15 min delayed, so shift to exchange time
    dm['time_utc'] = pd.to_datetime(dm['time_utc']) - pd.Timedelta(minutes=15)
    dm = rth(dm.assign(time_utc=dm['time_utc'].astype(str)), 'time_utc')
    dm = dm[dm['_t'].dt.date.astype(str) == day]
    return tp, dm


def profile(tp):
    px = (tp['last_price'] / TICK).round().astype(int)
    vap = tp.groupby(px)['volume'].sum().sort_index()
    poc = vap.idxmax()
    order = vap.index.tolist()
    i = order.index(poc)
    lo = hi = i
    acc, tot = vap.iloc[i], vap.sum()
    while acc < 0.7 * tot and (lo > 0 or hi < len(order) - 1):
        up = vap.iloc[hi + 1] if hi < len(order) - 1 else -1
        dn = vap.iloc[lo - 1] if lo > 0 else -1
        if up >= dn:
            hi += 1; acc += up
        else:
            lo -= 1; acc += dn
    return poc * TICK, order[hi] * TICK, order[lo] * TICK


for sym in ('NQ', 'ES'):
    res = {}
    allm = []
    bigs = []
    for day in DAYS:
        tp, dm = load(sym, day)
        sgn = np.where(tp['side'] == 'BUY', 1, np.where(tp['side'] == 'SELL', -1, 0))
        tp = tp.assign(sgn=sgn, sv=sgn * tp['volume'])
        p = tp['last_price'].values
        # day structure
        o, h, l, c = p[0], p.max(), p.min(), p[-1]
        t = tp['_t']
        ib = tp[t < t.iloc[0].normalize() + pd.Timedelta(hours=14, minutes=30)]['last_price']
        poc, vah, val = profile(tp)
        res[day] = {'open': o, 'high': h, 'low': l, 'close': c, 'range': h - l,
                    'close_pos_in_range': round((c - l) / (h - l), 2),
                    'time_high_ET': (t.iloc[int(np.argmax(p))] - pd.Timedelta(hours=4)).strftime('%H:%M'),
                    'time_low_ET': (t.iloc[int(np.argmin(p))] - pd.Timedelta(hours=4)).strftime('%H:%M'),
                    'IB_range': ib.max() - ib.min(), 'IB_share_of_day': round((ib.max() - ib.min()) / (h - l), 2),
                    'POC': poc, 'VAH': vah, 'VAL': val,
                    'trades': len(tp), 'contracts': int(tp['volume'].sum()),
                    'net_delta': int(tp['sv'].sum()), 'one_lot_share': round(float((tp['volume'] == 1).mean()), 3),
                    'median_size': float(tp['volume'].median()), 'p999_size': float(tp['volume'].quantile(0.999))}
        # minute table
        mm = tp.set_index('_t').resample('1min').agg({'last_price': 'last', 'volume': 'sum', 'sv': 'sum'})
        mm['ret'] = mm['last_price'].diff()
        mm['next_ret'] = mm['ret'].shift(-1)
        mm['next5'] = mm['last_price'].shift(-5) - mm['last_price']
        dmm = dm.set_index('_t').resample('1min').last()
        imb = (dmm['cum_bids'] - dmm['cum_asks']) / (dmm['cum_bids'] + dmm['cum_asks'])
        mm['book_imb'] = imb.reindex(mm.index)
        mm['day'] = day
        allm.append(mm)
        # big trades: top 0.1 % size of this day (descriptive)
        thr = tp['volume'].quantile(0.999)
        bt = tp[tp['volume'] >= thr]
        ts = tp.set_index('_t')['last_price']
        for _, r in bt.iterrows():
            if r['sgn'] == 0:
                continue
            fut = {}
            for k, lab in ((1, 'f1'), (5, 'f5'), (15, 'f15')):
                j = ts.index.searchsorted(r['_t'] + pd.Timedelta(minutes=k))
                if j < len(ts):
                    fut[lab] = r['sgn'] * (ts.iloc[j] - r['last_price'])
            bigs.append(dict(fut, size=r['volume'], side=r['sgn']))
    m = pd.concat(allm).dropna(subset=['ret'])
    # time-of-day (30-min buckets, ET)
    et = (m.index - pd.Timedelta(hours=4))
    bucket = (et.hour * 60 + et.minute) // 30 * 30
    tod = m.groupby(bucket).agg(vol=('volume', 'mean'), absret=('ret', lambda x: x.abs().mean()))
    res['time_of_day'] = {f'{b // 60:02d}:{b % 60:02d}': [int(r.vol), round(r.absret, 2)] for b, r in tod.iterrows()}
    ok = m.dropna(subset=['next_ret'])
    res['delta_vs_price'] = {
        'corr_same_minute': round(ok['sv'].corr(ok['ret']), 3),
        'corr_next_minute': round(ok['sv'].corr(ok['next_ret']), 3),
        'corr_next_5min': round(ok['sv'].corr(ok['next5']), 3),
        'minutes': len(ok)}
    ok2 = ok.dropna(subset=['book_imb'])
    res['book_imbalance_vs_price'] = {'corr_same_minute': round(ok2['book_imb'].corr(ok2['ret']), 3),
                                      'corr_next_minute': round(ok2['book_imb'].corr(ok2['next_ret']), 3),
                                      'corr_next_5min': round(ok2['book_imb'].corr(ok2['next5']), 3),
                                      'minutes': len(ok2)}
    b = pd.DataFrame(bigs)
    res['big_trades'] = {'n': len(b), 'buys': int((b.side > 0).sum()), 'sells': int((b.side < 0).sum()),
                         'mean_pts_in_aggressor_dir': {k: round(b[k].mean(), 2) for k in ('f1', 'f5', 'f15')},
                         'share_moving_their_way': {k: round(float((b[k] > 0).mean()), 2) for k in ('f1', 'f5', 'f15')}}
    OUT[sym] = res

# NQ vs ES lead-lag on 1-second last prices
ll = {}
for day in DAYS:
    s = {}
    for sym in ('NQ', 'ES'):
        tp, _ = load(sym, day)
        s[sym] = tp.set_index('_t')['last_price'].resample('1s').last().ffill()
    j = pd.concat(s, axis=1).dropna()
    r = np.log(j).diff().dropna()
    ll[day] = {str(k): round(r['NQ'].corr(r['ES'].shift(k)), 3) for k in (-5, -2, -1, 0, 1, 2, 5)}
OUT['NQ_vs_ES_1s_corr_by_lag'] = ll
json.dump(OUT, open(f'{D}/explore_out.json', 'w'), indent=1, default=float)
print(json.dumps(OUT, indent=1, default=float))
