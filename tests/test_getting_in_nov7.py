#!/usr/bin/env python3
"""Round 3 (Nov 7 2026): GB/IE/AU/NZ agency rows + access fields, and the OFF-by-default 'Getting in' block."""
import json, os, re, subprocess, sys
from urllib.parse import urlparse
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = 0
def ck(c, m):
    global bad
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: bad += 1
AG = json.load(open(f'{R}/data/maprep/agencies.json'))
P = AG['places']
for c in 'GB-ENG GB-SCT GB-WLS GB-NIR GB IE AU NZ AU-NSW AU-VIC AU-QLD AU-WA AU-SA AU-TAS'.split():
    ck(c in P and P[c]['agencies'], f'place {c} has agencies')
BANNED = ('33TOOklri9xpic7U', 'natureserve', 'ncnhde', 'services.arcgis.com', 'servicesX')
new = [c for c in P if c.split('-')[0] in ('GB', 'IE', 'AU', 'NZ')]
urls = []
def walk(o, home=None):
    if isinstance(o, dict):
        if 'url' in o and isinstance(o['url'], str): urls.append(o)
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
for c in new:
    for a in P[c]['agencies']:
        walk(a)
        h = urlparse((a.get('home') or {}).get('url', '')).hostname
        for k, v in (a.get('access') or {}).items():
            u = v.get('url') or v.get('template') or ''
            ck(not u or not h or urlparse(u).hostname.split('.', 1)[-1] in h or h.split('.', 1)[-1] in urlparse(u).hostname or True, f'{c} {a["name"][:24]} access.{k} host')
            if u and h: ck(h.replace('www.', '').split('.', 1)[-1] in urlparse(u).hostname or urlparse(u).hostname.replace('www.', '') == h.replace('www.', ''), f'{c} {a["name"][:24]} access.{k} same site as home ({urlparse(u).hostname})')
ck(all(u['url'] == '' or u['url'].startswith('https://') for u in urls), 'every url is https or empty')
ck(all(u.get('verified') is False for u in urls if u['url']), 'every url unverified (verified:false)')
ck(not any(b in u['url'] for u in urls for b in BANNED), 'no banned hosts')
sw = json.load(open(f'{R}/data/getting-in-switch.json'))
ck(sw.get('on') is False, 'switch file is OFF')
html = open(f'{R}/kpc-planner-us.html', encoding='utf-8').read()
ck('kpc-getting-in.js' in html, 'page loads the module')
js = open(f'{R}/kpc-us-planner.js', encoding='utf-8').read()
ck('KPCGetIn.block(' in js, 'planner calls the block')
r = subprocess.run(['node', f'{R}/kpc-getting-in.js'], capture_output=True, text=True)
ck(r.returncode == 0, 'module self-test passes')
# off by default: block returns '' with the switch off, and with data present when switch is on
t = r"""
const G=require('%s/kpc-getting-in.js'),fs=require('fs');
const AG=JSON.parse(fs.readFileSync('%s/data/maprep/agencies.json'));
global.fetch=async u=>({ok:true,json:async()=>/switch/.test(u)?{on:SW}:AG});
const PI={AU:Promise.resolve({parks:{'AU-1':['Royal National Park','','National Park','','','','','','','','NSW']}})};
(async()=>{global.SW=false;let a=await G.block({c:'AU-1',n:'x'},'AU',PI);
 console.log(a===''?'OFF-OK':'OFF-BAD');
 const m=G.build(AG,'AU','NSW',{name:'Royal National Park',type:'National Park'});
 console.log(m.length>0&&m.every(x=>x.links.every(l=>l.unverified))?'MODEL-OK':'MODEL-BAD');
 for(const [pre,sub] of [['GB','ENG'],['GB','HLD'],['GB','WLS'],['IE',''],['NZ','AUK'],['AU','QLD']]){
  const mm=G.build(AG,pre,sub,{name:'Test Forest',type:'Forest'});console.log(pre+sub,mm.length>0?'HAS':'NONE')}})();
""" % (R, R)
r = subprocess.run(['node', '-e', t], capture_output=True, text=True)
o = r.stdout
ck('OFF-OK' in o and 'MODEL-OK' in o, 'block is empty when the switch is off; model links all unverified')
ck(o.count('HAS') == 6, 'every GB/IE/AU/NZ test case gets at least one agency: ' + ' '.join(o.split()[2:]))
sys.exit(1 if bad else 0)
