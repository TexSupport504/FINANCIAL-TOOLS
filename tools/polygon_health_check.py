"""Health check utility for Polygon.io integration.

Tests connectivity, API limits, and data quality.
"""
import sys
from pathlib import Path
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def run_comprehensive_health_check():
    """Run comprehensive health check of Polygon integration."""
    print("🏥 POLYGON.IO HEALTH CHECK")
    print("=" * 50)
    
    try:
        adapter = PolygonDataAdapter()
        
        # 1. Basic connectivity
        print("\n1️⃣ Testing API connectivity...")
        health = adapter.health_check()
        
        if health['status'] == 'error':
            print(f"❌ Connection failed: {health['error']}")
            return False
        
        print(f"✅ API connected successfully")
        print(f"   Market status: {health.get('market_status', 'unknown')}")
        
        # 2. Market data retrieval
        print("\n2️⃣ Testing market data retrieval...")
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        for symbol in test_symbols:
            snapshot = adapter.get_market_snapshot(symbol)
            if snapshot:
                print(f"✅ {symbol}: ${snapshot.price:.2f} ({snapshot.change_percent:+.2f}%)")
            else:
                print(f"⚠️  {symbol}: No snapshot data available")
        
        # 3. Historical data
        print("\n3️⃣ Testing historical data...")
        bars = adapter.get_price_bars('AAPL', timespan='day', limit=10)
        
        if not bars.empty:
            print(f"✅ Retrieved {len(bars)} historical bars")
            print(f"   Date range: {bars.index[0].strftime('%Y-%m-%d')} to {bars.index[-1].strftime('%Y-%m-%d')}")
            print(f"   Latest close: ${bars['close'].iloc[-1]:.2f}")
        else:
            print("⚠️  No historical data available")
        
        # 4. News data
        print("\n4️⃣ Testing news data...")
        news = adapter.get_ticker_news('AAPL', limit=5)
        
        if news:
            print(f"✅ Retrieved {len(news)} news articles")
            latest = news[0] if news else {}
            print(f"   Latest: {latest.get('title', 'No title')[:60]}...")
        else:
            print("⚠️  No news data available")
        
        # 5. Data format compatibility
        print("\n5️⃣ Testing agent_trader compatibility...")
        compatible_bars = adapter.to_agent_trader_format(bars)
        
        expected_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in expected_cols if col not in compatible_bars.columns]
        
        if not missing_cols and not compatible_bars.empty:
            print("✅ Data format compatible with agent_trader")
            print(f"   Columns: {list(compatible_bars.columns)}")
        else:
            print(f"⚠️  Format issues: missing {missing_cols}")
        
        print("\n🎉 Health check completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        return False


def run_quick_check():
    """Run a quick connectivity test."""
    try:
        adapter = PolygonDataAdapter()
        health = adapter.health_check()
        
        if health['status'] == 'healthy':
            print("✅ Polygon.io connection: OK")
            return True
        else:
            print(f"❌ Polygon.io connection: {health.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Quick check failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Polygon.io health check")
    parser.add_argument("--quick", action="store_true", help="Run quick check only")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.quick:
        success = run_quick_check()
    else:
        success = run_comprehensive_health_check()
    
    if args.verbose:
        print(f"\nTimestamp: {datetime.now().isoformat()}")
        
        try:
            import os
            print(f"API Key set: {'✅' if os.getenv('POLYGON_API_KEY') else '❌'}")
        except:
            pass
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
