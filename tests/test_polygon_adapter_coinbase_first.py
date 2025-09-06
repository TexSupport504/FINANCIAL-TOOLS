import os
import sys

# Ensure workspace root is on sys.path so tests can import local packages
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter, MarketSnapshot


class DummyAdapter(PolygonDataAdapter):
    def __init__(self):
        # avoid requiring POLYGON_API_KEY for unit test
        super().__init__(api_key='test')
        self._coinbase_called = False
        self._polygon_called = False

    def get_crypto_spot_coinbase(self, symbol):
        self._coinbase_called = True
        # simulate Coinbase returning a snapshot
        return MarketSnapshot(symbol=symbol.upper(), price=100.0, change=0.0, change_percent=0.0, volume=0, timestamp=None, source='coinbase')

    def get_session(self):
        # prevent actual HTTP calls in tests; raise if Polygon would be used
        class _S:
            def get(self, *args, **kwargs):
                raise RuntimeError("Polygon should not be called when Coinbase is available")
        return _S()


def test_coinbase_preferred_for_crypto():
    a = DummyAdapter()
    snap = a.get_market_snapshot('X:ETHUSD')
    assert snap is not None
    assert snap.source == 'coinbase'
    assert a._coinbase_called is True

