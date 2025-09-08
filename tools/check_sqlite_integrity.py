"""
Scan workspace for SQLite files, run PRAGMA integrity_check, and rename corrupted files to *.corrupt (safe backup).
"""
import os
import sqlite3

ROOT = r"D:\OneDrive\Documents\GitHub\FINANCIAL-TOOLS"
corrupt = []
print(f"Scanning for .db/.sqlite files under {ROOT}")
for dirpath, dirs, files in os.walk(ROOT):
    for f in files:
        if f.lower().endswith(('.db', '.sqlite', '.sqlite3')):
            path = os.path.join(dirpath, f)
            try:
                conn = sqlite3.connect(path)
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
    print(f"\nFound {len(corrupt)} corrupted DB(s). Renaming to .corrupt backups")
    for p in corrupt:
        new = p + '.corrupt'
        try:
            os.rename(p, new)
            print('Renamed', p, '->', new)
        except Exception as e:
            print('Failed to rename', p, repr(e))
else:
    print('\nNo corrupted DBs found')
