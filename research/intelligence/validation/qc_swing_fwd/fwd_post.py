"""H-SWING-FWD post-processing: rebuild the result JSON from a QC log.
v2 logs: reassemble 'NEXA_SWING_FWD_PART i/n' chunks. v1 log (Part A, truncated, DEVIATIONS_SWING_FWD D-1): keep the complete part."""
from __future__ import annotations

import json
import re
import sys


def load(path):
    text = open(path).read()
    parts = {}
    for m in re.finditer(r'NEXA_SWING_FWD_PART (\d+)/(\d+) (.*)', text):
        parts[int(m.group(1))] = (int(m.group(2)), m.group(3))
    if parts:
        n = next(iter(parts.values()))[0]
        if sorted(parts) != list(range(1, n + 1)):
            sys.exit('missing chunks: have %s of %d' % (sorted(parts), n))
        return json.loads(''.join(parts[i][1] for i in range(1, n + 1))), True
    s = text[text.index('NEXA_SWING_FWD ') + len('NEXA_SWING_FWD '):].split('\n')[0]
    try:
        return json.loads(s), True
    except json.JSONDecodeError:
        return json.loads(s[:s.index(',"controls"')] + '}'), False


if __name__ == '__main__':
    res, complete = load(sys.argv[1])
    json.dump(res, open(sys.argv[2], 'w'), indent=1, sort_keys=True)
    print('complete' if complete else 'TRUNCATED (controls/A0/A1/fwd_verdict missing)', res.get('data_end'))
