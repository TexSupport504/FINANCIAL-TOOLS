import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
from agent_trader.performance import compute_metrics_from_equity
import pytest


def test_performance_metrics_basic():
    idx = pd.date_range('2020-01-01', periods=5, freq='D')
    eq = pd.DataFrame({'equity': [1000, 1010, 1020, 980, 1100]}, index=idx)
    metrics = compute_metrics_from_equity(eq)
    assert 'total_return' in metrics
    assert metrics['total_return'] == pytest.approx(0.10)
    assert 'max_drawdown' in metrics
