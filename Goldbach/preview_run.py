from goldbach_core import fetch_ohlcv_df, compute_indicators_and_pivots, backtest_goldbach, goldbach_phase_with_pdf

print('Fetching small preview...')
df_raw = fetch_ohlcv_df(hist_days=14, limit=500)
df = compute_indicators_and_pivots(df_raw)
print('Fetched rows:', len(df))

r=0.001; s=1.5
trades, metrics, eq = backtest_goldbach(df, initial_capital=10000.0, risk_pct=r, stop_atr_mult=s, target_r=3.0, long_only=True)
print('Preview metrics:', metrics)

last_row = df.iloc[-1]
phase, trend, mom, vol, score, meta = goldbach_phase_with_pdf(last_row, df_local=df)
print('Snapshot phase:', phase)
if not trades.empty:
    print('Last trade confidence:', trades['confidence'].iloc[-1])
else:
    print('No trades in preview')
