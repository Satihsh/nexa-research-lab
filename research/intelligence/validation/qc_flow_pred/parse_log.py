"""Rebuild the NEXA_FP_PART chunks of a saved QC log into one JSON file: python parse_log.py <log.txt> <out.json>."""
import json
import re
import sys

parts = {}
for line in open(sys.argv[1], encoding='utf-8'):
    m = re.search(r'NEXA_FP_PART (\d+)/(\d+) (.*)$', line.rstrip('\n'))
    if m:
        parts[int(m.group(1))] = (int(m.group(2)), m.group(3))
n = {t for t, _ in parts.values()}
assert len(n) == 1 and sorted(parts) == list(range(1, n.pop() + 1)), 'missing chunks'
res = json.loads(''.join(parts[i][1] for i in sorted(parts)))
json.dump(res, open(sys.argv[2], 'w'), indent=1)
print(res['target'], res['n_days'], res['first'], res['last'], res['test_q'], 'overall', res['overall'], res.get('skipped'))
for h, r in res['H'].items():
    s = r['stats']
    print(h, r['verdict'], 'n', s.get('S1', {}).get('n'), 'mean', s.get('S1', {}).get('mean'), s.get('S1', {}).get('ci'),
          'p', s.get('S1', {}).get('p'), 'q', s.get('q'), 'bss', r['bss'], 'p_rank', r['p_rank'],
          {f: a['adds'] for f, a in r['abl'].items()})
