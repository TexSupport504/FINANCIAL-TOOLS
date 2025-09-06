## Prompt templates for the Repo Assistant

### Fix failing tests

Run pytest for: `<list of test files>`. Collect failing tests and stack traces. Make the smallest code change and/or add tests to fix the failure. Run the tests again. Deliver: brief failure summary, patch files edited, and the new test output.

### Implement a small feature

Goal: `<one-sentence>`

Files to inspect: `<file paths>`

Tests to add: `<path/to/test>`

Constraints: `<max new deps, style>`

Acceptance: tests for affected project pass.

Steps for the agent:

- Add tests demonstrating expected behavior.
- Implement minimal code to make tests pass.
- Run tests and include results.

### Create an adapter between projects

Task: Create an adapter module that converts `<source>` trades/equity into `agent_trader` metrics.

Deliverables:

- adapter module under `<project>/adapters`
- small demo script
- unit test using synthetic data

### New strategy template

Add `agent_trader/strategies/<name>.py` implementing a class with `generate_signals(prices: pd.Series) -> pd.Series`.

Add example runner and tests under `tests/test_strategy_<name>.py`.

Usage note: replace placeholders and run the tests for the target project only.
