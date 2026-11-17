#!/usr/bin/env python3
"""D10 (owner ruling, 17 Nov 2026): a park on the tripwire not-sure list is NOT SURE for 2-fers; its outline stays on the map.
Offline, no network. KPC owner, 2026-11-17.
1 no list (none in kpcdata/, none in data/, no KPC_FERS_NOT_SURE) = no row changes, nothing counted
2 a listed park's shown rows of this run become 'not sure: tripwire <ref> <T..>'; other parks' rows are byte-identical
3 a row already not sure keeps its own reason; denials / merges stay as they are; rows reproduced from an older file stay exact
4 the list the tripwire bot writes (KPC-Data data/waiting/tripwires/not-sure.json) is read from the workflows' kpcdata/ checkout
5 an unreadable list holds nothing and warns (never red); no park's outline / key data is touched (the hold only edits rows)
6 both hold sites (pass 3 and pass 5) call it, beside the no-ownership hold
7 the fers rules hash moves once (b2d826ea5e3b -> the changelog's newest), scope entry 'none' waiting for the owner; US / CA / world unchanged"""
import copy, io, json, os, pathlib, sys, tempfile, types, contextlib
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.environ.setdefault('PASS', '3')
os.environ['HTTP_CACHE'] = ''
os.environ.pop('KPC_FERS_NOT_SURE', None)
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
_cwd = os.getcwd()
TD = pathlib.Path(tempfile.mkdtemp())
os.chdir(TD)
import kpc_fers as K
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def rows():
    return [{'refs': ['US-0001', 'US-0002'], 'kind': 'area', 'status': 'candidate', 'list': True},
            {'refs': ['US-0003', 'US-0004'], 'kind': 'area', 'status': 'approximate 2-fer', 'list': True},
            {'refs': ['US-0001', 'US-0005'], 'kind': 'river', 'status': 'not sure: no ownership source for this row'},
            {'refs': ['US-0001', 'US-0006'], 'kind': 'area', 'status': 'dropped: one park inside the other by 2 ft'},
            {'refs': ['US-0001', 'US-0007'], 'kind': 'area', 'status': 'merged into US-0001/US-0002'},
            {'refs': ['US-0001', 'US-0008'], 'kind': 'area', 'status': 'candidate', 'kept': True},
            {'refs': ['US-0009', 'US-0001'], 'kind': 'area', 'status': 'candidate', 'store_held': True}]


# the exact shape kpc_tripwires.py (KPC-Data) writes: compact codes per park, reasons spelled out once
LIST = {'about': 'parks the tripwires question (T1 / T2 / T4); not sure for 2-fers until a person clears them',
        'reasons': {'T1': 'one of its records is joined to another park too', 'T2': 'a piece of its land is cut off from its pin',
                    'T4': 'its pin is off its land and no person is behind the join'},
        'parks': {'US-0001': ['T4', 'T1'], 'US-9999': ['T2']}, 'cleared_left_out': 0}

try:
    # 1
    a = rows(); before = json.dumps(a, sort_keys=True)
    n = K.hold_tripwire(a)
    check(n == 0 and json.dumps(a, sort_keys=True) == before and K.tripwire_parks() == {}, '1 no list anywhere: 0 rows held, every row byte-identical')
    # 2 / 3
    a = rows(); ref = rows()
    n = K.hold_tripwire(a, listed={r: sorted(v) for r, v in LIST['parks'].items()})
    check(n == 1, f'2 one shown row of this run with the listed park is held ({n})')
    check(a[0]['status'] == 'not sure: tripwire US-0001 T1+T4 (a person clears it; its outline stays on the map)' and a[0]['tripwire'] == ['US-0001'] and 'list' not in a[0],
          f'2 its status reads not sure with the tripwires and says the outline stays ({a[0]["status"]!r})')
    check(a[0]['status'].startswith('not sure') and not K.denial(a[0]['status']), '2 not sure is a hold, not a denial (the pair is not dropped)')
    check(a[1] == ref[1], '2 a pair of two unlisted parks is byte-identical')
    check(a[2] == ref[2], '3 a row already not sure keeps its own reason')
    check(a[3] == ref[3] and a[4] == ref[4], '3 a denial and a merge are left as they are')
    check(a[5] == ref[5] and a[6] == ref[6], '3 rows reproduced from an older file (kept / store_held) stay exact copies')
    # 4 the list written by the tripwire bot, read from the kpcdata/ checkout the 2-fer workflows make
    p = TD / 'kpcdata/data/waiting/tripwires'; p.mkdir(parents=True)
    (p / 'not-sure.json').write_text(json.dumps(LIST, separators=(',', ':')), encoding='utf-8')
    check(K.TRIPWIRE_LISTS[0] == 'kpcdata/data/waiting/tripwires/not-sure.json', '4 the first place read is the kpcdata/ checkout of KPC-Data')
    K._TRIPWIRE.clear()
    got = K.tripwire_parks()
    check(got == {'US-0001': ['T1', 'T4'], 'US-9999': ['T2']}, f'4 the tripwire bot list is read ({got})')
    a = rows(); n = K.hold_tripwire(a)
    check(n == 1 and a[0]['status'].startswith('not sure: tripwire US-0001'), '4 with the list in place the hold uses it')
    for wf in ('kpc-fers.yml', 'kpc-fers-line.yml'):
        f = HERE.parent / 'KPC-Data/.github/workflows' / wf
        if f.is_file():
            check('path: kpcdata' in f.read_text(encoding='utf-8'), f'4 KPC-Data {wf} checks KPC-Data out at kpcdata/')
    os.environ['KPC_FERS_NOT_SURE'] = str(TD / 'other.json')
    (TD / 'other.json').write_text(json.dumps({'parks': {'US-0003': ['T2']}}), encoding='utf-8')
    K._TRIPWIRE.clear()
    check(K.tripwire_parks() == {'US-0003': ['T2']}, '4 KPC_FERS_NOT_SURE names another file')
    # 5
    (TD / 'other.json').write_text('{"parks": {"US-0003"', encoding='utf-8')
    K._TRIPWIRE.clear(); buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        a = rows(); n = K.hold_tripwire(a)
    check(n == 0 and a == rows() and '::warning' in buf.getvalue() and '::error' not in buf.getvalue(), '5 an unreadable list holds nothing and only warns')
    os.environ.pop('KPC_FERS_NOT_SURE')
    src = (S / 'kpc_fers.py').read_text(encoding='utf-8')
    body = src[src.index('def hold_tripwire'):src.index('SAME_RECORDS_HOLD = ')]
    check(not any(w in body for w in ('save_json', '.write', 'json.dump(', "['g']", "['m']", 'outlines/')),
          '5 the hold writes nothing and touches no outline; it only edits rows')
    # 6
    check(src.count('hold_tripwire(d.get(') == 2, '6 both hold sites call it (pass 3 and pass 5)')
    for site in ("n['candidates held: no ownership source'] = sum(hold_no_owner(", "counts['candidates held: no ownership source'] = counts.get("):
        i = src.index(site)
        check('hold_tripwire(' in src[i:i + 700], f'6 beside {site[:40]}...')
    check("if _tw:" in src, '6 no count line when nothing is held (no list = the report is as before)')
    # 7
    import kpc_key_freeze as KF, kpc_preflight as PF
    check(KF.rules_hash('fers') == PF.newest_hash('fers') != 'b2d826ea5e3b', f"7 fers rules hash {KF.rules_hash('fers')} = the changelog's newest (was b2d826ea5e3b)")
    sc = json.loads((HERE / '.github/fers-rule-scope.json').read_text(encoding='utf-8'))['changes']
    e = [x for x in sc if x['id'] == '2026-11-17-d10-tripwire-not-sure']
    check(len(e) == 1 and e[0]['scope'] == 'none' and e[0]['from'] == 'b2d826ea5e3b' and sc[-1] is e[0] and 'WAITING' in e[0].get('approved', ''),
          '7 one scope entry, scope none, from b2d826ea5e3b, waiting for the owner')
    top = (HERE / 'docs/key-rules-change.txt').read_text(encoding='utf-8').splitlines()
    check('fers rules b2d826ea5e3b -> ' + KF.rules_hash('fers') in top[0] and top[1].startswith('Why:'), '7 changelog top line names the move and has its Why line')
    check(tuple(KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')) == tuple(PF.newest_hash(k) for k in ('us-key', 'ca-key', 'world-key')),
          '7 US / CA / world rules hashes are what the changelog already says (do not move)')
finally:
    os.chdir(_cwd)
    import shutil; shutil.rmtree(TD, ignore_errors=True)
print('ALL PASS' if ok else 'FAILED')
sys.exit(0 if ok else 1)
