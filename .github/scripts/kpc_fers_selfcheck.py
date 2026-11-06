#!/usr/bin/env python3
"""2-FER SELF-CHECK AFTER EVERY KEY BUILD (Nov 6 2026 improvements 5, Mapping; Brandon directly in Mapping's chat, 4:58 PM CST
Nov 5: "You write the code and I think super and quality would agree to it"). OFFLINE: the key files + this area's 2-fer files.

Runs in the 2-fer line's checker (KPC-Data kpc-fers-line.yml), which the existing chain starts after a new key build (KPC-Links
key build -> post-key check -> KPC-Data copy (B3) -> kpc-fers-chain.yml -> the line). For every LIVE area / same-land 2-fer row
(status candidate / very tight / water only) of the run's areas it re-reads each half's status IN THAT STATE / PROVINCE /
COUNTRY in the current key (kpc_fers_key_status.py, Part A 07: per-state, weakest across states when the half is not in that
area's key). When a half is a PIN or APPROXIMATE there, the row is HELD:
    status  -> 'not sure: 2-fer self-check: <reason>'   was -> the old status   held_by -> 'fers-selfcheck'   ('list' dropped)
exactly like the far-spot hold (kpc_fers_far_hold.py): holding never invents or deletes a 2-fer, a later line on a key with
official outlines builds the row again. River / trail rows on an official LINE are not area rows and are left alone.
Writes the hold list data/fers/fers-holds-<tag>.json (every run, also when nothing was held). auto stays false; nothing published.

  TAG=<run tag> STATES='US-KY US-TN CA-ON W-DE' python3 kpc_fers_selfcheck.py [fers dir (data/fers)] [key root (.)]
  --selftest   rule-18 style: 12+ frozen cases (temp folder)
Never fails the line: exit 0 (the selftest exits 1 on a failed case)."""
import datetime, gzip, json, os, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_fers_key_status as FKS  # noqa: E402

LIVE = ('candidate', 'very tight', 'water only')
BY = 'fers-selfcheck'


def key_area(tag):
    """2-fer file stem -> the key's area name: US-TN -> US-TN, CA-ON -> CA-ON, W-DE -> DE."""
    return tag[2:] if tag.startswith('W-') else tag


def hold_rows(spots, area):
    """Hold the live area rows with a pin / approximate half in this area. Returns the hold list rows."""
    held = []
    for s in spots:
        if not str(s.get('status', '')).startswith(LIVE) or s.get('kind') not in ('area', 'same land'): continue
        refs = list(s.get('refs') or [])
        why = FKS.key_line_match(refs, s.get('kind'), areas={r: area for r in refs})
        if not why: continue
        halves = {r: FKS.status_for(r, area) for r in refs}
        s['was'] = s['status']
        s['status'] = f"not sure: 2-fer self-check: {why} in {area} (held until both halves are official outlines in {area})"
        s['held_by'] = BY
        s.pop('list', None)
        held.append({'id': s.get('id'), 'refs': refs, 'kind': s.get('kind'), 'area': area, 'was': s['was'], 'why': why, 'halves': halves})
    return held


def _read(f):
    return json.load(gzip.open(f, 'rt', encoding='utf-8') if f.endswith('.gz') else open(f, encoding='utf-8'))


def _write(f, d):
    txt = json.dumps(d, indent=1, ensure_ascii=False)
    try:
        from kpc_save import canon
        txt = canon(d, 1)
    except Exception: pass  # noqa: BLE001
    if f.endswith('.gz'):
        with gzip.open(f, 'wt', encoding='utf-8') as fh: fh.write(txt)
    else: open(f, 'w', encoding='utf-8').write(txt if txt.endswith('\n') else txt + '\n')


def run(states, tag, fdir='data/fers', key_root='.'):
    FKS.clear(); FKS.load_key_status(key_root)
    out, per = [], {}
    for st in states:
        for f in (os.path.join(fdir, f'{st}.json'), os.path.join(fdir, f'{st}.json.gz')):
            if not os.path.exists(f): continue
            try: d = _read(f)
            except Exception as e: print(f'::warning title=2-fer self-check::{f} unreadable ({type(e).__name__})'); continue  # noqa: BLE001
            h = hold_rows(d.get('spots') or [], key_area(st))
            if h: _write(f, d)
            per[st] = len(h); out += h
    rep = {'tag': tag, 'checked': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'), 'areas': per,
           'held': len(out), 'rule': 'an area / same-land 2-fer is held when either half is a PIN or APPROXIMATE in that state / province / country of the current key',
           'by': BY, 'rows': out}
    os.makedirs(fdir, exist_ok=True)
    json.dump(rep, open(os.path.join(fdir, f'fers-holds-{tag}.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f"::notice title=2-fer self-check::{len(out)} live row(s) held ({per}); hold list {fdir}/fers-holds-{tag}.json", flush=True)
    return rep


def selftest():
    import tempfile
    ok, n = True, 0
    def check(name, got, want):
        nonlocal ok, n
        n += 1; good = got == want; ok &= good
        print(('PASS ' if good else 'FAIL ') + name + ('' if good else f'  got={got!r} want={want!r}'))
    td = pathlib.Path(tempfile.mkdtemp(prefix='kpc-fers-selfcheck-'))
    for d in ('data/us-key', 'data/ca-key', 'data/world-key', 'fers'): (td / d).mkdir(parents=True)
    O = lambda: {'g': 'official', 'm': [[1, 'X', 10, 'name']]}
    P = lambda: {'g': 'pin', 'm': []}
    A = lambda: {'g': 'approximate', 'm': [[1, 'X', 10, 'name approx']]}
    json.dump({'parks': {'US-0001': O(), 'US-0002': O(), 'US-0003': P(), 'US-0004': A(), 'US-0005': P()}}, open(td / 'data/us-key/US-AA.json', 'w'))
    json.dump({'parks': {'US-0005': O(), 'US-0001': O()}}, open(td / 'data/us-key/US-BB.json', 'w'))   # US-0005: pin in AA, official in BB
    json.dump({'parks': {'CA-0001': O(), 'CA-0002': P()}}, open(td / 'data/ca-key/CA-ON.json', 'w'))
    json.dump({'parks': {'DE-0001': O(), 'DE-0002': A()}}, open(td / 'data/world-key/DE.json', 'w'))
    S = lambda i, refs, kind='area', status='candidate': {'id': i, 'refs': refs, 'kind': kind, 'status': status, 'list': 'yes'}
    json.dump({'spots': [S('a', ['US-0001', 'US-0002']), S('b', ['US-0001', 'US-0003']), S('c', ['US-0001', 'US-0004']),
                         S('d', ['US-0001', 'US-0003'], 'river'), S('e', ['US-0001', 'US-0003'], status='dropped in pass 3'),
                         S('f', ['US-0001', 'US-0003'], 'same land', 'very tight: check'), S('g', ['US-0001', 'US-0005'])]}, open(td / 'fers/US-AA.json', 'w'))
    with gzip.open(td / 'fers/US-BB.json.gz', 'wt') as fh: json.dump({'spots': [S('h', ['US-0001', 'US-0005'])]}, fh)
    json.dump({'spots': [S('i', ['CA-0001', 'CA-0002']), S('j', ['CA-0001', 'CA-0001'])]}, open(td / 'fers/CA-ON.json', 'w'))
    json.dump({'spots': [S('k', ['DE-0001', 'DE-0002'])]}, open(td / 'fers/W-DE.json', 'w'))
    rep = run(['US-AA', 'US-BB', 'CA-ON', 'W-DE'], 'test', str(td / 'fers'), str(td))
    aa = {s['id']: s for s in json.load(open(td / 'fers/US-AA.json'))['spots']}
    held = {r['id'] for r in rep['rows']}
    check('two official halves: not held', 'a' in held, False)
    check('a PIN half: held, with the reason', ('b' in held, aa['b']['status'].startswith('not sure: 2-fer self-check: dropped: key PIN')), (True, True))
    check('an APPROXIMATE half: held as not sure', aa['c']['status'].startswith('not sure: 2-fer self-check: not sure: key outline is approximate'), True)
    check('the old status is kept in was, list dropped, held_by set', (aa['b']['was'], 'list' in aa['b'], aa['b']['held_by']), ('candidate', False, BY))
    check('a river row is left alone (official LINE, 100-ft rule)', aa['d']['status'], 'candidate')
    check('a row already dropped is left alone', aa['e']['status'], 'dropped in pass 3')
    check('a live same-land row is checked too', 'f' in held, True)
    check('IN THAT STATE: US-0005 is a pin in US-AA -> held there', 'g' in held, True)
    check('IN THAT STATE: US-0005 is official in US-BB -> not held there (gz file read)', 'h' in held, False)
    check('Canada: a pin half in CA-ON is held', ('i' in held, 'j' in held), (True, False))
    check('world: W-DE reads the DE key; an approximate half is held', 'k' in held, True)
    check('hold list written with every held row and per-area counts', (json.load(open(td / 'fers/fers-holds-test.json'))['held'], rep['areas']),
          (6, {'US-AA': 4, 'US-BB': 0, 'CA-ON': 1, 'W-DE': 1}))
    check('nothing deleted: every row is still in the file', len(aa), 7)
    print(f"SELFTEST {'PASS' if ok else 'FAIL'}: {n} cases")
    return ok


if __name__ == '__main__':
    if '--selftest' in sys.argv: sys.exit(0 if selftest() else 1)
    try:
        st = (os.environ.get('STATES') or '').split()
        run(st, re.sub(r'[^A-Za-z0-9._-]', '-', os.environ.get('TAG') or 'run'), *(sys.argv[1:3]))
    except Exception as e:  # noqa: BLE001
        print(f'::warning title=2-fer self-check::stopped ({type(e).__name__}: {str(e)[:200]}); the line is not affected')
    sys.exit(0)
