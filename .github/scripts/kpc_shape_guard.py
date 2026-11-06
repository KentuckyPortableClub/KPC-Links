#!/usr/bin/env python3
"""US key shape-source guard (Nov 6). Not a join rule, and not part of the rules hash.

Run 42230313177 (held US key, rules a066624520b4) timed out on every Wisconsin DNR
layer at dnrmaps.wi.gov. The builder logs that as 'layer not found' and still writes
the state, so a park whose land was only on those layers is saved as a pin
(g=pin, bk=noshape). counts.padus is how many shapes that read kept.

This compares that count to the last live key (KPC-Data data/us-key/index.json,
per state). Zero shapes, or under half the live count, is a failed source: the
workflow refills that state from the saved outlines (boundary-cache) or, if that
is also short, puts the live key's state file back and fails the job. It never
decides a join and never touches Canada or the world key.

  python3 kpc_shape_guard.py --built data/us-key --live-index path/index.json --states "WI IA"
  exit 0  every listed state is at least half the live count, or the live key has no count
  exit 2  one or more states are short; stdout is 'ST got live' per state
  exit 3  the live index could not be read
"""
import gzip, json, os, pathlib, sys

# Under half the last live key's shape count. Half itself is kept (a real shrink
# can be large; Wisconsin's missed layers were about 98% of that state's shapes).
FAR = 0.5


def is_short(got, live, far=FAR):
    """True when the live key had shapes and this read has none, or under `far` of that count."""
    try:
        live = int(live)
    except (TypeError, ValueError):
        return False
    if live <= 0:
        return False
    try:
        got = int(got)
    except (TypeError, ValueError):
        return True
    if got <= 0:
        return True
    return got < live * far


def count_of(doc):
    """The builder's shape count (counts.padus = how many records that read kept), or None."""
    c = (doc or {}).get('counts') if isinstance(doc, dict) else None
    if not isinstance(c, dict) or 'padus' not in c:
        return None
    try:
        return int(c['padus'])
    except (TypeError, ValueError):
        return None


def live_counts(index):
    """{state: padus} from a US key index. Missing states are absent, not zero."""
    out = {}
    states = (index or {}).get('states') if isinstance(index, dict) else None
    if not isinstance(states, dict):
        return out
    for st, row in states.items():
        n = count_of({'counts': row}) if isinstance(row, dict) else None
        if n is not None:
            out[str(st).upper()] = n
    return out


def short_rows(built_dir, live_index, states):
    """[(state, got or 'none', live)] for states whose built file is short vs the live key."""
    live = live_counts(live_index)
    rows = []
    for st in states:
        st = str(st).upper()
        if st not in live:
            continue
        path = pathlib.Path(built_dir) / f'US-{st}.json'
        got = None
        if path.is_file():
            try:
                got = count_of(json.loads(path.read_text(encoding='utf-8')))
            except (OSError, ValueError):
                got = None
        if is_short(got, live[st]):
            rows.append((st, 'none' if got is None else got, live[st]))
    return rows


def cache_count(path):
    """How many records a saved-outline gzip holds, or None when it cannot be read."""
    try:
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            blob = json.load(f)
    except (OSError, ValueError, gzip.BadGzipFile):
        return None
    recs = blob.get('recs') if isinstance(blob, dict) else None
    return len(recs) if isinstance(recs, list) else None


def _states(arg):
    raw = arg if arg is not None else os.environ.get('STATES') or ''
    return [s.upper() for s in raw.replace(',', ' ').split() if s.strip()]


def main(argv):
    built, live_path, states, i = 'data/us-key', None, None, 0
    while i < len(argv):
        a = argv[i]
        if a == '--built' and i + 1 < len(argv):
            built = argv[i + 1]; i += 2
        elif a == '--live-index' and i + 1 < len(argv):
            live_path = argv[i + 1]; i += 2
        elif a == '--states' and i + 1 < len(argv):
            states = argv[i + 1]; i += 2
        elif a == '--cache-count' and i + 1 < len(argv):
            n = cache_count(argv[i + 1])
            print('none' if n is None else n)
            return 0 if n is not None else 1
        else:
            print(f'unknown argument {a}', file=sys.stderr)
            return 1
    if not live_path:
        print('need --live-index', file=sys.stderr)
        return 1
    try:
        index = json.loads(pathlib.Path(live_path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        print(f'live index not read ({e})', file=sys.stderr)
        return 3
    rows = short_rows(built, index, _states(states))
    for st, got, live in rows:
        print(f'{st} {got} {live}')
    return 2 if rows else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
