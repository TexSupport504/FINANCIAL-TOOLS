import traceback

out = 'import_check.txt'
with open(out, 'w') as f:
    f.write('Starting import check\n')
    modules = ['ccxt','ta','pandas','numpy','matplotlib']
    for m in modules:
        try:
            __import__(m)
            f.write(f'OK: {m}\n')
        except Exception:
            f.write(f'ERROR importing {m}:\n')
            traceback.print_exc(file=f)
            f.write('\n')
print('Wrote import_check.txt')
