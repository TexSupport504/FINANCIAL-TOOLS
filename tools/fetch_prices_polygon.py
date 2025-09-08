"""
Fetch live prices from Polygon.io using POLYGON_API_KEY (loaded from environment or .env)
and compute updated portfolio analysis from history_cleaned.csv. Writes history_analysis_polygon.txt
"""
import os
import csv
import time
import random
import json
from collections import defaultdict
from urllib.error import HTTPError, URLError
import urllib.request

ROOT = r"D:\OneDrive\Documents\GitHub\FINANCIAL-TOOLS"
CLEAN_CSV = os.path.join(ROOT, 'history_cleaned.csv')
OUT = os.path.join(ROOT, 'history_analysis_polygon.txt')

# Load API key from environment or .env
API_KEY = os.getenv('POLYGON_API_KEY')
if not API_KEY:
    env_path = os.path.join(ROOT, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('POLYGON_API_KEY='):
                    API_KEY = line.split('=', 1)[1].strip()
                    break

if not API_KEY:
    raise SystemExit('POLYGON_API_KEY not set in environment or .env')

# Read positions
positions = defaultdict(lambda: {'quantity': 0.0, 'total_cost': 0.0, 'trades': 0})
with open(CLEAN_CSV, newline='', encoding='utf-8') as f:
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

if not positions:
    raise SystemExit('No tickers found in cleaned CSV')

tickers = sorted(positions.keys())
quotes = {}

headers = {'User-Agent': 'polygon-client/1.0'}

for t in tickers:
    url = f'https://api.polygon.io/v2/last/trade/{urllib.parse.quote(t)}?apiKey={API_KEY}' if False else None

# import urllib.parse here (late to satisfy linter)
import urllib.parse

for t in tickers:
    # Use v2 last trade endpoint: /v2/last/trade/{symbol}
    url = f'https://api.polygon.io/v2/last/trade/{urllib.parse.quote(t)}?apiKey={API_KEY}'
    attempts = 0
    price = None
    while attempts < 6:
        attempts += 1
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'python-urllib/3'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.load(resp)
            # Expected structure: {'status':'OK', 'results': {'p': price, ...}}
            if isinstance(data, dict):
                r = data.get('results')
                if r and isinstance(r, dict):
                    price = r.get('p')
                else:
                    # Some endpoints use 'last' wrapper
                    price = r and r.get('price') if isinstance(r, dict) else None
            quotes[t] = price
            print(f'Got {t} -> {price}')
            break
        except HTTPError as e:
            code = getattr(e, 'code', None)
            print(f'HTTPError {code} for {t}; attempt {attempts}')
            if code in (429, 500, 502, 503, 504):
                sleep = min(30, (2 ** attempts)) + random.random()
                time.sleep(sleep)
                continue
            elif code in (401, 403):
                print('Auth/permission error from Polygon; aborting fetch')
                quotes[t] = None
                break
            else:
                quotes[t] = None
                break
        except URLError as e:
            print(f'URLError for {t}: {e}; attempt {attempts}')
            time.sleep(1 + random.random())
            continue
        except Exception as e:
            print(f'Error fetching {t}: {e}; attempt {attempts}')
            time.sleep(1 + random.random())
            continue
    if t not in quotes:
        quotes[t] = price

# Build analysis
lines = []
lines.append('Portfolio positions (by ticker):')
lines.append('ticker,total_quantity,total_cost,trades,avg_cost')
portfolio_cost = 0.0
for t in tickers:
    q = positions[t]['quantity']
    total_cost = positions[t]['total_cost']
    trades = positions[t]['trades']
    avg = (total_cost / q) if q else 0.0
    lines.append(f"{t},{q},{total_cost:.4f},{trades},{avg:.6f}")
    portfolio_cost += total_cost

lines.append('\nMarket snapshot:')
lines.append('ticker,total_quantity,avg_cost,market_price,market_value,unrealized_pnl,unrealized_pct')
portfolio_value = 0.0
for t in tickers:
    q = positions[t]['quantity']
    total_cost = positions[t]['total_cost']
    avg = (total_cost / q) if q else 0.0
    mp = quotes.get(t)
    mv = (mp * q) if (mp is not None and q) else 0.0
    upnl = mv - total_cost
    upct = (upnl / total_cost * 100) if total_cost else 0.0
    portfolio_value += mv
    lines.append(f"{t},{q},{avg:.6f},{mp},{mv:.2f},{upnl:.2f},{upct:.2f}%")

lines.append('\nPortfolio summary:')
lines.append(f"Total cost basis: ${portfolio_cost:.2f}")
lines.append(f"Total market value: ${portfolio_value:.2f}")
lines.append(f"Total unrealized P&L: ${portfolio_value - portfolio_cost:.2f} ({((portfolio_value - portfolio_cost) / portfolio_cost * 100) if portfolio_cost else 0.0:.2f}% )")

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Wrote', OUT)
