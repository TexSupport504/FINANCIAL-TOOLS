from agent_trader.data import load_dummy_price_series
from agent_trader.strategy import SMACrossover
from agent_trader.agent import Agent
from agent_trader.portfolio import Portfolio
from agent_trader import performance
import pandas as pd


def main():
    df = load_dummy_price_series(n=400)
    strat = SMACrossover(short_window=5, long_window=30)
    agent = Agent(strat)
    trades = agent.run(df)
    print("Sample trades (first 10):")
    print(trades.head(10))

    # show portfolio summary
    port = agent.portfolio
    last_price = float(df['price'].iloc[-1])
    equity = port.current_equity(last_price)
    print(f"\nPortfolio summary:\n  initial_cash: {port.initial_cash}\n  cash: {port.cash:.2f}\n  position: {port.position}\n  equity: {equity:.2f}")

    # print simple equity series stats
    eq = port.equity_series()
    if not eq.empty:
        returns = eq['equity'].pct_change().dropna()
        print(f"  periods: {len(eq)}  mean ret: {returns.mean():.6f}  std: {returns.std():.6f}")
        metrics = performance.compute_metrics_from_equity(eq)
        print("\nPerformance metrics:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")


if __name__ == '__main__':
    main()
