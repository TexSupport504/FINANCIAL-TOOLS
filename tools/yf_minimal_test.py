import yfinance as yf
import traceback
import os

out = os.path.join(os.path.dirname(__file__), 'yf_minimal_result.txt')
with open(out, 'w', encoding='utf-8') as f:
    try:
        f.write('starting\n')
        f.flush()
        t = yf.Ticker('AAPL')
        f.write('got ticker\n')
        f.flush()
        h = t.history(period='1d')
        f.write('rows:' + str(len(h)) + '\n')
        f.write('done\n')
    except Exception:
        traceback.print_exc(file=f)
        f.write('exception occurred\n')
        f.flush()
print('wrote', out)
