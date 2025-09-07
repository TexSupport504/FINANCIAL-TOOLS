"""Deterministic offline Goldbach-style demo backtest using synthetic data.

This file avoids external APIs and heavy deps. It computes a few indicators and
runs a simple EMA crossover backtest with the shared `agent_trader.Portfolio`.
"""
from typing import Tuple
import pandas as pd
import numpy as np

from offline_data import generate_synthetic_ohlcv
from agent_trader.portfolio import Portfolio
from agent_trader import performance


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # EMAs
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    # ATR(14)
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    df['atr14'] = tr.rolling(14, min_periods=1).mean()
    # RSI(14) - simple EWMA method
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['rsi14'] = 100 - (100 / (1 + rs))
    # Bollinger width (20)
    mavg = close.rolling(20, min_periods=1).mean()
    std = close.rolling(20, min_periods=1).std()
    df['bb_w'] = (4 * std) / mavg.replace(0, np.nan)
    return df


def run_demo(n: int = 400, seed: int = 0, position_size: float = 0.1, transaction_cost_per_share: float = 0.0, slippage_per_share: float = 0.0) -> Tuple[dict, pd.DataFrame]:
    """Run a simple offline backtest and return (metrics, equity_df).

    Strategy: enter long when ema20 > ema50 (crossover), exit when ema20 < ema50.
    Uses `agent_trader.Portfolio` for accounting.
    """
    df = generate_synthetic_ohlcv(n=n, seed=seed)
    df = compute_indicators(df)
    df = df.dropna(subset=['ema20', 'ema50', 'atr14'])

    port = Portfolio(initial_cash=10000.0, position_size=position_size, transaction_cost_per_share=transaction_cost_per_share, slippage_per_share=slippage_per_share)

    position_flag = 0
    timestamps = df.index
    # iterate bars; use next bar open for entries/exits when available
    for i in range(len(df) - 1):
        ts = timestamps[i]
        row = df.iloc[i]
        next_open = float(df.iloc[i + 1]['open'])
        price = float(row['close'])
        # mark
        port.record(ts, price)
        # simple EMA crossover logic
        if row['ema20'] > row['ema50'] and position_flag == 0:
            # enter at next open price (simulate market open)
            port.enter_long(next_open, timestamps[i + 1])
            position_flag = 1
        elif row['ema20'] < row['ema50'] and position_flag == 1:
            # exit at next open
            port.exit_long(next_open, timestamps[i + 1])
            position_flag = 0
    # final mark at last price
    last_ts = timestamps[-1]
    last_price = float(df.iloc[-1]['close'])
    port.record(last_ts, last_price)

    eq_df = port.equity_series()
    metrics = performance.compute_metrics_from_equity(eq_df)
    return metrics, eq_df


if __name__ == '__main__':
    m, e = run_demo(n=400, seed=42)
    print('Demo metrics:', m)
    print('Equity points:', len(e))
