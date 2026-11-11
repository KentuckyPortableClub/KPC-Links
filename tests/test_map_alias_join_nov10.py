"""Park Commander map, Nov 10: official outlines whose names differ from the POTA name still
draw solid when data/ky-answer-key.json already joins them (alias / file / name). The answer
key is loaded once, lazily, and layers restyle after it arrives. Static checks plus a Node
run against the repo's own outline files and key (no network)."""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ok = True
def check(name, cond, detail=''):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name + ((' — ' + detail) if detail and not cond else ''))
    ok = ok and bool(cond)

g = (ROOT / 'gis-overlays.js').read_text(encoding='utf-8')
check('answer key is loaded once, lazily', 'function loadKey()' in g and 'if(keyTried)return keyReadyP' in g and "data/ky-answer-key.json" in g)
check('ref lookup uses the key after properties.ref and before the name-match fallback',
      g.index('const own=ownRef(f)') < g.index('for(const row of keyJoin(f))') < g.index('for(const d of potaPts())'))
check('lookup is by layer + outline name', "f._lk||(f._L&&f._L.k)" in g and "keyOf(f._lk" in g)
check('"no POTA reference" is not remembered before the key has been tried', 'if(v||joinsReady())f._pota=v;else whenJoins()' in g and 'potaPts().length>0&&keyIdx!==null' in g)
check('drawn layers restyle after the key loads, and a cached no-join answer is cleared',
      'keyIdx=buildKeyIdx(j);restyleBounds()' in g and 'delete f._pota' in g)
check('layer key is stamped on each outline so the lookup can use it', 'f._lk=k' in g)
check('key helpers are exposed for tests', 'useAnswerKey' in g and 'keyJoin' in g)

# Tract fields (document what the key writer stores; do not change the key)
key_js = (ROOT / '.github/scripts/kpc_ky_key.js').read_text(encoding='utf-8')
check('key writer stores tracts as [layer, outline name, acres, how, pieces]',
      'tracts: [[layer, outline name, acres, how, pieces]]' in key_js)

key = json.loads((ROOT / 'data/ky-answer-key.json').read_text(encoding='utf-8'))
heiman = (key.get('parks') or {}).get('US-3790') or {}
lsf = (key.get('parks') or {}).get('US-7962') or {}
check('US-3790 Fort Heiman is an alias join on the Fort Heiman NPS tract',
      any(t[0]=='bnps' and t[1]=='Fort Heiman (Fort Donelson National Battlefield tract)' and t[3]=='alias' for t in heiman.get('tracts') or []))
check('US-7962 Little South Fork is an alias join on the Steele Hollow SNA tract',
      any(t[0]=='bsna' and t[1]=='Little South Fork State Natural Area (Steele Hollow SNA)' and t[3]=='alias' for t in lsf.get('tracts') or []))
nonum = {(x[0], x[1]) for x in key.get('nonum') or []}
check('Lake Barkley WMA is in the no-number list, not joined to a POTA park',
      ('bwma', 'Lake Barkley WMA') in nonum and 'US-7568' not in (key.get('parks') or {}))

js = r'''
const fs=require('fs');
global.window=global;
global.document={getElementById:()=>null,querySelector:()=>null,querySelectorAll:()=>[]};
global.matchMedia=()=>({matches:false});
global.fetch=()=>Promise.resolve({ok:false});
global.L={};
const rows=JSON.parse(fs.readFileSync('locations-ky.json','utf8')).rows;
global.data=rows;
eval(fs.readFileSync('gis-overlays.js','utf8'));
const G=kpcGIS;
const key=JSON.parse(fs.readFileSync('data/ky-answer-key.json','utf8'));
function feat(file, name, layer){
  const f=(JSON.parse(fs.readFileSync(file,'utf8')).features||[]).find(x=>(x.properties||{}).NAME===name);
  if(!f) throw new Error('missing '+name+' in '+file);
  f._lk=layer;
  return f;
}
const heiman=feat('ky-nps.geojson','Fort Heiman (Fort Donelson National Battlefield tract)','bnps');
const lsf=feat('ky-natural-areas.geojson','Little South Fork State Natural Area (Steele Hollow SNA)','bsna');
const barkley=feat('ky-hunting-areas.geojson','Lake Barkley WMA','bwma');
const before={
  heiman:G.matchPota(heiman).some(m=>m.d[1]==='US-3790'&&m.why.startsWith('name')),
  lsf:G.matchPota(lsf).some(m=>m.d[1]==='US-7962'&&m.why.startsWith('name')),
  barkley:G.matchPota(barkley).some(m=>m.why.startsWith('name'))||G.keyJoin(barkley).length>0
};
G.useAnswerKey(key);
const after={
  heiman:G.matchPota(heiman).filter(m=>m.d[1]==='US-3790').map(m=>m.why),
  heimanJoin:G.keyJoin(heiman).map(x=>x.ref+':'+x.how),
  lsf:G.matchPota(lsf).filter(m=>m.d[1]==='US-7962').map(m=>m.why),
  barkleyName:G.matchPota(barkley).some(m=>m.why.startsWith('name')),
  barkleyKey:G.keyJoin(barkley)
};
const layers={
  bstate:'ky-state-parks.geojson',bwma:'ky-hunting-areas.geojson',bsnp:'ky-nature-preserves.geojson',
  bsna:'ky-natural-areas.geojson',bdbnf:'ky-dbnf.geojson',bnps:'ky-nps.geojson',bwild:'ky-wild-rivers.geojson',
  bwilder:'ky-wilderness.geojson',bfws:'ky-fws.geojson',busace:'ky-usace.geojson',bpad:'ky-padus-parks.geojson',
  bkpc:'ky-kpc-drawn.geojson'
};
function dashed(useKey){
  if(useKey) G.useAnswerKey(key); else { /* leave as-is; we already injected the key, so count "before" from a fresh eval is done above */ }
  const miss=[];
  let total=0;
  for(const [lk,file] of Object.entries(layers)){
    const s=G.bounds[lk];
    const feats=JSON.parse(fs.readFileSync(file,'utf8')).features||[];
    for(const f of feats){
      if(!f.geometry) continue;
      f._lk=lk;
      total++;
      const has=!!G.ownRef(f)||G.keyJoin(f).length>0||G.matchPota(f).some(x=>x.why.startsWith('name'));
      const style=s.proc?'proc':s.corps?'corps':s.kpc?'kpc':s.own?'own':(has?'solid':'dashed');
      if(style==='dashed') miss.push({lk,nm:(f.properties||{}).NAME||'',key:G.keyJoin(f)});
    }
  }
  return {total,dashed:miss.length,names:miss,keyHits:miss.filter(x=>x.key.length)};
}
const counts=dashed(true);
const pad=JSON.parse(fs.readFileSync('ky-padus-parks.geojson','utf8')).features;
const padOk=pad.every(f=>{f._lk='bpad';return G.ownRef(f)===f.properties.ref && G.matchPota(f).some(m=>m.d[1]===f.properties.ref&&m.why.startsWith('name'))});
console.log(JSON.stringify({before,after,counts:{total:counts.total,dashed:counts.dashed,names:counts.names.map(x=>x.lk+':'+x.nm),keyHits:counts.keyHits},padOk,padN:pad.length}));
'''
try:
    out = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True, timeout=120)
    if out.returncode or not out.stdout.strip():
        check('Node alias-join run', False, (out.stderr or out.stdout or 'no output')[-400:])
    else:
        res = json.loads(out.stdout.strip().splitlines()[-1])
        check('before the key is injected, Fort Heiman is not a name join (pin is inside, names differ)', res['before']['heiman'] is False)
        check('Little South Fork SNA is already a name join from the built-in alias list, even before the key', res['before']['lsf'] is True)
        check('Lake Barkley WMA is not joined before the key', res['before']['barkley'] is False)
        check('after the key, Fort Heiman joins US-3790 as an answer-key alias',
              'name match (KPC answer key)' in res['after']['heiman'] and res['after']['heimanJoin']==['US-3790:alias'])
        check('after the key, Little South Fork SNA still joins US-7962', any(w.startswith('name') for w in res['after']['lsf']))
        check('Lake Barkley WMA stays unjoined after the key (it is no-number land, not US-7568)',
              res['after']['barkleyName'] is False and res['after']['barkleyKey']==[])
        check('PAD-US outlines still join from properties.ref', res['padOk'] and res['padN']==12)
        check('no remaining dashed outline is one the answer key already joins', res['counts']['keyHits']==[])
        check(f"dashed outlines after the key join: {res['counts']['dashed']} of {res['counts']['total']}",
              res['counts']['dashed'] < 48 and res['counts']['total']>=200)
        print('remaining dashed:', ', '.join(res['counts']['names']))
except Exception as e:
    check(f'Node alias-join run ({e})', False)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
