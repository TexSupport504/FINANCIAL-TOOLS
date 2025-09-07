import pandas as pd
import numpy as np

# Read latest candles
df = pd.read_csv('latest_candles.csv', parse_dates=['ts'])
df = df.rename(columns={'ts':'timestamp','o':'open','h':'high','l':'low','c':'close','v':'volume'})
df.set_index('timestamp', inplace=True)

# Quick indicators for phase classification
df['ema20'] = df['close'].ewm(span=20).mean()
df['ema50'] = df['close'].ewm(span=50).mean()

# RSI calculation
delta = df['close'].diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.ewm(span=14).mean()
avg_loss = loss.ewm(span=14).mean()
rs = avg_gain / (avg_loss + 1e-8)  # Avoid division by zero
df['rsi'] = 100 - (100 / (1 + rs))

# Bollinger Bands for discount/premium
df['bb_mid'] = df['close'].rolling(20).mean()
df['bb_upper'] = df['bb_mid'] + 2 * df['close'].rolling(20).std()
df['bb_lower'] = df['bb_mid'] - 2 * df['close'].rolling(20).std()

# Current values
current = df.iloc[-1]
close = current['close']
rsi = current['rsi'] if not pd.isna(current['rsi']) else 50
ema20 = current['ema20'] if not pd.isna(current['ema20']) else close
ema50 = current['ema50'] if not pd.isna(current['ema50']) else close
bb_upper = current['bb_upper'] if not pd.isna(current['bb_upper']) else close * 1.02
bb_lower = current['bb_lower'] if not pd.isna(current['bb_lower']) else close * 0.98
bb_mid = current['bb_mid'] if not pd.isna(current['bb_mid']) else close

print("GOLDBACH PHASE IDENTIFICATION")
print("=" * 40)
print(f"Current Price: ${close:.2f}")
print(f"EMA20: ${ema20:.2f}")
print(f"EMA50: ${ema50:.2f}")
print(f"RSI: {rsi:.1f}")
print(f"BB Upper: ${bb_upper:.2f}")
print(f"BB Lower: ${bb_lower:.2f}")
print(f"BB Mid: ${bb_mid:.2f}")

# Determine trend
if ema20 > ema50 * 1.001:
    trend = "BULLISH"
elif ema20 < ema50 * 0.999:
    trend = "BEARISH"
else:
    trend = "NEUTRAL"

# Determine RSI condition
if rsi > 70:
    rsi_condition = "OVERBOUGHT"
elif rsi < 30:
    rsi_condition = "OVERSOLD"
elif rsi > 60:
    rsi_condition = "HIGH"
elif rsi < 40:
    rsi_condition = "LOW"
else:
    rsi_condition = "NEUTRAL"

# Discount vs Premium (relative to Bollinger Bands)
bb_position = (close - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5

if bb_position > 0.8:
    price_level = "PREMIUM"
elif bb_position < 0.2:
    price_level = "DISCOUNT"
elif bb_position > 0.6:
    price_level = "FAIR VALUE HIGH"
elif bb_position < 0.4:
    price_level = "FAIR VALUE LOW"
else:
    price_level = "FAIR VALUE"

print(f"\nTrend: {trend}")
print(f"RSI Condition: {rsi_condition}")
print(f"Price Level: {price_level}")
print(f"BB Position: {bb_position:.3f} (0=discount, 1=premium)")

# Goldbach Phase Classification
if rsi > 70:
    if trend == "BULLISH":
        phase = "OB"  # Overbought
    else:
        phase = "RB"  # Reversal Bear
elif rsi < 30:
    if trend == "BEARISH":
        phase = "OS"  # Oversold (assuming this maps to one of your codes)
    else:
        phase = "RB"  # Reversal Bull
elif trend == "BULLISH" and bb_position > 0.6:
    phase = "H"   # High
elif trend == "BEARISH" and bb_position < 0.4:
    phase = "L"   # Low
elif bb_position > 0.4 and bb_position < 0.6:
    if trend == "NEUTRAL":
        phase = "FV"  # Fair Value
    else:
        phase = "MB"  # Mid Band
else:
    phase = "BR"  # Breakout/Range

print(f"\nGOLDBACH PHASE: {phase}")
print(f"DISCOUNT/PREMIUM: {price_level}")

# Phase explanations
phases = {
    'OB': 'Overbought - High RSI in uptrend',
    'RB': 'Reversal - RSI extreme opposite to trend', 
    'FV': 'Fair Value - Neutral positioning',
    'LV': 'Low Value - Below fair value',
    'MB': 'Mid Band - Between fair value levels',
    'BR': 'Breakout/Range - Transition phase',
    'H': 'High - Upper price zone',
    'L': 'Low - Lower price zone'
}

print(f"\nPhase Meaning: {phases.get(phase, 'Unknown phase')}")
