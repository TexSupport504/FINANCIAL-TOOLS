import sys, os  # noqa: E401
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from goldbach_core import fetch_ohlcv_df, compute_indicators_and_pivots, backtest_goldbach
from agent_trader import performance


def run_preview_and_report():
    print('Fetching small preview...')
    df_raw = fetch_ohlcv_df(hist_days=14, limit=500)
    df = compute_indicators_and_pivots(df_raw)
    print('Fetched rows:', len(df))

    trades, metrics, eq = backtest_goldbach(df, initial_capital=10000.0, risk_pct=0.001, stop_atr_mult=1.5, target_r=3.0, long_only=True)
    print('Backtest metrics (goldbach):', metrics)

    # convert eq (DataFrame index=ts, equity) to agent_trader expected input
    eq_df = eq.copy()
    eq_df.index = eq_df.index.tz_convert(None) if hasattr(eq_df.index, 'tz') else eq_df.index
    perf = performance.compute_metrics_from_equity(eq_df)
    print('Unified performance metrics:', perf)


if __name__ == '__main__':
    run_preview_and_report()
