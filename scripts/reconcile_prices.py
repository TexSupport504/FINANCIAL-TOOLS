"""
Compare reported prices in the latest eth_15m JSON audit with the recorded snapshot.
Prints deltas, percent differences, and timing/symbol notes to help reconcile discrepancies.
"""
import os
import json
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'analysis_reports')
files = [f for f in os.listdir(REPORTS_DIR) if f.startswith('eth_15m_') and f.endswith('.json')]
if not files:
    print('No eth_15m JSON audit files found in', REPORTS_DIR)
    raise SystemExit(1)
files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(REPORTS_DIR, x)))
json_path = os.path.join(REPORTS_DIR, files[-1])
print('Using JSON audit:', json_path)

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

report_price = data.get('current_price') or data.get('cycle', {}).get('completion_price')
cycle = data.get('cycle', {})
snapshot = data.get('snapshot', {})
symbol = data.get('symbol')

print('\nReport fields:')
print(' symbol:', symbol)
print(' report current_price:', report_price)
print(' cycle completion_time:', cycle.get('completion_time'))
print(' cycle completion_price:', cycle.get('completion_price'))
print(' cycle range high/low:', cycle.get('cycle_high'), '/', cycle.get('cycle_low'))

print('\nSnapshot fields:')
print(' snapshot source:', snapshot.get('source'))
print(' snapshot price:', snapshot.get('price'))
print(' snapshot timestamp:', snapshot.get('timestamp'))
print(' snapshot latency_seconds:', snapshot.get('latency_seconds'))

# numeric compare
try:
    rp = float(report_price)
    sp = float(snapshot.get('price'))
    diff = rp - sp
    pct = (diff / sp) * 100 if sp else None
    print('\nComparison:')
    print(f' delta = {diff:.2f} USD')
    if pct is not None:
        print(f' percent difference = {pct:.2f}%')
except Exception as e:
    print('Could not compare numeric prices:', e)

# timing check
try:
    ts_report = data.get('timestamp_utc')
    ts_snapshot = snapshot.get('timestamp')
    if ts_report:
        t_report = datetime.fromisoformat(ts_report.replace('Z',''))
    else:
        t_report = None
    if ts_snapshot:
        # try several formats
        try:
            t_snap = datetime.fromisoformat(ts_snapshot)
        except Exception:
            try:
                t_snap = datetime.strptime(ts_snapshot, '%Y-%m-%d %H:%M:%S.%f')
            except Exception:
                try:
                    t_snap = datetime.strptime(ts_snapshot, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    t_snap = None
    print('\nTimestamps:')
    print(' report timestamp_utc:', ts_report)
    print(' snapshot timestamp:', ts_snapshot)
    if t_report and t_snap:
        delta = (t_report - t_snap).total_seconds()
        print(' difference (report - snapshot) =', delta, 'seconds')
        if abs(delta) > 300:
            print(' NOTE: difference > 5 minutes — likely stale snapshot or timezone mismatch')
except Exception as e:
    print('Could not parse timestamps:', e)

# Suggestions
print('\nSuggested actions:')
print('- Re-run a live Coinbase snapshot now and compare to report current_price.')
print("- Confirm symbol normalization/feeds: e.g., 'X:ETHUSD' vs 'ETH-USD' vs 'ETHUSD'.")
print('- If snapshot is stale, ensure snapshot is fetched immediately before/after analysis run.')
print('- Optionally re-run the analysis using Coinbase price as the authoritative current_price.')
