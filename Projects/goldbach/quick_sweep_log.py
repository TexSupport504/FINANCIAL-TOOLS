import traceback
from goldbach_core import fetch_ohlcv_df, compute_indicators_and_pivots, backtest_goldbach, goldbach_phase_with_pdf
import pandas as pd
import matplotlib.pyplot as plt

def run_quick_sweep():
    LOG='sweep_log.txt'
    with open(LOG,'w') as log:
        try:
            log.write('Starting quick sweep\n')
            df_raw = fetch_ohlcv_df(hist_days=14, limit=500)
            log.write(f'Fetched rows: {len(df_raw)}\n')
            df = compute_indicators_and_pivots(df_raw)
            log.write(f'Computed indicators rows: {len(df)}\n')

            risk_grid=[0.001, 0.0015]
            stop_grid=[1.25,1.5]
            results=[]
            total = len(risk_grid)*len(stop_grid)
            for idx, (r,s) in enumerate([(a,b) for a in risk_grid for b in stop_grid], start=1):
                log.write(f'Running {idx}/{total}: r={r}, s={s}\n')
                trades, metrics, eq = backtest_goldbach(df, initial_capital=10000.0, risk_pct=r, stop_atr_mult=s, target_r=3.0, long_only=True)
                log.write(f" -> final_capital={metrics['final_capital']}, max_dd={metrics['max_drawdown']}, n_trades={metrics['n_trades']}\n")
                results.append({'risk_pct':r, 'stop_atr_mult':s, 'final_capital':metrics['final_capital'], 'max_drawdown':metrics['max_drawdown'], 'n_trades':metrics['n_trades'], 'win_rate':metrics.get('win_rate',None)})

            pdf = pd.DataFrame(results)
            pdf.to_csv('quick_sensitivity_grid.csv', index=False)
            log.write('Wrote quick_sensitivity_grid.csv\n')

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
            plt.title(f'Quick annotated price - phase {phase}')
            plt.tight_layout()
            plt.savefig('quick_annotated_price.png')
            log.write('Wrote quick_annotated_price.png\n')
            log.write('Quick sweep complete\n')
        except Exception as e:
            log.write('ERROR during quick sweep:\n')
            traceback.print_exc(file=log)
            log.write('\n')


if __name__ == '__main__':
    run_quick_sweep()
