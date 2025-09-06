import pandas as pd
import numpy as np


def compute_metrics_from_equity(eq_df: pd.DataFrame) -> dict:
    """Given an equity DataFrame with index=time and column 'equity', return metrics.

    Returns: dict with total_return, cagr, max_drawdown, sharpe
    """
    if eq_df.empty:
        return {}
    eq = eq_df['equity'].sort_index()
    start_val = float(eq.iloc[0])
    end_val = float(eq.iloc[-1])
    total_return = (end_val / start_val) - 1.0 if start_val > 0 else np.nan

    # compute years between first and last
    delta = eq.index[-1] - eq.index[0]
    years = delta.total_seconds() / (3600 * 24 * 365)
    if years <= 0:
        cagr = np.nan
    else:
        cagr = (end_val / start_val) ** (1.0 / years) - 1.0

    # drawdown
    cummax = eq.cummax()
    drawdown = (eq - cummax) / cummax
    max_drawdown = float(drawdown.min())

    # returns series (periodic)
    rets = eq.pct_change().dropna()
    if rets.empty or years <= 0:
        sharpe = np.nan
    else:
        periods_per_year = len(rets) / years
        sharpe = (rets.mean() / rets.std()) * np.sqrt(periods_per_year) if rets.std() != 0 else np.nan

    return {
        'total_return': float(total_return),
        'cagr': float(cagr) if not np.isnan(cagr) else np.nan,
        'max_drawdown': float(max_drawdown),
        'sharpe': float(sharpe) if not np.isnan(sharpe) else np.nan,
    }
