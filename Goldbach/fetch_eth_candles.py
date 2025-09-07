import ccxt
import pandas as pd
ex = ccxt.coinbase()
ohlcv = ex.fetch_ohlcv('ETH/USD','15m',limit=5)
df = pd.DataFrame(ohlcv, columns=['ts','o','h','l','c','v'])
df['ts'] = pd.to_datetime(df['ts'], unit='ms', utc=True)
df.to_csv('latest_candles.csv', index=False)
print('wrote latest_candles.csv')
