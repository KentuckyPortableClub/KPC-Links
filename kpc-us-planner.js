/* KPC US Trip Planner (Lite).
   Spots: locations.json (rows [prog,ref,name,lat,lon,url,...]) for POTA, SOTA and WWFF, plus POTA parks loaded live
   from api.pota.app/location/parks/US-XX for the states near the search (adds parks newer than the file).
   Place search: OpenStreetMap Nominatim (only when someone presses Search). Boundaries: OpenStreetMap via Overpass,
   only when someone taps "Show boundary". Routes: Google Maps links (3 stops between start and end on phone
   browsers, 9 elsewhere, per Google's docs) and an optional road line from the public OSRM demo server. */
(function(){
const $=id=>document.getElementById(id),esc=KPC.esc;
const COL={POTA:'#1d5a3a',SOTA:'#8a4b14',WWFF:'#2b6cb0',PIN:'#b5452b'};
const store={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
let ALL=[],BYREF={},BORD=[],map=null,dots=null,ctrMk=null,ring=null,bound=null,road=null,center=null,radius=25,progs=store.get('kpcUsProgs',['POTA','SOTA','WWFF']);
let trip=store.get('kpcUsTrip',[]),dropMode=false,NEAR=[];
const liveStates={};
const isPhone=()=>/Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)||matchMedia('(max-width:700px)').matches;
const fix=n=>Math.round(n*1e5)/1e5;
function status(t){$('us-status').innerHTML=t}

/* ---------- data ---------- */
async function loadAll(){const[L,B]=await Promise.all([fetch('locations.json').then(r=>r.json()),fetch('kpc-us-states.json').then(r=>r.json()).catch(()=>[])]);BORD=B;
 L.forEach(r=>{if(!['POTA','SOTA','WWFF'].includes(r[0]))return;if(r[0]==='POTA'&&!/^US-/.test(r[1]))return;const s={p:r[0],c:r[1],n:r[2],la:r[3],lo:r[4],url:r[5]||'',m:r[0]==='SOTA'?+r[6]||0:0,pts:r[0]==='SOTA'?+(String(r[7]||'').match(/\d+/)||[0])[0]:0};ALL.push(s);BYREF[s.c.toUpperCase()]=s})}
function statesNear(la,lo,mi){const dLa=mi/69,dLo=mi/(69*Math.cos(la*Math.PI/180));const out=[];
 BORD.forEach(b=>{let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;b.p.forEach(pl=>pl[0].forEach(([x,y])=>{x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}));
  if(lo+dLo>=x0&&lo-dLo<=x1&&la+dLa>=y0&&la-dLa<=y1)out.push(b.a)});return out}
async function addLive(la,lo,mi){if(!progs.includes('POTA'))return 0;let added=0;
 const st=statesNear(la,lo,mi).filter(a=>!(a in liveStates)).slice(0,4);
 await Promise.all(st.map(async a=>{liveStates[a]=null;try{const c=new AbortController(),t=setTimeout(()=>c.abort(),12000);const r=await fetch('https://api.pota.app/location/parks/US-'+a,{signal:c.signal});clearTimeout(t);if(!r.ok)throw 0;const j=await r.json();
  liveStates[a]=true;(Array.isArray(j)?j:[]).forEach(x=>{const ref=String(x.reference||'').toUpperCase(),la2=+x.latitude,lo2=+x.longitude;if(!/^US-\d+$/.test(ref)||!isFinite(la2)||!isFinite(lo2)||!la2)return;
   if(!BYREF[ref]){const s={p:'POTA',c:ref,n:x.name||ref,la:la2,lo:lo2,url:'',live:true};ALL.push(s);BYREF[ref]=s;added++}})}catch(e){delete liveStates[a]}}));
 return added}

/* ---------- map ---------- */
function initMap(){if(!window.L){$('usmap').innerHTML='<p style="padding:20px;color:#666">The map could not load. Check your connection or try refreshing.</p>';return}
 map=L.map('usmap',{preferCanvas:true,scrollWheelZoom:false}).setView([38.5,-96],4);
 const esri='https://server.arcgisonline.com/ArcGIS/rest/services/';
 const street=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'});
 const sat=L.tileLayer(esri+'World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery © Esri, Maxar, Earthstar Geographics'});
 const hyb=L.layerGroup([L.tileLayer(esri+'World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery © Esri, Maxar, Earthstar Geographics'}),
  L.tileLayer(esri+'Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',{maxZoom:19}),L.tileLayer(esri+'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:19})]);
 /* Satellite + Park Lines (beta): the OpenStreetMap street map, colors flipped and tinted yellow, blended onto the
    satellite picture with "screen". Its light background disappears and its dark parts (park and forest borders,
    labels, road edges) show as bright yellow lines over the real land. */
 map.createPane('parklines');const pl=map.getPane('parklines');pl.style.zIndex=250;pl.style.pointerEvents='none';pl.style.mixBlendMode='screen';
 pl.style.filter='invert(1) grayscale(1) contrast(2.2) brightness(.9) sepia(1) saturate(9) hue-rotate(2deg)';
 const glowStrength=()=>{const v=+store.get('kpcUsGlow',85);return Math.min(1,Math.max(.3,v/100))};
 const lines=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{pane:'parklines',maxZoom:19,opacity:glowStrength(),attribution:'Park lines © OpenStreetMap contributors'});
 const beta=L.layerGroup([L.tileLayer(esri+'World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery © Esri, Maxar, Earthstar Geographics'}),lines]);
 const base={'Street':street,'Satellite':sat,'Satellite + Streets':hyb,'Satellite + Park Lines (Beta)':beta};let want=store.get('kpcUsBase','Street');(base[want]||street).addTo(map);
 const glow=L.control({position:'bottomleft'});glow.onAdd=()=>{const d=L.DomUtil.create('div','us-glow');
  d.innerHTML=`<label>PARK LINES <input type="range" min="30" max="100" step="5" value="${Math.round(glowStrength()*100)}" aria-label="Park line strength"></label><small>Zoom in to county level to see park borders</small>`;
  L.DomEvent.disableClickPropagation(d);L.DomEvent.disableScrollPropagation(d);
  d.querySelector('input').oninput=e=>{lines.setOpacity(e.target.value/100);store.set('kpcUsGlow',+e.target.value)};return d};
 const showGlow=name=>{if(name==='Satellite + Park Lines (Beta)')glow.addTo(map);else glow.remove()};showGlow(base[want]?want:'Street');
 map.on('baselayerchange',e=>showGlow(e.name));
 L.control.layers(base,null,{position:'topright',collapsed:true}).addTo(map);map.on('baselayerchange',e=>store.set('kpcUsBase',e.name));
 dots=L.layerGroup().addTo(map);
 map.on('click',e=>{if(!dropMode)return;const nm=prompt('Name this pin (campsite, gas stop, lookout…):','My pin');if(nm===null)return;
  addStop({p:'PIN',c:'PIN-'+Date.now().toString(36),n:(nm.trim()||'My pin').slice(0,60),la:fix(e.latlng.lat),lo:fix(e.latlng.lng)});setDrop(false)});
 map.on('popupopen',e=>{const el=e.popup.getElement();if(!el)return;const s=e.popup._kpc;if(!s)return;
  el.querySelectorAll('[data-a]').forEach(b=>b.onclick=ev=>{ev.preventDefault();const a=b.dataset.a;if(a==='add'){inTrip(s.c)?removeStop(s.c):addStop(s);map.closePopup()}else if(a==='bound')showBoundary(s,b)});
  if(s.p==='POTA')livePota(s,el.querySelector('.live'))})}
function setDrop(on){dropMode=on;if(on&&map)map.closePopup();$('us-drop').setAttribute('aria-pressed',on);$('usmap').classList.toggle('dropping',on);$('us-maphint').textContent=on?'Tap the map where you want your pin.':'Tap a dot to add it to your trip, see Street View or show its boundary. Use the layers button for Street, Satellite or Satellite + Streets.'}
function links(s){const sv=`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${s.la},${s.lo}`;
 const page=s.p==='POTA'?KPC.links.pota(s.c):s.p==='SOTA'?(s.url||KPC.links.sota(s.c)):s.p==='WWFF'?KPC.links.kff(s.c):'';
 return{sv,dir:KPC.links.dir(s.la,s.lo),page}}
function popup(s){const l=links(s),d=center?KPC.miles(center[0],center[1],s.la,s.lo):null;
 const what=s.p==='POTA'?'POTA park':s.p==='SOTA'?`SOTA summit${s.m?' • '+s.m.toLocaleString()+' m ('+Math.round(s.m*3.28084).toLocaleString()+' ft)':''}${s.pts?' • '+s.pts+' pts':''}`:s.p==='WWFF'?'WWFF reference':'Your pin';
 const div=`<div class="us-pop"><b>${esc(s.n)}</b><div class="meta">${s.p==='PIN'?'':esc(s.c)+' • '}${what}${d!=null?' • '+d.toFixed(1)+' mi away':''} • grid ${KPC.grid(s.la,s.lo).slice(0,6)}</div>
<div class="live"></div>
<div class="acts"><button type="button" class="go" data-a="add">${inTrip(s.c)?'&#10003; IN TRIP (REMOVE)':'+ ADD TO TRIP'}</button><a href="${l.sv}" target="_blank" rel="noopener">&#128064; STREET VIEW</a><a href="${l.dir}" target="_blank" rel="noopener">DIRECTIONS</a>${s.p!=='PIN'&&s.p!=='SOTA'?'<button type="button" data-a="bound">SHOW BOUNDARY</button>':''}${l.page?`<a href="${l.page}" target="_blank" rel="noopener">${s.p} PAGE &#8599;</a>`:''}</div></div>`;
 return div}
async function livePota(s,el){if(!el||el.dataset.done)return;el.dataset.done=1;el.textContent='Checking POTA…';
 try{const r=await fetch(`https://api.pota.app/park/activations/${s.c}?count=all`);if(!r.ok)throw 0;const j=await r.json();const a=Array.isArray(j)?j:[];
  if(!a.length){el.textContent='No activations yet: a new one for POTA!';return}
  const last=a.map(x=>String(x.qso_date||'')).sort().pop();const good=a.filter(x=>+x.totalQSOs>=10).length;
  el.textContent=`${a.length} activation attempt${a.length===1?'':'s'} (${good} with 10+ QSOs) • last ${KPC.fmtDate(last)}`}catch(e){el.textContent=''}}
function drawDots(){if(!map)return;dots.clearLayers();
 const show=center?NEAR:[];
 show.forEach(s=>{const inT=inTrip(s.c);const mk=L.circleMarker([s.la,s.lo],{radius:inT?8:s.p==='SOTA'?5:6,weight:inT?3:1,color:inT?'#f0c96b':'#173a28',fillColor:COL[s.p],fillOpacity:.9});
  const pp=L.popup({maxWidth:300}).setContent(popup(s));pp._kpc=s;mk.bindPopup(pp);mk.addTo(dots)});
 trip.filter(s=>s.p==='PIN').forEach(s=>{const mk=L.marker([s.la,s.lo],{icon:L.divIcon({className:'',html:'<div class="pin-us"></div>',iconSize:[16,16],iconAnchor:[8,16]})});const pp=L.popup({maxWidth:300}).setContent(popup(s));pp._kpc=s;mk.bindPopup(pp);mk.addTo(dots)})}

/* ---------- search ---------- */
function normRef(q){q=q.trim().toUpperCase().replace(/\s+/g,'');if(/^K-\d{4,5}$/.test(q))q='US-'+q.slice(2);return q}
async function search(q){q=q.trim();if(!q)return;$('us-hits').style.display='none';
 const ref=normRef(q);if(BYREF[ref]){const s=BYREF[ref];await go(s.la,s.lo,s.n);openSpot(s);return}
 const lq=q.toLowerCase();const parks=ALL.filter(s=>progs.includes(s.p)&&s.n.toLowerCase().includes(lq)).slice(0,8);
 status('Searching places…');let places=[];
 try{const r=await fetch('https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=us&limit=6&q='+encodeURIComponent(q),{headers:{'Accept-Language':'en'}});if(r.ok)places=await r.json()}catch(e){}
 const items=[...places.map(p=>({t:'place',la:+p.lat,lo:+p.lon,n:p.display_name})),...parks.map(s=>({t:'spot',s}))];
 if(!items.length){status(`Nothing found for “${esc(q)}”. Try a town and state (“Berea KY”), a ZIP, or a park number.`);return}
 if(items.length===1){const i=items[0];if(i.t==='place')go(i.la,i.lo,i.n);else{await go(i.s.la,i.s.lo,i.s.n);openSpot(i.s)}return}
 status('Pick one:');const h=$('us-hits');h.style.display='block';
 h.innerHTML=items.map((i,k)=>i.t==='place'?`<button type="button" data-k="${k}">&#128205; ${esc(i.n.split(',').slice(0,3).join(','))}<small>Place</small></button>`:`<button type="button" data-k="${k}"><span class="dot" style="background:${COL[i.s.p]}"></span>${esc(i.s.n)}<small>${i.s.p} ${esc(i.s.c)}</small></button>`).join('');
 h.onclick=async e=>{const b=e.target.closest('button');if(!b)return;const i=items[+b.dataset.k];h.style.display='none';if(i.t==='place')go(i.la,i.lo,i.n.split(',').slice(0,2).join(','));else{await go(i.s.la,i.s.lo,i.s.n);openSpot(i.s)}}}
function openSpot(s){if(!map)return;let hit=null;dots.eachLayer(l=>{if(l.getPopup&&l.getPopup()&&l.getPopup()._kpc===s)hit=l});if(hit)hit.openPopup()}
async function go(la,lo,label){center=[la,lo];radius=+$('usr').value;store.set('kpcUsLast',{la,lo,label,r:radius});
 status(`Loading spots near ${esc(label||'there')}…`);
 const added=await addLive(la,lo,radius);
 NEAR=ALL.filter(s=>progs.includes(s.p)).map(s=>({s,d:KPC.miles(la,lo,s.la,s.lo)})).filter(x=>x.d<=radius).sort((a,b)=>a.d-b.d).map(x=>x.s);
 const n={POTA:0,SOTA:0,WWFF:0};NEAR.forEach(s=>n[s.p]++);
 status(`<b>${NEAR.length.toLocaleString()}</b> spots within ${radius} miles of ${esc(label||'there')}: ${progs.map(p=>n[p].toLocaleString()+' '+p).join(', ')}.${added?` (${added} newer POTA park${added===1?'':'s'} loaded live from POTA.)`:''}`);
 if(map){if(ctrMk)ctrMk.remove();if(ring)ring.remove();
  ctrMk=L.marker([la,lo],{interactive:false,icon:L.divIcon({className:'',html:'<div class="ctr-us"></div>',iconSize:[20,20],iconAnchor:[10,10]})}).addTo(map);
  ring=L.circle([la,lo],{radius:radius*1609.34,color:'#171717',weight:1.5,dashArray:'6 6',fill:false,interactive:false}).addTo(map);
  map.fitBounds(ring.getBounds(),{padding:[10,10]})}
 drawDots();drawNear()}
function drawNear(){const box=$('near');if(!center){box.style.display='none';return}box.style.display='';
 $('near-h').textContent=`Nearby (${NEAR.length.toLocaleString()}${NEAR.length>150?', closest 150 shown':''})`;
 $('near-body').innerHTML=NEAR.slice(0,150).map((s,i)=>`<tr><td><span class="dot" style="background:${COL[s.p]}"></span><a href="#" data-o="${i}" class="ref">${esc(s.c)}</a><br>${esc(s.n)}</td><td>${KPC.miles(center[0],center[1],s.la,s.lo).toFixed(1)}</td><td><button type="button" class="add${inTrip(s.c)?' in':''}" data-i="${i}">${inTrip(s.c)?'&#10003; ADDED':'+ ADD'}</button></td></tr>`).join('')||'<tr><td colspan="3" class="muted">Nothing that close. Try a bigger distance.</td></tr>'}

/* ---------- boundary (OpenStreetMap, on request) ---------- */
/* The main overpass-api.de server says it is overloaded and refuses requests at busy times, so try the free public
   mirrors it lists first (private.coffee and VK Maps, no rate limits), then the main one. A form POST avoids long URLs
   and needs no CORS preflight. Answers are remembered per park for this visit. */
const OVP=['https://overpass.private.coffee/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter','https://overpass-api.de/api/interpreter'];
const ovpCache={};
/* every failure is kept so the message can say exactly what each server answered */
const OVPN=['private.coffee','VK Maps','overpass-api.de'];
async function overpass(q,key){if(ovpCache[key])return ovpCache[key];let last;const why=[];
 for(const u of OVP){const c=new AbortController(),t=setTimeout(()=>c.abort(),25000);
  try{const r=await fetch(u,{method:'POST',body:'data='+encodeURIComponent(q),headers:{'Content-Type':'application/x-www-form-urlencoded'},signal:c.signal});
   if(!r.ok)throw new Error('HTTP '+r.status);const j=await r.json();if(j&&Array.isArray(j.elements)){ovpCache[key]=j;return j}throw new Error('bad answer')}
  catch(e){last=e;why.push(OVPN[OVP.indexOf(u)]+': '+(e.name==='AbortError'?'timed out after 25 s':/^HTTP \d+/.test(e.message)?'server answered '+e.message.replace('HTTP ','')+({'429':' (too many requests)','406':' (request refused)','504':' (server overloaded)','503':' (server unavailable)','400':' (query not accepted)'}[e.message.slice(5)]||''):e.message==='bad answer'?'sent something that was not boundary data':'blocked or unreachable from this browser ('+(e.message||e.name)+')'))}finally{clearTimeout(t)}}
 const err=new Error('all servers failed');err.why=why;throw err}
function sim(a,b){const w=t=>new Set(String(t).toLowerCase().replace(/[^a-z0-9 ]/g,' ').split(/\s+/).filter(x=>x.length>2&&!['state','park','national','area','the','and','wildlife','management'].includes(x)));const A=w(a),B=w(b);let n=0;A.forEach(x=>{if(B.has(x))n++});return n/Math.max(1,Math.min(A.size,B.size))}
async function showBoundary(s,btn){if(bound){bound.remove();bound=null}btn.textContent='LOOKING…';btn.disabled=true;
 const b=map.getBounds().pad(0.5),bb=`${b.getSouth().toFixed(4)},${b.getWest().toFixed(4)},${b.getNorth().toFixed(4)},${b.getEast().toFixed(4)}`;
 const q=`[out:json][timeout:25];is_in(${s.la},${s.lo})->.a;(way(pivot.a)["boundary"~"protected_area|national_park"];rel(pivot.a)["boundary"~"protected_area|national_park"];way(pivot.a)["leisure"~"park|nature_reserve"];rel(pivot.a)["leisure"~"park|nature_reserve"];);out geom(${bb});`;
 try{const j=await overpass(q,s.c);const els=(j.elements||[]).filter(e=>e.tags);if(!els.length){btn.textContent='NO OUTLINE IN OPENSTREETMAP';return}
  const area=e=>{const g=e.type==='way'?e.geometry:(e.members||[]).flatMap(m=>m.geometry||[]);if(!g||!g.length)return 1e9;let a=1e9,c=-1e9,d=1e9,f=-1e9;g.forEach(p=>{if(!p)return;a=Math.min(a,p.lat);c=Math.max(c,p.lat);d=Math.min(d,p.lon);f=Math.max(f,p.lon)});return(c-a)*(f-d)};
  els.sort((x,y)=>(sim(s.n,y.tags.name||'')-sim(s.n,x.tags.name||''))||(area(x)-area(y)));const e=els[0];
  const lines=[];if(e.type==='way'&&e.geometry)lines.push(e.geometry.filter(Boolean).map(p=>[p.lat,p.lon]));
  else(e.members||[]).forEach(m=>{if(m.type==='way'&&m.geometry)lines.push(m.geometry.filter(Boolean).map(p=>[p.lat,p.lon]))});
  bound=L.featureGroup(lines.filter(l=>l.length>1).map(l=>{const closed=l.length>3&&l[0][0]===l[l.length-1][0]&&l[0][1]===l[l.length-1][1];return closed?L.polygon(l,{color:'#f0c96b',weight:3,fillColor:'#f0c96b',fillOpacity:.12,interactive:false}):L.polyline(l,{color:'#f0c96b',weight:3,interactive:false})})).addTo(map);
  btn.textContent='OUTLINE: '+String(e.tags.name||'unnamed area').toUpperCase().slice(0,40);status(`Boundary shown: <b>${esc(e.tags.name||'unnamed area')}</b> from OpenStreetMap${sim(s.n,e.tags.name||'')<.5?' (closest match: it may not be the exact POTA park area)':''}.`)}
 catch(err){btn.textContent='BOUNDARY NOT AVAILABLE, TAP TO TRY AGAIN';status('Boundary lookup failed. What each server said: <b>'+esc((err.why||[err.message]).join(' \u2022 '))+'</b>. Send a screenshot of this to the site admin. Meanwhile try the <b>Satellite + Park Lines (Beta)</b> map in the layers button.');btn.disabled=false;return}btn.disabled=false}

/* ---------- trip ---------- */
const inTrip=c=>trip.some(s=>s.c===c);
function saveTrip(){store.set('kpcUsTrip',trip)}
function addStop(s){if(inTrip(s.c))return;trip.push({p:s.p,c:s.c,n:s.n,la:s.la,lo:s.lo,url:s.url||'',live:!!s.live});saveTrip();drawTrip();drawDots();drawNear()}
function removeStop(c){trip=trip.filter(s=>s.c!==c);saveTrip();drawTrip();drawDots();drawNear()}
function legs(){const per=isPhone()?5:11,fromMe=$('t-fromme').checked,out=[];
 const pts=trip.map(s=>`${s.la},${s.lo}`);if(!pts.length)return out;
 if(fromMe){for(let i=0;i<pts.length;i+=per-1){const seg=pts.slice(i,i+per-1);out.push({a:i+1,b:i+seg.length,url:'https://www.google.com/maps/dir/?api=1&travelmode=driving&destination='+seg[seg.length-1]+(seg.length>1?'&waypoints='+encodeURIComponent(seg.slice(0,-1).join('|')):'')+(i>0?'&origin='+pts[i-1]:'')})}}
 else{if(pts.length<2)return out;for(let i=0;i<pts.length-1;i+=per-1){const seg=pts.slice(i,i+per);out.push({a:i+1,b:i+seg.length,url:'https://www.google.com/maps/dir/?api=1&travelmode=driving&origin='+seg[0]+'&destination='+seg[seg.length-1]+(seg.length>2?'&waypoints='+encodeURIComponent(seg.slice(1,-1).join('|')):'')})}}
 return out}
function drawTrip(){const n=trip.length;$('trip-empty').style.display=n?'none':'';$('trip-acts').style.display=n?'flex':'none';$('t-fromme-l').style.display=n?'flex':'none';
 $('trip-list').innerHTML=trip.map((s,i)=>`<li><div><b>${esc(s.n)}</b><small>${s.p==='PIN'?'Your pin':esc(s.p+' '+s.c)} • <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${s.la},${s.lo}" target="_blank" rel="noopener">Street View</a></small></div><div class="mv"><button type="button" data-u="${i}" aria-label="Move up">&#8593;</button><button type="button" data-d="${i}" aria-label="Move down">&#8595;</button><button type="button" data-x="${i}" aria-label="Remove">&#10005;</button></div></li>`).join('');
 let mi=0;for(let i=1;i<n;i++)mi+=KPC.miles(trip[i-1].la,trip[i-1].lo,trip[i].la,trip[i].lo);
 $('trip-sum').textContent=n>1?`${n} stops • about ${Math.round(mi)} miles in a straight line (driving is longer).`:'';
 const L2=legs();$('trip-legs').innerHTML=L2.map((l,i)=>`<a class="btn" href="${l.url}" target="_blank" rel="noopener">${L2.length>1?`ROUTE PART ${i+1} (STOPS ${l.a}–${l.b})`:'OPEN ROUTE IN GOOGLE MAPS'} &#8599;</a>`).join('')+(L2.length>1?`<p class="muted" style="font-size:12px;margin:4px 0 0;flex-basis:100%">Google Maps only takes ${isPhone()?'5':'11'} stops per link${isPhone()?' on a phone':''}, so longer trips open in parts.</p>`:'');
 if(road&&n<2){road.remove();road=null}}
function bestOrder(){if(trip.length<3)return;const start=trip[0],rest=trip.slice(1),out=[start];
 while(rest.length){const last=out[out.length-1];let bi=0,bd=1e9;rest.forEach((s,i)=>{const d=KPC.miles(last.la,last.lo,s.la,s.lo);if(d<bd){bd=d;bi=i}});out.push(rest.splice(bi,1)[0])}
 const D=(a,b)=>KPC.miles(a.la,a.lo,b.la,b.lo);let better=true;while(better){better=false;for(let i=1;i<out.length-2;i++)for(let k=i+1;k<out.length-1;k++){if(D(out[i-1],out[i])+D(out[k],out[k+1])>D(out[i-1],out[k])+D(out[i],out[k+1])+1e-9){out.splice(i,k-i+1,...out.slice(i,k+1).reverse());better=true}}}
 trip=out;saveTrip();drawTrip()}
async function drawRoad(){if(trip.length<2||!map)return;const b=$('t-road');b.textContent='ROUTING…';
 try{const pts=trip.slice(0,25).map(s=>`${s.lo},${s.la}`).join(';');const r=await fetch(`https://router.project-osrm.org/route/v1/driving/${pts}?overview=full&geometries=geojson`);if(!r.ok)throw 0;const j=await r.json();const rt=j.routes&&j.routes[0];if(!rt)throw 0;
  if(road)road.remove();road=L.geoJSON(rt.geometry,{style:{color:'#b5452b',weight:5,opacity:.8}}).addTo(map);map.fitBounds(road.getBounds(),{padding:[20,20]});
  const h=Math.floor(rt.duration/3600),m=Math.round(rt.duration%3600/60);b.textContent='DRAW DRIVING ROUTE';
  $('trip-sum').textContent=`${trip.length} stops • about ${Math.round(rt.distance/1609.34)} driving miles, ${h?h+' h ':''}${m} min${trip.length>25?' (first 25 stops)':''}.`}
 catch(e){b.textContent='ROUTE SERVICE BUSY, USE GOOGLE MAPS'}}
function gpx(){const x=s=>String(s).replace(/[<>&"]/g,c=>({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c]));
 const body=trip.map(s=>`<wpt lat="${s.la}" lon="${s.lo}"><name>${x(s.p==='PIN'?s.n:s.c+' '+s.n)}</name><desc>${x(s.p)}</desc></wpt>`).join('\n');
 const rte='<rte><name>KPC trip</name>'+trip.map(s=>`<rtept lat="${s.la}" lon="${s.lo}"><name>${x(s.p==='PIN'?s.n:s.c)}</name></rtept>`).join('')+'</rte>';
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([`<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="Kentucky Portable Club" xmlns="http://www.topografix.com/GPX/1/1">\n${body}\n${rte}\n</gpx>`],{type:'application/gpx+xml'}));
 a.download=`KPC_trip_${new Date().toISOString().slice(0,10)}.gpx`;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},500)}
function shareUrl(){const t=trip.map(s=>s.p==='PIN'?`pin:${s.la},${s.lo},${encodeURIComponent(s.n)}`:s.live?`live:${s.c},${s.la},${s.lo},${encodeURIComponent(s.n)}`:s.c).join('~');const u=new URL(location.href);u.search='';u.hash='';u.searchParams.set('t',t);return u.toString()}
async function share(){const u=shareUrl(),b=$('t-share');try{if(navigator.share){await navigator.share({title:'KPC trip',url:u});return}}catch(e){}
 try{await navigator.clipboard.writeText(u);b.textContent='LINK COPIED';setTimeout(()=>b.textContent='SHARE LINK',2500)}catch(e){prompt('Copy this link:',u)}}
function loadShared(){const t=new URLSearchParams(location.search).get('t');if(!t)return false;const out=[];
 t.split('~').forEach(x=>{if(/^live:/.test(x)){const[c,la,lo,...n]=x.slice(5).split(',');if(isFinite(+la)&&isFinite(+lo)){const s=BYREF[c.toUpperCase()]||{p:'POTA',c:c.toUpperCase(),n:decodeURIComponent(n.join(','))||c,la:+la,lo:+lo,url:'',live:true};if(!BYREF[s.c]){ALL.push(s);BYREF[s.c]=s}out.push({p:'POTA',c:s.c,n:s.n,la:s.la,lo:s.lo,url:'',live:true})}}else if(/^pin:/.test(x)){const[la,lo,...n]=x.slice(4).split(',');if(isFinite(+la)&&isFinite(+lo))out.push({p:'PIN',c:'PIN-'+out.length+Date.now().toString(36),n:decodeURIComponent(n.join(','))||'Pin',la:+la,lo:+lo})}else{const s=BYREF[x.toUpperCase()];if(s)out.push({p:s.p,c:s.c,n:s.n,la:s.la,lo:s.lo,url:s.url})}});
 if(out.length){trip=out;saveTrip();return true}return false}

/* ---------- wire up ---------- */
$('usf').onsubmit=e=>{e.preventDefault();search($('usq').value)};
$('usr').onchange=()=>{if(center)go(center[0],center[1],(store.get('kpcUsLast',{})||{}).label)};
$('us-progs').onclick=e=>{const b=e.target.closest('button');if(!b)return;const p=b.dataset.p;progs=progs.includes(p)?progs.filter(x=>x!==p):progs.concat(p);if(!progs.length)progs=[p];store.set('kpcUsProgs',progs);
 [...$('us-progs').children].forEach(x=>x.setAttribute('aria-pressed',progs.includes(x.dataset.p)));if(center)go(center[0],center[1],(store.get('kpcUsLast',{})||{}).label)};
$('us-me').onclick=()=>{if(!navigator.geolocation){status('This browser can’t share your location.');return}status('Finding you…');
 navigator.geolocation.getCurrentPosition(p=>go(fix(p.coords.latitude),fix(p.coords.longitude),'you'),()=>status('Location was blocked or unavailable. Type a town or ZIP instead.'),{timeout:15000,maximumAge:300000})};
$('us-drop').onclick=()=>setDrop(!dropMode);
$('near-body').onclick=e=>{const a=e.target.closest('[data-i]'),o=e.target.closest('[data-o]');
 if(a){const s=NEAR[+a.dataset.i];inTrip(s.c)?removeStop(s.c):addStop(s)}
 if(o){e.preventDefault();const s=NEAR[+o.dataset.o];map&&map.setView([s.la,s.lo],Math.max(map.getZoom(),11));setTimeout(()=>openSpot(s),300);$('usmap').scrollIntoView({behavior:'smooth',block:'center'})}};
$('trip-list').onclick=e=>{const b=e.target.closest('button');if(!b)return;const i=+(b.dataset.u??b.dataset.d??b.dataset.x);
 if(b.dataset.x!=null)return removeStop(trip[i].c);const j=b.dataset.u!=null?i-1:i+1;if(j<0||j>=trip.length)return;[trip[i],trip[j]]=[trip[j],trip[i]];saveTrip();drawTrip()};
$('t-order').onclick=bestOrder;$('t-road').onclick=drawRoad;$('t-gpx').onclick=gpx;$('t-share').onclick=share;$('t-fromme').onchange=drawTrip;
$('t-clear').onclick=()=>{if(confirm('Clear all stops from this trip?')){trip=[];saveTrip();if(road){road.remove();road=null}drawTrip();drawDots();drawNear()}};
[...$('us-progs').children].forEach(x=>x.setAttribute('aria-pressed',progs.includes(x.dataset.p)));
initMap();
loadAll().then(()=>{const shared=loadShared();drawTrip();
 const last=store.get('kpcUsLast',null);if(last&&isFinite(last.la)){$('usr').value=String(last.r||25);go(last.la,last.lo,last.label)}
 else if(shared&&trip.length){go(trip[0].la,trip[0].lo,trip[0].n)}
 else status(`${ALL.length.toLocaleString()} POTA parks, SOTA summits and WWFF references ready. Search a town, ZIP or park to start.`);
 if(shared&&map&&trip.length)map.fitBounds(L.latLngBounds(trip.map(s=>[s.la,s.lo])),{padding:[30,30],maxZoom:11})})
 .catch(()=>status('Could not load the park list. Check your connection and refresh.'));
})();
