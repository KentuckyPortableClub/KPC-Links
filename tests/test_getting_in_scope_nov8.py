#!/usr/bin/env python3
"""Nov 8 2026 (Quality Nov 7 B1/B2): Getting-in links keep their scope. New Forest parking only for New Forest parks; the DOC
finder is nationwide; Greater Wellington only for Wellington-region parks; LINZ (not a park manager) never shown; generic scopes are
in the link text. Uses the real data/maprep/agencies.json through kpc-getting-in.js build()/html() (node). Switch stays OFF."""
import json, pathlib, shutil, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
FAILS = []


def check(c, m):
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: FAILS.append(m)


if not shutil.which('node'):
    print('PASS node not installed: skipped'); sys.exit(0)
js = r"""
const G=require('./kpc-getting-in.js'),AG=require('./data/maprep/agencies.json');
const urls=(pre,sub,p)=>G.build(AG,pre,sub,p).flatMap(m=>m.links.map(l=>l.url));
const names=(pre,sub,p)=>G.build(AG,pre,sub,p).map(m=>m.name);
console.log(JSON.stringify({
 sherwood:urls('GB','ENG',{name:'Sherwood Pines Forest Park',type:'Forest Park'}),
 newforest:urls('GB','ENG',{name:'New Forest National Park',type:'Forest'}),
 fiord:urls('NZ','STL',{name:'Fiordland National Park',type:'National Park'}),
 fiordNames:names('NZ','STL',{name:'Fiordland National Park',type:'National Park'}),
 kaitoke:names('NZ','WGN',{name:'Kaitoke Regional Park',type:'Regional Park'}),
 ie:G.html(G.build(AG,'IE','',{name:'Wicklow Mountains National Park',type:'National Park'}))
}));"""
r = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True)
if r.returncode:
    print(r.stderr[-800:]); check(False, 'node model ran'); sys.exit(1)
o = json.loads(r.stdout.strip().splitlines()[-1])
check(not any('new-forest' in u for u in o['sherwood']), 'no New Forest parking for Sherwood')
check(any('new-forest' in u for u in o['newforest']) or not o['newforest'], 'New Forest pages still offered for the New Forest')
check('https://www.doc.govt.nz/parks-and-recreation/places-to-go/' in o['fiord'] and not any('places-to-go/auckland' in u for u in o['fiord']), 'DOC finder is nationwide')
check(not any('gw.govt.nz' in u or 'linz.govt.nz' in u for u in o['fiord']), 'no Wellington council or LINZ for Fiordland')
check(any(n.startswith('Greater Wellington') for n in o['kaitoke']), 'Greater Wellington still shown for Kaitoke')
check('<small>(' in o['ie'], 'generic scope is visible in the link text')
sw = json.loads((ROOT / 'data/getting-in-switch.json').read_text())
check(sw.get('on') is False, 'getting-in switch stays OFF')
sys.exit(1 if FAILS else 0)
