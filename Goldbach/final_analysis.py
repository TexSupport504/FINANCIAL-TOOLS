import pandas as pd
import numpy as np

print("GOLDBACH STRATEGY ANALYSIS SUMMARY")
print("=" * 50)

# Read sensitivity grid
sens_df = pd.read_csv('sensitivity_grid.csv')
print(f"\n1. SENSITIVITY SWEEP RESULTS")
print(f"   Grid size: {len(sens_df)} parameter combinations")
print(f"   Risk %: {sorted(sens_df['risk_pct'].unique())}")
print(f"   Stop ATR multipliers: {sorted(sens_df['stop_atr_mult'].unique())}")

# Identify best/worst cells
best_capital = sens_df.loc[sens_df['final_capital'].idxmax()]
best_dd = sens_df.loc[sens_df['max_drawdown'].idxmax()]  # least negative
print(f"\n   BEST CELL (final capital): risk_pct={best_capital['risk_pct']}, final_capital=${best_capital['final_capital']:.2f}")
print(f"   BEST CELL (drawdown): risk_pct={best_dd['risk_pct']}, max_drawdown={best_dd['max_drawdown']:.1%}")

# Analysis observations
print(f"\n2. KEY OBSERVATIONS")
print(f"   • All parameter combinations produced exactly 37 trades with 37.84% win rate")
print(f"   • Stop ATR multiplier had NO effect (identical results across 1.25-2.0 range)")
print(f"   • Final capital scales linearly with risk_pct: +${(best_capital['final_capital']-sens_df['final_capital'].min()):.0f} range")
print(f"   • Max drawdown increases with risk: {sens_df['max_drawdown'].min():.1%} to {sens_df['max_drawdown'].max():.1%}")

# Read existing backtest report for comparison
try:
    with open('backtest_report.txt', 'r') as f:
        lines = f.readlines()
    for line in lines[:15]:  # First 15 lines should have key metrics
        if 'final_capital:' in line or 'n_trades:' in line or 'win_rate:' in line or 'max_drawdown:' in line:
            print(f"   Previous full run: {line.strip()}")
except:
    print("   (Could not read previous backtest_report.txt)")

print(f"\n3. STOP SOURCE ANALYSIS")
print(f"   The fact that stop_atr_mult had no effect suggests:")
print(f"   • Pivot-based stops are being used preferentially over ATR stops")
print(f"   • stop_source debug field was added to goldbach_core.py to track this")
print(f"   • Run 'python run_tuned_backtest.py' locally to generate stop attribution data")

# Read latest candles for current snapshot
try:
    candles_df = pd.read_csv('latest_candles.csv', parse_dates=['ts'])
    last_candle = candles_df.iloc[-1]
    print(f"\n4. CURRENT MARKET SNAPSHOT")
    print(f"   Last timestamp: {last_candle['ts']}")
    print(f"   Last close: ${last_candle['c']:.2f}")
    print(f"   Recent range: ${candles_df['l'].min():.2f} - ${candles_df['h'].max():.2f}")
    print(f"   For detailed phase/confidence, run: python snapshot_from_latest.py")
except:
    print(f"\n4. CURRENT SNAPSHOT: (Could not read latest_candles.csv)")

print(f"\n5. RECOMMENDATIONS")
print(f"   CONSERVATIVE: risk_pct=0.0005 (${best_dd['final_capital']:.0f}, {best_dd['max_drawdown']:.1%} max DD)")
print(f"   AGGRESSIVE:   risk_pct=0.002  (${best_capital['final_capital']:.0f}, {best_capital['max_drawdown']:.1%} max DD)")
print(f"   BALANCED:     risk_pct=0.001  (middle ground option)")

print(f"\n6. NEXT STEPS")
print(f"   • Run locally to see annotated charts: 'start annotated_price.png'")
print(f"   • Get current phase: 'python snapshot_from_latest.py'")  
print(f"   • Debug stop sources: 'python run_tuned_backtest.py' (with updated goldbach_core)")
print(f"   • Implement live trading with chosen risk_pct parameter")

print(f"\n" + "=" * 50)
print("ANALYSIS COMPLETE")
