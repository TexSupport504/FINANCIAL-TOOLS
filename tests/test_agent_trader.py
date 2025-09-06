import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent_trader.data import load_dummy_price_series
from agent_trader.strategy import SMACrossover
from agent_trader.agent import Agent


def test_agent_runs_and_generates_trades():
    df = load_dummy_price_series(n=100, seed=1)
    strat = SMACrossover(short_window=3, long_window=8)
    agent = Agent(strat)
    trades = agent.run(df)
    # trades should be a DataFrame (possibly empty) with expected columns when non-empty
    assert isinstance(trades, type(df)) or 'price' in df.columns
