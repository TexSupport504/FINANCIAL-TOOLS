"""
Fetch current market prices per-ticker from Yahoo Finance with retries/backoff to avoid 429.
Writes: history_analysis_updated_retry.txt
"""
import csv
import json
import urllib.parse
import urllib.request
import time
import random
from collections import defaultdict
from urllib.error import HTTPError, URLError

ROOT = r"D:\OneDrive\Documents\GitHub\FINANCIAL-TOOLS"
clean_csv = ROOT + "\\history_cleaned.csv"
out_file = ROOT + "\\history_analysis_updated_retry.txt"

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

tickers = sorted(positions.keys())
quotes = {}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01'
}

for t in tickers:
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(t)}"
    success = False
    for attempt in range(1, 6):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.load(resp)
            items = data.get('quoteResponse', {}).get('result', [])
            if items:
                item = items[0]
                price = item.get('regularMarketPrice')
                if price is None:
                    # try other fields
                    price = item.get('postMarketPrice') or item.get('preMarketPrice')
                quotes[t] = price
                print(f"Got {t} = {price}")
            else:
                print(f"No quote result for {t}")
                quotes[t] = None
            success = True
            break
        except HTTPError as e:
            code = e.code
            print(f"HTTPError for {t}: {code}; attempt {attempt}")
            if code == 429:
                sleep = min(30, 2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limited; sleeping {sleep:.1f}s")
                time.sleep(sleep)
                continue
            else:
                break
        except URLError as e:
            print(f"URLError for {t}: {e}; attempt {attempt}")
            time.sleep(1 + random.uniform(0, 1))
            continue
        except Exception as e:
            print(f"Error fetching {t}: {e}; attempt {attempt}")
            time.sleep(1 + random.uniform(0, 1))
            continue
    if not success and t not in quotes:
        quotes[t] = None

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
