"""
Scan common local cache locations for SQLite files, run PRAGMA integrity_check,
and rename corrupted files to *.corrupt to prevent client libraries from using them.

Run this script before re-running price fetches if you see "database disk image is malformed" errors.
"""
import os
import sqlite3
import tempfile
from pathlib import Path

HOME = Path.home()
locs = []
# Common cache locations on Windows
if 'LOCALAPPDATA' in os.environ:
    locs.append(Path(os.environ['LOCALAPPDATA']))
if 'APPDATA' in os.environ:
    locs.append(Path(os.environ['APPDATA']))
# User cache
locs.append(HOME / '.cache')
# Temp
locs.append(Path(tempfile.gettempdir()))
# Current user profile
locs.append(HOME)

seen = set()
corrupt = []
print('Scanning', ', '.join(str(p) for p in locs if p))
for base in locs:
    if not base or not base.exists():
        continue
    for dirpath, dirs, files in os.walk(base):
        for f in files:
            if f.lower().endswith(('.db', '.sqlite', '.sqlite3')):
                path = Path(dirpath) / f
                if path in seen:
                    continue
                seen.add(path)
                try:
                    conn = sqlite3.connect(str(path))
                    cur = conn.cursor()
                    cur.execute('PRAGMA integrity_check;')
                    res = cur.fetchone()
                    conn.close()
                    status = res[0] if res else None
                    if status != 'ok':
                        print('CORRUPT:', path, 'status=', status)
                        corrupt.append(path)
                    else:
                        print('OK:', path)
                except Exception as e:
                    print('ERROR opening', path, repr(e))
                    corrupt.append(path)

if corrupt:
    print('\nRenaming corrupted DBs to .corrupt backups:')
    for p in corrupt:
        try:
            new = p.with_suffix(p.suffix + '.corrupt')
            p.rename(new)
            print('Renamed', p, '->', new)
        except Exception as e:
            print('Failed to rename', p, repr(e))
else:
    print('\nNo corrupted DBs found')
print('\nDone')
