import pandas as pd
import numpy as np
from datetime import time as dt_time


def load_csv(filepath: str, symbol: str = "NQ") -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=True)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]

    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    elif 'date' in df.columns and 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
    elif 'timestamp_et' in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp_et'])
    elif 'timestamp' in df.columns:
        df['datetime'] = pd.to_datetime(df['timestamp'])
    else:
        df['datetime'] = pd.to_datetime(df.iloc[:, 0])

    if df['datetime'].dt.tz is not None:
        df['datetime'] = df['datetime'].dt.tz_convert('US/Eastern').dt.tz_localize(None)

    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']].copy()
    df['volume'] = df['volume'].fillna(0).astype(int)
    df.loc[df['volume'] == 0, 'volume'] = 1
    df = df.sort_values('datetime').reset_index(drop=True)
    df['symbol'] = symbol
    return df


def resample_to_2min(df: pd.DataFrame) -> pd.DataFrame:
    df = df.set_index('datetime')
    sym = df['symbol'].iloc[0] if 'symbol' in df.columns else 'NQ'
    ohlcv = df[['open', 'high', 'low', 'close', 'volume']].resample('2min').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum',
    }).dropna()
    ohlcv = ohlcv.reset_index().rename(columns={'index': 'datetime'})
    ohlcv['symbol'] = sym
    return ohlcv


def build_daily_bars(df_1m: pd.DataFrame) -> pd.DataFrame:
    df = df_1m.copy()
    df['t'] = df['datetime'].dt.time
    rth = df[(df['t'] >= dt_time(9, 30)) & (df['t'] < dt_time(16, 0))].copy()
    rth['date'] = rth['datetime'].dt.normalize()

    daily = rth.groupby('date').agg(
        open=('open', 'first'),
        high=('high', 'max'),
        low=('low', 'min'),
        close=('close', 'last'),
        volume=('volume', 'sum'),
    ).reset_index()
    daily['date'] = pd.to_datetime(daily['date'])
    return daily


def generate_synthetic_data(days: int = 60, symbol: str = "NQ",
                            start_price: float = 19500.0) -> pd.DataFrame:
    """Generate realistic synthetic 1-min NQ data with trends, sweeps, and sessions."""
    rng = np.random.default_rng(42)
    rows = []
    price = start_price
    base_date = pd.Timestamp("2024-01-02")

    trend = 0.0
    vol_regime = 1.0

    for d in range(days):
        date = base_date + pd.Timedelta(days=d)
        if date.weekday() >= 5:
            continue

        # daily trend bias shifts every few days
        if rng.random() < 0.3:
            trend = rng.choice([-1.5, -0.5, 0.5, 1.5])
        if rng.random() < 0.2:
            vol_regime = rng.choice([0.6, 1.0, 1.5, 2.0])

        day_high = price
        day_low = price

        # full session: overnight prev-day 18:00 through RTH 16:59
        # overnight: 18:00 to 09:29  = 930 minutes
        # RTH: 09:30 to 16:59 = 450 minutes
        for phase, (start_h, start_m, n_bars) in enumerate([
            (18, 0, 570),   # overnight 18:00 - 03:29 (low vol)
            (3, 0, 60),     # london kz 03:00 - 03:59
            (4, 0, 330),    # pre-RTH 04:00 - 09:29
            (9, 30, 20),    # open drive 09:30 - 09:49
            (9, 50, 20),    # NY AM killzone 09:50 - 10:09
            (10, 10, 50),   # mid-morning 10:10 - 10:59
            (11, 0, 360),   # rest of RTH 11:00 - 16:59
        ]):
            for m in range(n_bars):
                ts_date = date - pd.Timedelta(days=1) if phase == 0 else date
                ts = ts_date.replace(hour=start_h, minute=start_m) + pd.Timedelta(minutes=m)

                # vol multiplier by session
                if phase == 0:
                    vm = 0.3
                elif phase in (1, 3, 4):
                    vm = 2.5 * vol_regime
                elif phase == 5:
                    vm = 1.5 * vol_regime
                else:
                    vm = 0.7 * vol_regime

                # open drive often pushes hard then reverses at killzone
                if phase == 3:
                    drift = trend * 0.8 + rng.normal(0, 2.0) * vm
                elif phase == 4:
                    drift = -trend * 0.5 + rng.normal(0, 2.5) * vm
                else:
                    drift = trend * 0.15 + rng.normal(0, 1.8) * vm

                price += drift
                o = price
                spread = abs(rng.normal(0, 2.5 * vm))
                h = o + spread
                l = o - spread
                c = o + rng.normal(0, 1.5 * vm)
                h = max(h, o, c)
                l = min(l, o, c)
                v = max(10, int(abs(rng.normal(400, 200)) * vm))

                day_high = max(day_high, h)
                day_low = min(day_low, l)

                rows.append({
                    'datetime': ts,
                    'open': round(o, 2),
                    'high': round(h, 2),
                    'low': round(l, 2),
                    'close': round(c, 2),
                    'volume': v,
                })

    df = pd.DataFrame(rows)
    df = df.sort_values('datetime').reset_index(drop=True)
    df['symbol'] = symbol
    return df
