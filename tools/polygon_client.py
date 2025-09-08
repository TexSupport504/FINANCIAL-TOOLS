"""
Small Polygon client used by tools for per-ticker price lookups.

Provides get_last_trade_price(ticker, api_key=None, files_host=None)
which returns a float price or None.

This module is intentionally small and dependency-light so unit tests can
mock requests.get easily.
"""
from typing import Optional
import os
import urllib.parse
import requests


def get_last_trade_price(ticker: str, api_key: Optional[str] = None, files_host: Optional[str] = None) -> Optional[float]:
    """Try Polygon files host first, then api.polygon.io. Return price or None."""
    if not ticker:
        return None

    key = api_key or os.getenv('POLYGON_API_KEY')
    if not key:
        return None

    hosts = []
    if files_host:
        hosts.append(files_host.rstrip('/'))
    hosts.append('https://api.polygon.io')

    for host in hosts:
        url = f"{host}/v2/last/trade/{urllib.parse.quote(ticker)}?apiKey={key}"
        try:
            resp = requests.get(url, timeout=10)
        except Exception:
            continue

        if resp.status_code == 200:
            try:
                j = resp.json()
                r = j.get('results') or j.get('result')
                if isinstance(r, dict):
                    p = r.get('p') if r.get('p') is not None else r.get('price')
                    return float(p) if p is not None else None
            except Exception:
                return None
        elif resp.status_code in (401, 403):
            # unauthorized for this key
            return None
        else:
            # try next host
            continue

    return None
