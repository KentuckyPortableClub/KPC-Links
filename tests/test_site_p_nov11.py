#!/usr/bin/env python3
"""Nov 11 2026 (KPC owner): Park Commander, the two Trip Planners and the map pages (site review, package P).
- Am I in the Park? answers for the spot you are at now, says "Could not find" for an unknown reference, drops a slow answer for
  a reference already replaced and calls an approximate outline approximate (node: tests/in_park_nov11.js).
- US Trip Planner share links: a broken %-code no longer stops the page; a made-up reference in a live: stop is dropped.
- Kentucky Trip Planner share links: the start must be two numbers and a name.
- Park Commander links from the data files open only as web pages or site pages (never javascript: / data:).
- Map tooltips built from data are escaped; drive times never read "2 h 60 min"; a newer search / outline tap wins.
No network: node runs the real functions taken from the page files, on fake inputs."""
import json, pathlib, re, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
fails = 0
def check(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails += 1
rd = lambda f: (ROOT / f).read_text(encoding='utf-8')
node = shutil.which('node')

def run_node(src):
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d, 't.js'); p.write_text(src, encoding='utf-8')
        r = subprocess.run([node, str(p)], capture_output=True, text=True, timeout=60)
        return r.stdout.strip(), r.stderr.strip()[-800:], r.returncode

def fn(src, name, end):
    i = src.index('function ' + name + '(')
    j = src.index(end, i)
    return src[i:j]

US, KY, FJ = rd('kpc-us-planner.js'), rd('kpc-planner.js'), rd('finder.js')
PC, TR, VA, IP = rd('kpc-park-control.js'), rd('kpc-trails-layer.js'), rd('kpc-va-birding-layer.js'), rd('kpc-in-park.js')

if not node:
    print('SKIP node is not installed here: only the static checks run')
else:
    out, err, rc = run_node(rd('tests/in_park_nov11.js').replace("path.resolve(__dirname, '..')", json.dumps(str(ROOT))))
    print(out)
    if err: print(err)
    check(rc == 0 and out.endswith('ALL PASS'), 'Am I in the Park? node checks (tests/in_park_nov11.js)')

    # US planner: loadShared on fake data
    ls = fn(US, 'loadShared', '\n\n/* ---------- wire up')
    js = """
const BYREF={'US-1271':{p:'POTA',c:'US-1271',n:'Taylorsville',la:38,lo:-85,url:''}},ALL=[];let trip=[];const saveTrip=()=>{};
let search='';const location={get search(){return search}};
""" + ls + """
const R={};
search='?t='+encodeURIComponent('pin:37.5,-85.1,%E0%A4%A~US-1271');let ok=true;try{loadShared()}catch(e){ok=false}
R.badEscape=[ok,trip.length,trip[0]&&trip[0].n];
trip=[];search='?t='+encodeURIComponent('live:US-1" onmouseover="X,37.5,-85.1,Test');loadShared();R.badRef=trip.length;
trip=[];search='?t='+encodeURIComponent('live:US-99999,37.5,-85.1,New%20Park~pin:37,-85,Camp');loadShared();R.good=trip.map(s=>s.c.startsWith('PIN-')?'PIN:'+s.n:s.c+':'+s.n);
console.log(JSON.stringify(R));
"""
    out, err, rc = run_node(js)
    try:
        R = json.loads(out.splitlines()[-1])
    except Exception:
        R = {}; print(out, err)
    check(R.get('badEscape', [0])[0] is True and R['badEscape'][1] == 2, 'US share link with a broken %-code still loads its stops (no URIError): ' + str(R.get('badEscape')))
    check(R.get('badRef') == 0, 'US share link: a live: stop whose reference is not a reference is dropped')
    check(R.get('good') == ['US-99999:New Park', 'PIN:Camp'], 'US share link: normal live: and pin: stops still load: ' + str(R.get('good')))

    # KY planner: readShared origin
    rs = fn(KY, 'readShared', '\nfunction gpx(')
    js = """
const MAXSTOPS=10,uid=()=>'x',ALL=[{ref:'US-1271',k:'pota',n:'T',dest:[38,-85],dn:''}],items=()=>ALL;
const enc=o=>btoa(unescape(encodeURIComponent(JSON.stringify(o))));
""" + rs + """
const a=readShared(enc({o:[37.5,-84.3,'Berea'],s:[['p','US-1271']]})),b=readShared(enc({o:['x" onmouseover="y',1,'n'],s:[]})),c=readShared(enc({o:[37.5,-84.3,{}],s:[]}));
console.log(JSON.stringify({a:a.o,an:a.s.length,b:b.o,c:c.o}));
"""
    out, err, rc = run_node(js)
    try:
        R = json.loads(out.splitlines()[-1])
    except Exception:
        R = {}; print(out, err)
    check(R.get('a') == [37.5, -84.3, 'Berea'] and R.get('an') == 1, 'KY share link: a normal start and stop still load')
    check(R.get('b') is None, 'KY share link: a start that is not two numbers is ignored')
    check(isinstance(R.get('c'), list) and isinstance(R['c'][2], str), 'KY share link: the start name is plain text')

    # Park Commander link(): web pages and site pages only
    lk = re.search(r'function node\(tag,cls,txt\)\{.*?\}\nfunction link\(label,url\)\{.*?\n', FJ, re.S).group(0)
    js = """
const document={createElement:t=>({tag:t,href:'',set textContent(v){this.t=v}})};
""" + lk + """
console.log(JSON.stringify(['javascript:alert(1)',' JaVaScRiPt:x','data:text/html,x','https://parks.ky.gov/x','kpc-park-sheet.html?ref=US-1','kpc-weather.html?a=1&name=A%3AB','http://x.gov'].map(u=>link('l',u).href)));
"""
    out, err, rc = run_node(js)
    try:
        R = json.loads(out.splitlines()[-1])
    except Exception:
        R = []; print(out, err)
    check(R[:3] == ['', '', ''], 'Park Commander: javascript: / data: addresses from a data file get no link')
    check(R[3:] == ['https://parks.ky.gov/x', 'kpc-park-sheet.html?ref=US-1', 'kpc-weather.html?a=1&name=A%3AB', 'http://x.gov'], 'Park Commander: web and site links unchanged')

# static checks (the one-line fixes)
check('esc(ref)' not in IP, 'kpc-in-park.js: no reference to an undefined "ref" in the not-found message')
for f, s in (('kpc-planner.js', KY), ('kpc-us-planner.js', US)):
    check(not re.search(r'hrs%1\*60|duration%3600/60', s), f + ': drive time is rounded once (never "2 h 60 min")')
check('m.bindTooltip(`${esc(x.c)} · ${esc(x.n)}`)' in PC and 'p.bindTooltip(`🥾 ${esc(t.ref)} · ${esc(nm)}`' in PC, 'kpc-park-control.js: park and trail tooltips are escaped')
check('line.bindTooltip(esc(t.name)' in TR, 'kpc-trails-layer.js: trail tooltip is escaped')
check('m.bindTooltip(esc(p[3])' in VA, 'kpc-va-birding-layer.js: site tooltip is escaped')
check(all(('${park && webU(park.' + k + ')') in PC for k in ('web', 'off', 'camp')), 'kpc-park-control.js: park links open only as web pages')
check(re.search(r'href="\$\{u\}"', KY) is None and 'href="${esc(u)}"' in KY, 'kpc-planner.js: result-list links from the data file are escaped')
check('if(my!==goSeq)return;' in US and US.count('if(stale())return;') == 3, 'kpc-us-planner.js: a newer search / outline tap wins (no stale results, no orphan outline)')
check("esc(j.points||s.pts||0)" in US and 'href="${esc(l.page)}"' in US, 'kpc-us-planner.js: SOTA API numbers and program page link are escaped')
for f, s in (('finder.js', FJ), ('kpc-us-planner.js', US), ('kpc-park-control.js', PC)):
    check(not re.search(r'decodeURIComponent\(\(?location\.hash', s), f + ': the address #part is decoded inside try/catch (a broken %-code does not stop the page)')
if node:
    fh = re.search(r"const fHash=\(\)=>\{.*?\};", FJ).group(0)
    out, err, rc = run_node("const location={hash:'#%E0%A4%A'};" + fh + "const a=fHash();location.hash='#finder-planner';console.log(JSON.stringify([a,fHash()]))")
    check(out.splitlines()[-1:] == ['["%E0%A4%A","finder-planner"]'], 'Park Commander: a broken #%-code is kept as text, a normal one still works: ' + out[-60:])
# the shared release loader block is untouched (package M owns it)
blk = lambda s: re.search(r'/\* >>> kpc_released[\s\S]*?/\* <<< kpc_released \*/', s).group(0)
check(blk(US) == blk(rd('kpc-gps.js')), 'kpc-us-planner.js: the KPCREL block still equals kpc-gps.js')
print('ALL PASS' if not fails else 'SOME FAILED'); sys.exit(1 if fails else 0)
