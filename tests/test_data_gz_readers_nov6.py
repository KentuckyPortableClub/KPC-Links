#!/usr/bin/env python3
"""Nov 6: KPC-Links readers of the KPC-Data files that are now stored as .gz.

Each reader below is run twice, once on a plain-only tree and once on a gz-only tree,
and the decision it writes is the same. When both copies exist, .gz wins. A checkout
that is missing the expected file exits 1 and does not pretend the file was empty.

kpc_ca_hardlook.py is part of the Canada rules hash, so it is not edited. The workflow
materializes the preferred bytes onto the plain path first. That path is tested here.
Rules hashes stay us a066624520b4, ca 8feccbb7d9ee, world 1b50faf1dfe8 (6a5969a25d2c since the Nov 7 world rebuild).
KPC_RESEARCH_SOURCES stays off. Offline.
"""
import gzip, json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = HERE / '.github/scripts'
sys.path.insert(0, str(SCRIPTS))
os.environ.pop('KPC_RESEARCH_SOURCES', None)
os.environ.pop('KPC_ANSWERS_SKIP', None)
os.environ.pop('KPC_ANSWERS_TO', None)

import kpc_json_any as J  # noqa: E402
import kpc_key_freeze as KZ  # noqa: E402
import kpc_research_sources as RS  # noqa: E402

ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg)
    ok = ok and bool(c)


def gz_bytes(obj):
    raw = json.dumps(obj).encode('utf-8')
    return gzip.compress(raw, compresslevel=9, mtime=0)


def put(path, obj, mode):
    """mode: plain, gz, or both (gz bytes differ when obj is a pair (plain, gz))."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plain, packed = obj if isinstance(obj, tuple) else (obj, obj)
    if mode in ('plain', 'both'):
        path.write_text(json.dumps(plain), encoding='utf-8')
    if mode in ('gz', 'both'):
        path.with_name(path.name + '.gz').write_bytes(gz_bytes(packed))
        if mode == 'gz' and path.exists():
            path.unlink()


def run(script, cwd, env, args=None):
    e = dict(os.environ)
    e.pop('KPC_RESEARCH_SOURCES', None)
    e.update(env)
    return subprocess.run([sys.executable, str(SCRIPTS / script), *(args or [])], cwd=cwd, env=e, capture_output=True, text=True)


LAYER = {
    'area': 'US-KY', 'url': 'https://maps.example.gov/arcgis/rest/services/Parks/MapServer/3',
    'name_field': 'NAME', 'agency': 'Kentucky', 'kind': 'park', 'answer': 'YES',
    'checked_by': 'chat 11', 'ref': 'US-1',
}
LAYER_GZ = dict(LAYER, url='https://maps.example.gov/arcgis/rest/services/Parks/MapServer/9')
EXT_URL = 'https://apps.example.fs.usda.gov/arcx/rest/services/EDW/EDW_TrailNFSPublish_01/MapServer/0'
AREA_URL = 'https://maps.example.gov/arcgis/rest/services/Areas/MapServer/1'


def ext(result='SURE', url=AREA_URL, geometry='esriGeometryPolygon', ref='US-1', name='Alpha WMA'):
    return {'pairs': {f'{ref}|{url}': {'result': result, 'record_name': name}},
            'layers': {url: {'geometry': geometry, 'name_field': 'NAME', 'title': 'Areas', 'host': 'example.gov'}}}


def question(ref, answer, **extra):
    row = {'ref': ref, 'answer': answer, 'checked_by': 'chat 11'}
    row.update(extra)
    return {'questions': [row]}


# ---- rules hash and the research switch are untouched ----
# Nov 7 world rebuild (B1 B2 B3 B4 B6, world-failed-diagnosis.md section 7; Brandon OK'd the world hash move): kpc_world_key.py
# changed on purpose, so the world rules hash moved 1b50faf1dfe8 -> 6a5969a25d2c. US and CA stay; this check still pins all three.
check((KZ.rules_hash('us-key'), KZ.rules_hash('ca-key'), KZ.rules_hash('world-key')) == ('da660f0d5ae7', 'b1a521708978', '1a8913a378bb'),
      'rules hashes stay us da660f0d5ae7, ca b1a521708978, world 1a8913a378bb')
check(RS.mode() == 'off', 'KPC_RESEARCH_SOURCES still defaults to off')
check(any(str(p).endswith('kpc_ca_hardlook.py') for p in KZ.RULE_FILES['ca-key']),
      'Canada hard look stays a rules file (this patch does not edit it)')

# ---- helper: plain, gz, both, missing ----
with tempfile.TemporaryDirectory() as t:
    root = pathlib.Path(t)
    put(root / 'only.json', {'n': 1}, 'plain')
    check(J.load_json_any(root / 'only.json') == {'n': 1}, 'load_json_any reads a plain file when no .gz exists')
    put(root / 'only.json', ({'n': 1}, {'n': 2}), 'both')
    check(J.load_json_any(root / 'only.json') == {'n': 2}, 'load_json_any prefers .gz when both exist')
    (root / 'only.json').unlink()
    check(J.load_json_any(root / 'only.json') == {'n': 2} and J.exists_any(root / 'only.json'), 'load_json_any reads a gz-only file; exists_any sees it')
    try:
        J.load_json_any(root / 'missing.json')
        check(False, 'a missing file raises MissingInput')
    except J.MissingInput:
        check(True, 'a missing file raises MissingInput')
    (root / 'q').mkdir()
    put(root / 'q' / 'gis-hunter.json', {'questions': [{'ref': 'US-1'}]}, 'gz')
    put(root / 'q' / 'map-audit.json', {'questions': [{'ref': 'US-2'}]}, 'plain')
    found = [pathlib.Path(p).name for p in J.glob_json_any(str(root / 'q' / '*.json'))]
    check(found == ['gis-hunter.json', 'map-audit.json'], 'glob_json_any returns one logical name per file, plain and .gz')
    (root / 'log.jsonl.gz').write_bytes(gzip.compress(b'{"l":1}\n{"l":2}\n', mtime=0))
    check([r['l'] for r in J.iter_jsonl_any(root / 'log.jsonl')] == [1, 2], 'iter_jsonl_any reads a gz-only log')
    try:
        list(J.iter_jsonl_any(root / 'nope.jsonl'))
        check(False, 'a missing jsonl raises MissingInput')
    except J.MissingInput:
        check(True, 'a missing jsonl raises MissingInput')


def work():
    d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-gz-'))
    (d / 'data' / 'us-key').mkdir(parents=True)
    (d / 'data' / 'ca-key').mkdir(parents=True)
    (d / 'data' / 'world-key').mkdir(parents=True)
    (d / 'data' / 'parkinfo').mkdir()
    (d / 'data' / 'trails').mkdir()
    (d / 'key').mkdir()
    return d


def seed_parks(d):
    json.dump({'parks': {'US-1': {'n': 'Alpha WMA', 'm': []}}}, open(d / 'data/us-key/US-KY.json', 'w'))
    # US-2 is not a trail pin; US-1 is a trail pin for finds_lines
    json.dump({'parks': {'US-1': ['Alpha National Recreation Trail', '', 'National Recreation Trail', '', '', '38.0', '-84.0']}},
              open(d / 'data/parkinfo/US-KY.json', 'w'))


def data_tree(mode, layers=None, ready=None, external=None, questions=None, world=None):
    root = pathlib.Path(tempfile.mkdtemp(prefix='kpc-data-'))
    q = root / 'data' / 'waiting' / 'questions'
    q.mkdir(parents=True)
    (root / 'data' / 'intake').mkdir()
    if layers is not None:
        if isinstance(layers, tuple):
            put(q / 'layers.json', ({'questions': [layers[0]]}, {'questions': [layers[1]]}), 'both')
        else:
            put(q / 'layers.json', {'questions': [layers]}, mode)
    if ready is not None:
        put(root / 'data/intake/ready.json', {'questions': [ready]}, 'gz' if mode == 'gz' else mode)
    if external is not None:
        put(root / 'data/intake/external-results.json', external, mode if not isinstance(external, tuple) else 'both')
    for name, obj in (questions or {}).items():
        put(q / name, obj, mode if not isinstance(obj, tuple) else 'both')
    if world is not None:
        put(q / 'world-finder.json', world, mode if not isinstance(world, tuple) else 'both')
    return root


# ---- BOT W: layers.json and ready.json, plain and gz ----
def wired(d):
    p = d / 'data/state-gis.json'
    if not p.exists():
        return []
    return [(x.get('url'), st) for st, rows in json.loads(p.read_text()).get('states', {}).items() for x in rows]


for mode in ('plain', 'gz'):
    d, data = work(), data_tree(mode, layers=LAYER)
    r = run('kpc_key_layers.py', d, {'DATA': str(data)})
    got = wired(d)
    check(r.returncode == 0 and got == [(LAYER['url'], 'KY')], f'kpc_key_layers wires the same layer from a {mode}-only layers.json ({r.stdout.strip()[:140]})')

d, data = work(), data_tree('both', layers=(LAYER, LAYER_GZ))
r = run('kpc_key_layers.py', d, {'DATA': str(data)})
check(r.returncode == 0 and wired(d) == [(LAYER_GZ['url'], 'KY')], 'kpc_key_layers prefers layers.json.gz when the plain file is also there')

d, data = work(), data_tree('gz', ready=LAYER)
r = run('kpc_key_layers.py', d, {'DATA': str(data)})
check(r.returncode == 0 and wired(d) == [(LAYER['url'], 'KY')], 'kpc_key_layers reads ready.json.gz when the plain ready.json is absent')

d, data = work(), data_tree('plain')
r = run('kpc_key_layers.py', d, {'DATA': str(data)})
check(r.returncode == 1 and '::error' in r.stdout and not (d / 'data/state-gis.json').exists(),
      'kpc_key_layers fails when layers.json, queue.json and ready.json are all missing')

# queue.json is not one of the gzipped files; a plain copy is still read
d, data = work(), data_tree('plain')
put(data / 'data/intake/queue.json', {'questions': [LAYER]}, 'plain')
r = run('kpc_key_layers.py', d, {'DATA': str(data)})
check(r.returncode == 0 and wired(d) == [(LAYER['url'], 'KY')], 'kpc_key_layers still reads a plain queue.json')


# ---- lost finds: external-results + question globs ----
def lost_b(d):
    doc = json.loads((d / 'data/us-key/lost-finds.json').read_text())
    return doc['counts']['B_sure_area_not_asked'], [row[0] for row in doc['B']]


for mode in ('plain', 'gz'):
    d = work(); seed_parks(d)
    data = data_tree(mode, external=ext(), questions={})
    r = run('kpc_lost_finds.py', d, {'DATA': str(data)})
    check(r.returncode == 0 and lost_b(d) == (1, ['US-1']), f'kpc_lost_finds counts the same SURE area from a {mode}-only external-results.json')

d = work(); seed_parks(d)
data = data_tree('gz', external=ext(), questions={'gis-hunter.json': question('US-1', 'NO')})
r = run('kpc_lost_finds.py', d, {'DATA': str(data)})
check(r.returncode == 0 and lost_b(d) == (0, []), 'kpc_lost_finds reads a NO from a gz-only question file and does not list that park')

d = work(); seed_parks(d)
data = data_tree('both', external=(ext('MAYBE'), ext('SURE')))
r = run('kpc_lost_finds.py', d, {'DATA': str(data)})
check(r.returncode == 0 and lost_b(d) == (1, ['US-1']), 'kpc_lost_finds prefers external-results.json.gz over the plain file')

d = work(); seed_parks(d)
data = data_tree('plain')
r = run('kpc_lost_finds.py', d, {'DATA': str(data)})
check(r.returncode == 0 and '::error' not in r.stdout and lost_b(d) == (0, []),
      'kpc_lost_finds treats a missing external-results file as {} and still writes the report')
(data / 'data/waiting/questions/notes.md.gz').write_bytes(gzip.compress(b'# notes\n', mtime=0))
r = run('kpc_lost_finds.py', d, {'DATA': str(data)})
check(r.returncode == 1 and '::error' in r.stdout, 'kpc_lost_finds still fails when the questions directory has no question JSON')


# ---- found trail lines ----
def finds(d, out):
    return [row['ref'] for row in json.loads(pathlib.Path(out).read_text())]


trail_ext = ext(url=EXT_URL, geometry='esriGeometryPolyline', name='Alpha National Recreation Trail')
for mode in ('plain', 'gz'):
    d = work(); seed_parks(d)
    data = data_tree(mode, external=trail_ext)
    out = d / 'finds.json'
    r = run('kpc_finds_lines.py', d, {'DATA': str(data)}, [str(out)])
    check(r.returncode == 0 and finds(d, out) == ['US-1'], f'kpc_finds_lines hands off the same trail from a {mode}-only external-results.json')

d = work(); seed_parks(d)
data = data_tree('gz', external=trail_ext, questions={'gis-hunter.json': question('US-1', 'NO', layer=EXT_URL)})
out = d / 'finds.json'
r = run('kpc_finds_lines.py', d, {'DATA': str(data)}, [str(out)])
check(r.returncode == 0 and finds(d, out) == [], 'kpc_finds_lines honors a NO stored only as questions/*.json.gz')

d = work(); seed_parks(d)
data = data_tree('plain')
out = d / 'finds.json'
r = run('kpc_finds_lines.py', d, {'DATA': str(data)}, [str(out)])
check(r.returncode == 0 and '::error' not in r.stdout and finds(d, out) == [] and (d / 'data/status/finds-lines-report.json').exists(),
      'kpc_finds_lines treats a missing external-results file as {} and writes an empty hand-off')
(data / 'data/waiting/questions/notes.md.gz').write_bytes(gzip.compress(b'# notes\n', mtime=0))
r = run('kpc_finds_lines.py', d, {'DATA': str(data)}, [str(out)])
check(r.returncode == 1 and '::error' in r.stdout, 'kpc_finds_lines still fails when the questions directory has no question JSON')


# ---- US answers: question glob, skip stem, prefer gz, empty dir still walks ----
US_Q = question('US-1', 'YES', record='111', record_name='Alpha WMA', acres=10, area='US-KY')


def joins(key):
    p = json.loads((key / 'overrides.json').read_text()).get('parks', {})
    return {ref: v.get('join') for ref, v in p.items()}


for mode in ('plain', 'gz'):
    d = work()
    data = data_tree(mode, questions={'gis-hunter.json': US_Q})
    r = run('kpc_key_answers.py', d, {'DATA': str(data), 'KEY_DIR': str(d / 'key')})
    check(r.returncode == 0 and joins(d / 'key') == {'US-1': ['111']}, f'kpc_key_answers applies the same YES from a {mode}-only question file')
    led = json.loads((d / 'key' / 'answers-applied.json').read_text())
    check(any(k.startswith('gis-hunter:US-1:') for k in led) and not any('gis-hunter.json' in k for k in led),
          f'the answers ledger keeps the plain stem on a {mode}-only file')

d = work()
data = data_tree('both', questions={'gis-hunter.json': (question('US-1', 'NO', record='111', record_name='Alpha', acres=1, area='US-KY'), US_Q)})
r = run('kpc_key_answers.py', d, {'DATA': str(data), 'KEY_DIR': str(d / 'key')})
check(r.returncode == 0 and joins(d / 'key') == {'US-1': ['111']}, 'kpc_key_answers prefers the .gz question file when the plain file disagrees')

d = work()
data = data_tree('gz', questions={
    'gis-hunter.json': US_Q,
    'map-audit.json': question('US-2', 'YES', record='222', record_name='Beta', acres=2, area='US-KY'),
})
r = run('kpc_key_answers.py', d, {'DATA': str(data), 'KEY_DIR': str(d / 'key')})
check(r.returncode == 0 and joins(d / 'key') == {'US-1': ['111']} and 'map-audit' in r.stdout,
      'KPC_ANSWERS_SKIP still skips map-audit when that file is only map-audit.json.gz')

d = work()
data = data_tree('plain')
(d / 'key' / 'overrides.json').write_text(json.dumps({'parks': {'US-9': {'join': ['a1'], 'none': True,
    'why': "x · 2026-10-29 23:15: gis-hunter row YES 'Alpha Lake' (chat 11; applied by kpc_key_answers)"}}}))
r = run('kpc_key_answers.py', d, {'DATA': str(data), 'KEY_DIR': str(d / 'key')})
parks = json.loads((d / 'key' / 'overrides.json').read_text())['parks']
check(r.returncode == 0 and 'none' not in parks['US-9'], 'an empty questions directory is still no new rows, and the override walk still runs')

d = work()
data = data_tree('plain')
(data / 'data/waiting/questions/gis-hunter.md.gz').write_bytes(gzip.compress(b'# notes\n', mtime=0))
r = run('kpc_key_answers.py', d, {'DATA': str(data), 'KEY_DIR': str(d / 'key')})
check(r.returncode == 1 and '::error' in r.stdout, 'question files that are not *.json or *.json.gz are a missing input, not an empty read')


# ---- Canada answers ----
CA_Q = question('CA-1', 'YES', record_name='Alpha Park', area='CA-ON')
for mode in ('plain', 'gz'):
    d = work()
    data = data_tree(mode, questions={'gis-hunter.json': CA_Q})
    r = run('kpc_ca_answers.py', d, {'DATA': str(data)})
    p = d / 'data/ca-key/overrides.json'
    parks = json.loads(p.read_text()).get('parks', {}) if p.exists() else {}
    check(r.returncode == 0 and parks.get('CA-1', {}).get('join') == ['Alpha Park'],
          f'kpc_ca_answers applies the same Canada YES from a {mode}-only question file')

d = work()
data = data_tree('gz', questions={'map-audit.json': question('CA-2', 'YES', record_name='Skipped', area='CA-ON'),
                                  'gis-hunter.json': CA_Q})
r = run('kpc_ca_answers.py', d, {'DATA': str(data)})
parks = json.loads((d / 'data/ca-key/overrides.json').read_text()).get('parks', {})
check(r.returncode == 0 and 'CA-2' not in parks and parks.get('CA-1', {}).get('join') == ['Alpha Park'],
      'kpc_ca_answers skips map-audit.json.gz and still reads the other gz question file')


# ---- world answers ----
W_Q = question('AU-1', 'YES', record_name='Kakadu', area='AU', layer='official parks')
for mode in ('plain', 'gz'):
    d = work()
    data = data_tree(mode, world=W_Q)
    r = run('kpc_world_answers.py', d, {'DATA': str(data)})
    p = d / 'data/world-key/overrides.json'
    parks = json.loads(p.read_text()).get('parks', {}) if p.exists() else {}
    check(r.returncode == 0 and parks.get('AU-1', {}).get('join') == ['Kakadu'],
          f'kpc_world_answers applies the same YES from a {mode}-only world-finder.json')

d = work()
data = data_tree('both', world=(question('AU-1', 'NO', record_name='Kakadu', area='AU', layer='official'), W_Q))
r = run('kpc_world_answers.py', d, {'DATA': str(data)})
parks = json.loads((d / 'data/world-key/overrides.json').read_text()).get('parks', {})
check(r.returncode == 0 and parks.get('AU-1', {}).get('join') == ['Kakadu'] and 'Kakadu' not in parks.get('AU-1', {}).get('no', []),
      'kpc_world_answers prefers world-finder.json.gz')

d = work()
data = data_tree('plain')
r = run('kpc_world_answers.py', d, {'DATA': str(data)})
check(r.returncode == 1 and '::error' in r.stdout and not (d / 'data/world-key/overrides.json').exists(),
      'kpc_world_answers fails when world-finder.json is missing and writes no empty overrides')


# ---- Canada hard look: the rules file is unchanged; materialize feeds it ----
HL = {'rows': {'1': {'ref': 'CA-9', 'answer': 'YES', 'url': 'https://maps.example.ca/arcgis/rest/services/Parks/MapServer/4',
                     'record_given': 'OBJECTID 1649', 'name_field': 'NAME'}}}
HL_GZ = {'rows': {'1': {'ref': 'CA-9', 'answer': 'YES', 'url': 'https://maps.example.ca/arcgis/rest/services/Parks/MapServer/4',
                        'record_given': 'OBJECTID 99', 'name_field': 'NAME'}}}


def hardlook_oid(d):
    p = d / 'data/ca-key/hardlook-joins.json'
    if not p.exists():
        return None
    rows = json.loads(p.read_text()).get('rows') or []
    return rows[0].get('oid') if rows else None


for mode, expect in (('plain', 1649), ('gz', 1649)):
    d = work()
    data = data_tree(mode)
    src = data / 'data/waiting/questions/hardlook.json'
    put(src, HL, mode)
    mat = run('kpc_json_any.py', d, {}, ['--materialize', str(src)])
    r = run('kpc_ca_hardlook.py', d, {'DATA': str(data)})
    check(mat.returncode == 0 and r.returncode == 0 and hardlook_oid(d) == expect,
          f'hardlook materialize + kpc_ca_hardlook reads a {mode}-only hardlook.json (oid {expect})')

d = work()
data = data_tree('plain')
src = data / 'data/waiting/questions/hardlook.json'
put(src, (HL, HL_GZ), 'both')
mat = run('kpc_json_any.py', d, {}, ['--materialize', str(src)])
r = run('kpc_ca_hardlook.py', d, {'DATA': str(data)})
check(mat.returncode == 0 and hardlook_oid(d) == 99, 'materialize prefers hardlook.json.gz, then the unchanged reader joins that record')

d = work()
data = data_tree('gz')
src = data / 'data/waiting/questions/hardlook.json'
put(src, HL, 'gz')
r = run('kpc_ca_hardlook.py', d, {'DATA': str(data)})
check(r.returncode == 0 and hardlook_oid(d) is None and 'not read' in r.stdout,
      'kpc_ca_hardlook.py alone still does not see a gz-only file (that is why the workflow materializes)')

d = work()
data = data_tree('plain')
src = data / 'data/waiting/questions/hardlook.json'
mat = run('kpc_json_any.py', d, {}, ['--materialize', str(src)])
check(mat.returncode == 1 and '::error' in mat.stdout and not src.exists(),
      'materialize fails when hardlook.json and hardlook.json.gz are both missing')


# ---- verdicts.jsonl.gz merge in the shared save ----
def sh(cmd, cwd):
    env = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, env=env)


with tempfile.TemporaryDirectory() as T:
    sh('git init -q --bare -b main origin.git && git clone -q origin.git a', T)
    a = pathlib.Path(T) / 'a'
    log = a / 'data/waiting/verdicts.jsonl.gz'
    log.parent.mkdir(parents=True)
    log.write_bytes(gzip.compress(b'{"l":1}\n', mtime=0))
    sh('git add -A && git commit -qm init && git push -q origin main', a)
    sh('git clone -q origin.git b', pathlib.Path(T))
    b = pathlib.Path(T) / 'b'
    blog = b / 'data/waiting/verdicts.jsonl.gz'
    blog.write_bytes(gzip.compress(b'{"l":1}\n{"l":2}\n', mtime=0))
    out = sh(f'bash {SCRIPTS / "kpc_push_data.sh"} . "b save" data', b)
    sh('git pull -q origin main', a)
    lines = gzip.decompress((a / 'data/waiting/verdicts.jsonl.gz').read_bytes()).decode().split()
    check(sorted(lines) == ['{"l":1}', '{"l":2}'] and '::error title=Save merge' not in out.stdout,
          f'verdicts.jsonl.gz lines from main and this job are both kept ({lines})')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
