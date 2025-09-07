Minimal ETH 15m tool with a Goldbach-inspired phase labeling.

Files:

- `eth_15m_goldbach.py`: fetches 15m candles for ETH/USDT from Binance, computes indicators, and outputs the current Goldbach phase and last 5 candles.
- `requirements.txt`: Python deps.

Integration with `agent_trader`:

- A helper script `integrate_with_agent.py` is provided to run the existing `backtest_goldbach` function and convert its equity output into the `agent_trader` performance metrics (CAGR, max drawdown, Sharpe). This lets you compare results across projects and reuse the `agent_trader` reporting tools.

How to run (Windows PowerShell):

```powershell
python -m pip install -r requirements.txt
python eth_15m_goldbach.py
```

Notes/assumptions:

- "Goldbach" here is an assumed strategy: trend + momentum + volatility phases derived from moving averages, RSI, and Bollinger Bands. If you have a specific Goldbach algorithm, provide it and I'll integrate.
- Uses public Binance REST API via CCXT (no API key required for public candles).
