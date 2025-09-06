## Prompt templates for the Repo Assistant

## Prompt Templates for the Repo Assistant

**🚨 CRITICAL RULE - NO DEMO DATA:** Never use simulated, demo, mock, or fake data for financial analysis. If there is any issue accessing real market data, immediately notify the user and begin debugging/fixing the data source. Always prioritize data accuracy and authenticity - trading analysis with fake data leads to poor decisions and financial losses. See `.github/copilot-instructions.md` for full data quality guidelines.

Allowed live data providers: Coinbase (preferred for crypto spot) and Polygon (aggregates/historical and secondary live source). Do not query or fall back to other exchanges (for example, Binance) unless the user explicitly authorizes it.

## Testing & Debugging Template

Run pytest for the target test files (project-scoped). Collect failing tests and stack traces. Make the smallest code change and/or add tests to fix the failure. Run the tests again. Deliver: brief failure summary, the patch files edited, and the new test output.

## Implement a small feature

Goal: `<one-sentence>`

Files to inspect: `<file paths>`

Tests to add: `<path/to/test>`

Constraints: `<max new deps, style>`

Acceptance: tests for the affected project pass.

Steps for the agent:

- Add tests demonstrating expected behavior.
- Implement minimal code to make tests pass.
- Run tests and include results.

## Create an adapter between projects

Task: Create an adapter module that converts `<source>` trades/equity into the `agent_trader` metrics format.

Deliverables:

- adapter module under `<project>/adapters`
- small demo script
- unit test using deterministic synthetic data

## New strategy template

Add `agent_trader/strategies/<name>.py` implementing a class with `generate_signals(prices: pd.Series) -> pd.Series`.

Add example runner and tests under `tests/test_strategy_<name>.py`.

Usage note: replace placeholders and run the tests for the target project only.

