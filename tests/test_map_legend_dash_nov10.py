"""Park Commander map, Nov 10: the Boundaries legend button sits above the credits line on phones, and outlines
joined to a POTA reference draw solid (dashed only for no reference). Static checks plus a Node run of the
gis-overlays.js join logic against the repo's own outline files and POTA list (no network)."""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name); ok = ok and bool(cond)
g = (ROOT / 'gis-overlays.js').read_text(encoding='utf-8')
x = (ROOT / 'kpc-map-extras.js').read_text(encoding='utf-8')
check('an outline file\'s own POTA reference (properties.ref) counts as its join', 'const ownRef=' in g and '!!ownRef(f)||keyJoin(f).length>0||matchPota(f)' in g and 'const own=ownRef(f)' in g)
check('"no POTA reference" is not remembered before the POTA list and answer key are ready', 'if(v||joinsReady())f._pota=v;else whenJoins()' in g)
check('drawn layers are restyled when the POTA list or answer key arrives (forest boundary line left alone)', 'function restyleBounds()' in g and '!bounds[k].proc' in g and 'delete f._pota' in g)
check('dashed stays only for features with no join; OpenStreetMap outlines keep their dash-dot', "dashArray:'12 5 2 5'" in g and "f=>!has(f)?{color:'#ff2a2a'" in g)
check('bottom-left map buttons are lifted above the credits line', '__kpcLiftBL' in x and "'.leaflet-bottom.leaflet-left'" in x and 'leaflet-control-attribution' in x)
check('credits are never hidden by the lift', 'display:none' not in x.split('__kpcLiftBL')[1])
pages = list(ROOT.glob('*.html')) + list(ROOT.glob('.claude/build/**/*.html'))
want = {'gis-overlays': '?v=20261111z', 'kpc-map-extras': '?v=20261111rule', 'kpc-answer-key': '?v=20261110key'}
for name, stamp in want.items():
    vs = {}
    for p in pages:
        for m in re.finditer(r'src="' + re.escape(name) + r'\.js(\?v=[^"]*)?"', p.read_text(encoding='utf-8', errors='replace')):
            vs.setdefault(m.group(1), []).append(p.name)
    check(f'{name}.js has one bumped ?v= everywhere: {sorted(vs)}', list(vs) == [stamp])
# every PAD-US park outline carries a ref that is in the POTA list the page loads
pad = json.loads((ROOT / 'ky-padus-parks.geojson').read_text(encoding='utf-8'))
rows = json.loads((ROOT / 'locations-ky.json').read_text(encoding='utf-8'))['rows']
pota = {r[1] for r in rows if r[0] == 'POTA'}
refs = [f['properties'].get('ref') for f in pad['features']]
check(f'all {len(refs)} "More official park outlines" carry a POTA ref the page knows', refs and all(r in pota for r in refs))
# run the join helper in Node with a tiny Leaflet/DOM stub: every PAD-US outline must count as joined
js = r'''
const fs=require('fs');global.window=global;global.document={getElementById:()=>null,querySelector:()=>null,querySelectorAll:()=>[]};
global.matchMedia=()=>({matches:false});global.fetch=()=>Promise.resolve({ok:false});global.L={};
const rows=JSON.parse(fs.readFileSync('locations-ky.json','utf8')).rows;global.data=rows;
eval(fs.readFileSync('kpc-answer-key.js','utf8'));eval(fs.readFileSync('gis-overlays.js','utf8'));
const pad=JSON.parse(fs.readFileSync('ky-padus-parks.geojson','utf8')).features;
const res=pad.map(f=>({ref:f.properties.ref,own:kpcGIS.ownRef(f),joined:kpcGIS.matchPota(f).some(m=>m.d[1]===f.properties.ref&&m.why.startsWith('name'))}));
console.log(JSON.stringify(res));'''
try:
    out = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, timeout=120)
    res = json.loads(out.stdout.strip().splitlines()[-1])
    check(f'Node: each PAD-US outline is joined to its own ref ({sum(r["joined"] for r in res)}/{len(res)})', res and all(r['joined'] and r['own'] == r['ref'] for r in res))
except Exception as e:
    check(f'Node join run ({e}; {out.stderr[-300:] if "out" in dir() else ""})', False)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
