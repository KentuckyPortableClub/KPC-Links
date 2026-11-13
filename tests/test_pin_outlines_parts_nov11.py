#!/usr/bin/env python3
"""KPC owner, 2026-11-11 (job 2): (A) a park the US key grades pin has no outline: kpc_master.save_area leaves it out, so every writer
and reader agrees; the repo's outline files are clean. (B) an area over 1 MB is saved in parts with the release's own part scheme
(US-AK.geojson.gz + US-AK.p2.geojson.gz ...), every tool reads every part, and the pages' KPCREL block puts the parts together on the
working-copy path and the released path alike."""
import gzip, json, os, pathlib, random, shutil, subprocess, sys, tempfile, types
import os as _os; _os.environ.setdefault('GITHUB_TRIGGERING_ACTOR', 'KentuckyPortableClub')   # kpc_release.py checks the release login (regrade 3 LC)
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M
import kpc_release as R
import kpc_outlines_keep_main as K

ok = True
def check(name, cond, why=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + ('' if cond or not why else f'  [{str(why)[:600]}]'))
    ok = ok and bool(cond)

def sh(d, *a): return subprocess.run(a, cwd=d, capture_output=True, text=True)
def git_repo(d):
    sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
def commit(d, m='c'): sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', m); return sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip()

SQ = lambda x=0: {'type': 'Polygon', 'coordinates': [[[x, 0], [x, 1], [x + 1, 1], [x + 1, 0], [x, 0]]]}
def rec(ref, g='official', geom=None, layer='file:US-ZZ.json.gz', ids=None):
    return M.make_record(ref, ref, g, geom or SQ(), 'agency', layer, ids or ['1'], 10, '2026-11-11', '', 'key')
rnd = random.Random(7)
def island(cx, cy, n, r=0.05):
    import math
    pts = [[round(cx + (r + rnd.uniform(-0.002, 0.002)) * math.cos(2 * math.pi * i / n), 5), round(cy + (r + rnd.uniform(-0.002, 0.002)) * math.sin(2 * math.pi * i / n), 5)] for i in range(n)]
    return [pts + [pts[0]]]
def big_multi(n_islands, n_pts, x0=-160.0):
    return {'type': 'MultiPolygon', 'coordinates': [island(x0 + 0.2 * i, 60.0, n_pts) for i in range(n_islands)]}
def keyfile(d, st, parks): (d / f'US-{st}.json').parent.mkdir(parents=True, exist_ok=True); (d / f'US-{st}.json').write_text(json.dumps({'parks': parks}))

# ================================================================ A. pin-graded parks have no outline
# A1. the repo: no outline file holds a park the key grades pin (the same rule save_area keeps); US-0657 and others named
key_dir = ROOT / 'data/us-key'; grades = M._key_grades(key_dir); found = {}
for p in sorted((ROOT / 'data/outlines').glob('US-??.geojson.gz')):
    area = p.name[:5]; recs = M.load_area(area)
    for r in M.pin_drops(area, recs, key_dir): found.setdefault(area, []).append(r)
check(f'the repo outline files hold no park the key grades pin (found: {found or "none"})', not found)
for area, ref in (('US-DC', 'US-0657'), ('US-AK', 'US-7208'), ('US-AK', 'US-7209'), ('US-MI', 'US-4774'), ('US-MS', 'US-7124'), ('US-WI', 'US-4262')):
    check(f'{ref} ({area}): graded pin by the key and not in {area}\'s outline file',
          grades.get(ref, {}).get(area) == 'pin' and ref not in M.load_area(area))
check('US-4514 (pin in TX and OK, official in NM) keeps its NM outline', grades['US-4514'].get('US-NM') == 'official' and 'US-4514' in M.load_area('US-NM'))
rc = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_master_cli.py'), 'resave', '--dry-run'], capture_output=True, text=True)
check('a dry-run resave of the repo drops nothing more (0 pin-graded outlines left)', rc.returncode == 0 and '0 outline(s) of parks the key grades pin would be dropped' in rc.stdout)

with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); root = d / 'data/outlines'; kd = d / 'data/us-key'; root.mkdir(parents=True)
    keyfile(kd, 'TX', {'US-4514': {'g': 'pin'}, 'US-1': {'g': 'pin'}, 'US-2': {'g': 'official'}, 'US-5': {'g': 'pin'}})
    keyfile(kd, 'NM', {'US-4514': {'g': 'official'}, 'US-5': {'g': 'pin'}})
    keyfile(kd, 'DC', {'US-0657': {'g': 'pin'}, 'US-0658': {'g': 'official'}})
    M.save_area('US-TX', {r: rec(r) for r in ('US-4514', 'US-1', 'US-2', 'US-3', 'US-5')}, root)
    check('save_area: a pin-graded park is left out; one official in another state\'s key (US-4514) stays; one the key does not know is dropped',
          sorted(M.load_area('US-TX', root)) == ['US-2', 'US-4514'])
    check('save_area: pin in every key that knows it (US-5, two states) = dropped', 'US-5' not in M.load_area('US-TX', root))
    M.save_area('US-OK', {'US-1': rec('US-1')}, root)
    check('save_area: no key file for the state = nothing dropped', sorted(M.load_area('US-OK', root)) == ['US-1'])
    M.save_area('US-TX', {'US-1': rec('US-1')}, root, key_dir=d / 'nowhere')
    check('save_area: no key folder = nothing dropped (as before)', sorted(M.load_area('US-TX', root)) == ['US-1'])
    # A2. keep_main never brings a dropped pin outline back from main's copy; DC is small and the drop guard does not trip
    git_repo(d)
    dc = {f'US-06{i:02d}': rec(f'US-06{i:02d}') for i in range(50, 60)}
    def dckey(pin=False, extra=None):
        parks = {f'US-06{i:02d}': {'g': 'official'} for i in range(50, 60)}
        if pin: parks['US-0657'] = {'g': 'pin'}
        if extra: parks.update(extra)
        return parks
    (kd / 'US-DC.json').write_text(json.dumps({'parks': dckey(False, {'US-0659': {'g': 'official'}})}))
    # AL lists the same parks (so M2 does not drop them); 0659 will become pin-only on AL later
    keyfile(kd, 'AL', {r: {'g': 'official'} for r in dc})
    M.save_area('US-DC', dc, root); M.save_area('US-AL', dc, root); commit(d, 'main: US-0657 official')
    keyfile(kd, 'DC', dckey(True, {'US-0659': {'g': 'official'}}))          # this run's key: US-0657 is pin now
    M.save_area('US-DC', dc, root); (root / 'US-AL.geojson.gz').unlink()
    # 0659 is pin in AL and not listed by DC, so it is dropped from AL; 0657 is pin in DC only
    keyfile(kd, 'DC', dckey(True))   # 0659 no longer in DC
    keyfile(kd, 'AL', dict({r: {'g': 'official'} for r in dc if r not in ('US-0657', 'US-0659')}, **{'US-0659': {'g': 'pin'}}))
    M.save_area('US-DC', dc, root)   # 0657 is pin in the only key that lists it (DC); AL no longer lists it official
    check('this run\'s save drops US-0657', 'US-0657' not in M.load_area('US-DC', root) and len(M.load_area('US-DC', root)) == 9)
    rc = K.run(d, root, 'HEAD')
    check('keep_main: US-0657 is not brought back from main\'s copy, nothing else lost', rc == 0 and sorted(M.load_area('US-DC', root)) == sorted(set(dc) - {'US-0657'}))
    check('keep_main: a file the run lost is put back from main without the pin-graded park (US-0657 is pin in every key that lists it; US-0659 stays, official in DC)',
          rc == 0 and sorted(M.load_area('US-AL', root)) == sorted(set(dc) - {'US-0657'}))
    sh(d, 'git', 'add', 'data/us-key'); sh(d, 'git', 'commit', '-qm', 'key')
    g = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_key_drop_guard.py'), '--repo', str(d), '--ref', 'HEAD'], capture_output=True, text=True,
                       env=dict(os.environ, KPC_DROP_PCT='3', KPC_DROP_MIN='0'))
    check('drop guard: a pin clean-up is not a drop (DC 10 -> 9 with the strictest minimum)', g.returncode == 0 and 'Drop guard US-DC' not in g.stdout)
    M.save_area('US-DC', {r: v for r, v in dc.items() if r not in ('US-0657', 'US-0658')}, root)
    g = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_key_drop_guard.py'), '--repo', str(d), '--ref', 'HEAD'], capture_output=True, text=True,
                       env=dict(os.environ, KPC_DROP_PCT='3', KPC_DROP_MIN='0'))
    check('drop guard: losing a park that is NOT pin still counts', g.returncode == 1 and 'US-DC::outlines 9 -> 8' in g.stdout)

# ================================================================ A'. the key's approximate grade: a record is lowered, never raised
for area, ref in (('US-AK', 'US-7239'), ('US-AK', 'US-12678'), ('US-IN', 'US-4162')):
    r_ = M.load_area(area).get(ref) or {}
    check(f'{ref} ({area}): the key grades it approximate and its outline record says approximate (hash recomputed)',
          grades.get(ref, {}).get(area) == 'approximate' and r_.get('g') == 'approximate' and r_.get('hash') == M.content_hash(r_))
check('US-0015 (pin in DC, official in MD / WV): its MD and WV records stay official', M.load_area('US-MD')['US-0015']['g'] == 'official' and M.load_area('US-WV')['US-0015']['g'] == 'official')
check('US-4514 (pin in TX / OK, official in NM): its NM record stays official', M.load_area('US-NM')['US-4514']['g'] == 'official')
left = {p.name[:5]: sorted(M.grade_lowers(p.name[:5], M.load_area(p.name[:5]), key_dir)) for p in sorted((ROOT / 'data/outlines').glob('US-??.geojson.gz'))}
check('no repo outline record is graded higher than the key allows', not any(left.values()), {k: v for k, v in left.items() if v})
# a record in a NEIGHBOUR's file, for a park that state's key does not list: judged by every US key that lists the park
for area, ref in (('US-MT', 'US-11281'), ('US-MT', 'US-13296'), ('US-OR', 'US-12210')):
    check(f'{ref}: pin in every key that lists it ({grades.get(ref)}): no outline in the {area} file either', area not in grades.get(ref, {}) and ref not in M.load_area(area))
for area, ref in (('US-CO', 'US-4553'), ('US-TX', 'US-4553'), ('US-MT', 'US-7816'), ('US-TX', 'US-7563')):
    r_ = M.load_area(area).get(ref) or {}
    check(f'{ref} in the {area} file (its key does not list it; best grade anywhere approximate): saved approximate',
          area not in grades.get(ref, {}) and r_.get('g') == 'approximate' and r_.get('hash') == M.content_hash(r_))
r_ = M.load_area('US-TN').get('US-1278') or {}
check('US-1278 (listed by no US key): not in the TN outline file', 'US-1278' not in grades and 'US-1278' not in M.load_area('US-TN'))
nokey = [(p.name[:5], r) for p in sorted((ROOT / 'data/outlines').glob('US-??.geojson.gz')) for r in M.load_area(p.name[:5]) if r not in grades]
check(f'no outline record whose park no US key lists ({nokey})', nokey == [])
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); root = d / 'data/outlines'; kd = d / 'data/us-key'; root.mkdir(parents=True)
    keyfile(kd, 'CO', {'US-0': {'g': 'official'}}); keyfile(kd, 'NM', {'US-1': {'g': 'approximate'}, 'US-2': {'g': 'pin'}, 'US-3': {'g': 'official'}})
    M.save_area('US-CO', {r: rec(r) for r in ('US-0', 'US-1', 'US-2', 'US-3', 'US-9')}, root); got = M.load_area('US-CO', root)
    check('neighbour file: a pin park out, an approximate park approximate, an official park kept; a park in no key is dropped',
          sorted(got) == ['US-0', 'US-1', 'US-3'] and got['US-1']['g'] == 'approximate' and got['US-3']['g'] == 'official')
lay = (ROOT / 'kpc-padus-layer.js').read_text(encoding='utf-8')
check('the map layer draws a record whose g is not official dashed (so these 87 are dashed now)',
      "if (g && g !== 'official') return { color: '#c47a12', weight: W, opacity: 0.9, fill: false, dashArray: '6 6'" in lay)
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); root = d / 'data/outlines'; kd = d / 'data/us-key'; root.mkdir(parents=True)
    keyfile(kd, 'TX', {'US-1': {'g': 'approximate'}, 'US-2': {'g': 'approximate'}, 'US-3': {'g': 'approximate'}, 'US-4': {'g': 'official'}})
    keyfile(kd, 'NM', {'US-2': {'g': 'official'}})
    base = {'US-1': rec('US-1'), 'US-2': rec('US-2'), 'US-3': rec('US-3', 'point-circle'), 'US-4': rec('US-4', 'approximate')}
    M.save_area('US-TX', base, root); got = M.load_area('US-TX', root)
    check('save_area: official -> approximate when that is the best grade any key gives; everything but g and hash unchanged',
          got['US-1']['g'] == 'approximate' and got['US-1']['hash'] == M.content_hash(got['US-1'])
          and {k: v for k, v in got['US-1'].items() if k not in ('g', 'hash')} == {k: v for k, v in base['US-1'].items() if k not in ('g', 'hash')})
    check('save_area: a park official in another state\'s key stays official; a lower record is never raised',
          got['US-2']['g'] == 'official' and got['US-3']['g'] == 'point-circle' and got['US-4']['g'] == 'approximate')
    M.save_area('US-TX', got, root)
    check('a second save: still approximate', M.load_area('US-TX', root)['US-1']['g'] == 'approximate')
    kept, what = M.merge(M.load_area('US-TX', root)['US-1'], rec('US-1', layer='https://x.gov/0'))   # a later trim reads the official layer again
    have = M.load_area('US-TX', root); have['US-1'] = kept; M.save_area('US-TX', have, root)
    check('a later trim merge (official replaces approximate) is saved approximate again', what.startswith('replaced') and M.load_area('US-TX', root)['US-1']['g'] == 'approximate')
    git_repo(d); commit(d, 'x')
    run_recs = M.load_area('US-TX', root)
    (root / 'US-TX.geojson.gz').unlink(); M.save_area('US-TX', base, root, key_dir=d / 'none'); commit(d, 'main has the old official copy')
    M.save_area('US-TX', run_recs, root)
    rc = K.run(d, root, 'HEAD')
    check('keep_main with main\'s old official copy: still approximate, nothing lost', rc == 0 and M.load_area('US-TX', root)['US-1']['g'] == 'approximate'
          and sorted(M.load_area('US-TX', root)) == sorted(base))
    rc = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_master_cli.py'), 'check', '--root', str(root)], capture_output=True, text=True)
    g = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_key_drop_guard.py'), '--repo', str(d), '--ref', 'HEAD'], capture_output=True, text=True,
                       env=dict(os.environ, KPC_DROP_MIN='0'))
    check('the master check passes and the drop guard sees no loss', rc.returncode == 0 and 'all clear' in rc.stdout and g.returncode == 0)

# ================================================================ FIX 1: the same content in other bytes is never rewritten (CI's zlib vs this one)
def hdr(b):
    i = 10; name = b''
    if b[3] & 8: j = b.index(b'\0', 10); name = b[10:j]
    return b[3], int.from_bytes(b[4:8], 'little'), b[8], b[9], name
for p in sorted((ROOT / 'data/outlines').glob('US-??.geojson.gz')):
    h = hdr(p.read_bytes())
    if h != (8, 0, 2, 255, p.name[:-3].encode()): check(f'{p.name}: fixed gzip header', False, h); break
else: check('every outline file has the fixed gzip header (mtime 0, XFL 2, OS 255, its own name): the same zlib gives the same file', True)
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); root = d / 'data/outlines'; kd = d / 'data/us-key'; root.mkdir(parents=True); git_repo(d)
    keyfile(kd, 'AK', {'US-7000': {'g': 'official', 'm': [['sgaka1', 'x', 1, 'name']]}, 'US-7001': {'g': 'approximate'}, 'US-7002': {'g': 'pin'}})
    M.save_area('US-AK', {r: rec(r) for r in ('US-7000', 'US-7001')}, root)
    M.save_area('US-DC', {'US-0001': rec('US-0001')}, root)
    def other_zlib(f):   # the same content, packed at another level (other bytes), as another zlib build would
        raw = gzip.decompress(f.read_bytes()); b = gzip.compress(raw, compresslevel=1, mtime=0); assert b != f.read_bytes(); f.write_bytes(b); return b
    ci = {n: other_zlib(root / n) for n in ('US-AK.geojson.gz', 'US-DC.geojson.gz')}
    commit(d, 'files as CI wrote them')
    def clean(): return sh(d, 'git', 'status', '--porcelain', '--', ':(glob)data/outlines/US-*.geojson.gz').stdout.strip() == '' and all((root / n).read_bytes() == b for n, b in ci.items())
    M.save_area('US-AK', M.load_area('US-AK', root), root)
    check('save_area with the same content: the file is not rewritten, git sees no change', clean())
    subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_master_cli.py'), 'resave', '--root', str(root)], capture_output=True)
    check('resave: not rewritten', clean())
    subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_master_cli.py'), 'check', '--root', str(root)], capture_output=True)
    check('check: not rewritten', clean())
    other = d / 'other'; shutil.copytree(root, other); M.save_area('US-AK', M.load_area('US-AK', other), other, key_dir=d / 'none', cap=10 ** 9)
    (other / 'US-AK.geojson.gz').write_bytes(M._gz_named(gzip.decompress(ci['US-AK.geojson.gz']), 'US-AK.geojson.gz'))   # a build part packed by this zlib
    import kpc_master_fill as F
    F.part(types.SimpleNamespace(root=str(other), base=str(other), states='AK', out=str(d / 'pt')))
    check('part copies a build part\'s file (other bytes, same content as main)', (d / 'pt/US-AK.geojson.gz').read_bytes() != ci['US-AK.geojson.gz'])
    F.collect(types.SimpleNamespace(parts=[str(d / 'pt')], root=str(root), us_key=str(kd), needs_out=None, needs_in=None))
    check('collect: a part with the same content does not rewrite the file', clean())
    cache = d / 'cache'; cache.mkdir()
    with gzip.open(cache / 'US-AK.json.gz', 'wt') as f: json.dump({'recs': []}, f)
    subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_outlines_from_key.py'), '--cache', str(cache), '--states', 'AK', '--root', str(root), '--key', str(kd)], capture_output=True)
    check('kpc_outlines_from_key with nothing new: not rewritten', clean())
    check('keep_main on an unchanged tree: not rewritten', K.run(d, root, 'HEAD') == 0 and clean())
    (root / 'US-DC.geojson.gz').write_bytes(M._gz_named(gzip.decompress(ci['US-DC.geojson.gz']), 'US-DC.geojson.gz'))   # a tool that rewrote it anyway
    check('(a file rewritten with the same content shows in git: bytes)', not clean())
    check('keep_main (the save\'s redo) puts main\'s own bytes back: git sees no change', K.run(d, root, 'HEAD') == 0 and clean())
    sha = commit(d, 'same'); R.release(d, 'US', sha); rf = d / 'data/released/outlines/US-AK.geojson.gz'
    rf.write_bytes(gzip.compress(gzip.decompress(rf.read_bytes()), compresslevel=3, mtime=0)); before = rf.read_bytes()
    R.release(d, 'US', sha); idx = json.loads((d / 'data/released/RELEASED.json').read_text())
    check('release: a released file with the same content is not rewritten and keeps its version',
          rf.read_bytes() == before and idx['files']['outlines/US-AK.geojson.gz'][0][1] == __import__('hashlib').sha256(before).hexdigest()[:12])
    # a real change IS written (the new park is in the key, or M2 would drop it)
    keyfile(kd, 'AK', {'US-7000': {'g': 'official', 'm': [['sgaka1', 'x', 1, 'name']]}, 'US-7001': {'g': 'approximate'}, 'US-7002': {'g': 'pin'}, 'US-7009': {'g': 'official'}})
    have = M.load_area('US-AK', root); have['US-7009'] = rec('US-7009'); M.save_area('US-AK', have, root)
    check('a real content change IS written (git sees it)', 'US-7009' in M.load_area('US-AK', root) and 'data/outlines/US-AK.geojson.gz' in sh(d, 'git', 'status', '--porcelain', '--', 'data/outlines').stdout)
    check('... and keep_main keeps it', K.run(d, root, 'HEAD') == 0 and 'US-7009' in M.load_area('US-AK', root) and (root / 'US-AK.geojson.gz').read_bytes() != ci['US-AK.geojson.gz'])

# ================================================================ B. parts
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); root = d / 'data/outlines'; kd = d / 'data/us-key'; root.mkdir(parents=True)
    small = {f'US-7{i:03d}': rec(f'US-7{i:03d}', geom=SQ(i)) for i in range(30)}
    mid_names = {f'US-8{i:03d}': {'g': 'official'} for i in range(25)}
    keyfile(kd, 'AK', dict({'US-0156': {'g': 'official'}, 'US-0999': {'g': 'pin'}},
                           **{r: {'g': 'official'} for r in small}, **mid_names))
    M.save_area('US-AK', small, root); one = (root / 'US-AK.geojson.gz').read_bytes()
    check('an area under 1 MB stays one file with no part fields', M.area_files('US-AK', root) == [root / 'US-AK.geojson.gz'] and 'kpc_part' not in json.loads(gzip.decompress(one)))
    huge = rec('US-0156', geom=big_multi(100, 4000))                                     # one park far over 1 MB on its own
    mid = {f'US-8{i:03d}': rec(f'US-8{i:03d}', geom=big_multi(2, 1500, -150.0 + i)) for i in range(25)}
    allr = dict(small, **mid, **{'US-0156': huge, 'US-0999': rec('US-0999')})
    M.save_area('US-AK', allr, root)
    files = M.area_files('US-AK', root); sizes = [f.stat().st_size for f in files]
    check(f'a synthetic Alaska over 1 MB is written in parts, each under 1 MB ({len(files)} files: {", ".join(f"{f.name} {s:,}" for f, s in zip(files, sizes))})',
          len(files) >= 3 and all(s <= 1_000_000 for s in sizes) and sum(sizes) > 1_000_000
          and [f.name for f in files] == ['US-AK.geojson.gz'] + [f'US-AK.p{i}.geojson.gz' for i in range(2, len(files) + 1)])
    docs = [json.loads(gzip.decompress(f.read_bytes())) for f in files]
    check('every part says [i, N, tag] with one tag', [x['kpc_part'][:2] for x in docs] == [[i, len(files)] for i in range(1, len(files) + 1)] and len({x['kpc_part'][2] for x in docs}) == 1)
    check('the park too big for one part is in pieces (kpc_piece), the others whole', sum(1 for x in docs for f in x['features'] if f.get('kpc_piece')) > 1
          and all(f['properties']['ref'] == 'US-0156' for x in docs for f in x['features'] if f.get('kpc_piece')))
    back = M.load_area('US-AK', root)
    check('load_area reads every part: the same records, every hash right, the pin-graded park left out',
          sorted(back) == sorted(set(allr) - {'US-0999'}) and all(M.content_hash(v) == v['hash'] == allr[r]['hash'] for r, v in back.items()))
    before = [f.read_bytes() for f in files]; M.save_area('US-AK', back, root)
    check('saving the same records again writes the same files (deterministic)', [f.read_bytes() for f in M.area_files('US-AK', root)] == before)
    rc = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_master_cli.py'), 'check', '--root', str(root)], capture_output=True, text=True)
    check('master check reads an area in parts (part files are not areas of their own)', rc.returncode == 0 and 'all clear' in rc.stdout)
    # parts of two saves never go together
    p2 = (root / 'US-AK.p2.geojson.gz').read_bytes(); x = json.loads(gzip.decompress(p2)); x['kpc_part'][2] = 'other'
    (root / 'US-AK.p2.geojson.gz').write_bytes(gzip.compress(json.dumps(x).encode()))
    try: M.load_area('US-AK', root); mixed = False
    except M.MasterError: mixed = True
    check('a part of another save (other tag): load_area refuses (never half an area)', mixed)
    (root / 'US-AK.p2.geojson.gz').write_bytes(p2); (root / 'US-AK.p3.geojson.gz').rename(root / 'gone')
    try: M.load_area('US-AK', root); miss = False
    except M.MasterError: miss = True
    check('a missing part: load_area refuses', miss); (root / 'gone').rename(root / 'US-AK.p3.geojson.gz')
    # the part step / collect carry every part; keep_main and the drop guard read them
    out = d / 'part'
    import kpc_master_fill as F
    F.part(types.SimpleNamespace(root=str(root), base=str(root), states='AK', out=str(out)))
    check('the part step copies every part of its state', sorted(p.name for p in out.glob('US-AK*')) == sorted(f.name for f in files))
    git_repo(d); commit(d, 'main has AK in parts')
    M.save_area('US-AK', small, root)
    check('an area that fits again is one file; old parts are removed here (part 1 says N anyway)', M.area_files('US-AK', root) == [root / 'US-AK.geojson.gz'] and not list(root.glob('US-AK.p*')))
    (root / 'US-AK.p2.geojson.gz').write_bytes(p2)                                        # a stale part the save did not delete
    check('a stale part file is not read: part 1 decides', sorted(M.load_area('US-AK', root)) == sorted(small))
    rc = K.run(d, root, 'HEAD'); got = M.load_area('US-AK', root)
    check('keep_main: main in parts, this run smaller: every outline main had is kept and saved in parts again',
          rc == 0 and sorted(got) == sorted(back) and len(M.area_files('US-AK', root)) >= 3)
    (root / 'US-AK.p2.geojson.gz').write_bytes(b'broken')
    rc = K.run(d, root, 'HEAD')
    check('keep_main: a broken part = exit 1 and main\'s parts are all put back', rc == 1 and sorted(M.load_area('US-AK', root)) == sorted(back))
    g = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_key_drop_guard.py'), '--repo', str(d), '--ref', 'HEAD'], capture_output=True, text=True)
    check('drop guard counts every part (no change = pass)', g.returncode == 0 and 'Drop guard US-AK' not in g.stdout)
    # release: a working state already in parts is released part by part, byte for byte
    sha = commit(d, 'x'); r = R.release(d, 'US', sha); idx = json.loads((d / 'data/released/RELEASED.json').read_text())
    lst = idx['files']['outlines/US-AK.geojson.gz']
    check('release: a working state in parts is listed part by part with the same names and bytes',
          [p for p, _ in lst] == ['outlines/' + f.name for f in M.area_files('US-AK', root)]
          and all((d / 'data/released' / p).read_bytes() == (root / p.split('/')[1]).read_bytes() for p, _ in lst) and 'outlines/US-AK.p2.geojson.gz' not in idx['files'])
    check('release: the released parts join to the same records', M.recs_of_doc(R.join([R.load_doc(p, (d / 'data/released' / p).read_bytes()) for p, _ in lst])).keys() == back.keys())

# ================================================================ B. the Alaska build, end to end on a synthetic saved copy (shapely stood in)
STUB = {'__init__.py': '', 'validation.py': 'def make_valid(s): return s\n',
        'geometry.py': '''class Polygon:
    def __init__(self, rings): self.rings = rings
    is_empty = False
class MultiPolygon:
    def __init__(self, polys): self.geoms = list(polys)
    is_empty = False
def shape(g): return Polygon(g['coordinates']) if g['type'] == 'Polygon' else MultiPolygon([Polygon(c) for c in g['coordinates']])
def mapping(s): return {'type': 'Polygon', 'coordinates': s.rings} if isinstance(s, Polygon) else {'type': 'MultiPolygon', 'coordinates': [p.rings for p in s.geoms]}
''', 'ops.py': '''from shapely.geometry import MultiPolygon, Polygon
def unary_union(ss):   # the test shapes do not overlap: their union is all their polygons
    return MultiPolygon([p for s in ss for p in ([s] if isinstance(s, Polygon) else s.geoms)])
'''}
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); stub = d / 'stub/shapely'; stub.mkdir(parents=True)
    for n, s in STUB.items(): (stub / n).write_text(s)
    root = d / 'data/outlines'; kd = d / 'data/us-key'; cache = d / 'cache'; root.mkdir(parents=True); cache.mkdir()
    def esri(poly): return [list(reversed(r)) for r in poly]                           # Esri: outer ring clockwise
    recs, parks = [], {}
    for i in range(30):                                                                   # parks already in the file
        parks[f'US-7{i:03d}'] = {'g': 'official', 'm': [[f'sgaka{i}', 'x', 1, 'name']]}
    M.save_area('US-AK', {f'US-7{i:03d}': rec(f'US-7{i:03d}', geom=SQ(i), ids=[f'sgaka{i}']) for i in range(30)}, root, key_dir=kd)
    existing = M.load_area('US-AK', root)
    yk = big_multi(60, 4000, -165.0)
    recs += [{'OBJECTID': 5457, '_r': [r for p in yk['coordinates'][:30] for r in esri(p)]}, {'OBJECTID': 4496, '_r': [r for p in yk['coordinates'][30:] for r in esri(p)]}]
    parks['US-0156'] = {'g': 'official', 'n': 'Yukon Delta National Wildlife Refuge', 'm': [[5457, 'Yukon Delta', 1, 'name'], [4496, 'Yukon Delta', 1, 'name']]}
    for i in range(12):
        poly = island(-150.0 + i, 62.0, 2000)
        recs.append({'OBJECTID': f'sgakb{i}', '_r': esri(poly)})
        parks[f'US-9{i:03d}'] = {'g': 'approximate' if i == 0 else 'official', 'n': f'Park {i}', 'm': [[f'sgakb{i}', 'x', 1, 'name']]}
    parks['US-9100'] = {'g': 'official', 'n': 'Missing record', 'm': [['sgakz1', 'x', 1, 'name']]}
    parks['US-9101'] = {'g': 'official', 'n': 'A trail', 'm': [['trl5', 'x', 1, 'name']]}
    parks['US-9102'] = {'g': 'pin', 'n': 'Pin', 'm': [['sgakb3', 'x', 1, 'name']]}
    keyfile(kd, 'AK', parks)
    with gzip.open(cache / 'US-AK.json.gz', 'wt') as f: json.dump({'recs': recs}, f)
    FK = str(ROOT / '.github/scripts/kpc_outlines_from_key.py'); env = dict(os.environ, PYTHONPATH=str(d / 'stub'))
    base = [sys.executable, FK, '--cache', str(cache), '--states', 'AK', '--root', str(root), '--key', str(kd)]
    dry = subprocess.run(base + ['--dry-run'], capture_output=True, text=True, env=env)
    check('Alaska build --dry-run: per park what would be written, the part files with sizes, the skipped parks and why; nothing written',
          dry.returncode == 0 and 'would write US-0156 official' in dry.stdout and 'would write US-9000 approximate' in dry.stdout
          and 'would save US-AK.p2.geojson.gz' in dry.stdout and 'US-AK: 13 outline(s) would be added; 1 skipped' in dry.stdout
          and 'skipped US-9100: 1 of 1 joined records not in the saved copy' in dry.stdout and M.area_files('US-AK', root) == [root / 'US-AK.geojson.gz'], dry.stdout[-600:] + dry.stderr[-600:])
    run = subprocess.run(base, capture_output=True, text=True, env=env)
    files = M.area_files('US-AK', root); got = M.load_area('US-AK', root)
    check(f'Alaska build: written in {len(files)} parts, each under 1 MB', run.returncode == 0 and len(files) >= 2 and all(f.stat().st_size <= 1_000_000 for f in files), run.stdout[-400:] + run.stderr[-400:])
    check('Alaska build: the 13 parks with every joined record are added (official / approximate as the key grades them); no trail, no pin, no partial one',
          set(got) - set(existing) == {'US-0156', *(f'US-9{i:03d}' for i in range(12))} and got['US-9000']['g'] == 'approximate' and got['US-0156']['g'] == 'official')
    check('Alaska build: the outlines that were there are unchanged (same hash)', all(got[r]['hash'] == v['hash'] for r, v in existing.items()))
    yk_pts = sum(len(r) for p in got['US-0156']['geometry']['coordinates'] for r in p)
    check(f'Alaska build: full default precision (5 decimals, 0.0001 deg trim only; Yukon Delta keeps {yk_pts:,} points of 240,060)',
          len(got['US-0156']['geometry']['coordinates']) == 60 and yk_pts > 200_000 and got['US-0156']['detail'] == M.DEFAULT_DETAIL)
with tempfile.TemporaryDirectory() as t:     # --verify: the check to run afterwards (against the commit before the build)
    d = pathlib.Path(t); root = d / 'data/outlines'; kd = d / 'data/us-key'; root.mkdir(parents=True); git_repo(d)
    keyfile(kd, 'AK', {'US-7000': {'g': 'official'}, 'US-7001': {'g': 'pin'}, 'US-7002': {'g': 'official'}, 'US-0156': {'g': 'official'}})
    M.save_area('US-AK', {r: rec(r) for r in ('US-7000', 'US-7001', 'US-7002')}, root, key_dir=d / 'none'); commit(d, 'before')
    M.save_area('US-AK', dict({r: rec(r) for r in ('US-7000', 'US-7001', 'US-7002')}, **{'US-0156': rec('US-0156', geom=big_multi(100, 4000))}), root, key_dir=kd)
    FK = str(ROOT / '.github/scripts/kpc_outlines_from_key.py')
    v = subprocess.run([sys.executable, FK, '--verify', '--states', 'AK', '--root', str(root)], capture_output=True, text=True, cwd=d)
    check('--verify: in parts, the old outlines unchanged, the pin-graded one dropped, every file under 1 MB = OK',
          v.returncode == 0 and 'US-AK: OK' in v.stdout and '1 new,' in v.stdout and 'dropped as pin' in v.stdout and 'US-AK.p2.geojson.gz' in v.stdout, v.stdout + v.stderr)
    d2 = M.load_area('US-AK', root); d2['US-7000'] = rec('US-7000', geom=SQ(5)); M.save_area('US-AK', d2, root)
    v = subprocess.run([sys.executable, FK, '--verify', '--states', 'AK', '--root', str(root)], capture_output=True, text=True, cwd=d)
    check('--verify: an old outline that changed = PROBLEM, exit 1', v.returncode == 1 and 'changed: US-7000' in v.stdout)

# ================================================================ B. the pages: KPCREL / kpcKeyOutlines / KPCB.usOutline read every part (node)
node = shutil.which('node')
HARNESS = r"""
const fs = require('fs'), path = require('path');
const [web, script, mode] = process.argv.slice(2);
globalThis.window = globalThis; let asked = [];
window.fetch = (u, o) => { asked.push(u); const f = path.join(web, String(u).split('?')[0]);
  if (!fs.existsSync(f)) return Promise.resolve({ ok: false, status: 404 });
  const b = fs.readFileSync(f); const ab = b.buffer.slice(b.byteOffset, b.byteOffset + b.length);
  return Promise.resolve({ ok: true, status: 200, arrayBuffer: () => Promise.resolve(ab), json: () => Promise.resolve(JSON.parse(b.toString())) }); };
globalThis.document = { createElement: () => ({ style: {} }), head: { appendChild() {} }, addEventListener() {}, querySelector: () => null, querySelectorAll: () => [] };
globalThis.localStorage = { getItem: () => null, setItem() {} };
if (mode === 'working') window.KPC_WORKING_COPY = true;   /* Nov 11 (job 3): the working-copy path is the Map Rep path now; a public page never reads it */
require(script);
(async () => {
  const out = {};
  const pack = await window.kpcKeyOutlines.load('ZZ');
  out.n = pack ? pack.features.length : -1;
  out.refs = pack ? Object.keys(pack.by).sort() : [];
  const big = pack && pack.by['US-9003'];
  out.bigPolys = big ? big.geometry.coordinates.length : -1;
  out.pieceLeft = pack ? pack.features.some(f => f.kpc_piece) : true;
  if (window.KPCB) {
    for (const r of ['US-9001', 'US-9002', 'US-9003', 'US-9004']) { const u = await KPCB.usOutline(r, r, 61, -150, ['ZZ']); out[r] = [u.label, (u.fs || []).length]; }
  }
  out.asked = asked.filter(u => /outlines/.test(u));
  console.log(JSON.stringify(out));
})();
"""
if node:
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t); web = d / 'web'; root = web / 'data/outlines'; kd = web / 'data/us-key'; root.mkdir(parents=True)
        parks = {'US-9001': {'g': 'official', 'n': 'One', 'm': [['a1', 'One', 1, 'name']]}, 'US-9002': {'g': 'approximate', 'n': 'Two', 'm': [['a2', 'Two', 1, 'name']]},
                 'US-9003': {'g': 'official', 'n': 'Big', 'm': [['a3', 'Big', 1, 'name']]}, 'US-9004': {'g': 'pin', 'n': 'Pin', 'm': [['a4', 'Pin', 1, 'name']]}}
        parks.update({f'US-95{i:02d}': {'g': 'official', 'n': f'Fill {i}', 'm': [[f'a95{i:02d}', 'x', 1, 'name']]} for i in range(20)})
        keyfile(kd, 'ZZ', parks)
        rs = {'US-9001': rec('US-9001', geom=big_multi(2, 400, -150)), 'US-9002': rec('US-9002', 'approximate', geom=big_multi(2, 400, -149)),
              'US-9003': rec('US-9003', geom=big_multi(12, 400, -148)), 'US-9004': rec('US-9004')}
        rs.update({f'US-95{i:02d}': rec(f'US-95{i:02d}', geom=big_multi(1, 300, -140 + i)) for i in range(20)})
        M.save_area('US-ZZ', rs, root, cap=12_000)
        nparts = len(M.area_files('US-ZZ', root))
        want = sorted(set(rs) - {'US-9004'})
        def run(script, wd=web, mode='working'):
            hp = d / 'h.js'; hp.write_text(HARNESS)
            r = subprocess.run([node, str(hp), str(wd), str(ROOT / script), mode], capture_output=True, text=True, timeout=120)
            try: return json.loads(r.stdout.strip().splitlines()[-1])
            except Exception: return {'err': (r.stdout + r.stderr)[-500:]}
        for script in ('kpc-bounds.js', 'kpc-padus-layer.js'):
            o = run(script)
            check(f'{script} working copy: kpcKeyOutlines.load reads all {nparts} parts, the big park whole again ({o.get("bigPolys")} polygons)',
                  nparts >= 3 and o.get('n') == len(want) and o.get('refs') == want and o.get('bigPolys') == 12 and o.get('pieceLeft') is False, o)
            check(f'{script}: the parts asked for are part 1 then .p2 .. .p{nparts}', [a.split('?')[0] for a in o.get('asked', [])] ==
                  ['data/outlines/US-ZZ.geojson.gz'] + [f'data/outlines/US-ZZ.p{i}.geojson.gz' for i in range(2, nparts + 1)], o.get('asked'))
        o = run('kpc-bounds.js')
        check('KPCB.usOutline (planner, Park Commander card, overlap finder) on a state in parts: official -> official shape, approximate -> approx, pin -> nothing',
              o.get('US-9001') == ['official', 1] and o.get('US-9002') == ['approx', 1] and o.get('US-9003') == ['official', 1] and o.get('US-9004') == ['none', 0], o)
        # parts of two saves: nothing (never half a state)
        p2 = root / 'US-ZZ.p2.geojson.gz'; keep = p2.read_bytes(); x = json.loads(gzip.decompress(keep)); x['kpc_part'][2] = 'zzzz'; p2.write_bytes(gzip.compress(json.dumps(x).encode()))
        o = run('kpc-bounds.js')
        check('working copy: a part of another save = no outlines for the state (and it was read again fresh)', o.get('n') == -1 and len(o.get('asked', [])) == 2 * nparts, o)
        p2.write_bytes(keep)
        # the released path: the release lists the same parts; the pages read them from data/released
        git_repo(web); sha = commit(web, 'zz'); R.release(web, 'US', sha)
        shutil.rmtree(root)                                                                  # only the released copy is left
        o = run('kpc-bounds.js', mode='public')
        check('released path: the same parts from data/released, joined the same way',
              o.get('n') == len(want) and o.get('bigPolys') == 12 and o.get('US-9002') == ['approx', 1] and o.get('US-9004') == ['none', 0]
              and all(a.startswith('data/released/outlines/US-ZZ') for a in o.get('asked', [])), o)
else: print('SKIP node not installed: the page loader runs')

# ================================================================ wiring
pages = {'kpc-planner-us.html': ('kpc-bounds.js', 'kpc-padus-layer.js', 'kpc-us-planner.js'), 'kpc-park-control.html': ('kpc-bounds.js', 'kpc-padus-layer.js'),
         'kpc-overlap-finder.html': ('kpc-bounds.js', 'kpc-padus-layer.js')}
for h, js in pages.items():
    hs = (ROOT / h).read_text(encoding='utf-8', errors='replace')
    check(f'{h} loads the part-aware loaders ({", ".join(js)}, ?v=20261111zr)', all(f'{j}?v=20261111zr' in hs for j in js))   # Nov 11 (page size): bumped again
blk = lambda s: s[s.index('/* >>> kpc_released'):s.index('/* <<< kpc_released */')]
srcs = [(ROOT / n).read_text(encoding='utf-8') for n in ('kpc-bounds.js', 'kpc-padus-layer.js', 'kpc-us-planner.js', 'kpc-gps.js')]
check('the four KPCREL copies are the same and read parts on the working path', len({blk(s) for s in srcs}) == 1 and 'more(path, d, wk)' in blk(srcs[0]) and 'pieces(' in blk(srcs[0]))
wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text()
check('the key workflow\'s outline paths go through the part-aware tools (part / collect / from_key / keep_main / check)',
      all(x in wf for x in ('kpc_master_cli.py part', 'kpc_master_cli.py collect', 'kpc_outlines_from_key.py', 'kpc_outlines_keep_main.py', 'kpc_master_cli.py check')))
import kpc_key_freeze as FZ
check('no rules file is touched by this change', not any(x.endswith(('kpc_master.py', 'kpc_release.py', 'kpc_master_cli.py', 'kpc_master_fill.py', 'kpc_outlines_from_key.py'))
                                                         for v in FZ.RULE_FILES.values() for x in v))
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
