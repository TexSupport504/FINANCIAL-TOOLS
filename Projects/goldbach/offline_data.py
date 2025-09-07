import pandas as pd
import numpy as np


def generate_synthetic_ohlcv(n=1000, seed=0, start_price=1000.0, freq='15T'):
    """Return a deterministic synthetic OHLCV DataFrame with a datetime index.

    freq '15T' yields 15-minute intervals; this function uses a simple random walk with drift.
    """
    rng = np.random.default_rng(seed)
    returns = rng.normal(loc=0.0002, scale=0.01, size=n)
    price = start_price * (1 + returns).cumprod()
    # build OHLC from price series by adding small variation
    open_ = price
    close = price * (1 + rng.normal(scale=0.001, size=n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(scale=0.002, size=n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(scale=0.002, size=n)))
    volume = rng.integers(100, 1000, size=n)
    idx = pd.date_range(end=pd.Timestamp.now(), periods=n, freq=freq)
    df = pd.DataFrame({'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume}, index=idx)
    df.index.name = 'timestamp'
    return df
