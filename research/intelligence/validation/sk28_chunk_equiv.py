"""Offline check: the half-year chunk procedure (120-day warm-up) on THEIR file vs the full-history reference."""
import csv, sys, types, importlib.util, os
from datetime import datetime, date
V = '~/NEXA-Agent-Lab/research/intelligence/validation'
sys.path.insert(0, V + '/qc_sk28/frozen'); sys.path.insert(0, V + '/qc_sk28')
stub = types.ModuleType('AlgorithmImports'); stub.QCAlgorithm = object; sys.modules['AlgorithmImports'] = stub
spec = importlib.util.spec_from_file_location('m', V + '/qc_sk28/main.py'); qm = importlib.util.module_from_spec(spec); spec.loader.exec_module(qm)
year, half = int(sys.argv[3]), int(sys.argv[4])
a, b = qm.data_range(year, half)
rows = []
with open(sys.argv[1]) as f:
    r = csv.reader(f); next(r)
    for x in r:
        t = datetime.strptime(x[0], '%m/%d/%Y %H:%M')
        if a <= t.date() <= b:
            rows.append((t, float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])))
from ref_trades import REF
res = qm.chunk_result(rows, year, half, REF)
print({k: res[k] for k in ('window', 'bars', 'first_bar', 'signals', 'trades', 'mirror_refused', 'r_clamped', 'eth_1801', 'gross_mean', 'S1_mean', 'gate', 'seconds')})
