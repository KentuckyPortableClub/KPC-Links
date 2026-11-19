#!/usr/bin/env python3
"""kpc_fers_age.py: which old 2-fer row may be copied into the new file (hand-off 06, R-2F4).

A row is copied only when it carries a made_on stamp and, for both of its parks, that stamp still matches today:
the park's key entry, and the outline fingerprint when the store index has one. A row with no stamp is never copied.
The whole-key build id is not used: that id changes on every key run, even when no park was rebuilt.

The stamp is written on every row the bot decides, whether or not this check is on. The check itself follows
KPC_FERS_CARRY_MADE_ON (the switch file; an environment variable of the same name wins). Off = every row, as before.

A key file that cannot be read, or a park missing from it, is not copied. Where the store index has no fingerprint
for a park (a public shelf does not list a park it left off), the stamp checks the key entry only.

Standard library only. It decides no pair."""
import hashlib, json, os, pathlib

SETTING = 'KPC_FERS_CARRY_MADE_ON'
NOT_CARRIED = []
_INDEX = {}


def _sw():
    import kpc_fers_switches as SW
    return SW


def enabled():
    return _sw().on(SETTING)


def _fp(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()[:16]


def _bits(p):
    """The key entry as the 2-fer loader reads it: joined rows, grade, and a line record when the key has one.
    No date, no run id, no check row, no count."""
    rows = []
    for x in p.get('m') or []:
        if isinstance(x, (list, tuple)):
            rows.append([x[i] if len(x) > i else '' for i in range(4)])
    return {'m': rows, 'g': p.get('g') or '', 'line': p.get('line') if 'line' in p else None}


def _bits_ky(p):
    tr = []
    for t in p.get('tracts') or []:
        if isinstance(t, (list, tuple)):
            tr.append([t[0] if len(t) > 0 else '', t[1] if len(t) > 1 else ''])
    return {'m': tr, 'g': p.get('g') or '', 'line': p.get('line') if 'line' in p else None}


def _parks(root):
    """{ref: bits} from the key files, or None when a key file cannot be read."""
    root = str(root or '.')
    if root in _INDEX:
        return _INDEX[root]
    found, rootp = {}, pathlib.Path(root)
    try:
        for folder, pat in (('data/us-key', 'US-*.json'), ('data/ca-key', 'CA-*.json'), ('data/world-key', '*.json')):
            d = rootp / folder
            if not d.is_dir():
                continue
            for f in sorted(d.glob(pat)):
                if f.name == 'index.json':
                    continue
                doc = json.loads(f.read_text(encoding='utf-8'))
                for ref, p in (doc.get('parks') or {}).items():
                    if isinstance(p, dict):
                        found[ref] = _bits(p)
        ky = rootp / 'data/ky-answer-key.json'
        if ky.is_file():
            doc = json.loads(ky.read_text(encoding='utf-8'))
            for ref, p in (doc.get('parks') or {}).items():
                if isinstance(p, dict) and ref not in found:
                    found[ref] = _bits_ky(p)
    except (OSError, ValueError):
        _INDEX[root] = None
        return None
    _INDEX[root] = found
    return found


def key_fingerprint(ref, root='.'):
    """(fingerprint, reason). reason is set when the key cannot be read or the park is not in it."""
    parks = _parks(root)
    if parks is None:
        return '', f'the key file could not be read, so no old row is copied (fail closed)'
    bits = parks.get(ref)
    if bits is None:
        return '', f'{ref} is not in the key, so no old row of it is copied (fail closed)'
    return _fp(bits), ''


def stamp(row, area='', root='.', store_fp=None):
    """Write made_on on a row the bot just decided. Always, not only while the copy check is on.
    store_fp is {ref: the store index fingerprint} when this is a store run and the index has one.
    No date, no run id, no count."""
    if not isinstance(row, dict):
        return row
    made = {}
    for ref in row.get('refs') or []:
        key, _why = key_fingerprint(ref, root)
        outline = ''
        if isinstance(store_fp, dict) and store_fp.get(ref):
            outline = str(store_fp[ref])
        made[str(ref)] = {'key': key, 'outline': outline}
    row['made_on'] = made
    return row


def _store_fp(ref):
    """The store index fingerprint for ref, without reading the outline, or ('', reason).
    ('', '') when this run has no store index to check (the stamp then checks the key only)."""
    try:
        import kpc_fers_store as KS
    except Exception:
        return '', ''
    fn = getattr(KS, 'outline_fp', None)
    if not callable(fn):
        return '', ''
    try:
        return fn(ref)
    except Exception:
        return '', 'the store index could not be read, so no old row is copied (fail closed)'


def too_old(row, area, file_date=None, root='.'):
    """'' when the row may be copied; else the plain reason it may not. The check off = ''."""
    if not enabled() or not isinstance(row, dict):
        return ''
    made = row.get('made_on')
    if not isinstance(made, dict) or not made:
        return 'no stamp: made before this rule, so the new system measures the pair again'
    refs = [str(r) for r in (row.get('refs') or [])] or list(made)
    for ref in refs:
        got = made.get(ref) if isinstance(made.get(ref), dict) else None
        if not got:
            return f'{ref} has no stamp, so the row is not copied'
        key, why = key_fingerprint(ref, root)
        if why:
            return why
        if got.get('key') != key:
            return f"{ref}: the key entry changed, so the row is not copied"
        stored = str(got.get('outline') or '')
        if stored:
            now, owhy = _store_fp(ref)
            if owhy:
                return owhy
            if not now or now != stored:
                return f"{ref}: the outline fingerprint changed, so the row is not copied"
    return ''


def _store_present():
    try:
        import kpc_fers_store as KS
    except Exception:
        return False
    return bool(getattr(KS, 'STORE_ON', False))


def keep_fresh(rows, area, file_date=None, root='.'):
    """The rows that may be copied. The others are listed in NOT_CARRIED. The check off = every row."""
    if not enabled():
        return list(rows)
    out = []
    for x in rows:
        why = too_old(x, area, file_date, root)
        if why:
            NOT_CARRIED.append({'area': area, 'refs': list((x or {}).get('refs') or []), 'kind': (x or {}).get('kind'), 'why': why})
        else:
            out.append(x)
    return out


def old_system_areas(out_dir):
    """Area codes whose public file still has rows and none of them carries made_on. Counts only."""
    d = pathlib.Path(out_dir)
    if not d.is_dir():
        return []
    old = []
    for f in sorted(d.glob('*.json')):
        name = f.name
        if not name[:1].isalpha() or name.startswith(('report', 'receipt', 'reuse', 'store-', 'looked', 'missing')):
            continue
        try:
            doc = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        spots = doc.get('spots') if isinstance(doc, dict) else None
        area = (doc.get('st') if isinstance(doc, dict) else None) or f.stem
        if not isinstance(spots, list) or not spots:
            continue
        if any(isinstance(s, dict) and s.get('made_on') for s in spots):
            continue
        old.append(str(area))
    return old
