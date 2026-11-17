#!/usr/bin/env python3
"""kpc_fers_age.py: how old a carried 2-fer row may get (Handoff 9, bug 4 / owner question 4; KPC owner's fix list, 2026-11-17).

Several 'keep the old row' paths copy a row from the previous public file unchanged (a pair skipped for time or that crashed in
pass 1, a small-batch run, a withheld park's rows, the store's keep-the-old-row and partial-boundary rows). None of them asked how
old the row was or which key built it: on Nov 17, 42 public files (1,849 shown rows) were made before the Oct 29-30 key rebuild.

Setting KPC_FERS_CARRY_MAX (default 'off' = today's behaviour, nothing changes):
  key   never past a key rebuild: a row is carried only when it was made on the area's CURRENT key build. A row that carries its
        key build stamp ('key_build', written on every decided row while the setting is on) must match the key's build id; an
        older row without a stamp must have been checked on or after the day the key was built. Anything else is NOT carried:
        the next run measures the pair again (the row is listed for a person in the private folder, counted in the report).
        A key whose build date cannot be read = not carried (fail closed, said in the reason).
Standard library only. Decides no pair itself: it only says whether an old row may be reused."""
import json, os, pathlib

SETTING = 'KPC_FERS_CARRY_MAX'
KEY_DIRS = {'US-': 'data/us-key', 'CA-': 'data/ca-key', 'W-': 'data/world-key'}
_BUILT = {}
NOT_CARRIED = []   # [{'area', 'refs', 'kind', 'why'}]: for a person, private folder only


def mode():
    v = str(os.environ.get(SETTING) or 'off').strip().lower()
    return 'key' if v == 'key' else 'off'


def key_build(area, root='.'):
    """(build id, 'YYYY-MM-DD' built) of the key the area's parks come from; ('', '') when it cannot be read."""
    pre = next((p for p in KEY_DIRS if str(area or '').startswith(p)), None)
    if pre is None: return '', ''
    k = (str(root), pre)
    if k not in _BUILT:
        try:
            d = json.loads((pathlib.Path(root) / KEY_DIRS[pre] / 'index.json').read_text(encoding='utf-8'))
            _BUILT[k] = (str(d.get('build') or ''), str(d.get('built') or '')[:10])
        except (OSError, ValueError): _BUILT[k] = ('', '')
    return _BUILT[k]


def stamp(row, area, root='.'):
    """While the setting is on, a row decided now carries the key build it was made on."""
    if mode() != 'key' or not isinstance(row, dict): return
    b, _ = key_build(area, root)
    if b: row['key_build'] = b


def too_old(row, area, file_date=None, root='.'):
    """'' when the row may be carried; else the plain reason it may not (setting on only)."""
    if mode() != 'key' or not isinstance(row, dict): return ''
    b, d = key_build(area, root)
    if not d: return f'the {area} key build date could not be read, so no old row is carried (fail closed)'
    if row.get('key_build'):
        return '' if row['key_build'] == b else f"made on key build {row['key_build']}, the key is now {b} (built {d})"
    rd = str(row.get('checked') or row.get('found') or file_date or '')[:10]
    if rd and rd >= d: return ''
    return f"made {rd or 'on an unknown date'}, before the key was rebuilt on {d} (never past a key rebuild)"


def keep_fresh(rows, area, file_date=None, root='.'):
    """The rows that may be carried; the others are listed in NOT_CARRIED. Setting off = every row, unchanged."""
    if mode() != 'key': return list(rows)
    out = []
    for x in rows:
        why = too_old(x, area, file_date, root)
        if why: NOT_CARRIED.append({'area': area, 'refs': list((x or {}).get('refs') or []), 'kind': (x or {}).get('kind'), 'why': why})
        else: out.append(x)
    return out
