#!/usr/bin/env python3
"""kpc_fers_age.py: which old 2-fer row may be copied into the new file (hand-off 06, R-2F4).

A row is copied only when it carries a made_on stamp and, for both of its parks, that stamp still matches today:
the park's key entry, and the outline it was measured from when this run has that outline in hand. A row with no
stamp is never copied. The whole-key build id is not used: that id changes on every key run, even when no park
was rebuilt.

The stamp is written on every row pass 3 settles, whether or not this check is on. The check itself follows
KPC_FERS_CARRY_MADE_ON (the switch file; an environment variable of the same name wins). Off = every row, as before.

outline_kind says which fingerprint `outline` is, so a store index fingerprint and an outline hash are never
compared with each other:
  store    the store index's own checksum (a store run)
  outline  the outline hash pair_fp reads for that park (its outline, its line without the read date)
  ''       no outline was stamped (the index had none). The check is the key entry only.

A key file that cannot be read, or a park missing from it, is not copied. A stamp that holds an outline
fingerprint is not copied when today's index has none for that park (it cannot be proved unchanged).

Standard library only. It decides no pair."""
import hashlib, json, os, pathlib, re

SETTING = 'KPC_FERS_CARRY_MADE_ON'
FILE_MARK = 'R-2F4'
FILE_MARK_FIELD = 'written_by_rule'
NOT_CARRIED = []
KEY_ONLY = []   # rows copied on the key entry only: this run did not read that park's outline
_INDEX = {}
_key_only = False


def _sw():
    import kpc_fers_switches as SW
    return SW


def enabled():
    return _sw().on(SETTING)


def _fp(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()[:16]


def _bits(p):
    """The key entry as the 2-fer loader reads it: joined rows (id, name, acres, how), grade, a line record,
    parts (the loader clips a shared record to these pieces) and approx. No date, no run id, no check row, no count."""
    rows = []
    for x in p.get('m') or []:
        if isinstance(x, (list, tuple)):
            rows.append([x[i] if len(x) > i else '' for i in range(4)])
    return {'m': rows, 'g': p.get('g') or '', 'line': p.get('line') if 'line' in p else None,
            'parts': p.get('parts') if 'parts' in p else None,
            'approx': p.get('approx') if 'approx' in p else None}


def _bits_ky(p):
    """Kentucky tracts: layer, name, acres and how, as the US joined row does. The fifth number is a count and is left out."""
    tr = []
    for t in p.get('tracts') or []:
        if isinstance(t, (list, tuple)):
            tr.append([t[i] if len(t) > i else '' for i in range(4)])
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
        return '', 'the key file could not be read, so no old row is copied (fail closed)'
    bits = parks.get(ref)
    if bits is None:
        return '', f'{ref} is not in the key, so no old row of it is copied (fail closed)'
    return _fp(bits), ''


def stamp(row, area='', root='.', store_fp=None, outlines=None):
    """Write made_on on a row pass 3 just settled. Always, not only while the copy check is on.
    store_fp is {ref: the store index fingerprint} on a store run, for the refs the index can fingerprint.
    outlines is {ref: the outline hash} on a run that is not using the store. No date, no run id, no count."""
    if not isinstance(row, dict):
        return row
    made = {}
    for ref in row.get('refs') or []:
        ref = str(ref)
        key, _why = key_fingerprint(ref, root)
        if isinstance(store_fp, dict) and store_fp.get(ref):
            made[ref] = {'key': key, 'outline': str(store_fp[ref]), 'outline_kind': 'store'}
        elif isinstance(outlines, dict) and outlines.get(ref):
            made[ref] = {'key': key, 'outline': str(outlines[ref]), 'outline_kind': 'outline'}
        else:
            made[ref] = {'key': key, 'outline': '', 'outline_kind': ''}
    row['made_on'] = made
    return row


def _store_fp(ref):
    """The store index fingerprint for ref, without reading the outline, or ('', reason).
    ('', '') when this run has no store index to check."""
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


def _outline_in_hand(ref):
    """True when this run loaded that park's outline or its line."""
    try:
        import kpc_fers as K
    except Exception:
        return False
    return ref in (getattr(K, 'CURG', None) or {}) or ref in (getattr(K, 'CURLN', None) or {})


def _outline_now(ref):
    import kpc_fers as K
    return K.outline_stamp(ref, getattr(K, 'CURG', {}) or {}, getattr(K, 'CURLN', {}) or {})


def too_old(row, area, file_date=None, root='.'):
    """'' when the row may be copied; else the plain reason it may not. The check off = ''.
    Sets _key_only when an outline-hash stamp was checked on the key entry only, because this run
    did not read that park."""
    global _key_only
    _key_only = False
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
        kind = str(got.get('outline_kind') or '')
        if not kind and stored:
            kind = 'store'   # a stamp from the first round held a store fingerprint and no kind
        if kind == 'store' and stored:
            now, owhy = _store_fp(ref)
            if owhy:
                return owhy
            if not now or now != stored:
                return f"{ref}: the outline fingerprint changed, so the row is not copied"
        elif kind == 'outline' and stored:
            if _outline_in_hand(ref):
                if _outline_now(ref) != stored:
                    return f"{ref}: the outline hash changed, so the row is not copied"
            else:
                _key_only = True
    return ''


def _store_present():
    try:
        import kpc_fers_store as KS
    except Exception:
        return False
    return bool(getattr(KS, 'STORE_ON', False))


def keep_fresh(rows, area, file_date=None, root='.'):
    """The rows that may be copied. The others are listed in NOT_CARRIED. The check off = every row.
    A copied row whose outline hash could not be checked (this run did not read the park) is listed in KEY_ONLY."""
    if not enabled():
        return list(rows)
    out = []
    for x in rows:
        why = too_old(x, area, file_date, root)
        if why:
            NOT_CARRIED.append({'area': area, 'refs': list((x or {}).get('refs') or []), 'kind': (x or {}).get('kind'), 'why': why})
        else:
            out.append(x)
            if _key_only:
                KEY_ONLY.append({'area': area, 'refs': list((x or {}).get('refs') or [])})
    return out


def _in_region(stem, region):
    region = (region or 'na').strip().lower()
    if region == 'world':
        return bool(re.fullmatch(r'W-[A-Z]{2}', stem))
    if region == 'ky':
        return stem == 'US-KY'
    if stem == 'US-KY':
        return False
    return bool(re.fullmatch(r'(US|CA)-[A-Z]{2}', stem))


def old_system_areas(out_dir, region=None):
    """Area codes of this run's region whose public file does not carry this rule's mark.
    A file this code writes carries written_by_rule. A file outside the region is not listed.
    A file that cannot be read is not listed."""
    if region is None:
        try:
            import kpc_fers as K
            region = getattr(K, 'REGION', 'na')
        except Exception:
            region = 'na'
    d = pathlib.Path(out_dir)
    if not d.is_dir():
        return []
    old = []
    for f in sorted(d.glob('*.json')):
        if not _in_region(f.stem, region):
            continue
        try:
            doc = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if not isinstance(doc, dict):
            continue
        if doc.get(FILE_MARK_FIELD) == FILE_MARK:
            continue
        area = doc.get('st') or f.stem
        old.append(str(area))
    return old
