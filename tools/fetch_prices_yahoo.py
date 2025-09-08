"""
Fetch current market prices using Yahoo Finance public quote API and recompute analysis.
Writes: history_analysis_updated.txt
"""
import csv
import json
import urllib.parse
import urllib.request
from collections import defaultdict

ROOT = r"D:\OneDrive\Documents\GitHub\FINANCIAL-TOOLS"
clean_csv = ROOT + "\\history_cleaned.csv"
out_file = ROOT + "\\history_analysis_updated.txt"

# Read positions
positions = defaultdict(lambda: {"quantity":0.0, "total_cost":0.0, "trades":0})
with open(clean_csv, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        t = (r.get('ticker') or '').strip()
        if not t:
            continue
        q = float(r.get('quantity') or 0)
        price = float(r.get('price') or 0)
        positions[t]['quantity'] += q
        positions[t]['total_cost'] += q * price
        positions[t]['trades'] += 1

tickers = sorted([t for t in positions.keys()])
if not tickers:
    print('No tickers found in', clean_csv)
    raise SystemExit(1)

# Query Yahoo Finance quote API
symbols = ','.join(tickers)
url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(symbols)}"
print('Querying', url)
req = urllib.request.Request(url, headers={'User-Agent': 'python-urllib/3'})
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.load(resp)

quotes = {}
for item in data.get('quoteResponse', {}).get('result', []):
    sym = item.get('symbol')
    price = item.get('regularMarketPrice')
    quotes[sym] = price

# Build analysis
lines = []
lines.append('Portfolio positions (by ticker):')
lines.append('ticker,total_quantity,total_cost,trades,avg_cost')
for t in tickers:
    q = positions[t]['quantity']
    total_cost = positions[t]['total_cost']
    trades = positions[t]['trades']
    avg = total_cost / q if q else 0.0
    lines.append(f"{t},{q},{total_cost:.4f},{trades},{avg:.6f}")

lines.append('\nMarket snapshot:')
lines.append('ticker,total_quantity,avg_cost,market_price,market_value,unrealized_pnl,unrealized_pct')
portfolio_cost = 0.0
portfolio_value = 0.0
for t in tickers:
    q = positions[t]['quantity']
    total_cost = positions[t]['total_cost']
    avg = total_cost / q if q else 0.0
    mp = quotes.get(t)
    mv = (mp * q) if (mp is not None and q) else 0.0
    upnl = mv - total_cost
    upct = (upnl / total_cost * 100) if total_cost else 0.0
    portfolio_cost += total_cost
    portfolio_value += mv
    lines.append(f"{t},{q},{avg:.6f},{mp},{mv:.2f},{upnl:.2f},{upct:.2f}%")

lines.append('\nPortfolio summary:')
lines.append(f"Total cost basis: ${portfolio_cost:.2f}")
lines.append(f"Total market value: ${portfolio_value:.2f}")
lines.append(f"Total unrealized P&L: ${portfolio_value - portfolio_cost:.2f} ({( (portfolio_value - portfolio_cost) / portfolio_cost * 100) if portfolio_cost else 0.0:.2f}% )")

with open(out_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Wrote updated analysis to', out_file)
