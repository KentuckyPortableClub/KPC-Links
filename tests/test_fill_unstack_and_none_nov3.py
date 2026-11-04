#!/usr/bin/env python3
"""Nov 3 (remake after Quality's Canada key fixes grade): offline checks, no network.
- kpc_ca_fill_bounds._unstack: dots / flat lines go (CA-3380), a file with nothing real left is [] (the file is removed), and a
  copy that is 80-98% inside is kept when it alone draws 1 acre or more (CA-3212 East Sooke, CA-3229).
- kpc_key_answers: 'none' is cleared when this bot's YES is followed only by its NOs on OTHER records (US-7383), and kept when the
  later NO is on the joined record or comes from the map audit (US-10025 / US-1080 / US-7145).
Run: python3 tests/test_fill_unstack_and_none_nov3.py"""
import json, os, pathlib, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_ca_fill_bounds as F

ok = True
def check(c, label):
    global ok
    print(('ok   ' if c else 'FAIL ') + label); ok = ok and bool(c)

line = [[0, 0], [0.001, 0.001], [0, 0], [0.001, 0.001]]
check(F._unstack([[line], [line]]) == [], 'a file of a flat line drawn twice: nothing real left ([] = remove the file)')
sq = [[0, 0], [0, .01], [.01, .01], [.01, 0], [0, 0]]
check(F._unstack([[sq], [sq]]) == [[sq]], 'the same square twice: one kept')
check(F._unstack([[sq], [line]]) == [[sq]], 'a flat line next to a real ring is left out')
check(F._unstack([[sq]]) is None, 'nothing to change: None')
big = [[0, 0], [0, .1], [.1, .1], [.1, 0], [0, 0]]                 # ~30,000 ac at the equator
near = [[0, 0], [0, .1], [.109, .1], [.109, 0], [0, 0]]            # ~92% inside, adds ~2,700 ac of its own
check(F._unstack([[big], [near]]) is None, 'a copy 80-98% inside that alone draws real land is kept (East Sooke)')
tiny = [[0, 0], [0, .1], [.10002, .1], [.10002, 0], [0, 0]]        # 99.98% inside
check(F._unstack([[big], [tiny]]) == [[big]], 'a copy 98%+ inside is left out')

# Nov 3 recut (Quality should-fix S2-06): a 3-point FLAT ring has 3 distinct points but draws no land; a ring must also draw
# at least REAL_MIN_AC (0.01 ac). CA-4106 (0 ac), CA-4798 (0.00013 ac) and CA-5438 (0.0068 ac) held nothing else.
flat = [[-75.0, 45.0], [-74.99, 45.0], [-74.98, 45.0], [-75.0, 45.0]]                 # 3 points on one line
speck = [[-75.0, 45.0], [-74.99995, 45.0], [-74.99995, 45.00005], [-75.0, 45.0]]      # about 0.0024 ac
check(not F._real(flat) and not F._real(speck), 'a 3-point flat ring and a speck under 0.01 ac are not real')
check(F._unstack([[flat]]) == [] and F._unstack([[speck], [flat]]) == [], 'a file of nothing but flat rings / specks has nothing real left')
check(F._unstack([[big], [flat]]) == [[big]], 'a flat ring next to real land is left out, the land stays')
hole = [[-79.5, 44.5], [-79.49995, 44.5], [-79.49995, 44.50005], [-79.5, 44.5]]
check(F._unstack([[big, hole]]) is None, 'a small but real hole is NOT removed by the area floor (only dot holes go)')
check(F.REAL_MIN_AC == 0.01, 'the floor is 0.01 ac (the smallest real outline on main, CA-3699, is 0.066 ac)')

# key_answers 'none'
P = {
 'US-7383': {'fp': {'sgazc6': ['Tonto Creek Hatchery', 62]}, 'join': ['sgazc6'], 'no': ['2756'], 'none': True,
             'why': "hand review · 2026-10-29 23:15: gis-hunter row YES 'Tonto Creek Hatchery' (chat 11; applied by kpc_key_answers) · "
                    "2026-10-29 23:15: gis-hunter row NO 'Tonto National Forest' (chat 11; applied by kpc_key_answers)"},
 'US-1080': {'fp': {'sgarb44': ['DeGray Lake Resort State Park', 819]}, 'join': ['sgarb44'], 'no': ['sgarb44'], 'none': True,
             'why': "x · 2026-11-02 12:49: layers row YES 'DeGray Lake Resort State Park' (chat 11; applied by kpc_key_answers) · "
                    "Nov 2 map audit: chat 11 NO on sgarb44 (PIN until fixed)"},
 'US-9': {'fp': {'a1': ['Alpha Lake', 5]}, 'join': ['a1'], 'none': True,
          'why': "x · 2026-10-29 23:15: gis-hunter row YES 'Alpha Lake' (chat 11; applied by kpc_key_answers) · "
                 "2026-10-29 23:16: gis-hunter row NO 'Alpha Lake' (chat 11; applied by kpc_key_answers)"},
}
with tempfile.TemporaryDirectory() as t:
    k = pathlib.Path(t, 'key'); k.mkdir(); d = pathlib.Path(t, 'data/data/waiting/questions'); d.mkdir(parents=True)
    (k / 'overrides.json').write_text(json.dumps({'parks': P}))
    env = dict(os.environ, KEY_DIR=str(k), DATA=str(pathlib.Path(t, 'data')))
    r = subprocess.run([sys.executable, str(HERE / '.github/scripts/kpc_key_answers.py')], env=env, capture_output=True, text=True, cwd=t)   # its status file goes to the temp dir
    Q = json.loads((k / 'overrides.json').read_text())['parks']
    check('none' not in Q['US-7383'], "US-7383: a later NO on a different record does not keep 'none'")
    check(Q['US-1080'].get('none') is True, "US-1080: a map-audit NO on the joined record keeps 'none' (a person decides)")
    check(Q['US-9'].get('none') is True, "a later NO on the joined record's own name keeps 'none'")
    if not ok: print(r.stdout[-800:], r.stderr[-800:])

# v5b (Quality grade of v4; Brandon 7:33 PM CST Nov 3, relayed by Super: "When in doubt drop it put it on a list"): the bounds fill
# must NOT write CA-2218.json / CA-2227.json again while the key files still carry the old join: a person's 'no' is honored.
import gzip  # noqa: E402
def _fine_square(x0, y0, d=0.01, n=60):   # segments ~20 m, so the 50 m roughness gate lets it through
    e = [[x0 + d * i / n, y0] for i in range(n)] + [[x0 + d, y0 + d * i / n] for i in range(n)] + \
        [[x0 + d - d * i / n, y0 + d] for i in range(n)] + [[x0, y0 + d - d * i / n] for i in range(n)]
    return e + [e[0]]
with tempfile.TemporaryDirectory() as t:
    T = pathlib.Path(t); (T / 'data/ca-key').mkdir(parents=True); (T / 'data/canada-bounds').mkdir(parents=True); (T / 'cache/ca').mkdir(parents=True)
    recs = [{'oid': 'Québec Réser:n-Réserve faunique de Rimouski', 'n': 'Réserve faunique de Rimouski', 'src': 'Québec', '_r': [_fine_square(-68.5, 48.0)]},
            {'oid': 'Québec prote:2496', 'n': 'Réserve naturelle de la Rivière-Malbaie (Sec. SCCN / Par. Stallman)', 'src': 'Québec', '_r': [_fine_square(-70.3, 47.6)]},
            {'oid': 'Québec prote:9', 'n': 'Okay Reserve', 'src': 'Québec', '_r': [_fine_square(-71.0, 46.0)]}]
    with gzip.open(T / 'cache/ca/CA-ALL.json.gz', 'wt', encoding='utf-8') as f: json.dump({'recs': recs}, f)
    (T / 'data/ca-key/CA-QC.json').write_text(json.dumps({'parks': {
        'CA-2218': {'n': 'Rimouski Reserve Nature Reserve', 'm': [[recs[0]['oid'], recs[0]['n'], 445000, 'reviewed']]},
        'CA-2227': {'n': 'Riviere Malbaie (CNC/Stallman) Nature Reserve', 'm': [[recs[1]['oid'], recs[1]['n'], 38, 'name']]},
        'CA-9': {'n': 'Okay Reserve', 'm': [[recs[2]['oid'], recs[2]['n'], 100, 'name']]}}}, ensure_ascii=False))
    (T / 'data/ca-key/overrides.json').write_text(json.dumps({'parks': {
        'CA-2218': {'no': ['Québec Réser:n-Réserve faunique de Rimouski', 'Réserve faunique de Rimouski'], 'none': True},
        'CA-2227': {'no': ['Québec prote:2496'], 'none': True}}}, ensure_ascii=False))
    env = dict(os.environ); env.pop('GEO_CACHE', None)
    r = subprocess.run([sys.executable, os.environ.get('FILL_TOOL') or str(HERE / '.github/scripts/kpc_ca_fill_bounds.py')], cwd=t, env=env, capture_output=True, text=True)
    B = T / 'data/canada-bounds'
    check((B / 'CA-9.json').exists(), 'fill: a park with no NO still gets its outline file (the test fixture draws)')
    check(not (B / 'CA-2218.json').exists() and not (B / 'CA-2227.json').exists(),
          "fill: a joined record a person said NO to (overrides 'no', by id or name) is never written again (CA-2218, CA-2227)")
    if not ok: print(r.stdout[-600:], r.stderr[-600:])
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
