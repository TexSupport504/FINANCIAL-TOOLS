from goldbach_core import fetch_ohlcv_df, compute_indicators_and_pivots, backtest_goldbach, goldbach_phase_with_pdf
import pandas as pd
import matplotlib.pyplot as plt

print('Running single tuned backtest with stop_source debug...')

# Fetch data
df_raw = fetch_ohlcv_df(hist_days=120, limit=1000)
print(f'Fetched {len(df_raw)} OHLCV rows')
df = compute_indicators_and_pivots(df_raw)
print(f'Computed indicators; {len(df)} rows ready')

# Run single backtest with mid-range parameters
risk_pct = 0.0015
stop_atr_mult = 1.5
target_r = 3.0
long_only = True

print(f'Running backtest: risk_pct={risk_pct}, stop_atr_mult={stop_atr_mult}, target_r={target_r}, long_only={long_only}')
trades_df, metrics, equity = backtest_goldbach(df, initial_capital=10000.0, risk_pct=risk_pct, stop_atr_mult=stop_atr_mult, target_r=target_r, long_only=long_only)

# Save detailed outputs
trades_df.to_csv('tuned_trades_detailed.csv', index=False)
print('Wrote tuned_trades_detailed.csv')

# Write backtest report
with open('tuned_backtest_report.txt', 'w') as f:
    f.write('Tuned Backtest Report (with stop_source debug)\n')
    f.write(f'Parameters: risk_pct={risk_pct}, stop_atr_mult={stop_atr_mult}, target_r={target_r}, long_only={long_only}\n\n')
    for k, v in metrics.items():
        f.write(f'{k}: {v}\n')
    f.write('\nSample trades (first 10):\n')
    if not trades_df.empty:
        f.write(trades_df.head(10).to_string(index=False))
        # Count stop sources
        if 'stop_source' in trades_df.columns:
            stop_counts = trades_df['stop_source'].value_counts()
            f.write(f'\n\nStop source distribution:\n{stop_counts.to_string()}\n')
print('Wrote tuned_backtest_report.txt')

# Create annotated chart with phase info
last_row = df.iloc[-1]
phase, trend, mom, vol, score, meta = goldbach_phase_with_pdf(last_row, df_local=df)

plt.figure(figsize=(14,8))
plt.subplot(2,1,1)
plt.plot(df.index, df['close'], label='close', alpha=0.8)
pv = df.dropna(subset=['pivot'])
plt.scatter(pv.index[pv['pivot']=='high'], pv['close'][pv['pivot']=='high'], marker='v', color='red', label='pivot high', s=30)
plt.scatter(pv.index[pv['pivot']=='low'], pv['close'][pv['pivot']=='low'], marker='^', color='green', label='pivot low', s=30)

# Add trade entries/exits if available
if not trades_df.empty and 'entry_idx' in trades_df.columns:
    entries = trades_df.dropna(subset=['entry_idx'])
    for _, trade in entries.iterrows():
        color = 'blue' if trade['side'] == 'long' else 'orange'
        plt.axvline(trade['entry_idx'], color=color, alpha=0.3, linestyle='--')

stop_suggestion = meta.get('stop')
if stop_suggestion is not None:
    plt.axhline(stop_suggestion, color='orange', linestyle='--', label=f'suggested stop: {stop_suggestion:.2f}')

plt.title(f'Tuned Backtest: Price with Pivots\nPhase: {phase} | Trend: {trend} | Last Close: {last_row["close"]:.2f}')
plt.legend()
plt.ylabel('Price')

# Bottom subplot: equity curve
plt.subplot(2,1,2)
plt.plot(equity.index, equity['equity'], label='equity curve', color='green')
plt.title('Equity Curve')
plt.xlabel('Time')
plt.ylabel('Equity ($)')
plt.legend()

plt.tight_layout()
plt.savefig('tuned_annotated_chart.png', dpi=100)
print('Wrote tuned_annotated_chart.png')

# Current snapshot
try:
    rsi_z = (last_row['rsi14'] - df['rsi14'].mean()) / (df['rsi14'].std() or 1.0)
    bbw_z = (last_row['bb_w'] - df['bb_w'].mean()) / (df['bb_w'].std() or 1.0)
    ema_z = ((last_row['ema20'] - last_row['ema50']) / last_row['ema50'] - ((df['ema20'] - df['ema50']) / df['ema50']).mean()) / (((df['ema20'] - df['ema50']) / df['ema50']).std() or 1.0)
    conf_score = 0.5 * ema_z + 0.4 * rsi_z + 0.1 * bbw_z
    confidence = 1.0 / (1.0 + pd.np.exp(-conf_score))
except:
    confidence = 0.5

with open('current_snapshot.txt', 'w') as f:
    f.write('CURRENT GOLDBACH SNAPSHOT\n')
    f.write('=' * 30 + '\n')
    f.write(f'Timestamp: {df.index[-1]}\n')
    f.write(f'Close: {last_row["close"]:.2f}\n')
    f.write(f'Phase: {phase}\n')
    f.write(f'Trend: {trend}\n')
    f.write(f'Momentum: {mom}\n')
    f.write(f'Volatility: {vol}\n')
    f.write(f'Phase Score: {score}\n')
    f.write(f'Confidence: {confidence:.3f}\n')
    f.write(f'Entry Suggestion: {meta.get("entry", "N/A")}\n')
    f.write(f'Stop Suggestion: {meta.get("stop", "N/A")}\n')
print('Wrote current_snapshot.txt')

print('Tuned backtest complete!')
