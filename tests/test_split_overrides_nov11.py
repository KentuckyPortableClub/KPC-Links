#!/usr/bin/env python3
"""KPC-Links #151 (Nov 11 2026), carried onto the Nov 12 stack with the readers fixed (KPC owner, 2026-11-12): data/us-key/overrides.json
is split into a manifest + part files, each under 1 MB, and kpc_overrides.load gives back exactly the single file's content.
Offline, no network (sockets refused below).

  python3 tests/test_split_overrides_nov11.py
"""
import hashlib, json, pathlib, shutil, socket, subprocess, sys, tempfile

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

# The single file on KPC-Links main 2cd7aa0 (unchanged since c06294e, so the same as #151 measured): 5,038 parks, 1,527,615 bytes.
SPLIT_SUBJECT = 'US overrides: split into a manifest + parts under 1 MB, every live reader and writer through kpc_overrides'
MAIN_PARKS, MAIN_PARKS_SHA, MAIN_BYTES = 5038, '0dc041b8dc76984b740edab31ca093cad6400c1704284f0e4002a7321c8ac93a', 1527615
MAIN_BLOCKED_SHA = '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945'  # canonical sha256 of [] (no blocked ids)

path = HERE / 'data/us-key/overrides.json'
doc = KO.load(path)
parks, blocked = doc.get('parks') or {}, doc.get('blocked_ids') or []
man = json.loads(path.read_text(encoding='utf-8'))
parts = man.get('parts') or []
check(path.stat().st_size < KO.CAP, f'the manifest is under 1 MB ({path.stat().st_size} bytes)')
check(len(parts) >= 2 and set(man.get('parts_sha256') or {}) == set(parts), f'parks are in {len(parts)} part files, each with its digest in the manifest')
check(parts == ['overrides-parks-01.json', 'overrides-parks-02.json'],
      'overrides.json lists overrides-parks-01.json and overrides-parks-02.json so the hash part is readable')
# the hasher merges the named parts (a missing name would be !unreadable and move every US area)
import kpc_area_hash as KAH
_obj, _ok = KAH.Tree(HERE, None).json('data/us-key/overrides.json')
check(_ok is True and isinstance(_obj, dict) and not _obj.get('parts') and len((_obj.get('parks') or {})) == len(parks),
      f'area-hash reads the listed override parts whole ({len((_obj or {}).get("parks") or {})} parks, ok={_ok})')
for name in parts:
    p = path.parent / name
    check(p.stat().st_size <= KO.CAP, f'{name} is under 1 MB ({p.stat().st_size} bytes)')
check(all(KO.has_no(v) for v in (man.get('parks') or {}).values()) and all(not KO.has_no(v) for n in parts for v in json.loads((path.parent / n).read_text(encoding='utf-8'))['parks'].values()),
      f"every park with a 'no' list is in the manifest ({len(man.get('parks') or {})}), none in a part")

# content equality with the single file, while the override files are still the split commit's (a later override edit is a real change)
last = subprocess.run(['git', 'log', '-1', '--format=%s', '--', 'data/us-key/overrides.json', 'data/us-key/overrides-parks-*.json'],
                      cwd=HERE, capture_output=True, text=True).stdout.strip()
canon = KO.canon_sha(parks)
dirty = subprocess.run(['git', 'status', '--porcelain', '--', 'data/us-key/'], cwd=HERE, capture_output=True, text=True).stdout.strip()
if not last or last.startswith(SPLIT_SUBJECT) or dirty:
    check(len(parks) == MAIN_PARKS and canon == MAIN_PARKS_SHA, f'loaded parks equal the single file on main: {len(parks)} parks, canonical sha256 {canon}')
    check(KO.canon_sha(blocked) == MAIN_BLOCKED_SHA, 'blocked_ids is unchanged (same canonical sha256)')
    r = subprocess.run(['git', 'show', '2cd7aa0:data/us-key/overrides.json'], cwd=HERE, capture_output=True)
    if r.returncode == 0:
        single = json.loads(r.stdout.decode('utf-8'))
        check(len(r.stdout) == MAIN_BYTES and single['parks'] == parks and all(single[k] == doc[k] for k in single if k not in ('parks', 'note')),
              f'the single file at main 2cd7aa0 ({len(r.stdout):,} bytes, over the cap) = the loaded document, park for park and every header but the note')
        sf = td0 = pathlib.Path(tempfile.mkdtemp()) / 'single.json'; sf.write_bytes(r.stdout)
        check(FG.override_no(sf) == FG.override_no(path), "kpc_fers_guard.override_no: the manifest gives the same no lists as the single file")
    else:
        print('SKIP the single file at 2cd7aa0 is not in this clone (shallow): the canonical sha256 above stands for it')
else:
    print(f'SKIP equality with the Nov 12 single file: the override files changed since the split ({last[:80]}); checked when the split landed')

# a single-file overrides.json (what tests write in a temp tree) still loads as itself, and a small document stays one file
td = pathlib.Path(tempfile.mkdtemp())
one = {'note': 'temp', 'blocked_ids': [], 'parks': {'US-1': {'join': ['1'], 'why': 't'}}}
(td / 'overrides.json').write_text(json.dumps(one))
check(KO.load(td / 'overrides.json') == one, 'a single-file overrides.json (no parts) loads as itself')
KO.save(td / 'overrides.json', one)
check(not list(td.glob('overrides-parks-*.json')) and json.loads((td / 'overrides.json').read_text())['parks'] == one['parks'],
      'a document under 1 MB is written as one file, no parts')

# deterministic: the repo's files are exactly what save() writes for the loaded document; twice = the same bytes
want = KO.layout(path, doc)
check(sorted(want) == sorted(['overrides.json'] + parts) and all((path.parent / n).read_bytes() == b for n, b in want.items()),
      "the repo's override files are byte for byte what kpc_overrides.save writes (kpc_overrides.py check)")
dest = td / 'real'; dest.mkdir()
for n in ['overrides.json'] + parts: shutil.copy(path.parent / n, dest / n)
KO.save(dest / 'overrides.json', KO.load(dest / 'overrides.json')); b1 = {f.name: f.read_bytes() for f in dest.iterdir()}
KO.save(dest / 'overrides.json', KO.load(dest / 'overrides.json')); b2 = {f.name: f.read_bytes() for f in dest.iterdir()}
check(b1 == b2 and b1 == {n: (path.parent / n).read_bytes() for n in b1}, 'running the splitter twice gives identical bytes')
fresh = td / 'fresh'; fresh.mkdir()
KO.save(fresh / 'overrides.json', doc); again = KO.load(fresh / 'overrides.json')
check(again['parks'] == parks and all((fresh / n).stat().st_size <= KO.CAP for n in again['parts']), 'a split from scratch reloads equal, parts under 1 MB')

# stable: a one-park edit rewrites one part (+ its digest line in the manifest); a new 'no' moves the park into the manifest
d = KO.load(dest / 'overrides.json'); r2 = next(iter(json.loads((dest / parts[-1]).read_text())['parks']))
d['parks'][r2] = dict(d['parks'][r2], why=str(d['parks'][r2].get('why') or '') + ' (test edit)')
KO.save(dest / 'overrides.json', d); b3 = {f.name: f.read_bytes() for f in dest.iterdir()}
check(sorted(n for n in b3 if b3[n] != b2.get(n)) == sorted([parts[-1], 'overrides.json'])
      and sum(1 for x, y in zip(b2['overrides.json'].splitlines(), b3['overrides.json'].splitlines()) if x != y) == 1,
      f'a one-park edit ({r2}) rewrites only {parts[-1]} and one digest line of the manifest')

# the 2-fer reader (kpc_fers_guard.override_no, a 2-fer rule file, NOT edited) sees every 'no' from the manifest alone
nos = FG.override_no(path)
walk = {r: ({str(x) for x in (v or {}).get('no') or [] if x is not None}, {str(x).strip().lower() for x in (v or {}).get('no') or [] if x is not None})
        for r, v in parks.items() if KO.has_no(v)}
check(nos == walk and len(nos) > 500, f'kpc_fers_guard.override_no on the manifest = every no list of the whole set ({len(nos)} parks)')

# hashes: US moved once (kpc_us_key.py reads through kpc_overrides); CA, world and 2-fers did not
us, ca, world, fers = (KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers'))
check((us, ca, world, fers) == tuple(PF.newest_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers')),
      f'every rules hash is the newest in docs/key-rules-change.txt ({us}, {ca}, {world}, {fers})')
check(not any(f.endswith(('kpc_overrides.py', 'kpc_precheck_whole.py')) for fs in KF.RULE_FILES.values() for f in fs)
      and {'kpc_overrides.py', 'kpc_precheck_whole.py'} <= KF.NOT_RULES, 'kpc_overrides.py / kpc_precheck_whole.py are not rule files')

print('ALL PASS' if not bad else f'{bad} FAILED - SOME FAILED')
sys.exit(1 if bad else 0)
