#!/usr/bin/env python3
"""Display copy from the outline store (KPC owner, 2026-11-13): tools/kpc_display_copy.py and kpc-outline-display.js.

Everything here is SYNTHETIC: a small fake store is written into a temporary folder by this test (made-up parks in the ocean
off Africa, at 0-1 degrees), in the store's format 1. No real outline, no network (sockets are blocked), no repo file written.
Checks: the store reader's checksums, the licence gate (and WDPA even in a private preview), a park with one unlicensed tract
falls back whole, doubtful / far-apart joins fall back, the draw-once rule, the 3,000-point cap and the error it costs, the fine
level, holes, parts under the size limit, byte-identical rebuilds, the preview stamp, and the browser loader (switch off =
nothing new; on = new + today's for the rest; a preview, a bad part or a missing index = today's file only).
Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import gzip, hashlib, io, json, math, os, pathlib, shutil, socket, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))


def _no_net(*a, **k): raise OSError('network blocked in this test')


socket.socket.connect = _no_net
socket.create_connection = _no_net
import kpc_display_copy as K  # noqa: E402

FAILS = []


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: FAILS.append(name)


# ---- a synthetic store writer (format 1) ------------------------------------------------------------------------------------
def enc(ring):
    out, px, py = [], 0, 0
    for i, (x, y) in enumerate(ring):
        xi, yi = int(round(x * 1e6)), int(round(y * 1e6))
        out += [xi, yi] if i == 0 else [xi - px, yi - py]
        px, py = xi, yi
    return out


def circle(cx, cy, r_deg, n, wobble=0.0, clockwise=True, phase=0.0):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n * (-1 if clockwise else 1)
        rr = r_deg * (1 + wobble * math.sin(7 * a + phase) + wobble * 0.5 * math.sin(23 * a))
        pts.append((round(cx + rr * math.cos(a), 6), round(cy + rr * math.sin(a), 6)))
    pts.append(pts[0])
    return pts


def record(key, layer, rings, licence='OPEN; credit: Test Agency', url='https://example.invalid/arcgis/rest/services/x/MapServer/0'):
    er = [enc(r) for r in rings]
    return {'key': key, 'layer': layer, 'record_id': key, 'layer_url': url, 'agency_label': 'Test Agency ' + layer,
            'record_name': key, 'licence': licence, 'source': 'live', 'rings': er, 'points': sum(len(r) for r in rings),
            'sha256': K.geometry_sha256(er), 'q': 6, 'use': True}


def write_store(d, area, parks, index_licence=True, extra=None):
    d.mkdir(parents=True, exist_ok=True)
    fname = f'{area}.kpcstore.json.gz'
    buf, idx, off = io.BytesIO(), {}, 0
    head = gzip.compress(json.dumps({'kpcstore': 1, 'area': area})[:-1].encode() + b',"parks":[\n', 9, mtime=0)
    buf.write(head); off = len(head)
    for i, p in enumerate(parks):
        txt = (',\n' if i else '') + json.dumps(p, separators=(',', ':'))
        m = gzip.compress(txt.encode(), 9, mtime=0)
        fp = hashlib.sha256('|'.join(r['sha256'] for r in p['records']).encode()).hexdigest()
        e = {'file': fname, 'o': off, 'n': len(m), 'grade': p['grade'], 'circle': False, 'records': [r['key'] for r in p['records']],
             'points': sum(r['points'] for r in p['records']), 'fp': fp}
        if index_licence: e['licence'] = {r['key']: (r.get('licence') or 'not recorded') for r in p['records']}
        e.update((extra or {}).get(p['ref'], {}))
        idx[p['ref']] = e
        buf.write(m); off += len(m)
    buf.write(gzip.compress(b']}\n', 9, mtime=0))
    (d / fname).write_bytes(buf.getvalue())
    sha = hashlib.sha256(buf.getvalue()).hexdigest()
    (d / 'index.json').write_text(json.dumps({'format': 1, 'area': area, 'files': {fname: {'sha256': sha}}, 'parks': idx}))
    return d / fname


def park(ref, recs, name=None):
    return {'ref': ref, 'name': name or ('Test Park ' + ref), 'grade': 'official', 'circle': False, 'pin': None, 'records': recs}


tmp = pathlib.Path(tempfile.mkdtemp(prefix='kpc-display-test-'))
try:
    store = tmp / 'store'
    big = [circle(0.5 + 0.02 * k, 0.5, 0.008, 900, wobble=0.05, phase=k) for k in range(6)]   # 6 tracts x 900 points: over the cap
    parks = [
        park('US-0001', [record('a1', 'lay1', [circle(0.1, 0.1, 0.01, 200, wobble=0.03)])]),                     # one tract, small
        park('US-0002', [record('b1', 'lay1', [circle(0.2, 0.1, 0.01, 120)]),
                         record('b2', 'lay2', [circle(0.2, 0.1, 0.01, 120)]),                                       # same land, same points
                         record('b3', 'lay3', [circle(0.2, 0.1, 0.0100001, 97)])]),                                  # same land, other vertices
        park('US-0003', [record('c1', 'lay1', [circle(0.3, 0.1, 0.01, 80)]),
                         record('c2', 'lay2', [circle(0.31, 0.1, 0.004, 60)], licence='')]),                        # one tract unlicensed
        park('US-0004', [record('d1', 'lay1', [circle(0.4, 0.1, 0.01, 60)]),
                         record('d2', 'lay1', [circle(0.9, 0.1, 0.01, 60)])]),                                       # tracts ~55 km apart
        park('US-0005', [record('e%d' % k, 'lay1', [r]) for k, r in enumerate(big)]),                               # over the cap
        park('US-0006', [record('f1', 'wdpa', [circle(0.6, 0.2, 0.01, 50)], licence='OPEN; credit: Protected Planet WDPA',
                                url='https://data-gis.unep-wcmc.org/server/rest/services/ProtectedSites/The_World_Database_of_Protected_Areas/MapServer/1')]),
        park('US-0007', [record('g1', 'lay1', [circle(0.7, 0.2, 0.02, 100), circle(0.7, 0.2, 0.005, 40, clockwise=False)])]),  # a hole
        park('US-0008', [record('h1', 'lay4', [circle(0.8, 0.2, 0.01, 50)], licence='RESTRICTED; credit: X')]),
        park('US-0009', [record('i1', 'lay1', [circle(0.1, 0.3, 0.01, 50)])]),                                      # in the doubtful CSV
        park('US-0010', [record('j1', 'lay5', [circle(0.2, 0.3, 0.01, 50)], licence='NON-COMMERCIAL; credit: County Parks')]),
        park('US-0011', [record('k%d' % k, 'lay1', [circle(0.3 + 0.005 * (k % 26), 0.4 + 0.005 * (k // 26), 0.002, 8, phase=k)])
                         for k in range(650)]),                                                                       # 650 small tracts
    ]
    write_store(store, 'US-ZZ', parks)
    dcsv = tmp / 'doubtful.csv'
    dcsv.write_text('state,park,name,matcher_doubt_code,key_records_joined,matcher_records,matcher_review_state\n'
                    'ZZ,US-0009,Test,pin-far,i1,,KEEP-FLAGGED\nAA,US-0001,Other state,pin-far,a1,,KEEP-FLAGGED\n')
    out = tmp / 'out'
    logs = []
    rep = K.build(store, 'US-ZZ', out, doubtful=K.read_doubtful(dcsv, 'US-ZZ'), log=logs.append)
    idx = json.loads((out / 'US-ZZ' / 'INDEX.json').read_text())
    feats = {}
    for name, *_ in idx['parts']:
        for f in json.loads(gzip.decompress((out / 'US-ZZ' / name).read_bytes()))['features']: feats[f['properties']['ref']] = f
    fb = idx['fallback']
    rows = {r['ref']: r for r in rep['rows']}

    check('the check of what was written finds no problem', K.check(out, 'US-ZZ') == [])
    check('a one-tract park with an OPEN licence is drawn with every point (no simplifying under the cap)',
          'US-0001' in feats and rows['US-0001']['detail_m'] == 0 and rows['US-0001']['points'] == 201)
    check('identical geometry in two layers is drawn once; a near-identical tract (other vertices, within 3 m) is drawn once too',
          rows['US-0002']['distinct_records'] == 2 and rows['US-0002']['drawn_records'] == 1
          and sorted(feats['US-0002']['properties']['records']) == ['b1', 'b3'] and feats['US-0002']['properties']['drawn_once'] == 1)
    check('...and every tract is still listed with its layer (lay1, lay3)', feats['US-0002']['properties']['layers'] == ['lay1', 'lay3'])
    check('a park with ONE unlicensed tract is left out whole and keeps today\'s outline (never half a park)',
          'US-0003' not in feats and 'licence gate' in fb.get('US-0003', '') and 'c2' in fb.get('US-0003', ''))
    check('tracts 10 km or more apart = check join: today\'s outline, flagged', 'US-0004' not in feats and fb.get('US-0004', '').startswith('check join'))
    check('a park over the cap is simplified to the cap with the smallest ladder step, and the step is written on it',
          rows['US-0005']['store_points'] == 5406 and rows['US-0005']['points'] <= 3000 and rows['US-0005']['detail_m'] in K.LADDER
          and feats['US-0005']['properties']['detail_m'] == rows['US-0005']['detail_m'])
    check('the error at the cap is measured and never more than the tolerance plus rounding (0.6 m at 5 decimals)',
          0 < rows['US-0005']['worst_m'] <= rows['US-0005']['detail_m'] + 0.7)
    prev = ([0.0] + [s for s in K.LADDER if s < rows['US-0005']['detail_m']])[-1]
    check('the step before the one used would have gone over the cap (simplified only as far as needed)',
          (prev == 0 and rows['US-0005']['store_points'] > 3000) or
          K.simplify_park(K.park_rings(parks[4]), 10 ** 9, ladder=[prev], min_tol=prev)[2] > 3000)
    check('a park under 5 m at the cap gets no fine level', 'US-0005' not in idx['fine'] or rows['US-0005']['worst_m'] > K.FINE_OVER_M)
    check('a park of many small tracts (650 rings) needs a coarse step to reach the cap: the cost is measured, and over 5 m',
          rows['US-0011']['points'] <= 3000 and rows['US-0011']['worst_m'] > K.FINE_OVER_M and rows['US-0011']['detail_m'] >= 5)
    check('...so a fine level is written for that park, finer than the cap, and marked on the coarse feature',
          'US-0011' in idx['fine'] and rows['US-0011']['fine_worst_m'] < rows['US-0011']['worst_m']
          and feats['US-0011']['properties']['fine'] is True and (out / 'US-ZZ' / idx['fine']['US-0011'][0]).is_file())
    check('WDPA never goes in, whatever its licence text says', 'US-0006' not in feats and 'WDPA' in fb.get('US-0006', ''))
    check('a hole stays a hole: one polygon with an outer ring and an inner ring',
          len(feats['US-0007']['geometry']['coordinates']) == 1 and len(feats['US-0007']['geometry']['coordinates'][0]) == 2)
    check('a RESTRICTED licence class is refused', 'US-0008' not in feats and 'RESTRICTED' in fb.get('US-0008', ''))
    check('a park in the doubtful-joins list keeps today\'s outline (the other state\'s row is ignored)',
          'US-0009' not in feats and fb.get('US-0009', '').startswith('doubtful join') and 'US-0001' in feats)
    check('NON-COMMERCIAL counts as publishable and its credit line is kept per layer',
          'US-0010' in feats and idx['credits'].get('lay5') == 'County Parks' and feats['US-0010']['properties']['cr'] == ['lay5'])
    check('every park of the store is either drawn or in the fallback list, never both',
          set(feats) | set(fb) == {p['ref'] for p in parks} and not (set(feats) & set(fb)))

    # parts: force a small part size so the area splits; every file under the limit, whole parks per part
    out2 = tmp / 'out2'
    K.build(store, 'US-ZZ', out2, doubtful=K.read_doubtful(dcsv, 'US-ZZ'), max_part=20000, log=logs.append)
    idx2 = json.loads((out2 / 'US-ZZ' / 'INDEX.json').read_text())
    sizes = [(out2 / 'US-ZZ' / n).stat().st_size for n, *_ in idx2['parts']]
    check(f'a small part size splits the area into whole-park parts, each under the limit ({len(sizes)} parts)',
          len(sizes) >= 2 and all(s <= 20000 for s in sizes) and K.check(out2, 'US-ZZ') == [])
    # byte-identical rebuild
    out3 = tmp / 'out3'
    K.build(store, 'US-ZZ', out3, doubtful=K.read_doubtful(dcsv, 'US-ZZ'), log=logs.append)
    same = all((out / 'US-ZZ' / n).read_bytes() == (out3 / 'US-ZZ' / n).read_bytes() for n, *_ in idx['parts'])
    check('the same store gives byte-identical display files', same)
    # the store is only read
    before = {p.name: p.read_bytes() for p in store.iterdir()}
    K.build(store, 'US-ZZ', tmp / 'out4', log=logs.append)
    check('the store files are never changed', before == {p.name: p.read_bytes() for p in store.iterdir()})
    # a store whose index has no licence (an early pilot store): nothing is public
    st5 = tmp / 'store5'
    write_store(st5, 'US-ZZ', parks[:2], index_licence=False)
    for pk in parks[:2]:
        for r in pk['records']: pass
    raw = json.loads((st5 / 'index.json').read_text())
    check('a store index with no licence map uses the record\'s own licence', 'licence' not in raw['parks']['US-0001'])
    p6 = [park('US-0001', [dict(record('a1', 'lay1', [circle(0.1, 0.1, 0.01, 50)]), licence='')])]
    st6 = tmp / 'store6'; write_store(st6, 'US-ZZ', p6, index_licence=False)
    r6 = K.build(st6, 'US-ZZ', tmp / 'out6', log=logs.append)
    check('no licence recorded anywhere = not public (0 parks drawn, kept on today\'s outline)', r6['parks_drawn'] == 0 and r6['fallback'] == 1)
    # private preview: gate skipped but stamped; WDPA still out; refused in a public folder
    r7 = K.build(store, 'US-ZZ', tmp / 'prev', preview=True, log=logs.append)
    i7 = json.loads((tmp / 'prev' / 'US-ZZ' / 'INDEX.json').read_text())
    check('a private preview skips the licence gate but is stamped PRIVATE PREVIEW in the index and every part',
          i7.get('stamp') == K.PREVIEW_STAMP and 'US-0003' not in i7['fallback'] and r7['parks_drawn'] > rep['parks_drawn'] and K.check(tmp / 'prev', 'US-ZZ') == [])
    check('a private preview still never draws WDPA', 'US-0006' in i7['fallback'])
    check('check --public refuses a private preview; the gated copy passes it',
          any('PRIVATE PREVIEW' in x for x in K.check(tmp / 'prev', 'US-ZZ', public=True)) and K.check(out, 'US-ZZ', public=True) == [])
    (out / 'US-ZZ' / 'stray.json').write_text('{}')
    check('check --public refuses a file the INDEX does not list', any('not listed' in x for x in K.check(out, 'US-ZZ', public=True)))
    (out / 'US-ZZ' / 'stray.json').unlink()
    try:
        K.build(store, 'US-ZZ', tmp / 'site' / 'data' / 'display', preview=True, log=logs.append); refused = False
    except K.DisplayError: refused = True
    check('a private preview is refused in a folder named like the public one (data/display)', refused)
    # a moved coordinate in the store is caught by the checksum
    st8 = tmp / 'store8'; shutil.copytree(store, st8)
    b = bytearray((st8 / 'US-ZZ.kpcstore.json.gz').read_bytes())
    e = json.loads((st8 / 'index.json').read_text())['parks']['US-0001']
    m = json.loads(gzip.decompress(bytes(b[e['o']:e['o'] + e['n']])).decode().lstrip(',\n'))
    m['records'][0]['rings'][0][3] += 1
    nm = gzip.compress(json.dumps(m, separators=(',', ':')).encode(), 9, mtime=0)
    ix = json.loads((st8 / 'index.json').read_text())
    shift = len(nm) - e['n']
    for ref, v in ix['parks'].items():
        if v['o'] > e['o']: v['o'] += shift
    ix['parks']['US-0001']['n'] = len(nm); ix['files'] = {}
    (st8 / 'index.json').write_text(json.dumps(ix))
    (st8 / 'US-ZZ.kpcstore.json.gz').write_bytes(bytes(b[:e['o']]) + nm + bytes(b[e['o'] + e['n']:]))
    try:
        K.build(st8, 'US-ZZ', tmp / 'out8', log=logs.append); caught = False
    except K.DisplayError as ex: caught = 'checksum' in str(ex)
    check('a moved coordinate in the store stops the build (checksum), nothing half-written is used', caught)
    # Douglas-Peucker: segment distance, never over the tolerance, rings keep at least 4 points
    xs = [i * 10.0 for i in range(50)] + [0.0]; ys = [math.sin(i / 3) * 40 for i in range(50)] + [0.0]
    worst_ok, min_ok = True, True
    for t in (1, 5, 20, 100, 1000, 5000):
        k = K.dp_keep(xs, ys, t)
        worst_ok &= K.ring_error(xs, ys, k) <= t + 1e-9
        min_ok &= len(k) >= 4
    check('Douglas-Peucker never leaves a point farther than the tolerance, and a ring keeps at least 4 points', worst_ok and min_ok)
    check('the local projection is metres on the ellipsoid (1 degree of latitude at 45 N = 111.13 km, of longitude 78.85 km)',
          abs(K.local_scale(45)[1] - 111132) < 15 and abs(K.local_scale(45)[0] - 78847) < 15)

    # ---- the browser loader (node, if this machine has it) -----------------------------------------------------------------
    node = shutil.which('node')
    if not node:
        print('SKIP browser loader checks: node is not installed here')
    else:
        site = tmp / 'site2'; (site / 'data' / 'display').mkdir(parents=True)
        shutil.copytree(out / 'US-ZZ', site / 'data' / 'display' / 'US-ZZ')
        shutil.copytree(tmp / 'prev' / 'US-ZZ', site / 'data' / 'display' / 'US-ZY')   # a preview under another name
        js = (ROOT / 'kpc-outline-display.js').resolve()
        old = {'features': [{'type': 'Feature', 'properties': {'ref': r, 'g': 'official', 'old': True}, 'geometry': None}
                            for r in ('US-0001', 'US-0003', 'US-0099')] + [{'type': 'Feature', 'properties': {'ref': 'US-0098', 'g': 'pin'}, 'geometry': None}]}
        script = r'''
const fs=require('fs'),path=require('path'),zlib=require('zlib');const SITE=process.argv[2],JS=process.argv[3],OLD=JSON.parse(process.argv[4]);
function setup(search,store){const ls={};global.localStorage={getItem:k=>k in ls?ls[k]:null,setItem:(k,v)=>{ls[k]=String(v)},removeItem:k=>{delete ls[k]}};if(store)ls.kpcOutlineStore='1';
 global.location={search};global.window=global;delete global.kpcDisplayOutlines;global.fetched=[];
 global.fetch=(u,o)=>{global.fetched.push(u);const p=path.join(SITE,u.replace(/\?.*$/,''));if(!fs.existsSync(p))return Promise.resolve({ok:false,status:404});const b=fs.readFileSync(p);
  return Promise.resolve({ok:true,status:200,arrayBuffer:()=>Promise.resolve(b.buffer.slice(b.byteOffset,b.byteOffset+b.length))});};
 global.DecompressionStream=undefined;global.Response=class{constructor(s){this.s=s}text(){return this.s.then(b=>b.toString())}};
 delete require.cache[require.resolve(JS)];return require(JS);}
/* node has no DecompressionStream in this shim: unpack gzip with zlib through the same code path */
const realSetup=setup;setup=function(s,st){const api=realSetup(s,st);global.DecompressionStream=function(){};global.Blob=function(parts){this.b=Buffer.from(parts[0])};
 global.Blob.prototype.stream=function(){const b=this.b;return{pipeThrough:()=>zlib.gunzipSync(b)}};global.Response=function(x){this.x=x};global.Response.prototype.text=function(){return Promise.resolve(this.x.toString())};return api;};
(async()=>{const r={};
 let A=setup('',false);r.offNull=(await A.load('US-ZZ',OLD))===null;r.offFetched=global.fetched.length;
 A=setup('?outlines=store',false);let pk=await A.load('US-ZZ',OLD);r.on=pk&&pk.source;r.refs=pk?pk.features.map(f=>f.properties.ref):[];
 r.oldKept=pk?pk.features.filter(f=>f.properties.old).map(f=>f.properties.ref):[];r.remember=global.localStorage.getItem('kpcOutlineStore');
 r.versioned=global.fetched.filter(u=>/geojson\.gz\?v=[0-9a-f]{12}$/.test(u)).length;r.credit=pk?A.creditLine(pk,pk.by['US-0010']):'';
 r.fine=pk&&pk.by['US-0005']&&pk.by['US-0005'].properties.fine?!!(await A.fine('US-ZZ','US-0005')):'nofine';
 r.needFineFar=pk&&pk.by['US-0005']?A.needFine(pk.by['US-0005'],2,0.5):null;r.needFineNear=pk&&pk.by['US-0005']?A.needFine(pk.by['US-0005'],18,0.5):null;
 A=setup('?outlines=old',true);r.oldParam=(await A.load('US-ZZ',OLD))===null;r.forgot=global.localStorage.getItem('kpcOutlineStore');
 A=setup('',true);r.preview=(await A.load('US-ZY',OLD))===null;
 A=setup('',true);r.missing=(await A.load('US-QQ',OLD))===null;
 const p2=path.join(SITE,'data/display/US-ZZ/US-ZZ.geojson.gz'),keep=fs.readFileSync(p2);fs.writeFileSync(p2,zlib.gzipSync(Buffer.from('{"kpc":{"format":"kpc-display-1","area":"US-ZZ","part":[1,2]},"features":[]}')));
 A=setup('',true);r.badPart=(await A.load('US-ZZ',OLD))===null;fs.writeFileSync(p2,keep);
 r.badArea=setup('?outlines=store',false).wanted('../x')===false;
 console.log(JSON.stringify(r));})().catch(e=>{console.log(JSON.stringify({error:String(e&&e.stack||e)}));});
'''
        sp = tmp / 'loader_test.js'; sp.write_text(script)
        env = {k: v for k, v in os.environ.items() if 'proxy' not in k.lower()}
        res = subprocess.run([node, str(sp), str(site), str(js), json.dumps(old)], capture_output=True, text=True, timeout=60, env=env)
        try: r = json.loads(res.stdout.strip().splitlines()[-1])
        except Exception: r = {'error': res.stdout + res.stderr}
        if r.get('error'): print('   ', r['error'][:600])
        check('loader: switch off (no ?outlines, no toggle, empty go-live list) = null and NOTHING is fetched',
              r.get('offNull') is True and r.get('offFetched') == 0)
        check('loader: ?outlines=store draws the display copy and is remembered in this browser',
              r.get('on') == 'store' and r.get('remember') == '1')
        check("loader: today's outline is kept for every park the display copy leaves out (fallback, new parks); pin rows stay out",
              sorted(r.get('oldKept') or []) == ['US-0003', 'US-0099'] and 'US-0098' not in (r.get('refs') or [])
              and 'US-0001' in (r.get('refs') or []) and len(r.get('refs') or []) == len(feats) + 2)
        check('loader: every part is asked for with its own ?v=<sha12> (cache-friendly)', (r.get('versioned') or 0) >= 1)
        check('loader: the popup credit line names the agency from the index and says to check the official map',
              'County Parks' in (r.get('credit') or '') and 'official map' in (r.get('credit') or ''))
        check('loader: the fine level loads for a capped park, and only when zoomed in past its detail',
              r.get('fine') in (True, 'nofine') and (r.get('fine') == 'nofine' or (r.get('needFineFar') is False and r.get('needFineNear') is True)))
        check('loader: ?outlines=old switches it off again and forgets the toggle', r.get('oldParam') is True and r.get('forgot') is None)
        check('loader: a PRIVATE PREVIEW copy is never drawn', r.get('preview') is True)
        check('loader: no display copy for an area = null (today\'s outline)', r.get('missing') is True)
        check('loader: a part of another build = null for the whole area (never half an area)', r.get('badPart') is True)
        check('loader: an area name that is not an area is refused', r.get('badArea') is True)
        src = js.read_text(encoding='utf-8')
        check('loader: the go-live list ships empty (LIVE_AREAS = [])', 'var LIVE_AREAS = [];' in src)
        pages = [p.name for p in ROOT.glob('*.html') if 'kpc-outline-display.js' in p.read_text(encoding='utf-8', errors='replace')]
        check('loader: no page includes kpc-outline-display.js yet (nothing changes for the public)', pages == [])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
sys.exit(1 if FAILS else 0)
