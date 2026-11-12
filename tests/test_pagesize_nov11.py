"""Nov 11 (page-size PR, static checks; offline, no network). The big map files are read on first need, once, from one address;
WHICH files the planners and Park Commander read is unchanged. Browser checks: tests/pagesize_nov11_browser.py (hand-run).
Prints PASS / FAIL lines."""
import os, re, sys, glob, hashlib
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
R = lambda p: open(os.path.join(ROOT, p), encoding='utf8').read()
fails = 0
def ok(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails += 1
STAMP = '20261111zr'   # Nov 11 (job 3 loaders, on top of page size): the released copies
CHANGED = ['kpc-us-planner.js', 'kpc-padus-layer.js', 'gis-overlays.js', 'kpc-planner.js', 'kpc-bounds.js', 'kpc-park-control.js', 'kpc-gps-wire.js', 'kpc-offline.js']
pages = glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, '.claude/build/**/*.html'), recursive=True)
bad = []
for f in pages:
    t = open(f, encoding='utf8').read()
    for s in CHANGED:
        for v in re.findall(r'(?<![A-Za-z0-9_-])' + re.escape(s) + r'\?v=([A-Za-z0-9_.-]+)', t):
            if v != STAMP: bad.append((os.path.relpath(f, ROOT), s, v))
ok(not bad, f'every page (and .claude/build page source) loads the changed scripts at ?v={STAMP}: ' + str(bad[:6]))
gw = R('kpc-gps-wire.js'); ok("kpc-bounds.js?v=" + STAMP in gw, 'kpc-gps-wire.js loads kpc-bounds.js at the same new stamp')
# one address for the Kentucky boundary files on every page
addr = {
 'kpc-planner.js': re.findall(r"kpcRel\(B\[k\]\.file,p=>\{const u=p\+'\?v=([^']+)'", R('kpc-planner.js')),
 'kpc-padus-layer.js': re.findall(r"const old = p => \{ const u = p \+ '\?v=([^']+)'", R('kpc-padus-layer.js')),
 'gis-overlays.js': re.findall(r"getBoundary1[\s\S]{0,200}?kpcRel\(s\.file,p=>fetch\(p\+'\?v=([^']+)'", R('gis-overlays.js')),
 'kpc-bounds.js': re.findall(r"relFile\(L\.file, p => fetch\(p \+ '\?v=([^']+)'", R('kpc-bounds.js')),
 'kpc-park-control.js': re.findall(r"kpcRel\('ky-usace\.geojson', p => fetch\(p \+ '\?v=([^']+)'", R('kpc-park-control.js'))}   # Nov 11 (job 3): public pages read the released copy (one ?v= hash on every page); this is the Map Rep working address
ok(all(v == ['20261110us'] for v in addr.values()), 'the Kentucky boundary files have ONE address (?v=20261110us) in the KY planner, US planner, Park Commander, kpc-bounds and the Park Map: ' + str(addr))
# US planner: the park list only through ready(); same three files, same order
us = R('kpc-us-planner.js')
ok(len(re.findall(r'(?<![A-Za-z.])loadAll\(\)', us)) == 2 and 'DATA=loadAll().then(' in us, 'US planner: loadAll() is defined once and called only from ready() (one shared promise)')
ok("Promise.all([dfetch('locations.json').then(r=>r.json()),fetch('kpc-us-states.json').then(r=>r.json()).catch(()=>[]),J('data/canada.json?v='+new Date().toISOString().slice(0,10)),J('data/northam.json')])" in us, 'US planner: the SAME four files, in the same order, are read (locations.json, kpc-us-states.json, data/canada.json, data/northam.json)')
ok("getJson('data/canada.json?v=' + day())" in R('kpc-padus-layer.js') and "const day = () => new Date().toISOString().slice(0, 10);" in R('kpc-padus-layer.js'), 'US planner: data/canada.json has the same address in the park list and the official-outline layer (one download, not two)')
for fn in ['async function search(q){q=q.trim();if(!q)return;if(!LOADED)await ready();', 'async function go(la,lo,label,sw){if(!LOADED)await ready();', 'async function runRoute(){if(!LOADED)await ready();', "if(!LOADED){await ready();if(q!==seq)return}"]:
    ok(fn in us, 'US planner: waits for the park list before using it: ' + fn[:48])
ok("if(!LOADED){$('t-offmsg').textContent='Loading the park list first…';await ready()}" in us, 'US planner: SAVE FOR NO SIGNAL reads the park list first, so the saved copy still has it')
ok("if(qs.get('t')||qs.get('q')||(last&&isFinite(last.la)))ready();" in us, 'US planner: a shared trip, a ?q= search or the last search still read the list at once')
ok("kyStart:FIRST" in us, 'US planner: Kentucky outlines wait for the first view (kyStart)')
# padus: Kentucky files only when the layer is on and the map shows Kentucky
pad = R('kpc-padus-layer.js')
ok("const check = () => { if (began || !go || !map.hasLayer(host) || !showsKY()) return; began = true; loadAll(); };" in pad and "map.on('moveend zoomend', check);" in pad, 'kpc-padus-layer.js: the 13 Kentucky files start once, when the layer is on and the map shows Kentucky')
ok(pad.count("const KY_OFFICIAL = {") == 1 and len(re.findall(r"file:'ky-[a-z-]+\.geojson'", pad.split('const KY_OFFICIAL = {')[1].split('};')[0])) == 13, 'kpc-padus-layer.js: the same 13 Kentucky files as before')
# Park Commander
gis = R('gis-overlays.js')
ok("return bWait[k]||(bWait[k]=getBoundary1(k).finally(()=>{delete bWait[k]}))" in gis, 'gis-overlays.js: one shared request per boundary layer (toggle + Am I inside + pre-ticked never download twice)')
ok("setTimeout(()=>{Object.keys(bounds).forEach(k=>{if($('gis-'+k)?.checked)toggleBoundary(k)})" not in gis and "requestIdleCallback(()=>draw(),{timeout:2000})" in gis, 'gis-overlays.js: pre-ticked layers start after the page has loaded and gone idle (still ticked by default)')
fh = R('finder.html')
ok(all(re.search(r'id="gis-' + k + r'" type="checkbox" checked', fh) for k in ['bstate', 'bwma', 'bdbnf', 'busace']), 'finder.html: the boundary layers are still ticked by default (members see the same map)')
# KY planner
kp = R('kpc-planner.js')
ok(" boundsSoon();\n" in kp and "loadBoundaries();\n /* new checker" not in kp and "const boundsNow=()=>bLoad||(bLoad=loadBoundaries());" in kp, 'kpc-planner.js: boundaries start after idle, once (shared promise)')
ok("if(!bReady){$('offmsg').textContent='Loading the boundaries first…';await boundsNow()}" in kp, 'kpc-planner.js: SAVE FOR NO SIGNAL waits for the boundary files so the saved copy has them')
ok("function addSpot(ll){if(!canAdd())return;boundsNow();" in kp and "function addMode(v){adding=v;if(v)boundsNow();" in kp, 'kpc-planner.js: adding a spot starts the boundary files at once')
# offline save lists still cover the files
off = R('kpc-offline.js')
# Nov 11 (job 3 loaders): the Kentucky files are saved as their released copies (KY_REL through KPCREL.need), the rest from FILES
_lists = off.split('const FILES = [')[1].split('];')[0] + off.split('const KY_REL = [')[1].split('];')[0]
ok(all("'" + f + "'" in _lists for f in ['ky-state-parks.geojson', 'ky-hunting-areas.geojson', 'ky-nature-preserves.geojson', 'ky-natural-areas.geojson', 'ky-dbnf.geojson', 'ky-dbnf-owned.geojson', 'ky-nps.geojson', 'ky-wild-rivers.geojson', 'ky-wilderness.geojson', 'ky-fws.geojson', 'ky-usace.geojson', 'ky-padus-parks.geojson', 'ky-kpc-drawn.geojson', 'locations.json', 'locations-ky.json', 'ky-overlaps.geojson']), 'kpc-offline.js (Park Commander SAVE FOR OFFLINE) names every boundary layer that is on by default (incl. ky-usace, ky-fws, ky-padus-parks, ky-kpc-drawn, missing before) and locations.json')
sw = R('kpc-finder-sw.js'); ok("kpc-finder-v1" in sw and "kpc-tiles-v1" in sw, 'cache names kpc-finder-v1 / kpc-tiles-v1 unchanged')
# KPCREL: four identical copies
blk = []
for f in ['kpc-bounds.js', 'kpc-gps.js', 'kpc-padus-layer.js', 'kpc-us-planner.js']:
    m = re.search(r'/\* >>> kpc_released.*?/\* <<< kpc_released \*/', R(f), re.S); blk.append(hashlib.sha1(m.group(0).encode()).hexdigest() if m else None)
ok(None not in blk and len(set(blk)) == 1, 'the KPCREL block is the same in all four files')
# images
ok(all('parks-mobile.jpg' in R(f) and 'parks-mobile.png' not in R(f) for f in ['kpc-guide-beginners.html', 'kpc-guide-safety.html']) and os.path.isfile(os.path.join(ROOT, 'parks-mobile.jpg')), 'the two guide pages whose phone header really shows parks-mobile use parks-mobile.jpg (the same picture, 146 KB smaller, already used by parks.html and kpc-guide.css)')
ab = R('about.html'); ev = R('events.html')
ok(all(re.search(r'src="' + s + r'" loading="lazy" decoding="async"', ab) for s in ['KPC_Founders_Group.jpg', 'KPC_Brandon_KZ4CP_Cropped.jpg', 'KPC_Aaron_KQ4HZK.jpg', 'KPC_Zach_K4ZSR.jpg', 'KPC_Brent_N4BDW.jpg']), 'about.html: the founders photos far down the page load when scrolled to')
ok('<img src="KPC26-Group-Photo.jpg" alt="KPC 2026 group photo" width="1920" height="1080" loading="lazy"' in ev, 'events.html: the group photo far down the page loads when scrolled to, with its size so nothing jumps')
# no new data files, no .gz copies
ok(not glob.glob(os.path.join(ROOT, '*.geojson.gz')) and not glob.glob(os.path.join(ROOT, 'locations*.json.gz')), 'no .gz copies of the root data files')
print('ALL PASSED' if not fails else f'SOME FAILED ({fails})')
sys.exit(1 if fails else 0)
