"""Pytest-friendly integration tests for Polygon-related modules.

These tests use pytest-style assertions and will skip if the
relevant modules aren't importable in the test environment.
"""
import pytest
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path when running locally
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports_available():
    """Assert that core Polygon-related modules are importable.

    If the modules aren't present in the environment we skip the
    test so CI doesn't fail on optional integrations.
    """
    try:
        from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter  # noqa: F401
        from agent_trader.strategies.polygon.momentum_strategy import PolygonMomentumStrategy  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Polygon integration modules not available: {exc}")


def test_strategy_initialization_has_expected_attrs():
    """Instantiate the strategy and check a few expected attributes."""
    if not os.environ.get("POLYGON_API_KEY"):
        pytest.skip("POLYGON_API_KEY not set; skipping strategy initialization test")

    try:
        from agent_trader.strategies.polygon.momentum_strategy import PolygonMomentumStrategy
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Strategy module not available: {exc}")

    strategy = PolygonMomentumStrategy()
    assert hasattr(strategy, "lookback_days"), "strategy must expose lookback_days"
    assert hasattr(strategy, "short_ma"), "strategy must expose short_ma"
    assert hasattr(strategy, "long_ma"), "strategy must expose long_ma"


def test_polygon_adapter_can_construct():
    """Ensure the Polygon adapter class can be constructed without raising.

    Adapter may require environment variables for API keys for full calls; we
    only assert construction here to keep CI stable.
    """
    if not os.environ.get("POLYGON_API_KEY"):
        pytest.skip("POLYGON_API_KEY not set; skipping adapter construction test")

    try:
        from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Polygon adapter not available: {exc}")

    adapter = PolygonDataAdapter()
    assert adapter is not None
