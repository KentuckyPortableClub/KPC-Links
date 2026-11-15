#!/usr/bin/env python3
"""Problem solver, Nov 14 2026: the key run also covers the Canada key (data/ca-key) and the world key (data/world-key), each with
its own overrides file (KIND=CA|WORLD|ALL; the default stays US only). Synthetic rows in temp folders, offline; nothing is written
to the repo."""
import gzip, json, os, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_problem_solver as S

ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)

def sq(lo, la, d=0.01): return [[[lo - d, la - d], [lo + d, la - d], [lo + d, la + d], [lo - d, la + d], [lo - d, la - d]]]
def wj(p, d): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d), encoding='utf-8')
def wgz(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, 'wt', encoding='utf-8') as f: json.dump(d, f)

def tree(ca_ov=None, w_ov=None):
    t = pathlib.Path(tempfile.mkdtemp(prefix='solver-caw-'))
    # US: one plain held park (no saved outline) so the default run has something to write
    wj(t / 'data/us-key/US-KY.json', {'parks': {'US-1': {'n': 'Pine Creek State Forest', 't': 'State Forest', 'm': [], 'g': 'pin',
                                                          'held': {'ids': ['h1']}, 'bk': ['h1', 20.0], 'c': [['h1', 'Pine Creek State Forest', 500, 'held']]}}})
    wj(t / 'data/us-key/overrides.json', {'parks': {}})
    # CANADA: CA-0001 land wrong (held piece far, a same-name piece at the pin); CA-0002 pin wrong; CA-0003 a kind clash at the pin
    wj(t / 'data/ca-key/CA-AB.json', {'prov': 'AB', 'parks': {
        'CA-0001': {'n': 'Elk Lake Provincial Park', 't': 'Provincial Park', 'm': [], 'g': 'pin', 'far': 'well outside',
                    'held': {'ids': ['Alberta Park:1'], 'why': 'far'}, 'bk': ['Alberta Park:1', 30.0, '', '-'],
                    'c': [['Alberta Park:1', 'Elk Lake Provincial Park', 600, 'held'], ['Alberta Park:2', 'Elk Lake Provincial Park', 500, 'at the pin']]},
        'CA-0002': {'n': 'Moose Hill Provincial Park', 't': 'Provincial Park', 'm': [], 'g': 'pin', 'far': 'well outside',
                    'held': {'ids': ['Alberta Park:3']}, 'bk': ['Alberta Park:3', 25.0, '', '-'], 'c': [['Alberta Park:3', 'Moose Hill Provincial Park', 1200, 'held']]},
        'CA-0003': {'n': 'Fox Creek Provincial Park', 't': 'Provincial Park', 'm': [], 'g': 'pin', 'far': 'well outside',
                    'held': {'ids': ['Alberta Park:4']}, 'bk': ['Alberta Park:4', 30.0, '', '-'],
                    'c': [['Alberta Park:4', 'Fox Creek Provincial Park', 600, 'held'], [22001, 'Fox Creek National Wildlife Area', 500, 'at the pin']]}}})
    wj(t / 'data/ca-key/overrides.json', ca_ov if ca_ov is not None else {'blocked_ids': [], 'parks': {}})
    wj(t / 'pi/CA.json', {'parks': {'CA-0001': ['Elk Lake', '', 'Provincial Park', '', '', 54.0, -114.0, 0, 0, 0, 'AB'],
                                    'CA-0002': ['Moose Hill', '', 'Provincial Park', '', '', 54.3, -114.5, 0, 0, 0, 'AB'],
                                    'CA-0003': ['Fox Creek', '', 'Provincial Park', '', '', 55.0, -115.0, 0, 0, 0, 'AB']}})
    big = [[[-114.05, 54.47], [-113.95, 54.47], [-113.95, 54.53], [-114.05, 54.53], [-114.05, 54.47]]]   # ~1,600 ha, 25 km from the pin
    wgz(t / 'cc/CA-ALL.json.gz', {'saved': '2026-11-01', 'recs': [
        {'oid': 'Alberta Park:1', 'n': 'Elk Lake Provincial Park', 'ha': 240, '_r': sq(-114.0, 54.3)},
        {'oid': 'Alberta Park:2', 'n': 'Elk Lake Provincial Park', 'ha': 200, '_r': sq(-114.0, 54.0)},
        {'oid': 'Alberta Park:3', 'n': 'Moose Hill Provincial Park', 'ha': 0, '_r': big},
        {'oid': 'Alberta Park:4', 'n': 'Fox Creek Provincial Park', 'ha': 240, '_r': sq(-115.0, 55.3)},
        {'oid': 22001, 'n': 'Fox Creek National Wildlife Area', 'ha': 200, '_r': sq(-115.0, 55.0)}]})
    # WORLD: AT-0001 land wrong with layer names in the third cell (not acres); NO-0179 sits in SJ.json, its pin in NO.json;
    # AT-0002: id 7 is two different saved places (per-layer ids), so it is not trusted
    wj(t / 'data/world-key/AT.json', {'cc': 'AT', 'parks': {
        'AT-0001': {'n': 'Naturpark Kaunergrat', 't': 'Nature Park', 'm': [], 'g': 'pin', 'far': 'well outside',
                    'held': {'ids': [48]}, 'bk': [48, 57.5, '', '-'],
                    'c': [[48, 'Naturpark Kaunergrat', 'NAP_AT', 'held'], [49, 'Naturpark Kaunergrat', 'NAP_AT', 'at the pin']]},
        'AT-0002': {'n': 'Lobau Nature Reserve', 't': 'Nature Reserve', 'm': [], 'g': 'pin', 'far': 'well outside',
                    'held': {'ids': [7]}, 'bk': [7, 20.0, '', '-'], 'c': [[7, 'Lobau', 'Layer A', 'held'], [8, 'Lobau', 'Layer A', 'at the pin']]}}})
    wj(t / 'data/world-key/SJ.json', {'cc': 'SJ', 'parks': {
        'NO-0179': {'n': 'Blomstrandhamna Nature Reserve', 't': 'Nature Reserve', 'm': [], 'g': 'pin', 'far': 'well outside',
                    'held': {'ids': [100]}, 'bk': [100, 20.0, '', '-'],
                    'c': [[100, 'Blomstrandhamna', 'Naturbase', 'held'], [101, 'Blomstrandhamna', 'Naturbase', 'at the pin']]}}})
    wj(t / 'data/world-key/overrides.json', w_ov if w_ov is not None else {'parks': {}})
    wj(t / 'pi/AT.json', {'parks': {'AT-0001': ['', '', '', '', '', 47.0, 10.7], 'AT-0002': ['', '', '', '', '', 48.2, 16.5]}})
    wj(t / 'pi/NO.json', {'parks': {'NO-0179': ['', '', '', '', '', 78.95, 12.1]}})
    wgz(t / 'wc/W-AT.json.gz', {'cc': 'AT', 'saved': '2026-11-02', 'recs': [
        {'id': 48, 'n': 'Naturpark Kaunergrat', 'src': 'NAP_AT', '_r': sq(10.7, 47.5)},
        {'id': 49, 'n': 'Naturpark Kaunergrat', 'src': 'NAP_AT', '_r': [[[10.7, 47.0]]], '_f': sq(10.7, 47.0)},
        {'id': 7, 'n': 'Lobau', 'src': 'Layer A', '_r': sq(16.5, 48.4)}, {'id': 7, 'n': 'Donau-Auen', 'src': 'Layer B', '_r': sq(16.5, 48.3)},
        {'id': 8, 'n': 'Lobau', 'src': 'Layer A', '_r': sq(16.5, 48.2)}]})
    wgz(t / 'wc/W-SJ.json.gz', {'cc': 'SJ', 'recs': [{'id': 100, 'n': 'Blomstrandhamna', 'src': 'Naturbase', '_r': sq(12.1, 79.2)},
                                                      {'id': 101, 'n': 'Blomstrandhamna', 'src': 'Naturbase', '_r': sq(12.1, 78.95)}]})
    return t

def env(t, **kw):
    e = {'PARKINFO': str(t / 'pi'), 'GEO_CACHE': str(t / 'none'), 'GEO_CACHE_CA': str(t / 'cc'), 'GEO_CACHE_WORLD': str(t / 'wc'),
         'GITHUB_RUN_ID': '777'}
    e.update(kw); return e

def res(t, kind):
    f = t / S.KEYS[kind]['dir'] / 'review/problem-solver.json'
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else None

# ---------------------------------------------------------------- default = US only (as before)
t = tree()
out = S.run(env(t), t)
check(isinstance(out, list) and res(t, 'US') and res(t, 'CA') is None and res(t, 'WORLD') is None, 'no KIND: only the US key is read and written')

# ---------------------------------------------------------------- Canada
out = S.run(env(t, KIND='CA'), t)
v = {x['park']: x for x in out}
check(v['CA-0001']['verdict'] == 'land wrong' and 'Alberta Park:2' in v['CA-0001']['recommend'] and v['CA-0001']['state'] == 'CA-AB',
      f"CA land wrong: {v['CA-0001']['recommend']}")
check(v['CA-0002']['verdict'] == 'pin wrong' and not any('lies in' in r for r in v['CA-0002']['reasons']),
      f"CA pin wrong, never 'wrong state' (US states file): {v['CA-0002']['verdict']}")
check(v['CA-0003']['verdict'] == 'needs a person' and v['CA-0003']['not_proposed'][0]['id'] == '22001'
      and v['CA-0003']['not_proposed'][0]['why'].startswith('name does not fit'), 'CA: the name test keeps a wildlife area off a provincial park')
d = res(t, 'CA')
check(d and all(x.get('by') == 'kpc_problem_solver:key' and x.get('when') and x.get('run_id') == '777' for x in d['parks'] + d['why']),
      'CA rows (verdicts + why) carry by / when / run_id')
check((t / 'data/ca-key/review/problem-solver.md').exists() and '| By | When | Run ID |' in (t / 'data/ca-key/review/problem-solver.md').read_text(),
      'CA: the .md is written beside it, with the who / when / run id columns')
check('saved outlines are from 2026-11-01' in '; '.join(S.solve('CA-9', {'n': 'X Park', 'm': [], 'held': {'ids': ['q:1']}, 'c': [['q:1', 'X Park', 1, 'h']]},
                                                                (54, -114), {}, None, 'CA-AB', ctx={'kind': 'CA', 'cache_note': S.cache_note('', 'CA-ALL')})['reasons']),
      "CA: the saved copy's own date is named when a held record has no outline")

# a person's NO in data/ca-key/overrides.json wins: 'no' by name, and blocked_ids (with decided_by)
t2 = tree(ca_ov={'blocked_ids': [{'ref': 'CA-0002', 'id': 'Alberta Park:3', 'reason': 'x', 'decided_by': 'Brandon'}],
                 'parks': {'CA-0001': {'no': ['Elk Lake Provincial Park'], 'why': 'test'}}})
v = {x['park']: x for x in S.run(env(t2, KIND='CA'), t2)}
check(v['CA-0001']['verdict'] == 'needs a person' and "blocked by a person's no" in '; '.join(v['CA-0001']['reasons']), "CA: an overrides 'no' (name) blocks the proposal")
check(v['CA-0002']['verdict'] == 'needs a person' and "blocked_ids" in '; '.join(v['CA-0002']['reasons']), 'CA: blocked_ids blocks keeping the held record')

# a broken Canada overrides file: fail closed, nothing written for Canada
t3 = tree(); (t3 / 'data/ca-key/overrides.json').write_text('{"parks": {', encoding='utf-8')
try: S.run(env(t3, KIND='CA'), t3); raised = False
except Exception as e: raised = 'not readable JSON' in str(e)  # noqa: BLE001
check(raised and res(t3, 'CA') is None, 'CA: a broken overrides file stops the Canada run (nothing written)')

# ---------------------------------------------------------------- world
out = S.run(env(t, KIND='WORLD'), t)
v = {x['park']: x for x in out}
a = v['AT-0001']
check(a['verdict'] == 'land wrong' and a['recommend'].startswith('join 49') and 'acres not on file' in '; '.join(a['reasons']),
      f"WORLD land wrong on the fine ring, a layer name in the acres cell is not read as acres: {a['recommend']}")
check(v['NO-0179']['verdict'] == 'land wrong' and v['NO-0179']['state'] == 'SJ', "WORLD: a territory file's ref (SJ: NO-0179) finds its pin in NO.json")
check('7' not in S.kind_recs('WORLD', str(t / 'wc'), 'AT') and v['AT-0002']['records'][0]['points'] is None,
      'WORLD: an id two saved places share (per-layer ids) is not trusted as the held outline')
d = res(t, 'WORLD')
check(d and all(x.get('by') and x.get('when') and x.get('run_id') == '777' for x in d['parks'] + d['why']), 'WORLD rows carry by / when / run_id')
t4 = tree(w_ov={'parks': {'AT-0001': {'no': ['49'], 'join': ['Naturpark Kaunergrat']}}})
v = {x['park']: x for x in S.run(env(t4, KIND='WORLD'), t4)}
check(v['AT-0001']['verdict'] == 'needs a person' and "blocked by a person's no" in '; '.join(v['AT-0001']['reasons']), "WORLD: an overrides 'no' (id) blocks the proposal")

# ---------------------------------------------------------------- ALL: a broken world file stops the world only
t5 = tree(); (t5 / 'data/world-key/overrides.json').write_text('[broken', encoding='utf-8')
try: S.run(env(t5, KIND='ALL'), t5); raised = False
except Exception: raised = True  # noqa: BLE001
check(raised and res(t5, 'US') and res(t5, 'CA') and res(t5, 'WORLD') is None, 'ALL: US and CA written, the broken world overrides stops the world (and is raised)')
r = S.run(env(tree(), KIND='ALL'), t)
check(set(r) == {'US', 'CA', 'WORLD'}, 'ALL: every kind runs')
try: S.run(env(t, KIND='MARS'), t); raised = False
except ValueError: raised = True
check(raised, 'an unknown KIND is refused')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
