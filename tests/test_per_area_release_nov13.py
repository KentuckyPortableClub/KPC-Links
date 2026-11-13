#!/usr/bin/env python3
"""Nov 13 (KPC owner): key release works one area (country, state or province) at a time.
A green, graded, no-worse-than-live area is promoted alone; a held or failed area keeps its
live data and never blocks the others. RELEASED.json live records the build each area came from.
US-42797939226 is never released. The by-hand workflow stays owner-run.
Offline: temp repos only.

  python3 tests/test_per_area_release_nov13.py
"""
import json, os, pathlib, re, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_release as R

ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + (f' {extra}' if extra and not cond else ''))
    ok = ok and bool(cond)

def sh(d, *a): return subprocess.run(a, cwd=d, capture_output=True, text=True)
def commit(d, m): sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', m); return sh(d, 'git', 'rev-parse', 'HEAD').stdout.strip()
def parks(n, outlined=True):
    if outlined: return {'parks': {f'US-{i}': {'g': 'official', 'm': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]} for i in range(n)}}
    return {'parks': {f'US-{i}': {'g': 'pin'} for i in range(n)}}
def wparks(cc, n):
    return {'parks': {f'{cc}-{i:04d}': {'g': 'official', 'm': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]} for i in range(n)}}
def write_key(d, path, doc):
    p = d / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(doc))
    # R2: a same-build key-check (gate PASS) is required to promote; keep fixtures honest
    if path.endswith('index.json') and isinstance(doc, dict) and doc.get('build'):
        b = str(doc['build'])
        prefix = 'us' if b.startswith('US-') else 'ca' if b.startswith('CA-') else 'world' if b.startswith('W-') else ''
        if prefix:
            c = d / f'data/status/key-check/{prefix}-{b}.json'
            c.parent.mkdir(parents=True, exist_ok=True)
            if not c.exists():
                c.write_text(json.dumps({'key': prefix, 'build': b, 'gate': 'PASS'}))
def write_outline(d, name):
    p = d / 'data/outlines' / name; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(R.gz(json.dumps({'type': 'FeatureCollection', 'features': []}).encode()))

# 1. parse_areas and the blocked-build constant
check('parse_areas reads mixed kinds (DE FR US-KY)', R.parse_areas('DE FR US-KY') == [('world', 'DE'), ('world', 'FR'), ('US', 'US-KY')])
check('KY alone is the Kentucky map pack; the US state is US-KY', R.parse_areas('KY') == [('KY', 'KY')] and R.parse_areas('US-KY') == [('US', 'US-KY')])
try: R.parse_areas('US'); bad = False
except R.ReleaseError as e: bad = 'kind' in str(e)
check('a kind name (US) is refused: name the states', bad)
check('US-42797939226 is on the never-released list', 'US-42797939226' in R.BLOCKED_BUILDS)

# 2. the owner-run workflow: areas input, no schedule, actor list, grade, no all-of-kind
wf = (ROOT / '.github/workflows/kpc-release.yml').read_text()
check('kpc-release.yml is workflow_dispatch only (no schedule, no push)',
      'workflow_dispatch:' in wf and 'schedule:' not in wf and 'pull_request:' not in wf and not re.search(r'^\s+push:', wf, re.M))
check('kpc-release.yml has an areas input (e.g. DE FR US-KY) and a grade input',
      'areas:' in wf and 'DE FR US-KY' in wf and 'grade:' in wf and '--areas' in wf and '--grade' in wf)
check('releases stay owner-run (KPC_RELEASE_ACTORS, fail closed) and the sha must be on main',
      'KPC_RELEASE_ACTORS' in wf and 'is not in the repo variable' in wf and 'is not a commit on main' in wf)
check('the owner-run workflow does not pass --all-of-kind (that skips the per-area grade)',
      '--all-of-kind' not in wf)
md = (ROOT / '.github/rebuild-levels.md').read_text()
check('rebuild-levels.md has a short per-area release section in plain words',
      'Per-area release' in md and 'one area at a time' in md and 'US-42797939226' in md and 'WDPA' in md)

# 3. per-area promote on a temp repo
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t) / 'r'; d.mkdir()
    sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
    for f in ('data/outlines', 'data/us-key', 'data/world-key', 'data/status/quality'): (d / f).mkdir(parents=True)
    write_outline(d, 'US-KY.geojson.gz'); write_outline(d, 'US-FL.geojson.gz')
    write_key(d, 'data/us-key/US-KY.json', parks(5))
    write_key(d, 'data/us-key/US-FL.json', parks(5))
    write_key(d, 'data/us-key/layers.json', {'layers': []})
    write_key(d, 'data/world-key/DE.json', wparks('DE', 4))
    write_key(d, 'data/world-key/FR.json', wparks('FR', 4))
    write_key(d, 'data/world-key/layers.json', {'layers': []})
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-43109409415',
        'states': {'KY': {'check': 'ok', 'parks': 5, 'matched': 5}, 'FL': {'check': 'ok', 'parks': 5, 'matched': 5}},
        'failed': [], 'held_expected': [],
    })
    write_key(d, 'data/world-key/index.json', {
        'build': 'W-43314866156',
        'countries': {'DE': {'check': 'ok', 'parks': 4}, 'FR': {'check': 'ok', 'parks': 4}},
        'failed': [], 'held_expected': ['FR'],
    })
    sha1 = commit(d, 'one')
    # seed a full live release of US (the old copier) so FL has live files
    R.release(d, 'US', sha1, run='1', now='T1')
    R.release(d, 'world', sha1, run='2', now='T2')
    live_fl = (d / 'data/released/us-key/US-FL.json').read_bytes()
    live_fr = (d / 'data/released/world-key/FR.json').read_bytes()
    live_de = (d / 'data/released/world-key/DE.json').read_bytes()
    layers = (d / 'data/released/us-key/layers.json').read_bytes()

    # newer commit: KY and DE get more parks; FL would get worse (drop outlines); FR is held
    write_key(d, 'data/us-key/US-KY.json', parks(8))
    write_key(d, 'data/us-key/US-FL.json', parks(2))  # worse than live (5 outlined -> 2)
    write_key(d, 'data/us-key/layers.json', {'layers': ['new-layer-must-not-land-on-a-partial-release']})
    write_key(d, 'data/world-key/DE.json', wparks('DE', 7))
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-43109999999',
        'states': {'KY': {'check': 'ok', 'parks': 8, 'matched': 8}, 'FL': {'check': 'ok', 'parks': 2, 'matched': 2}},
        'failed': [], 'held_expected': [],
    })
    write_key(d, 'data/world-key/index.json', {
        'build': 'W-43319999999',
        'countries': {'DE': {'check': 'ok', 'parks': 7}, 'FR': {'check': 'ok', 'parks': 4}},
        'failed': [], 'held_expected': ['FR'],
    })
    sha2 = commit(d, 'two')

    grade = {
        'RELEASE-READY': 'PARTIAL',
        'sha': sha2,
        'areas': {
            'US-KY': {'RELEASE-READY': 'YES'},
            'DE': {'RELEASE-READY': 'YES'},
            'FR': {'RELEASE-READY': 'NO'},
            'US-FL': {'RELEASE-READY': 'YES'},  # would be yes, but worse than live and so kept
        },
    }
    gf = d / 'data/status/quality/verdicts.json'
    gf.write_text(json.dumps(grade))

    r = R.release_areas(d, sha2, 'DE FR US-KY US-FL', run='9', now='T9', grade=gf)
    idx = json.loads((d / 'data/released/RELEASED.json').read_text())
    check('DE and US-KY are promoted; FR (held) and US-FL (worse than live) are kept',
          {p['unit'] for p in r['promoted']} == {'DE', 'US-KY'}
          and {k['unit'] for k in r['kept']} == {'FR', 'US-FL'},
          r)
    check('a held area keeps its live bytes (FR) and does not block DE or US-KY',
          (d / 'data/released/world-key/FR.json').read_bytes() == live_fr
          and (d / 'data/released/world-key/DE.json').read_bytes() != live_de
          and (d / 'data/released/us-key/US-KY.json').read_bytes() != live_fl)
    check('a worse-than-live area keeps its live bytes (US-FL)',
          (d / 'data/released/us-key/US-FL.json').read_bytes() == live_fl)
    check('a partial US release does not replace shared layers.json',
          (d / 'data/released/us-key/layers.json').read_bytes() == layers)
    check('live records the new build for promoted areas only',
          idx['live']['US-KY']['build'] == 'US-43109999999' and idx['live']['US-KY']['sha'] == sha2
          and idx['live']['US-KY'].get('rules') is not None
          and idx['live']['DE']['build'] == 'W-43319999999' and idx['live']['DE']['sha'] == sha2
          and idx['live']['US-FL']['sha'] == sha1 and idx['live']['FR']['sha'] == sha1,
          idx.get('live'))
    check('areas.US / areas.world sha stay on the last full-kind release (a partial run does not pretend the whole kind moved)',
          idx['areas']['US']['sha'] == sha1 and idx['areas']['world']['sha'] == sha1)

    # no grade -> nothing promoted, live unchanged
    fl2 = (d / 'data/released/us-key/US-FL.json').read_bytes()
    r2 = R.release_areas(d, sha2, 'US-KY', run='10', now='T10', grade=None)
    check('with no Quality grade, the area is kept live (fail closed)',
          r2['promoted'] == [] and r2['kept'][0]['unit'] == 'US-KY' and 'no Quality grade' in r2['kept'][0]['why']
          and (d / 'data/released/us-key/US-FL.json').read_bytes() == fl2)

    # blocked build: even a YES grade cannot release US-42797939226
    write_key(d, 'data/us-key/US-KY.json', parks(9))
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-42797939226',
        'states': {'KY': {'check': 'ok', 'parks': 9}, 'FL': {'check': 'ok', 'parks': 5}},
        'failed': [], 'held_expected': [],
    })
    sha3 = commit(d, 'blocked')
    g3 = {'RELEASE-READY': 'YES', 'sha': sha3, 'areas': {'US-KY': {'RELEASE-READY': 'YES'}}}
    ky_before = (d / 'data/released/us-key/US-KY.json').read_bytes()
    r3 = R.release_areas(d, sha3, 'US-KY', run='11', now='T11', grade=g3)
    check('US-42797939226 is never released, even with RELEASE-READY: YES',
          r3['promoted'] == [] and 'never released' in r3['kept'][0]['why']
          and (d / 'data/released/us-key/US-KY.json').read_bytes() == ky_before,
          r3)

    # a failed area keeps live and does not block a green neighbour
    write_key(d, 'data/world-key/index.json', {
        'build': 'W-43320000000',
        'countries': {'DE': {'check': 'ok', 'parks': 7}, 'FR': {'check': 'ok', 'parks': 4}},
        'failed': ['FR'], 'held_expected': [],
    })
    write_key(d, 'data/world-key/DE.json', wparks('DE', 8))
    sha4 = commit(d, 'failed-fr')
    g4 = {'RELEASE-READY': 'YES', 'sha': sha4, 'areas': {'DE': {'RELEASE-READY': 'YES'}, 'FR': {'RELEASE-READY': 'YES'}}}
    r4 = R.release_areas(d, sha4, 'DE FR', run='12', now='T12', grade=g4)
    check('a failed area (FR) keeps live and does not block DE',
          {p['unit'] for p in r4['promoted']} == {'DE'} and r4['kept'][0]['unit'] == 'FR'
          and 'failed' in r4['kept'][0]['why']
          and (d / 'data/released/world-key/FR.json').read_bytes() == live_fr)


# 4. end to end (Brandon, 5:10 AM CT Nov 13): one held / broken area never blocks the others;
#    provinces work the same way; only the declared area is rebuilt after a scoped rule change.
import kpc_key_freeze as F
sc, _, _ = F.pending_scope('ca-key', '2a4d0154d95c')
check('only the declared area rebuilds: the CA pin-fill hold is CA-QC only (not a full CA rebuild)',
      sc == {'CA-QC'}, sc)
scw, _, _ = F.pending_scope('world-key', 'a47e0479ad41')
check('world pin-fill hold is scope none: no country is rebuilt for that change',
      scw == set(), scw)
scu, _, _ = F.pending_scope('us-key', 'd4ebfafce438')
check('no new US rule-scope is pending: this work is not a full US rebuild',
      scu in (None, set()), scu)

with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t) / 'r'; d.mkdir()
    sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
    for f in ('data/outlines', 'data/us-key', 'data/ca-key', 'data/world-key', 'data/status/quality'): (d / f).mkdir(parents=True)
    write_outline(d, 'US-KY.geojson.gz'); write_outline(d, 'US-AK.geojson.gz')
    write_key(d, 'data/us-key/US-KY.json', parks(5))
    write_key(d, 'data/us-key/US-AK.json', parks(5))
    write_key(d, 'data/us-key/layers.json', {'layers': []})
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-43100000001',
        'states': {'KY': {'check': 'ok', 'parks': 5, 'matched': 5}, 'AK': {'check': 'ok', 'parks': 5, 'matched': 5}},
        'failed': [], 'held_expected': [],
    })
    write_key(d, 'data/ca-key/CA-AB.json', wparks('CA', 3))
    write_key(d, 'data/ca-key/CA-QC.json', wparks('CA', 3))
    write_key(d, 'data/ca-key/layers.json', {'layers': []})
    write_key(d, 'data/ca-key/refs.json', {'refs': []})
    write_key(d, 'data/ca-key/index.json', {
        'build': 'CA-43300000001',
        'provinces': {'AB': {'check': 'ok', 'parks': 3}, 'QC': {'check': 'ok', 'parks': 3}},
        'failed': [], 'held_expected': [],
    })
    write_key(d, 'data/world-key/DE.json', wparks('DE', 3))
    write_key(d, 'data/world-key/layers.json', {'layers': []})
    write_key(d, 'data/world-key/index.json', {
        'build': 'W-43300000001',
        'countries': {'DE': {'check': 'ok', 'parks': 3}},
        'failed': [], 'held_expected': [],
    })
    sha1 = commit(d, 'live')
    R.release(d, 'US', sha1, run='1', now='T1')
    R.release(d, 'CA', sha1, run='2', now='T2')
    R.release(d, 'world', sha1, run='3', now='T3')
    live_ak = (d / 'data/released/us-key/US-AK.json').read_bytes()
    live_qc = (d / 'data/released/ca-key/CA-QC.json').read_bytes()
    live_ky = (d / 'data/released/us-key/US-KY.json').read_bytes()
    live_ab = (d / 'data/released/ca-key/CA-AB.json').read_bytes()
    live_de = (d / 'data/released/world-key/DE.json').read_bytes()

    # newer: KY, AB, DE grow; QC is held; AK's outline file is not even gzip (a broken neighbour)
    write_key(d, 'data/us-key/US-KY.json', parks(8))
    write_key(d, 'data/ca-key/CA-AB.json', wparks('CA', 5))
    write_key(d, 'data/world-key/DE.json', wparks('DE', 6))
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-43100000002',
        'states': {'KY': {'check': 'ok', 'parks': 8, 'matched': 8}, 'AK': {'check': 'ok', 'parks': 5, 'matched': 5}},
        'failed': [], 'held_expected': [],
    })
    write_key(d, 'data/ca-key/index.json', {
        'build': 'CA-43300000002',
        'provinces': {'AB': {'check': 'ok', 'parks': 5}, 'QC': {'check': 'ok', 'parks': 3}},
        'failed': [], 'held_expected': ['QC'],
    })
    write_key(d, 'data/world-key/index.json', {
        'build': 'W-43300000002',
        'countries': {'DE': {'check': 'ok', 'parks': 6}},
        'failed': [], 'held_expected': [],
    })
    (d / 'data/outlines/US-AK.geojson.gz').write_bytes(b'NOT-GZIP-BROKEN-OUTLINE')
    sha2 = commit(d, 'next')
    grade = {
        'RELEASE-READY': 'PARTIAL', 'sha': sha2,
        'areas': {
            'US-KY': {'RELEASE-READY': 'YES'},
            'US-AK': {'RELEASE-READY': 'YES'},
            'CA-AB': {'RELEASE-READY': 'YES'},
            'CA-QC': {'RELEASE-READY': 'NO'},
            'DE': {'RELEASE-READY': 'YES'},
        },
    }
    gf = d / 'data/status/quality/verdicts.json'
    gf.write_text(json.dumps(grade))

    r = R.release_areas(d, sha2, 'US-KY US-AK CA-AB CA-QC DE', run='20', now='T20', grade=gf)
    check('KY, AB and DE are promoted; held QC and broken AK are kept and do not block the others',
          {p['unit'] for p in r['promoted']} == {'US-KY', 'CA-AB', 'DE'}
          and {k['unit'] for k in r['kept']} == {'US-AK', 'CA-QC'},
          r)
    check('held CA-QC keeps its live bytes and does not block CA-AB',
          (d / 'data/released/ca-key/CA-QC.json').read_bytes() == live_qc
          and (d / 'data/released/ca-key/CA-AB.json').read_bytes() != live_ab)
    check('a broken outline in one state (US-AK) keeps live and does not block US-KY',
          (d / 'data/released/us-key/US-AK.json').read_bytes() == live_ak
          and (d / 'data/released/us-key/US-KY.json').read_bytes() != live_ky)
    check('a US neighbour problem does not block a world country (DE)',
          (d / 'data/released/world-key/DE.json').read_bytes() != live_de)

    # the same list through the owner-run CLI (what kpc-release.yml calls)
    write_key(d, 'data/us-key/US-KY.json', parks(9))
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-43100000003',
        'states': {'KY': {'check': 'ok', 'parks': 9, 'matched': 9}, 'AK': {'check': 'ok', 'parks': 5, 'matched': 5}},
        'failed': [], 'held_expected': [],
    })
    sha3 = commit(d, 'cli')
    grade['sha'] = sha3
    grade['areas']['US-KY'] = {'RELEASE-READY': 'YES'}
    gf.write_text(json.dumps(grade))
    ky_before = (d / 'data/released/us-key/US-KY.json').read_bytes()
    ak_before = (d / 'data/released/us-key/US-AK.json').read_bytes()
    qc_before = (d / 'data/released/ca-key/CA-QC.json').read_bytes()
    env = dict(os.environ, PYTHONPATH=str(ROOT / '.github/scripts'))
    cli = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_release.py'),
                          '--repo', str(d), '--sha', sha3, '--run', '21',
                          '--areas', 'US-KY US-AK CA-QC DE', '--grade', str(gf)],
                         cwd=d, env=env, capture_output=True, text=True)
    check('CLI (the owner-run workflow): exit 0 when at least one area was promoted',
          cli.returncode == 0, cli.stdout[-400:] + cli.stderr[-400:])
    check('CLI: US-KY was promoted and US-AK / CA-QC were kept live (a held or broken area does not fail the job)',
          'US-KY promoted' in cli.stdout and 'US-AK kept live' in cli.stdout and 'CA-QC kept live' in cli.stdout
          and (d / 'data/released/us-key/US-KY.json').read_bytes() != ky_before
          and (d / 'data/released/us-key/US-AK.json').read_bytes() == ak_before
          and (d / 'data/released/ca-key/CA-QC.json').read_bytes() == qc_before,
          cli.stdout[-600:])


# R2, R4, R8, R9, and a 3-area byte/checksum compare (R1 + R7)
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t) / 'r'; d.mkdir()
    sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
    for f in ('data/outlines', 'data/us-key/tracts', 'data/world-key', 'data/status/quality', 'pages'):
        (d / f).mkdir(parents=True)
    def ol(st):
        feat = [{'type': 'Feature', 'properties': {'ref': f'US-{i}', 'g': 'official'},
                 'geometry': {'type': 'Point', 'coordinates': [i, i]}} for i in range(3)]
        (d / 'data/outlines' / f'{st}.geojson.gz').write_bytes(
            R.gz(json.dumps({'type': 'FeatureCollection', 'kpc': {'area': st}, 'features': feat}).encode()))
    for st in ('US-KY', 'US-FL', 'US-AK'):
        ol(st)
        write_key(d, f'data/us-key/{st}.json', {'st': st[-2:], 'parks': {f'US-{i}': {'g': 'official'} for i in range(3)}})
        write_key(d, f'data/us-key/tracts/{st}.json', {'tracts': [st]})
    write_key(d, 'data/us-key/layers.json', {'layers': []})
    write_key(d, 'pages/index.html', {'note': 'a page file release must not touch'})
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-44000000001', 'rules': 'd4ebfafce438',
        'states': {s: {'check': 'ok', 'parks': 3} for s in ('KY', 'FL', 'AK')},
        'failed': [], 'held_expected': [],
    })
    write_key(d, 'data/world-key/DE.json', wparks('DE', 3))
    write_key(d, 'data/world-key/MT.json', wparks('MT', 3))
    write_key(d, 'data/world-key/AU.json', wparks('AU', 3))
    write_key(d, 'data/world-key/layers.json', {'layers': []})
    write_key(d, 'data/outlines/world-expected-holds.approved.json', {
        'holds': {'MT': {'reason': 'test hold', 'approved_by': 'Brandon (KZ4CP)', 'approved_date': '2026-11-11'}}
    })
    write_key(d, 'data/world-key/index.json', {
        'build': 'W-44000000001', 'rules': 'a47e0479ad41',
        'countries': {c: {'check': 'ok', 'parks': 3} for c in ('DE', 'MT', 'AU')},
        'failed': [], 'held_expected': [],
    })
    sha1 = commit(d, 'live')
    R.release(d, 'US', sha1, run='1', now='T1')
    R.release(d, 'world', sha1, run='2', now='T2')
    def rb(rel): return (d / 'data/released' / rel).read_bytes()
    live_fl, live_ak = rb('us-key/US-FL.json'), rb('us-key/US-AK.json')
    live_flo, live_ako = rb('outlines/US-FL.geojson.gz'), rb('outlines/US-AK.geojson.gz')
    live_mt, live_au = rb('world-key/MT.json'), rb('world-key/AU.json')
    live_de = rb('world-key/DE.json')
    live_ky = rb('us-key/US-KY.json')
    tracts = {st: (d / f'data/us-key/tracts/{st}.json').read_bytes() for st in ('US-KY', 'US-FL', 'US-AK')}
    page = (d / 'pages/index.html').read_bytes()

    write_key(d, 'data/us-key/US-KY.json', {'st': 'KY', 'parks': {f'US-{i}': {'g': 'official'} for i in range(5)}})
    write_key(d, 'data/world-key/DE.json', wparks('DE', 5))
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-44000000002', 'rules': 'd4ebfafce438',
        'states': {s: {'check': 'ok', 'parks': 5 if s == 'KY' else 3} for s in ('KY', 'FL', 'AK')},
        'failed': [], 'held_expected': ['FL'],
    })
    write_key(d, 'data/world-key/index.json', {
        'build': 'W-44000000002', 'rules': 'a47e0479ad41',
        'countries': {c: {'check': 'ok', 'parks': 5 if c == 'DE' else 3} for c in ('DE', 'MT', 'AU')},
        'failed': [], 'held_expected': [],
    })
    sha2 = commit(d, 'next')
    grade = {'RELEASE-READY': 'PARTIAL', 'sha': sha2,
             'areas': {u: {'RELEASE-READY': 'YES'} for u in ('US-KY', 'US-FL', 'US-AK', 'DE', 'MT', 'AU')}}
    gf = d / 'data/status/quality/verdicts.json'
    gf.write_text(json.dumps(grade))

    def snap():
        out = {str(p.relative_to(d)): p.read_bytes() for p in (d / 'data/released').rglob('*') if p.is_file()}
        out['pages/index.html'] = (d / 'pages/index.html').read_bytes()
        for st in ('US-KY', 'US-FL', 'US-AK'):
            out[f'data/us-key/tracts/{st}.json'] = (d / f'data/us-key/tracts/{st}.json').read_bytes()
        return out
    before = snap()
    R.release_areas(d, sha2, 'US-KY US-FL US-AK DE MT AU', run='30', now='T30', grade=gf, dry_run=True)
    check('R8: a dry run changes nothing (released files, pages, tracts)', snap() == before)

    # 3-area: only US-KY is named for the US kind; FL is held; AK is not in the list. World: DE yes, MT/AU refused.
    r = R.release_areas(d, sha2, 'US-KY US-FL DE MT AU', run='31', now='T31', grade=gf)
    promoted = {p['unit'] for p in r['promoted']}
    kept = {k['unit']: k['why'] for k in r['kept']}
    check('R7: only KY and DE are promoted in a 3-area run (FL held, MT expected hold, AU until graded)',
          promoted == {'US-KY', 'DE'} and set(kept) >= {'US-FL', 'MT', 'AU'}, r)
    check('R1: held FL keeps live key and outline bytes',
          rb('us-key/US-FL.json') == live_fl and rb('outlines/US-FL.geojson.gz') == live_flo)
    check('R1: AK, not named in this run, keeps live key and outline bytes',
          rb('us-key/US-AK.json') == live_ak and rb('outlines/US-AK.geojson.gz') == live_ako)
    check('R1: pages and tracts are byte-identical after a per-area release',
          (d / 'pages/index.html').read_bytes() == page
          and all((d / f'data/us-key/tracts/{st}.json').read_bytes() == tracts[st] for st in tracts))
    check('R1/R7: promoted KY and DE changed; held MT and AU keep live',
          rb('us-key/US-KY.json') != live_ky and rb('world-key/DE.json') != live_de
          and rb('world-key/MT.json') == live_mt and rb('world-key/AU.json') == live_au)
    check('R4: MT is refused as an expected hold', 'expected hold' in kept.get('MT', ''), kept)
    check('R4: AU is refused until a graded world build', 'graded world build' in kept.get('AU', ''), kept)
    idx = json.loads((d / 'data/released/RELEASED.json').read_text())
    check('R9: live records the build id and the rules hash for each promoted area',
          idx['live']['US-KY']['build'] == 'US-44000000002' and idx['live']['US-KY']['rules'] == 'd4ebfafce438'
          and idx['live']['DE']['build'] == 'W-44000000002' and idx['live']['DE']['rules'] == 'a47e0479ad41'
          and idx['live']['US-FL']['build'] == 'US-44000000001' and idx['live']['US-AK']['build'] == 'US-44000000001',
          idx.get('live'))
    # R3: every manifest checksum matches the file bytes (mixed live + new)
    bad = []
    files = dict(idx.get('files') or {})
    # include sub-index rows if any
    for sub in (idx.get('subs') or {}).values():
        sp = d / 'data/released' / sub['file']
        if sp.is_file():
            files.update(json.loads(sp.read_text()).get('files') or {})
    for rel, parts in files.items():
        for path, ver in parts:
            raw = (d / 'data/released' / path).read_bytes()
            got = __import__('hashlib').sha256(raw).hexdigest()[:12]
            if got != ver: bad.append((path, ver, got))
    check('R3: every RELEASED.json checksum matches the file bytes (mixed builds)', not bad, bad[:5])

    # R2: missing or older key-check is refused (KY would otherwise be green and graded)
    write_key(d, 'data/us-key/US-KY.json', {'st': 'KY', 'parks': {f'US-{i}': {'g': 'official'} for i in range(6)}})
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-44000000003', 'rules': 'd4ebfafce438',
        'states': {s: {'check': 'ok', 'parks': 6 if s == 'KY' else 3} for s in ('KY', 'FL', 'AK')},
        'failed': [], 'held_expected': [],
    })
    # write_key just wrote a PASS check for US-44000000003; replace it with an older build and drop the named file after commit? 
    # after write_key the new check exists. Rewrite it as older, then commit; also leave a last-us.json for the older build.
    (d / 'data/status/key-check/us-US-44000000003.json').unlink()
    write_key(d, 'data/status/key-check/last-us.json', {'key': 'us', 'build': 'US-44000000002', 'gate': 'PASS'})
    sha3 = commit(d, 'older-check')
    grade['sha'] = sha3
    grade['areas']['US-KY'] = {'RELEASE-READY': 'YES'}
    gf.write_text(json.dumps(grade))
    ky_before = rb('us-key/US-KY.json')
    r = R.release_areas(d, sha3, 'US-KY', run='32', now='T32', grade=gf)
    check('R2: an older key-check (last-us on a previous build, named file missing) is refused',
          not r['promoted'] and 'US-KY' in {k['unit'] for k in r['kept']}
          and 'older or other check' in r['kept'][0]['why']
          and rb('us-key/US-KY.json') == ky_before, r)
    # missing check, no last-* either
    write_key(d, 'data/us-key/index.json', {
        'build': 'US-44000000004', 'rules': 'd4ebfafce438',
        'states': {s: {'check': 'ok', 'parks': 6 if s == 'KY' else 3} for s in ('KY', 'FL', 'AK')},
        'failed': [], 'held_expected': [],
    })
    (d / 'data/status/key-check/us-US-44000000004.json').unlink()
    (d / 'data/status/key-check/last-us.json').unlink(missing_ok=True)
    sha4 = commit(d, 'missing-check')
    grade['sha'] = sha4
    gf.write_text(json.dumps(grade))
    r = R.release_areas(d, sha4, 'US-KY', run='33', now='T33', grade=gf)
    check('R2: a missing key-check is refused',
          not r['promoted'] and 'missing check' in r['kept'][0]['why']
          and rb('us-key/US-KY.json') == ky_before, r)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
