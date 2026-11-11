#!/usr/bin/env python3
"""KPC owner, 2026-11-11 (world rules change; Australia failed every build): a layer that fails with no saved records no longer
holds its country. The parks the previous key joined through that layer keep their previous entry, the rest is rebuilt, and the
layer is logged. Layers that joined no park were taken out (AU: 7 + a duplicate; GB: 3) and BOT W never wires them again. The
post-check flags any layer that joined no park. Offline."""
import collections, json, os, pathlib, subprocess, sys, tempfile, textwrap
ROOT = pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT); sys.path.insert(0, str(ROOT / '.github/scripts'))
TEXT = (ROOT / '.github/scripts/kpc_world_key.py').read_text(encoding='utf-8')
ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)

# the helper functions, as they are in the builder
i = TEXT.index('def prev_key(cc):'); j = TEXT.index('HELD = []', i); notes = []
ns = {'json': json, 'OUT': None, 'notice': lambda t, m: notes.append(f'{t}: {m}')}
exec(compile(TEXT[i:j], 'kpc_world_key.py (fall back)', 'exec'), ns)
A, B = ('Layer A', 'arcgis', 'https://a.example/MapServer/0'), ('Layer B', 'arcgis', 'https://b.example/MapServer/0')
prev = {'XX-1': {'n': 'One', 'm': [[1, 'One', 'Layer A', 'name']], 'c': []},
        'XX-2': {'n': 'Two', 'm': [[2, 'Two', 'Layer B', 'name']], 'c': []},
        'XX-3': {'n': 'Three', 'm': [[3, 'Three', 'Layer A', 'name'], [9, 'Three', 'Layer B', 'name']], 'c': []},
        'XX-4': {'n': 'Four', 'm': [], 'c': [[4, 'Fourish', 'Layer B', 'similar name']]},
        'XX-5': {'n': 'Gone', 'm': [[5, 'Gone', 'Layer B', 'name']], 'c': []}}
with tempfile.TemporaryDirectory() as t:
    ns['OUT'] = pathlib.Path(t); (pathlib.Path(t) / 'XX.json').write_text(json.dumps({'cc': 'XX', 'parks': prev}))
    check('no failed layer: nothing kept, nothing logged', ns['fell_back_plan']('XX', [], True) == {'labels': [], 'keep': {}} and not notes)
    plan = ns['fell_back_plan']('XX', [B], True)
    check('layer B fell back: the parks that JOINED through it are kept (a candidate-only park is not)', plan['labels'] == ['Layer B'] and sorted(plan['keep']) == ['XX-2', 'XX-3', 'XX-5'])
    check('the layer is logged by name with its park count', any('layer fell back' in n and 'Layer B [https://b.example/MapServer/0]' in n and '3 park(s) keep their previous joins' in n for n in notes))
    check('no layer gave any record: None (the country is held as before)', ns['fell_back_plan']('XX', [B], False) is None)
    check('no previous key: the country is still built from what answered', ns['fell_back_plan']('YY', [B], True) == {'labels': ['Layer B'], 'keep': {}})
    rebuilt = {'XX-1': {'n': 'One', 'm': [[1, 'One', 'Layer A', 'name']], 'c': []}, 'XX-2': {'n': 'Two', 'm': [], 'c': []},
               'XX-3': {'n': 'Three', 'm': [[3, 'Three', 'Layer A', 'name']], 'c': []}, 'XX-4': {'n': 'Four', 'm': [], 'c': []}, 'XX-6': {'n': 'New', 'm': [], 'c': []}}
    kept = ns['fell_back_apply'](rebuilt, plan, {'XX-1', 'XX-2', 'XX-3', 'XX-4', 'XX-6'})
    check('kept parks carry their whole previous entry; the others are this build\'s', kept == ['XX-2', 'XX-3'] and rebuilt['XX-2'] == prev['XX-2'] and rebuilt['XX-3'] == prev['XX-3']
          and rebuilt['XX-1']['m'] == [[1, 'One', 'Layer A', 'name']] and rebuilt['XX-4']['m'] == [])
    check('a park POTA no longer lists is not brought back', 'XX-5' not in rebuilt and 'XX-6' in rebuilt)

# the real source loop: a saved-only host (never contacted) with no saved records falls back, by name, with no request made
START, END = '    if recs is None:\n        recs, failed = [], False', '\n    if not recs: continue'
BLOCK = textwrap.dedent(TEXT[TEXT.index(START):TEXT.index(END, TEXT.index(START))])
i = TEXT.index('def src_id(s):'); src_ns = {}; exec(TEXT[i:TEXT.index('\n\n\n', i)], src_ns)
OKL = ('CAPAD', 'arcgis', 'https://gis.environment.gov.au/x/MapServer/0'); BLK = ('NSW State Forest', 'arcgis', 'https://services2.arcgis.com/x/FeatureServer/0')
GONE = ('Surface_HydroLines_National', 'arcgis', 'https://services.ga.gov.au/gis/rest/services/Surface_Hydrology/MapServer/2')
def loop(sources, old, answers):
    asked, held, saved, nn = [], [], [], []
    def pull(name, url, *_):
        asked.append(url); a = answers[url]
        if isinstance(a, Exception): raise a
        return [dict(r) for r in a]
    e = {'cc': 'AU', 'CMODE': 'refresh', 'recs': None, 'SRC': {'AU': sources}, 'pull_arcgis': pull, 'pull_find': None, 'pull_a10': None, 'pull_a10n': None, 'pull_chshp': None,
         'pull_wfs': pull, 'collections': collections, 'HELD': held, 'src_id': src_ns['src_id'], 'wload': lambda cc: [dict(r) for r in old] if old is not None else None,
         'wsave': lambda cc, r: saved.append(len(r)), 'notice': lambda t, m: nn.append(f'{t}: {m}'), 'print': lambda *a, **k: None,
         'fell_back_plan': lambda cc, h, have: {'labels': [x[0] for x in h], 'keep': {}} if (have or not h) else None, 'FELL': None}
    exec(compile('went_on = False\nfor _once in [0]:\n' + textwrap.indent(BLOCK, '    ') + '\n    went_on = True\n', 'source loop', 'exec'), e)
    return e, held, saved, nn
live = [{'src': 'CAPAD', 'id': n, 'n': f'P{n}'} for n in range(500)]
e, held, saved, nn = loop([OKL, BLK], None, {OKL[2]: live, BLK[2]: RuntimeError('saved copy only')})
check('a layer that cannot be read and has no saved records: the country goes on with the other layers', not held and e['went_on'] and len(e['recs']) == 500 and e['FELL']['labels'] == ['NSW State Forest'])
check('a build with a fallen-back layer is never saved over the saved copy', saved == [])
sid = src_ns['src_id']
old = [dict(r, sid=sid(OKL)) for r in live] + [{'src': GONE[0], 'id': f'h{n}', 'n': 'river', 'sid': sid(GONE)} for n in range(50_000)] + [{'src': BLK[0], 'id': 's1', 'n': 'Forest', 'sid': sid(BLK)}]
e, held, saved, nn = loop([OKL, BLK], old, {OKL[2]: live, BLK[2]: RuntimeError('saved copy only')})
check('saved records of a layer the country no longer reads are not brought back (like with like)', not held and len(e['recs']) == 501 and not any(r['src'] == GONE[0] for r in e['recs'])
      and sum(1 for r in e['recs'] if r['src'] == BLK[0]) == 1)
import kpc_master as M
check('services*.arcgis.com is still never read live', M.live_ok(BLK[2])[0] is False and 'saved_only(u): raise LayerStall' in TEXT.replace('if saved_only(u): raise', 'saved_only(u): raise'))

# the data: layers taken out, and BOT W keeps them out
X = json.load(open(ROOT / 'data/world-key/extra-layers.json')); au = {l['label'] for l in X['countries']['AU']}
gone = {'Walking track', 'Great walk', 'Beach Presence', 'Beach Names', 'Forest Blocks (DBCA-025)', 'Surface_HydroLines_National', 'Beach', 'Protected Areas (CAPAD)'}
check('AU: the 7 no-park layers and the duplicate CAPAD layer are out, and listed under dropped with a reason', not (au & gone) and {x['label'] for x in X['dropped']['AU']} == gone and all(x.get('why') and x.get('url') for x in X['dropped']['AU']))
check('AU keeps its 14 other wired layers', len(X['countries']['AU']) == 14)
check('GB: the 3 never-read layers that joined nothing are out', {x['label'] for x in X['dropped']['GB']} == {'INV_BLKDATA', 'Forest_Blocks', 'FE_Ownership_160726'})
k = json.load(open(ROOT / 'data/world-key/AU.json')); lost = [r for r, p in k['parks'].items() if p.get('m') and all(x[2] in gone for x in p['m'])]
check('no AU park in the published key is joined only through a layer that was taken out', lost == [])
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); (t / 'data/world-key').mkdir(parents=True); (t / '.github/scripts').mkdir(parents=True); (t / 'd/data/intake').mkdir(parents=True)
    hy = next(x['url'] for x in X['dropped']['AU'] if x['label'] == 'Surface_HydroLines_National')
    (t / 'data/world-key/extra-layers.json').write_text(json.dumps({'countries': {'AU': []}, 'dropped': {'AU': [{'url': hy, 'label': 'x'}]}}))
    rows = [{'area': 'W-AU', 'url': hy, 'name_field': 'name', 'answer': 'YES', 'title': 'Hydro lines'},
            {'area': 'W-AU', 'url': 'https://example.gov.au/arcgis/rest/services/Parks/MapServer/3', 'name_field': 'NAME', 'answer': 'YES', 'title': 'Parks'}]
    (t / 'd/data/intake/ready.json').write_text(json.dumps({'rows': rows})); (t / 'd/data/waiting/questions').mkdir(parents=True); (t / 'd/data/waiting/questions/layers.json').write_text(json.dumps({'rows': rows}))
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_key_layers.py')], cwd=t, env=dict(os.environ, DATA=str(t / 'd')), capture_output=True, text=True)
    after = json.load(open(t / 'data/world-key/extra-layers.json')); urls = [l['url'] for l in after['countries'].get('AU', [])]
    check('BOT W: a dropped layer with a standing YES is not wired again; another approved layer still is', hy not in urls and urls == ['https://example.gov.au/arcgis/rest/services/Parks/MapServer/3'] and after.get('dropped'))

# the post-check
import kpc_key_postcheck as P
new = {'AU': {'sources': ['A', 'B', 'C', 'D'], 'fell_back': ['D'], 'parks': {
    'AU-1': {'m': [[1, 'x', 'A', 'name']]}, 'AU-2': {'m': [], 'c': [[2, 'y', 'B', 'similar name']]}, 'AU-3': {'m': [[3, 'z', 'D', 'name']]}}},
       'US-TN': {'parks': {'US-1': {'m': [[1, 2]]}}}}
idle, fell = P.layer_use(new)
check('post-check: a layer that joined no park is flagged, with its candidate count', idle == [{'area': 'AU', 'layer': 'B', 'candidates': 1}, {'area': 'AU', 'layer': 'C', 'candidates': 0}])
check('post-check: a fallen-back layer is listed with the parks it kept, not as idle', fell == [{'area': 'AU', 'layer': 'D', 'parks_kept': 1}])
txt = (ROOT / '.github/scripts/kpc_key_postcheck.py').read_text()
check('post-check: both lists reach the report, its summary and a warning line', "rep['layers_no_parks'], rep['layers_fell_back'] = layer_use(new)" in txt and "'layers that joined no park'" in txt and 'Layers that joined no park' in txt and 'layer(s) joined no park' in txt)

# the rules hash and its declaration
import kpc_key_freeze as F, kpc_preflight as PF
sc = json.load(open(ROOT / '.github/world-key-rule-scope.json'))
check('world rules: a scope entry from the old hash, and the newest changelog line names old -> new, approved', sc['changes'][-1]['from'] == '096a551a8cb6'
      and F.SCOPE_FILES['world-key'] == '.github/world-key-rule-scope.json' and '.github/world-key-rule-scope.json' in F.RULE_FILES['world-key']
      and F.rules_hash('world-key') == PF.newest_hash('world-key')
      and f"world rules 096a551a8cb6 -> {F.rules_hash('world-key')}" in PF.changelog_hashes(open(ROOT / 'docs/key-rules-change.txt').read(), 'world-key')[2]
      and 'APPROVED, decided_by KPC owner, 2026-11-11' in PF.changelog_hashes(open(ROOT / 'docs/key-rules-change.txt').read(), 'world-key')[2])
# Nov 11 (overlap finder, 25 m): the 2-fer hash moved later in its own entry; it must equal its newest changelog line (no literal to edit on a rebase)
check('the US and Canada hashes did not move; the 2-fer hash is the one its newest changelog line names', (F.rules_hash('us-key'), F.rules_hash('ca-key')) == ('46ef34a04ab0', '4b4176190334') and F.rules_hash('fers') == PF.newest_hash('fers'))
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
