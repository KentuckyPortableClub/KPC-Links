#!/usr/bin/env python3
"""KPC owner, 2026-11-11 (job 3, loader half): the public pages read the Canada park outlines and the Kentucky map files from
data/released only (KPCREL): Canada through data/released/canada-bounds/INDEX.json (RELEASED.json subs), Kentucky as ky/<name>
(a file in parts is joined back, all parts or nothing). No public page fetches data/canada-bounds/, data/ky-answer-key.json or a
root ky-*.geojson any more except through KPCREL; Map Rep pages (KPC_WORKING_COPY) still read the working copies.
Offline: node with a stub fetch that serves this checkout's own files (nothing leaves the machine). Prints PASS / FAIL lines.
The headless Chrome check of the five pages is tests/loaders_released_ca_ky_nov11_browser.py (not in the full suite)."""
import json, pathlib, re, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_release as R

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)

STAMP = '20261111zr'
LOADERS = ['kpc-bounds.js', 'kpc-gps.js', 'kpc-padus-layer.js', 'kpc-us-planner.js']
src = {n: (ROOT / n).read_text(encoding='utf-8') for n in LOADERS}
blk = lambda s: s[s.index('/* >>> kpc_released'):s.index('/* <<< kpc_released */')] + '/* <<< kpc_released */'
B = blk(src['kpc-bounds.js'])

# ---- 1. the block: four identical copies, and what it learned
check('the four loaders carry the same KPCREL block', len({blk(s) for s in src.values()}) == 1)
check('the block: canada-bounds/ is area CA, ky/ is area KY, UNRELEASED_WORKING stays []',
      "[/^(ca-key|canada-bounds)\\//, 'CA']" in B and "[/^ky\\//, 'KY']" in B and 'var UNRELEASED_WORKING = [];' in B)
check('the block maps data/ky-answer-key.json and a root ky-*.geojson to ky/<name>', "replace(/^(ky-[a-z0-9-]+\\.geojson|ky-answer-key\\.json)$/, 'ky/$1')" in B)
check('the block reads the sub-index with its own version and only when its sha / time equal the area row',
      "'data/released/' + s.file + '?v=' + s.v" in B and 'x.sha !== a.sha || x.time !== a.time' in B and 'Date.now() - c.at > 60000' in B)
check('the working-copy part reader knows plain .geojson parts', "replace(/(\\.geojson\\.gz|\\.geojson|\\.json)$/, '.p' + i + '$1')" in B)
check('the sub-index is not kept in localStorage (only RELEASED.json is): HTTP cache under its ?v= + the saved copy',
      B.count('localStorage.setItem') == 1 and "w.localStorage.setItem(LAST, JSON.stringify(d))" in B)

# ---- 2. grep: no public page fetches a working Canada outline or Kentucky file except through KPCREL
ALLOW = {'kpc-maprep-check.js': 'Map Rep review tool: reads the working copies on purpose (the key being reviewed)',
         'kpc-lc-map.js': 'dead code: no page loads it'}
pages = {p.name: p.read_text(encoding='utf-8', errors='replace') for p in sorted(ROOT.glob('*.js')) + sorted(ROOT.glob('*.html'))}
KYF = r"(?:data/ky-answer-key\.json|ky-[a-z0-9-]+\.geojson)"
direct = [re.compile(r"(?:fetch|jget|dget|getJSON|getJson|dfetch|KPC\.dataUrl|tf)\(\s*['\"]" + KYF),
          re.compile(r"(?:fetch|jget|dget|getJSON|getJson|dfetch|tf)\(\s*['\"]data/canada-bounds/"),
          re.compile(r"'data/canada-bounds/' \+ encodeURIComponent\(ref\) \+ '\.json\?v="),
          re.compile(r"(?:fetch|jget)\((?:s|B\[k\]|T\[k\]|L|tr)\.file\b"), re.compile(r"fetch\(FILES\[t\]\)"), re.compile(r"tf\(t\.f\)"),
          re.compile(r"dget\('data/canada-bounds/")]
def hits(text): return [m.group(0) for rx in direct for m in rx.finditer(text)]
bad = {n: hits(s) for n, s in pages.items() if n not in ALLOW and hits(s)}
check('no root *.js / *.html fetches data/canada-bounds/, data/ky-answer-key.json or a root ky-*.geojson except through KPCREL'
      + (f' ({bad})' if bad else '') + f"; allowed: {', '.join(f'{k} ({v})' for k, v in ALLOW.items())}", not bad)
r = subprocess.run(['git', 'show', 'HEAD~1:gis-overlays.js'], cwd=ROOT, capture_output=True, text=True)
if r.returncode == 0 and 'kpcRel' not in r.stdout:
    check('the grep finds the old direct reads (checked on the commit before this change)', len(hits(r.stdout)) >= 2)
check('every non-block reader waits for KPCREL (never the working copy when it is missing)',
      all("addEventListener('kpcrel'" in pages[n] for n in ('gis-overlays.js', 'kpc-planner.js', 'kpc-map-extras.js', 'kpc-answer-key.js', 'kpc-park-control.js', 'kpc-map-tools.js', 'kpc-guide-pota.js'))
      and "w.dispatchEvent(new Event('kpcrel'))" in B)
check('the POTA guide page loads a KPCREL file before its script (it reads the wild river corridors)',
      pages['kpc-guide-pota.html'].index(f'kpc-padus-layer.js?v={STAMP}') < pages['kpc-guide-pota.html'].index(f'kpc-guide-pota.js?v={STAMP}'))
check('gis-overlays: a layer whose released copy did not load never falls back to the working file name',
      "if(/^ky-[a-z0-9-]+\\.geojson$/.test(s.live))throw Error('the saved copy did not load')" in pages['gis-overlays.js'])
check('kpc-ky-data.json is read as before (not through KPCREL)', "fetch('kpc-ky-data.json')" in pages['kpc-park-control.js'] and 'kpcRel(\'kpc-ky-data' not in ''.join(pages.values()))

# ---- 3. offline save lists
off, kit, trip, sw = pages['kpc-offline.js'], pages['kpc-kit.js'], pages['kpc-trip-offline.js'], (ROOT / 'kpc-finder-sw.js').read_text(encoding='utf-8')
files_block = off[off.index('const FILES = ['):off.index('];', off.index('const FILES = ['))]
check('kpc-offline.js: FILES names no working Kentucky map file; KY_REL is saved as released copies (KPCREL.need)',
      not re.search(KYF, files_block) and 'KPCREL.need(KY_REL)' in off and 'ky-overlaps.geojson' in off[off.index('const KY_REL'):])
check('kpc-kit.js: the Kentucky layers and a Canada park outline are saved as released copies (KPCREL.need), not B.KY files',
      'B.KY.map(L => L.file), B.tilesUsed()' not in kit and "KPCREL.need(B.KY.map(L => L.file).concat(" in kit and "'data/canada-bounds/' + p.c + '.json'" in kit)
check('kpc-us-planner.js: a Canada stop is saved from data/released (KPCREL.need) with the INDEX', "KPCREL.need(ca)" in pages['kpc-us-planner.js'])
check('kpc-trip-offline.js and the service worker keep the ?v= of every data/released/ file (ky/ and canada-bounds/ included)',
      "const REL = /\\/data\\/released\\//;" in trip and "const RELEASED = /\\/data\\/released\\//;" in sw)
check('cache names unchanged (kpc-finder-v1 / kpc-tiles-v1)', "const APP = 'kpc-finder-v1';" in sw and "const TILES = 'kpc-tiles-v1';" in sw and "APP = 'kpc-finder-v1', TILES = 'kpc-tiles-v1'" in off)

# ---- 4. stamps: one new ?v= for every script this change touched, on every page and page source
TOUCHED = ['gis-overlays.js', 'kpc-answer-key.js', 'kpc-bounds.js', 'kpc-gps.js', 'kpc-gps-wire.js', 'kpc-guide-pota.js', 'kpc-kit.js', 'kpc-map-extras.js',
           'kpc-map-tools.js', 'kpc-offline.js', 'kpc-padus-layer.js', 'kpc-park-control.js', 'kpc-planner.js', 'kpc-us-planner.js']
srcs = [p for p in list(ROOT.glob('*.html')) + list((ROOT / '.claude/build').rglob('*.html')) + list(ROOT.glob('*.js'))]
vs = {n: set() for n in TOUCHED}
for p in srcs:
    t = p.read_text(encoding='utf-8', errors='replace')
    for n in TOUCHED: vs[n] |= set(re.findall(r'(?<![\w.-])' + re.escape(n) + r'\?v=([A-Za-z0-9_-]+)', t))
check(f'every touched script is loaded with ?v={STAMP} everywhere', all(v == {STAMP} for v in vs.values()) and all(vs.values()))

# ---- 5. the block in node against this checkout's real released files
node = shutil.which('node')
rel = ROOT / 'data/released'
idx = json.loads((rel / 'RELEASED.json').read_text()) if (rel / 'RELEASED.json').exists() else {}
if node and 'subs' in idx and 'KY' in idx.get('areas', {}):
    IX = json.loads((rel / idx['subs']['canada-bounds/']['file']).read_text())
    refs = sorted(IX['files'])
    ca1, ca2 = refs[0][len('canada-bounds/'):-5], refs[-1][len('canada-bounds/'):-5]
    nolist = next(f'CA-{i:04d}' for i in range(1, 10000) if f'canada-bounds/CA-{i:04d}.json' not in IX['files'])
    JS = r"""
const fs = require('fs'), path = require('path'), ROOT = %(root)s, BLOCK = %(block)s, CA1 = %(ca1)s, CA2 = %(ca2)s, NOLIST = %(nolist)s;
globalThis.window = globalThis; const store = {}; let asked = [], over = {}, clock = 0;
const realNow = Date.now; Date.now = () => realNow() + clock;
window.localStorage = { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); } };
function resp(status, buf) { return { ok: status === 200, status, json: () => Promise.resolve(JSON.parse(buf.toString('utf8'))), arrayBuffer: () => Promise.resolve(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength)) }; }
window.fetch = (u, o) => { asked.push([String(u), (o || {}).cache || '']); const p = String(u).split('?')[0];
  if (/^https?:/.test(p)) return Promise.resolve(resp(404, Buffer.from('')));
  if (p in over) return Promise.resolve(typeof over[p] === 'number' ? resp(over[p], Buffer.from('')) : resp(200, Buffer.from(over[p])));
  const f = path.join(ROOT, p); return Promise.resolve(fs.existsSync(f) ? resp(200, fs.readFileSync(f)) : resp(404, Buffer.from(''))); };
const fresh = () => { delete window.KPCREL; delete window.KPC_WORKING_COPY; (0, eval)(BLOCK); };
const stable = v => Array.isArray(v) ? '[' + v.map(stable).join(',') + ']' : v && typeof v === 'object' ? '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + stable(v[k])).join(',') + '}' : JSON.stringify(v);
const working = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const same = (j, p) => !!j && stable(j) === stable(working(p));
const non = () => asked.filter(a => !a[0].startsWith('data/released/'));
(async () => {
  const o = {};
  fresh(); asked = [];
  const c1 = await KPCREL.get('data/canada-bounds/' + CA1 + '.json'), c2 = await KPCREL.get('data/canada-bounds/' + CA2 + '.json');
  await Promise.all([KPCREL.get('data/canada-bounds/' + CA1 + '.json'), KPCREL.get('data/canada-bounds/' + CA2 + '.json')]);
  o.caListed = { same1: same(c1, 'data/canada-bounds/' + CA1 + '.json'), same2: same(c2, 'data/canada-bounds/' + CA2 + '.json'), asked: asked.slice(), non: non(), state: await KPCREL.state('data/canada-bounds/' + CA1 + '.json') };
  asked = []; o.caNot = { got: await KPCREL.get('data/canada-bounds/' + NOLIST + '.json'), state: await KPCREL.state('data/canada-bounds/' + NOLIST + '.json'), asked: asked.slice() };
  // the INDEX does not load: nothing (never the working file); asked again only after a minute
  fresh(); const IXP = 'data/released/' + JSON.parse(fs.readFileSync(path.join(ROOT, 'data/released/RELEASED.json'))).subs['canada-bounds/'].file;
  over[IXP] = 503; asked = [];
  const f1 = await KPCREL.get('data/canada-bounds/' + CA1 + '.json'), s1 = await KPCREL.state('data/canada-bounds/' + CA1 + '.json'), n1 = asked.filter(a => a[0].startsWith(IXP)).length;
  await KPCREL.get('data/canada-bounds/' + CA2 + '.json'); const n2 = asked.filter(a => a[0].startsWith(IXP)).length;
  delete over[IXP]; clock += 61000; const f3 = await KPCREL.get('data/canada-bounds/' + CA1 + '.json'); const n3 = asked.filter(a => a[0].startsWith(IXP)).length; clock = 0;
  o.idxFail = { f1, s1, n1, n2, n3, same3: same(f3, 'data/canada-bounds/' + CA1 + '.json'), non: non() };
  // an INDEX of another release (sha differs): nothing, after one fresh try
  fresh(); const ix = JSON.parse(fs.readFileSync(path.join(ROOT, IXP))); ix.sha = 'f'.repeat(40); over[IXP] = JSON.stringify(ix); asked = [];
  o.idxOther = { got: await KPCREL.get('data/canada-bounds/' + CA1 + '.json'), modes: asked.filter(a => a[0].startsWith(IXP)).map(a => a[1]), non: non() }; delete over[IXP];
  // RELEASED.json does not load: the last good copy (kept by the first read) still finds the Canada INDEX of that release
  fresh(); await KPCREL.index(); fresh(); over['data/released/RELEASED.json'] = 503; asked = [];
  o.lastGood = { same: same(await KPCREL.get('data/canada-bounds/' + CA1 + '.json'), 'data/canada-bounds/' + CA1 + '.json'), non: non() }; delete over['data/released/RELEASED.json'];
  // Kentucky
  fresh(); asked = [];
  const ky = {};
  for (const [p, w] of [['ky-usace.geojson', 'ky-usace.geojson'], ['ky-hunting-areas.geojson', 'ky-hunting-areas.geojson'], ['data/ky-answer-key.json', 'data/ky-answer-key.json'], ['ky-overlaps.geojson', 'ky-overlaps.geojson'], ['ky-sheltowee.geojson', 'ky-sheltowee.geojson']]) {
    const j = await KPCREL.get(p); ky[p] = { same: same(j, w), n: j && j.features ? j.features.length : -1, wn: (working(w).features || []).length, part: !!(j && j.kpc_part) };
  }
  o.ky = ky; o.kyAsked = asked.slice(); o.kyNon = non();
  fresh(); over['data/released/ky/ky-usace.p2.geojson'] = 404; asked = [];
  o.kyMissing = { got: await KPCREL.get('ky-usace.geojson'), non: non() }; delete over['data/released/ky/ky-usace.p2.geojson'];
  fresh(); const p3 = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/released/ky/ky-usace.p3.geojson'))); p3.kpc_part[2] = '000000000000'; over['data/released/ky/ky-usace.p3.geojson'] = JSON.stringify(p3);
  o.kyTag = { got: await KPCREL.get('ky-usace.geojson') }; delete over['data/released/ky/ky-usace.p3.geojson'];
  fresh(); asked = []; o.kyNot = { got: await KPCREL.get('ky-not-on-the-list.geojson'), state: await KPCREL.state('ky-not-on-the-list.geojson'), non: non() };
  // Map Rep: the working copies, as before
  fresh(); window.KPC_WORKING_COPY = true; asked = [];
  const wu = await KPCREL.get('ky-usace.geojson'), wc = await KPCREL.get('data/canada-bounds/' + CA1 + '.json');
  o.rep = { usace: same(wu, 'ky-usace.geojson'), ca: same(wc, 'data/canada-bounds/' + CA1 + '.json'), asked: asked.map(a => a[0].split('?')[0]) };
  fresh(); o.need = await KPCREL.need(['ky-usace.geojson', 'data/canada-bounds/' + CA1 + '.json', 'data/canada-bounds/' + NOLIST + '.json', 'kpc-ky-data.json']);
  console.log(JSON.stringify(o));
})().catch(e => console.log(JSON.stringify({ fatal: String(e && e.stack || e) })));
"""
    results = {}
    for n in LOADERS:
        with tempfile.TemporaryDirectory() as t:
            p = pathlib.Path(t) / 'r.js'
            p.write_text(JS % {'root': json.dumps(str(ROOT)), 'block': json.dumps(blk(src[n])), 'ca1': json.dumps(ca1), 'ca2': json.dumps(ca2), 'nolist': json.dumps(nolist)})
            r = subprocess.run([node, str(p)], capture_output=True, text=True, timeout=120)
        try: results[n] = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception: results[n] = {'fatal': (r.stdout[-400:] + r.stderr[-400:])}
    o = results['kpc-bounds.js']
    check('node: the four copies give the very same answers', 'fatal' not in o and all(results[n] == o for n in LOADERS))
    if 'fatal' in o: print('  ', o['fatal'][:400])
    else:
        v = idx['subs']['canada-bounds/']['v']; ixu = f"data/released/{idx['subs']['canada-bounds/']['file']}?v={v}"
        c = o['caListed']
        check('Canada park listed in the INDEX: the released copy, equal to the working file', c['same1'] and c['same2'] and c['state'] == 'released'
              and [f'data/released/canada-bounds/{ca1}.json?v={IX["files"][f"canada-bounds/{ca1}.json"][0][1]}', 'force-cache'] in c['asked'])
        check('the INDEX is read once per page, with its version from RELEASED.json subs, only when a Canada outline is asked for',
              [a for a in c['asked'] if 'INDEX.json' in a[0]] == [[ixu, 'force-cache']])
        check('no request for a working canada-bounds path or to the KPC-Data host', not c['non'] and all(a[0].startswith('data/released/') for a in c['asked'] + o['caNot']['asked']))
        check('CA released but this park not listed: nothing (state not listed), no request at all', o['caNot']['got'] is None and o['caNot']['state'] == 'not listed' and o['caNot']['asked'] == [])
        f = o['idxFail']
        check('INDEX fails: nothing (no index), not the working file; not asked again within a minute; asked again after it and then works',
              f['f1'] is None and f['s1'] == 'no index' and f['n1'] == 2 and f['n2'] == 2 and f['n3'] == 3 and f['same3'] and not f['non'])
        check('an INDEX of another release (sha differs from areas.CA): nothing, after one fresh (reload) try', o['idxOther']['got'] is None and o['idxOther']['modes'] == ['force-cache', 'reload'] and not o['idxOther']['non'])
        check('RELEASED.json does not load: the last good copy (localStorage) and the INDEX of that release still give the outline', o['lastGood']['same'] and not o['lastGood']['non'])
        k = o['ky']
        for nm, parts in (('ky-usace.geojson', 3), ('ky-hunting-areas.geojson', 4)):
            check(f'{nm}: its {parts} released parts joined = the working FeatureCollection ({k[nm]["wn"]} features, same content)',
                  len(idx['files'][f'ky/{nm}']) == parts and k[nm]['same'] and k[nm]['n'] == k[nm]['wn'] and not k[nm]['part'])
        check('the answer key, ky-overlaps.geojson and a trail line come from data/released/ky/ and equal the working files',
              all(k[p]['same'] for p in ('data/ky-answer-key.json', 'ky-overlaps.geojson', 'ky-sheltowee.geojson'))
              and all(any(a[0].startswith(f'data/released/ky/{n}?v=') for a in o['kyAsked']) for n in ('ky-answer-key.json', 'ky-overlaps.geojson', 'ky-usace.p3.geojson')))
        check('Kentucky: no working-path request at all', not o['kyNon'])
        check('a missing part fails the whole layer (never a partial layer)', o['kyMissing']['got'] is None and not o['kyMissing']['non'])
        check('a part of another save (tag differs) fails the whole layer', o['kyTag']['got'] is None)
        check('KY released but the file not listed: nothing, no working fetch', o['kyNot']['got'] is None and o['kyNot']['state'] == 'not listed' and not o['kyNot']['non'])
        check('Map Rep (KPC_WORKING_COPY): the working copies, as before', o['rep']['usace'] and o['rep']['ca'] and 'ky-usace.geojson' in o['rep']['asked']
              and f'data/canada-bounds/{ca1}.json' in o['rep']['asked'] and not any(a.startswith('data/released/ky') for a in o['rep']['asked']))
        want = ['data/released/RELEASED.json'] + [f'data/released/{p}?v={vv}' for p, vv in idx['files']['ky/ky-usace.geojson']] + [
            f'data/released/canada-bounds/{ca1}.json?v={IX["files"][f"canada-bounds/{ca1}.json"][0][1]}', ixu]
        check('KPCREL.need: RELEASED.json, every part with its ?v=, the outline and the INDEX (not listed / not released kinds add nothing)', o['need'] == want)
else: print('SKIP node not installed or the Canada / Kentucky release is not in data/released: the node run')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
