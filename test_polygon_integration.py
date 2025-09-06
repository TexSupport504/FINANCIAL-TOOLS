"""Quick test script to validate the Polygon momentum strategy setup."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter
        print("✅ PolygonDataAdapter imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PolygonDataAdapter: {e}")
        return False
    
    try:
        from agent_trader.strategies.polygon.momentum_strategy import PolygonMomentumStrategy
        print("✅ PolygonMomentumStrategy imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import PolygonMomentumStrategy: {e}")
        return False
    
    return True

def test_strategy_init():
    """Test strategy initialization."""
    print("\n🔧 Testing strategy initialization...")
    
    try:
        from agent_trader.strategies.polygon.momentum_strategy import PolygonMomentumStrategy
        strategy = PolygonMomentumStrategy()
        print("✅ Strategy initialized successfully")
        print(f"   Lookback days: {strategy.lookback_days}")
        print(f"   Short MA: {strategy.short_ma}")
        print(f"   Long MA: {strategy.long_ma}")
        return True
    except Exception as e:
        print(f"❌ Strategy initialization failed: {e}")
        return False

def test_polygon_adapter():
    """Test Polygon adapter without API key."""
    print("\n🌐 Testing Polygon adapter...")
    
    try:
        from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter
        adapter = PolygonDataAdapter()  # No API key
        print("✅ Polygon adapter created (no API key)")
        print("   Note: API calls will fail without valid API key")
        return True
    except Exception as e:
        print(f"❌ Polygon adapter creation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 POLYGON INTEGRATION TEST SUITE")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_strategy_init, 
        test_polygon_adapter
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print("   Continuing with next test...\n")
    
    print(f"\n📊 TEST RESULTS: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Integration framework is ready.")
        print("\nNext steps:")
        print("1. Get a Polygon.io API key from https://polygon.io/")
        print("2. Run: python tools/setup_polygon.py --api-key YOUR_API_KEY")
        print("3. Test with: python tools/polygon_health_check.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
