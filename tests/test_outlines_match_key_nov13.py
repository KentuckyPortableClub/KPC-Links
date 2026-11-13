#!/usr/bin/env python3
"""Nov 13 (Quality M1/M2, US-43293787778): outlines agree with the key.
M1: no outline for a park the key grades PIN; no outline that holds a record missing from the key's m
(held record 2165 in AK US-10281). The save-time check (kpc_master_cli.py check) fails closed, and
kpc_release.py trims PIN / not-in-key features and refuses an area with a held-record leftover.
M2: the outline builder / save_area drops refs no US key lists (MN US-13655..13658).
Per-area: a dirty neighbour (AK) does not block a clean state (KY). US-42797939226 stays on the refuse-list.
Offline: temp dirs only.
"""
import gzip, json, os, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M
import kpc_release as R
import kpc_outlines_from_key as FK

ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + (f'  [{str(extra)[:400]}]' if extra and not cond else ''))
    ok = ok and bool(cond)

def sh(d, *a): return subprocess.run(a, cwd=d, capture_output=True, text=True)
def git_repo(d):
    sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
def commit(d, m='c'):
    sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', m)
    return sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip()
SQ = lambda x=0: {'type': 'Polygon', 'coordinates': [[[x, 0], [x, 1], [x + 1, 1], [x + 1, 0], [x, 0]]]}
def rec(ref, g='official', geom=None, ids=None):
    return M.make_record(ref, ref, g, geom or SQ(), 'agency', 'file:US-ZZ.json.gz', ids or ['1'], 10, '2026-11-11', '', 'key')
def keyfile(d, st, parks):
    (d / f'US-{st}.json').parent.mkdir(parents=True, exist_ok=True)
    (d / f'US-{st}.json').write_text(json.dumps({'parks': parks}))

# --- helpers on a synthetic MN / NV / AK set ---
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); root = d / 'data/outlines'; kd = d / 'data/us-key'; root.mkdir(parents=True)
    keyfile(kd, 'MN', {'US-0100': {'g': 'official', 'm': [['a', 'n', 1, 'name']]}})
    keyfile(kd, 'NV', {'US-10844': {'g': 'pin', 'm': []}, 'US-0200': {'g': 'official', 'm': [['b', 'n', 1, 'name']]}})
    keyfile(kd, 'NH', {'US-4868': {'g': 'pin'}, 'US-4886': {'g': 'pin'}, 'US-0300': {'g': 'official', 'm': [['c', 'n', 1, 'name']]}})
    keyfile(kd, 'OR', {'US-12841': {'g': 'pin'}, 'US-0400': {'g': 'official', 'm': [['d', 'n', 1, 'name']]}})
    keyfile(kd, 'AK', {'US-10281': {'g': 'official', 'm': [['rst11010', 'White Mountains SRMA', 1, 'name'],
                                                           ['sgakg11010', 'White Mountains SRMA', 1, 'reviewed']]}})
    keyfile(kd, 'KY', {'US-0500': {'g': 'official', 'm': [['e', 'n', 1, 'name']]}})
    keyfile(kd, 'NM', {'US-4514': {'g': 'official', 'm': [['f', 'n', 1, 'name']]}})
    keyfile(kd, 'TX', {'US-4514': {'g': 'pin'}})

    M.save_area('US-MN', {r: rec(r, ids=['x']) for r in ('US-0100', 'US-13655', 'US-13656', 'US-13657', 'US-13658')}, root, key_dir=kd)
    check('M2: save_area drops US-13655..13658 (not in any key) and keeps the keyed park',
          sorted(M.load_area('US-MN', root)) == ['US-0100'])
    M.save_area('US-NV', {r: rec(r, ids=['b'] if r == 'US-0200' else ['z']) for r in ('US-10844', 'US-0200')}, root, key_dir=kd)
    check('M1: save_area drops a PIN park (US-10844) and keeps the official one',
          sorted(M.load_area('US-NV', root)) == ['US-0200'])
    M.save_area('US-TX', {'US-4514': rec('US-4514', ids=['f'])}, root, key_dir=kd)
    check('US-4514 (pin in TX, official in NM) keeps its outline wherever it has one',
          'US-4514' in M.load_area('US-TX', root))

    dirty = rec('US-10281', ids=['rst11010', 'sgakg11010', '2165'])
    M.save_area('US-AK', {'US-10281': dirty}, root, key_dir=kd)   # official: not dropped, held id stays until rebuild
    got = M.load_area('US-AK', root)['US-10281']
    check('save_area does not silently drop an official park with a held-record leftover',
          'US-10281' in M.load_area('US-AK', root) and '2165' in M.outline_record_ids(got))
    probs = M.outline_key_problems('US-AK', M.load_area('US-AK', root), kd)
    check('outline_key_problems names US-10281 and held record 2165',
          any('US-10281' in m and '2165' in m for m in probs), probs)
    M.save_area('US-KY', {'US-0500': rec('US-0500', ids=['e'])}, root, key_dir=kd)
    M.save_area('US-NH', {'US-4868': rec('US-4868'), 'US-4886': rec('US-4886'), 'US-0300': rec('US-0300', ids=['c'])}, root, key_dir=kd)
    M.save_area('US-OR', {'US-12841': rec('US-12841'), 'US-0400': rec('US-0400', ids=['d'])}, root, key_dir=kd)
    check('NH US-4868/4886 and OR US-12841 (PIN) are not in the outline files after save',
          'US-4868' not in M.load_area('US-NH', root) and 'US-4886' not in M.load_area('US-NH', root)
          and 'US-12841' not in M.load_area('US-OR', root))

    # save-time check: whole tree fails; --areas US-KY is clean; --areas US-AK fails
    rc = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_master_cli.py'), 'check',
                         '--root', str(root), '--key', str(kd)], capture_output=True, text=True)
    check('check fails closed when AK holds record 2165', rc.returncode == 1 and '2165' in rc.stderr + rc.stdout)
    rc_ky = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_master_cli.py'), 'check',
                            '--root', str(root), '--key', str(kd), '--areas', 'US-KY'], capture_output=True, text=True)
    check('check --areas US-KY is clean (per-area: AK does not block KY)', rc_ky.returncode == 0, rc_ky.stderr)
    rc_ak = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_master_cli.py'), 'check',
                            '--root', str(root), '--key', str(kd), '--areas', 'US-AK'], capture_output=True, text=True)
    check('check --areas US-AK still fails on held record 2165', rc_ak.returncode == 1 and '2165' in rc_ak.stderr + rc_ak.stdout)

    # from_key: drops PIN leftovers already in the file even when nothing new is added
    have_nv = M.load_area('US-NV', root)
    # sneak a PIN leftover back into the file without going through save_area's drop, then from_key with no new parks
    # (build a bare file)
    leftover = dict(have_nv); leftover['US-10844'] = rec('US-10844')
    # write raw to bypass save_area drop so from_key must clean it
    import kpc_release as _R
    # use save_area with a missing key first, then run from_key with the real key
    M.save_area('US-NV', leftover, root, key_dir=d / 'nowhere')
    check('precondition: PIN leftover is in the file when the key is absent', 'US-10844' in M.load_area('US-NV', root))
    added, skipped = FK.build_state('NV', cache=d, root=root, key_dir=kd, say=lambda *a, **k: None)
    check('from_key drops the PIN leftover even when it adds no new park',
          'US-10844' not in M.load_area('US-NV', root) and 'US-0200' in M.load_area('US-NV', root))

# --- per-area release: trim PIN/not-in-key, refuse AK, promote KY ---
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t) / 'r'; d.mkdir()
    git_repo(d)
    for f in ('data/outlines', 'data/us-key', 'data/status/quality'): (d / f).mkdir(parents=True)
    def wkey(st, parks): (d / 'data/us-key' / f'US-{st}.json').write_text(json.dumps({'parks': parks}))
    wkey('KY', {'US-0500': {'g': 'official', 'm': [['e', 'n', 1, 'name']]}})
    wkey('AK', {'US-10281': {'g': 'official', 'm': [['rst11010', 'n', 1, 'name'], ['sgakg11010', 'n', 1, 'reviewed']]}})
    wkey('MN', {'US-0100': {'g': 'official', 'm': [['a', 'n', 1, 'name']]}})
    wkey('NV', {'US-10844': {'g': 'pin'}, 'US-0200': {'g': 'official', 'm': [['b', 'n', 1, 'name']]}})
    # outlines: KY clean; AK has held 2165; MN has orphans; NV has a PIN leftover written without key_fix
    M.save_area('US-KY', {'US-0500': rec('US-0500', ids=['e'])}, d / 'data/outlines', key_dir=d / 'data/us-key')
    M.save_area('US-AK', {'US-10281': rec('US-10281', ids=['rst11010', 'sgakg11010', '2165'])}, d / 'data/outlines', key_dir=d / 'data/us-key')
    # put the four orphans in MN by writing through no-key, then we will release with the real key
    recs_mn = {'US-0100': rec('US-0100', ids=['a'])}
    recs_mn.update({r: rec(r, ids=['x']) for r in ('US-13655', 'US-13656', 'US-13657', 'US-13658')})
    M.save_area('US-MN', recs_mn, d / 'data/outlines', key_dir=d / 'nowhere')
    M.save_area('US-NV', {'US-10844': rec('US-10844'), 'US-0200': rec('US-0200', ids=['b'])},
                d / 'data/outlines', key_dir=d / 'nowhere')
    (d / 'data/us-key' / 'layers.json').write_text(json.dumps({'layers': []}))
    (d / 'data/us-key' / 'index.json').write_text(json.dumps({
        'build': 'US-43293787778',
        'states': {st: {'check': 'ok', 'parks': 1, 'matched': 1} for st in ('KY', 'AK', 'MN', 'NV')},
        'failed': [], 'held_expected': [],
    }))
    (d / 'data/status/key-check').mkdir(parents=True, exist_ok=True)
    (d / 'data/status/key-check' / 'us-US-43293787778.json').write_text(json.dumps({'key': 'us', 'build': 'US-43293787778', 'gate': 'PASS'}))
    sha = commit(d, 'dirty outlines')
    grade = {'RELEASE-READY': 'YES', 'sha': sha}
    # seed live from a first clean-enough release of KY only? need live files for no_worse. no live yet is ok.
    why_ak = R.why_not_promote(d, 'US', 'US-AK', sha, grade)
    why_ky = R.why_not_promote(d, 'US', 'US-KY', sha, grade)
    why_mn = R.why_not_promote(d, 'US', 'US-MN', sha, grade)
    why_nv = R.why_not_promote(d, 'US', 'US-NV', sha, grade)
    check('release refuses US-AK: outline holds record 2165 not in the key\'s m',
          why_ak and '2165' in why_ak and 'US-10281' in why_ak, why_ak)
    check('US-KY is not refused (per-area: AK does not block KY)', why_ky == '', why_ky)
    check('US-MN and US-NV are not refused (PIN / not-in-key will be trimmed, not held)',
          why_mn == '' and why_nv == '', (why_mn, why_nv))

    r = R.release_areas(d, sha, 'US-KY US-AK US-MN US-NV', run='r1', now='T1', grade=grade)
    promoted = {p['unit'] for p in r['promoted']}
    kept = {k['unit']: k['why'] for k in r['kept']}
    check('per-area release promotes KY, MN, NV and keeps AK on live',
          promoted == {'US-KY', 'US-MN', 'US-NV'} and 'US-AK' in kept, (promoted, kept))
    check('AK keep-reason names held record 2165', '2165' in kept.get('US-AK', ''), kept.get('US-AK'))
    # released MN / NV outlines must not carry the dropped refs
    mn = M.recs_of_doc(R.load_doc('outlines/US-MN.geojson.gz', (d / 'data/released/outlines/US-MN.geojson.gz').read_bytes()))
    nv = M.recs_of_doc(R.load_doc('outlines/US-NV.geojson.gz', (d / 'data/released/outlines/US-NV.geojson.gz').read_bytes()))
    check('released MN outline dropped US-13655..13658 and kept US-0100',
          sorted(mn) == ['US-0100'] and not any(r in mn for r in ('US-13655', 'US-13656', 'US-13657', 'US-13658')))
    check('released NV outline dropped PIN US-10844 and kept US-0200',
          sorted(nv) == ['US-0200'] and 'US-10844' not in nv)
    check('US-AK was not written to released/ (kept live; no file yet)',
          not (d / 'data/released/outlines/US-AK.geojson.gz').exists())

# refuse-list
check('US-42797939226 is on the release refuse-list', 'US-42797939226' in R.BLOCKED_BUILDS)
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t) / 'r'; d.mkdir(); git_repo(d)
    for f in ('data/outlines', 'data/us-key', 'data/status/quality'): (d / f).mkdir(parents=True)
    M.save_area('US-KY', {'US-0500': rec('US-0500', ids=['e'])}, d / 'data/outlines', key_dir=d / 'none')
    (d / 'data/us-key' / 'US-KY.json').write_text(json.dumps({'parks': {'US-0500': {'g': 'official', 'm': [['e', 'n', 1, 'name']]}}}))
    (d / 'data/us-key' / 'layers.json').write_text(json.dumps({'layers': []}))
    (d / 'data/us-key' / 'index.json').write_text(json.dumps({
        'build': 'US-42797939226',
        'states': {'KY': {'check': 'ok', 'parks': 1, 'matched': 1}},
        'failed': [], 'held_expected': [],
    }))
    sha = commit(d, 'blocked')
    why = R.why_not_promote(d, 'US', 'US-KY', sha, {'RELEASE-READY': 'YES', 'sha': sha})
    check('a sha whose index build is US-42797939226 is never released, even when the area looks green',
          why and 'US-42797939226' in why and 'never released' in why, why)

# from_key rebuild of US-10281 when the saved copy is present
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); root = d / 'outlines'; kd = d / 'us-key'; cache = d / 'cache'
    root.mkdir(); kd.mkdir(); cache.mkdir()
    keyfile(kd, 'AK', {'US-10281': {'g': 'official', 'n': 'White Mountains', 'read': '2026-11-11',
                                    'm': [['rst11010', 'White Mountains SRMA', 1, 'name'],
                                          ['sgakg11010', 'White Mountains SRMA', 1, 'reviewed']]}})
    # existing dirty outline
    M.save_area('US-AK', {'US-10281': rec('US-10281', ids=['rst11010', 'sgakg11010', '2165'], geom=SQ(0))}, root, key_dir=kd)
    # saved copy with the two joined records (and 2165, which must not be used)
    def rec_blob(oid, x):
        return {'OBJECTID': oid, '_r': [[[x, 0], [x, 1], [x + 1, 1], [x + 1, 0], [x, 0]]], 'Loc_Mang': 'BLM'}
    blob = {'saved': '2026-11-11', 'recs': [rec_blob('rst11010', 0), rec_blob('sgakg11010', 1), rec_blob('2165', 50)]}
    with gzip.open(cache / 'US-AK.json.gz', 'wt', encoding='utf-8') as f: json.dump(blob, f)
    added, skipped = FK.build_state('AK', cache=cache, root=root, key_dir=kd, say=lambda *a, **k: None)
    got = M.load_area('US-AK', root)['US-10281']
    check('from_key rebuilds US-10281 from the key\'s m (2165 is not in record_ids)',
          '2165' not in M.outline_record_ids(got) and set(M.outline_record_ids(got)) == {'rst11010', 'sgakg11010'},
          M.outline_record_ids(got))
    check('after rebuild, outline_key_problems is empty for AK',
          M.outline_key_problems('US-AK', M.load_area('US-AK', root), kd) == [])

print('ALL PASS' if ok else 'FAILED')
sys.exit(0 if ok else 1)
