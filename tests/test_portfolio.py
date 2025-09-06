import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent_trader.portfolio import Portfolio


def test_enter_and_exit_long():
    p = Portfolio(initial_cash=1000.0, position_size=0.5)
    # price 10 -> invest 50% of 1000 = 500 -> buy 50 shares
    p.enter_long(10.0, 't1')
    assert p.position > 0
    assert p.cash <= 1000.0
    # mark
    p.record('t2', 12.0)
    equity = p.current_equity(12.0)
    # exit
    p.exit_long(12.0, 't3')
    assert p.position == 0
    assert p.cash >= 1000.0 or abs(p.cash - 1000.0) < 1e-6
