import pandas as pd
import numpy as np

def determine_goldbach_algorithm(df):
    """
    Determine which Goldbach algorithm based on price structure
    
    ALGO 1 (MMxM - Mean Reversion):
    HIGH/LOW → RB → OB → FV → BR → LV
    
    ALGO 2 (Trending/OTE):  
    RB → OB → Opposite BR → Opposite RB → BR → FV
    """
    
    # Calculate trend and momentum indicators
    current_price = df['c'].iloc[-1]
    prev_price = df['c'].iloc[-2] if len(df) > 1 else current_price
    
    # Simple trend detection (more sophisticated logic would go here)
    ema_9 = df['c'].ewm(span=9).mean().iloc[-1]
    ema_21 = df['c'].ewm(span=21).mean().iloc[-1]
    
    # Price position in range
    range_high = df['h'].max()
    range_low = df['l'].min()
    position = (current_price - range_low) / (range_high - range_low) if range_high != range_low else 0.5
    
    # Determine algorithm based on structure
    if position > 0.8 or position < 0.2:  # At extremes
        # More likely ALGO 1 (mean reversion from extremes)
        return "ALGO 1 (MMxM)", "Mean reversion from extreme levels"
    elif abs(ema_9 - ema_21) < (range_high - range_low) * 0.02:  # EMAs close = consolidation
        # Consolidating - likely ALGO 1
        return "ALGO 1 (MMxM)", "Consolidation/mean reversion pattern"
    else:
        # Trending - likely ALGO 2
        trend_direction = "bullish" if ema_9 > ema_21 else "bearish"
        return "ALGO 2 (Trending)", f"Trending {trend_direction} pattern"
    
def determine_phase(price, range_high, range_low, position):
    """
    Determine specific Goldbach phase based on position and context
    
    Premium Phases: OB, RB, FV, LV, MB, BR, H (above 50% midpoint)
    Discount Phases: -OB, -RB, -FV, -LV, -MB, -BR, L (below 50% midpoint)
    """
    midpoint = (range_high + range_low) / 2
    is_premium = price > midpoint
    
    # Phase logic based on position in range
    if position >= 0.95:  # Extreme high
        return "H"
    elif position <= 0.05:  # Extreme low  
        return "L"
    elif position >= 0.8:  # High region - Resistance/Order Block area
        if is_premium:
            return "RB"  # Resistance Break (premium)
        else:
            return "-RB"  # Resistance Break (discount)
    elif position >= 0.6:  # Upper mid region - Order Block area
        if is_premium:
            return "OB"  # Order Block (premium)
        else:
            return "-OB"  # Order Block (discount)
    elif position >= 0.4:  # Fair value region around 50%
        if is_premium:
            return "FV"  # Fair Value (premium)
        else:
            return "-FV"  # Fair Value (discount)  
    elif position >= 0.2:  # Lower mid region - Liquidity area
        if is_premium:
            return "LV"  # Low Value/Liquidity (premium)
        else:
            return "-LV"  # Low Value/Liquidity (discount)
    else:  # Low region - Breaker area
        if is_premium:
            return "BR"  # Breaker (premium)  
        else:
            return "-BR"  # Breaker (discount)

def analyze_goldbach_path():
    """Analyze which Goldbach algorithm (1 or 2) and phase progression"""
    
    # Read the data
    df = pd.read_csv('latest_candles.csv')
    df['ts'] = pd.to_datetime(df['ts'])
    
    print("GOLDBACH ALGORITHM PATH ANALYSIS")
    print("=" * 60)
    
    # Determine which Goldbach algorithm
    algorithm, algo_description = determine_goldbach_algorithm(df)
    
    # Calculate range for phase determination  
    window = 10  # Look back period for range
    df['range_high'] = df['h'].rolling(window=window, min_periods=1).max()
    df['range_low'] = df['l'].rolling(window=window, min_periods=1).min()
    
    phases = []
    
    # Determine phase for each candle
    for i in range(len(df)):
        row = df.iloc[i]
        
        # Calculate position in range
        range_size = row['range_high'] - row['range_low']
        if range_size > 0:
            position = (row['c'] - row['range_low']) / range_size
        else:
            position = 0.5
        
        phase = determine_phase(row['c'], row['range_high'], row['range_low'], position)
        phases.append(phase)
    
    df['phase'] = phases
    
    # Current analysis
    current = df.iloc[-1]
    current_phase = phases[-1]
    
    print(f"CURRENT STATUS:")
    print(f"Time: {current['ts']}")
    print(f"Price: ${current['c']:.2f}")
    print(f"Current Phase: {current_phase}")
    print(f"Algorithm: {algorithm}")
    print(f"Algorithm Logic: {algo_description}")
    
    # Determine algo path
    premium_phases = current_phase in ['OB', 'RB', 'FV', 'LV', 'MB', 'BR', 'H']
    discount_phases = current_phase in ['-OB', '-RB', '-FV', '-LV', '-MB', '-BR', 'L']
    
    if premium_phases:
        algo_path = "PREMIUM PATH"
    elif discount_phases:
        algo_path = "DISCOUNT PATH"
    else:
        algo_path = "TRANSITIONAL"
    
    print(f"Algorithm Path: {algo_path}")
    
    # Last 3 phases with timestamps
    print(f"\nLAST 3 PHASES (15-min intervals):")
    print("-" * 40)
    
    last_3 = df.tail(3)
    for i, (_, row) in enumerate(last_3.iterrows()):
        time_str = row['ts'].strftime('%H:%M')
        position_pct = ((row['c'] - row['range_low']) / (row['range_high'] - row['range_low']) * 100) if row['range_high'] != row['range_low'] else 50
        
        print(f"{i+1}. {time_str} - Phase: {row['phase']} (${row['c']:.2f}, {position_pct:.0f}% of range)")
    
    # Range analysis
    range_size = current['range_high'] - current['range_low']
    power_of_3 = range_size ** (1/3)
    
    print(f"\nRANGE ANALYSIS:")
    print(f"High: ${current['range_high']:.2f}")
    print(f"Low: ${current['range_low']:.2f}")
    print(f"Midpoint: ${(current['range_high'] + current['range_low'])/2:.2f}")
    print(f"Size: ${range_size:.2f}")
    print(f"Power of 3: {power_of_3:.4f}")
    
    # Phase transition analysis
    if len(phases) >= 2:
        recent_phases = phases[-3:] if len(phases) >= 3 else phases
        print(f"\nPHASE PROGRESSION: {' → '.join(recent_phases)}")
        
        # Determine trend
        premium_count = sum(1 for p in recent_phases if p in ['OB', 'RB', 'FV', 'LV', 'MB', 'BR', 'H'])
        discount_count = sum(1 for p in recent_phases if p in ['-OB', '-RB', '-FV', '-LV', '-MB', '-BR', 'L'])
        
        if premium_count > discount_count:
            trend = "PREMIUM TRENDING"
        elif discount_count > premium_count:
            trend = "DISCOUNT TRENDING"  
        else:
            trend = "MIXED/CONSOLIDATING"
            
        print(f"Recent Trend: {trend}")
    
    return df

# Run the analysis
if __name__ == "__main__":
    df = analyze_goldbach_path()
