import pandas as pd
import numpy as np


def load_dummy_price_series(n=200, seed=0):
    """Return a DataFrame with a simple synthetic price series for testing."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(loc=0.0005, scale=0.01, size=n)
    price = 100 * (1 + returns).cumprod()
    # use 'min' for minute frequency (avoids FutureWarning for 'T')
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq='min')
    return pd.DataFrame({"price": price}, index=dates)
