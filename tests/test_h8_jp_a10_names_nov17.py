#!/usr/bin/env python3
"""Handoff 8 fix 7 (switch KPC_JP_A10_NAMES): Japan's national A10 file names each park by a code; the v3 codelist row is
'102 | 網走' - a bare name with no 公園 in it - so pull_a10n kept only the 5 areas whose names say 公園 and dropped every
national / quasi-national park. With the switch on it takes the name cell next to the code and adds the kind from A10_003.
Part 1 runs the real pull_a10n on a saved excerpt of the public MLIT codelist page (rows copied as served on Nov 17 2026) and a
tiny A10-style shapefile built here (no network: fetch_bytes is replaced). Part 2 runs the real kpc_world_key.py offline
(tests/kpc_pinfill_fixture.py) on the areas part 1 produced: JP-0102 Abashiri, JP-0132 Biwako and JP-0116 Minami-Boso get a
candidate with the switch on and none with it off; a name that already says 公園 (野幌森林公園, code 208) is the same either way.
Run:  python3 tests/test_h8_jp_a10_names_nov17.py   (needs pyshp and pykakasi, as the workflow installs)"""
import sys as _sys; _sys.dont_write_bytecode = True
import io, json, os, pathlib, sys, zipfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests')); sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_pinfill_fixture as H  # noqa: E402  (refuses every socket on import)
import run_match_tests as RMT  # noqa: E402
import shapefile  # noqa: E402
RESULTS = []
def check(ok, what): RESULTS.append((bool(ok), what)); print(('PASS' if ok else 'FAIL') + ': ' + what, flush=True)

CODELIST = '''<html><body><table>
<tr align="center"> 
    <td  bgcolor="#CCCCCC" width="80" ><b>コード</b></td>
    <td  bgcolor="#CCCCCC" width="200"><b>公園名称</b></td>
  </tr>
<tr>
    <td>102</td><td>網走</td>
  </tr>
<tr>
    <td>117</td><td>南房総</td>
  </tr>
<tr>
    <td>132</td><td>琵琶湖</td>
  </tr>
<tr>
    <td>018</td><td>南アルプス</td>
  </tr>
<tr>
    <td>022</td><td>瀬戸内海</td>
  </tr>
<tr align="center"> 
    <td  bgcolor="#CCCCCC" width="80" ><b>コード</b></td>
    <td  bgcolor="#CCCCCC" width="200"><b>公園名称</b></td>
    <td  bgcolor="#CCCCCC" width="150"><b>都道府県名</b></td>
  </tr>
<tr>
    <td>208</td><td>野幌森林公園</td><td>北海道</td>
  </tr>
</table></body></html>'''.encode('utf-8')
PINS = {'018': (35.6421, 138.217, '1'), '022': (34.7338, 134.397, '1'), '102': (44.1892, 143.748, '2'), '117': (35.1161, 140.122, '2'), '132': (35.2377, 136.166, '2'), '208': (43.04, 141.51, '3')}
def a10_zip():
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    w = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON, encoding='cp932')
    w.field('A10_003', 'C', 2); w.field('A10_005', 'C', 6)
    for code, (la, lo, cls) in PINS.items():
        d = .05; w.poly([[[lo - d, la - d], [lo - d, la + d], [lo + d, la + d], [lo + d, la - d], [lo - d, la - d]]]); w.record(cls, code)
    w.close(); z = io.BytesIO()
    with zipfile.ZipFile(z, 'w') as zf:
        for ext, b in (('shp', shp), ('shx', shx), ('dbf', dbf)): zf.writestr(f'A10-10_00-g_NaturalParkArea.{ext}', b.getvalue())
    return z.getvalue()
ZIP = a10_zip()
LABEL = 'MLIT natural park areas, national file FY2010 (A10-10)'

def pull(sw):
    os.environ['KPC_JP_A10_NAMES'] = sw
    wk = RMT._load('kpc_world_key.py', '\nfor cc in COUNTRIES:')
    wk.fetch_bytes = lambda u, **k: CODELIST if 'codelist' in u else ZIP
    wk.notice = lambda *a, **k: None
    return wk.pull_a10n(LABEL, 'https://nlftp.mlit.go.jp/ksj/gml/data/A10/A10-10/A10-10_00-g_GML.zip')
off, on = pull('0'), pull('1'); os.environ.pop('KPC_JP_A10_NAMES', None)
byc = lambda rs: {r['_a']['A10_005']: r['n'] for r in rs}
check(byc(off) == {'208': '野幌森林公園'}, f"OFF (today): only the name that says 公園 is kept: {byc(off)}")
check(byc(on) == {'018': '南アルプス国立公園', '022': '瀬戸内海国立公園', '102': '網走国定公園', '117': '南房総国定公園', '132': '琵琶湖国定公園', '208': '野幌森林公園'},
      f"ON: the bare names are kept with their kind from A10_003: {byc(on)}")

def saved(rs):
    out = []
    for r in rs:
        q = {k: v for k, v in r.items() if k != '_f'}; q['_k0'] = sorted(q.get('_k0') or []); out.append(q)
    return out
PARKS = {'JP': {'JP-0102': ['Abashiri Quasi-National Park', '', 'Quasi-National Park', '', '', 44.1892, 143.748, None, None, None, 'HK'],
                'JP-0132': ['Biwako Quasi-National Park', '', 'Quasi-National Park', '', '', 35.2377, 136.166, None, None, None, 'KY'],
                'JP-0116': ['Minami-Boso Quasi-National Park', '', 'Quasi-National Park', '', '', 35.1161, 140.122, None, None, None, 'CH'],
                'JP-0019': ['Minami Alps National Park', '', 'National Park', '', '', 35.6421, 138.217, None, None, None, 'NN'],
                'JP-1544': ['Ako Seaside Prefectural Park', '', 'Prefectural Park', '', '', 34.7338, 134.397, None, None, None, 'HG'],
                'JP-9208': ['Nopporo Shinrin Koen Prefectural Natural Park', '', 'Prefectural Natural Park', '', '', 43.04, 141.51, None, None, None, 'HK']}}
# today's current layer: the Ministry of the Environment area 321 '南アルプス' holds JP-0019's pin (joined today by the pin rule)
MOE = [{'id': 321, 'n': '南アルプス', 'ty': '', 'src': 'Ministry of the Environment national parks (Esri Japan)', '_bb': [138.20011, 35.56971, 138.26696, 35.70276],
        '_r': [H.ring(35.6421, 138.217, .03)], '_a': {'FID': 321, '名称': '南アルプス'}, 'code': '', 'dc': ''}]
def build(rs):
    r, out = H.world_build(['JP'], PARKS, {'JP': MOE + saved(rs)}, {'KPC_JP_A10_NAMES': '1' if rs is on else '0'})
    k = json.loads(out.get('data/world-key/JP.json') or '{}').get('parks') or {}
    return r, k
r0, k0 = build(off); r1, k1 = build(on)
check(r0.returncode == 0 and r1.returncode == 0, f'both offline world builds ran (exit {r0.returncode} / {r1.returncode})' + ('' if r1.returncode == 0 else (r1.stderr or r1.stdout)[-400:]))
got = lambda k, ref: [q[1] for q in ((k.get(ref) or {}).get('m') or []) + ((k.get(ref) or {}).get('c') or [])]
for ref in ('JP-0102', 'JP-0132', 'JP-0116'):
    check(not got(k0, ref) and got(k1, ref), f'{ref} {PARKS["JP"][ref][0]}: OFF no candidate; ON a candidate {got(k1, ref)}')
ids = lambda k, ref: [q[0] for q in (k.get(ref) or {}).get('m') or []]
check(ids(k0, 'JP-0019') == ids(k1, 'JP-0019') == [321], "must NOT: JP-0019 Minami Alps stays joined to today's Ministry area 321 (the FY2010 area only fills gaps; no second outline, no ambiguous pin)")
check(not ids(k0, 'JP-1544') and not ids(k1, 'JP-1544'), "must NOT: JP-1544 Ako Seaside Prefectural Park, whose pin is inside the new 瀬戸内海国立公園 area, is not joined to it (new areas join by name only, never by the pin alone)")
check(got(k0, 'JP-9208') == got(k1, 'JP-9208'), 'must NOT: a park whose area name already said 公園 is the same either way')
n = sum(1 for ok, _ in RESULTS if ok); print(f'\n{n}/{len(RESULTS)} checks passed'); sys.exit(0 if n == len(RESULTS) else 1)
