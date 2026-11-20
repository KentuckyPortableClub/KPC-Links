#!/usr/bin/env python3
"""kpc_park_facts_read.py: the keys' one reader for KPC-Data's park facts file (data/park-facts.json.gz).

The owner, 20 Nov 2026 2:49-2:51 PM: "have the master file built for the keys to read ... teach the key bots to read it".
KPC-Data's kpc-park-facts.yml puts the acreage bot's official sizes, the park page reader's facts and the link IDs side by side,
one row per park. This module is how a key bot reads that file. It contacts nothing: the workflow step clones the one file
read-only (as the key jobs already clone KPC-Data's parks list) and sets PARK_FACTS to its path.

What reads it today:
  official_acres()   the size readers (kpc_us_key size self-check, kpc_join_check, kpc_key_health, kpc_key_trend) read
                     data/acres.json first, exactly as before; only when that file is missing do they take the official sizes
                     from here. Same numbers the acreage bot found, with the same source and date.
  link_ids(), page_facts()   ready for the size-witness rules (plan section 3). NOTHING calls them yet: what a link id or a page
                     fact may count for is the reviewed rules' call, not this reader's.

  python3 kpc_park_facts_read.py acres [--out data/acres.json]   write the official sizes as an acres.json file (never over one)
  python3 kpc_park_facts_read.py counts
  python3 kpc_park_facts_read.py --selftest
"""
import gzip, json, os, sys, tempfile

PATHS = ('data/park-facts.json.gz', 'data/park-facts.json', '.pf/data/park-facts.json.gz', '.pi/data/park-facts.json.gz',
         'kpcdata/data/park-facts.json.gz')
_CACHE = {}


def find(path=None):
    """The park facts file: PARK_FACTS, else $DATA/data/park-facts.json.gz, else the usual places. None when there is none."""
    cands = [path, os.environ.get('PARK_FACTS')]
    if os.environ.get('DATA'):
        cands.append(os.path.join(os.environ['DATA'], 'data', 'park-facts.json.gz'))
    cands += list(PATHS)
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


def load(path=None):
    """-> the whole document, or {} when there is no file or it cannot be read (a reader never stops a key build)."""
    p = find(path)
    if not p:
        return {}
    if p in _CACHE:
        return _CACHE[p]
    try:
        op = gzip.open if p.endswith('.gz') else open
        with op(p, 'rt', encoding='utf-8') as f:
            d = json.load(f)
        d = d if isinstance(d, dict) and isinstance(d.get('parks'), dict) else {}
    except (OSError, ValueError, EOFError):
        d = {}
    _CACHE[p] = d
    return d


def parks(path=None):
    return load(path).get('parks') or {}


def acres_rows(path=None):
    """-> {ref: row} in the acreage bot's own acres.json shape (acres, agency, source_url, read_date, ...)."""
    out = {}
    for ref, r in parks(path).items():
        s = r.get('size') if isinstance(r, dict) else None
        if isinstance(s, dict) and s.get('acres') is not None:
            out[ref] = dict(s)
    return out


def official_acres(path=None):
    """-> {ref: acres as a float}: the acreage bot's official sizes."""
    out = {}
    for ref, s in acres_rows(path).items():
        try:
            out[ref] = float(s['acres'])
        except (TypeError, ValueError):
            pass
    return out


def link_ids(path=None, usable_only=True):
    """-> {ref: link facts}. Usable only by default (own page, a known id kind, the id on no other park, the park's state)."""
    out = {}
    for ref, r in parks(path).items():
        lk = r.get('link') if isinstance(r, dict) else None
        if isinstance(lk, dict) and lk.get('id_value') and (lk.get('usable') or not usable_only):
            out[ref] = lk
    return out


def page_facts(path=None):
    """-> {ref: page facts} (the page reader's facts as kept in the one file)."""
    return {ref: r['page'] for ref, r in parks(path).items() if isinstance(r, dict) and isinstance(r.get('page'), dict)}


def acres_json_fallback(acres_path='data/acres.json', facts_path=None):
    """For the size readers: (path, rows) of data/acres.json when it exists, else the park facts sizes. rows = {ref: row}."""
    if acres_path and os.path.isfile(acres_path):
        return acres_path, None
    rows = acres_rows(facts_path)
    return (find(facts_path), rows) if rows else (None, {})


def selftest():
    bad = []

    def check(what, got, want):
        ok = got == want
        print(f'  {"ok  " if ok else "FAIL"} {what}' + ('' if ok else f': got {got!r}, wanted {want!r}'))
        if not ok:
            bad.append(what)
    with tempfile.TemporaryDirectory() as t:
        doc = {'made': '2026-11-20', 'parks': {
            'US-9001': {'area': 'US-ZZ', 'size': {'acres': 1200.5, 'agency': 'Invented Parks', 'read_date': '2026-11-02'},
                        'link': {'id_kind': 'nps code', 'id_value': 'invp', 'usable': True}, 'facts_from': ['size', 'link']},
            'US-9002': {'area': 'US-ZZ', 'link': {'id_kind': 'page number', 'id_value': '77', 'usable': False},
                        'page': {'read': '2026-11-20', 'sizes': []}, 'facts_from': ['link', 'page']},
            'US-9003': {'area': 'US-ZZ', 'size': {'acres': 'n/a'}, 'facts_from': ['size']}}}
        p = os.path.join(t, 'park-facts.json.gz')
        with gzip.open(p, 'wt', encoding='utf-8') as f:
            json.dump(doc, f)
        _CACHE.clear()
        os.environ['PARK_FACTS'] = p
        check('found through PARK_FACTS', find(), p)
        check('official sizes as numbers, a bad value left out', official_acres(), {'US-9001': 1200.5})
        check('rows in the acres.json shape', acres_rows()['US-9001']['agency'], 'Invented Parks')
        check('usable link ids only by default', sorted(link_ids()), ['US-9001'])
        check('every link id when asked', sorted(link_ids(usable_only=False)), ['US-9001', 'US-9002'])
        check('page facts', sorted(page_facts()), ['US-9002'])
        a = os.path.join(t, 'acres.json')
        check('no acres.json: the park facts sizes are used', acres_json_fallback(a)[0], p)
        open(a, 'w').write('{}')
        check('an acres.json that exists always wins', acres_json_fallback(a), (a, None))
        out = os.path.join(t, 'out', 'acres.json')
        check('the acres command writes the file', main(['acres', '--out', out]), 0)
        check('it holds the official sizes', sorted(json.load(open(out))), ['US-9001', 'US-9003'])
        check('it never writes over an acres.json', main(['acres', '--out', out]), 0)
        os.environ['PARK_FACTS'] = os.path.join(t, 'missing.json.gz')
        _CACHE.clear()
        cwd = os.getcwd(); os.chdir(t)
        try:
            os.remove('park-facts.json.gz')
            check('no file at all: empty, never an error', (load(), official_acres()), ({}, {}))
        finally:
            os.chdir(cwd)
        bad_p = os.path.join(t, 'broken.json.gz'); open(bad_p, 'wb').write(b'not gzip')
        _CACHE.clear()
        check('a broken file: empty, never an error', load(bad_p), {})
        os.environ.pop('PARK_FACTS', None)
    print('SELF-TEST PASSED' if not bad else f'SELF-TEST FAILED: {len(bad)}: ' + '; '.join(bad))
    return 0 if not bad else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--selftest' in argv:
        return selftest()
    cmd = argv[0] if argv else 'counts'
    if cmd == 'acres':
        out = argv[argv.index('--out') + 1] if '--out' in argv else 'data/acres.json'
        if os.path.exists(out):
            print(f'{out} already exists: left as it is')
            return 0
        rows = acres_rows()
        if not rows:
            print('::notice title=Park facts::no park facts file (or no official sizes in it): nothing written')
            return 0
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, separators=(',', ':'))
        print(f'::notice title=Park facts::{len(rows)} official sizes from {find()} written to {out}')
        return 0
    d = load()
    print(json.dumps({'file': find(), 'made': d.get('made'), 'parks': len(d.get('parks') or {}),
                      'official sizes': len(official_acres()), 'usable link ids': len(link_ids()), 'page facts': len(page_facts())}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
