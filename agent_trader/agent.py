import pandas as pd
from .portfolio import Portfolio


class Agent:
    """Agent runs a strategy over price data and records simple trades.

    strategy: object with generate_signals(prices: pd.Series) -> pd.Series
    """

    def __init__(self, strategy):
        self.strategy = strategy
        self.trades = []
        self.portfolio = Portfolio()

    def run(self, price_df: pd.DataFrame) -> pd.DataFrame:
        prices = price_df['price']
        signals = self.strategy.generate_signals(prices)
        position = 0
        for ts, sig in signals.items():
            price = float(prices.loc[ts])
            # mark portfolio each step
            self.portfolio.record(ts, price)
            if sig == 1 and position == 0:
                # enter long using portfolio sizing
                self.portfolio.enter_long(price, ts)
                self.trades.append({'time': ts, 'action': 'buy', 'price': price})
                position = 1
            elif sig == 0 and position == 1:
                # exit long
                self.portfolio.exit_long(price, ts)
                self.trades.append({'time': ts, 'action': 'sell', 'price': price})
                position = 0
        return pd.DataFrame(self.trades)
