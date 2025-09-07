import traceback

OUT='quick_wrapper_log.txt'
with open(OUT,'w') as out:
    try:
        out.write('Importing quick_sweep_log.py\n')
        import quick_sweep_log
        out.write('Imported module quick_sweep_log successfully\n')
    except Exception:
        out.write('Exception during import/run of quick_sweep_log:\n')
        traceback.print_exc(file=out)
print('Wrote quick_wrapper_log.txt')
