import ccxt
import pandas as pd
import numpy as np
import ta
from math import isnan

EXCHANGE_ID = 'coinbase'
SYMBOL = 'ETH/USD'
TIMEFRAME = '15m'
LIMIT = 1000

# params (match run_backtest)
EMA_FAST = 13
EMA_SLOW = 55
RSI_LEN = 14
RSI_OB = 72
RSI_OS = 28
BB_WINDOW = 20
BB_DEV = 2
BB_WIDTH_LOW = 0.015
BB_WIDTH_HIGH = 0.07
PIVOT_LOOKBACK = 5

# fetch recent candles
ex = getattr(ccxt, EXCHANGE_ID)()
ohlcv = ex.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=LIMIT)
if not ohlcv:
    raise SystemExit('No OHLCV fetched')

df = pd.DataFrame(ohlcv, columns=['ts','open','high','low','close','volume'])
df['timestamp'] = pd.to_datetime(df['ts'], unit='ms', utc=True)
df.set_index('timestamp', inplace=True)

# indicators
df['ema20'] = df['close'].ewm(span=EMA_FAST, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=EMA_SLOW, adjust=False).mean()
try:
    df['rsi14'] = ta.momentum.RSIIndicator(df['close'], window=RSI_LEN).rsi()
except Exception:
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/RSI_LEN, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/RSI_LEN, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['rsi14'] = 100 - (100 / (1 + rs))

bb = ta.volatility.BollingerBands(df['close'], window=BB_WINDOW, window_dev=BB_DEV)
df['bb_h'] = bb.bollinger_hband()
df['bb_l'] = bb.bollinger_lband()
df['bb_m'] = bb.bollinger_mavg()
df['bb_w'] = (df['bb_h'] - df['bb_l']) / df['bb_m']
df['bb_pos'] = (df['close'] - df['bb_l']) / (df['bb_h'] - df['bb_l'])
atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14)
df['atr14'] = atr.average_true_range()

# pivot detection
pivots = {}
prices = df['close'].values
atr_vals = df['atr14'].fillna(method='backfill').values
n = len(prices)
for i in range(PIVOT_LOOKBACK, n - PIVOT_LOOKBACK):
    window = prices[i - PIVOT_LOOKBACK:i + PIVOT_LOOKBACK + 1]
    v = prices[i]
    local_mean = window.mean()
    prom = abs(v - local_mean)
    if v == window.max() and prom >= max(0.0, 0.5 * atr_vals[i]):
        pivots[df.index[i]] = 'high'
    elif v == window.min() and prom >= max(0.0, 0.5 * atr_vals[i]):
        pivots[df.index[i]] = 'low'

df['pivot'] = pd.NA
for idx,k in pivots.items():
    if idx in df.index:
        df.at[idx, 'pivot'] = k

# helper funcs (copied from run_backtest)
def recent_pivot_level(df_local, kind='low', lookback=200):
    recent = df_local.tail(lookback)
    if 'pivot' not in recent.columns:
        return None, None
    mask = recent['pivot'] == kind
    if mask.any():
        idx = recent[mask].index[-1]
        return idx, recent.at[idx, 'close']
    return None, None


def detect_rsi_divergence(df_local, kind='high'):
    if 'pivot' not in df_local.columns:
        return False, None
    piv = df_local.dropna(subset=['pivot'])[['close','rsi14','pivot']]
    piv = piv[piv['pivot']==kind]
    if len(piv) < 2:
        return False, None
    last_two = piv.tail(2)
    p1 = last_two.iloc[0]; p2 = last_two.iloc[1]
    price1, price2 = p1['close'], p2['close']
    rsi1, rsi2 = p1['rsi14'], p2['rsi14']
    if kind=='high':
        if price2 > price1 and rsi2 < rsi1:
            return True, {'type':'bear_reg','pivots':list(last_two.index)}
    else:
        if price2 < price1 and rsi2 > rsi1:
            return True, {'type':'bull_reg','pivots':list(last_two.index)}
    return False, None


def goldbach_phase_refined(row, df_local=None):
    ema20 = row.get('ema20', np.nan)
    ema50 = row.get('ema50', np.nan)
    rsi = row.get('rsi14', np.nan)
    bb_w = row.get('bb_w', np.nan)
    close = row['close']
    atr = row.get('atr14', np.nan)

    if ema20 > ema50:
        trend = 'bull'
    elif ema20 < ema50:
        trend = 'bear'
    else:
        trend = 'flat'

    if pd.isna(bb_w):
        vol = 'unknown'
    elif bb_w > BB_WIDTH_HIGH:
        vol = 'high'
    elif bb_w < BB_WIDTH_LOW:
        vol = 'low'
    else:
        vol = 'normal'

    if pd.isna(rsi):
        mom = 'unknown'
    elif rsi > RSI_OB:
        mom = 'overbought'
    elif rsi < RSI_OS:
        mom = 'oversold'
    else:
        mom = 'neutral'

    prox = 'far'
    if df_local is not None and not pd.isna(atr) and atr>0:
        idx_low, lvl_low = recent_pivot_level(df_local, 'low', lookback=200)
        idx_high, lvl_high = recent_pivot_level(df_local, 'high', lookback=200)
        if lvl_low is not None and abs(close - lvl_low) <= 1.0 * atr:
            prox = 'near_low'
        if lvl_high is not None and abs(close - lvl_high) <= 1.0 * atr:
            prox = 'near_high'

    # phase heuristics
    if vol == 'low':
        phase = 'Ranging/Consolidation'
    elif trend == 'bull' and mom in ('neutral','oversold'):
        phase = 'Bull Pullback (support test)' if prox=='near_low' else 'Bull Trend'
    elif trend == 'bear' and mom in ('neutral','overbought'):
        phase = 'Bear Pullback (resistance test)' if prox=='near_high' else 'Bear Trend'
    elif mom == 'oversold' and vol == 'high':
        phase = 'Reversal Candidate (bear exhausted)'
    elif mom == 'overbought' and vol == 'high':
        phase = 'Reversal Candidate (bull exhausted)'
    else:
        phase = 'Unknown/Transition'

    score = 0
    score += 1 if trend=='bull' else -1 if trend=='bear' else 0
    if mom=='overbought':
        score -= 1
    if mom=='oversold':
        score += 1
    if vol=='high':
        score *= 2

    return phase, trend, mom, vol, score


def goldbach_phase_with_pdf(row, df_local=None):
    phase, trend, mom, vol, score = goldbach_phase_refined(row, df_local=df_local)
    div_bear, info_b = (False, None)
    div_bull, info_l = (False, None)
    if df_local is not None:
        div_bear, info_b = detect_rsi_divergence(df_local, kind='high')
        div_bull, info_l = detect_rsi_divergence(df_local, kind='low')
    if div_bear and trend=='bull':
        phase = 'Reversal Candidate (bear divergence)'
        score -= 2
    if div_bull and trend=='bear':
        phase = 'Reversal Candidate (bull divergence)'
        score += 2

    entry_suggestion = None
    stop_suggestion = None
    if trend=='bull' and df_local is not None:
        idx_low, lvl_low = recent_pivot_level(df_local, 'low', lookback=200)
        if lvl_low is not None and row.get('atr14') is not None:
            entry_suggestion = f'Pullback to EMA{EMA_FAST} or pivot low ~{lvl_low:.2f}'
            stop_suggestion = max(0.0, lvl_low - 0.5 * row['atr14'])
        else:
            entry_suggestion = f'Pullback to EMA{EMA_FAST} or mid-BB'
    if trend=='bear' and df_local is not None:
        idx_high, lvl_high = recent_pivot_level(df_local, 'high', lookback=200)
        if lvl_high is not None and row.get('atr14') is not None:
            entry_suggestion = f'Pullback to EMA{EMA_FAST} or pivot high ~{lvl_high:.2f}'
            stop_suggestion = lvl_high + 0.5 * row['atr14']
        else:
            entry_suggestion = f'Pullback to EMA{EMA_FAST} or mid-BB'

    meta = {'div_bear': info_b, 'div_bull': info_l, 'entry': entry_suggestion, 'stop': stop_suggestion}
    return phase, trend, mom, vol, score, meta


if __name__ == '__main__':
    row = df.iloc[-1]
    phase, trend, mom, vol, score, meta = goldbach_phase_with_pdf(row, df_local=df)
    # confidence
    try:
        rsi_z = (row['rsi14'] - df['rsi14'].mean()) / (df['rsi14'].std() or 1.0)
        bbw_z = (row['bb_w'] - df['bb_w'].mean()) / (df['bb_w'].std() or 1.0)
        ema_z = ((row['ema20'] - row['ema50']) / row['ema50'] - ((df['ema20'] - df['ema50'])/df['ema50']).mean()) / (((df['ema20'] - df['ema50'])/df['ema50']).std() or 1.0)
        conf_score = 0.5 * ema_z + 0.4 * rsi_z + 0.1 * bbw_z
        conf = 1.0 / (1.0 + np.exp(-conf_score))
    except Exception:
        conf = 0.5

    print('Snapshot for latest 15m bar:')
    print('ts:', df.index[-1])
    print('close:', row['close'])
    print('phase:', phase)
    print('trend:', trend)
    print('momentum:', mom)
    print('volatility:', vol)
    print('phase_score:', score)
    print('confidence:', round(conf,3))
    print('entry suggestion:', meta.get('entry'))
    print('stop suggestion:', meta.get('stop'))
