/* KPC Trip Planner — v20261010l
   Close-up map (zoom 19, satellite + roads), official boundaries and trails,
   drop-a-pin spots with an inside-boundary check, and a reorderable trip
   that opens in Google Maps, shares as a link, and downloads as GPX.
   Boundaries are state/federal GIS outlines — they usually match POTA but not always. */
'use strict';
(() => {
const $ = id => document.getElementById(id);
const esc = s => KPC.esc(s);
const MAXSTOPS = 10;               // Google Maps: destination + 9 waypoints
const TRIPKEY = 'kpcTripV1';
const ICON = {pota:'#1d5a3a', sota:'#b5452b', kff:'#2b5f8a', multi:'#d5a63a'};
let D, map, layer, tripLayer, V0, origin = null, ALL = null, res = [];
let on = {pota:1, sota:1, kff:1, two:0};
let trip = [];                     // {id,t:'park'|'spot',ref,k,n,la,lo,note}
let adding = false, bReady = false;
let X = null, OVX = null;           // map extras (parking/entrances/overlaps) and the overlap index by reference

/* ---------------- boundaries & trails ---------------- */
const B = {
 bstate:{name:'State parks', file:'ky-state-parks.geojson', color:'#2fa84f'},
 bwma:{name:'WMAs & public hunting areas', file:'ky-hunting-areas.geojson', color:'#f08a1c', note:'Public hunting land: check season dates and wear blaze orange during gun seasons.'},
 bsnp:{name:'State nature preserves', file:'ky-nature-preserves.geojson', color:'#a25ee0'},
 bsna:{name:'State natural areas', file:'ky-natural-areas.geojson', color:'#e2559f'},
 bdbnf:{name:'Daniel Boone National Forest', file:'ky-dbnf.geojson', color:'#2f7fd6', note:'This is the outer forest boundary. It includes private land and towns, so check land ownership on the Forest Service map.'},
 bnps:{name:'National Park Service', file:'ky-nps.geojson', color:'#9b6a3c'},
 bwild:{name:'Wild river corridors', file:'ky-wild-rivers.geojson', color:'#16b3c0', note:'Much of the land along wild rivers is private. Check access first.'},
 bwilder:{name:'Wilderness areas', file:'ky-wilderness.geojson', color:'#c6e03a', note:'Designated wilderness: no motorized equipment, and group size limits apply.'}
};
const NPSQ = '?where=1%3D1&geometry=-89.6%2C36.4%2C-81.9%2C39.2&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&geometryPrecision=5&f=geojson';
const T = {
 sheltowee:{name:'Sheltowee Trace', file:'ky-sheltowee.geojson', color:'#6cdb97', ref:'US-11181'},
 pine:{name:'Pine Mountain State Trail', file:'ky-pine-mountain.geojson', color:'#ffc36b', ref:'US-10102'},
 dawkins:{name:'Dawkins Line Rail Trail', file:'ky-dawkins.geojson', color:'#c7a5ff', ref:'US-1253'},
 tears:{name:'Trail of Tears (NPS)', url:'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/TRTE_NHT/FeatureServer/0/query'+NPSQ, color:'#ef8a98', ref:'US-3791'},
 lewis:{name:'Lewis & Clark (NPS)', url:'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/Lewis_and_Clark_National_Historic_Trail_Congressionally_Designated_Route/FeatureServer/0/query'+NPSQ, color:'#5bd5ec', ref:'US-4572'}
};
const ALIAS = {"Clifty Wilderness":["US-3801"],"Big South Fork National River and Recreation Area":["US-0686"],"Bad Branch Wild River":["US-10112"],"Big South Fork Wild River":["US-10107"],"Cumberland River Wild River":["US-10103"],"Green River Wild River":["US-10105"],"Rock Creek Wild River":["US-10111"],"Red River Wild River":["US-10104"],"Rockcastle River Wild River":["US-10106"],"Little South Fork Wild River":["US-7962"],"Mammoth Cave National Park":["US-0050"],"Abraham Lincoln Birthplace National Historical Park":["US-0724"],"Camp Nelson National Monument":["US-7950"],"Mill Springs Battlefield National Monument":["US-7708"],"Cumberland Gap National Historical Park":["US-0019"],"Fort Donelson National Battlefield":["US-0703","US-3790"],"Jefferson National Forest":["US-4526"],"Pine Mountain State Scenic Trail":["US-10102"],"Daniel Boone National Forest":["US-4484"]};
const bData = {}, bLay = {}, tData = {};
const norm = s => String(s||'').toLowerCase().replace(/wildlife management area|state nature preserve|state natural area|state resort park|state historic site|state park|national forest|wma|snp|sna|the |[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();
const ringsOf = g => !g ? [] : g.type==='Polygon' ? [g.coordinates] : g.type==='MultiPolygon' ? g.coordinates : [];
const linesOf = g => !g ? [] : g.type==='LineString' ? [g.coordinates] : g.type==='MultiLineString' ? g.coordinates : [];
function inRing(x,y,r){let s=false;for(let i=0,j=r.length-1;i<r.length;j=i++){const xi=r[i][0],yi=r[i][1],xj=r[j][0],yj=r[j][1];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi+1e-15)+xi)s=!s}return s}
function inside(lat,lon,g){for(const p of ringsOf(g)){if(!p.length||!inRing(lon,lat,p[0]))continue;if(p.slice(1).some(h=>inRing(lon,lat,h)))continue;return true}return false}
function segKm(lat,lon,pts){let best=Infinity;const sx=111.195*Math.cos(lat*Math.PI/180),sy=111.195;for(let i=1;i<pts.length;i++){const a=pts[i-1],b=pts[i],dx=(b[0]-a[0])*sx,dy=(b[1]-a[1])*sy,x=(lon-a[0])*sx,y=(lat-a[1])*sy,t=Math.max(0,Math.min(1,(x*dx+y*dy)/((dx*dx+dy*dy)||1)));best=Math.min(best,Math.hypot(x-t*dx,y-t*dy))}return best}
function edgeKm(lat,lon,g){let b=Infinity;for(const p of ringsOf(g))for(const r of p)b=Math.min(b,segKm(lat,lon,r));for(const l of linesOf(g))b=Math.min(b,segKm(lat,lon,l));return b}
function bbox(g){let a=[180,90,-180,-90];const add=([x,y])=>{if(x<a[0])a[0]=x;if(y<a[1])a[1]=y;if(x>a[2])a[2]=x;if(y>a[3])a[3]=y};for(const p of ringsOf(g))for(const r of p)r.forEach(add);for(const l of linesOf(g))l.forEach(add);return a}
const fmtMi = km => {const m=km*0.621371;return m<0.1?Math.round(m*5280)+' ft':m.toFixed(m<10?1:0)+' mi'};
const fName = f => (f.properties&&(f.properties.NAME||f.properties.Name||f.properties.name||f.properties.UNIT_NAME||f.properties.TRAIL_NAME))||'';
function potaFor(f){ // POTA parks matched to a boundary: alias, reference point inside, or name match
 if(f._pota)return f._pota;const nm=norm(fName(f)),b=f._bb||(f._bb=bbox(f.geometry)),out=new Map();
 (ALIAS[fName(f)]||[]).forEach(r=>{const p=D.parks.find(x=>x.c===r);if(p)out.set(r,p)});
 for(const p of D.parks){if(out.has(p.c))continue;
  if(p.lo>=b[0]-.02&&p.lo<=b[2]+.02&&p.la>=b[1]-.02&&p.la<=b[3]+.02&&inside(p.la,p.lo,f.geometry)){out.set(p.c,p);continue}
  const dn=norm(p.n);if(nm.length>4&&dn&&p.lo>=b[0]-.5&&p.lo<=b[2]+.5&&p.la>=b[1]-.5&&p.la<=b[3]+.5){const sh=dn.length<nm.length?dn:nm,lg=dn.length<nm.length?nm:dn;if(dn===nm||(sh.length>6&&lg.startsWith(sh)&&sh.length/lg.length>=.7))out.set(p.c,p)}}
 return (f._pota=[...out.values()])}
const refTxt = ps => ps.length ? ps.slice(0,4).map(p=>p.c).join(', ')+(ps.length>4?' +'+(ps.length-4):'') : '';

/* where is a point? inside which boundaries, near which trails */
function whereIs(lat,lon){
 const hits=[],trails=[];let near=null;
 for(const k of Object.keys(bData)){for(const f of bData[k].features){const b=f._bb||(f._bb=bbox(f.geometry));
  const rough=Math.max(0,(b[0]-lon)*89,(lon-b[2])*89,(b[1]-lat)*111,(lat-b[3])*111);if(rough>40)continue;
  if(inside(lat,lon,f.geometry))hits.push({k,f,name:fName(f)||B[k].name,refs:potaFor(f)});
  else{const d=edgeKm(lat,lon,f.geometry);if(!near||d<near.d)near={k,f,d,name:fName(f)||B[k].name,refs:potaFor(f)}}}}
 for(const k of Object.keys(tData)){let best=Infinity;for(const f of tData[k].features){const b=f._bb||(f._bb=bbox(f.geometry));
  if(Math.max(0,(b[0]-lon)*89,(lon-b[2])*89,(b[1]-lat)*111,(lat-b[3])*111)>1)continue;best=Math.min(best,edgeKm(lat,lon,f.geometry))}
  if(best<0.4)trails.push({k,name:T[k].name,ref:T[k].ref,d:best})}
 hits.sort((a,b)=>(b.refs.length>0)-(a.refs.length>0)||(a.k==='bdbnf')-(b.k==='bdbnf'));
 return {hits,near,trails}}
function whereHtml(w){
 if(!bReady)return '<span class="pw-muted">Loading boundaries… the check appears in a moment.</span>';
 let h='';
 if(w.hits.length)h+=w.hits.slice(0,4).map(x=>`<div class="pw-in">✓ Inside <b>${esc(x.name)}</b>${x.refs.length?` · POTA <b>${esc(refTxt(x.refs))}</b>`:' · <i>no POTA ref matched</i>'}</div>${B[x.k].note?`<div class="pw-note">${esc(B[x.k].note)}</div>`:''}`).join('');
 else if(w.near)h+=`<div class="pw-out">✗ Not inside a mapped boundary. Nearest: <b>${esc(w.near.name)}</b>${w.near.refs.length?` (${esc(refTxt(w.near.refs))})`:''}, ${fmtMi(w.near.d)} away.</div>`;
 else h+='<div class="pw-out">✗ Not inside a mapped boundary.</div>';
 if(w.trails.length)h+=w.trails.map(t=>`<div class="pw-in">🥾 ${t.d<0.03?'On':'Near'} <b>${esc(t.name)}</b> · POTA <b>${t.ref}</b> · ${fmtMi(t.d)} from the trail</div>`).join('');
 return h+'<div class="pw-muted">Map outlines can differ from POTA’s boundary, so confirm on the POTA map.</div>'}

const bRend = () => L.canvas({pane:'bndp', padding:.4, tolerance:6});
let canvasR=null;
async function loadBoundaries(){
 const stat=$('lyrStat');let n=0;const keys=Object.keys(B);
 await Promise.all(keys.map(async k=>{try{const r=await fetch(B[k].file,{cache:'force-cache'});if(!r.ok)throw 0;const j=await r.json();j.features=(j.features||[]).filter(f=>f.geometry&&ringsOf(f.geometry).length);bData[k]=j;drawB(k)}catch(e){}if(stat)stat.textContent=`Loading boundaries… ${++n} of ${keys.length}`}));
 const tk=Object.keys(T);await Promise.all(tk.map(async k=>{try{const r=await fetch(T[k].file||T[k].url,T[k].file?{cache:'force-cache'}:{});if(!r.ok)throw 0;const j=await r.json();if(!Array.isArray(j.features))throw 0;j.features=j.features.filter(f=>f.geometry&&linesOf(f.geometry).length);tData[k]=j;drawT(k)}catch(e){}}));
 bReady=true;if(stat)stat.textContent=`${Object.keys(bData).length} boundary layers and ${Object.keys(tData).length} trails loaded.`;
 tripLayer.eachLayer(m=>{if(m._stop&&m.isPopupOpen&&m.isPopupOpen())m.setPopupContent(spotPopup(m._stop))});renderTrip()}
function shown(k){try{const o=JSON.parse(localStorage.getItem('kpcPlanLayers')||'{}');return o[k]!==false}catch(e){return true}}
function setShown(k,v){try{const o=JSON.parse(localStorage.getItem('kpcPlanLayers')||'{}');o[k]=v;localStorage.setItem('kpcPlanLayers',JSON.stringify(o))}catch(e){}}
function drawB(k){const s=B[k];canvasR=canvasR||bRend();
 bLay[k]=L.geoJSON(bData[k],{renderer:canvasR,pane:'bndp',style:f=>{const has=potaFor(f).length>0;return{color:s.color,weight:has?3:2,opacity:.95,dashArray:has?null:'6 5',fillColor:s.color,fillOpacity:k==='bdbnf'?.05:(has?.18:.08)}},
  onEachFeature:(f,l)=>{l.on('click',e=>{if(adding)return;L.popup({maxWidth:290}).setLatLng(e.latlng).setContent(bPopup(f,s,e.latlng)).openOn(map)})}});
 if(shown(k))bLay[k].addTo(map);order()}
function drawT(k){const s=T[k];
 const under=L.geoJSON(tData[k],{pane:'trlp',interactive:false,style:{color:'#111',weight:7,opacity:.35}});
 const top=L.geoJSON(tData[k],{pane:'trlp',style:{color:s.color,weight:4,opacity:1},onEachFeature:(f,l)=>l.on('click',e=>{if(adding)return;L.popup({maxWidth:280}).setLatLng(e.latlng).setContent(`<b>${esc(s.name)}</b><br>POTA <a href="${KPC.links.pota(s.ref)}" target="_blank" rel="noopener">${s.ref}</a><div style="margin-top:8px"><button type="button" class="btn sm" data-drop="${e.latlng.lat},${e.latlng.lng}">📍 ADD A SPOT HERE</button></div>`).openOn(map)})});
 bLay['t_'+k]=L.layerGroup([under,top]);if(shown('t_'+k))bLay['t_'+k].addTo(map)}
function order(){if(bLay.bdbnf&&map.hasLayer(bLay.bdbnf))bLay.bdbnf.bringToBack()}
function bPopup(f,s,ll){const p=f.properties||{},refs=potaFor(f);
 return `<b>${esc(fName(f)||s.name)}</b><div style="font-size:12px;color:#555">${esc(p.TYPE||s.name)}${p.ACCESS?' · access: '+esc(p.ACCESS):''}</div>`+
 (refs.length?`<div style="margin-top:6px"><b>POTA:</b> ${refs.slice(0,5).map(r=>`<a href="${KPC.links.pota(r.c)}" target="_blank" rel="noopener">${r.c}</a> ${esc(r.n)}`).join('<br>')}</div>`:'<div style="margin-top:6px">No POTA reference matched to this outline.</div>')+
 (s.note?`<div style="margin-top:6px;font-size:12px;font-weight:700">⚠ ${esc(s.note)}</div>`:'')+(p.URL?`<div style="margin-top:6px"><a href="${esc(p.URL)}" target="_blank" rel="noopener">Official page ↗</a></div>`:'')+
 `<div style="margin-top:8px"><button type="button" class="btn sm" data-drop="${ll.lat},${ll.lng}">📍 ADD A SPOT HERE</button></div>`}

/* ---------------- map ---------------- */
function makeMap(){
 const m=L.map('map',{scrollWheelZoom:true,maxZoom:19,tapHold:true,zoomControl:true}).setView([37.75,-85.7],7);
 const esri=p=>`https://server.arcgisonline.com/ArcGIS/rest/services/${p}/MapServer/tile/{z}/{y}/{x}`,EA='Imagery © Esri, Maxar, Earthstar Geographics';
 const base={
  'Road Map':L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}),
  'Satellite + Roads':L.layerGroup([L.tileLayer(esri('World_Imagery'),{maxZoom:19,attribution:EA}),L.tileLayer(esri('Reference/World_Transportation'),{maxZoom:19}),L.tileLayer(esri('Reference/World_Boundaries_and_Places'),{maxZoom:19})]),
  'Satellite':L.tileLayer(esri('World_Imagery'),{maxZoom:19,attribution:EA}),
  'Terrain':L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxNativeZoom:17,maxZoom:19,attribution:'© OpenTopoMap (CC-BY-SA), © OpenStreetMap contributors'})};
 let want='Road Map';try{want=localStorage.getItem('kpcPlanBase')||'Road Map'}catch(e){}
 want={'Street':'Road Map','Satellite + roads':'Satellite + Roads'}[want]||want;
 (base[want]||base['Road Map']).addTo(m);L.control.layers(base,null,{position:'topright',collapsed:true}).addTo(m);
 m.on('baselayerchange',e=>{try{localStorage.setItem('kpcPlanBase',e.name)}catch(_){}});
 L.control.scale({imperial:true,metric:false,position:'bottomleft'}).addTo(m);
 m.createPane('bndp').style.zIndex=350;m.createPane('trlp').style.zIndex=380;
 // full-screen + add-spot buttons
 const Btns=L.Control.extend({options:{position:'topleft'},onAdd(){const d=L.DomUtil.create('div','leaflet-bar pl-ctl');
  d.innerHTML='<a href="#" role="button" id="plFull" title="Full-screen map" aria-label="Full-screen map">⛶</a><a href="#" role="button" id="plPin" title="Add a spot" aria-label="Add a spot">📍</a>';
  L.DomEvent.disableClickPropagation(d);L.DomEvent.on(d,'click',e=>{L.DomEvent.preventDefault(e);const a=e.target.closest('a');if(!a)return;if(a.id==='plFull')full();if(a.id==='plPin')addMode(!adding)});return d}});
 new Btns().addTo(m);
 // boundary layer picker
 const Lyr=L.Control.extend({options:{position:'topright'},onAdd(){const d=L.DomUtil.create('div','pl-lyr');
  d.innerHTML='<button type="button" class="pl-lyrbtn" aria-expanded="false">Boundaries ▾</button><div class="pl-lyrbox" hidden>'+
   Object.entries(B).map(([k,s])=>`<label><input type="checkbox" data-l="${k}" ${shown(k)?'checked':''}><i style="background:${s.color}"></i>${esc(s.name)}</label>`).join('')+
   '<div class="pl-lyrh">Trails (POTA)</div>'+Object.entries(T).map(([k,s])=>`<label><input type="checkbox" data-l="t_${k}" ${shown('t_'+k)?'checked':''}><i style="background:${s.color}"></i>${esc(s.name)}</label>`).join('')+
   '<div class="pl-lyrh" style="font-weight:400">Solid outline = matched to a POTA park. Dashed = no POTA reference found.</div><div id="lyrStat" class="pl-lyrh" style="font-weight:400">Loading boundaries…</div></div>';
  L.DomEvent.disableClickPropagation(d);L.DomEvent.disableScrollPropagation(d);
  const btn=d.querySelector('.pl-lyrbtn'),box=d.querySelector('.pl-lyrbox');
  btn.onclick=()=>{box.hidden=!box.hidden;btn.setAttribute('aria-expanded',String(!box.hidden))};
  d.addEventListener('change',e=>{const k=e.target.dataset.l;if(!k)return;setShown(k,e.target.checked);const l=bLay[k];if(!l)return;e.target.checked?l.addTo(map):map.removeLayer(l);order()});return d}});
 new Lyr().addTo(m);
 // parking & entrance markers + Park Overlaps (shared with KY Park Commander)
 if(window.KPCX){X=KPCX.attach(m,{key:'plan',addStop:true,parks:D.parks,busy:()=>adding});
  X.onChange(s=>{if(!!s.O!==!!on.two){on.two=s.O?1:0;const b=document.querySelector('#prog_ [data-k=two]');if(b)b.setAttribute('aria-pressed',String(!!on.two));if(origin)run(false)}});
  on.two=X.overlapsOn()?1:0;
  KPCX.overlapIndex().then(ix=>{OVX=ix;ALL=null;if(origin)run(false)}).catch(()=>{})}
 m.on('popupopen',()=>$('mapwrap').classList.add('pl-popopen'));m.on('popupclose',()=>$('mapwrap').classList.remove('pl-popopen'));
 m.on('click',e=>{if(adding){addSpot(e.latlng);addMode(false)}});
 m.on('contextmenu',e=>{addSpot(e.latlng);addMode(false)}); // long-press on phones, right-click on desktop
 return m}
function full(force){const w=$('mapwrap');const onNow=typeof force==='boolean'?force:!w.classList.contains('pl-full');w.classList.toggle('pl-full',onNow);document.documentElement.classList.toggle('pl-noscroll',onNow);
 const b=$('plFull');if(b){b.textContent=onNow?'✕':'⛶';b.title=onNow?'Close full screen':'Full-screen map'}setTimeout(()=>map.invalidateSize(),60)}
document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(adding)addMode(false);else if($('mapwrap').classList.contains('pl-full'))full(false)}});
function addMode(v){adding=v;$('mapwrap').classList.toggle('pl-adding',v);$('addSpot').setAttribute('aria-pressed',String(v));$('addSpot').textContent=v?'✕ CANCEL ADDING':'📍 ADD A SPOT';const b=$('plPin');if(b)b.classList.toggle('on',v);if(v)map.closePopup()}

/* ---------------- trip ---------------- */
const uid = () => Math.random().toString(36).slice(2,9);
function save(){try{localStorage.setItem(TRIPKEY,JSON.stringify({o:origin,s:trip}))}catch(e){}}
function stopDest(s){return [s.la,s.lo]}
function canAdd(){if(trip.length>=MAXSTOPS){alert('Google Maps directions allow up to '+MAXSTOPS+' stops. Remove one to add another.');return false}return true}
function addPark(x){if(trip.some(s=>s.ref===x.ref))return;if(!canAdd())return;trip.push({id:uid(),t:'park',ref:x.ref,k:x.k,n:x.n,la:x.dest[0],lo:x.dest[1],note:x.dn||''});changed()}
function removeStop(id){trip=trip.filter(s=>s.id!==id);changed()}
function spotName(w){if(w.trails.length&&!w.hits.length)return 'Spot on '+w.trails[0].name;if(w.hits.length)return 'Spot at '+w.hits[0].name;
 let best=null;if(D)for(const p of D.parks){const d=KPC.miles(lastLL.lat,lastLL.lng,p.la,p.lo);if(!best||d<best.d)best={p,d}}return best?'Spot near '+best.p.n:'My spot'}
let lastLL=null;
function addSpot(ll){if(!canAdd())return;lastLL=ll;const w=whereIs(ll.lat,ll.lng);
 const s={id:uid(),t:'spot',n:bReady?spotName(w):'My spot '+(trip.filter(x=>x.t==='spot').length+1),la:+ll.lat.toFixed(6),lo:+ll.lng.toFixed(6),note:''};
 trip.push(s);changed();const m=tripLayer.getLayers().find(x=>x._stop&&x._stop.id===s.id);if(m)m.openPopup()}
function spotPopup(s){const d=L.DomUtil.create('div','pl-pop');const w=whereIs(s.la,s.lo);
 d.innerHTML=`<label class="pl-f">Name<input type="text" maxlength="60" value="${esc(s.n)}" data-f="n"></label><label class="pl-f">Note (parking, gate, surface…)<input type="text" maxlength="120" value="${esc(s.note||'')}" data-f="note" placeholder="Gravel pull-off, room for 2 cars"></label>
 <div class="pl-where">${whereHtml(w)}</div><div class="pl-ll">${s.la.toFixed(5)}, ${s.lo.toFixed(5)} · drag the pin to fine-tune</div>
 <div class="pl-pacts"><a class="btn sm" href="https://www.google.com/maps/search/?api=1&query=${s.la},${s.lo}" target="_blank" rel="noopener">GOOGLE MAPS</a><button type="button" class="btn sm alt" data-rm="${s.id}">REMOVE</button></div>`;
 L.DomEvent.disableClickPropagation(d);
 d.addEventListener('input',e=>{const f=e.target.dataset.f;if(!f)return;s[f]=e.target.value;save();renderTripList()});
 return d}
function parkPopup(s){return `<b>${esc(s.n)}</b><br>${s.ref}${s.note?'<br>Parking: '+esc(s.note):''}<div class="pl-pacts" style="margin-top:8px"><button type="button" class="btn sm alt" data-info="${esc(s.ref)}">DETAILS</button><a class="btn sm" href="${KPC.links.pota(s.ref)}" target="_blank" rel="noopener">POTA</a><button type="button" class="btn sm alt" data-rm="${s.id}">REMOVE FROM TRIP</button></div>`}
function drawTrip(){tripLayer.clearLayers();
 trip.forEach((s,i)=>{const spot=s.t==='spot';
  const icon=L.divIcon({className:'pl-pin'+(spot?' spot':''),html:`<span><b>${i+1}</b></span>`,iconSize:[34,34],iconAnchor:[17,41],popupAnchor:[0,-38]});
  const m=L.marker([s.la,s.lo],{icon,draggable:spot,autoPan:true,zIndexOffset:1000,title:`${i+1}. ${s.n}`});m._stop=s;
  if(spot){m.bindPopup(()=>spotPopup(s),{maxWidth:290,minWidth:220,autoPanPadding:[12,12]});m.on('popupopen',ev=>{const w=map.getSize().x,p=ev.popup;p.options.maxWidth=Math.max(200,Math.min(290,w-50));p.options.minWidth=Math.min(220,p.options.maxWidth);p.update()});
   m.on('dragend',()=>{const p=m.getLatLng();s.la=+p.lat.toFixed(6);s.lo=+p.lng.toFixed(6);save();renderTripList();m.setPopupContent(spotPopup(s));m.openPopup()})}
  else m.bindPopup(parkPopup(s),{maxWidth:280});
  if(window.KPCX)KPCX.hover(m);
  m.addTo(tripLayer)});
 if(trip.length>1)L.polyline(trip.map(s=>[s.la,s.lo]),{color:'#d5a63a',weight:3,opacity:.85,dashArray:'2 8',interactive:false}).addTo(tripLayer)}
function renderTripList(){const ol=$('trip');$('tripN').textContent=trip.length+(trip.length===1?' stop':' stops');
 ['route','share','gpx','sortd','clear'].forEach(id=>$(id).disabled=!trip.length);
 if(!trip.length){ol.innerHTML='<li class="pl-empty">No stops yet. Tick parks in the list, tap <b>+ Add to trip</b> on a map pin, or use <b>📍 Add a spot</b> to drop your own spot.</li>';return}
 ol.innerHTML=trip.map((s,i)=>{let sub='';
  if(s.t==='park')sub=`<span class="tag">${(s.k||'pota').toUpperCase()}</span> ${s.ref}`;
  else{const w=bReady?whereIs(s.la,s.lo):null;sub='<span class="tag g">MY SPOT</span> '+(w?(w.hits.length?'Inside '+esc(w.hits[0].name)+(w.hits[0].refs.length?' · '+esc(refTxt(w.hits[0].refs)):''):w.trails.length?'On '+esc(w.trails[0].name)+' · '+w.trails[0].ref:'Not inside a mapped boundary'):'')}
  return `<li data-id="${s.id}"><span class="pl-num${s.t==='spot'?' spot':''}">${i+1}</span><div class="pl-ti"><button type="button" class="pl-go" data-go="${s.id}">${esc(s.n)}</button><div class="pl-sub">${sub}</div>${s.note?`<div class="pl-sub">${esc(s.note)}</div>`:''}</div>
  <div class="pl-mv"><button type="button" data-up="${s.id}" aria-label="Move up" ${i?'':'disabled'}>▲</button><button type="button" data-dn="${s.id}" aria-label="Move down" ${i<trip.length-1?'':'disabled'}>▼</button><button type="button" data-rm="${s.id}" aria-label="Remove">✕</button></div></li>`}).join('')}
function renderTrip(){drawTrip();renderTripList();syncChecks();if(typeof refreshInfo==='function'&&D)refreshInfo()}
function changed(){save();renderTrip()}
function syncChecks(){document.querySelectorAll('#list input[type=checkbox]').forEach(cb=>{const x=res[+cb.dataset.i];if(x)cb.checked=trip.some(s=>s.ref===x.ref)})}
function move(id,d){const i=trip.findIndex(s=>s.id===id),j=i+d;if(i<0||j<0||j>=trip.length)return;[trip[i],trip[j]]=[trip[j],trip[i]];changed()}
document.addEventListener('click',e=>{const t=e.target.closest('[data-up],[data-dn],[data-rm],[data-go],[data-add],[data-drop]');if(!t)return;
 if(t.dataset.up)move(t.dataset.up,-1);else if(t.dataset.dn)move(t.dataset.dn,1);
 else if(t.dataset.rm){map.closePopup();removeStop(t.dataset.rm)}
 else if(t.dataset.go){const s=trip.find(x=>x.id===t.dataset.go);if(!s)return;if(s.t==='park')showInfo(s.ref);map.setView([s.la,s.lo],Math.max(map.getZoom(),s.t==='spot'?17:14));const m=tripLayer.getLayers().find(x=>x._stop&&x._stop.id===s.id);if(m)setTimeout(()=>m.openPopup(),250);$('mapwrap').scrollIntoView({behavior:'smooth',block:'center'})}
 else if(t.dataset.add){const x=(ALL||[]).find(i=>i.ref===t.dataset.add);if(x){addPark(x);map.closePopup()}}
 else if(t.dataset.drop){const [a,b]=t.dataset.drop.split(',').map(Number);map.closePopup();addSpot(L.latLng(a,b))}});

/* directions, share, GPX */
function gmapsUrl(){const s=trip.map(stopDest),last=s[s.length-1],mid=s.slice(0,-1);
 return 'https://www.google.com/maps/dir/?api=1'+(origin?`&origin=${origin[0]},${origin[1]}`:'')+`&destination=${last[0]},${last[1]}`+(mid.length?'&waypoints='+mid.map(p=>p.join(',')).join('%7C'):'')+'&travelmode=driving'}
function shareUrl(){const o={o:origin,s:trip.map(s=>s.t==='park'?['p',s.ref]:['s',s.la,s.lo,s.n,s.note||''])};
 const b=btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');return location.origin+location.pathname+'?trip='+b}
function readShared(code){try{const o=JSON.parse(decodeURIComponent(escape(atob(code.replace(/-/g,'+').replace(/_/g,'/')))));const out=[];
 for(const s of o.s||[]){if(s[0]==='p'){const x=(ALL||items()).find(i=>i.ref===s[1]);if(x)out.push({id:uid(),t:'park',ref:x.ref,k:x.k,n:x.n,la:x.dest[0],lo:x.dest[1],note:x.dn||''})}
  else if(s[0]==='s'&&isFinite(s[1])&&isFinite(s[2]))out.push({id:uid(),t:'spot',la:+s[1],lo:+s[2],n:String(s[3]||'Shared spot').slice(0,60),note:String(s[4]||'').slice(0,120)})}
 return {o:Array.isArray(o.o)?o.o:null,s:out.slice(0,MAXSTOPS)}}catch(e){return null}}
function gpx(){const x=s=>String(s).replace(/[<>&"']/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;',"'":'&apos;'}[c]));
 const pts=trip.map((s,i)=>({la:s.la,lo:s.lo,n:`${i+1}. ${s.n}`,d:[s.ref,s.note].filter(Boolean).join(' · ')}));
 return `<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="Kentucky Portable Club Trip Planner" xmlns="http://www.topografix.com/GPX/1/1">\n<metadata><name>KPC trip</name><time>${new Date().toISOString()}</time></metadata>\n`+
  pts.map(p=>`<wpt lat="${p.la}" lon="${p.lo}"><name>${x(p.n)}</name>${p.d?`<desc>${x(p.d)}</desc>`:''}</wpt>`).join('\n')+
  `\n<rte><name>KPC trip</name>\n`+pts.map(p=>`<rtept lat="${p.la}" lon="${p.lo}"><name>${x(p.n)}</name></rtept>`).join('\n')+`\n</rte>\n</gpx>\n`}
function flash(msg){const n=$('tripMsg');n.textContent=msg;n.hidden=false;clearTimeout(flash.t);flash.t=setTimeout(()=>n.hidden=true,4000)}

/* ---------------- search results (unchanged behaviour) ---------------- */
/* overlap lookups (ky-overlaps.geojson). Until that file loads, only the park file's 2-fer list (tf) is used. */
function ovAnySet(){const s=new Set();if(OVX)OVX.forEach((l,r)=>{s.add(r);l.forEach(o=>{o.sota.forEach(x=>s.add(x[0]));if(o.kind!=='2fer')o.kff.forEach(x=>s.add(x[0]))})});return s}
function twoFers(p){const P=new Map(D.parks.map(q=>[q.c,q.n]));   // park file list + mapped overlaps of two POTA refs
 const out=p.tf.map(r=>[r,P.get(r)||'']);
 if(OVX)for(const o of OVX.get(p.c)||[])if(o.kind==='2fer')for(const r of o.others)if(!out.some(x=>x[0]===r[0]))out.push(r);
 return out.filter(r=>r[0]!==p.c)}
function items(){const out=[],P=new Map(D.parks.map(p=>[p.c,p])),ANY=ovAnySet();
 D.parks.forEach(p=>{const two=twoFers(p),multi=two.length||p.kff.length||p.sota.length;const dest=p.ap.length?[p.ap[0][0],p.ap[0][1]]:[p.la,p.lo];
  const also=[...p.kff,...p.sota.map(r=>'SOTA '+r)];
  out.push({k:'pota',ref:p.c,n:p.n,co:p.co,la:p.la,lo:p.lo,dest,dn:p.ap.length?p.ap[0][2]:'',multi,two,also,cls:p.t,ov:ANY.has(p.c)||two.length>0,
  tags:[...two.map(r=>`<span class="tag g">POSSIBLE 2-FER ${r[0]}</span>`),...p.kff.map(r=>`<span class="tag k">${r}</span>`),...p.sota.map(r=>`<span class="tag r">${r}</span>`)],
  links:[['POTA',KPC.links.pota(p.c)],p.off&&['OFFICIAL MAP',p.off],['WEATHER',KPC.links.wx(p.la,p.lo)]].filter(Boolean)})});
 D.summits.forEach(s=>{const inPark=D.parks.filter(p=>p.sota.includes(s.c));
  out.push({k:'sota',ref:s.c,n:s.n,co:s.co,la:s.la,lo:s.lo,dest:[s.la,s.lo],multi:inPark.length,two:[],also:inPark.map(p=>'inside POTA '+p.c+' '+p.n),cls:'SOTA summit',ov:ANY.has(s.c)||inPark.length>0,meta:`${s.ft?s.ft.toLocaleString()+' ft • ':''}${s.pts||'?'} pts`,
  tags:inPark.map(p=>`<span class="tag g">IN ${p.c}</span>`),links:[['SOTLAS',KPC.links.sota(s.c)],['WEATHER',KPC.links.wx(s.la,s.lo)]]})});
 D.kff.forEach(k=>{if(k.p&&P.has(k.p))return;out.push({k:'kff',ref:k.c,n:k.n,co:k.co,la:k.la,lo:k.lo,dest:[k.la,k.lo],multi:0,two:[],also:[],cls:'WWFF / KFF reference',ov:ANY.has(k.c),tags:[],links:[['WWFF',KPC.links.kff(k.c)]]})});
 return out}
function run(fit){ALL=ALL||items();const R=+$('rad').value;
 res=ALL.map(x=>({...x,d:KPC.miles(origin[0],origin[1],x.la,x.lo)})).filter(x=>x.d<=R&&on[x.k]&&(!on.two||x.ov)).sort((a,b)=>a.d-b.d);
 const c={pota:0,sota:0,kff:0};res.forEach(x=>c[x.k]++);
 $('where').innerHTML=`From <b>${esc(origin[2])}</b> within ${R} miles: <b>${c.pota}</b> POTA parks • <b>${c.sota}</b> summits • <b>${c.kff}</b> KFF-only references`;
 layer.clearLayers();L.circle([origin[0],origin[1]],{radius:R*1609.34,color:'#d5a63a',weight:1.5,fillOpacity:.04,interactive:false}).addTo(layer);
 L.circleMarker([origin[0],origin[1]],{radius:7,color:'#000',fillColor:'#000',fillOpacity:1}).bindPopup('Start: '+esc(origin[2])).addTo(layer);
 res.forEach(x=>{const two=x.two&&x.two.length;
  const mk=L.circleMarker([x.la,x.lo],{radius:two?8:6,weight:x.ov&&!two?2.5:1.2,color:x.ov&&!two?'#7b3fa0':'#222',fillColor:two?ICON.multi:ICON[x.k],fillOpacity:.95})
   .bindPopup(()=>pinCard(x),{maxWidth:290,minWidth:210,autoPanPadding:[12,12]});
  if(window.KPCX)KPCX.hover(mk);mk.on('click',()=>showInfo(x.ref));x.mk=mk;mk.addTo(layer)});
 if(fit!==false)map.fitBounds(L.latLng(origin[0],origin[1]).toBounds(R*1609.34*2.1));
 $('list').innerHTML=res.length?res.map((x,i)=>`<div class="item ${x.k}"><input type="checkbox" data-i="${i}" ${trip.some(s=>s.ref===x.ref)?'checked':''} aria-label="Add ${esc(x.ref)} to trip">
 <div><span class="ref">${x.ref}</span> <span class="tag">${x.k.toUpperCase()}</span><h3>${esc(x.n)}</h3><div class="meta">${esc(KPC.cty(x.co))}${x.meta?' • '+x.meta:''}${x.dn?` • parking: ${esc(x.dn)}`:''}</div>${x.tags.length?`<div>${x.tags.join('')}</div>`:''}
 <div class="acts"><button type="button" class="btn sm alt" data-zoom="${i}">SHOW ON MAP</button><a class="btn sm" href="${KPC.links.dir(x.dest[0],x.dest[1],origin)}" target="_blank" rel="noopener">DIRECTIONS</a>${x.links.map(([l,u])=>`<a class="btn sm alt" href="${u}" target="_blank" rel="noopener">${l}</a>`).join('')}</div></div>
 <div class="dist">${x.d.toFixed(1)}<small>MILES</small></div></div>`).join(''):'<div class="empty">Nothing in range. Try a bigger distance.</div>';
 $('list').querySelectorAll('input[type=checkbox]').forEach(cb=>cb.onchange=()=>{const x=res[+cb.dataset.i];if(cb.checked){if(!canAdd()){cb.checked=false;return}addPark(x)}else{trip=trip.filter(s=>s.ref!==x.ref);changed()}});
 $('list').querySelectorAll('[data-zoom]').forEach(b=>b.onclick=()=>{const x=res[+b.dataset.zoom];showInfo(x.ref);map.setView([x.la,x.lo],15);$('mapwrap').scrollIntoView({behavior:'smooth',block:'center'})})}
/* ---------------- park details box (same facts as KY Park Commander's cards) ---------------- */
function grid6(lat,lon){lat=+lat+90;lon=+lon+180;if(!(lat>=0&&lat<=180&&lon>=0&&lon<=360))return '';const A='ABCDEFGHIJKLMNOPQR',a='abcdefghijklmnopqrstuvwx';return A[Math.floor(lon/20)]+A[Math.floor(lat/10)]+Math.floor((lon%20)/2)+Math.floor(lat%10)+a[Math.floor((lon%2)*12)]+a[Math.floor((lat%1)*24)]}
function coTxt(co){if(!co||/official|see /i.test(co))return '';const l=String(co).replace(/\?/g,'').split('/').map(s=>s.trim()).filter(Boolean);return l.length>3?'Multi-county ('+l.length+' counties)':l.length>1?l.join(' / ')+' counties':l[0]+' County'}
const HOSTL=[[/parks\.ky\.gov/,'Kentucky State Parks page'],[/fw\.ky\.gov/,'KDFWR area page'],[/eec\.ky\.gov/,'Nature Preserves page'],[/nps\.gov/,'National Park Service page'],[/fs\.usda\.gov/,'Forest Service page'],[/fws\.gov/,'Fish & Wildlife Service page']];
const hostL=u=>{for(const [r,l] of HOSTL)if(r.test(u))return l;return 'Official park page'};
const TYPEN={'WMA':'Wildlife Management Area','National / NPS':'National Park Service site'};
const gdir=(a,b)=>`https://www.google.com/maps/dir/?api=1&destination=${a},${b}&travelmode=driving`;
function infoHtml(x){const P=new Map(D.parks.map(q=>[q.c,q])),p=x.k==='pota'?P.get(x.ref):null,lk=[];const L2=(l,u)=>lk.push(`<a href="${esc(u)}" target="_blank" rel="noopener">${esc(l)}</a>`);
 const line=[`Grid ${grid6(x.la,x.lo)}`,coTxt(x.co),`${(+x.la).toFixed(5)}, ${(+x.lo).toFixed(5)}`].filter(Boolean).join(' · ');
 let h=`<span class="pi-tag ${x.k}">${x.k==='pota'?'POTA':x.k==='sota'?'SOTA':'WWFF / KFF'} • ${esc(x.ref)}</span><h3>${esc(x.n)}</h3><div class="pi-m">${line}</div>`;
 if(x.k==='sota')h+=`<div class="pi-m">${esc(x.meta||'')}</div>`;
 if(x.also&&x.also.length)h+=`<div class="pi-m"><b>Also:</b> ${esc(x.also.join(' · '))}</div>`;
 if(x.two&&x.two.length)h+=`<div class="pi-m pi-two"><b>Possible POTA 2-fer</b> with ${x.two.map(r=>`${esc(r[0])}${r[1]?' ('+esc(r[1])+')':''}`).join(', ')}. Verify before activating.</div>`;
 const aps=p&&Array.isArray(p.ap)?p.ap.filter(a=>isFinite(a[0])&&isFinite(a[1])):[];
 const tot={},cnt={};aps.forEach(a=>{const k=String(a[2]||'Access point');tot[k]=(tot[k]||0)+1});const nm=a=>{const k=String(a[2]||'Access point');if(tot[k]>1){cnt[k]=(cnt[k]||0)+1;return k+' #'+cnt[k]}return k};
 const names=aps.map(nm);
 if(aps.length>1)h+=`<div class="pi-m"><b>Other entrances and parking:</b> ${aps.slice(1,8).map((a,i)=>`<a href="${gdir(a[0],a[1])}" target="_blank" rel="noopener">${esc(names[i+1])}</a>`).join(' · ')}${aps.length>8?` · +${aps.length-8} more`:''}</div>`;
 if(p){const info=[TYPEN[p.t]||p.t];if(p.acc)info.push(p.acc+' access point'+(p.acc>1?'s':'')+' on record');if(p.camp)info.push('Camping available');h+=`<div class="pi-m"><b>KPC guide:</b> ${esc(info.filter(Boolean).join(' · '))}</div>`}
 if(x.k==='pota')L2('Program details',KPC.links.pota(x.ref));else if(x.k==='sota')L2('SOTLAS summit page',KPC.links.sota(x.ref));else L2('WWFF directory',KPC.links.kff(x.ref));
 if(aps.length)L2('Directions: '+names[0],gdir(aps[0][0],aps[0][1]));else L2('Directions',gdir(x.la,x.lo));
 if(p&&p.web)L2(hostL(p.web),p.web);if(p&&p.camp&&p.camp!==p.web)L2('Campground page',p.camp);if(p&&p.off&&p.off!==p.web)L2(/\.pdf(\?|$)/i.test(p.off)?'Official map (PDF)':'Official map / info',p.off);
 L2('Share location',`https://www.google.com/maps/search/?api=1&query=${x.la},${x.lo}`);
 L2('Weather',`kpc-weather.html?lat=${x.la}&lon=${x.lo}&ref=${encodeURIComponent(x.ref)}&name=${encodeURIComponent(x.n)}`);
 if(x.k==='pota')L2('Park sheet',`kpc-park-sheet.html?ref=${encodeURIComponent(x.ref)}`);
 h+=`<div class="pi-links">${lk.join('')}</div>`;
 const inTrip=trip.some(s=>s.ref===x.ref),inList=res.some(r=>r.ref===x.ref);
 h+=`<div class="pi-acts"><button type="button" class="btn sm" data-add="${esc(x.ref)}" ${inTrip?'disabled':''}>${inTrip?'✓ IN TRIP':'+ TRIP STOP'}</button>${inList?`<button type="button" class="btn sm alt" data-findlist="${esc(x.ref)}">FIND IN RESULTS LIST →</button>`:''}${x.k==='pota'?`<a class="btn sm alt" href="finder.html?q=${encodeURIComponent(x.ref)}">OPEN IN KY PARK COMMANDER →</a>`:''}</div>`;
 return h}
function showInfo(ref,scroll){ALL=ALL||items();const x=(ALL||[]).find(i=>i.ref===ref);if(!x)return;$('parkInfoBody').innerHTML=infoHtml(x);$('parkInfoRef').textContent=x.ref;$('parkInfo').dataset.ref=ref;
 if(scroll)$('parkInfo').scrollIntoView({behavior:'smooth',block:'nearest'})}
function refreshInfo(){const r=$('parkInfo')&&$('parkInfo').dataset.ref;if(r)showInfo(r)}
document.addEventListener('click',e=>{const b=e.target.closest('[data-findlist],[data-info]');if(!b)return;
 if(b.dataset.info){showInfo(b.dataset.info,true);return}
 const i=res.findIndex(r=>r.ref===b.dataset.findlist);const el=$('list').querySelectorAll('.item')[i];if(el){el.scrollIntoView({behavior:'smooth',block:'center'});el.style.outline='3px solid #d5a63a';setTimeout(()=>el.style.outline='',1800)}});
const PROG={pota:['POTA PARK','#1d5a3a'],sota:['SOTA SUMMIT','#b5452b'],kff:['WWFF / KFF','#2b5f8a']};
function pinCard(x){const inTrip=trip.some(s=>s.ref===x.ref),P=PROG[x.k]||PROG.pota;
 return `<div class="kx-card"><span class="kx-badge" style="background:${P[1]};color:#fff">${P[0]}</span>
 <div class="kx-t">${esc(x.n)}</div>
 <div class="kx-d"><b>${esc(x.ref)}</b>${x.cls?' · '+esc(x.cls):''}${x.co&&!/official|see /i.test(x.co)?' · '+esc(KPC.cty(x.co)):''}</div>
 <div class="kx-d">${x.d.toFixed(1)} mi from ${esc(origin?origin[2]:'start')}${x.meta?' · '+x.meta:''}</div>
 ${x.dn?`<div class="kx-d">Parking / entrance on file: ${esc(x.dn)}</div>`:''}
 ${x.two&&x.two.length?`<div class="kx-d" style="margin-top:5px"><span class="kx-badge g">Possible POTA 2-Fer</span><br>with ${x.two.slice(0,4).map(r=>`<b>${esc(r[0])}</b> ${esc(r[1]||'')}`).join(', ')}${x.two.length>4?` and ${x.two.length-4} more`:''}. Verify before activating.</div>`:''}
 ${x.also&&x.also.length?`<div class="kx-d">Also: ${esc(x.also.join(' · '))}</div>`:''}
 <div class="kx-acts"><button type="button" class="pri" data-add="${x.ref}" ${inTrip?'disabled':''}>${inTrip?'✓ IN TRIP':'+ ADD TO TRIP'}</button><button type="button" data-info="${esc(x.ref)}">DETAILS ↓</button><a href="${KPC.links.dir(x.dest[0],x.dest[1],origin)}" target="_blank" rel="noopener">DIRECTIONS</a>${(x.links||[]).slice(0,1).map(([l,u])=>`<a href="${u}" target="_blank" rel="noopener">${l}</a>`).join('')}</div>
 ${x.k==='pota'?`<a href="finder.html?q=${x.ref}" style="display:inline-block;margin-top:6px;font-weight:700;font-size:12px">Open in KY Park Commander →</a>`:''}</div>`}
/* start box: a town, or a park / summit / KFF by name or number (US-1286, K-1286, 1286, W4K/EC-001, KFF-1286) */
function places(){ALL=ALL||items();return ALL}
function lbl(x){return `${x.n} (${x.ref})`}
function findPlace(v){v=v.trim();if(!v)return null;const lo=v.toLowerCase(),P=places();
 const t=D.towns.find(t=>t.n.toLowerCase()===lo);if(t)return {la:t.la,lo:t.lo,n:t.n};
 const inParen=(v.match(/\(([^)]+)\)\s*$/)||[])[1];
 let r=(inParen||v).toUpperCase().replace(/\s+/g,'');
 if(/^K-?\d{1,5}$/.test(r))r='US-'+r.replace(/^K-?/,'').padStart(4,'0');
 if(/^\d{1,5}$/.test(r))r='US-'+r.padStart(4,'0');
 if(/^US\d/.test(r))r='US-'+r.slice(2);
 if(/^KFF\d/.test(r))r='KFF-'+r.slice(3);
 let x=P.find(x=>x.ref.toUpperCase()===r);
 if(!x&&/^KFF-/.test(r)){const k=D.kff.find(k=>k.c.toUpperCase()===r);if(k&&k.p)x=P.find(y=>y.ref===k.p)}   // KFF that shares a POTA park
 if(!x){const exact=P.filter(x=>x.n.toLowerCase()===lo);const starts=P.filter(x=>x.n.toLowerCase().startsWith(lo));const has=P.filter(x=>x.n.toLowerCase().includes(lo));
  x=exact[0]||(starts.length===1?starts[0]:null)||(has.length===1?has[0]:null);
  if(!x&&(starts.length||has.length)&&lo.length>2){const l=(starts.length?starts:has);$('where').innerHTML=`<b>${l.length}</b> matches for “${esc(v)}”. Pick one from the list: ${l.slice(0,6).map(x=>esc(lbl(x))).join(' · ')}${l.length>6?' …':''}`;return null}}
 if(!x){$('where').innerHTML=`No town, park or reference matches “${esc(v)}”. Try a park name, a POTA number like US-1286, or a summit like W4K/EC-001.`;return null}
 return {la:x.la,lo:x.lo,n:lbl(x),ref:x.ref}}
function pickTown(){const p=findPlace($('town').value);if(!p)return;origin=[p.la,p.lo,p.n];if(p.ref)$('town').value=p.n;save();run();if(p.ref)showInfo(p.ref);
 if(p.ref){map.setView([p.la,p.lo],Math.max(map.getZoom(),11));const x=res.find(x=>x.ref===p.ref);if(x&&x.mk)setTimeout(()=>{x.mk.getPopup().options.autoPan=true;x.mk.openPopup()},350)}}

/* ---------------- start ---------------- */
(async()=>{
 D=await KPC.data();
 $('towns').innerHTML=D.towns.map(t=>`<option value="${esc(t.n)}">Town</option>`).join('')+places().map(x=>`<option value="${esc(lbl(x))}">${x.k==='pota'?'POTA park':x.k==='sota'?'SOTA summit':'KFF'}</option>`).join('');
 map=makeMap();KPC.countyLayer(map).catch(()=>{});
 {const b=document.querySelector('#prog_ [data-k=two]');if(b)b.setAttribute('aria-pressed',String(!!on.two))}
 layer=L.layerGroup().addTo(map);tripLayer=L.layerGroup().addTo(map);V0=[map.getCenter(),map.getZoom()];ALL=items();
 const q=new URLSearchParams(location.search);let restored=false;
 if(q.get('trip')){const t=readShared(q.get('trip'));if(t){trip=t.s;if(t.o)origin=t.o;restored=true;save();setTimeout(()=>flash('Trip loaded from a shared link.'),300)}}
 if(!restored){try{const o=JSON.parse(localStorage.getItem(TRIPKEY)||'null');if(o&&Array.isArray(o.s)){trip=o.s.filter(s=>isFinite(s.la)&&isFinite(s.lo)).slice(0,MAXSTOPS);if(Array.isArray(o.o))origin=o.o}}catch(e){}}
 if(q.get('town')){$('town').value=q.get('town');pickTown()}
 else if(origin){$('town').value=origin[2]==='your location'?'':origin[2];run()}
 renderTrip();
 if(trip.length&&!origin){map.fitBounds(L.latLngBounds(trip.map(s=>[s.la,s.lo])).pad(.3),{maxZoom:15})}
 loadBoundaries();
 window.kpcPlanner={map:()=>map,trip:()=>trip,where:(a,b)=>whereIs(a,b),ready:()=>bReady,extras:()=>X,res:()=>res};
})();
$('town').addEventListener('change',pickTown);$('town').addEventListener('input',e=>{if(e.inputType==='insertReplacementText'||!e.inputType)pickTown()});$('town').addEventListener('keydown',e=>{if(e.key==='Enter')pickTown()});
$('gps').onclick=()=>{if(!navigator.geolocation){$('where').textContent='Location is not available in this browser.';return}
 $('where').textContent='Finding your location…';navigator.geolocation.getCurrentPosition(p=>{origin=[p.coords.latitude,p.coords.longitude,'your location'];save();run()},()=>{$('where').textContent='Could not get your location. Choose a town instead.'},{enableHighAccuracy:true,timeout:15000})};
$('rad').oninput=e=>{$('rLbl').textContent=e.target.value+' MILES';if(origin)run()};
$('prog_').onclick=e=>{const b=e.target.closest('button');if(!b)return;on[b.dataset.k]=on[b.dataset.k]?0:1;b.setAttribute('aria-pressed',!!on[b.dataset.k]);if(b.dataset.k==='two'&&X)X.setOverlaps(!!on.two);if(origin)run(false)};
$('newSearch').onclick=()=>{origin=null;save();$('town').value='';$('rad').value=40;$('rLbl').textContent='40 MILES';on={pota:1,sota:1,kff:1,two:X&&X.overlapsOn()?1:0};$('prog_').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',!!on[b.dataset.k]));if(layer)layer.clearLayers();if(map&&V0)map.setView(V0[0],V0[1]);$('where').textContent='Choose a town or use your location to start.';$('list').innerHTML='<div class="empty">Results show here.</div>';try{history.replaceState(null,'',location.pathname)}catch(e){}$('town').focus()};
$('addSpot').onclick=()=>{addMode(!adding);if(adding){$('mapwrap').scrollIntoView({behavior:'smooth',block:'center'});if(map.getZoom()<12)flash('Zoom in close, then tap the exact spot. Satellite + Roads (top-right) is best for spotting pull-offs.')}};
$('clear').onclick=()=>{if(trip.length&&!confirm('Remove all '+trip.length+' stops from this trip?'))return;trip=[];changed()};
$('sortd').onclick=()=>{const o=origin||(trip[0]&&[trip[0].la,trip[0].lo]);if(!o)return;const left=[...trip],out=[];let cur=o;
 while(left.length){let bi=0,bd=Infinity;left.forEach((s,i)=>{const d=KPC.miles(cur[0],cur[1],s.la,s.lo);if(d<bd){bd=d;bi=i}});const s=left.splice(bi,1)[0];out.push(s);cur=[s.la,s.lo]}
 trip=out;changed();flash('Stops put in nearest-next order'+(origin?' from your start.':'.'))};
$('route').onclick=()=>{if(trip.length)window.open(gmapsUrl(),'_blank','noopener')};
$('share').onclick=async()=>{if(!trip.length)return;const u=shareUrl();
 try{if(navigator.share){await navigator.share({title:'KPC trip',text:'My KPC radio trip ('+trip.length+' stops)',url:u});return}}catch(e){if(e&&e.name==='AbortError')return}
 try{await navigator.clipboard.writeText(u);flash('Trip link copied. Paste it in a text or email.')}catch(e){prompt('Copy this trip link:',u)}};
$('gpx').onclick=()=>{if(!trip.length)return;const b=new Blob([gpx()],{type:'application/gpx+xml'}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='kpc-trip.gpx';document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},500)};
})();
