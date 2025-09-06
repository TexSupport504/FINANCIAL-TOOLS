"""Ethereum 15-minute Goldbach Analysis Tool

Analyzes ETH/USD on 15-minute timeframe to identify:
- Current algo cycle (Algorithm 1: MMxM vs Algorithm 2: Trending)
- AMD phases (Accumulation, Manipulation, Distribution)
- Power of Three levels and dealing ranges
- Current market position and phase
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_trader.knowledge_base import get_kb, search_goldbach
from agent_trader.data_sources.polygon_adapter import PolygonDataAdapter
import os


class EthereumGoldbachAnalyzer:
    """Analyze Ethereum using Goldbach strategy concepts."""
    
    def __init__(self):
        """Initialize with Polygon data and Goldbach knowledge."""
        # Get API key
        self.api_key = os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('POLYGON_API_KEY='):
                            self.api_key = line.split('=', 1)[1].strip()
                            break
            except FileNotFoundError:
                pass
        
        if not self.api_key:
            raise ValueError("Polygon API key required")
            
        self.polygon = PolygonDataAdapter(self.api_key)
        self.kb = get_kb()
        
        # PO3 levels from Goldbach knowledge
        self.po3_levels = [27, 81, 243, 729, 2187, 6561, 19683]
        
    def validate_real_data(self, data: pd.DataFrame, symbol: str) -> bool:
        """
        Validate that we have real market data, not demo/mock data.
        
        Args:
            data: DataFrame with OHLCV data
            symbol: Symbol being analyzed
        
        Returns:
            True if data appears to be real, False if likely demo/mock data
        """
        if data.empty:
            print(f"❌ Data validation failed: No data for {symbol}")
            return False
            
        current_price = data['close'].iloc[-1]
        
        # ETH-specific validation
        if symbol.upper() in ['X:ETHUSD', 'ETHUSD', 'ETH-USD']:
            if not (500 <= current_price <= 15000):  # Reasonable ETH range
                print(f"❌ Data validation failed: ETH price ${current_price:.2f} outside reasonable range ($500-$15,000)")
                return False
                
        # Check for obviously fake/demo patterns
        price_range = data['high'].max() - data['low'].min()
        if price_range < (current_price * 0.001):  # Less than 0.1% range is suspicious
            print(f"❌ Data validation failed: Price range too narrow ({price_range:.2f}), likely demo data")
            return False
            
        # Check for realistic volume (should vary significantly)
        if len(data) > 10:
            volume_std = data['volume'].std()
            volume_mean = data['volume'].mean()
            if volume_mean > 0 and (volume_std / volume_mean) < 0.1:  # Very low volume variance
                print(f"⚠️  Warning: Volume data has low variance, may be demo data")
                
        # Check for realistic timestamp progression
        if len(data) > 2:
            time_diffs = data.index.to_series().diff().dropna()
            expected_interval = pd.Timedelta(minutes=15)  # 15-minute bars
            actual_intervals = time_diffs.dt.total_seconds() / 60  # Convert to minutes
            
            if not actual_intervals.between(10, 20).any():  # Should have ~15min intervals
                print(f"⚠️  Warning: Time intervals don't match 15-minute expectation")
        
        print(f"✅ Data validation passed: {symbol} data appears to be real market data")
        return True

    def get_eth_data(self, days: int = 5) -> pd.DataFrame:
        """Get recent ETH 15-minute data."""
        print("📊 Fetching ETH 15-minute data...")
        
        # For crypto, we use ETH-USD or X:ETHUSD
        try:
            print("Attempting to fetch with X:ETHUSD symbol...")
            # Try crypto format first with date range for better results
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            bars = self.polygon.get_price_bars(
                symbol='X:ETHUSD',
                timespan='minute',
                multiplier=15,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d'),
                limit=days * 96  # 96 x 15min bars per day
            )
            
            if not bars.empty:
                current_price = bars['close'].iloc[-1]
                print(f"✅ Successfully fetched with X:ETHUSD. Current price: ${current_price:.2f}")
                
                # Validate this is real data, not demo data
                if self.validate_real_data(bars, 'X:ETHUSD'):
                    return bars
                else:
                    print("❌ Data validation failed - will not proceed with demo/invalid data")
                    raise ValueError("Invalid or demo data detected - analysis requires real market data")
                    
        except Exception as e:
            print(f"❌ X:ETHUSD failed: {e}")
            
            # Fallback to regular format
            try:
                print("Attempting fallback with ETHUSD symbol...")
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                bars = self.polygon.get_price_bars(
                    symbol='ETHUSD',
                    timespan='minute', 
                    multiplier=15,
                    from_date=start_date.strftime('%Y-%m-%d'),
                    to_date=end_date.strftime('%Y-%m-%d'),
                    limit=days * 96
                )
                
                if not bars.empty:
                    current_price = bars['close'].iloc[-1]
                    print(f"✅ Successfully fetched with ETHUSD. Current price: ${current_price:.2f}")
                    
                    # Validate this is real data, not demo data  
                    if self.validate_real_data(bars, 'ETHUSD'):
                        return bars
                    else:
                        print("❌ Data validation failed - will not proceed with demo/invalid data")
                        raise ValueError("Invalid or demo data detected - analysis requires real market data")
                        
            except Exception as e2:
                print(f"❌ ETHUSD also failed: {e2}")
        
        # If both methods fail, raise an error instead of using demo data
        raise RuntimeError("❌ Could not fetch real ETH data from any source. Analysis requires real market data - will not proceed with demo/mock data.")
    
    def identify_amd_phases(self, data: pd.DataFrame) -> dict:
        """Identify AMD phases in the data."""
        print("\n🕒 Analyzing AMD Phases...")
        
        # Get Goldbach knowledge about AMD phases
        amd_knowledge = search_goldbach("AMD accumulation manipulation distribution phases session", top_k=3)
        
        # Extract key session times (convert to market hours)
        phase_info = {
            'asian_session': {'start': '00:00', 'end': '09:00', 'phase': 'Accumulation'},
            'london_session': {'start': '07:00', 'end': '16:00', 'phase': 'Manipulation'}, 
            'ny_session': {'start': '13:00', 'end': '22:00', 'phase': 'Distribution'}
        }
        
        # Analyze recent 24 hours for complete AMD cycle
        recent_data = data.tail(96)  # Last 96 x 15min = 24 hours
        
        current_hour = datetime.now().hour
        current_phase = self._get_current_amd_phase(current_hour)
        
        # Look for phase characteristics
        phases_detected = []
        for i in range(0, len(recent_data), 24):  # Every 6 hours
            chunk = recent_data.iloc[i:i+24]
            if len(chunk) < 10:
                continue
                
            volatility = chunk['high'].max() - chunk['low'].min()
            volume_avg = chunk['volume'].mean()
            
            # Classify based on Goldbach concepts
            if volatility < chunk['close'].std() * 2:
                phases_detected.append('Accumulation')
            elif volatility > chunk['close'].std() * 3:
                phases_detected.append('Manipulation') 
            else:
                phases_detected.append('Distribution')
        
        return {
            'current_phase': current_phase,
            'phases_detected': phases_detected,
            'amd_knowledge': [r['content'][:200] + "..." for r in amd_knowledge]
        }
    
    def _get_current_amd_phase(self, hour: int) -> str:
        """Determine current AMD phase based on hour."""
        # Based on Goldbach: Asian (Accumulation), London (Manipulation), NY (Distribution)
        if 0 <= hour < 9:
            return 'Accumulation (Asian Session)'
        elif 7 <= hour < 16:
            return 'Manipulation (London Session)'
        elif 13 <= hour <= 23:
            return 'Distribution (NY Session)'
        else:
            return 'Transition Period'
    
    def identify_algorithms(self, data: pd.DataFrame) -> dict:
        """Identify which algorithm (1 or 2) is currently active."""
        print("\n🤖 Analyzing Algorithms...")
        
        # Get Goldbach knowledge about algorithms
        algo_knowledge = search_goldbach("algorithms MMxM Market Maker trending algo", top_k=3)
        
        recent_data = data.tail(48)  # Last 12 hours of 15min data
        
        # Algorithm 1: MMxM (Market Maker Buy/Sell Model)
        # Characteristics: Range-bound, accumulation/distribution patterns
        price_range = recent_data['high'].max() - recent_data['low'].min()
        avg_price = recent_data['close'].mean()
        range_percentage = (price_range / avg_price) * 100
        
        # Algorithm 2: Trending
        # Characteristics: Directional movement, OTE patterns
        price_change = recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]
        trend_strength = abs(price_change) / avg_price * 100
        
        # Decision logic based on Goldbach concepts
        if range_percentage < 2.0 and trend_strength < 1.5:
            current_algo = "Algorithm 1 (MMxM - Market Maker Model)"
            characteristics = "Range-bound price action, accumulation/distribution patterns"
        else:
            current_algo = "Algorithm 2 (Trending Algorithm)" 
            characteristics = "Directional movement, creating OTE (Optimal Trade Entry) opportunities"
        
        return {
            'current_algorithm': current_algo,
            'characteristics': characteristics,
            'range_percentage': range_percentage,
            'trend_strength': trend_strength,
            'algo_knowledge': [r['content'][:200] + "..." for r in algo_knowledge]
        }
    
    def identify_po3_levels(self, data: pd.DataFrame) -> dict:
        """Identify active PO3 levels and dealing ranges."""
        print("\n🔢 Analyzing PO3 Levels...")
        
        # Get current price
        current_price = data['close'].iloc[-1]
        
        # Get PO3 knowledge
        po3_knowledge = search_goldbach("PO3 power of three dealing ranges 27 81 243", top_k=3)
        
        # Calculate recent range to determine appropriate PO3 level
        recent_high = data['high'].tail(96).max()  # Last 24 hours
        recent_low = data['low'].tail(96).min()
        range_pips = abs(recent_high - recent_low)
        
        # For ETH, convert to "pips" (assuming 1 pip = $1 for simplicity)
        range_in_pips = int(range_pips)
        
        # Find the most appropriate PO3 level
        active_po3 = None
        for level in self.po3_levels:
            if range_in_pips <= level:
                active_po3 = level
                break
        
        if active_po3 is None:
            active_po3 = self.po3_levels[-1]  # Use largest level
        
        # Calculate PO3 dealing range levels
        range_high = recent_high
        range_low = recent_low
        range_mid = (range_high + range_low) / 2
        
        # Premium, Equilibrium, Discount levels
        premium_zone = range_mid + (range_high - range_mid) * 0.67
        discount_zone = range_mid - (range_mid - range_low) * 0.67
        
        # Determine current position
        if current_price >= premium_zone:
            current_zone = "Premium Zone"
        elif current_price <= discount_zone:
            current_zone = "Discount Zone" 
        else:
            current_zone = "Equilibrium Zone"
        
        return {
            'active_po3_level': active_po3,
            'range_high': range_high,
            'range_low': range_low,
            'premium_zone': premium_zone,
            'discount_zone': discount_zone,
            'equilibrium': range_mid,
            'current_price': current_price,
            'current_zone': current_zone,
            'po3_knowledge': [r['content'][:200] + "..." for r in po3_knowledge]
        }
    
    def find_recent_algo_cycle(self, data: pd.DataFrame) -> dict:
        """Find the most recent complete algorithm cycle."""
        print("\n🔍 Finding Recent Complete Algo Cycle...")
        
        # Look for complete cycles in recent data (last 3-5 days)
        cycle_data = data.tail(288)  # 72 hours of 15min data
        
        # Identify potential cycle completion points
        # Look for significant high/low points that could mark cycle completion
        highs = cycle_data['high'].rolling(window=12).max()  # 3-hour windows
        lows = cycle_data['low'].rolling(window=12).min()
        
        # Find most recent significant reversal (potential cycle completion)
        price_changes = cycle_data['close'].pct_change().abs()
        significant_moves = price_changes > price_changes.quantile(0.9)
        
        last_cycle_end = cycle_data[significant_moves].tail(1)
        
        if not last_cycle_end.empty:
            cycle_completion_time = last_cycle_end.index[-1]
            cycle_completion_price = last_cycle_end['close'].iloc[-1]
            
            # Analyze the cycle characteristics
            cycle_start_idx = max(0, len(cycle_data) - 96)  # Go back 24 hours
            cycle_segment = cycle_data.iloc[cycle_start_idx:]
            
            cycle_high = cycle_segment['high'].max()
            cycle_low = cycle_segment['low'].min()
            cycle_range = cycle_high - cycle_low
            
            return {
                'cycle_found': True,
                'completion_time': cycle_completion_time,
                'completion_price': cycle_completion_price,
                'cycle_high': cycle_high,
                'cycle_low': cycle_low,
                'cycle_range': cycle_range,
                'bars_in_cycle': len(cycle_segment)
            }
        else:
            return {
                'cycle_found': False,
                'message': 'No clear cycle completion detected in recent data'
            }


def main():
    """Main analysis function."""
    print("🚀 ETHEREUM 15-MINUTE GOLDBACH ANALYSIS")
    print("=" * 50)
    
    try:
        analyzer = EthereumGoldbachAnalyzer()
        
        # Get ETH data
        eth_data = analyzer.get_eth_data(days=5)
        current_price = eth_data['close'].iloc[-1]
        
        print(f"💰 Current ETH Price: ${current_price:.2f}")
        print(f"📅 Analysis Period: {len(eth_data)} 15-minute bars")
        
        # 1. Find recent algo cycle
        cycle_info = analyzer.find_recent_algo_cycle(eth_data)
        
        print(f"\n🔄 RECENT ALGORITHM CYCLE")
        print("-" * 30)
        if cycle_info['cycle_found']:
            print(f"✅ Complete cycle found")
            print(f"   Completion time: {cycle_info['completion_time']}")
            print(f"   Completion price: ${cycle_info['completion_price']:.2f}")
            print(f"   Cycle range: ${cycle_info['cycle_range']:.2f}")
            print(f"   Duration: {cycle_info['bars_in_cycle']} bars (15min each)")
        else:
            print(f"⚠️  {cycle_info['message']}")
        
        # 2. Identify current algorithm
        algo_info = analyzer.identify_algorithms(eth_data)
        
        print(f"\n🤖 CURRENT ALGORITHM")
        print("-" * 25)
        print(f"Active: {algo_info['current_algorithm']}")
        print(f"Characteristics: {algo_info['characteristics']}")
        print(f"Range %: {algo_info['range_percentage']:.2f}%")
        print(f"Trend Strength: {algo_info['trend_strength']:.2f}%")
        
        # 3. Identify AMD phase
        amd_info = analyzer.identify_amd_phases(eth_data)
        
        print(f"\n🕒 AMD PHASE ANALYSIS")
        print("-" * 25)
        print(f"Current Phase: {amd_info['current_phase']}")
        print(f"Recent Phases Detected: {amd_info['phases_detected']}")
        
        # 4. Identify PO3 levels
        po3_info = analyzer.identify_po3_levels(eth_data)
        
        print(f"\n🔢 PO3 LEVELS & ZONES")
        print("-" * 25)
        print(f"Active PO3 Level: {po3_info['active_po3_level']} pips")
        print(f"Current Zone: {po3_info['current_zone']}")
        print(f"Current Price: ${po3_info['current_price']:.2f}")
        print(f"Premium Zone: ${po3_info['premium_zone']:.2f}")
        print(f"Equilibrium: ${po3_info['equilibrium']:.2f}") 
        print(f"Discount Zone: ${po3_info['discount_zone']:.2f}")
        print(f"Range High: ${po3_info['range_high']:.2f}")
        print(f"Range Low: ${po3_info['range_low']:.2f}")
        
        # 5. Summary and recommendations
        print(f"\n📋 GOLDBACH ANALYSIS SUMMARY")
        print("=" * 35)
        
        print(f"🎯 Current Market State:")
        print(f"   • Price: ${current_price:.2f} in {po3_info['current_zone']}")
        print(f"   • Algorithm: {algo_info['current_algorithm'].split('(')[0].strip()}")
        print(f"   • Phase: {amd_info['current_phase']}")
        print(f"   • PO3 Level: {po3_info['active_po3_level']} pip dealing range")
        
        print(f"\n💡 Key Insights:")
        if po3_info['current_zone'] == "Premium Zone":
            print(f"   • In Premium Zone - Watch for potential sell opportunities")
        elif po3_info['current_zone'] == "Discount Zone":
            print(f"   • In Discount Zone - Watch for potential buy opportunities")
        else:
            print(f"   • In Equilibrium - Watch for breakout direction")
            
        if "MMxM" in algo_info['current_algorithm']:
            print(f"   • Market Maker Model active - Range-bound behavior expected")
        else:
            print(f"   • Trending Algorithm active - Directional moves expected")
        
        print(f"\n✅ Analysis Complete!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
