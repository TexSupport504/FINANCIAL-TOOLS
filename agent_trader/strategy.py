import pandas as pd


class SMACrossover:
    """Simple moving-average crossover strategy.

    short_window: lookback for short SMA
    long_window: lookback for long SMA
    """

    def __init__(self, short_window=5, long_window=20):
        assert short_window < long_window
        self.short = short_window
        self.long = long_window

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        """Return a Series of signals: 1 for long, 0 for cash/flat."""
        sma_short = prices.rolling(self.short).mean()
        sma_long = prices.rolling(self.long).mean()
        signal = (sma_short > sma_long).astype(int)
        # ensure align index
        signal = signal.reindex(prices.index).fillna(0).astype(int)
        return signal
