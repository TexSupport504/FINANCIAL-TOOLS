import itertools
import pandas as pd
import matplotlib.pyplot as plt
from goldbach_core import fetch_ohlcv_df, compute_indicators_and_pivots, backtest_goldbach, goldbach_phase_with_pdf, recent_pivot_level

OUT_CSV = 'sensitivity_grid.csv'
results = []

print('Fetching OHLCV for sensitivity sweep...')
df_raw = fetch_ohlcv_df(hist_days=120, limit=1000)
print('Fetched rows:', len(df_raw))
df = compute_indicators_and_pivots(df_raw)
print('Computed indicators; rows with indicators:', len(df))

risk_grid = [0.0005, 0.001, 0.0015, 0.002]
stop_grid = [1.25, 1.5, 1.75, 2.0]

for idx, (r, s) in enumerate(itertools.product(risk_grid, stop_grid), start=1):
    print(f'Running grid {idx}/{len(risk_grid)*len(stop_grid)}: risk={r}, stop_atr_mult={s}')
    try:
        trades, metrics, eq = backtest_goldbach(df, initial_capital=10000.0, risk_pct=r, stop_atr_mult=s, target_r=3.0, long_only=True)
        results.append({'risk_pct': r, 'stop_atr_mult': s, 'final_capital': metrics['final_capital'], 'max_drawdown': metrics['max_drawdown'], 'n_trades': metrics['n_trades'], 'win_rate': metrics.get('win_rate', None)})
        print(' -> done; final_capital=', metrics['final_capital'], 'max_dd=', metrics['max_drawdown'])
    except Exception as e:
        print(' -> ERROR for grid', r, s, ':', e)
        results.append({'risk_pct': r, 'stop_atr_mult': s, 'final_capital': None, 'max_drawdown': None, 'n_trades': 0, 'win_rate': None})

res_df = pd.DataFrame(results)
res_df.to_csv(OUT_CSV, index=False)
print('Wrote', OUT_CSV)

# create annotated price chart with pivots and last suggested entry/stop using latest df
last_row = df.iloc[-1]
phase, trend, mom, vol, score, meta = goldbach_phase_with_pdf(last_row, df_local=df)
entry = meta.get('entry')
stop = meta.get('stop')

plt.figure(figsize=(12,6))
plt.plot(df.index, df['close'], label='close')
pv = df.dropna(subset=['pivot'])
plt.scatter(pv.index[pv['pivot']=='high'], pv['close'][pv['pivot']=='high'], marker='v', color='red', label='pivot high')
plt.scatter(pv.index[pv['pivot']=='low'], pv['close'][pv['pivot']=='low'], marker='^', color='green', label='pivot low')
plt.title(f'Price with pivots - phase: {phase} - last close {last_row["close"]:.2f}')
if stop is not None:
    plt.axhline(stop, color='orange', linestyle='--', label='suggested stop')
plt.legend()
plt.tight_layout()
plt.savefig('annotated_price.png')
print('Wrote annotated_price.png')

if __name__ == '__main__':
    print('Sensitivity sweep complete')
