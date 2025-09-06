import os
import sys
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter, MarketSnapshot


class DummyAdapter(PolygonDataAdapter):
    def __init__(self):
        super().__init__(api_key='test')
        self.called_polygon = False

    def get_crypto_spot_coinbase(self, symbol):
        # Simulate Coinbase being unavailable
        return None

    def get_session(self):
        # Simulate Polygon returning 403
        class _S:
            def get(self, *args, **kwargs):
                class Resp:
                    status_code = 403

                    def json(self):
                        return {'message': 'NOT_AUTHORIZED'}

                    def raise_for_status(self):
                        raise Exception('403')

                return Resp()

        return _S()


def test_polygon_permission_error_propagates():
    a = DummyAdapter()
    try:
        a.get_market_snapshot('X:ETHUSD')
        assert False, "Expected PermissionError to be raised"
    except PermissionError:
        pass


def test_file_logging_records_coinbase_snapshot(tmp_path):
    class LogAdapter(PolygonDataAdapter):
        def __init__(self):
            super().__init__(api_key='test')

        def get_crypto_spot_coinbase(self, symbol):
            return MarketSnapshot(symbol=symbol.upper(), price=123.45, change=0.0, change_percent=0.0, volume=0, timestamp=None, source='coinbase')

    a = LogAdapter()
    log_file = Path(tmp_path) / "adapter.log"
    a.enable_file_logging(str(log_file))

    snap = a.get_market_snapshot('X:ETHUSD')
    assert snap is not None
    # flush handlers
    for h in a.logger.handlers:
        h.flush()

    text = log_file.read_text()
    assert 'Returning Coinbase snapshot' in text
