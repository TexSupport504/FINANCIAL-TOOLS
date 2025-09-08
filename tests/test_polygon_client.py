import json
import pytest
from unittest.mock import patch, Mock

from tools.polygon_client import get_last_trade_price


def make_resp(status_code=200, data=None):
    m = Mock()
    m.status_code = status_code
    import json
    import os
    import requests
    import pytest
    from unittest.mock import patch, Mock

    from tools.polygon_client import get_last_trade_price


    def make_resp(status_code=200, data=None):
        m = Mock()
        m.status_code = status_code
        if data is None:
            data = {'results': {'p': 1.23}}
        m.json.return_value = data
        return m


    @patch('tools.polygon_client.requests.get')
    def test_files_host_then_api(mock_get):
        # First call (files host) returns 404, second call (api host) returns 200
        mock_get.side_effect = [make_resp(404, {}), make_resp(200, {'results': {'p': 5.5}})]
        price = get_last_trade_price('XYZ', api_key='key', files_host='https://files.polygon.io')
        assert price == 5.5


    @patch('tools.polygon_client.requests.get')
    def test_files_host_success(mock_get):
        mock_get.return_value = make_resp(200, {'results': {'p': 9.99}})
        price = get_last_trade_price('ABC', api_key='key', files_host='https://files.polygon.io')
        assert price == 9.99


    @patch('tools.polygon_client.requests.get')
    def test_unauthorized_returns_none(mock_get):
        mock_get.return_value = make_resp(403, {})
        price = get_last_trade_price('DEF', api_key='key', files_host='https://files.polygon.io')
        assert price is None


    @patch('tools.polygon_client.requests.get')
    def test_empty_ticker_returns_none(mock_get):
        # empty ticker should short-circuit before any network call
        price = get_last_trade_price('', api_key='key', files_host='https://files.polygon.io')
        assert price is None
        mock_get.assert_not_called()


    def test_no_api_key_env_returns_none(monkeypatch):
        # ensure absence of API key (env + arg) returns None
        monkeypatch.delenv('POLYGON_API_KEY', raising=False)
        assert get_last_trade_price('XYZ', api_key=None, files_host='https://files.polygon.io') is None


    @patch('tools.polygon_client.requests.get')
    def test_result_key_price_field(mock_get):
        # API might return `result` with `price` instead of `results.p`
        mock_get.return_value = make_resp(200, {'result': {'price': 7.25}})
        price = get_last_trade_price('GHI', api_key='key')
        assert price == 7.25


    @patch('tools.polygon_client.requests.get')
    def test_requests_exception_on_files_host_then_api_success(mock_get):
        # first call raises (files host), then API host returns 200
        def side_effect(url, timeout):
            if 'files.polygon.io' in url:
                raise requests.exceptions.ConnectionError()
            return make_resp(200, {'results': {'p': 4.4}})

        mock_get.side_effect = side_effect
        price = get_last_trade_price('JKL', api_key='key', files_host='https://files.polygon.io')
        assert price == 4.4


    @patch('tools.polygon_client.requests.get')
    def test_malformed_json_returns_none(mock_get):
        m = make_resp(200, {'results': 'not a dict'})
        m.json.side_effect = ValueError("bad json")
        mock_get.return_value = m
        assert get_last_trade_price('MNO', api_key='key') is None
