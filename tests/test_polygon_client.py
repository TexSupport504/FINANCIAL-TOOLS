import json
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
