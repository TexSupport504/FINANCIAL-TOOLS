agent_trader — template project

This is a lightweight, runnable template that demonstrates an agent pattern and a simple SMA crossover strategy for financial investing/trading (stocks / crypto).

Files:
- `main.py` — entrypoint that runs the agent on dummy data.
- `agent.py` — simple Agent class that iterates over price data and uses the strategy.
- `strategy.py` — SMA crossover strategy implementation.
- `data.py` — dummy data loader (can be swapped with real data sources like yfinance).
- `requirements.txt` — project-specific deps (keeps small for example).

To run:

```powershell
python agent_trader\main.py
```
