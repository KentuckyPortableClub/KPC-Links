#!/usr/bin/env python3
"""Nov 11 (KPC owner, 2026-11-11), job 3 part 2: the world key join takes each COUNTRY from the build part that owns it and fails closed
(exit 1, nothing written) on any conflict, like kpc_us_key_join.py. Before: the four shared files (layers / eea-designations / jp-wikidata /
outline-test) were "the biggest copy wins". Two-group cases for every output, plus a snapshot check that a failed join writes nothing."""
import json, os, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_world_key_join as J  # noqa: E402
ok = True


def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)


def snap(*dirs):
    out = {}
    for d in dirs:
        for p in sorted(pathlib.Path(d).rglob('*')):
            if p.is_file(): out[str(p)] = p.read_bytes()
    return out


def setup(t):
    o = t / 'world-key'; (o / 'review').mkdir(parents=True)
    (o / 'index.json').write_text(json.dumps({'countries': {'AU': {'p': 'old'}, 'DE': {'p': 'old'}}, 'build': 'b1'}))
    (o / 'AU.json').write_text('{"old": "AU"}'); (o / 'DE.json').write_text('{"old": "DE"}')
    (o / 'layers.json').write_text(json.dumps({'srcA': 'u1'}, indent=1))
    (o / 'eea-designations.json').write_text('{\n"AD00": "old"\n}')
    (o / 'jp-wikidata.json').write_text(json.dumps({'JP-0001': [['Q1', '利尻']]}, ensure_ascii=False, separators=(',', ':')))
    (o / 'outline-test.json').write_text(json.dumps({'CH': {'outlines': 1}}, indent=1))
    b = t / 'world-bounds'; (b / 'AU').mkdir(parents=True); (b / 'AU' / 'old.txt').write_text('old'); (b / 'DE').mkdir(); (b / 'DE' / 'old.txt').write_text('old')
    return o, b


def mkpart(t, i, countries, *, failed=(), shared=None, extra=None, countries_txt=True):
    d = t / 'parts' / f'world-key-part-{i}'; (d / 'world-key' / 'review').mkdir(parents=True); (d / 'world-bounds').mkdir()
    if countries_txt: (d / 'countries.txt').write_text(' '.join(countries) + '\n')
    (d / 'failed.txt').write_text(''.join(f + '\n' for f in failed))
    (d / 'world-key' / 'index.json').write_text(json.dumps({'countries': {c: {'p': f'new{i}'} for c in countries}}))
    for c in countries:
        (d / 'world-key' / f'{c}.json').write_text(json.dumps({'new': i, 'c': c}))
        (d / 'world-key' / 'review' / f'{c}.md').write_text(f'review {c} {i}')
        (d / 'world-bounds' / c).mkdir(); (d / 'world-bounds' / c / f'new{i}.txt').write_text('new')
    for name, body in (shared or {}).items(): (d / 'world-key' / name).write_text(body)
    for name, body in (extra or {}).items(): (d / name).parent.mkdir(parents=True, exist_ok=True); (d / name).write_text(body)
    return d


def run(t, parts, failed_out=None):
    here = os.getcwd(); os.chdir(t)   # kpc_save writes its status file under ./data/status: keep it in the temp dir
    try: return J.main([str(p) for p in parts] + ['--out', str(t / 'world-key'), '--bounds', str(t / 'world-bounds'), '--failed-out', str(failed_out or t / 'failed.txt')])
    finally:
        import kpc_save
        kpc_save.flush_status()   # while still in the temp dir: the status file must not land in the repo (the suite counts that as a dirty run)
        os.chdir(here)


def j(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))


# 1) the good join: each country from its owner; the shared files take what each part CHANGED (no "biggest copy wins")
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); o, b = setup(t)
    base_layers, base_eea = (o / 'layers.json').read_text(), (o / 'eea-designations.json').read_text()
    p0 = mkpart(t, 0, ['AU'], failed=['JP'], shared={
        'layers.json': json.dumps({'srcA': 'u1', 'srcAU': 'u2'}, indent=1),                       # part 0 adds a layer source
        'eea-designations.json': base_eea,                                                         # unchanged copy
        'jp-wikidata.json': json.dumps({'JP-0001': [['Q1', '利尻']], 'JP-0002': [['Q2', '知床']]}, ensure_ascii=False, separators=(',', ':'))})
    p1 = mkpart(t, 1, ['DE'], shared={
        'layers.json': json.dumps({'srcA': 'u1', 'srcDE': 'u3', 'junk1': 'x' * 400, 'junk2': 'y' * 400}, indent=1),   # the BIGGER copy, a different addition
        'eea-designations.json': '{\n"AD00": "old",\n"AD01": "new"\n}',
        'outline-test.json': json.dumps({'CH': {'outlines': 1}, 'DE': {'outlines': 7}}, indent=1)})
    rc = run(t, [p0, p1])
    check('two groups join: exit 0', rc == 0)
    check('AU file + review from its owner, DE file + review from its owner', j(o / 'AU.json') == {'new': 0, 'c': 'AU'} and j(o / 'DE.json') == {'new': 1, 'c': 'DE'}
          and (o / 'review' / 'AU.md').read_text() == 'review AU 0' and (o / 'review' / 'DE.md').read_text() == 'review DE 1')
    check('world-bounds replaced per owned country', (b / 'AU' / 'new0.txt').is_file() and not (b / 'AU' / 'old.txt').exists() and (b / 'DE' / 'new1.txt').is_file() and not (b / 'DE' / 'old.txt').exists())
    idx = j(o / 'index.json')
    check('index rows: each country from its owner; the old build id is kept as previous_build',
          idx['countries']['AU'] == {'p': 'new0'} and idx['countries']['DE'] == {'p': 'new1'} and idx.get('previous_build') == 'b1')
    lay = j(o / 'layers.json')
    check('layers.json: both parts\' additions are in (the bigger copy does not win)', lay.get('srcAU') == 'u2' and lay.get('srcDE') == 'u3' and lay.get('srcA') == 'u1' and 'junk1' in lay)
    check('eea-designations.json: the one changing part\'s bytes, as it wrote them', (o / 'eea-designations.json').read_text() == '{\n"AD00": "old",\n"AD01": "new"\n}')
    check('jp-wikidata.json: the one changing part\'s bytes (non-ASCII kept)', (o / 'jp-wikidata.json').read_text().count('知床') == 1 and 'JP-0002' in (o / 'jp-wikidata.json').read_text())
    check('outline-test.json: DE added by its owner', j(o / 'outline-test.json').get('DE') == {'outlines': 7})
    check('failed list is written', (t / 'failed.txt').read_text() == 'JP\n')

# 2) conflicts: exit 1 and NOTHING written (a snapshot of the out folders is unchanged)
def conflict(name, build):
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td); o, b = setup(t); parts = build(t)
        before = snap(o, b); rc = run(t, parts)
        check(f'{name}: exit 1', rc == 1)
        check(f'{name}: nothing written (key, review, bounds, index, shared files all unchanged)', snap(o, b) == before and not (t / 'failed.txt').exists())


conflict('one country in two parts', lambda t: [mkpart(t, 0, ['AU', 'DE']), mkpart(t, 1, ['DE'])])
conflict('a part carries a country file it does not own', lambda t: [mkpart(t, 0, ['AU'], extra={'world-key/DE.json': '{"stale": 1}'}), mkpart(t, 1, ['DE'])])
conflict('a part carries a review file it does not own', lambda t: [mkpart(t, 0, ['AU'], extra={'world-key/review/DE.md': 'stale'}), mkpart(t, 1, ['DE'])])
conflict('a part carries a tracts file it does not own', lambda t: [mkpart(t, 0, ['AU'], extra={'world-key/tracts/DE.json': '{}'}), mkpart(t, 1, ['DE'])])
conflict('a part carries world-bounds it does not own', lambda t: [mkpart(t, 0, ['AU'], extra={'world-bounds/DE/stale.txt': 'x'}), mkpart(t, 1, ['DE'])])
conflict('a part with no countries.txt that carries a country', lambda t: [mkpart(t, 0, ['AU'], countries_txt=False), mkpart(t, 1, ['DE'])])
conflict('one shared key written differently by two parts',
         lambda t: [mkpart(t, 0, ['AU'], shared={'layers.json': json.dumps({'srcA': 'FROM0'})}), mkpart(t, 1, ['DE'], shared={'layers.json': json.dumps({'srcA': 'FROM1'})})])
conflict('outline-test changed for a country the part does not own',
         lambda t: [mkpart(t, 0, ['AU'], shared={'outline-test.json': json.dumps({'CH': {'outlines': 1}, 'DE': {'outlines': 9}})}), mkpart(t, 1, ['DE'])])
conflict('a conflict in the second part still writes nothing from the first',
         lambda t: [mkpart(t, 0, ['AU'], shared={'jp-wikidata.json': json.dumps({'JP-0001': 'a'})}), mkpart(t, 1, ['DE'], shared={'jp-wikidata.json': json.dumps({'JP-0001': 'b'})})])

# 2b) a conflict says built=0 to the workflow, so Save / stamp / world-bounds (always() && built != '0') do not run
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); o, b = setup(t); go = t / 'gh-output'; go.write_text('')
    os.environ['GITHUB_OUTPUT'] = str(go)
    try: rc = run(t, [mkpart(t, 0, ['AU', 'DE']), mkpart(t, 1, ['DE'])])
    finally: os.environ.pop('GITHUB_OUTPUT', None)
    check('conflict: GITHUB_OUTPUT gets built=0 (the save steps are skipped)', rc == 1 and 'built=0' in go.read_text())

# 2c) a merge of two writers is written the way the key writes it (sorted keys, kpc_save.canon), not in arrival order
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); o, b = setup(t)
    import kpc_save
    p0 = mkpart(t, 0, ['AU'], shared={'layers.json': kpc_save.canon({'srcA': 'u1', 'zz': 'a'}, 1)})
    p1 = mkpart(t, 1, ['DE'], shared={'layers.json': kpc_save.canon({'srcA': 'u1', 'bb': 'b'}, 1)})
    rc = run(t, [p0, p1])
    check('merged layers.json: same bytes the key writer would give', rc == 0 and (o / 'layers.json').read_text() == kpc_save.canon({'bb': 'b', 'srcA': 'u1', 'zz': 'a'}, 1))

# 2d) a json.dump file (unsorted) keeps its key order and format when two parts merge into it (no re-sort diff)
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); o, b = setup(t)
    (o / 'outline-test.json').write_text(json.dumps({'JP': {'o': 1}, 'CH': {'o': 1}}, indent=1))
    p0 = mkpart(t, 0, ['AU'], shared={'outline-test.json': json.dumps({'JP': {'o': 1}, 'CH': {'o': 1}, 'AU': {'o': 2}}, indent=1)})
    p1 = mkpart(t, 1, ['DE'], shared={'outline-test.json': json.dumps({'JP': {'o': 1}, 'CH': {'o': 1}, 'DE': {'o': 3}}, indent=1)})
    rc = run(t, [p0, p1])
    check('merged outline-test.json: checkout order kept, new keys after, json.dump format',
          rc == 0 and (o / 'outline-test.json').read_text() == json.dumps({'JP': {'o': 1}, 'CH': {'o': 1}, 'AU': {'o': 2}, 'DE': {'o': 3}}, indent=1))

# 3) the same new value from two parts is not a conflict; a stale copy of the checkout is not a write
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); o, b = setup(t)
    same = json.dumps({'srcA': 'u1', 'srcNew': 'same'}, indent=1)
    p0 = mkpart(t, 0, ['AU'], shared={'layers.json': same, 'eea-designations.json': '{\n"AD00": "STALE"\n}'})
    p1 = mkpart(t, 1, ['DE'], shared={'layers.json': same, 'eea-designations.json': (o / 'eea-designations.json').read_text()})
    rc = run(t, [p0, p1])
    check('two parts writing the same value: exit 0, merged once', rc == 0 and j(o / 'layers.json') == {'srcA': 'u1', 'srcNew': 'same'})
    check('a part\'s differing copy is still a write when only it differs (the other equals the checkout)', j(o / 'eea-designations.json') == {'AD00': 'STALE'})

# 4) a non-object shared file is a whole-file write; two different ones conflict
conflict('two different whole-file writes of a non-object shared file',
         lambda t: [mkpart(t, 0, ['AU'], shared={'outline-test.json': '[1]'}), mkpart(t, 1, ['DE'], shared={'outline-test.json': '[2]'})])

# 5) no key change at all: the join does not touch the shared files (no noisy diff)
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); o, b = setup(t)
    sh = {n: (o / n).read_text() for n in J.SHARED}
    p0 = mkpart(t, 0, ['AU'], shared=sh); p1 = mkpart(t, 1, ['DE'], shared=sh)
    before = {n: (o / n).stat().st_mtime_ns for n in J.SHARED}
    rc = run(t, [p0, p1])
    check('unchanged shared copies: exit 0 and the shared files are not rewritten', rc == 0 and {n: (o / n).stat().st_mtime_ns for n in J.SHARED} == before)

# 6) the workflow runs this script (not the old inline "biggest copy wins")
wf = (ROOT / '.github/workflows/kpc-world-key.yml').read_text()
check('workflow calls kpc_world_key_join.py and the old size rule is gone', 'kpc_world_key_join.py parts/world-key-part-*' in wf and 'the biggest copy wins' not in wf)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
