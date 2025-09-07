import pandas as pd
import numpy as np
from pathlib import Path

p = Path(__file__).parent
csv = p / 'latest_candles.csv'
if not csv.exists():
    print('latest_candles.csv not found')
    raise SystemExit(1)

df = pd.read_csv(csv, parse_dates=['ts'])
df = df.set_index('ts')
# ensure numeric
for c in ['o', 'h', 'l', 'c', 'v']:
    df[c] = pd.to_numeric(df[c], errors='coerce')

N = len(df)

# Robust indicators that work with small N
ema_fast = df['c'].ewm(span=13, adjust=False).mean()
ema_slow = df['c'].ewm(span=55, adjust=False).mean()

# RSI fallback using EWMA so it handles small samples
delta = df['c'].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
rs = avg_gain / (avg_loss.replace(0, np.nan))
rsi = 100 - (100 / (1 + rs))
rsi = rsi.fillna(50)

# ATR fallback
high_low = df['h'] - df['l']
high_close = (df['h'] - df['c'].shift()).abs()
low_close = (df['l'] - df['c'].shift()).abs()
true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
atr = true_range.rolling(window=14, min_periods=1).mean()

# Bollinger Bands fallback
ma20 = df['c'].rolling(window=20, min_periods=1).mean()
std20 = df['c'].rolling(window=20, min_periods=1).std().fillna(0)
bb_h = ma20 + 2 * std20
bb_l = ma20 - 2 * std20
bb_width = (bb_h - bb_l) / df['c']

last = df.iloc[-1]
idx = df.index[-1]
last_close = float(last['c'])
last_ema13 = float(ema_fast.iloc[-1])
last_ema55 = float(ema_slow.iloc[-1])
last_rsi = float(rsi.iloc[-1])
last_atr = float(atr.iloc[-1])
last_bbw = float(bb_width.iloc[-1])

# Simple phase heuristic
if last_ema13 > last_ema55:
    trend = 'up'
else:
    trend = 'down'

if last_rsi >= 60:
    momentum = 'strong'
elif last_rsi <= 40:
    momentum = 'weak'
else:
    momentum = 'neutral'

phase = 'Unknown'
suggested_entry = None
suggested_stop = None

# Heuristic mapping
if trend == 'up' and momentum == 'strong':
    phase = 'Trending / Momentum (look for continuation)'
    # entry on breakout above recent high -> suggest buy at last close
    suggested_entry = last_close
    suggested_stop = last_close - 1.5 * last_atr
elif trend == 'up' and momentum != 'strong':
    phase = 'Pullback / Accumulation (look for long entries on support)'
    # entry near EMA13
    suggested_entry = last_ema13
    suggested_stop = suggested_entry - 1.5 * last_atr
elif trend == 'down' and momentum == 'weak':
    phase = 'Downtrend / Momentum (look for shorts)'
    suggested_entry = last_close
    suggested_stop = last_close + 1.5 * last_atr
else:
    phase = 'Range/Indecision'
    suggested_entry = last_close
    suggested_stop = last_close - 1.5 * last_atr if trend == 'up' else last_close + 1.5 * last_atr

# Print concise summary
print('snapshot_ts,close,ema13,ema55,rsi,atr,bbw')
print(f"{idx},{last_close:.2f},{last_ema13:.2f},{last_ema55:.2f},{last_rsi:.2f},{last_atr:.2f},{last_bbw:.4f}")
print('\nphase: ' + phase)
print('trend: ' + trend + ', momentum: ' + momentum)
if suggested_entry is not None:
    print(f"suggested_entry: {suggested_entry:.2f}")
    print(f"suggested_stop: {suggested_stop:.2f}")

# Mention trade log
trade_log = p / 'goldbach_trades.csv'
print('\ntrade_log_exists: ' + str(trade_log.exists()))
if trade_log.exists():
    try:
        t = pd.read_csv(trade_log)
        total_pnl = t['pnl'].sum()
        wins = (t['pnl'] > 0).sum()
        losses = (t['pnl'] <= 0).sum()
        last_trade = t.iloc[-1].to_dict()
        print(f"trades: {len(t)}, wins: {wins}, losses: {losses}, total_pnl: {total_pnl:.2f}")
        print('last_trade_sample: ' + str({k: last_trade.get(k) for k in ['side','entry','exit','pnl','entry_idx','exit_idx']}))
    except Exception as e:
        print('failed to read trade log: ' + str(e))

# Classifier: which algo and subcase
def which_algo_row(row, df_local=None):
    ema_fast = last_ema13
    ema_slow = last_ema55
    rsi_val = last_rsi
    bbw = last_bbw
    close = last_close
    atr_v = last_atr

    prox = 'far'
    if df_local is not None and atr_v is not None:
        def recent_pivot_level_local(df_loc, kind='low', lookback=200):
            recent = df_loc.tail(lookback)
            if 'pivot' not in recent.columns:
                return None, None
            mask = recent['pivot'] == kind
            if mask.any():
                idx = recent[mask].index[-1]
                return idx, recent.at[idx, 'close']
            return None, None
        idx_low, lvl_low = recent_pivot_level_local(df_local, 'low')
        idx_high, lvl_high = recent_pivot_level_local(df_local, 'high')
        if lvl_low is not None and abs(close - lvl_low) <= 1.0 * atr_v:
            prox = 'near_low'
        if lvl_high is not None and abs(close - lvl_high) <= 1.0 * atr_v:
            prox = 'near_high'

    strong_mom = (rsi_val is not None and rsi_val > 60)
    weak_mom = (rsi_val is not None and rsi_val < 40)
    low_vol = (bbw is not None and bbw < 0.015)
    high_vol = (bbw is not None and bbw > 0.07)

    is_up = ema_fast > ema_slow
    is_down = ema_fast < ema_slow

    if (is_up and strong_mom) or (is_down and weak_mom) or high_vol:
        algo = 'Algo 1 (trend-following)'
        if is_up:
            sub = 'Bull continuation — breakout/pullback'
        elif is_down:
            sub = 'Bear continuation — breakout/pullback'
        else:
            sub = 'Volatility breakout'
    elif low_vol or prox.startswith('near') or (not strong_mom and not weak_mom):
        algo = 'Algo 2 (mean-reversion/pullback)'
        if prox == 'near_low':
            sub = 'Long fade near pivot low (support)'
        elif prox == 'near_high':
            sub = 'Short fade near pivot high (resistance)'
        else:
            sub = 'Range / mean reversion'
    else:
        algo = 'Unknown/mixed'
        sub = 'Transition / wait'

    return {'algo': algo, 'subcase': sub, 'prox': prox, 'rsi': rsi_val, 'ema_fast': ema_fast, 'ema_slow': ema_slow, 'bb_w': bbw}

print('\nalgo_classification:')
print(which_algo_row(last, df))
