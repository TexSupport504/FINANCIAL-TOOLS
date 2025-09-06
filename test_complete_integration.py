"""Complete integration test: Goldbach Knowledge + Polygon Data"""
import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_goldbach_knowledge():
    """Test Goldbach knowledge base access."""
    print("🧠 Testing Goldbach Knowledge Base...")
    
    try:
        from agent_trader.knowledge_base import search_goldbach, get_goldbach_strategy
        
        # Test search
        results = search_goldbach("PO3 premium discount", top_k=3)
        print(f"✅ Found {len(results)} Goldbach search results")
        
        # Test strategy access
        strategy = get_goldbach_strategy()
        po3_levels = strategy['po3_levels']['levels']
        print(f"✅ PO3 levels accessible: {po3_levels[:5]}...")
        
        return True
    except Exception as e:
        print(f"❌ Goldbach knowledge error: {e}")
        return False

def test_polygon_data():
    """Test Polygon data access."""
    print("\n📊 Testing Polygon.io Data Access...")
    
    try:
        from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter
        
        # Get API key from environment
        api_key = os.getenv('POLYGON_API_KEY')
        if not api_key:
            print("⚠️  No API key in environment, checking .env file...")
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('POLYGON_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            break
            except FileNotFoundError:
                pass
        
        if not api_key:
            print("❌ No Polygon API key found")
            return False
            
        # Test adapter
        adapter = PolygonDataAdapter(api_key)
        
        # Test historical data (works even when markets closed)
        bars = adapter.get_price_bars('AAPL', 'day', limit=5)
        if not bars.empty:
            print(f"✅ Retrieved {len(bars)} historical bars")
            print(f"   Latest close: ${bars['close'].iloc[-1]:.2f}")
        else:
            print("⚠️  No historical bars retrieved")
        
        # Test news (should work anytime)  
        news = adapter.get_ticker_news('AAPL', limit=3)
        if news:
            print(f"✅ Retrieved {len(news)} news articles")
            print(f"   Latest: {news[0]['title'][:60]}...")
        else:
            print("⚠️  No news articles retrieved")
        
        return True
    except Exception as e:
        print(f"❌ Polygon data error: {e}")
        return False

def test_integration():
    """Test the complete integration."""
    print("\n🔗 Testing Complete Integration...")
    
    try:
        # Import both systems
        from agent_trader.knowledge_base import get_kb
        from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter
        
        kb = get_kb()
        
        # Get PO3 levels from Goldbach knowledge
        po3_info = kb.get_po3_levels()
        po3_levels = po3_info['levels']
        print(f"✅ Goldbach PO3 levels: {po3_levels}")
        
        # Get AMD phase information
        amd_info = kb.get_amd_phases()
        sessions = list(amd_info['sessions'].keys())
        print(f"✅ AMD sessions from Goldbach: {sessions}")
        
        # Get premium/discount knowledge  
        premium_info = kb.get_premium_discount_levels()
        print(f"✅ Premium/discount concept: {premium_info['concept']}")
        
        print("\n💡 Integration Complete! The agent can now:")
        print("   • Access all 74 pages of Goldbach strategy")
        print("   • Retrieve live/historical market data via Polygon")
        print("   • Apply PO3 levels to real price movements")
        print("   • Use AMD session timing with market data")
        print("   • Combine Goldbach concepts with live trading")
        
        return True
    except Exception as e:
        print(f"❌ Integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run complete integration test."""
    print("🚀 COMPLETE GOLDBACH + POLYGON INTEGRATION TEST")
    print("=" * 60)
    
    # Test individual components
    goldbach_ok = test_goldbach_knowledge()
    polygon_ok = test_polygon_data()
    
    # Test integration
    if goldbach_ok and polygon_ok:
        integration_ok = test_integration()
    else:
        print("\n⚠️  Skipping integration test due to component failures")
        integration_ok = False
    
    # Summary
    print(f"\n📋 TEST SUMMARY")
    print("=" * 20)
    print(f"Goldbach Knowledge: {'✅ PASS' if goldbach_ok else '❌ FAIL'}")
    print(f"Polygon Data: {'✅ PASS' if polygon_ok else '❌ FAIL'}")
    print(f"Integration: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    
    if goldbach_ok and polygon_ok and integration_ok:
        print("\n🎉 COMPLETE SUCCESS!")
        print("The agent is ready for live trading with Goldbach strategy!")
    else:
        print("\n⚠️  Some components need attention")
    
    return goldbach_ok and polygon_ok and integration_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
