import traceback

OUT='quick_wrapper_log.txt'
with open(OUT,'w') as out:
    try:
        out.write('Starting import of quick_sweep_log\n')
        import quick_sweep_log
        out.write('Import succeeded\n')
    except Exception:
        out.write('Exception during import/run of quick_sweep_log:\n')
        traceback.print_exc(file=out)
print('Wrote quick_wrapper_log.txt')
