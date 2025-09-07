import ccxt
import pandas as pd
import ta
import os

import ccxt
import pandas as pd
import numpy as np
import ta
import os
import time

# parameters
EXCHANGE_ID = 'coinbase'
SYMBOL = 'ETH/USD'
TIMEFRAME = '15m'
LIMIT = 1000
HIST_DAYS = 120  # full multi-month fetch (~120 days)
ENABLE_SHORTS = False
LONG_ONLY = True  # set True to disable shorts and run long-only backtest

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
STOP_ATR_MULT = 2.5
BACKTEST_RISK_PCT = 0.0015  # reduced risk for tuned run (half)
BACKTEST_SLIPPAGE = 0.0008
BACKTEST_FEE = 0.0015

# Short-entry tightening
SHORT_RSI_MAX = 45
SHORT_BB_MIN = 0.01
SHORT_PROX_ATR_MULT = 1.0

# Long-entry tuning for tuned run
LONG_ENTRY_RSI_MIN = 45  # require RSI >= 45 for long entries
LONG_ENTRY_EMA_BUFFER = 1.001  # tighter buffer vs ema

# Confidence sizing params (weights for z-score blend)
CONF_W_TRND = 0.5
CONF_W_MOM = 0.4
CONF_W_VOL = 0.1

OUT_DIR = os.getcwd()

print('Fetching OHLCV via pagination...')
exchange = getattr(ccxt, EXCHANGE_ID)()
now_ms = exchange.milliseconds()
since_ms = now_ms - int(HIST_DAYS * 24 * 60 * 60 * 1000)
all_ohlcv = []
fetch_since = since_ms
calls = 0
while True:
    calls += 1
    print(f' fetch call {calls}, since={pd.to_datetime(fetch_since, unit="ms", utc=True)}')
    batch = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, since=fetch_since, limit=LIMIT)
    if not batch:
        break
    all_ohlcv.extend(batch)
    last_ts = batch[-1][0]
    fetch_since = last_ts + 1
    if fetch_since >= now_ms:
        break
    # safety: avoid runaway
    if len(all_ohlcv) > HIST_DAYS * 24 * 4 * 2:
        break
    time.sleep(0.2)

if not all_ohlcv:
    raise SystemExit('No OHLCV fetched; check exchange/symbol/timeframe')

# build dataframe
df = pd.DataFrame(all_ohlcv, columns=['timestamp','open','high','low','close','volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
df.set_index('timestamp', inplace=True)
print('Rows fetched:', len(df))

# indicators
print('Computing indicators...')
df['ema20'] = df['close'].ewm(span=EMA_FAST, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=EMA_SLOW, adjust=False).mean()
# RSI with fallback
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

# pivot detection (ATR prominence)
print('Detecting pivots...')
from math import isnan
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
        df.at[idx,'pivot'] = k

# helper functions
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


# Backtester
print('Running backtest...')

def backtest_goldbach(df, initial_capital=10000.0, risk_pct=BACKTEST_RISK_PCT, slippage=BACKTEST_SLIPPAGE, fee=BACKTEST_FEE):
    df = df.copy().dropna(subset=['ema20','ema50','atr14'])
    capital = initial_capital
    position = 0.0  # positive=long units, negative=short units
    position_side = None
    trades = []
    equity_idx = []
    equity_vals = []
    exposures = []

    for i in range(50, len(df)-1):
        row = df.iloc[i]
        next_open = df.iloc[i+1]['open']

        # record MTM
        mtm = capital + position * row['close']
        equity_idx.append(row.name)
        equity_vals.append(mtm)
        exposures.append(abs(position) * row['close'])

        phase, trend, mom, vol, score, meta = goldbach_phase_with_pdf(row, df_local=df.iloc[:i+1])
        div_bear = meta.get('div_bear')
        div_bull = meta.get('div_bull')

        # compute per-bar confidence (z-blend)
        try:
            rsi_z = (row['rsi14'] - df['rsi14'].mean()) / (df['rsi14'].std() or 1.0)
            bbw_z = (row['bb_w'] - df['bb_w'].mean()) / (df['bb_w'].std() or 1.0)
            ema_z = ((row['ema20'] - row['ema50']) / row['ema50'] - ((df['ema20'] - df['ema50'])/df['ema50']).mean()) / (((df['ema20'] - df['ema50'])/df['ema50']).std() or 1.0)
            conf_score = CONF_W_TRND * ema_z + CONF_W_MOM * rsi_z + CONF_W_VOL * bbw_z
            conf = 1.0 / (1.0 + np.exp(-conf_score))
        except Exception:
            conf = 0.5

        # LONG entry
        if position == 0:
            if trend == 'bull' and (row['close'] <= row['ema20'] * LONG_ENTRY_EMA_BUFFER or (meta.get('entry') and 'pivot low' in str(meta.get('entry')))) and row['rsi14'] >= LONG_ENTRY_RSI_MIN and not div_bear:
                stop = (recent_pivot_level(df.iloc[:i+1], 'low', lookback=200)[1] - 0.5 * row['atr14']) if recent_pivot_level(df.iloc[:i+1], 'low', lookback=200)[1] is not None else row['close'] - STOP_ATR_MULT * row['atr14']
                risk_per_unit = next_open - stop
                if risk_per_unit <= 0:
                    continue
                usd_risk = capital * risk_pct * conf  # scale risk by confidence
                units = usd_risk / risk_per_unit
                entry_price = next_open * (1 + slippage)
                position = units
                position_side = 'long'
                entry = {'side':'long','entry':entry_price,'stop':stop,'units':units,'entry_idx':row.name,'fee':fee,'slippage':slippage,'confidence':conf}
                trades.append(entry.copy())

            # SHORT entry (tightened)
            elif ENABLE_SHORTS and not LONG_ONLY and trend == 'bear' and (row['close'] >= row['ema20'] * 0.998 or (meta.get('entry') and 'pivot high' in str(meta.get('entry')))) and row['rsi14'] < SHORT_RSI_MAX and row['bb_w'] > SHORT_BB_MIN and not div_bull:
                idx_high, lvl_high = recent_pivot_level(df.iloc[:i+1], 'high', lookback=200)
                stop = (lvl_high + 0.5 * row['atr14']) if lvl_high is not None else row['close'] + STOP_ATR_MULT * row['atr14']
                if lvl_high is not None and abs(row['close'] - lvl_high) > SHORT_PROX_ATR_MULT * row['atr14']:
                    continue
                risk_per_unit = stop - next_open if stop > next_open else row['atr14']
                if risk_per_unit <= 0:
                    continue
                usd_risk = capital * risk_pct * conf
                units = usd_risk / risk_per_unit
                entry_price = next_open * (1 - slippage)
                position = -units
                position_side = 'short'
                entry = {'side':'short','entry':entry_price,'stop':stop,'units':units,'entry_idx':row.name,'fee':fee,'slippage':slippage,'confidence':conf}
                trades.append(entry.copy())

        else:
            # Manage open position: check stop or 2x target
            current_price = row['close']
            last = trades[-1]
            stop = last['stop']
            if last['side'] == 'long':
                target = last['entry'] + 2*(last['entry'] - stop)
                if current_price <= stop:
                    exit_price = current_price * (1 - slippage) - fee*current_price
                    pnl = (exit_price - last['entry']) * last['units']
                    capital += pnl
                    last.update({'exit':exit_price,'pnl':pnl,'exit_idx':row.name})
                    position = 0
                    position_side = None
                elif current_price >= target:
                    exit_price = target * (1 - slippage) - fee*target
                    pnl = (exit_price - last['entry']) * last['units']
                    capital += pnl
                    last.update({'exit':exit_price,'pnl':pnl,'exit_idx':row.name})
                    position = 0
                    position_side = None
            else:
                target = last['entry'] - 2*(stop - last['entry'])
                if current_price >= stop:
                    exit_price = current_price * (1 + slippage) + fee*current_price
                    pnl = (last['entry'] - exit_price) * last['units']
                    capital += pnl
                    last.update({'exit':exit_price,'pnl':pnl,'exit_idx':row.name})
                    position = 0
                    position_side = None
                elif current_price <= target:
                    exit_price = target * (1 + slippage) + fee*target
                    pnl = (last['entry'] - exit_price) * last['units']
                    capital += pnl
                    last.update({'exit':exit_price,'pnl':pnl,'exit_idx':row.name})
                    position = 0
                    position_side = None

    # finalize equity series with last bar
    equity_idx.append(df.index[-1])
    equity_vals.append(capital + position * df.iloc[-1]['close'])
    exposures.append(abs(position) * df.iloc[-1]['close'])

    print('Backtest finished. Trades:', len(trades))

    # build trades_df
    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        trades_df['entry_idx'] = pd.to_datetime(trades_df['entry_idx'])
        trades_df['exit_idx'] = pd.to_datetime(trades_df.get('exit_idx'))
        # compute trade_length and return
        trades_df['trade_length_min'] = trades_df.apply(lambda r: (r['exit_idx'] - r['entry_idx']).total_seconds()/60.0 if pd.notna(r.get('exit_idx')) and pd.notna(r['entry_idx']) else None, axis=1)
        trades_df['return_pct'] = trades_df.apply(lambda r: r.get('pnl',0) / (abs(r['entry'] * r['units']) if (r.get('entry') is not None and r.get('units') is not None) else 1), axis=1)

    # save trades
    out_path = os.path.join(OUT_DIR, 'goldbach_trades.csv')
    trades_df.to_csv(out_path, index=False)
    print('Wrote', out_path)

    # attach confidence metadata where possible (already stored per entry)
    try:
        if 'confidence' not in trades_df.columns:
            trades_df['confidence'] = 0.5
            trades_df.to_csv(out_path, index=False)
    except Exception:
        pass

    # equity
    eq = pd.DataFrame({'ts': equity_idx, 'equity': equity_vals}).set_index('ts')
    eq.to_csv(os.path.join(OUT_DIR, 'equity_curve.csv'))

    # metrics
    metrics = {}
    metrics['initial_capital'] = initial_capital
    metrics['final_capital'] = float(eq['equity'].iloc[-1])
    metrics['total_return'] = metrics['final_capital'] / metrics['initial_capital'] - 1.0
    days = (df.index[-1] - df.index[0]).total_seconds() / 86400.0
    metrics['days'] = days
    metrics['CAGR'] = (metrics['final_capital'] / metrics['initial_capital']) ** (365.0 / days) - 1.0 if days>0 else 0.0

    if not trades_df.empty:
        metrics['n_trades'] = len(trades_df)
        metrics['wins'] = int((trades_df['pnl'] > 0).sum())
        metrics['losses'] = int((trades_df['pnl'] <= 0).sum())
        metrics['win_rate'] = metrics['wins'] / metrics['n_trades']
        metrics['avg_pnl'] = float(trades_df['pnl'].mean())
        metrics['median_trade_length_min'] = float(trades_df['trade_length_min'].dropna().median()) if trades_df['trade_length_min'].dropna().size>0 else None
        metrics['avg_return_pct'] = float(trades_df['return_pct'].dropna().mean()) if trades_df['return_pct'].dropna().size>0 else None
    else:
        metrics['n_trades'] = 0

    # exposure
    metrics['avg_exposure_usd'] = float(np.mean(exposures)) if len(exposures)>0 else 0.0
    metrics['max_exposure_usd'] = float(np.max(exposures)) if len(exposures)>0 else 0.0

    # drawdown
    eq['cummax'] = eq['equity'].cummax()
    eq['drawdown'] = (eq['equity'] - eq['cummax']) / eq['cummax']
    metrics['max_drawdown'] = float(eq['drawdown'].min())

    # sharpe-ish
    daily = eq['equity'].resample('1D').last().pct_change().dropna()
    metrics['sharpe_annual'] = float(daily.mean() / daily.std() * (252 ** 0.5)) if (not daily.empty and daily.std()>0) else 0.0

    # write report
    with open(os.path.join(OUT_DIR, 'backtest_report.txt'), 'w') as f:
        f.write('Backtest report\n')
        for k,v in metrics.items():
            f.write(f"{k}: {v}\n")
        f.write('\nSample trades (first 10):\n')
        if not trades_df.empty:
            f.write(trades_df.head(10).to_string(index=False))
        else:
            f.write('No trades')

    # plot
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10,4))
        plt.plot(eq.index, eq['equity'])
        plt.title('Equity Curve')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(OUT_DIR, 'equity_curve.png'))
        print('Wrote equity_curve.png')
    except Exception as e:
        print('Failed to plot:', e)

    return trades_df, metrics


if __name__ == '__main__':
    trades_df, metrics = backtest_goldbach(df)
    print('Done. Metrics:')
    print(metrics)

print('Backtest done. Trades:', len(trades))
trades_df = pd.DataFrame(trades)
if not trades_df.empty:
    trades_df.to_csv('goldbach_trades.csv', index=False)
    print('Wrote goldbach_trades.csv')
else:
    print('No trades generated')
