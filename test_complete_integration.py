"""Complete integration test: Goldbach Knowledge + Polygon Data"""
import sys
from pathlib import Path
import os
import pytest

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_goldbach_knowledge():
    """Test Goldbach knowledge base access."""
    from agent_trader.knowledge_base import search_goldbach, get_goldbach_strategy

    # Test search returns results
    results = search_goldbach("PO3 premium discount", top_k=3)
    assert results is not None
    assert isinstance(results, list)

    # Test strategy access and PO3 levels
    strategy = get_goldbach_strategy()
    assert 'po3_levels' in strategy
    po3_levels = strategy['po3_levels']['levels']
    assert isinstance(po3_levels, list)
    assert len(po3_levels) > 0


def test_polygon_data():
    """Test Polygon.io Data Access."""
    from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter

    # Get API key from environment or .env; skip test if not present
    api_key = os.getenv('POLYGON_API_KEY')
    if not api_key:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('POLYGON_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
        except FileNotFoundError:
            pass

    if not api_key:
        pytest.skip("No POLYGON_API_KEY available for integration test")

    adapter = PolygonDataAdapter(api_key)

    # Historical bars
    bars = adapter.get_price_bars('AAPL', 'day', limit=5)
    assert hasattr(bars, 'empty')

    # News retrieval
    news = adapter.get_ticker_news('AAPL', limit=3)
    assert isinstance(news, (list, type(None)))


def test_integration():
    """Test the complete integration."""
    from agent_trader.knowledge_base import get_kb

    kb = get_kb()

    # Get PO3 levels from Goldbach knowledge
    po3_info = kb.get_po3_levels()
    assert 'levels' in po3_info
    po3_levels = po3_info['levels']
    assert isinstance(po3_levels, list)

    # Get AMD phase information
    amd_info = kb.get_amd_phases()
    assert 'sessions' in amd_info
    sessions = list(amd_info['sessions'].keys())
    assert isinstance(sessions, list)

    # Get premium/discount knowledge
    premium_info = kb.get_premium_discount_levels()
    assert 'concept' in premium_info

# Tests are executed via pytest; no CLI runner here.
