'use strict';
const $=id=>document.getElementById(id), status=$('status');
let data=[],unmapped=[],center=null,markers=[],map=null,layer=null,requestController=null,lastMatches=[];
let showLimit=150,lastSig='';
let potaWWFF=new Map(),sotaLocations=[];
let userLocationMarker=null;
let official2ferEvidence={};fetch('official-2fer-evidence.json').then(r=>r.ok?r.json():{}).then(x=>{official2ferEvidence=x;if(data.length)render()}).catch(()=>{});
let officialParkAccess={};fetch('official-park-access.json').then(r=>r.ok?r.json():{}).then(x=>{officialParkAccess=x;if(data.length)render()}).catch(()=>{});
let officialTrailMaps={};fetch('official-trail-maps.json').then(r=>{if(!r.ok)throw Error('map list');return r.json()}).then(x=>{officialTrailMaps=x; if(data.length)render()}).catch(()=>{});
function buildCrossReferences(){potaWWFF=new Map();sotaLocations=[];for(const d of data){if(d[0]==='WWFF'&&d[7]){const a=potaWWFF.get(d[7])||[];a.push(d[1]);potaWWFF.set(d[7],a)}if(d[0]==='SOTA')sotaLocations.push(d)}}
const savedKey='radio-finder-saved-v1';let saved={favorites:[],trip:[]};try{const v=JSON.parse(localStorage.getItem(savedKey));if(v&&Array.isArray(v.favorites)&&Array.isArray(v.trip))saved=v}catch(_){}
const key=d=>d[0]+':'+d[1];function persist(){try{localStorage.setItem(savedKey,JSON.stringify(saved))}catch(_){}drawSaved()}
function toggleSaved(kind,d){const k=key(d),a=saved[kind];const i=a.indexOf(k);if(i<0){a.push(k)}else{a.splice(i,1)}persist();render()}
function drawSaved(){for(const kind of ['favorites']){const el=$(kind==='favorites'?'favorites':'tripstops');el.replaceChildren();const entries=saved[kind].map(k=>data.find(d=>key(d)===k)).filter(Boolean);$(kind==='favorites'?'favcount':'tripcount').textContent=entries.length;for(const d of entries){const r=node('div','saveditem');r.append(node('span','',d[0]+' '+d[1]+' · '+d[2]));const b=node('button','tiny','Remove');b.type='button';b.addEventListener('click',()=>toggleSaved(kind,d));r.append(b);el.append(r)}if(!entries.length)el.append(node('p','meta','No saved locations yet.'))}if(typeof renderRove==='function')renderRove()}
$('clearplan').addEventListener('click',()=>{saved.trip=[];persist();render()});
// Use one consistent map tile layer. Do not switch providers during zoom or pan.
// Failed tiles can be retried by reloading the page without disturbing map markers.
if(window.L){
  map=L.map('map',{zoomAnimation:true,markerZoomAnimation:true}).setView([39,-97],4);
  (function mapSize(){const el=document.getElementById('map'),wrap=el.parentElement;
   const bar=document.createElement('div');bar.className='mapbar';
   bar.innerHTML='<span class="mapbar-l">MAP SIZE</span><button type="button" data-s="s" class="secondary tiny">Small</button><button type="button" data-s="m" class="secondary tiny">Medium</button><button type="button" data-s="t" class="secondary tiny">Tall</button><button type="button" data-s="f" class="primary tiny mapfs">⛶ Full screen</button><button type="button" class="secondary tiny maplay" hidden>☰ Layers</button><button type="button" class="primary tiny mapx" hidden>✕ Close map</button>';
   el.insertAdjacentElement('beforebegin',bar);
   const H={s:'280px',m:'',t:'78vh'};let cur='m';try{cur=localStorage.getItem('kpcMapSize')||'m'}catch(e){}if(cur==='f')cur='m';
   const fx=()=>setTimeout(()=>map.invalidateSize(),60);
   function set(k){if(k==='f')return full(true);cur=k;try{localStorage.setItem('kpcMapSize',k)}catch(e){}el.style.height=H[k]||'';bar.querySelectorAll('[data-s]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.s===k)));fx()}
   function sizeFull(){if(wrap.classList.contains('kpc-mapfull')){el.style.height='';el.style.minHeight='';el.style.flex=''}else el.style.height=H[cur]||''}
   window.addEventListener('resize',()=>{if(wrap.classList.contains('kpc-mapfull')){sizeFull();map.invalidateSize()}});
   const lph=document.createComment('layers');function moveLayers(on){const drops=[...document.querySelectorAll('.layerdrop')];if(!drops.length)return;let g=wrap.querySelector('.gis-controls');if(on){if(!g){g=document.createElement('div');g.className='gis-controls';wrap.append(g)}if(!lph.parentNode)drops[0].before(lph);drops.forEach(x=>g.append(x))}else if(lph.parentNode){drops.reverse().forEach(x=>lph.after(x));lph.remove();g&&g.classList.remove('open')}}
   function full(on){moveLayers(on);wrap.classList.toggle('kpc-mapfull',on);document.documentElement.classList.toggle('kpc-nofs-scroll',on);bar.querySelector('.mapx').hidden=!on;bar.querySelector('.maplay').hidden=!on;if(!on){const g=wrap.querySelector('.gis-controls');g&&g.classList.remove('open')}bar.querySelector('.mapfs').hidden=on;sizeFull();
    if(on){try{history.pushState({kpcfs:1},'')}catch(e){}}fx()}
   bar.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;if(b.classList.contains('maplay')){const g=wrap.querySelector('.gis-controls');if(g){g.style.top=(bar.offsetTop+bar.offsetHeight+6)+'px';g.classList.toggle('open')}}else if(b.classList.contains('mapx')){if(history.state&&history.state.kpcfs){history.back()}else full(false)}else set(b.dataset.s)});
   window.addEventListener('keydown',e=>{if(e.key==='Escape'&&wrap.classList.contains('kpc-mapfull'))full(false)});
   window.addEventListener('popstate',()=>{if(wrap.classList.contains('kpc-mapfull'))full(false)});
   set(cur);})();
  const tileNotice=document.createElement('p');
  tileNotice.setAttribute('role','status');
  tileNotice.setAttribute('aria-live','polite');
  tileNotice.style.cssText='font-size:13px;color:#f0c96b;margin:7px 0';
  document.getElementById('map').insertAdjacentElement('afterend',tileNotice);
  const baseTiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution:'&copy; OpenStreetMap contributors',
    maxZoom:19, tileSize:256, zoomOffset:0, updateWhenIdle:true, crossOrigin:true
  });
  let tileErrors=0;
  baseTiles.on('tileerror',()=>{
    tileErrors++;
    if(tileErrors>=3)tileNotice.textContent='Some map tiles did not load. Check your internet connection or content blocker, then refresh the page.';
  });
  baseTiles.on('load',()=>{tileErrors=0;tileNotice.textContent='';});
  const esriT=p=>L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/'+p+'/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:p.indexOf('Imagery')>-1?'Imagery &copy; Esri, Maxar, Earthstar Geographics':''});
  const baseMaps={'Road Map':baseTiles,
   'Terrain':L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'&copy; OpenTopoMap (CC-BY-SA), &copy; OpenStreetMap contributors'}),
   'Satellite':L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery &copy; Esri, Maxar, Earthstar Geographics'}),
   'Satellite + Roads':L.layerGroup([esriT('World_Imagery'),esriT('Reference/World_Transportation'),esriT('Reference/World_Boundaries_and_Places')])};
  let wantBase='Road Map';try{wantBase=localStorage.getItem('kpcBaseMap')||'Road Map'}catch(_){}
  wantBase={'Street':'Road Map'}[wantBase]||wantBase;
  (baseMaps[wantBase]||baseTiles).addTo(map);
  L.control.layers(baseMaps,null,{position:'topright',collapsed:true}).addTo(map);
  const satCls=n=>map.getContainer().classList.toggle('kpc-sat',/^Satellite/.test(n));satCls(baseMaps[wantBase]?wantBase:'Road Map');
  map.on('baselayerchange',e=>{satCls(e.name);try{localStorage.setItem('kpcBaseMap',e.name)}catch(_){}});
  layer=L.layerGroup().addTo(map);
  /* parking & entrance markers + Park Overlaps (kpc-map-extras.js, shared with the Trip Planner) */
  if(window.KPCX)window.kpcExtras=KPCX.attach(map,{key:'cmd'});window.kpcMap=map;
  window.addEventListener('load',()=>map.invalidateSize({animate:false}));
}else{status.textContent='Map library could not load; search results can still work.'}
const rad=n=>n*Math.PI/180;
function miles(a,b,c,d){const dl=rad(c-a),dn=rad(d-b),h=Math.sin(dl/2)**2+Math.cos(rad(a))*Math.cos(rad(c))*Math.sin(dn/2)**2;return 3958.7613*2*Math.asin(Math.min(1,Math.sqrt(h)))}
function node(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e}
function link(label,url){const a=node('a','',label);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a}

/* KPC additions: Kentucky guide data (county, park type), Maidenhead grid, shortcuts, remembered search */
let kyGuide=new Map();fetch('kpc-ky-data.json').then(r=>r.ok?r.json():null).then(j=>{if(!j)return;for(const p of j.parks||[])kyGuide.set(p.c,p);for(const p of j.summits||[])kyGuide.set(p.c,p);for(const p of j.kff||[])kyGuide.set(p.c,p);if(data.length)render()}).catch(()=>{});
function grid6(lat,lon){lat=Number(lat)+90;lon=Number(lon)+180;if(!(lat>=0&&lat<=180&&lon>=0&&lon<=360))return '';const A='ABCDEFGHIJKLMNOPQR',a='abcdefghijklmnopqrstuvwx';const f1=Math.floor(lon/20),f2=Math.floor(lat/10),s1=Math.floor((lon%20)/2),s2=Math.floor(lat%10),t1=Math.floor((lon%2)*12),t2=Math.floor((lat%1)*24);return A[f1]+A[f2]+s1+s2+a[t1]+a[t2]}
function kyLine(d){const g=grid6(d[3],d[4]),p=kyGuide.get(d[1]);let co='';if(p&&p.co&&!/official|see /i.test(p.co)){const l=String(p.co).replace(/\?/g,'').split('/').map(x=>x.trim()).filter(Boolean);co=l.length>3?'Multi-county ('+l.length+' counties)':l.length>1?l.join(' / ')+' counties':l[0]+' County'}return [g?'Grid '+g:'',co].filter(Boolean).join(' · ')}

/* KPC: better card links - directions to a real entrance, park-specific pages, camping, and a guide summary line */
const HOSTLBL=[[/parks\.ky\.gov/,'Kentucky State Parks page'],[/fw\.ky\.gov/,'KDFWR area page'],[/eec\.ky\.gov/,'Nature Preserves page'],[/nps\.gov/,'National Park Service page'],[/fs\.usda\.gov/,'Forest Service page'],[/fws\.gov/,'Fish & Wildlife Service page']];
const hostLabel=(u,def)=>{for(const [r,l] of HOSTLBL)if(r.test(u))return l;return def};
const genericCamp=u=>/parks\.ky\.gov\/(parks\/)?camping\/?$|reserve-a-campground\/?$|parks\.ky\.gov\/?$/i.test(u||'');
const TYPENAME={'WMA':'Wildlife Management Area','National / NPS':'National Park Service site'};
function kyExtras(d,kp,links,card){
 const dest=(la,lo)=>`https://www.google.com/maps/dir/?api=1&destination=${la},${lo}&travelmode=driving`;
 let aps=(d[0]==='POTA'&&kp&&Array.isArray(kp.ap))?kp.ap.filter(a=>Number.isFinite(Number(a[0]))&&Number.isFinite(Number(a[1]))):[];
 if(aps.length&&center)aps=aps.slice().sort((a,b)=>miles(center[0],center[1],a[0],a[1])-miles(center[0],center[1],b[0],b[1]));
 const cnt={},tot={};aps.forEach(a=>{const k=String(a[2]||'access point').trim();tot[k]=(tot[k]||0)+1});const nm=a=>{const k=String(a[2]||'access point').replace(/\s+/g,' ').trim().slice(0,32),kk=String(a[2]||'access point').trim();if(tot[kk]>1){cnt[kk]=(cnt[kk]||0)+1;return k+' #'+cnt[kk]}return k};
 if(aps.length){links.append(link('Directions: '+nm(aps[0]),dest(aps[0][0],aps[0][1])));if(Math.abs(aps[0][0]-d[3])>.002||Math.abs(aps[0][1]-d[4])>.002)links.append(link('Directions: park center',dest(d[3],d[4])))}
 else links.append(link('Directions',dest(d[3],d[4])));
 if(aps.length>1){const o=node('div','meta','Other entrances and parking: ');aps.slice(1,6).forEach((a,i)=>{if(i)o.append(document.createTextNode(' · '));o.append(link(nm(a),dest(a[0],a[1])))});card.append(o)}
 if(!kp||d[0]!=='POTA'||kp.t===undefined)return;
 const info=[TYPENAME[kp.t]||kp.t];if(kp.acc)info.push(kp.acc+' access point'+(kp.acc>1?'s':'')+' on record');
 if(kp.camp)info.push('Camping available');
 card.append(node('div','meta','KPC guide: '+info.join(' · ')));
 const seen=new Set([d[5]]);
 if(kp.web&&!seen.has(kp.web)){seen.add(kp.web);links.append(link(hostLabel(kp.web,'Official park page'),kp.web))}
 if(kp.camp&&!seen.has(kp.camp)){seen.add(kp.camp);links.append(link(genericCamp(kp.camp)?'Camping & reservations (state page)':'Campground page',kp.camp));if(genericCamp(kp.camp))card.append(node('div','meta','The camping link opens the statewide Kentucky State Parks camping page. Pick this park there, or use the park page above.'))}
 if(kp.off&&!seen.has(kp.off)){seen.add(kp.off);links.append(link(/\.pdf(\?|$)/i.test(kp.off)?'Official map (PDF)':'Official map / info',kp.off))}
}
function dedupeLinks(box){const seen=new Set();[...box.querySelectorAll('a')].forEach(a=>{if(seen.has(a.href))a.remove();else seen.add(a.href)})}
const LASTKEY='kpcFinderLast';
function saveLast(){try{const q=$('place').value.trim();if(!center&&!q)return;localStorage.setItem(LASTKEY,JSON.stringify({lat:center?center[0]:null,lon:center?center[1]:null,q,radius:$('radius').value,sota:$('sota').checked,pota:$('pota').checked,wwff:$('wwff').checked,t:Date.now()}))}catch(_){}}
function restoreLast(){try{if(location.search)return false;const v=JSON.parse(localStorage.getItem(LASTKEY)||'null');if(!v)return false;if(['25','50','100','200','500'].includes(String(v.radius)))$('radius').value=String(v.radius);$('sota').checked=!!v.sota;$('pota').checked=!!v.pota;$('wwff').checked=!!v.wwff;$('place').value=v.q||'';
 if(Number.isFinite(v.lat)&&Number.isFinite(v.lon)){center=[v.lat,v.lon];render();status.textContent='Showing your last search'+(v.q?' ('+v.q+')':'')+'. Use GPS or search to change it.';return true}
 if(v.q){town();return true}}catch(_){}return false}
/* Other programs at the same place ("Also: KFF-1268 · SOTA W4K/EC-180") and possible POTA 2-fers (v20261010d) */
let sotaToPota=null;
function crossInfo(d,kp,card){const also=[],add=s=>{if(s&&!also.includes(s))also.push(s)};
 if(d[0]==='POTA'){((kp&&kp.kff)||[]).forEach(add);(potaWWFF.get(d[1])||[]).forEach(add);((kp&&kp.sota)||[]).forEach(s=>add('SOTA '+s))}
 else if(d[0]==='WWFF'){add(d[7]?'POTA '+d[7]:(kp&&kp.p?'POTA '+kp.p:''))}
 else if(d[0]==='SOTA'){if(!sotaToPota){sotaToPota=new Map();kyGuide.forEach(p=>{if(p&&Array.isArray(p.sota)&&/^US-/.test(p.c))p.sota.forEach(s=>{const a=sotaToPota.get(s)||[];if(!a.includes(p.c))a.push(p.c);sotaToPota.set(s,a)})})}(sotaToPota.get(d[1])||[]).forEach(r=>add('POTA '+r))}
 if(also.length){const n=node('div','meta alsoin');n.append(node('b','','Also: '),document.createTextNode(also.slice(0,6).join(' · ')+(also.length>6?' +'+(also.length-6)+' more':'')));card.append(n)}
 const tf=d[0]==='POTA'?twoFerRefs(d[1],kp):[];
 if(tf.length){const n=node('div','twofer');n.append(node('b','','Possible POTA 2-fer'),document.createTextNode(' with '+tf.slice(0,4).map(r=>{const o=kyGuide.get(r);return r+(o&&o.n?' ('+o.n+')':'')}).join(', ')+(tf.length>4?' and '+(tf.length-4)+' more':'')+'. Verify before activating.'));card.append(n)}}
/* 2-fer partners: the park file's list plus mapped boundary overlaps of two POTA references (ky-overlaps.geojson, v20261010j) */
let ovIdx=null;
if(window.KPCX)KPCX.overlapIndex().then(ix=>{ovIdx=ix;if(data.length)render()}).catch(()=>{});
function twoFerRefs(ref,kp){const out=[...((kp&&Array.isArray(kp.tf))?kp.tf:[])];
 if(ovIdx)for(const o of ovIdx.get(ref)||[])if(o.kind==='2fer')o.others.forEach(r=>{if(!out.includes(r[0]))out.push(r[0])});
 return out.filter(r=>r!==ref)}
function buildCard(d,dist){const card=node('article','entry');const tag=node('span','tag '+d[0].toLowerCase(),d[0]+' • '+d[1]);card.append(tag,node('h3','',d[2]));const details=[dist===null?'':dist.toFixed(1)+' mi straight-line',Number.isFinite(Number(d[6]))&&d[0]==='SOTA'&&d[6]!==null?'Elevation '+d[6]+' m':'',kyLine(d),Number(d[3]).toFixed(5)+', '+Number(d[4]).toFixed(5)].filter(Boolean).join(' · ');card.append(node('div','meta',details));const kp=kyGuide.get(d[1]);crossInfo(d,kp,card);if(d[0]==='POTA'&&kp&&kp.t==='WMA'){const w=node('div','crossref wma','Public hunting land: check Kentucky Fish & Wildlife season dates and wear blaze orange during gun seasons. ');w.append(link('Hunting seasons','https://fw.ky.gov/Hunt/Pages/ky-hunting-fishing-seasons-planner.aspx'));card.append(w)}const links=node('div','links');if(d[0]==='POTA'&&official2ferEvidence[d[1]]){const e=official2ferEvidence[d[1]];links.append(link(e.map_label,e.map))}links.append(link('Program details',d[5]));kyExtras(d,kp,links,card);links.append(link('Share location',`https://www.google.com/maps/search/?api=1&query=${d[3]},${d[4]}`));if(d[0]==='POTA'&&kp&&kp.t!==undefined){links.append(link('Weather',`kpc-weather.html?lat=${d[3]}&lon=${d[4]}&ref=${encodeURIComponent(d[1])}&name=${encodeURIComponent(d[2])}`),link('Park sheet',`kpc-park-sheet.html?ref=${encodeURIComponent(d[1])}`))}if(d[0]==='POTA'&&officialTrailMaps[d[1]]){const t=officialTrailMaps[d[1]];links.append(link('Official trail map / agency maps',t.url));card.append(node('div','meta',(t.type==='official directory (not park-specific)'?'Agency directory (not a park-specific trail map).':'Official agency resource; map coverage may vary.')+' Verify current routes and activation boundaries.'))}if(d[0]==='POTA'&&officialParkAccess[d[1]]){const access=officialParkAccess[d[1]];if(access.access_url)links.append(link('Official access / trailheads',access.access_url));if(access.camping_url)links.append(link('Official camping information',access.camping_url));if(access.trailheads){const stops=node('div','meta','Official trailhead parking: ');access.trailheads.forEach((t,i)=>{if(i)stops.append(document.createTextNode(' · '));stops.append(link(t.name,`https://www.google.com/maps/search/?api=1&query=${t.lat},${t.lon}`))});card.append(stops)}if(access.note)card.append(node('div','meta',access.note))}dedupeLinks(links);card.append(links);const actions=node('div','saveactions');for(const [kind,label] of [['favorites','Favorite'],['trip','Trip stop']]){const b=node('button','tiny', (saved[kind].includes(key(d))?'✓ ':'+ ')+label);b.type='button';b.setAttribute('aria-pressed',String(saved[kind].includes(key(d))));b.addEventListener('click',()=>toggleSaved(kind,d));actions.append(b)}card.append(actions);card.dataset.k=key(d);return card}
function hdrOff(){let off=0;for(const e of document.querySelectorAll('header,nav,div')){const cs=getComputedStyle(e);if((cs.position==='fixed'||cs.position==='sticky')&&e.offsetHeight<200&&e.offsetWidth>innerWidth*.6){const r=e.getBoundingClientRect();if(r.top<=2)off=Math.max(off,r.bottom)}}return off}
const sideBySide=()=>matchMedia('(min-width:1000px)').matches;
function showSelected(d,go){const k=key(d);let m=[...document.querySelectorAll('#items .entry')].find(e=>e.dataset.k===k);
 if(!m&&go){const idx=lastMatches.findIndex(x=>key(x[0])===k);if(idx>=0){showLimit=Math.ceil((idx+1)/150)*150;render();m=[...document.querySelectorAll('#items .entry')].find(e=>e.dataset.k===k)}}
 document.querySelectorAll('#items .entry.sel').forEach(e=>e.classList.remove('sel'));if(!m)return;m.classList.add('sel');
 const items=$('items');
 if(sideBySide()){items.scrollTo({top:items.scrollTop+m.getBoundingClientRect().top-items.getBoundingClientRect().top-6,behavior:go?'smooth':'auto'});if(go){const r=items.getBoundingClientRect();if(r.top<hdrOff()||r.top>innerHeight*.5)window.scrollTo({top:Math.max(0,r.top+scrollY-hdrOff()-60),behavior:'smooth'})}return}
 if(go)window.scrollTo({top:Math.max(0,m.getBoundingClientRect().top+scrollY-hdrOff()-12),behavior:'smooth'})}
function popCard(d){const dist=center?miles(center[0],center[1],d[3],d[4]):null;const w=node('div','kpc-popcard');w.append(buildCard(d,dist));const b=node('button','popgo',sideBySide()?'Find in Nearby list →':'Show in Nearby list ↓');b.type='button';b.addEventListener('click',()=>{if(map)map.closePopup();showSelected(d,true)});w.append(b);if(!matchMedia('(hover:none)').matches)w.append(node('div','pophint','Tip: double-click a pin to jump to it in the list.'));return w}
function render(){if(!data.length)return;const radius=Number($('radius').value),on={SOTA:$('sota').checked,POTA:$('pota').checked,WWFF:$('wwff').checked};const ref=$('place').value.trim().toUpperCase();const isRef=/^(?:W\d[A-Z]*\/|US-\d|KFF-\d)/.test(ref);let found=[];const exactRef=isRef&&data.some(d=>on[d[0]]&&d[1].toUpperCase()===ref);for(const d of data){if(!on[d[0]])continue;if(isRef){if(exactRef?d[1].toUpperCase()!==ref:!d[1].toUpperCase().includes(ref))continue;found.push([d,center?miles(center[0],center[1],d[3],d[4]):null]);}else if(center){let distance=miles(center[0],center[1],d[3],d[4]);if(distance<=radius)found.push([d,distance]);}}const sig=[center,radius,on.SOTA,on.POTA,on.WWFF,ref].join('|');const sigChanged=sig!==lastSig;if(sigChanged){showLimit=150;lastSig=sig}found.sort((a,b)=>isRef?a[0][1].localeCompare(b[0][1]):a[1]-b[1]);lastMatches=found;const shown=found.slice(0,showLimit);$('count').textContent=(found.length+(isRef&&on.WWFF?unmapped.filter(x=>x[0].includes(ref)).length:0)).toLocaleString()+' found';const items=$('items');items.replaceChildren();if(isRef&&on.WWFF){for(const r of unmapped.filter(x=>x[0].includes(ref)).slice(0,50)){const card=node('article','entry');card.append(node('span','tag wwff','WWFF • '+r[0]),node('h3','',r[1]||r[0]),node('div','meta',[r[2],r[3],'Coordinates not supplied — reference lookup only'].filter(Boolean).join(' · ')));items.append(card)}}if(layer)layer.clearLayers();const bounds=[];for(const [d,dist] of shown){const card=buildCard(d,dist);items.append(card)}if(isRef&&found.length===1){const p=found[0][0];const nb=node('button','secondary nearbybtn','\ud83d\udccd Show nearby parks ('+radius+' mi around '+p[1]+')');nb.type='button';nb.style.cssText='width:100%;margin-top:10px';nb.addEventListener('click',()=>{center=[p[3],p[4]];$('place').value='';status.textContent='Showing parks within '+radius+' miles of '+p[1]+'.';render()});items.append(nb)}
if(layer){for(const [d] of found.slice(0,2500)){const pinColor=d[0]==='SOTA'?'#168454':d[0]==='WWFF'?'#b04ae8':'#d5a63a';const pinIcon=L.divIcon({className:'kpc-map-pin',html:'<span style="display:block;width:16px;height:16px;border:2px solid white;border-radius:50%;background:'+pinColor+';box-shadow:0 1px 6px #000c"></span>',iconSize:[16,16],iconAnchor:[8,8]});const mark=L.marker([d[3],d[4]],{icon:pinIcon,title:d[0]+' '+d[1]+' — '+d[2]}).addTo(layer);const popup=node('div');popup.append(node('strong','',d[2]),node('div','',d[1]),link('Directions',`https://www.google.com/maps/dir/?api=1&destination=${d[3]},${d[4]}`));mark.bindPopup(()=>popCard(d),{maxWidth:300,minWidth:200,maxHeight:300,autoPanPadding:[10,10],className:'kpc-popcard-wrap'});mark.on('popupopen',ev=>{const sz=map.getSize(),p=ev.popup;p.options.maxWidth=Math.max(190,Math.min(320,sz.x-60));p.options.minWidth=Math.min(220,p.options.maxWidth);p.options.maxHeight=Math.max(150,Math.min(340,Math.round(sz.y*.58)-40));p.update()});mark.on('click',()=>showSelected(d,false));mark.on('dblclick',e=>{if(e.originalEvent)L.DomEvent.stop(e.originalEvent);showSelected(d,true)});bounds.push([d[3],d[4]])}}
if(!shown.length&&!items.children.length)items.append(node('p','empty',center||isRef?'No matching locations. Try a wider radius or another program.':'Use GPS or enter a town to begin.'));if(map&&sigChanged){if(bounds.length)map.fitBounds(bounds,{padding:[30,30],maxZoom:11});else if(center)map.setView(center,9)}saveLast();if(found.length>showLimit){const more=node('button','secondary','Show '+Math.min(150,found.length-showLimit)+' more (showing '+showLimit+' of '+found.length.toLocaleString()+')');more.type='button';more.addEventListener('click',()=>{showLimit+=150;render()});items.append(more)}status.textContent=found.length>showLimit?`Showing the nearest ${showLimit} of ${found.length.toLocaleString()} in the list; all matches are pinned on the map.`:`${found.length.toLocaleString()} matching locations.`}
async function town(){const value=$('place').value.trim();if(!value){status.textContent='Enter a town, state, ZIP, or reference number.';return}if(/^(?:W\d[A-Z]*\/|US-\d|KFF-\d)/i.test(value)){render();return}status.textContent='Looking up town…';$('town').disabled=true;try{if(requestController)requestController.abort();requestController=new AbortController();const res=await fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=us&q='+encodeURIComponent(value),{signal:requestController.signal});if(!res.ok)throw Error('Town lookup unavailable');const j=await res.json();if(!j.length){status.textContent='Town not found. Try including the state abbreviation.';return}center=[Number(j[0].lat),Number(j[0].lon)];render()}catch(e){if(e.name!=='AbortError')status.textContent='Town lookup failed. Please retry.'}finally{$('town').disabled=false}}
$('town').addEventListener('click',town);$('place').addEventListener('keydown',e=>{if(e.key==='Enter')town()});$('gps').addEventListener('click',()=>{if(!navigator.geolocation){status.textContent='GPS is unavailable in this browser.';return}status.textContent='Requesting GPS permission…';navigator.geolocation.getCurrentPosition(p=>{center=[p.coords.latitude,p.coords.longitude];$('place').value='';render();if(map&&window.L){if(userLocationMarker)map.removeLayer(userLocationMarker);userLocationMarker=L.marker(center,{icon:L.divIcon({className:'kpc-user-location',html:'<span></span>',iconSize:[20,20],iconAnchor:[10,10]}),title:'You are here',zIndexOffset:1000}).addTo(map).bindPopup('<strong>You are here</strong><div>Approximate GPS location</div>');userLocationMarker.openPopup();map.setView(center,11,{animate:false});map.invalidateSize();}status.textContent='GPS location found. Blue dot shows your reported location ('+Math.round(p.coords.accuracy)+' m accuracy).';},e=>{status.textContent='Could not get GPS location: '+e.message},{enableHighAccuracy:false,timeout:15000,maximumAge:60000})});['sota','pota','wwff','radius'].forEach(id=>$(id).addEventListener('change',render));
Promise.all([fetch('locations.json').then(r=>{if(!r.ok)throw Error('Missing locations.json');return r.json()}),fetch('wwff-unmapped.json').then(r=>r.ok?r.json():[])]).then(([j,u])=>{data=j;unmapped=u;buildCrossReferences();drawSaved();status.textContent=`Loaded ${data.length.toLocaleString()} mapped SOTA, POTA and WWFF locations. Use GPS or search for a town.`;restoreSearch();if(!center&&!$('place').value.trim())restoreLast()}).catch(()=>{status.textContent='Could not load finder data files. Upload them beside finder.html on an HTTPS website.'});


// Offline exports contain only user-visible program data; no GPS location is transmitted by this feature.
function exportCSV(records,filename){
 const rows=[['Program','Reference','Name','Latitude','Longitude','Details URL','Distance (miles)']];
 for(const [d,dist] of records)rows.push([d[0],d[1],d[2],d[3],d[4],d[5],dist==null?'':dist.toFixed(1)]);
 const content=rows.map(row=>row.map(v=>'"'+String(v??'').replace(/"/g,'""')+'"').join(',')).join('\r\n');
 const blob=new Blob(['\uFEFF',content],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$('exportresults').addEventListener('click',()=>{if(!lastMatches.length){status.textContent='Search for locations before exporting.';return}exportCSV(lastMatches,'activation-search-results.csv')});
$('exporttrip').addEventListener('click',()=>{const matches=saved.trip.map(k=>data.find(d=>key(d)===k)).filter(Boolean).map(d=>[d,null]);if(!matches.length){status.textContent='Add a trip stop before exporting.';return}exportCSV(matches,'activation-trip.csv')});
$('sharesearch').addEventListener('click',async()=>{const url=new URL(location.href);if(center){url.searchParams.set('lat',center[0].toFixed(5));url.searchParams.set('lon',center[1].toFixed(5))}else{url.searchParams.delete('lat');url.searchParams.delete('lon')}url.searchParams.set('radius',$('radius').value);url.searchParams.set('sota',$('sota').checked?'1':'0');url.searchParams.set('pota',$('pota').checked?'1':'0');url.searchParams.set('wwff',$('wwff').checked?'1':'0');if($('place').value.trim())url.searchParams.set('q',$('place').value.trim());else url.searchParams.delete('q');try{if(navigator.share)await navigator.share({title:'KY Park Commander',url:url.href});else if(navigator.clipboard){await navigator.clipboard.writeText(url.href);status.textContent='Search link copied.'}else{prompt('Copy this search link',url.href)}}catch(e){if(e.name!=='AbortError')status.textContent='Unable to share this search.'}});
function restoreSearch(){const q=new URLSearchParams(location.search);const radius=q.get('radius');if(['25','50','100','200','500'].includes(radius))$('radius').value=radius;if(q.has('sota'))$('sota').checked=q.get('sota')==='1';if(q.has('pota'))$('pota').checked=q.get('pota')==='1';if(q.has('wwff'))$('wwff').checked=q.get('wwff')==='1';const query=q.get('q');if(query)$('place').value=query;const lat=Number(q.get('lat')),lon=Number(q.get('lon'));if(q.has('lat')&&q.has('lon')&&Number.isFinite(lat)&&Number.isFinite(lon)&&Math.abs(lat)<=90&&Math.abs(lon)<=180){center=[lat,lon];render()}else if(query){town()}}

// Trail guide town shortcuts; actual route GIS not included in this package.
document.querySelectorAll(".trailsearch").forEach(button=>button.addEventListener("click",()=>{ $("place").value=button.dataset.town;town();document.querySelector(".resultshead").scrollIntoView({behavior:"smooth",block:"start"});}));

/* KPC: out-of-state visitors can jump to Kentucky */
(function(){const b=document.getElementById('ky-jump');if(!b)return;b.addEventListener('click',()=>{center=[37.84,-85.7];$('place').value='';$('radius').value='200';render();if(map&&window.L)map.setView([37.8,-85.7],7,{animate:false});status.textContent='Showing locations within 200 miles of central Kentucky. Use GPS or search to change it.'})})();

/* KPC: POTA activity (times activated, last activated) - loaded only when a card's button is tapped */
(function(){
 const items=document.getElementById('items');if(!items)return;
 const CK='kpcPotaActivity_v1',TTL=6*3600e3;
 const cache=(()=>{try{return JSON.parse(localStorage.getItem(CK)||'{}')}catch(e){return{}}})();
 const keep=()=>{try{localStorage.setItem(CK,JSON.stringify(cache))}catch(e){}};
 const j=async u=>{const c=new AbortController(),t=setTimeout(()=>c.abort(),12000);try{const r=await fetch(u,{signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}};
 const fmt=s=>{s=String(s||'');const m=s.match(/^(\d{4})-?(\d{2})-?(\d{2})/);if(!m)return s;const d=new Date(Date.UTC(+m[1],+m[2]-1,+m[3],12));const days=Math.round((Date.now()-d)/864e5);const nice=d.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});return nice+(days>=0&&days<400?' ('+(days<1?'today':days===1?'yesterday':days+' days ago')+')':'')};
 async function load(ref){
  const c=cache[ref];if(c&&Date.now()-c.t<TTL)return c;
  const base='https://api.pota.app/park/';
  const [st,ac]=await Promise.all([j(base+'stats/'+ref),j(base+'activations/'+ref+'?count=1').catch(()=>null)]);
  const last=Array.isArray(ac)&&ac[0]?ac[0]:null;
  const r={t:Date.now(),acts:Number(st&&st.activations),attempts:Number(st&&st.attempts),qsos:Number(st&&st.contacts),last:last&&(last.qso_date||last.date||''),by:last&&(last.activeCallsign||last.callsign||'')};
  cache[ref]=r;keep();return r}
 function show(box,r){
  box.textContent='';
  if(!Number.isFinite(r.acts)){box.textContent='No activity data returned for this park.';return}
  const parts=[];
  if(r.acts===0&&!r.last)parts.push('Not activated yet - be the first!');
  else{parts.push('Activated '+r.acts.toLocaleString()+' time'+(r.acts===1?'':'s'));if(r.last)parts.push('last '+fmt(r.last)+(r.by?' by '+r.by:''));if(Number.isFinite(r.qsos)&&r.qsos>0)parts.push(r.qsos.toLocaleString()+' contacts logged')}
  box.textContent=parts.join(' · ')}
 const io='IntersectionObserver' in window?new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){io.unobserve(e.target);e.target.__go&&e.target.__go()}}),{rootMargin:'200px'}):null;
 let busy=0;const q=[];const pump=()=>{while(busy<3&&q.length){const f=q.shift();busy++;f().finally(()=>{busy--;pump()})}};
 function add(card){
  if(card.dataset.act)return;const tag=card.querySelector('.tag.pota');if(!tag)return;
  const m=tag.textContent.match(/US-\d+|[A-Z]{1,2}-\d{3,5}/);if(!m)return;card.dataset.act='1';
  const ref=m[0],wrap=document.createElement('div');wrap.className='meta kpc-act';wrap.style.cssText='margin-top:8px;padding:8px 10px;border-left:3px solid #d5a63a;background:rgba(213,166,58,.08)';
  const out=document.createElement('span');out.textContent='POTA activity: loading...';
  const b=document.createElement('button');b.type='button';b.className='secondary';b.textContent='Try again';b.style.cssText='display:none;margin-left:8px;padding:6px 10px;font-size:12px';
  const run=()=>new Promise(res=>{q.push(()=>load(ref).then(x=>{show(out,x);out.textContent='POTA activity: '+out.textContent}).catch(()=>{out.textContent='POTA activity could not load (offline or POTA not answering).';b.style.display='inline-block'}).finally(res));pump()});
  b.onclick=()=>{out.textContent='POTA activity: loading...';b.style.display='none';run()};wrap.append(out,b);card.append(wrap);card.__go=run;
  if(io)io.observe(card);else card.__go()}
 const scan=()=>items.querySelectorAll('article.entry').forEach(add);
 new MutationObserver(scan).observe(items,{childList:true});scan();
})();

/* KPC: park-name suggestions - type part of a park, summit or WWFF name and tap a match */
(function(){
 const inp=document.getElementById('place');if(!inp)return;
 const box=document.createElement('div');box.id='kpc-sugg';box.style.cssText='display:none;margin-top:8px;border:1px solid #80632e;border-radius:10px;background:#151515;overflow:hidden';
 const row=inp.closest('.inputrow')||inp.parentElement;row.insertAdjacentElement('afterend',box);
 const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9 ]+/g,' ').replace(/\s+/g,' ').trim();
 let idx=null;const build=()=>{if(idx||!data.length)return;idx=data.map(d=>[norm(d[2]),d])};
 const show=()=>{const q=norm(inp.value);box.textContent='';
  if(q.length<3||/^(w\d[a-z]*\/|us-\d|kff-\d)/i.test(inp.value.trim())){box.style.display='none';return}
  build();if(!idx){box.style.display='none';return}
  const words=q.split(' ');const hits=[];
  for(const [n,d] of idx){if(words.every(w=>n.includes(w))){hits.push([n.startsWith(q)?0:n.includes(' '+q)?1:2,d])}}
  hits.sort((a,b)=>a[0]-b[0]||(a[1][0]==='POTA'?0:1)-(b[1][0]==='POTA'?0:1)||String(a[1][2]).localeCompare(String(b[1][2])));
  if(!hits.length){box.style.display='none';return}
  const h=document.createElement('div');h.textContent='Parks and summits matching "'+inp.value.trim()+'" - tap one to open it, or press SEARCH for a town';h.style.cssText='font-size:12px;color:#c9c5bc;padding:8px 12px;border-bottom:1px solid #493d2b';box.append(h);
  hits.slice(0,8).forEach(([,d])=>{const b=document.createElement('button');b.type='button';b.style.cssText='display:block;width:100%;text-align:left;background:none;color:#f5f0e4;border:0;border-bottom:1px solid #2a2418;border-radius:0;padding:11px 12px;font-weight:600;white-space:normal';
   b.textContent=d[2]+'  \u2022  '+d[0]+' '+d[1];b.onclick=()=>{inp.value=d[1];box.style.display='none';center=null;render();try{inp.blur()}catch(_){}};box.append(b)});
  if(hits.length>8){const m=document.createElement('div');m.textContent=(hits.length-8)+' more - keep typing to narrow it down';m.style.cssText='font-size:12px;color:#c9c5bc;padding:8px 12px';box.append(m)}
  box.style.display='block'};
 inp.addEventListener('input',show);inp.addEventListener('keydown',e=>{if(e.key==='Escape')box.style.display='none'});
})();

/* Jump links: land the section just under the sticky navbar, and re-aim if the page grows while scrolling (v20261010a) */
document.addEventListener('click',e=>{const a=e.target.closest('.finder-jump a[href^="#"]');if(!a||e.ctrlKey||e.metaKey||e.shiftKey)return;const t=document.querySelector(a.getAttribute('href'));if(!t)return;e.preventDefault();
 const y=()=>Math.max(0,Math.round(t.getBoundingClientRect().top+scrollY-hdrOff()-12));let tries=0,timer=0;
 const settle=()=>{clearTimeout(timer);timer=setTimeout(()=>{const d=y();if(Math.abs(d-scrollY)>6&&tries++<4)scrollTo({top:d,behavior:Math.abs(d-scrollY)>1500?'auto':'smooth'}),settle();else removeEventListener('scroll',settle)},180)};
 addEventListener('scroll',settle,{passive:true});scrollTo({top:y(),behavior:'smooth'});settle();
 try{history.replaceState(null,'',a.getAttribute('href'))}catch(_){}});


/* Rove planner (v20261010m): one list of stops, as many as you like.
   Add parks from the search results (+ Trip stop) and drop your own pins anywhere: home, a parking lot,
   a pull-off, lunch. Put them in any order. Drag a park's pin to the lot you will really drive to.
   Google Maps takes about 10 stops per link, so a big rove opens as legs that pick up where the last one ended. */
const ROVEKEY='kpcRove',ROVEOPT='kpcRoveOpt',LEG=11;            // a Google Maps link: origin + 9 waypoints + destination
var rove=null,roveLay=null,roveAdding=false,roveOpt={first:false}; // var: drawSaved() runs before this block is reached
try{const o=JSON.parse(localStorage.getItem(ROVEOPT)||'null');if(o)roveOpt=Object.assign(roveOpt,o)}catch(_){}
const rid=()=>Math.random().toString(36).slice(2,9);
const okLL=p=>p&&p.la!=null&&p.lo!=null&&Number.isFinite(+p.la)&&Number.isFinite(+p.lo);
const fmtLL=p=>(+p.la).toFixed(5)+', '+(+p.lo).toFixed(5);
function esc2(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
let byKey=null,byKeyN=0;function dOf(k){if(!byKey||byKeyN!==data.length){byKey=new Map(data.map(d=>[key(d),d]));byKeyN=data.length}return byKey.get(k)}
function saveRove(){try{localStorage.setItem(ROVEKEY,JSON.stringify(rove))}catch(_){}}
function loadRove(){if(rove)return rove;
 try{const v=JSON.parse(localStorage.getItem(ROVEKEY)||'null');if(Array.isArray(v))rove=v.filter(s=>s&&(s.t==='park'?typeof s.k==='string':okLL(s)))}catch(_){}
 if(!rove){rove=[];let en={},sp={};try{en=JSON.parse(localStorage.getItem('kpcCmdEnds')||'{}')||{}}catch(_){}try{sp=JSON.parse(localStorage.getItem('kpcCmdSpots')||'{}')||{}}catch(_){}
  // carry over an earlier Start / End and arrival spots
  if(okLL(en.s))rove.push({id:rid(),t:'pin',la:+en.s.la,lo:+en.s.lo,n:en.s.n||'Start'});
  saved.trip.forEach(k=>{const x=sp[k];rove.push({id:rid(),t:'park',k,la:okLL(x)?+x.la:null,lo:okLL(x)?+x.lo:null,n:okLL(x)?(x.n||'My spot'):''})});
  if(en.round&&okLL(en.s))rove.push({id:rid(),t:'pin',la:+en.s.la,lo:+en.s.lo,n:(en.s.n||'Start')+' (back home)'});
  else if(okLL(en.e))rove.push({id:rid(),t:'pin',la:+en.e.la,lo:+en.e.lo,n:en.e.n||'End'});
  saveRove()}
 return rove}
/* parks follow the + Trip stop buttons: new ones go on the end, removed ones leave the list */
function syncRove(){loadRove();const have=new Set(rove.filter(s=>s.t==='park').map(s=>s.k));let ch=false;
 saved.trip.forEach(k=>{if(!have.has(k)){rove.push({id:rid(),t:'park',k,la:null,lo:null,n:''});ch=true}});
 const before=rove.length;rove=rove.filter(s=>s.t!=='park'||saved.trip.includes(s.k));if(ch||rove.length!==before)saveRove()}
function ptOf(s){if(s.t==='park'){if(okLL(s))return {la:+s.la,lo:+s.lo};const d=dOf(s.k);return d?{la:+d[3],lo:+d[4]}:null}return okLL(s)?{la:+s.la,lo:+s.lo}:null}
function nameOf(s){if(s.t==='pin')return s.n||'Pin';const d=dOf(s.k);return d?d[1]+' · '+d[2]:s.k.replace(':',' ')}
function stops(){return loadRove().map(s=>({s,p:ptOf(s)})).filter(x=>x.p)}
function nearPark(la,lo){let best=null;kyGuide.forEach(p=>{if(!p||!/^US-/.test(p.c)||!Number.isFinite(p.la))return;const m=miles(la,lo,p.la,p.lo);if(m<1.5&&(!best||m<best.m))best={p,m}});return best}
function addPin(la,lo,n){loadRove();const np=n?null:nearPark(la,lo);
 rove.push({id:rid(),t:'pin',la:+(+la).toFixed(6),lo:+(+lo).toFixed(6),n:n||(np?(np.m<.15?'Pin at ':'Pin near ')+np.p.n:'Pin '+(rove.filter(s=>s.t==='pin').length+1))});saveRove();renderRove()}
function removeStop(id){const s=rove.find(x=>x.id===id);if(!s)return;
 if(s.t==='park'){const i=saved.trip.indexOf(s.k);if(i>=0)saved.trip.splice(i,1);rove=rove.filter(x=>x.id!==id);saveRove();persist();render();return}
 rove=rove.filter(x=>x.id!==id);saveRove();renderRove()}
function moveStop(id,dir){const i=rove.findIndex(x=>x.id===id),j=i+dir;if(i<0||j<0||j>=rove.length)return;[rove[i],rove[j]]=[rove[j],rove[i]];saveRove();renderRove()}
function nearestOrder(){const L0=stops();if(L0.length<3)return;const out=[L0[0]],left=L0.slice(1);
 while(left.length){const c=out[out.length-1].p;let bi=0,bd=Infinity;left.forEach((x,i)=>{const m=miles(c.la,c.lo,x.p.la,x.p.lo);if(m<bd){bd=m;bi=i}});out.push(left.splice(bi,1)[0])}
 const ids=out.map(x=>x.s.id);rove.sort((a,b)=>ids.indexOf(a.id)-ids.indexOf(b.id));saveRove();renderRove();status.textContent='Stops put in nearest-next order, starting from stop 1.'}
/* Google Maps links: one per leg of up to 11 points; each leg starts where the last one ended */
function legs(){const P=stops().map(x=>x.p.la+','+x.p.lo);if(!P.length)return [];const out=[];let i=0;
 if(!roveOpt.first){const end=Math.min(P.length,LEG-1);out.push({o:null,pts:P.slice(0,end),a:1,b:end});i=end-1}
 while(i<P.length-1){const end=Math.min(P.length,i+LEG);out.push({o:P[i],pts:P.slice(i+1,end),a:i+1,b:end});i=end-1}
 if(!out.length)out.push({o:null,pts:P.slice(0,1),a:1,b:1});
 return out.map(l=>({a:l.a,b:l.b,href:'https://www.google.com/maps/dir/?api=1'+(l.o?'&origin='+encodeURIComponent(l.o):'')+'&destination='+encodeURIComponent(l.pts[l.pts.length-1])+(l.pts.length>1?'&waypoints='+encodeURIComponent(l.pts.slice(0,-1).join('|')):'')+'&travelmode=driving'}))}
function gpx(){const x=s=>String(s).replace(/[<>&"']/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&apos;'}[c]));const L0=stops();
 const w=L0.map((t,i)=>`<wpt lat="${t.p.la}" lon="${t.p.lo}"><name>${x((i+1)+'. '+nameOf(t.s))}</name>${t.s.t==='park'&&t.s.n?`<desc>${x('Drive to: '+t.s.n)}</desc>`:''}</wpt>`).join('\n');
 return `<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="KY Park Commander" xmlns="http://www.topografix.com/GPX/1/1">\n<metadata><name>KPC rove</name><time>${new Date().toISOString()}</time></metadata>\n${w}\n<rte><name>KPC rove</name>\n`+L0.map((t,i)=>`<rtept lat="${t.p.la}" lon="${t.p.lo}"><name>${x((i+1)+'. '+nameOf(t.s))}</name></rtept>`).join('\n')+`\n</rte>\n</gpx>\n`}
function shareUrl(){const o=stops().map(t=>t.s.t==='park'?['p',t.s.k,okLL(t.s)?+t.s.la:null,okLL(t.s)?+t.s.lo:null,t.s.n||'']:['s',t.p.la,t.p.lo,t.s.n||'']);
 const b=btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');return location.origin+location.pathname+'?rove='+b+'#finder-planner'}
function readShared(){const c=new URLSearchParams(location.search).get('rove');if(!c)return;
 try{const o=JSON.parse(decodeURIComponent(escape(atob(c.replace(/-/g,'+').replace(/_/g,'/')))));const r=[],trip=[];
  for(const s of o){if(s[0]==='p'&&typeof s[1]==='string'){r.push({id:rid(),t:'park',k:s[1],la:Number.isFinite(s[2])?s[2]:null,lo:Number.isFinite(s[3])?s[3]:null,n:String(s[4]||'').slice(0,60)});trip.push(s[1])}
   else if(s[0]==='s'&&Number.isFinite(+s[1])&&Number.isFinite(+s[2]))r.push({id:rid(),t:'pin',la:+s[1],lo:+s[2],n:String(s[3]||'Shared pin').slice(0,60)})}
  if(r.length){rove=r;saved.trip=trip;saveRove();try{localStorage.setItem(savedKey,JSON.stringify(saved))}catch(_){}status.textContent='Rove loaded from a shared link: '+r.length+' stops.'}}catch(_){status.textContent='That shared rove link could not be read.'}}
/* the list under Trip stops */
function renderRove(){const box=$('tripstops');if(!box)return;syncRove();const L0=stops();$('tripcount').textContent=L0.length;
 const old=$('triproute');if(old)old.hidden=true;
 let h='';
 if(!L0.length)h='<p class="meta">No stops yet. Tap <b>+ Trip stop</b> on any park, or <b>📍 Add pins</b> and tap the map: your home, a parking lot, a pull-off, lunch. Add as many as you like.</p>';
 else h='<ol class="rovelist">'+L0.map((t,i)=>{const s=t.s,park=s.t==='park';
  const sub=park?(okLL(s)?`Drive to: <b>${esc2(s.n||'my pin')}</b> · ${fmtLL(t.p)} <button type="button" class="linkbtn" data-rv="reset" data-id="${s.id}">use park pin</button>`:`Park pin · ${fmtLL(t.p)} <span class="rv-hint">(drag it on the map to a closer lot)</span>`):fmtLL(t.p);
  return `<li class="rv-${park?'park':'pin'}" data-id="${s.id}"><span class="rv-n">${i+1}</span><div class="rv-b">${park?`<div class="rv-t">${esc2(nameOf(s))}</div>`:`<input class="rv-in" type="text" maxlength="60" value="${esc2(s.n)}" data-id="${s.id}" aria-label="Name for stop ${i+1}">`}<div class="rv-s">${sub}</div></div>
  <div class="rv-m"><button type="button" data-rv="show" data-id="${s.id}" title="Show on map">◎</button><button type="button" data-rv="up" data-id="${s.id}" ${i?'':'disabled'} aria-label="Move up">▲</button><button type="button" data-rv="dn" data-id="${s.id}" ${i<L0.length-1?'':'disabled'} aria-label="Move down">▼</button><button type="button" data-rv="rm" data-id="${s.id}" aria-label="Remove">✕</button></div></li>`}).join('')+'</ol>';
 const lg=legs();
 h+=`<div class="rove-tools"><button type="button" class="tiny ${roveAdding?'primary':''}" data-rv="add">${roveAdding?'✓ Done adding pins':'📍 Add pins'}</button><button type="button" class="tiny secondary" data-rv="gps">📍 Add my location</button>${L0.length>2?'<button type="button" class="tiny secondary" data-rv="order">Nearest-next order</button>':''}</div>`;
 if(L0.length){h+=`<label class="rove-first"><input type="checkbox" id="roveFirst" ${roveOpt.first?'checked':''}> Start the route at stop 1 (otherwise Google starts from where you are)</label>`;
  h+='<div class="rove-legs">'+lg.map((l,i)=>`<a class="routebtn" href="${l.href}" target="_blank" rel="noopener noreferrer">${lg.length===1?'Open rove in Google Maps: '+L0.length+' stop'+(L0.length===1?'':'s'):'Leg '+(i+1)+' in Google Maps: stops '+l.a+'–'+l.b}</a>`).join('')+'</div>';
  if(lg.length>1)h+=`<p class="meta">Google Maps takes about 10 stops per link, so this rove opens as ${lg.length} legs. Each leg starts where the last one ended.</p>`;
  h+=`<div class="rove-tools"><button type="button" class="tiny secondary" data-rv="gpx">⬇ GPX file</button><button type="button" class="tiny secondary" data-rv="share">Share rove link</button></div>`}
 box.innerHTML=h;drawRovePins()}
function drawRovePins(){if(!map||!window.L)return;if(!roveLay)roveLay=L.layerGroup().addTo(map);roveLay.clearLayers();const L0=stops();
 if(L0.length>1)L.polyline(L0.map(t=>[t.p.la,t.p.lo]),{color:'#d5a63a',weight:3,opacity:.85,dashArray:'2 8',interactive:false}).addTo(roveLay);
 L0.forEach((t,i)=>{const s=t.s,park=s.t==='park';
  const m=L.marker([t.p.la,t.p.lo],{draggable:true,autoPan:true,zIndexOffset:1900,title:'Stop '+(i+1)+': '+nameOf(s),
   icon:L.divIcon({className:'',html:`<span class="endpin" style="background:${park?'#1d5a3a':'#2456a6'}">${i+1}</span>`,iconSize:[30,30],iconAnchor:[15,30],popupAnchor:[0,-28]})})
   .bindPopup(()=>`<b>Stop ${i+1}: ${esc2(nameOf(s))}</b>${park&&s.n?'<br>Drive to: '+esc2(s.n):''}<br>${fmtLL(t.p)}<br><a href="https://www.google.com/maps/dir/?api=1&destination=${t.p.la},${t.p.lo}&travelmode=driving" target="_blank" rel="noopener">Directions ↗</a> · <button type="button" class="linkbtn" data-rv="rm" data-id="${s.id}">Remove</button><br><small>Drag the pin to move it.</small>`).addTo(roveLay);
  m.on('dragend',()=>{const ll=m.getLatLng();s.la=+ll.lat.toFixed(6);s.lo=+ll.lng.toFixed(6);if(park&&!s.n)s.n='My pin';if(!park&&/^Pin (near|at) /.test(s.n||'')){const np=nearPark(s.la,s.lo);s.n=np?(np.m<.15?'Pin at ':'Pin near ')+np.p.n:s.n}saveRove();renderRove()})})}
/* a tap within ~28 px of a parking or entrance marker snaps onto it and takes its name */
function snapTo(cp){const X=window.kpcExtras;if(!X||!cp)return null;const st=X.state();let best=null;
 for(const p of X.points()){const pk=/parking|pulloff/.test(p.kind);if(pk?!st.P:!st.E)continue;const q=map.latLngToContainerPoint([p.la,p.lo]),dd=Math.hypot(q.x-cp.x,q.y-cp.y);if(dd<28&&(!best||dd<best.dd))best=Object.assign({dd},p)}
 if(best&&!best.name)best.name=({parking:'Parking area',pulloff:'Roadside pull-off',trailhead:'Trailhead',gate:'Gate',boat:'Boat access',entrance:'Entrance'})[best.kind]||'Access point';
 return best}
function addMode(on){roveAdding=on;const w=$('map');if(!w)return;w.classList.toggle('cmd-dropping',on);
 if(map&&map.doubleClickZoom){if(on)map.doubleClickZoom.disable();else map.doubleClickZoom.enable()}   // quick taps add pins instead of zooming
 let bn=document.getElementById('roveBanner');
 if(on&&!bn&&map){bn=document.createElement('div');bn.id='roveBanner';bn.className='rove-banner';map.getContainer().append(bn);if(window.L)L.DomEvent.disableClickPropagation(bn);
  bn.addEventListener('click',e=>{if(e.target.closest('button'))addMode(false)})}
 if(bn){bn.hidden=!on;bn.innerHTML='Tap the map to add stops. <button type="button">✓ Done</button>'}
 const mb=document.querySelector('.mapbar .rovebtn');if(mb){mb.setAttribute('aria-pressed',String(on));mb.textContent=on?'✓ Done adding':'📍 Add pins'}
 if(on){status.textContent='Tap the map to add stops. Zoom in close and use Satellite + Roads to find lots and pull-offs. With 🅿️ Parking on, a tap near a lot snaps to it.';if(!document.querySelector('.kpc-mapfull'))w.scrollIntoView({block:'center',behavior:'smooth'})}
 renderRove()}
document.addEventListener('click',e=>{const b=e.target.closest('[data-rv]');if(!b)return;const id=b.dataset.id,a=b.dataset.rv;
 if(a==='rm'){map&&map.closePopup();removeStop(id)}else if(a==='up')moveStop(id,-1);else if(a==='dn')moveStop(id,1);
 else if(a==='show'){const s=rove.find(x=>x.id===id),p=s&&ptOf(s);if(p&&map){$('map').scrollIntoView({block:'center',behavior:'smooth'});map.setView([p.la,p.lo],Math.max(map.getZoom(),15));const mk=roveLay&&roveLay.getLayers().find(l=>l.options&&l.options.title&&l.getLatLng&&Math.abs(l.getLatLng().lat-p.la)<1e-6&&Math.abs(l.getLatLng().lng-p.lo)<1e-6);if(mk)setTimeout(()=>mk.openPopup(),300)}}
 else if(a==='reset'){const s=rove.find(x=>x.id===id);if(s){s.la=null;s.lo=null;s.n='';saveRove();renderRove()}}
 else if(a==='add')addMode(!roveAdding);
 else if(a==='gps'){if(!navigator.geolocation){status.textContent='Location is not available in this browser.';return}status.textContent='Finding your location…';
  navigator.geolocation.getCurrentPosition(p=>{addPin(p.coords.latitude,p.coords.longitude,'My location');status.textContent='Your location was added as stop '+rove.length+'. Move it up to make it the start.'},()=>{status.textContent='Could not get your location. Tap 📍 Add pins and tap the map instead.'},{enableHighAccuracy:true,timeout:15000})}
 else if(a==='order')nearestOrder();
 else if(a==='gpx'){const bl=new Blob([gpx()],{type:'application/gpx+xml'}),l=document.createElement('a');l.href=URL.createObjectURL(bl);l.download='kpc-rove.gpx';document.body.append(l);l.click();setTimeout(()=>{URL.revokeObjectURL(l.href);l.remove()},500)}
 else if(a==='share'){const u=shareUrl();(async()=>{try{if(navigator.share){await navigator.share({title:'KPC rove',text:'My KPC rove ('+stops().length+' stops)',url:u});return}}catch(er){if(er&&er.name==='AbortError')return}
  try{await navigator.clipboard.writeText(u);status.textContent='Rove link copied. Paste it in a text or email.'}catch(_){prompt('Copy this rove link:',u)}})()}});
document.addEventListener('input',e=>{const i=e.target.closest('.rv-in');if(!i)return;const s=rove.find(x=>x.id===i.dataset.id);if(s){s.n=i.value;saveRove();if(roveLay)drawRovePins()}});
document.addEventListener('change',e=>{if(e.target.id==='roveFirst'){roveOpt.first=e.target.checked;try{localStorage.setItem(ROVEOPT,JSON.stringify(roveOpt))}catch(_){}renderRove()}});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&roveAdding)addMode(false)});
$('clearplan').addEventListener('click',()=>{rove=[];saveRove();renderRove()});
if(map&&window.L){
 /* catch the tap before park outlines, pins or overlap areas can open their own popups */
 map.getContainer().addEventListener('click',e=>{if(!roveAdding)return;if(e.target.closest&&e.target.closest('.leaflet-control,.leaflet-popup,.rove-banner,.leaflet-marker-icon'))return;if(map.dragging&&map.dragging.moved&&map.dragging.moved())return;
  e.stopPropagation();e.preventDefault();let ll=map.mouseEventToLatLng(e);const sn=snapTo(map.mouseEventToContainerPoint(e));if(sn)ll=L.latLng(sn.la,sn.lo);map.closePopup();
  addPin(ll.lat,ll.lng,sn?sn.name+(sn.osm?' (OpenStreetMap)':''):'');status.textContent='Stop '+rove.length+' added. Keep tapping to add more, or tap ✓ Done.';
  const bn=document.getElementById('roveBanner');if(bn)bn.innerHTML=`Stop ${rove.length} added. Tap to add more. <button type="button">✓ Done</button>`},true);
 /* 📍 Add pins button in the map toolbar too (handy in full screen) */
 const bar=document.querySelector('.mapbar');if(bar){const rb=document.createElement('button');rb.type='button';rb.className='secondary tiny rovebtn';rb.textContent='📍 Add pins';rb.title='Drop your own stops on the map';rb.setAttribute('aria-pressed','false');
  rb.addEventListener('click',ev=>{ev.stopPropagation();addMode(!roveAdding)});const fs=bar.querySelector('.mapfs');(fs||bar.lastChild).after(rb)}
 const st=document.createElement('style');st.textContent='.rovelist{list-style:none;margin:6px 0 10px;padding:0}.rovelist li{display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-top:1px solid #2a2418}.rovelist li:first-child{border-top:0}.rv-n{flex:0 0 26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font:900 12px Arial;color:#fff;background:#1d5a3a;margin-top:2px}.rv-pin .rv-n{background:#2456a6}.rv-b{flex:1 1 auto;min-width:0}.rv-t{font-size:14px;font-weight:700}.rv-s{font-size:12px;color:#c9c5bc;margin-top:2px;overflow-wrap:anywhere}.rv-hint{color:#9b968a}.rv-in{width:100%;box-sizing:border-box;font:700 14px Arial;padding:5px 7px;border-radius:6px;border:1px solid #5a4a2a;background:#100f0c;color:#f2ead8}.rv-m{display:flex;gap:4px;flex:0 0 auto}.rv-m button{min-width:30px;height:30px;border-radius:6px;border:1px solid #5a4a2a;background:#1b1914;color:#f2ead8;cursor:pointer;font-size:13px}.rv-m button:disabled{opacity:.35}.linkbtn{background:none;border:0;padding:0;color:#e5c87b;text-decoration:underline;cursor:pointer;font:inherit}.rove-tools{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}.rove-first{display:flex;gap:8px;align-items:center;font-size:13px;margin:8px 0;cursor:pointer}.rove-first input{width:18px;height:18px;accent-color:#d5a63a;flex:0 0 auto}.rove-legs{display:flex;flex-direction:column;gap:8px;margin:8px 0}.rove-legs .routebtn{display:block}.endpin{display:flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);color:#fff;font:900 13px Arial;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.5);line-height:1}.endpin{}.cmd-dropping{cursor:crosshair!important;outline:3px solid #d5a63a;outline-offset:-3px}.rove-banner{position:absolute;left:50%;top:10px;transform:translateX(-50%);z-index:1200;background:#151515;color:#fff;border:1px solid #d5a63a;border-radius:999px;padding:7px 8px 7px 14px;font:800 13px Arial;max-width:92%;text-align:center;white-space:nowrap}.rove-banner button{margin-left:8px;border:0;border-radius:999px;padding:6px 12px;background:#d5a63a;color:#111;font-weight:900;cursor:pointer}.mapbar .rovebtn[aria-pressed=true]{background:#d5a63a;color:#111}@media(max-width:600px){.rove-banner{white-space:normal;font-size:12px}.rovelist li{flex-wrap:wrap}.rv-b{flex:1 1 calc(100% - 40px)}.rv-m{flex:1 1 100%;padding-left:36px;gap:8px}.rv-m button{min-width:44px;height:36px}}';
 document.head.appendChild(st)}
readShared();

/* Park Overlaps button next to the map size buttons (same switch as the map panel) */
(function(){const bar=document.querySelector('.mapbar'),X=window.kpcExtras;if(!bar||!X)return;
 const b=document.createElement('button');b.type='button';b.className='secondary tiny ovlbtn';b.textContent='◆ Park Overlaps';b.title='Highlight possible POTA 2-fers and other program overlaps';
 const sync=()=>{b.setAttribute('aria-pressed',String(X.overlapsOn()))};
 b.addEventListener('click',e=>{e.stopPropagation();X.setOverlaps(!X.overlapsOn());sync();status.textContent=X.overlapsOn()?'Park Overlaps on: gold = possible POTA 2-fer, purple = other program overlap. Tap an area for details.':'Park Overlaps off.'});
 X.onChange(sync);sync();const fs=bar.querySelector('.mapfs');(fs||bar.lastChild).after(b)})();
drawSaved();
