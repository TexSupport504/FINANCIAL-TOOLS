"""
Fetch ETH/USDT 15m candles from Binance, compute indicators, and output a Goldbach-style phase.

Assumptions for Goldbach algorithm (custom, inferred):
- Trend: EMA20 vs EMA50
- Momentum: RSI(14)
- Volatility/Range: Bollinger Band width and position
- Phases: 'Bull Trend', 'Bear Trend', 'Ranging/Consolidation', 'Reversal Candidate', 'Exploding/Volatile'

This is a minimal, self-contained script for local use.
"""

import ccxt
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timezone

EXCHANGE_ID = 'binance'
SYMBOL = 'ETH/USDT'
TIMEFRAME = '15m'
LIMIT = 500


def fetch_ohlcv():
    exchange = getattr(ccxt, EXCHANGE_ID)()
    # Binance uses timeframe '15m' and returns [ts, open, high, low, close, volume]
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=LIMIT)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df.set_index('timestamp', inplace=True)
    return df


def compute_indicators(df):
    df = df.copy()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['rsi14'] = ta.momentum.rsi(df['close'], window=14)
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_h'] = bb.bollinger_hband()
    df['bb_l'] = bb.bollinger_lband()
    df['bb_m'] = bb.bollinger_mavg()
    df['bb_w'] = (df['bb_h'] - df['bb_l']) / df['bb_m']
    df['bb_pos'] = (df['close'] - df['bb_l']) / (df['bb_h'] - df['bb_l'])
    return df


def goldbach_phase(row):
    # Simple rule-based phase detection
    ema20 = row['ema20']
    ema50 = row['ema50']
    rsi = row['rsi14']
    bb_w = row['bb_w']
    bb_pos = row['bb_pos']
    close = row['close']

    # Trend
    if ema20 > ema50:
        trend = 'bull'
    elif ema20 < ema50:
        trend = 'bear'
    else:
        trend = 'flat'

    # Volatility
    if bb_w > 0.06:
        vol = 'high'
    elif bb_w < 0.02:
        vol = 'low'
    else:
        vol = 'normal'

    # Momentum
    if rsi is not None:
        if rsi > 70:
            mom = 'overbought'
        elif rsi < 30:
            mom = 'oversold'
        else:
            mom = 'neutral'
    else:
        mom = 'unknown'

    # Combine into phases
    if trend == 'bull' and mom == 'neutral' and vol != 'high':
        phase = 'Bull Trend'
    elif trend == 'bull' and mom == 'overbought' and vol == 'high':
        phase = 'Exploding/Bull Blowoff'
    elif trend == 'bear' and mom == 'neutral' and vol != 'high':
        phase = 'Bear Trend'
    elif trend == 'bear' and mom == 'oversold' and vol == 'high':
        phase = 'Exploding/Bear Crash'
    elif vol == 'low':
        phase = 'Ranging/Consolidation'
    elif mom in ('overbought', 'oversold') and vol == 'normal':
        phase = 'Reversal Candidate'
    else:
        phase = 'Unknown/Transition'

    # Also return some scoring
    score = 0
    score += 1 if trend == 'bull' else -1 if trend == 'bear' else 0
    if mom == 'overbought':
        score -= 1
    if mom == 'oversold':
        score += 1
    if vol == 'high':
        score *= 2

    return phase, trend, mom, vol, score


def label_df(df):
    df = df.copy()
    phases = df.apply(lambda r: goldbach_phase(r), axis=1)
    df[['phase', 'trend', 'momentum', 'volatility', 'score']] = pd.DataFrame(phases.tolist(), index=df.index)
    return df


def pretty_print(df):
    last = df.iloc[-5:].copy()
    out = last[['open', 'high', 'low', 'close', 'volume', 'ma10', 'ema20', 'ema50', 'rsi14', 'bb_w', 'phase', 'score']]
    pd.options.display.float_format = '{:,.6f}'.format
    print('\nLast 5 candles (UTC):')
    print(out)
    cur = df.iloc[-1]
    print('\nCurrent status:')
    print(f"Time: {df.index[-1]}")
    print(f"Price: {cur['close']:.6f}")
    print(f"Phase: {cur['phase']}")
    print(f"Trend: {cur['trend']}, Momentum: {cur['momentum']}, Volatility: {cur['volatility']}, Score: {cur['score']}")


def main():
    print('Fetching OHLCV...')
    df = fetch_ohlcv()
    print('Computing indicators...')
    df = compute_indicators(df)
    print('Labeling phases...')
    df = label_df(df)
    pretty_print(df)


if __name__ == '__main__':
    main()
