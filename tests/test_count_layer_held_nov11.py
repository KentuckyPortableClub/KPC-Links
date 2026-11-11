#!/usr/bin/env python3
"""Nov 11 r2 (KPC owner, 2026-11-11; Quality NO on #126, must-fix 2): a one-state live layer read is checked against the layer's OWN
total (count_layer, no box). A failed or missing count_layer on such a read HOLDS it; the expected count is count_layer (less
layers.json outside_box_ok), not the boxed count_live. Only a layer that is this state's alone gets count_layer (NRHP and the USACE
layer are listed once per state). A saved layer under its own verified baseline is re-read (the FL sgflf saved copy)."""
import gzip, json, pathlib, sys, tempfile, types
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M
import kpc_master_fill as F

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)

FL = {'area': 'US-FL', 'layer': 'sgflf', 'source': 'live'}
with tempfile.TemporaryDirectory() as td:
    root = pathlib.Path(td); (root / 'layers.json').write_text(json.dumps({'format': 1, 'layers': {'US-TX.sgtxa': {'outside_box_ok': 3}}, 'caches': {}}))
    # expected
    check('expected = count_layer, not the boxed count_live', M.layer_file_expected({**FL, 'count_live': 77144, 'count_layer': 79689}) == 79689)
    check('count_layer present but None (the count failed) = no expected count', M.layer_file_expected({**FL, 'count_live': 77144, 'count_layer': None}) is None)
    check('outside_box_ok lowers it only by what a person allowed', M.layer_file_expected({'area': 'US-TX', 'layer': 'sgtxa', 'source': 'live', 'count_live': 90, 'count_layer': 100}, 3) == 97)
    check('no count_layer key (hand file, national layer) = count_live / count_expected as before',
          M.layer_file_expected({**FL, 'count_live': 5}) == 5 and M.layer_file_expected({'source': 'hand', 'count_expected': 8}) == 8)
    # box_short
    check('box_short: count_layer None = HELD', 'HELD' in F.box_short({**FL, 'count_layer': None}, 77144, root))
    check('box_short: count_layer 79689, read 77144 = SHORT', 'SHORT' in F.box_short({**FL, 'count_layer': 79689}, 77144, root))
    check('box_short: whole read passes', F.box_short({**FL, 'count_layer': 79689}, 79689, root) == '')
    check('box_short: no count_layer key / a hand file = not this check', F.box_short(dict(FL), 1, root) == '' and F.box_short({**FL, 'source': 'hand', 'count_layer': None}, 1, root) == '')
    # apply_layer_file refuses before any trim or merge
    def lf(meta, n):
        p = root / f"lf-{meta.get('count_layer')}-{n}.geojson.gz"
        return M.write_layer_file(p, meta, [{'type': 'Feature', 'properties': {'OBJECTID': i}, 'geometry': None} for i in range(n)])
    okk, what = F.apply_layer_file(lf({**FL, 'count_live': 3, 'count_layer': None, 'count_raw': 3}, 3), root / 'cache', root, root / 'parks.json')
    check('apply: a failed unboxed count plus a good boxed count is HELD, not merged (Quality proof case)', not okk and 'HELD' in what)
    okk, what = F.apply_layer_file(lf({**FL, 'count_live': 3, 'count_layer': 5, 'count_raw': 3}, 3), root / 'cache', root, root / 'parks.json')
    check('apply: a read of 3 against the layer total 5 is SHORT, not merged', not okk and 'SHORT' in what and '3 of 5' in what)

# _one_state_layer, run from the key's source (importing kpc_us_key runs a build)
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
i = src.index('def _one_state_layer('); j = src.index('def layer_total_count(', i)
ns = {'XS': [('sgflf', 'https://ca.dep.state.fl.us/x/MapServer/0/query', 'N', '', set(), 'L', 'STAT', {'FL'}, {}),
             ('sgaki', 'https://nrhp.example/MapServer/1/query', 'N', '', set(), 'L', 'STAT', {'AK'}, {}),
             ('sgaki', 'https://nrhp.example/MapServer/1/query', 'N', '', set(), 'L', 'STAT', {'UT'}, {'where': 'x'}),
             ('sgide', 'https://usace.example/FeatureServer/0/query', 'N', '', set(), 'L', 'STAT', {'ID'}, {}),
             ('sgide', 'https://usace.example/FeatureServer/0/query', 'N', '', set(), 'L', 'STAT', {'MS'}, {}),
             ('padus', 'https://padus.example/0/query', 'N', '', set(), 'L', 'FED', None, {})]}
exec(compile(src[i:j], 'kpc_us_key.py', 'exec'), ns)
check('one-state layer: FL DEP lands yes; NRHP (AK+UT), USACE (ID+MS), PAD-US no',
      ns['_one_state_layer']('sgflf', 'FL') and not ns['_one_state_layer']('sgaki', 'AK') and not ns['_one_state_layer']('sgide', 'MS') and not ns['_one_state_layer']('padus', 'FL'))
check('the key writes count_layer for every one-state live layer (None when the count fails)', "if x and _one_state_layer(pre, st): meta['count_layer'] = layer_total_count(" in src)

# a saved layer under its own verified baseline is re-read
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td); (t / 'cache').mkdir()
    recs = [{'OBJECTID': f'sgflf{i}'} for i in range(5)] + [{'OBJECTID': f'sgflb{i}'} for i in range(2)]
    with gzip.open(t / 'cache/US-FL.json.gz', 'wt') as f: json.dump({'st': 'FL', 'recs': recs}, f)
    doc = {'layers': {'US-FL.sgflf': {'expected_count': 7}, 'US-FL.sgflb': {'expected_count': 2}, 'US-FL.sgide': {'expected_count': 9}}}
    table = {'sgflf': {'url': 'https://ca.dep.state.fl.us/x/MapServer/0/query'}, 'sgflb': {'url': 'https://gis.example.org/y/MapServer/0'},
             'sgide': {'url': 'https://services7.arcgis.com/z/FeatureServer/0'}}
    got = F.layers_below_baseline(t / 'cache', ['FL'], doc, table)
    check('FL sgflf (5 saved, baseline 7) is re-read; a whole layer and a never-contact host are not', got == {('FL', 'sgflf')})
fill_src = (ROOT / '.github/scripts/kpc_master_fill.py').read_text(encoding='utf-8')
check('fill() adds those layers to the refill (KPC_REFILL_FORCE)', 'below = layers_below_baseline(a.cache, states, doc, table)' in fill_src and "force = ' '.join(sorted(set(force.split()) | {p for _, p in below}))" in fill_src)

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
