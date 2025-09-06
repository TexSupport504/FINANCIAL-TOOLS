"""Polygon.io data adapter for FINANCIAL-TOOLS integration.

This module provides a unified interface to Polygon.io market data
that integrates with the existing agent_trader framework.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging
import pandas as pd
from dataclasses import dataclass
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class MarketSnapshot:
    """Standardized market data snapshot.

    Adds a `source` field to record which data provider supplied the snapshot
    (e.g., 'coinbase', 'polygon', 'binance').
    """
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    prev_close: Optional[float] = None
    source: Optional[str] = None


class PolygonDataAdapter:
    """Main adapter for Polygon.io data integration."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key (from env or parameter)."""
        self.api_key = api_key or os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("Polygon API key required. Set POLYGON_API_KEY env var or pass api_key parameter.")

        # Base URLs and session
        self.base_url = "https://api.polygon.io"
        self._session = None

        # Logger for structured messages
        self.logger = logging.getLogger(__name__)
        self._file_handler = None

    def enable_file_logging(self, path: str, level: int = logging.INFO):
        """Enable persistent file logging for the adapter.

        Args:
            path: path to the log file to write.
            level: logging level (default: INFO).
        """
        # Remove previous handler if present
        if self._file_handler:
            self.logger.removeHandler(self._file_handler)
            try:
                self._file_handler.close()
            except Exception:
                pass

        # Create and attach a file handler
        file_handler = logging.FileHandler(path)
        file_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        # Ensure logger will emit messages at the requested level
        self.logger.setLevel(level)
        self._file_handler = file_handler
    
    def get_session(self):
        """Get or create HTTP session."""
        if self._session is None:
            try:
                import requests
                self._session = requests.Session()
                self._session.params.update({'apikey': self.api_key})
            except ImportError:
                raise ImportError("requests library required for Polygon data access")
        return self._session
    
    def get_market_snapshot(self, symbol: str) -> Optional[MarketSnapshot]:
        """Get current market snapshot for a symbol.

        For crypto symbols (e.g., 'X:ETHUSD' or 'ETHUSD'), prefer Coinbase spot for
        live prices. If Coinbase is unavailable, try Polygon last-trade. Binance
        is no longer used as a data source per repository policy.
        """
        try:
            # If this appears to be a crypto symbol, prefer Coinbase public spot API first
            # for live price collections. If Coinbase fails, try Polygon last-trade, then
            # fall back to other exchange APIs (Binance) as necessary.
            if self._is_crypto_symbol(symbol):
                # 1) Coinbase spot (preferred)
                try:
                    cb = self.get_crypto_spot_coinbase(symbol)
                    if cb:
                        self.logger.info(f"Returning Coinbase snapshot for {symbol}")
                        cb.source = 'coinbase'
                        return cb
                except Exception as e:
                    print(f"Coinbase spot unavailable for {symbol}: {e}")

                # 2) Polygon last-trade (may be gated by subscription)
                try:
                    session = self.get_session()
                    last_url = f"{self.base_url}/v2/last/trade/{symbol.upper()}"
                    resp = session.get(last_url, timeout=8)
                    if resp.status_code == 403:
                        # Not authorized for this endpoint — surface to caller so they can
                        # decide if they want to upgrade entitlements or rely on fallbacks.
                        raise PermissionError(resp.json().get('message', 'Not authorized'))
                    resp.raise_for_status()
                    j = resp.json()
                    # Polygon last-trade shape varies; try to extract price
                    price = None
                    if isinstance(j, dict) and 'results' in j and j['results']:
                        price = j['results'].get('p') or j['results'].get('price')
                    elif isinstance(j, dict) and 'result' in j:
                        price = j['result'].get('p') or j['result'].get('price')
                    if price is not None:
                        self.logger.info(f"Returning Polygon last-trade snapshot for {symbol}")
                        return MarketSnapshot(symbol=symbol.upper(), price=float(price), change=0.0, change_percent=0.0, volume=0, timestamp=datetime.now(), source='polygon')
                except PermissionError:
                    # Surface permission issues upward after trying Coinbase and Polygon
                    self.logger.warning(f"Polygon permission error for last-trade {symbol}")
                    raise
                except Exception:
                    # Any other failure — try Binance fallback (or return None below)
                    pass

                # If both Coinbase and Polygon fail for live crypto price, return None
                # and surface the error so the caller can decide how to proceed.
                self.logger.warning(f"Both Coinbase and Polygon failed to provide a live snapshot for {symbol}")
                return None

            # Default: equities snapshot (stocks)
            session = self.get_session()
            url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol.upper()}"
            response = session.get(url, timeout=10)
            if response.status_code == 403:
                # Explicit permission problem
                raise PermissionError(response.json().get('message', 'Not authorized for snapshot'))
            response.raise_for_status()
            data = response.json()
            if 'results' in data and data['results']:
                ticker_data = data['results']['value']
                return MarketSnapshot(
                    symbol=symbol.upper(),
                    price=ticker_data.get('c', 0.0),  # close/current price
                    change=ticker_data.get('c', 0.0) - ticker_data.get('o', 0.0),
                    change_percent=((ticker_data.get('c', 0.0) - ticker_data.get('o', 0.0)) / ticker_data.get('o', 1.0)) * 100,
                    volume=ticker_data.get('v', 0),
                    high=ticker_data.get('h'),
                    low=ticker_data.get('l'),
                    open=ticker_data.get('o'),
                    prev_close=ticker_data.get('pc'),
                    timestamp=datetime.now(),
                    source='polygon'
                )
        except PermissionError as pe:
            # Surface permission errors to the caller so it can decide on a fallback
            print(f"Permission error fetching snapshot for {symbol}: {pe}")
            raise
        except Exception as e:
            print(f"Error fetching snapshot for {symbol}: {e}")
            return None
    
    def get_price_bars(self, symbol: str, timespan: str = "day", 
                      from_date: Optional[str] = None, to_date: Optional[str] = None,
                      limit: int = 100, multiplier: int = 1) -> pd.DataFrame:
        """
        Get OHLCV price bars for a symbol.
        
        Args:
            symbol: Stock ticker or crypto pair (e.g., 'AAPL' or 'X:ETHUSD')
            timespan: 'minute', 'hour', 'day', 'week', 'month', 'quarter', 'year'
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            limit: Number of bars to return
            multiplier: Size of the timespan multiplier (e.g., 15 for 15-minute bars)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        session = self.get_session()

        # Default date range (last 30 days)
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')

        url = f"{self.base_url}/v2/aggs/ticker/{symbol.upper()}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {
            'adjusted': 'true',
            'sort': 'asc',
            'limit': limit
        }

        try:
            response = session.get(url, params=params, timeout=30)

            # Handle explicit permission error from Polygon
            if response.status_code == 403:
                try:
                    msg = response.json().get('message', 'Not authorized')
                except Exception:
                    msg = 'Not authorized'
                raise PermissionError(msg)

            response.raise_for_status()
            data = response.json()

            if 'results' in data and data['results']:
                bars = data['results']
                df = pd.DataFrame([
                    {
                        'timestamp': pd.to_datetime(bar['t'], unit='ms', utc=True),
                        'open': bar['o'],
                        'high': bar['h'], 
                        'low': bar['l'],
                        'close': bar['c'],
                        'volume': bar['v']
                    }
                    for bar in bars
                ])
                df.set_index('timestamp', inplace=True)
                return df

            # No results returned from Polygon aggregates; surface empty DataFrame.
            print(f"No data returned for {symbol} from Polygon aggregates")
            # Per repository policy, do not query Binance. Return empty DataFrame so
            # caller can decide whether to retry or use another data source.

            return pd.DataFrame()

        except PermissionError:
            # Surface permission error
            print(f"Permission error fetching price bars for {symbol}")
            raise
        except Exception as e:
            print(f"Error fetching price bars for {symbol}: {e}")
            # If crypto, attempt Binance fallback
            if self._is_crypto_symbol(symbol):
                try:
                    return self._fallback_binance_klines(symbol, multiplier, limit)
                except Exception as e2:
                    print(f"Binance fallback also failed: {e2}")
            return pd.DataFrame()

    # --- Helper methods for crypto fallbacks ---
    def _is_crypto_symbol(self, symbol: str) -> bool:
        s = symbol.upper()
        return s.startswith('X:') or (s.endswith('USD') and len(s) <= 7)

    def get_crypto_spot_coinbase(self, symbol: str) -> Optional[MarketSnapshot]:
        """Fetch spot price from Coinbase public API for a crypto symbol like X:ETHUSD or ETHUSD."""
        try:
            # Map symbol -> Coinbase format (ETH-USD)
            s = symbol.upper().replace('X:', '').replace('/', '-').replace('USD', 'USD')
            # Coinbase expects ETH-USD
            s = s.replace('USD', '-USD') if '-' not in s else s
            if s.endswith('-USD') is False:
                s = s.replace('USD', '-USD')

            url = f"https://api.coinbase.com/v2/prices/{s}/spot"
            r = requests.get(url, timeout=8)
            r.raise_for_status()
            j = r.json()
            amount = float(j['data']['amount'])
            return MarketSnapshot(symbol=symbol.upper(), price=amount, change=0.0, change_percent=0.0, volume=0, timestamp=datetime.now())
        except Exception as e:
            print(f"Coinbase spot fetch failed for {symbol}: {e}")
            return None

    # Note: Binance fallbacks intentionally removed per repository policy. If
    # additional exchange fallbacks are needed, add them in a configurable
    # and reviewed manner.
    
    def get_ticker_news(self, ticker: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent news for a ticker or general market news."""
        try:
            session = self.get_session()
            
            if ticker:
                url = f"{self.base_url}/v2/reference/news"
                params = {'ticker': ticker.upper(), 'limit': limit}
            else:
                url = f"{self.base_url}/v2/reference/news" 
                params = {'limit': limit}
            
            response = session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def to_agent_trader_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Polygon data to agent_trader compatible format."""
        if df.empty:
            return df
        
        # Ensure we have the columns expected by agent_trader
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0.0
        
        # agent_trader expects datetime index
        if df.index.name != 'timestamp':
            df.index.name = 'timestamp'
        
        return df[required_cols]
    
    def health_check(self) -> Dict[str, Any]:
        """Check API connectivity and account status."""
        try:
            session = self.get_session()
            
            # Test market status endpoint
            response = session.get(f"{self.base_url}/v1/marketstatus/now", timeout=10)
            response.raise_for_status()
            
            status_data = response.json()
            
            return {
                'status': 'healthy',
                'market_status': status_data.get('market', 'unknown'),
                'api_key_valid': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Example usage and testing
def main():
    """Test the Polygon adapter."""
    try:
        adapter = PolygonDataAdapter()
        
        print("🔍 Testing Polygon.io connection...")
        health = adapter.health_check()
        print(f"Health check: {health}")
        
        if health['status'] == 'healthy':
            print("\n📊 Testing market snapshot...")
            snapshot = adapter.get_market_snapshot('AAPL')
            if snapshot:
                print(f"AAPL: ${snapshot.price:.2f} ({snapshot.change_percent:+.2f}%)")
            
            print("\n📈 Testing price bars...")
            bars = adapter.get_price_bars('AAPL', timespan='day', limit=5)
            if not bars.empty:
                print(f"Retrieved {len(bars)} daily bars for AAPL")
                print(bars.tail())
            
            print("\n📰 Testing news...")
            news = adapter.get_ticker_news('AAPL', limit=3)
            print(f"Retrieved {len(news)} news articles")
            for article in news[:2]:
                print(f"- {article.get('title', 'No title')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Make sure POLYGON_API_KEY is set in your environment")


if __name__ == "__main__":
    main()

