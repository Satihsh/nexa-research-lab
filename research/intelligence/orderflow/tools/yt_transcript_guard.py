#!/usr/bin/env python3
"""Rate-limit-safe YouTube transcript fetcher for NEXA research (no proxies, no cookies, no installs).

Why: the YouTube MCP (`yt-mcp-server` 0.1.2) calls youtube-transcript-api with no backoff, retries a second request
chain on every failure, and fans out 5 parallel workers in `search_channel_transcripts`. Once YouTube answers 429,
every further call extends the block. This guard enforces:

  * a PERSISTENT cooldown (state file survives sessions); no network request is made while it is active;
  * EXPONENTIAL backoff: cooldown = min(48 h, 2 h * 2**(n-1)) + jitter after the n-th consecutive block;
  * a REQUEST BUDGET: max videos per local day, per run, and a minimum spacing between videos;
  * STOP-ON-BLOCK: the first IpBlocked / RequestBlocked / HTTP 429 ends the run immediately (no in-run retry);
  * one request chain per video (watch page -> innertube player -> timedtext); no list() fallback;
  * permanent failures (transcripts disabled, unavailable) are remembered and never retried;
  * a lock file so two runs never overlap.

Run it with the interpreter of the MCP's cached uv environment (already present; nothing is installed), e.g.
  ~/.cache/uv/archive-v0/<env>/bin/python -I yt_transcript_guard.py status
Commands: status | fetch --ids ... --out DIR | watch --ids ... --out DIR [--max-attempts N] [--max-hours H] | selftest
Exit codes: 0 all done, 75 blocked/cooldown (EX_TEMPFAIL), 76 budget exhausted, 2 usage/lock error.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import random
import sys
import tempfile
import time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.environ.get('YT_GUARD_STATE', os.path.join(HERE, 'yt_guard_state.json'))

BASE_COOLDOWN_S = 2 * 3600
MAX_COOLDOWN_S = 48 * 3600
JITTER_S = 600
DAILY_BUDGET_VIDEOS = 25          # each video = ~3 HTTP requests
MAX_VIDEOS_PER_RUN = 10
MIN_SPACING_S = 30
SPACING_JITTER_S = 15

EX_OK, EX_USAGE, EX_TEMPFAIL, EX_BUDGET = 0, 2, 75, 76


# ----------------------------------------------------------------------------- state
def _now() -> float:
    return time.time()


def load_state(path: str = None) -> dict:
    path = path or STATE
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {'cooldown_until': 0.0, 'consecutive_blocks': 0, 'last_block_at': None, 'budget': {},
            'done': [], 'permanent_fail': {}, 'events': []}


def save_state(st: dict, path: str = None) -> None:
    path = path or STATE
    st['events'] = st['events'][-200:]
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, path)


def _iso(ts) -> str | None:
    return datetime.fromtimestamp(ts).isoformat(timespec='seconds') if ts else None


def _log(st: dict, kind: str, **kw) -> None:
    st['events'].append({'t': _iso(_now()), 'kind': kind, **kw})


def register_block(st: dict, reason: str, rng=random) -> float:
    st['consecutive_blocks'] = int(st.get('consecutive_blocks', 0)) + 1
    n = st['consecutive_blocks']
    cd = min(MAX_COOLDOWN_S, BASE_COOLDOWN_S * 2 ** (n - 1)) + rng.uniform(0, JITTER_S)
    st['cooldown_until'] = _now() + cd
    st['last_block_at'] = _iso(_now())
    _log(st, 'block', reason=reason, consecutive=n, cooldown_h=round(cd / 3600, 2), until=_iso(st['cooldown_until']))
    return cd


def cooldown_left(st: dict) -> float:
    return max(0.0, float(st.get('cooldown_until', 0)) - _now())


def budget_left(st: dict) -> int:
    day = datetime.now().strftime('%Y-%m-%d')
    st['budget'] = {day: st.get('budget', {}).get(day, 0)}       # keep today only
    return DAILY_BUDGET_VIDEOS - st['budget'][day]


def spend(st: dict) -> None:
    day = datetime.now().strftime('%Y-%m-%d')
    st['budget'][day] = st['budget'].get(day, 0) + 1


# ----------------------------------------------------------------------------- fetching
def classify(exc: Exception) -> str:
    """'block' | 'permanent' | 'soft'."""
    name = type(exc).__name__
    names = {c.__name__ for c in type(exc).__mro__}
    if names & {'IpBlocked', 'RequestBlocked'} or ' 429' in str(exc) or 'Too Many Requests' in str(exc):
        return 'block'
    if name in {'TranscriptsDisabled', 'NoTranscriptFound', 'VideoUnavailable', 'InvalidVideoId',
                'AgeRestricted', 'VideoUnplayable'}:
        return 'permanent'
    return 'soft'


def real_fetcher(video_id: str) -> list:
    from youtube_transcript_api import YouTubeTranscriptApi          # present in the MCP's uv env
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id, languages=['en'])                   # one request chain; no list() fallback
    return [{'start': s.start, 'duration': s.duration, 'text': s.text} for s in fetched]


def run_fetch(ids: list, out: str, fetcher=real_fetcher, state_path: str = None, sleep=time.sleep,
              rng=random) -> int:
    st = load_state(state_path)
    os.makedirs(out, exist_ok=True)
    left = cooldown_left(st)
    if left > 0:
        print(f'COOLDOWN active until {_iso(st["cooldown_until"])} ({left / 3600:.2f} h); no request made.')
        return EX_TEMPFAIL
    pending = [v for v in ids if v not in st['done'] and v not in st['permanent_fail']
               and not os.path.exists(os.path.join(out, v + '.json'))]
    if not pending:
        print('Nothing pending.')
        return EX_OK
    soft_streak = 0
    n_run = 0
    for k, vid in enumerate(pending):
        if budget_left(st) <= 0:
            _log(st, 'budget_exhausted'); save_state(st, state_path)
            print('Daily budget exhausted; stopping.')
            return EX_BUDGET
        if n_run >= MAX_VIDEOS_PER_RUN:
            save_state(st, state_path)
            print(f'Per-run cap ({MAX_VIDEOS_PER_RUN}) reached; stopping.')
            return EX_BUDGET
        if k > 0:
            sleep(MIN_SPACING_S + rng.uniform(0, SPACING_JITTER_S))
        spend(st); n_run += 1
        try:
            segs = fetcher(vid)
        except Exception as e:                                          # noqa: BLE001 - classified below
            kind = classify(e)
            if kind == 'block':
                cd = register_block(st, f'{type(e).__name__} on {vid}', rng)
                save_state(st, state_path)
                print(f'BLOCKED on {vid} ({type(e).__name__}); cooldown {cd / 3600:.2f} h until {_iso(st["cooldown_until"])}. Stopping.')
                return EX_TEMPFAIL
            if kind == 'permanent':
                st['permanent_fail'][vid] = type(e).__name__
                _log(st, 'permanent_fail', video=vid, error=type(e).__name__)
                save_state(st, state_path)
                print(f'{vid}: permanent failure {type(e).__name__}; will not retry.')
                continue
            soft_streak += 1
            _log(st, 'soft_fail', video=vid, error=f'{type(e).__name__}: {str(e)[:200]}')
            save_state(st, state_path)
            print(f'{vid}: soft failure {type(e).__name__}.')
            if soft_streak >= 2:
                print('Two consecutive soft failures; stopping.')
                return EX_TEMPFAIL
            continue
        soft_streak = 0
        with open(os.path.join(out, vid + '.json'), 'w') as f:
            json.dump(segs, f, ensure_ascii=False)
        st['done'].append(vid)
        st['consecutive_blocks'] = 0                                    # success resets the backoff ladder
        _log(st, 'ok', video=vid, segments=len(segs))
        save_state(st, state_path)
        print(f'{vid}: OK ({len(segs)} segments).')
    print('All pending processed.')
    return EX_OK


def with_lock(fn):
    def wrapper(*a, **kw):
        lock_path = (kw.get('state_path') or STATE) + '.lock'
        fd = open(lock_path, 'w')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another guard run holds the lock; exiting.')
            return EX_USAGE
        try:
            return fn(*a, **kw)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN); fd.close()
    return wrapper


@with_lock
def run_watch(ids, out, max_attempts=4, max_hours=36.0, state_path=None, fetcher=real_fetcher):
    deadline = _now() + max_hours * 3600
    attempts = 0
    while True:
        st = load_state(state_path)
        left = cooldown_left(st)
        if left > 0:
            if _now() + left > deadline:
                print(f'Next window {_iso(st["cooldown_until"])} is past the deadline; exiting.')
                return EX_TEMPFAIL
            print(f'{_iso(_now())} waiting {left / 3600:.2f} h for cooldown to end ({_iso(st["cooldown_until"])}).', flush=True)
            time.sleep(left + 5)
        attempts += 1
        print(f'{_iso(_now())} attempt {attempts}/{max_attempts}', flush=True)
        rc = run_fetch(ids, out, fetcher=fetcher, state_path=state_path)
        if rc == EX_OK:
            return EX_OK
        if rc == EX_BUDGET:
            return EX_BUDGET
        if attempts >= max_attempts:
            print('Max attempts reached; exiting (state keeps the cooldown).')
            return EX_TEMPFAIL


# ----------------------------------------------------------------------------- self-test (no network)
def selftest() -> int:
    class IpBlocked(Exception):
        pass

    class TranscriptsDisabled(Exception):
        pass

    with tempfile.TemporaryDirectory() as d:
        sp = os.path.join(d, 's.json'); out = os.path.join(d, 'o')
        calls = []

        def fake(vid):
            calls.append(vid)
            if vid == 'blk':
                raise IpBlocked(vid)
            if vid == 'dis':
                raise TranscriptsDisabled(vid)
            return [{'start': 0, 'duration': 1, 'text': 'x'}]
        nos = lambda s: None
        # 1. success + permanent failure are recorded; spacing sleeps are skipped in test
        assert run_fetch(['a', 'dis', 'b'], out, fake, sp, sleep=nos) == EX_OK
        st = load_state(sp)
        assert st['done'] == ['a', 'b'] and 'dis' in st['permanent_fail']
        # 2. block stops the run immediately; later ids are not requested
        calls.clear()
        assert run_fetch(['blk', 'c'], out, fake, sp, sleep=nos) == EX_TEMPFAIL
        assert calls == ['blk']
        st = load_state(sp)
        cd1 = st['cooldown_until'] - _now()
        assert 2 * 3600 - 5 <= cd1 <= 2 * 3600 + JITTER_S + 5 and st['consecutive_blocks'] == 1
        # 3. during cooldown no request is made at all
        calls.clear()
        assert run_fetch(['c'], out, fake, sp, sleep=nos) == EX_TEMPFAIL and calls == []
        # 4. exponential ladder: 2h, 4h, 8h, ... capped at 48h
        st['cooldown_until'] = 0; save_state(st, sp)
        for n_expected, base in ((2, 4), (3, 8), (4, 16), (5, 32), (6, 48), (7, 48)):
            st = load_state(sp); st['cooldown_until'] = 0; save_state(st, sp)
            run_fetch(['blk'], out, fake, sp, sleep=nos)
            st = load_state(sp)
            cd = st['cooldown_until'] - _now()
            assert st['consecutive_blocks'] == n_expected
            assert base * 3600 - 5 <= cd <= base * 3600 + JITTER_S + 5, (n_expected, cd / 3600)
        # 5. success resets the ladder
        st['cooldown_until'] = 0; save_state(st, sp)
        assert run_fetch(['d'], out, fake, sp, sleep=nos) == EX_OK
        assert load_state(sp)['consecutive_blocks'] == 0
        # 6. budget: exhausted budget stops before any request
        st = load_state(sp); st['budget'] = {datetime.now().strftime('%Y-%m-%d'): DAILY_BUDGET_VIDEOS}; save_state(st, sp)
        calls.clear()
        assert run_fetch(['e'], out, fake, sp, sleep=nos) == EX_BUDGET and calls == []
        # 7. per-run cap
        st = load_state(sp); st['budget'] = {}; save_state(st, sp)
        many = [f'v{i}' for i in range(MAX_VIDEOS_PER_RUN + 3)]
        calls.clear()
        assert run_fetch(many, out, fake, sp, sleep=nos) == EX_BUDGET and len(calls) == MAX_VIDEOS_PER_RUN
    print('selftest: 7/7 PASS')
    return EX_OK


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status')
    sub.add_parser('selftest')
    for name in ('fetch', 'watch'):
        p = sub.add_parser(name)
        p.add_argument('--ids', nargs='+', required=True)
        p.add_argument('--out', required=True)
        if name == 'watch':
            p.add_argument('--max-attempts', type=int, default=4)
            p.add_argument('--max-hours', type=float, default=36.0)
    sub.add_parser('seed-block').add_argument('--at', required=True, help='ISO time of the last observed block')
    a = ap.parse_args()
    if a.cmd == 'selftest':
        return selftest()
    if a.cmd == 'status':
        st = load_state()
        print(json.dumps({'cooldown_until': _iso(st.get('cooldown_until')), 'cooldown_left_h': round(cooldown_left(st) / 3600, 2),
                          'consecutive_blocks': st.get('consecutive_blocks'), 'budget_left_today': budget_left(st),
                          'done': len(st.get('done', [])), 'permanent_fail': st.get('permanent_fail'),
                          'last_events': st.get('events', [])[-5:]}, indent=1))
        return EX_OK
    if a.cmd == 'seed-block':
        st = load_state()
        t = datetime.fromisoformat(a.at).timestamp()
        st['consecutive_blocks'] = int(st.get('consecutive_blocks', 0)) + 1
        n = st['consecutive_blocks']
        st['cooldown_until'] = t + min(MAX_COOLDOWN_S, BASE_COOLDOWN_S * 2 ** (n - 1))
        st['last_block_at'] = a.at
        _log(st, 'seeded_block', at=a.at, consecutive=n, until=_iso(st['cooldown_until']))
        save_state(st)
        print(f'seeded: consecutive={n}, cooldown until {_iso(st["cooldown_until"])}')
        return EX_OK
    if a.cmd == 'fetch':
        return with_lock(run_fetch)(a.ids, a.out)
    if a.cmd == 'watch':
        return run_watch(a.ids, a.out, a.max_attempts, a.max_hours)
    return EX_USAGE


if __name__ == '__main__':
    sys.exit(main())
