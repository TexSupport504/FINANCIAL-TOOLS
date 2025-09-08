# FINANCIAL-TOOLS — History cleaner & pricing

This repository contains scripts to clean a broker `History.xlsx` export, enrich positions with live prices (Polygon primary, yfinance fallback), and produce a cleaned CSV and a small portfolio analysis.

Quick local steps
1. Install dev/test deps (pytest is required to run unit tests):

```powershell
python -m pip install -r requirements-dev.txt
```

2. Run the cleaner (writes `history_cleaned.csv` and `history_analysis.txt`):

```powershell
python tools/clean_history_and_analyze.py
```

3. Run unit tests locally:

```powershell
pytest -q
```

Environment
- The scripts read `POLYGON_API_KEY` from the environment or `.env` if you use a loader. You can also pass `POLYGON_FILES_HOST` to force the S3/files host (e.g. `https://files.polygon.io`).

CI
- A GitHub Actions workflow is included at `.github/workflows/ci.yml`. On push or PR it will:
  - checkout the repo
  - install Python and dev requirements from `requirements-dev.txt`
  - run `pytest`

Notes
- Tests mock network calls; they run offline and only require the packages in `requirements-dev.txt`.
- If you hit issues with yfinance and a local SQLite cache, see `tools/check_sqlite_integrity.py` and `tools/repair_local_sqlite_caches.py` for diagnostics.
FINANCIAL-TOOLS (multi-project repository)

This repository groups multiple financial projects. Current projects:

- Options-Backtest-Engine/ — existing project for options backtesting.
- Goldbach/ — existing research/backtest project.
- agent_trader/ — new template project: agent-driven trading strategy for stocks/crypto.

See each project folder for its README and usage notes.
