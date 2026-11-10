import json
#!/usr/bin/env python3
"""Nov 7 Part 1 (KEY / 2-FER / WORLD handoff): tracts + parks inside parks + the 2-fer switch. Hidden, hash-neutral, OFF by default.

FLAG OFF = byte-identical to origin/main:
  * rules hashes and the rule files / key-rules-version.json / answer keys untouched;
  * kpc_tracts.tract() / doc() / nested_geometry() write exactly what main's module writes (KPC_TRACT_STORE=1), on fixtures and on
    every RI, DE, AL side-file record (DATA);
  * kpc_fers_count.apply() in whole_park hands back the very same object for every 2-fer spot file in DATA/data/fers (94 of them);
  * in node: KPCB.usOutline for every RI, DE, AL park, its KML / GPX / GeoJSON (saveGeo) and the GPS button's GPX / KML / GeoJSON
    (kpc-gps-wire + kpc-gps), saved world outlines (GB), and the Tool Box 'Check all' for RI, DE, AL: same text as main's scripts,
    for a guest, for a member with the switch file off, and for a member with no switch file.
FLAG ON fixtures (both tract modes, one_park and own_park, on the same fixtures):
  a 3-tract park (US-12752 style), a multipart record split by pieces, a nested pair (US-3706 in US-10396), an L-shaped tract
  (shape vs box), overlapping tracts in one MultiPolygon, key twins; the world tract runner (kpc_world_tracts.py) = the world key's
  own _world_tracts() on the same records.
LINKS = this checkout; DATA = a KPC-Data checkout (env DATA, default ../kpc-data). Uses node. No network. Writes only to /tmp."""
import copy, gzip, importlib.util, json, os, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = pathlib.Path(os.environ.get('DATA') or (ROOT.parent / 'kpc-data')).resolve()
BASE = os.environ.get('TRACTS_BASE') or 'origin/main'
SCRIPTS = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
os.environ.pop('KPC_TRACT_MODE', None); os.environ.pop('KPC_FERS_COUNT_MODE', None); os.environ['KPC_TRACT_STORE'] = '1'
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def git_show(rel):
    r = subprocess.run(['git', 'show', f'{BASE}:{rel}'], cwd=ROOT, capture_output=True, timeout=60)
    return r.stdout if r.returncode == 0 else None


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def rect(w, s, e, n): return [[w, s], [e, s], [e, n], [w, n], [w, s]]


TMP = pathlib.Path(tempfile.mkdtemp(prefix='kpc-tracts-nov7-'))
try:
    # ------------------------------------------------------------------ 0. hashes, rule files, keys
    import kpc_key_freeze as KF
    EXP = {'us-key': 'f489a836894f', 'ca-key': '570b09c3cb52', 'world-key': '1b50faf1dfe8'}
    # Combined with the Nov 7 world rebuild (Part 2, Brandon OK'd): that patch moves the world hash by editing kpc_world_key.py
    # only, and declares it in docs/key-rules-change.txt. Tracts (Part 1) must still not touch any rule file, so the declared
    # world change is the one exception: the world hash may be the declared one and kpc_world_key.py may differ from main.
    _decl = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8') if (ROOT / 'docs/key-rules-change.txt').is_file() else ''
    _wdecl = re.search(r'world rules (?:1b50faf1dfe8|6a5969a25d2c) -> ([0-9a-f]{12})', _decl)   # Nov 7 rebuild; Nov 8 CH (#76)
    _wok = {EXP['world-key']} | ({_wdecl.group(1)} if _wdecl else set())
    check('rules hashes unchanged (world: main or the declared world rebuild) ' + json.dumps({k: KF.rules_hash(k) for k in EXP}),
          KF.rules_hash('us-key') == EXP['us-key'] and KF.rules_hash('ca-key') == EXP['ca-key'] and KF.rules_hash('world-key') in _wok)
    rels = sorted(set(sum((v for k, v in KF.RULE_FILES.items() if k != 'fers'), [])))  # Nov 8: fers kind is separate
    if _wdecl: rels = [r for r in rels if not r.endswith('/kpc_world_key.py')]
    have_base = git_show('kpc-bounds.js') is not None
    check(f'{BASE} is readable (the OFF comparisons need it)', have_base)
    check('us/ca/world rule files are byte-identical to ' + BASE, have_base and all(git_show(r) == (ROOT / r).read_bytes() for r in rels))
    _ver = json.loads((ROOT / KF.VERSION_FILE).read_text(encoding='utf-8'))
    check('key-rules-version.json us/ca/world stay v5b (fers kind may be added)',
          _ver.get('us-key') == 'v5b' and _ver.get('ca-key') == 'v5b' and _ver.get('world-key') == 'v5b')
    sys.path.insert(0, str(ROOT / 'tests')); from kpc_moved_sources import moved_sources, apply_moved
    _MOVES = moved_sources(ROOT)
    d = subprocess.run(['git', 'diff', '--quiet', BASE, '--', 'data/us-key', 'data/ca-key', 'data/world-key', 'data/ky-answer-key.json',
                        ':!data/us-key/overrides.json',   # round 3: the hand-override ledger may gain a declared row (US-3917)
                        # Nov 7 evening bundle: the layer lists and 'rebuild tonight' lists are inputs, not answer keys
                        ':!data/*/answers-states.txt', ':!data/*/answers-provinces.txt', ':!data/*/answers-countries.txt',
                        ':!data/world-key/extra-layers.json',
                        # Nov 8 (#76): a declared moved source (docs/key-rules-change.txt) is checked just below
                        *([':!data/world-key/layers.json', ':!data/world-key/sheet-countries.json'] if _MOVES else [])], cwd=ROOT)
    for _f in (['data/world-key/layers.json', 'data/world-key/sheet-countries.json'] if _MOVES else []):
        _b = git_show(_f)
        check(f'{_f}: only the declared moved source(s) differ from ' + BASE,
              _b is not None and apply_moved(_b.decode('utf-8'), _MOVES) == (ROOT / _f).read_text(encoding='utf-8'))
    check('answer keys in this repo are byte-identical to ' + BASE + ' (the declared overrides ledger aside)', d.returncode == 0)
    check('the world tract runner is listed as NOT a rule file', 'kpc_world_tracts.py' in KF.NOT_RULES and 'kpc_tracts.py' in KF.NOT_RULES)
    wf = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / '.github' / 'workflows').glob('*.yml'))
    check('no workflow runs the world tract runner (by hand only; no new cron)', 'kpc_world_tracts' not in wf)
    sw = json.loads((ROOT / 'data/tract-switch.json').read_text(encoding='utf-8'))
    check('data/tract-switch.json ships OFF: on false, mode whole_park, tract_mode one_park', (sw['on'], sw['mode'], sw['tract_mode']) == (False, 'whole_park', 'one_park'))

    import kpc_tracts as TR
    import kpc_fers_count as FC
    OLD = TMP / 'old'; OLD.mkdir()
    for f in ('kpc-bounds.js', 'kpc-gps.js', 'kpc-gps-wire.js', 'kpc-maprep-logic.js', 'kpc-maprep-candidates.js', 'kpc-maprep-check.js', 'kpc-maprep-toolbox.js',
              '.github/scripts/kpc_tracts.py', '.github/scripts/kpc_fers_count.py'):
        b = git_show(f) if have_base else None
        (OLD / pathlib.Path(f).name).write_bytes(b if b is not None else (ROOT / f).read_bytes())
    (OLD / 'data/maprep').mkdir(parents=True)
    for f in (ROOT / 'data/maprep').glob('*.json'): shutil.copy(f, OLD / 'data/maprep' / f.name)
    TRo = load_mod('kpc_tracts_main', OLD / 'kpc_tracts.py')
    FCo = load_mod('kpc_fers_count_main', OLD / 'kpc_fers_count.py')

    # ------------------------------------------------------------------ 1. OFF: the side-file writer is unchanged
    FIX = {   # ref -> [(rid, name, rings)]
        'US-12752': [('sgx1', 'Davis Bend', [rect(-86.00, 37.00, -85.96, 37.03), rect(-85.99, 37.01, -85.98, 37.02)[::-1]]),
                     ('sgx2', 'Green River Tract B', [rect(-85.80, 37.00, -85.78, 37.02)]),
                     ('sgx3', 'Green River Tract C', [rect(-85.60, 37.10, -85.59, 37.11)])],
        'US-9001': [(99001, 'Two Piece Refuge', [rect(-85.00, 37.00, -84.97, 37.02), rect(-84.70, 37.00, -84.69, 37.01)])],
        'US-10396': [('sgx263', 'Black Warrior Wildlife Management Area', [rect(-87.50, 34.20, -87.20, 34.45)])],
        'US-3706': [('wld397', 'Sipsey Wilderness', [rect(-87.45, 34.28, -87.35, 34.39)])],
        'US-9002': [(99002, 'L Shaped Area', [[[-86.5, 36.0], [-86.3, 36.0], [-86.3, 36.02], [-86.48, 36.02], [-86.48, 36.2], [-86.5, 36.2], [-86.5, 36.0]]])],
        'US-9003': [(99003, 'Overlap Pieces', [rect(-85.50, 36.00, -85.48, 36.02), rect(-85.49, 36.01, -85.47, 36.03)])],
        'US-9004': [(99041, 'Twin Refuge', [rect(-84.0, 36.0, -83.99, 36.01)]), (99042, 'Twin Refuge', [rect(-84.0, 36.0, -83.99, 36.01)])],
    }

    def side(mod, store):
        os.environ['KPC_TRACT_STORE'] = store
        PT, SH = {}, {}
        for ref, recs in FIX.items():
            PT[ref] = [mod.tract(rid, nm, 'name', {}, None, rings, 'Fixture layer', src_key='fixture') for rid, nm, rings in recs]
            SH[ref] = [r for _, _, rg in recs for r in rg]
        d = mod.doc('US-ZZ', PT, mod.nested_geometry(SH), 'fixture')
        os.environ['KPC_TRACT_STORE'] = '1'
        return d

    new1, old1 = side(TR, '1'), side(TRo, '1')
    check('KPC_TRACT_STORE=1: the fixture side file is exactly what main writes', json.dumps(new1, sort_keys=True) == json.dumps(old1, sort_keys=True))
    check('KPC_TRACT_STORE=1: no tract carries a shape', not any('shape' in t for ts in new1['parks'].values() for t in ts))
    real_same, real_n = True, 0
    for st in ('RI', 'DE', 'AL'):
        sd = TR.load(DATA / f'data/us-key/tracts/US-{st}.json') or {}
        PT, PTo, SH = {}, {}, {}
        for ref, ts in (sd.get('parks') or {}).items():
            for t in ts:
                rg = [rect(*t['box'])] if t.get('box') and t['box'][2] > t['box'][0] and t['box'][3] > t['box'][1] else None
                PT.setdefault(ref, []).append(TR.tract(t.get('rid'), t.get('name'), t.get('how'), {}, None, rg, t.get('layer'), src_key=t.get('src')))
                PTo.setdefault(ref, []).append(TRo.tract(t.get('rid'), t.get('name'), t.get('how'), {}, None, rg, t.get('layer'), src_key=t.get('src')))
                if rg: SH.setdefault(ref, []).extend(rg)
                real_n += 1
        a = TR.doc(f'US-{st}', PT, TR.nested_geometry(SH)); b = TRo.doc(f'US-{st}', PTo, TRo.nested_geometry(SH))
        real_same &= json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    check(f'KPC_TRACT_STORE=1: RI, DE, AL side files rebuilt from {real_n} records are exactly what main writes', real_same and real_n > 100)

    # ------------------------------------------------------------------ 2. OFF: every 2-fer spot file, whole_park
    files = sorted(p for p in (DATA / 'data/fers').glob('*.json*'))
    n_spot, same = 0, True
    for f in files:
        try:
            op = gzip.open if f.suffix == '.gz' else open
            with op(f, 'rt', encoding='utf-8') as h: dd = json.load(h)
        except Exception: continue  # noqa: BLE001
        if not isinstance(dd, dict) or not isinstance(dd.get('spots'), list): continue
        n_spot += 1
        raw = json.dumps(dd, sort_keys=True)
        x = FC.apply(f, dd, 'whole_park', {}); y = FC.apply(f, dd)
        same &= x is dd and y is dd and json.dumps(dd, sort_keys=True) == raw and json.dumps(FCo.apply(f, json.loads(raw), 'whole_park', {}), sort_keys=True) == raw
    check(f'whole_park (default): all {n_spot} 2-fer spot files come back as the very same object, byte-identical', same and n_spot == 94)
    check('default KPC_FERS_COUNT_MODE is whole_park', FC.MODE == 'whole_park')

    # ------------------------------------------------------------------ 3. ON (Python): read-time tracts, shapes, both tract modes
    shp = side(TR, 'shapes')
    check('KPC_TRACT_STORE=shapes adds a thinned shape to each tract and nothing else', all('shape' in t for ts in shp['parks'].values() for t in ts)
          and json.dumps({r: [{k: v for k, v in t.items() if k != 'shape'} for t in ts] for r, ts in shp['parks'].items()}, sort_keys=True) == json.dumps(new1['parks'], sort_keys=True))
    check('nested pair found from the shapes: US-3706 inside US-10396', any(x['child'] == 'US-3706' and x['parent'] == 'US-10396' for x in new1['nested']))
    s3 = TR.split('US-12752', shp['parks']['US-12752'])
    check('3-tract park: ids US-12752#1..#3, largest first', [t['id'] for t in s3] == ['US-12752#1', 'US-12752#2', 'US-12752#3'] and [t['rid'] for t in s3] == ['sgx1', 'sgx2', 'sgx3'])
    mp = TR.split('US-9001', shp['parks']['US-9001']); mp0 = TR.split('US-9001', new1['parks']['US-9001'])
    check('multipart record (pieces 2, 27 km apart) is split by its shape into 2 tracts', shp['parks']['US-9001'][0]['pieces'] == 2 and len(mp) == 2 and mp[0]['ac'] > mp[1]['ac'] and mp[0]['part'] in (1, 2) and not mp[0].get('approx_split'))
    check('without a shape the multipart record still gives 2 tracts, marked approx_split', len(mp0) == 2 and all(t.get('approx_split') for t in mp0))
    check('key twins are left out (two records, one twin -> 1 tract)', len(TR.split('US-9004', new1['parks']['US-9004'], ['99042'])) == 1 and len(TR.split('US-9004', new1['parks']['US-9004'])) == 2)
    L = TR.split('US-9002', shp['parks']['US-9002'])[0]; Lb = TR.split('US-9002', new1['parks']['US-9002'])[0]
    check('L-shaped tract: a spot in the empty corner of its box is NOT in the tract by shape (box says yes)', TR.at(L, 36.15, -86.35) == (False, 'shape') and TR.at(Lb, 36.15, -86.35) == (True, 'box') and TR.at(L, 36.01, -86.4) == (True, 'shape'))
    O = TR.split('US-9003', shp['parks']['US-9003'])[0]
    import kpc_pin_edge as PE
    check('overlapping tracts in one record: inside where they overlap (even-odd would say outside)', TR.in_shape(O['shape'], 36.015, -85.485) and not PE.inside(36.015, -85.485, O['shape']) and not TR.in_shape(O['shape'], 36.035, -85.475))
    D = shp['parks']['US-12752'][0]
    check('a hole stays a hole (Davis Bend has a hole)', not TR.in_shape(D['shape'], 37.015, -85.985) and TR.in_shape(D['shape'], 37.005, -85.995))

    def spotfile():
        return {'st': 'US-ZZ', 'spots': [
            {'id': 's1', 'refs': ['US-12752', 'US-5555'], 'center': [37.01, -85.79], 'status': 'candidate', 'shape': []},
            {'id': 's2', 'refs': ['US-12752', 'US-5555'], 'center': [37.105, -85.595], 'status': 'candidate', 'shape': []},
            {'id': 's3', 'refs': ['US-9002', 'US-5557'], 'center': [36.15, -86.35], 'status': 'candidate', 'shape': []},
            {'id': 's4', 'refs': ['US-9003', 'US-5558'], 'center': [36.015, -85.485], 'status': 'candidate', 'shape': []},
            {'id': 's5', 'refs': ['US-9001', 'US-5559'], 'center': [37.005, -84.695], 'status': 'candidate', 'shape': []},
            {'id': 's6', 'refs': ['US-9001', 'US-5559'], 'center': [37.01, -84.985], 'status': 'candidate', 'shape': []},
            {'id': 's7', 'refs': ['US-9002', 'US-5560'], 'center': [30.0, -80.0], 'status': 'candidate', 'shape': [[-86.495, 36.1], [-86.49, 36.1]]}]}

    res = {}
    for store, doc_ in (('1', new1), ('shapes', shp)):
        dd = TMP / f'side-{store}' / 'data' / 'us-key' / 'tracts'; dd.mkdir(parents=True)
        (dd / 'US-ZZ.json').write_text(json.dumps(doc_), encoding='utf-8')
        (dd.parent / 'US-ZZ.json').write_text(json.dumps({'parks': {'US-9004': {'twin': ['99042']}}}), encoding='utf-8')
        IDX = TR.index([str(dd)], twins=True)
        for tm in ('one_park', 'own_park'):
            os.environ['KPC_TRACT_MODE'] = tm
            res[(store, tm)] = FC.apply('US-ZZ.json', spotfile(), 'tracts', IDX)
            res[(store, tm, 'n')] = FC.apply('US-ZZ.json', spotfile(), 'nested', IDX)
        os.environ.pop('KPC_TRACT_MODE')
    a = res[('shapes', 'one_park')]; S = {s['id']: s.get('tracts') for s in a['spots']}
    check('tracts mode (shapes): each spot names its tract ' + json.dumps(S), S['s1'] == {'US-12752': ['US-12752#2']} and S['s2'] == {'US-12752': ['US-12752#3']}
          and S['s3'] is None and S['s4'] == {'US-9003': ['US-9003#1']} and len(set(S['s5']['US-9001'] + S['s6']['US-9001'])) == 2)
    check('a spot whose centre misses is placed by its own outline points (s7)', S['s7'] == {'US-9002': ['US-9002#1']})
    b = res[('1', 'one_park')]; Sb = {s['id']: s.get('tracts') for s in b['spots']}
    check('tracts mode (boxes only, KPC_TRACT_STORE=1): the L-shape corner spot is still labelled (the old box rule)', Sb['s3'] == {'US-9002': ['US-9002#1']} and b['tract_basis'].get('box') and not b['tract_basis'].get('shape'))
    check(f"one_park: count = park combos ({a['count_parks']}), own_park: count = tract combos ({res[('shapes', 'own_park')]['count_tracts']})",
          a['tract_mode'] == 'one_park' and a['count'] == a['count_parks'] == 5 and res[('shapes', 'own_park')]['tract_mode'] == 'own_park'
          and res[('shapes', 'own_park')]['count'] == res[('shapes', 'own_park')]['count_tracts'] == 6)
    check('tracts mode changes no status and drops / adds no spot', all([s['status'] for s in res[k]['spots']] == ['candidate'] * 7 for k in res if len(k) == 2))
    n = res[('shapes', 'one_park', 'n')]
    check('nested mode lists US-10396 / US-3706 although no spot row holds them (spots 0)', {'parent': 'US-10396', 'child': 'US-3706', 'spots': 0} in [{k: x[k] for k in ('parent', 'child', 'spots')} for x in n['nested_pairs']])
    check('the same answers in both tract modes for nested (tract_mode only changes the tracts count)', res[('shapes', 'one_park', 'n')] == res[('shapes', 'own_park', 'n')])
    os.environ['KPC_TRACT_MODE'] = 'bogus'
    check('KPC_TRACT_MODE: bad value -> switch file -> one_park; env beats the file', TR.tract_mode() == 'one_park')
    os.environ['KPC_TRACT_MODE'] = 'own_park'
    check('KPC_TRACT_MODE=own_park', TR.tract_mode() == 'own_park')
    os.environ.pop('KPC_TRACT_MODE')
    swf = TMP / 'sw.json'; swf.write_text(json.dumps({'on': True, 'mode': 'tracts', 'tract_mode': 'own_park'}))
    check('switch file is read (on, mode, tract_mode) and env still wins', TR.switch([swf]) == {'on': True, 'mode': 'tracts', 'tract_mode': 'own_park'} and TR.tract_mode([swf]) == 'own_park')

    # ------------------------------------------------------------------ 4. world tract runner = the world key's own writer, on the same records
    import kpc_world_tracts as WT
    W = TMP / 'world'; (W / 'data/world-key').mkdir(parents=True); (W / 'cache/world').mkdir(parents=True)
    wkey = {'cc': 'NZ', 'parks': {'NZ-9901': {'n': 'Fixture Forest', 'm': [[11, 'Fixture Forest', 'Fixture DOC layer', 'name'], [12, 'Fixture Forest East', 'Fixture DOC layer', 'name']]},
                                  'NZ-9902': {'n': 'Inner Reserve', 'm': [[13, 'Inner Reserve', 'Fixture DOC layer', 'name']]},
                                  'NZ-9903': {'n': 'No Shape', 'm': [[None, 'Something', 'Unknown', 'pin']]}}}
    recs = [{'src': 'Fixture DOC layer', 'id': 11, 'n': 'Fixture Forest', '_a': {'SITE_ID': 'A1', 'Hectares': 100.0}, '_r': [rect(172.0, -41.0, 172.2, -40.8)]},
            {'src': 'Fixture DOC layer', 'id': 12, 'n': 'Fixture Forest East', '_a': {'SITE_ID': 'A2'}, '_r': [rect(172.5, -41.0, 172.6, -40.9), rect(173.5, -41.0, 173.6, -40.9)]},
            {'src': 'Fixture DOC layer', 'id': 13, 'n': 'Inner Reserve', '_a': {}, '_r': [rect(172.05, -40.95, 172.1, -40.9)]}]
    (W / 'data/world-key/NZ.json').write_text(json.dumps(wkey)); (W / 'data/world-key/layers.json').write_text(json.dumps({'Fixture DOC layer': 'https://fixture.example/doc/FeatureServer/0'}))
    with gzip.open(W / 'cache/world/W-NZ.json.gz', 'wt', encoding='utf-8') as h: json.dump({'cc': 'NZ', 'recs': recs}, h)
    st_, path_, how_ = WT.run('NZ', out=str(W / 'data/world-key'), cache=str(W / 'cache/world'), wb=str(W / 'data/world-bounds'))
    got = json.loads(pathlib.Path(path_).read_text()) if path_ else {}
    cwd = os.getcwd(); os.chdir(W)
    try:
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            KW = load_mod('kpc_world_key_fixture', SCRIPTS / 'kpc_world_key.py')
            KW.OUT = W / 'ref'; KW.SRC = {'NZ': [('Fixture DOC layer', 'arcgis', 'https://fixture.example/doc/FeatureServer/0')]}
            KW._world_tracts('NZ', copy.deepcopy(wkey['parks']), copy.deepcopy(recs))
    finally: os.chdir(cwd)
    ref_ = json.loads((W / 'ref/tracts/NZ.json').read_text()) if (W / 'ref/tracts/NZ.json').exists() else None
    strip = lambda x: {k: v for k, v in (x or {}).items() if k not in ('built', 'from')}  # noqa: E731
    check(f'world runner ({st_}, {how_}) writes what the world key itself writes for the same records', st_ == 'written' and how_ == 'record cache' and ref_ is not None and strip(got) == strip(ref_))
    check('world runner: tracts, pieces and a park inside a park', len(got['parks']['NZ-9901']) == 2 and got['parks']['NZ-9901'][1].get('pieces') == 2 and any(x['child'] == 'NZ-9902' and x['parent'] == 'NZ-9901' for x in got['nested']))
    check('world runner --check: nothing written, file the same', WT.run('NZ', out=str(W / 'data/world-key'), cache=str(W / 'cache/world'), check=True)[0] == 'same')
    (W / 'cache/world/W-NZ.json.gz').unlink()
    (W / 'data/world-bounds/NZ').mkdir(parents=True)
    (W / 'data/world-bounds/NZ/99.json').write_text(json.dumps({'NZ-9902': {'n': 'Inner Reserve', 's': 'Fixture DOC layer', 'r': [rect(172.05, -40.95, 172.1, -40.9)]}}))
    before = pathlib.Path(path_).read_bytes()
    held = WT.run('NZ', out=str(W / 'data/world-key'), cache=str(W / 'cache/world'), wb=str(W / 'data/world-bounds'))
    check('world runner never replaces a record-cache file with a poorer saved-outline one (held unless --force)', held[0].startswith('held: existing file is better') and pathlib.Path(path_).read_bytes() == before
          and WT.run('NZ', out=str(W / 'data/world-key'), cache=str(W / 'cache/world'), wb=str(W / 'data/world-bounds'), check=True, force=True)[0] == 'would change')
    check('world runner with no record cache and no saved outlines HOLDS (writes nothing) unless --labels-only',
          WT.run('NZ', out=str(W / 'data/world-key'), cache=str(W / 'cache/world'), wb=str(W / 'nowb'))[0] == 'held'
          and WT.run('NZ', out=str(W / 'data/world-key'), cache=str(W / 'cache/world'), wb=str(W / 'nowb'), labels_only=True, check=True)[2] == 'key rows only')
    os.environ['KPC_TRACT_STORE'] = '0'
    check('world runner: KPC_TRACT_STORE=0 = off', WT.run('NZ', out=str(W / 'data/world-key'))[0] == 'off')
    os.environ['KPC_TRACT_STORE'] = '1'

    # ------------------------------------------------------------------ 5. node: OFF byte-identical, ON fixtures
    lay = {'sgx': ['https://fixture.example/sgx/MapServer/0/query', 'NAME', 'Fixture state layer']}
    zz_key = {'parks': {
        'US-12752': {'n': 'Green River State Natural Area', 'g': 'official', 'bk': ['sgx1', 0.0, '', '-'], 'm': [['sgx1', 'Davis Bend', 300, 'name'], ['sgx2', 'Green River Tract B', 120, 'name'], ['sgx3', 'Green River Tract C', 20, 'name']]},
        'US-9001': {'n': 'Two Piece Refuge', 'g': 'official', 'm': [[99001, 'Two Piece Refuge', 900, 'name']]},
        'US-10396': {'n': 'Black Warrior WMA', 'g': 'official', 'm': [['sgx263', 'Black Warrior Wildlife Management Area', 90268, 'name']]},
        'US-3706': {'n': 'Sipsey Wilderness', 'g': 'official', 'm': [['wld397', 'Sipsey Wilderness', 25851, 'name']]},
        'US-9004': {'n': 'Twin Refuge', 'g': 'official', 'twin': ['99042'], 'm': [[99041, 'Twin Refuge', 24, 'name'], [99042, 'Twin Refuge', 24, 'name']]}}}

    def gj(rings):   # flat fixture rings -> GeoJSON: each ring its own polygon, except a ring inside the first one = its hole
        polys = []
        for r in rings:
            if polys and TR._in_ring(r[0][0], r[0][1], polys[0][0]) and abs(TR._signed(r)) < abs(TR._signed(polys[0][0])): polys[0].append(r)
            else: polys.append([r])
        return {'type': 'Polygon', 'coordinates': polys[0]} if len(polys) == 1 else {'type': 'MultiPolygon', 'coordinates': polys}
    geom = {}
    for ref, rs in FIX.items():
        for rid, nm, rings in rs: geom['*|' + str(rid).lstrip('sgxwld')] = gj(rings)
    fx = {'files': {'data/us-key/US-ZZ.json': zz_key, 'data/us-key/tracts/US-ZZ.json': new1, 'data/us-key/layers.json': lay}, 'geom': geom}
    big = {'parks': {f'US-{8000 + i}': {'n': f'Park {i}', 'm': []} for i in range(450)}}
    big['parks'].update(zz_key['parks'])
    fx_tb = {'files': {'data/us-key/US-RI.json': big, 'data/us-key/tracts/US-RI.json': new1}}
    # a saved world outline with a hole (a ring inside the outer ring) and a park whose saved outline is a ring inside a ring
    wfx = {'files': {'data/world-key/NZ.json': {'parks': {'NZ-9911': {'n': 'Holey Park', 'm': [[1, 'Holey Park', 'Fixture saved', 'name']]}}}, 'data/world-key/layers.json': {},
                     'data/world-bounds/NZ/99.json': {'NZ-9911': {'n': 'Holey Park', 's': 'Fixture saved', 'r': [rect(172.0, -41.0, 172.2, -40.8), rect(172.05, -40.95, 172.1, -40.9)]}},
                     'data/world-key/tracts/NZ.json': {'parks': {'NZ-9911': [{'rid': 1, 'name': 'Holey Park', 'pieces': 1, 'ac_measured': 100, 'box': [172.0, -41.0, 172.2, -40.8]}]}, 'nested': []}}, 'only': False}
    gb_refs = sorted(sorted(TR.load(DATA / 'data/world-bounds/GB/10.json') or {})[:20] + sorted(TR.load(DATA / 'data/world-bounds/GB/13.json') or {})[:20])
    MEMBER_OFF = {'member': True, 'switchDoc': {'on': False, 'mode': 'whole_park', 'tract_mode': 'one_park'}}
    ON = {'member': True, 'search': '?tracts=1', 'switchDoc': {'on': False, 'mode': 'whole_park', 'tract_mode': 'one_park'}}
    ON_OWN = {'member': True, 'switchDoc': {'on': True, 'mode': 'tracts', 'tract_mode': 'own_park'}}
    tasks = []
    for st in ('RI', 'DE', 'AL'):
        for tag, opt in (('guest', {}), ('member', MEMBER_OFF), ('noswitch', {'member': True})):
            tasks += [{'id': f'us-{st}-{tag}', 'kind': 'us', 'st': st, 'opt': opt}, {'id': f'us-{st}-{tag}-old', 'kind': 'us', 'st': st, 'opt': opt, 'old': True},
                      {'id': f'tb-{st}-{tag}', 'kind': 'toolbox', 'code': st, 'opt': opt}, {'id': f'tb-{st}-{tag}-old', 'kind': 'toolbox', 'code': st, 'opt': opt, 'old': True}]
    tasks += [{'id': 'gb', 'kind': 'world', 'cc': 'GB', 'refs': gb_refs, 'opt': MEMBER_OFF}, {'id': 'gb-old', 'kind': 'world', 'cc': 'GB', 'refs': gb_refs, 'opt': MEMBER_OFF, 'old': True}]
    tasks += [{'id': 'sw-guest-url', 'kind': 'switch', 'opt': {'search': '?tracts=1', 'switchDoc': {'on': True}}},
              {'id': 'sw-member-off', 'kind': 'switch', 'opt': MEMBER_OFF}, {'id': 'sw-member-none', 'kind': 'switch', 'opt': {'member': True}},
              {'id': 'sw-member-url', 'kind': 'switch', 'opt': ON}, {'id': 'sw-member-ls', 'kind': 'switch', 'opt': {'member': True, 'ls': {'kpcMapTracts': '1'}}},
              {'id': 'sw-member-file', 'kind': 'switch', 'opt': ON_OWN}, {'id': 'sw-nonmember-ls', 'kind': 'switch', 'opt': {'member': False, 'ls': {'kpcMapTracts': '1'}}},
              {'id': 'sw-ls-mode', 'kind': 'switch', 'opt': dict(ON, ls={'kpcTractMode': 'own_park'})}]
    for tag, opt in (('off', dict(MEMBER_OFF, fx=fx)), ('on', dict(ON, fx=fx)), ('own', dict(ON_OWN, fx=fx))):
        tasks.append({'id': f'zz-{tag}', 'kind': 'us', 'st': 'ZZ', 'opt': opt})
    tasks.append({'id': 'zz-off-old', 'kind': 'us', 'st': 'ZZ', 'opt': dict(MEMBER_OFF, fx=fx), 'old': True})
    for tag, opt in (('off', dict(MEMBER_OFF, fx=fx_tb)), ('on', dict(ON, fx=fx_tb)), ('own', dict(ON_OWN, fx=fx_tb))):
        tasks.append({'id': f'tbzz-{tag}', 'kind': 'toolbox', 'code': 'RI', 'opt': opt})
    tasks.append({'id': 'tbzz-off-old', 'kind': 'toolbox', 'code': 'RI', 'opt': dict(MEMBER_OFF, fx=fx_tb), 'old': True})
    hp = {'NZ-9911': [[-40.92, 172.07], [-40.85, 172.15]]}
    for tag, opt in (('off', dict(MEMBER_OFF, fx=wfx, holePoints=hp)), ('on', dict(ON, fx=wfx, holePoints=hp))):
        tasks.append({'id': f'nz-{tag}', 'kind': 'world', 'cc': 'NZ', 'refs': ['NZ-9911'], 'opt': opt})
    over = {'type': 'MultiPolygon', 'coordinates': [[rect(-85.50, 36.00, -85.48, 36.02)], [rect(-85.49, 36.01, -85.47, 36.03)]]}
    pins = [{'ref': 'US-10396', 'lat': 36.005, 'lon': -85.495}, {'ref': 'US-3706', 'lat': 36.015, 'lon': -85.485}, {'ref': 'US-1', 'lat': 30, 'lon': -80}]
    for tag, opt in (('off', MEMBER_OFF), ('on', ON)):
        tasks.append({'id': f'logic-{tag}', 'kind': 'logic', 'opt': opt, 'geom': over, 'pt': [36.015, -85.485], 'pins': pins})
    big_ring = [[-86 + 0.05 * __import__('math').cos(i / 400 * 6.283), 37 + 0.05 * __import__('math').sin(i / 400 * 6.283)] for i in range(400)] + [[-85.95, 37.0]]
    small = [rect(-85.0 + i * 0.1, 37.0, -84.9999 + i * 0.1, 37.0001) for i in range(3)]
    feats = [{'type': 'Feature', 'properties': {'tract': 'US-9100#1', 'tracts_total': 4}, 'geometry': {'type': 'Polygon', 'coordinates': [big_ring]}}] + \
            [{'type': 'Feature', 'properties': {'tract': f'US-9100#{i + 2}', 'tracts_total': 4}, 'geometry': {'type': 'Polygon', 'coordinates': [r]}} for i, r in enumerate(small)]
    tasks.append({'id': 'simplify', 'kind': 'simplify', 'polys': [[big_ring]] + [[r] for r in small], 'tracts': ['a', 'b', 'c', 'd'], 'max': 12, 'features': feats})
    job = TMP / 'job.json'
    job.write_text(json.dumps({'root': str(ROOT), 'old': str(OLD), 'data': str(DATA), 'tasks': tasks}))
    r = subprocess.run(['node', str(ROOT / 'tests/fixtures/tracts_nov7/harness.js'), str(job)], cwd=TMP, capture_output=True, text=True, timeout=170)
    check('node harness ran: ' + (r.stderr.strip().splitlines() or ['ok'])[-1][:200], r.returncode == 0)
    o = json.loads(r.stdout or '{}')
    errs = {k: v['error'][:300] for k, v in o.items() if isinstance(v, dict) and 'error' in v}
    check('no harness task failed ' + json.dumps(errs)[:600], not errs)
    if not errs and o:
        for st in ('RI', 'DE', 'AL'):
            for tag in ('guest', 'member', 'noswitch'):
                a_, b_ = o[f'us-{st}-{tag}'], o[f'us-{st}-{tag}-old']
                nfiles = sum(1 for v in a_.values() if v['files']); ngps = sum(1 for v in a_.values() if v['gps'] and v['gps']['outline'].get('status') != 'pin')
                check(f'OFF ({tag}) {st}: usOutline + KML/GPX/GeoJSON for {len(a_)} parks ({nfiles} with outlines, {ngps} GPS files) byte-identical to {BASE}',
                      json.dumps(a_, sort_keys=True) == json.dumps(b_, sort_keys=True) and nfiles > 0 and ngps > 0)
                ta, tb = o[f'tb-{st}-{tag}'], o[f'tb-{st}-{tag}-old']
                check(f'OFF ({tag}) {st}: Tool Box Check all ({ta["n"]} parks) byte-identical to {BASE}', ta['html'] == tb['html'] and ta['n'] == tb['n'] > 0 and not ta['tractsOn'])
        ngb = sum(1 for v in o['gb'].values() if v['files'])
        check(f'OFF: {len(gb_refs)} GB world parks ({ngb} saved outlines) + their KML/GPX/GeoJSON byte-identical to {BASE}', json.dumps(o['gb'], sort_keys=True) == json.dumps(o['gb-old'], sort_keys=True) and ngb >= 20)
        sw = {k[3:]: v for k, v in o.items() if k.startswith('sw-')}
        check('switch: a guest with ?tracts=1 (and the file on) stays OFF', not sw['guest-url']['on'] and not sw['guest-url']['logic'])
        check('switch: a member with the file off / no file stays OFF', not sw['member-off']['on'] and not sw['member-none']['on'] and not sw['member-off']['logic'])
        check('switch: a member with ?tracts=1, localStorage kpcMapTracts=1 or the file on is ON; KPCMapLogic.tractsOn() follows KPCB', sw['member-url']['on'] and sw['member-ls']['on'] and sw['member-file']['on'] and sw['member-url']['logic'] and sw['member-file']['logic'])
        check('switch: not a member + localStorage = OFF', not sw['nonmember-ls']['on'])
        check('switch: tract_mode one_park by default, own_park from the file or localStorage kpcTractMode; count mode from the file', sw['member-url']['mode'] == 'one_park' and sw['member-file']['mode'] == 'own_park' and sw['ls-mode']['mode'] == 'own_park' and sw['member-file']['count'] == 'tracts' and sw['member-url']['count'] == 'whole_park')
        zoff, zold, zon, zown = o['zz-off'], o['zz-off-old'], o['zz-on'], o['zz-own']
        check('OFF fixture: same as main (no tract fields, one feature per record)', json.dumps(zoff, sort_keys=True) == json.dumps(zold, sort_keys=True) and 'tract' not in json.dumps(zoff['US-12752']['u']))
        T = lambda z, ref: [(f['properties'].get('tract'), f['properties'].get('tracts_total'), f['properties'].get('parent')) for f in z[ref]['u']['fs']]  # noqa: E731
        check('ON: 3-tract park -> US-12752#1..#3 (largest first), tracts_total 3 ' + json.dumps(T(zon, 'US-12752')),
              T(zon, 'US-12752') == [('US-12752#1', 3, None), ('US-12752#2', 3, None), ('US-12752#3', 3, None)] and [f['_tractRec']['rid'] for f in zon['US-12752']['u']['fs']] == ['sgx1', 'sgx2', 'sgx3'])
        check('ON: the multipart record is split into one feature per piece ' + json.dumps(T(zon, 'US-9001')), T(zon, 'US-9001') == [('US-9001#1', 2, None), ('US-9001#2', 2, None)] and len(T(zoff, 'US-9001')) == 1)
        check('ON: the child park carries parent US-10396; the parent none', T(zon, 'US-3706') == [('US-3706#1', 1, 'US-10396')] and T(zon, 'US-10396') == [('US-10396#1', 1, None)])
        check('ON: key twins stay out (one tract)', T(zon, 'US-9004') == [('US-9004#1', 1, None)])
        check('ON: both tract modes give the same outline labels', json.dumps(zon, sort_keys=True) == json.dumps(zown, sort_keys=True))
        g_on, g_off = zon['US-12752']['files']['gpx'], zoff['US-12752']['files']['gpx']
        check('ON: GPX names each track by tract and writes the hole (OFF: outer rings only, as before)', 'tract 1 of 3' in g_on and g_on.count('<trkseg>') == g_off.count('<trkseg>') + 1 and 'tract' not in g_off)
        check('ON: KML Placemarks name the tract and the parent', 'tract 2 of 3' in zon['US-12752']['files']['kml'] and 'inside US-10396' in zon['US-3706']['files']['kml'])
        gj_on = json.loads(zon['US-12752']['files']['geojson'])
        check('ON: GeoJSON features carry properties.tract', [f['properties']['tract'] for f in gj_on['features']] == ['US-12752#1', 'US-12752#2', 'US-12752#3'])
        go = zon['US-3706']['gps']['outline']['geojson']['features'][0]['properties']
        check('ON: the GPS button outline (kpc-gps-wire fc) keeps tract, tracts_total, parent', go == {'name': 'Sipsey Wilderness', 'tract': 'US-3706#1', 'tracts_total': 1, 'parent': 'US-10396'}
              and zoff['US-3706']['gps']['outline']['geojson']['features'][0]['properties'] == {'name': 'Sipsey Wilderness'})
        a_, b_ = o['tbzz-off'], o['tbzz-off-old']
        check('Tool Box OFF with 455 parks: unchanged (first 400 + the old note)', a_['html'] == b_['html'] and 'The first 400 names are listed.' in a_['html'])
        on_, own_ = o['tbzz-on'], o['tbzz-own']
        check('Tool Box ON: rows say "3 tracts" and "inside US-10396"', 'US-12752 · 3 tracts' in on_['rows2'] and 'US-3706 · inside US-10396' in on_['rows2'] and 'US-9001 · 2 tracts' in on_['rows2'])
        check('Tool Box ON: no 400-row cut, SHOW MORE pages the rest', on_['rows'].count('<p>') == 400 and 'Show more (400 of 455)' in on_['more'] and on_['rows2'].count('<p>') == 455)
        check('Tool Box ON one_park: no tract is offered as a new park', 'possible new park' not in on_['rows'] + (on_['rows2'] or ''))
        allr = own_['rows2'] or own_['rows']
        check('Tool Box ON own_park: the other tracts are "possible new park (tract of <ref>)", the pin tract keeps the number',
              allr.count('possible new park (tract of US-12752)') == 2 and 'US-12752#1 · possible' not in allr and allr.count('possible new park (tract of US-9001)') == 1)
        check('Tool Box page text keeps the hidden-UI words out', 'SHOW TRACTS' not in on_['html'] and 'PARK NUMBER FOR TRACTS' not in on_['html'])
        nz_off, nz_on = o['nz-off']['NZ-9911'], o['nz-on']['NZ-9911']
        check('world saved outline: OFF unchanged (the inner ring reads as land, the old way); ON the inner ring is a hole', nz_off['inHole'] == [True, True] and nz_on['inHole'] == [False, True]
              and nz_on['w']['fs'][0]['properties']['tract'] == 'NZ-9911#1')
        lo_, ln_ = o['logic-off'], o['logic-on']
        check('Map Rep insideGeom: OFF even-odd as before (overlap = outside); ON inside any polygon (overlap = inside)', lo_['inOverlap'] is False and ln_['inOverlap'] is True and lo_['insideAny'] is True and lo_['kpcbInside'] is True)
        check('alreadyParks returns every pin (parent and child); alreadyPark still the first; pinCheck lists all only when ON',
              ln_['parks'] == ['US-10396', 'US-3706'] and lo_['first'] == 'US-10396' and 'US-3706' in ln_['pinCheck']['text'] and 'US-3706' not in lo_['pinCheck']['text'])
        sp = o['simplify']
        kept_off = len(sp['off']['polys']); kept_on = len(sp['on']['polys'])
        check(f'simplifyOutline: OFF leaves small tracts out ({kept_off} of 4 kept, as before); with tract ids every tract keeps a ring ({kept_on} of 4)', kept_off < 4 and kept_on == 4)
        check('the GPS park file keeps every tract when the outline is tract-labelled', sp['park']['gpx'].count('<trkseg>') == 4 and 'small pieces left out' not in sp['park']['gpx'])
finally:
    shutil.rmtree(TMP, ignore_errors=True)
    try:   # kpc_save notes every file it wrote in data/status/<script>.json at exit: these were all in /tmp, so note none
        import kpc_save
        for k in [k for k in kpc_save._changed if k.startswith(str(TMP))]: kpc_save._changed.pop(k, None)
    except Exception: pass  # noqa: BLE001

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
