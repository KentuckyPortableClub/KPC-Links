"""Kentucky Trip Planner, Nov 10: official outlines whose names differ from the POTA name
draw solid when data/ky-answer-key.json already joins them, same as Park Commander after #119.
The lookup lives in kpc-answer-key.js and is shared. Static checks plus a Node run against
the repo's own outline files, kpc-ky-data.json, and the answer key (no network)."""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ok = True
def check(name, cond, detail=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + ((' — ' + detail) if detail and not cond else ''))
    ok = ok and bool(cond)

js = (ROOT / 'kpc-planner.js').read_text(encoding='utf-8')
ak = (ROOT / 'kpc-answer-key.js').read_text(encoding='utf-8')
html = (ROOT / 'kpc-planner.html').read_text(encoding='utf-8')
g = (ROOT / 'gis-overlays.js').read_text(encoding='utf-8')

check('planner and finder share kpc-answer-key.js',
      'kpc-answer-key.js' in html and 'kpc-answer-key.js' in (ROOT / 'finder.html').read_text(encoding='utf-8')
      and 'window.kpcAnswerKey' in g and 'kpcAnswerKey.keyJoin(f,fName)' in js)
check('answer key is loaded once, lazily, from the saved copy',
      'function loadKey' in ak and 'if (keyTried) return keyReadyP' in ak and "data/ky-answer-key.json?v=20261110aj" in ak)
check('planner lookup order is properties.ref, then the answer key, then name/alias fallback',
      js.index('const own=ownRef(f)') < js.index('kpcAnswerKey.keyJoin(f,fName)') < js.index('ALIAS[fName(f)]'))
check('lookup is by layer + outline name',
      "f._lk || (f._L && f._L.k)" in ak and 'f._lk=k' in js and 'keyJoin(f,fName)' in js)
check('"no POTA reference" is not remembered before the key has been tried',
      'if(f._pota&&(f._named||joinsReady()))return f._pota' in js and 'whenJoins()' in js)
check('drawn layers restyle after the key loads, and a cached no-join answer is cleared',
      'function restyleBounds()' in js and 'delete f._pota' in js and 'delete f._named' in js
      and 'kpcAnswerKey.loadKey(restyleBounds)' in js)
check('kpc-planner.js and kpc-answer-key.js cache stamps are bumped',
      'kpc-planner.js?v=20261111p' in html and 'kpc-answer-key.js?v=20261110key' in html)

# The two Green River SNA tracts (and Fort Heiman) are alias joins in the key
key = json.loads((ROOT / 'data/ky-answer-key.json').read_text(encoding='utf-8'))
gr = (key.get('parks') or {}).get('US-12752') or {}
check('US-12752 Green River SNA is an alias join on both Davis Bend and Rush Island Bottoms',
      any(t[0]=='bsna' and t[1]=='Green River State Natural Area (Davis Bend)' and t[3]=='alias' for t in gr.get('tracts') or [])
      and any(t[0]=='bsna' and t[1]=='Green River State Natural Area (Rush Island Bottoms)' and t[3]=='alias' for t in gr.get('tracts') or []))

node = r'''
const fs=require('fs');
global.window=global;
global.fetch=()=>Promise.resolve({ok:false});
eval(fs.readFileSync('kpc-answer-key.js','utf8'));
const AK=kpcAnswerKey;
const key=JSON.parse(fs.readFileSync('data/ky-answer-key.json','utf8'));
const D=JSON.parse(fs.readFileSync('kpc-ky-data.json','utf8'));
const planner=fs.readFileSync('kpc-planner.js','utf8');
const ALIAS=eval('('+planner.match(/const ALIAS = (\{[\s\S]*?\});/)[1]+')');
const fName=f=>(f.properties&&(f.properties.NAME||f.properties.Name||f.properties.name||f.properties.UNIT_NAME||f.properties.TRAIL_NAME))||'';
const norm=s=>String(s||'').toLowerCase().replace(/wildlife management area|state nature preserve|state natural area|state resort park|state historic site|state park|national forest|wma|snp|sna|the |[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();
const kOf=s=>{s=String(s||'').toLowerCase();const k=[];if(/wildlife management area|\bwma\b|hunting area/.test(s))k.push('wma');if(/nature preserve|natural area|\bsnp\b|\bsna\b/.test(s))k.push('snp');if(/state (resort )?park|recreation(al)? area/.test(s))k.push('sp');if(/state forest/.test(s))k.push('sf');if(/wild river|scenic river/.test(s))k.push('wr');return k};
const kSame=(a,b)=>{const x=kOf(a),y=kOf(b);return !x.length||!y.length||x.some(v=>y.includes(v))};
const ringsOf=g=>!g?[]:g.type==='Polygon'?[g.coordinates]:g.type==='MultiPolygon'?g.coordinates:[];
function inRing(x,y,r){let s=false;for(let i=0,j=r.length-1;i<r.length;j=i++){const xi=r[i][0],yi=r[i][1],xj=r[j][0],yj=r[j][1];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi+1e-15)+xi)s=!s}return s}
function inside(lat,lon,g){for(const p of ringsOf(g)){if(!p.length||!inRing(lon,lat,p[0]))continue;if(p.slice(1).some(h=>inRing(lon,lat,h)))continue;return true}return false}
function bbox(g){let a=[180,90,-180,-90];const add=([x,y])=>{if(x<a[0])a[0]=x;if(y<a[1])a[1]=y;if(x>a[2])a[2]=x;if(y>a[3])a[3]=y};for(const p of ringsOf(g))for(const r of p)r.forEach(add);return a}
const ownRef=f=>{const r=(f&&f.properties||{}).ref;return typeof r==='string'&&/^[A-Z0-9]{1,4}-\d{4,5}$/.test(r.trim())?r.trim():''};
function nmEq(a,b){a=norm(a);b=norm(b);if(!a||!b)return false;const s=a.length<b.length?a:b,l=a.length<b.length?b:a;return a===b||(s.length>6&&l.startsWith(s))}
function otherRefs(f){const o={kn:[]};const b=f._bb||(f._bb=bbox(f.geometry)),nm=fName(f),inB=(la,lo)=>lo>=b[0]&&lo<=b[2]&&la>=b[1]&&la<=b[3]&&inside(la,lo,f.geometry);
 for(const k of D.kff||[]){if(!k.p&&nmEq(k.n,nm))o.kn.push(k)}return o}
function named(f, useKey){
  const parks=D.parks||[],park=r=>parks.find(x=>x.c===r),out=new Map(),NM=new Set();
  const own=ownRef(f);if(own){out.set(own,park(own)||{c:own,n:fName(f)});NM.add(own)}
  if(useKey){for(const row of AK.keyJoin(f,fName)){const r=row.ref;if(!NM.has(r)){out.set(r,park(r)||{c:r,n:row.n||fName(f)});NM.add(r)}}}
  (ALIAS[fName(f)]||[]).forEach(r=>{const p=park(r);if(p){if(!out.has(r))out.set(r,p);NM.add(r)}});
  const nm=norm(fName(f)),b=f._bb||(f._bb=bbox(f.geometry));
  for(const p of parks){if(NM.has(p.c))continue;
    if(p.lo>=b[0]-.02&&p.lo<=b[2]+.02&&p.la>=b[1]-.02&&p.la<=b[3]+.02&&inside(p.la,p.lo,f.geometry)){if(!out.has(p.c))out.set(p.c,p);continue}
    const dn=norm(p.n);if(nm.length>4&&dn&&kSame(p.n,fName(f))&&p.lo>=b[0]-.5&&p.lo<=b[2]+.5&&p.la>=b[1]-.5&&p.la<=b[3]+.5){const sh=dn.length<nm.length?dn:nm,lg=dn.length<nm.length?nm:dn;if(dn===nm||(sh.length>6&&lg.startsWith(sh)&&sh.length/lg.length>=.7)){out.set(p.c,p);NM.add(p.c)}}}
  return NM.size>0||otherRefs(f).kn.length>0;
}
const layers={
  bstate:{file:'ky-state-parks.geojson'},bwma:{file:'ky-hunting-areas.geojson'},
  bsnp:{file:'ky-nature-preserves.geojson'},bsna:{file:'ky-natural-areas.geojson'},
  bdbnfo:{file:'ky-dbnf-owned.geojson',own:true},bdbnf:{file:'ky-dbnf.geojson',proc:true},
  bnps:{file:'ky-nps.geojson'},bwild:{file:'ky-wild-rivers.geojson'},
  bwilder:{file:'ky-wilderness.geojson'},bfws:{file:'ky-fws.geojson'},
  busace:{file:'ky-usace.geojson',corps:true},bpad:{file:'ky-padus-parks.geojson'},
  bkpc:{file:'ky-kpc-drawn.geojson',kpc:true}
};
function count(useKey){
  if(useKey) AK.useAnswerKey(key);
  const miss=[]; let total=0;
  for(const [lk,s] of Object.entries(layers)){
    if(s.proc||s.corps||s.kpc) continue; // those layers are not red-dashed "no POTA reference"
    const feats=JSON.parse(fs.readFileSync(s.file,'utf8')).features||[];
    for(const f of feats){
      if(!f.geometry||!ringsOf(f.geometry).length) continue;
      f._lk=lk; total++;
      if(!named(f, useKey)) miss.push(lk+':'+fName(f));
    }
  }
  return {total, dashed:miss.length, names:miss};
}
function feat(file,name,layer){
  const f=(JSON.parse(fs.readFileSync(file,'utf8')).features||[]).find(x=>(x.properties||{}).NAME===name);
  if(!f) throw new Error('missing '+name);
  f._lk=layer; return f;
}
const davis=feat('ky-natural-areas.geojson','Green River State Natural Area (Davis Bend)','bsna');
const rush=feat('ky-natural-areas.geojson','Green River State Natural Area (Rush Island Bottoms)','bsna');
const heiman=feat('ky-nps.geojson','Fort Heiman (Fort Donelson National Battlefield tract)','bnps');
const lsf=feat('ky-natural-areas.geojson','Little South Fork State Natural Area (Steele Hollow SNA)','bsna');
const barkley=feat('ky-hunting-areas.geojson','Lake Barkley WMA','bwma');
const before={davis:named(davis,false),rush:named(rush,false),heiman:named(heiman,false),lsf:named(lsf,false),barkley:named(barkley,false)};
const beforeC=count(false);
const afterC=count(true);
const after={davis:named(davis,true),rush:named(rush,true),heiman:named(heiman,true),lsf:named(lsf,true),barkley:named(barkley,true),
             davisKey:AK.keyJoin(davis).map(x=>x.ref+':'+x.how),
             rushKey:AK.keyJoin(rush).map(x=>x.ref+':'+x.how)};
const flipped=beforeC.names.filter(n=>!afterC.names.includes(n));
const keyHits=afterC.names.filter(n=>{const [lk,...rest]=n.split(':'); const f={properties:{NAME:rest.join(':')},_lk:lk}; return AK.keyJoin(f,f=>f.properties.NAME).length>0});
console.log(JSON.stringify({before,after,beforeC:{total:beforeC.total,dashed:beforeC.dashed,names:beforeC.names},afterC:{total:afterC.total,dashed:afterC.dashed,names:afterC.names},flipped,keyHits}));
'''
try:
    out = subprocess.run(['node', '-e', node], cwd=ROOT, capture_output=True, text=True, timeout=180)
    if out.returncode or not out.stdout.strip():
        check('Node planner answer-key run', False, (out.stderr or out.stdout or 'no output')[-500:])
    else:
        res = json.loads(out.stdout.strip().splitlines()[-1])
        check('before the key, both Green River SNA tracts are dashed (names differ from the POTA name)',
              res['before']['davis'] is False and res['before']['rush'] is False)
        check('before the key, Fort Heiman is dashed', res['before']['heiman'] is False)
        check('Little South Fork SNA is already solid from the planner alias list, even before the key',
              res['before']['lsf'] is True)
        check('Lake Barkley WMA is not joined before the key', res['before']['barkley'] is False)
        check('after the key, both Green River SNA tracts join US-12752 and draw solid',
              res['after']['davis'] is True and res['after']['rush'] is True
              and res['after']['davisKey']==['US-12752:alias'] and res['after']['rushKey']==['US-12752:alias'])
        check('after the key, Fort Heiman joins and draws solid', res['after']['heiman'] is True)
        check('Little South Fork SNA stays solid after the key', res['after']['lsf'] is True)
        check('Lake Barkley WMA stays unjoined after the key (it is no-number land, not US-7568)',
              res['after']['barkley'] is False)
        check('no remaining dashed outline is one the answer key already joins', res['keyHits']==[])
        b, a = res['beforeC'], res['afterC']
        check(f"planner dashed counts: {b['dashed']} of {b['total']} before the key, {a['dashed']} of {a['total']} after",
              a['total']==b['total'] and a['dashed'] < b['dashed'])
        print('BEFORE dashed:', b['dashed'], 'of', b['total'])
        print('AFTER  dashed:', a['dashed'], 'of', a['total'])
        print('Newly solid:', ', '.join(res['flipped']))
        print('Still dashed:', ', '.join(a['names']))
except Exception as e:
    check(f'Node planner answer-key run ({e})', False)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
