"""Session VWAP calculation."""
from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import time as dt_time


def compute_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """Add VWAP and standard deviation bands to 1m/2m/5m dataframe."""
    df = df.copy()
    df['t'] = df['datetime'].dt.time
    df['date'] = df['datetime'].dt.date

    # RTH VWAP resets at 9:30
    df['rth'] = df['t'] >= dt_time(9, 30)
    df['session_id'] = (df['date'].astype(str) + '_' +
                        df['rth'].astype(str))

    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_vol'] = df['tp'] * df['volume']

    df['cum_vol'] = df.groupby('session_id')['volume'].cumsum()
    df['cum_tp_vol'] = df.groupby('session_id')['tp_vol'].cumsum()

    df['vwap'] = df['cum_tp_vol'] / df['cum_vol'].replace(0, np.nan)

    # deviation bands
    df['vwap_sq_diff'] = (df['tp'] - df['vwap']) ** 2 * df['volume']
    df['cum_sq'] = df.groupby('session_id')['vwap_sq_diff'].cumsum()
    df['vwap_std'] = np.sqrt(df['cum_sq'] / df['cum_vol'].replace(0, np.nan))
    df['vwap_upper'] = df['vwap'] + df['vwap_std']
    df['vwap_lower'] = df['vwap'] - df['vwap_std']

    df.drop(columns=['t', 'rth', 'session_id', 'tp', 'tp_vol',
                      'cum_vol', 'cum_tp_vol', 'vwap_sq_diff', 'cum_sq'],
            inplace=True)
    return df


def compute_opening_range(df: pd.DataFrame, minutes: int = 15) -> pd.DataFrame:
    """Add opening range high/low columns (first N minutes of RTH)."""
    df = df.copy()
    df['t'] = df['datetime'].dt.time
    df['date'] = df['datetime'].dt.date

    or_end = dt_time(9, 30 + minutes)
    or_bars = df[(df['t'] >= dt_time(9, 30)) & (df['t'] < or_end)]

    or_levels = or_bars.groupby('date').agg(
        or_high=('high', 'max'),
        or_low=('low', 'min'),
    ).reset_index()

    df = df.merge(or_levels, on='date', how='left')
    df['or_mid'] = (df['or_high'] + df['or_low']) / 2
    df['or_range'] = df['or_high'] - df['or_low']
    df.drop(columns=['t'], inplace=True)
    return df
