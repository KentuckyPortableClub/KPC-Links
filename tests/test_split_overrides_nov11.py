#!/usr/bin/env python3
"""Nov 11 2026 (KPC owner): data/us-key/overrides.json is split into part files under 1 MB; kpc_overrides.load returns
parks identical to the single file that was on main (sha256 below). Offline, no network. The US and 2-fer rules hashes
move because the readers in kpc_us_key.py and kpc_fers_guard.py changed; CA and world do not.

  python3 tests/test_split_overrides_nov11.py
"""
import hashlib, json, pathlib, socket, sys, tempfile

def _no_net(*a, **k): raise RuntimeError('network refused in this test')
socket.socket.connect = _no_net; socket.create_connection = _no_net; socket.getaddrinfo = _no_net

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_overrides as KO  # noqa: E402
import kpc_key_freeze as KF  # noqa: E402
import kpc_fers_guard as FG  # noqa: E402
import kpc_preflight as PF  # noqa: E402

bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)

def canon(o):
    return json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

# sha256 of the parks object (canonical JSON) in data/us-key/overrides.json on origin/main (11f908d9), 5,038 parks.
MAIN_PARKS_SHA = '0dc041b8dc76984b740edab31ca093cad6400c1704284f0e4002a7321c8ac93a'
MAIN_BLOCKED_SHA = '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945'  # empty list

path = HERE / 'data/us-key/overrides.json'
doc = KO.load(path)
parks, blocked = doc.get('parks') or {}, doc.get('blocked_ids') or []
check(path.stat().st_size < KO.CAP, f'the manifest is under 1 MB ({path.stat().st_size} bytes)')
parts = doc.get('parts') or []
check(len(parts) >= 2, f'parks are in {len(parts)} part files')
sizes = []
for name in parts:
    p = path.parent / name
    sizes.append((name, p.stat().st_size))
    check(p.stat().st_size <= KO.CAP, f'{name} is under 1 MB ({p.stat().st_size} bytes)')
    check(p.stat().st_size > 0 and 'parks' in json.loads(p.read_text(encoding='utf-8')), f'{name} is a parks object')
check(len(parks) == 5038, f'loaded parks has every row ({len(parks)})')
check(hashlib.sha256(canon(parks).encode('utf-8')).hexdigest() == MAIN_PARKS_SHA,
      'loaded parks are byte-identical (canonical sha256) to the single file on main')
check(hashlib.sha256(canon(blocked).encode('utf-8')).hexdigest() == MAIN_BLOCKED_SHA,
      'blocked_ids is unchanged (still empty, same canonical sha256)')

# a single-file overrides.json (what tests write in a temp tree) still loads as itself
td = pathlib.Path(tempfile.mkdtemp())
one = {'note': 'temp', 'blocked_ids': [], 'parks': {'US-1': {'join': ['1'], 'why': 't'}}}
(td / 'overrides.json').write_text(json.dumps(one))
got = KO.load(td / 'overrides.json')
check(got == one, 'a single-file overrides.json (no parts) loads as itself')

# save of that small file stays one file; save of the real parks stays split and reloads equal
KO.save(td / 'overrides.json', one)
check(not list(td.glob('overrides-parks-*.json')) and json.loads((td / 'overrides.json').read_text())['parks'] == one['parks'],
      'a document under 1 MB is written as one file, no parts')
# round-trip the real document through a temp dir
dest = td / 'real' ; dest.mkdir()
KO.save(dest / 'overrides.json', {'note': doc.get('note'), 'blocked_ids': blocked, 'blocked_ids_about': doc.get('blocked_ids_about'), 'parks': parks})
again = KO.load(dest / 'overrides.json')
check(again['parks'] == parks and hashlib.sha256(canon(again['parks']).encode()).hexdigest() == MAIN_PARKS_SHA,
      'save + load of the real parks is equal (same canonical sha256)')
check(all((dest / n).stat().st_size <= KO.CAP for n in (again.get('parts') or [])), 'rewritten parts stay under 1 MB')

# readers used by the US key and the 2-fer bot
# import of kpc_us_key is heavy; the load line is checked by test_blocked_ids. Here: override_no sees every 'no'.
nos = FG.override_no(path)
# compare to a direct walk of loaded parks
walk = {r: ({str(x) for x in (v or {}).get('no') or [] if x is not None},
            {str(x).strip().lower() for x in (v or {}).get('no') or [] if x is not None})
        for r, v in parks.items() if (v or {}).get('no')}
check(nos == walk, f'kpc_fers_guard.override_no returns the same no-lists as a walk of the loaded parks ({len(nos)} parks)')

# hashes: US and fers moved (readers + scope); CA and world did not
us, ca, world, fers = (KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers'))
check((ca, world) == ('4b4176190334', '9358c2ede2d5'), f'CA and world rules hashes unchanged ({ca}, {world})')
check(us == PF.newest_hash('us-key') == '5d8b9b5ab648', f'US rules hash is the changelog newest ({us})')
check(fers == PF.newest_hash('fers') == 'b49c1ba6f9db', f'fers rules hash is the changelog newest ({fers})')
check('kpc_overrides.py' in KF.NOT_RULES, 'kpc_overrides.py is on the not-a-rule list')

print('ALL PASS' if not bad else f'{bad} FAILED')
sys.exit(1 if bad else 0)
