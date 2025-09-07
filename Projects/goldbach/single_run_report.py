from goldbach_core import fetch_ohlcv_df, compute_indicators_and_pivots, backtest_goldbach, goldbach_phase_with_pdf
import matplotlib.pyplot as plt

print('Running single run...')
df_raw = fetch_ohlcv_df(hist_days=120, limit=1000)
df = compute_indicators_and_pivots(df_raw)
trades, metrics, eq = backtest_goldbach(df, initial_capital=10000.0, risk_pct=0.001, stop_atr_mult=1.5, target_r=3.0, long_only=True)

with open('single_run_report.txt','w') as f:
    f.write(str(metrics) + '\n')
    if not trades.empty:
        trades.to_csv('single_run_trades.csv', index=False)
        f.write('Wrote trades CSV\n')

print('Saved single run outputs')
# annotated price
last_row = df.iloc[-1]
phase, trend, mom, vol, score, meta = goldbach_phase_with_pdf(last_row, df_local=df)
stop = meta.get('stop')
plt.figure(figsize=(10,4))
plt.plot(df.index, df['close'], label='close')
pv = df.dropna(subset=['pivot'])
plt.scatter(pv.index[pv['pivot']=='high'], pv['close'][pv['pivot']=='high'], marker='v', color='red')
plt.scatter(pv.index[pv['pivot']=='low'], pv['close'][pv['pivot']=='low'], marker='^', color='green')
if stop is not None:
    plt.axhline(stop, color='orange', linestyle='--')
plt.title(f'Annotated price - phase {phase}')
plt.tight_layout()
plt.savefig('single_annotated_price.png')
print('Wrote single_annotated_price.png')
