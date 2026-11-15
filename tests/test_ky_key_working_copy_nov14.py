#!/usr/bin/env python3
"""Nov 14 (KPC owner): the Kentucky answer key is built from the WORKING Kentucky layers again, and a Kentucky release refuses a drop.
1. kpc_ky_key.js runs kpc-bounds.js in a node vm. Since the Nov 12 "released maps only" change kpc-bounds.js reads every Kentucky layer
   through KPCREL, which was never defined in that vm (no fetch on the vm's window; the bare name KPCREL not visible): every layer
   read as empty and only 5 of 193 parks kept an outline. The vm window now has fetch + KPC_WORKING_COPY and ctx.KPCREL is set.
   Synthetic case (a temp folder): the park's outline is found in the WORKING root file, never in the released copy.
   Real case: the key script on a temp copy of this repo's Kentucky files finds no fewer outlined parks than the released key.
2. kpc_release.py: Kentucky gets the same "fewer outlined parks than live = worse, refused, the live copy stays" check as US / CA / world.
Offline: temp folders and node only; the repo's own files are only read."""
import json, pathlib, shutil, subprocess, sys, tempfile
import os as _os; _os.environ.setdefault('GITHUB_TRIGGERING_ACTOR', 'KentuckyPortableClub')
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_release as R

ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + (f'  [{str(extra)[:300]}]' if extra and not cond else ''))
    ok = ok and bool(cond)

def sh(d, *a): return subprocess.run(a, cwd=d, capture_output=True, text=True)
def run_key(d):
    r = subprocess.run(['node', str(pathlib.Path(d) / '.github/scripts/kpc_ky_key.js')], cwd=d, capture_output=True, text=True, timeout=240)
    first = (r.stdout.splitlines() or [''])[0]
    key = json.loads((pathlib.Path(d) / 'data/ky-answer-key.json').read_text()) if (pathlib.Path(d) / 'data/ky-answer-key.json').is_file() else {}
    return r, first, key
def outlined(key): return sum(1 for p in (key.get('parks') or {}).values() if p.get('tracts'))
SQ = [[[-85.01, 37.99], [-84.99, 37.99], [-84.99, 38.01], [-85.01, 38.01], [-85.01, 37.99]]]

# ---- 1a. synthetic: one park, its outline only in the WORKING layer; the released copy of that layer is empty
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    (d / '.github/scripts').mkdir(parents=True); (d / 'data/released/ky').mkdir(parents=True)
    shutil.copy(ROOT / '.github/scripts/kpc_ky_key.js', d / '.github/scripts/kpc_ky_key.js')
    shutil.copy(ROOT / 'kpc-bounds.js', d / 'kpc-bounds.js')
    (d / 'kpc-ky-data.json').write_text(json.dumps({'parks': [{'c': 'US-9901', 'n': 'Synthetic Lake State Park', 't': 'State park', 'la': 38.0, 'lo': -85.0}], 'kff': [], 'summits': []}))
    (d / 'ky-state-parks.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'NAME': 'Synthetic Lake State Park'}, 'geometry': {'type': 'Polygon', 'coordinates': SQ}}]}))
    (d / 'data/released/ky/ky-state-parks.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': []}))
    (d / 'data/released/RELEASED.json').write_text(json.dumps({'areas': {'KY': {'sha': 'x', 'time': 't'}}, 'files': {'ky/ky-state-parks.geojson': [['ky/ky-state-parks.geojson', 'v1']]}}))
    r, first, key = run_key(d)
    check('synthetic: the key script runs (exit 0)', r.returncode == 0, r.stderr)
    check('synthetic: the park gets its outline from the WORKING ky-state-parks.geojson (1 with outlines, 0 none)',
          '1 with outlines' in first and '0 none' in first and key.get('missing') == [], first)
    tr = ((key.get('parks') or {}).get('US-9901') or {}).get('tracts') or []
    check('synthetic: the tract is the state-park record, joined by name', bool(tr) and tr[0][0] == 'bstate' and tr[0][1] == 'Synthetic Lake State Park' and tr[0][3] == 'name', tr)

# ---- 1b. real Kentucky files: no fewer outlined parks than the released key (Nov 12 working key: 5 of 193)
rel_key = json.loads((ROOT / 'data/released/ky/ky-answer-key.json').read_text())
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    (d / '.github/scripts').mkdir(parents=True); (d / 'data/released').mkdir(parents=True)
    shutil.copy(ROOT / '.github/scripts/kpc_ky_key.js', d / '.github/scripts/kpc_ky_key.js')
    for f in ['kpc-bounds.js', 'kpc-ky-data.json'] + [p.name for p in ROOT.glob('ky-*.geojson')]:
        shutil.copy(ROOT / f, d / f)
    for f in ('data/ky-answer-key.json', 'data/park-transfers.json', 'data/ky-key-no.json', 'data/released/RELEASED.json'):
        if (ROOT / f).is_file(): shutil.copy(ROOT / f, d / f)
    if (ROOT / 'data/trails').is_dir(): shutil.copytree(ROOT / 'data/trails', d / 'data/trails')
    r, first, key = run_key(d)
    n_new, n_rel = outlined(key), outlined(rel_key)
    check('real: the key script runs (exit 0)', r.returncode == 0, r.stderr)
    check(f'real: every Kentucky park is in the key ({len(key.get("parks") or {})} parks)', len(key.get('parks') or {}) == len(json.loads((ROOT / 'kpc-ky-data.json').read_text())['parks']))
    check(f'real: outlined parks {n_new} >= the released key\'s {n_rel} (the broken vm gave 5)', n_new >= n_rel and n_new > 5, first)

# ---- 2. the Kentucky release refuses a drop in outlined parks; the live copy stays
def ky_key(n_out, n_all):
    parks = {f'US-{9000 + i}': {'n': f'P{i}', 't': '', 'tracts': ([['bsp', f'P{i}', 10, 'name', 1]] if i < n_out else [])} for i in range(n_all)}
    return {'updated': '2026-11-14', 'parks': parks, 'nonum': [], 'kffonly': [], 'missing': [r for r, p in parks.items() if not p['tracts']]}
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
    (d / 'data/released/ky').mkdir(parents=True)
    def commit_key(k):
        (d / 'data/ky-answer-key.json').write_text(json.dumps(k)); sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'k')
        return sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip()
    sha_new = commit_key(ky_key(10, 10))
    check('no live KY copy yet: allowed', R.no_worse_than_live(d, 'KY', 'KY', sha_new)[0] is True)
    (d / 'data/released/ky/ky-answer-key.json').write_text(json.dumps(ky_key(193, 193)))
    sha_bad = commit_key(ky_key(5, 193))
    okb, why = R.no_worse_than_live(d, 'KY', 'KY', sha_bad)
    check('193 -> 5 outlined parks: refused as worse than live', okb is False and '193 -> 5' in why and 'worse than live' in why, why)
    sha_same = commit_key(ky_key(193, 193))
    check('193 -> 193: allowed', R.no_worse_than_live(d, 'KY', 'KY', sha_same) == (True, ''))
    sha_more = commit_key(ky_key(194, 194))
    check('193 -> 194 (a new park with an outline): allowed', R.no_worse_than_live(d, 'KY', 'KY', sha_more) == (True, ''))
    check('193 -> 192: refused', R.no_worse_than_live(d, 'KY', 'KY', commit_key(ky_key(192, 193)))[0] is False)
    (d / 'data/ky-answer-key.json').unlink(); sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'gone')
    check('no key file at the commit: refused', R.no_worse_than_live(d, 'KY', 'KY', sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip())[0] is False)
    grade = {'sha': sha_bad, 'RELEASE-READY': 'YES', 'areas': {'KY': {'RELEASE-READY': 'YES'}}}
    res = R.release_areas(d, sha_bad, [('KY', 'KY')], dry_run=True, grade=grade)
    check('release_areas: the worse KY build is kept live (not promoted), with the reason',
          not res['promoted'] and any(k['unit'] == 'KY' and 'worse than live' in k['why'] for k in res['kept']), res)
    check('the US / CA / world count is unchanged (outlined_n still counts US-style rows)',
          R.outlined_n({'parks': {'a': {'g': 'official', 'm': [1]}, 'b': {'g': 'pin'}}}) == 1)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
