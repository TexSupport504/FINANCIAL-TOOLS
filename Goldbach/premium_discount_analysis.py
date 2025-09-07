import pandas as pd

# Read latest candles
df = pd.read_csv('latest_candles.csv')
print("GOLDBACH PHASE - PREMIUM/DISCOUNT ANALYSIS")
print("=" * 50)

# Current data
current_price = df['c'].iloc[-1]
high = df['h'].max()
low = df['l'].min()
range_midpoint = (high + low) / 2

print(f"Current Price: ${current_price:.2f}")
print(f"Range High: ${high:.2f}")
print(f"Range Low: ${low:.2f}")
print(f"Range Midpoint (50%): ${range_midpoint:.2f}")
print(f"Range Size: ${high - low:.2f}")

# Calculate position relative to range
if high != low:
    range_position = (current_price - low) / (high - low)
else:
    range_position = 0.5

print(f"Position in Range: {range_position:.1%}")

# Determine premium/discount relative to 50% midpoint
if current_price > range_midpoint:
    level_status = "PREMIUM"
    distance_from_mid = current_price - range_midpoint
    print(f"Status: PREMIUM (${distance_from_mid:.2f} above midpoint)")
elif current_price < range_midpoint:
    level_status = "DISCOUNT" 
    distance_from_mid = range_midpoint - current_price
    print(f"Status: DISCOUNT (${distance_from_mid:.2f} below midpoint)")
else:
    level_status = "FAIR VALUE"
    print(f"Status: FAIR VALUE (exactly at midpoint)")

# More granular classification
if range_position > 0.8:
    detailed_level = "HIGH PREMIUM"
elif range_position > 0.6:
    detailed_level = "PREMIUM"
elif range_position > 0.4:
    detailed_level = "FAIR VALUE"
elif range_position > 0.2:
    detailed_level = "DISCOUNT"
else:
    detailed_level = "DEEP DISCOUNT"

print(f"\nDETAILED CLASSIFICATION:")
print(f"Relative to 50% midpoint: {level_status}")
print(f"Range position: {detailed_level}")

# Goldbach phase based on position
if range_position > 0.75:
    goldbach_phase = "H"  # High
elif range_position < 0.25:
    goldbach_phase = "L"  # Low  
elif range_position > 0.6:
    goldbach_phase = "MB" # Mid Band (premium side)
elif range_position < 0.4:
    goldbach_phase = "MB" # Mid Band (discount side)
else:
    goldbach_phase = "FV" # Fair Value

print(f"\nGOLDBACH PHASE: {goldbach_phase}")
print(f"PREMIUM/DISCOUNT: {level_status}")

# Show the math
print(f"\nCALCULATION:")
print(f"${current_price:.2f} vs ${range_midpoint:.2f} midpoint")
print(f"= {level_status}")
