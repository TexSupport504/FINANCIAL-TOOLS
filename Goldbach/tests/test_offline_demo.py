import sys
import os
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, repo_root)
# also ensure agent_trader is importable from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(repo_root, '..')))
from offline_demo import run_demo
import pandas as pd


def test_offline_demo_runs_and_returns_metrics():
    metrics, eq = run_demo(n=200, seed=42)
    assert isinstance(metrics, dict)
    assert 'total_return' in metrics
    assert isinstance(eq, pd.DataFrame)
    # equity should have at least one point
    assert len(eq) >= 1
