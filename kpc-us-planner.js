/* place-name labels over satellite (Esri). Oct 16: an iPhone-only CARTO version was tried and taken out again:
   CARTO now answers 'API KEY REQUIRED' (Brandon's iPhone screenshot). Same labels on every device. */
window.kpcPlaceLabels=window.kpcPlaceLabels||function(z){var o={maxZoom:19};if(z)o.zIndex=z;
 return L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',o)};
/* KPC KPC US Trip Planner.
   Spots: locations.json (rows [prog,ref,name,lat,lon,url,...]) for POTA, SOTA and WWFF, plus POTA parks loaded live
   from api.pota.app/location/parks/US-XX for the states near the search (adds parks newer than the file).
   Place search: OpenStreetMap Nominatim (only when someone presses Search). Boundaries: OpenStreetMap via Overpass,
   only when someone taps "Show boundary". Routes: Google Maps links (3 stops between start and end on phone
   browsers, 9 elsewhere, per Google's docs) and an optional road line from the public OSRM demo server. */
(function(){
const $=id=>document.getElementById(id),esc=KPC.esc;
const COL={POTA:'#1d5a3a',SOTA:'#8a4b14',WWFF:'#2b6cb0',PIN:'#b5452b'};
const store={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
let BIG=store.get('kpcUsBig',false),ALL=[],BYREF={},BORD=[],map=null,dots=null,ctrMk=null,ring=null,bound=null,boundRef='',road=null,center=null,radius=25,progs=store.get('kpcUsProgs',['POTA','SOTA','WWFF']);
let trip=store.get('kpcUsTrip',[]),dropMode=false,NEAR=[];
const liveStates={};
const TAP=matchMedia('(pointer:coarse)').matches;
const isPhone=()=>/Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)||matchMedia('(max-width:700px)').matches;
const fix=n=>Math.round(n*1e5)/1e5;
function status(t){$('us-status').innerHTML=t}
/* My Parks checker (kpc-my-parks.js): NEW TO ME / ATNO filters, badges and faded / orange-ringed dots */
const KM=window.KPCMine||null;
let LIST=[];const PICKED={};   /* route boxes: places picked from the suggestion list */
const allNear=()=>NEAR;
const vis=()=>KM&&KM.filtering()?NEAR.filter(s=>KM.show(s.c)):NEAR;
const kmBadge=s=>KM&&s.p!=='PIN'?KM.badge(s.c):'';

/* ---------- data ---------- */
async function loadAll(){const[L,B,CA]=await Promise.all([fetch('locations.json').then(r=>r.json()),fetch('kpc-us-states.json').then(r=>r.json()).catch(()=>[]),fetch('data/canada.json').then(r=>r.ok?r.json():{rows:[]}).catch(()=>({rows:[]}))]);BORD=B;
 /* Canada (Brandon Oct 16: pins now, boundaries later): CA- POTA parks, VEFF WWFF, VE/VA/VY/VO SOTA from data/canada.json */
 L.concat((CA&&CA.rows)||[]).forEach(r=>{if(!['POTA','SOTA','WWFF'].includes(r[0]))return;if(r[0]==='POTA'&&!/^(US|CA)-/.test(r[1]))return;if(BYREF[String(r[1]).toUpperCase()])return;const s={p:r[0],c:r[1],n:r[2],la:r[3],lo:r[4],url:r[5]||'',m:r[0]==='SOTA'?+r[6]||0:0,pts:r[0]==='SOTA'?+(String(r[7]||'').match(/\d+/)||[0])[0]:0};ALL.push(s);BYREF[s.c.toUpperCase()]=s})}
function statesNear(la,lo,mi){const dLa=mi/69,dLo=mi/(69*Math.cos(la*Math.PI/180));const out=[];
 BORD.forEach(b=>{let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;b.p.forEach(pl=>pl[0].forEach(([x,y])=>{x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}));
  if(lo+dLo>=x0&&lo-dLo<=x1&&la+dLa>=y0&&la-dLa<=y1)out.push(b.a)});return out}
async function addLive(la,lo,mi){if(!progs.includes('POTA'))return 0;let added=0;
 const st=statesNear(la,lo,mi).filter(a=>!(a in liveStates)).slice(0,4);
 await Promise.all(st.map(async a=>{liveStates[a]=null;try{const c=new AbortController(),t=setTimeout(()=>c.abort(),12000);const r=await fetch('https://api.pota.app/location/parks/US-'+a,{signal:c.signal});clearTimeout(t);if(!r.ok)throw 0;const j=await r.json();
  liveStates[a]=true;if(window.KPCMine)KPCMine.takePotaList(a,j);(Array.isArray(j)?j:[]).forEach(x=>{const ref=String(x.reference||'').toUpperCase(),la2=+x.latitude,lo2=+x.longitude;if(!/^US-\d+$/.test(ref)||!isFinite(la2)||!isFinite(lo2)||!la2)return;
   if(!BYREF[ref]){const s={p:'POTA',c:ref,n:x.name||ref,la:la2,lo:lo2,url:'',live:true};ALL.push(s);BYREF[ref]=s;added++}})}catch(e){delete liveStates[a]}}));
 return added}

/* ---------- map ---------- */
function initMap(){if(!window.L){$('usmap').innerHTML='<p style="padding:20px;color:#666">The map could not load. Check your connection or try refreshing.</p>';return}
 /* dots are drawn on a canvas; tolerance widens the tap area around each dot (more on touch screens) */
 map=L.map('usmap',{preferCanvas:true,renderer:L.canvas({padding:.5,tolerance:TAP?14:5}),scrollWheelZoom:false}).setView([38.5,-96],4);
 try{kpcFullBtn(map,'bottomright')}catch(e){}
 if(window.kpcLocate)kpcLocate(map,{position:'bottomright'});
 const esri='https://server.arcgisonline.com/ArcGIS/rest/services/';
 const street=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'});
 const sat=L.tileLayer(esri+'World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery © Esri, Maxar, Earthstar Geographics'});
 const hyb=L.layerGroup([L.tileLayer(esri+'World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery © Esri, Maxar, Earthstar Geographics'}),
  L.tileLayer(esri+'Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,zIndex:8}),kpcPlaceLabels(9)]);
 const terrain=L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxNativeZoom:17,maxZoom:19,attribution:'© OpenTopoMap (CC-BY-SA), © OpenStreetMap contributors'});
 /* Official boundaries (USGS PAD-US, kpc-padus-layer.js): federal + state land outlined over any map */
 const pad=window.KPCPad?KPCPad(map,{keyPos:'bottomleft'}):null;
 const offi=L.layerGroup([L.tileLayer(esri+'World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery © Esri, Maxar, Earthstar Geographics'}),
  L.tileLayer(esri+'Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,zIndex:8}),kpcPlaceLabels(9)]);   /* streets + names above the boundary outlines (zIndex 6) */
 const OFF='Satellite + Streets + Official Boundaries';
 /* the old 'Satellite + Park Lines (Beta)' map was removed Oct 16 (Brandon); anyone who had it gets the official boundaries map */
 const base={'Street':street,'Terrain':terrain,'Satellite':sat,'Satellite + Streets':hyb,[OFF]:offi};let want=store.get('kpcUsBase',pad?OFF:'Street');if(want==='Satellite + Official Boundaries'||/Park Lines/.test(want))want=pad?OFF:'Satellite + Streets';if(window.KPCTripOffline&&KPCTripOffline.offline())want='Street';   /* no signal: the saved street map */
 (base[want]||street).addTo(map);
 if(pad){if(store.get('kpcUsPad',true)||want===OFF)pad.layer.addTo(map);
  map.on('baselayerchange',e=>{if(e.name===OFF&&!map.hasLayer(pad.layer))pad.layer.addTo(map)});
  map.on('overlayadd',e=>{if(e.layer===pad.layer)store.set('kpcUsPad',true)});map.on('overlayremove',e=>{if(e.layer===pad.layer)store.set('kpcUsPad',false)})}
 /* National Scenic / Historic Trails that are POTA parks (data/trails, official lines from the NPS, Forest Service and
    trail partners, refreshed monthly by kpc-us-trails.yml). Only trails crossing the map view are loaded. Drawn in their
    own pane under the park dots so a tap on a dot still opens the dot. */
 const trails=window.KPCTrails?KPCTrails(map):L.layerGroup();
 const over={};if(pad)over['Official park boundaries (PAD-US)']=pad.layer;over['Trails that are POTA parks']=trails;
 if(store.get('kpcUsTrails',true))trails.addTo(map);
 map.on('overlayadd',e=>{if(e.layer===trails)store.set('kpcUsTrails',true)});map.on('overlayremove',e=>{if(e.layer===trails)store.set('kpcUsTrails',false)});
 L.control.layers(base,over,{position:'topright',collapsed:true}).addTo(map);map.on('baselayerchange',e=>store.set('kpcUsBase',e.name));
 dots=L.featureGroup().addTo(map);
 /* drop mode wins over dots: with big phone tap areas most taps land on a dot, so drop the pin there too */
 let dropBusy=0;const dropAt=ll=>{if(!dropMode||dropBusy)return;dropBusy=1;map.closePopup();setTimeout(()=>{dropBusy=0;const nm=prompt('Name this pin (campsite, gas stop, lookout…):','My pin');if(nm===null)return;
  addStop({p:'PIN',c:'PIN-'+Date.now().toString(36),n:(nm.trim()||'My pin').slice(0,60),la:fix(ll.lat),lo:fix(ll.lng)});setDrop(false)},30)};
 map.on('click',e=>dropAt(e.latlng));dots.on('click',e=>{if(dropMode){L.DomEvent.stop(e);dropAt(e.latlng)}});
 map.on('popupopen',e=>{if(dropMode)setTimeout(()=>map.closePopup(),0)});
 map.on('popupopen',e=>{const el=e.popup.getElement();if(!el)return;const s=e.popup._kpc;if(!s)return;
  {const bb=el.querySelector('[data-a="bound"]');if(bb)bb.textContent=bound&&boundRef===s.c?'HIDE OUTLINE':'SHOW THIS PARK\u2019S OUTLINE'}
  el.querySelectorAll('[data-a]').forEach(b=>b.onclick=ev=>{ev.preventDefault();const a=b.dataset.a;if(a==='add'){inTrip(s.c)?removeStop(s.c):addStop(s);map.closePopup()}else if(a==='bound')showBoundary(s,b)});
  if(s.p==='POTA')livePota(s,el.querySelector('.live'));if(s.p!=='PIN')parkInfo(s,el.querySelector('.pinfo'))})}
function setDrop(on){dropMode=on;if(on&&map)map.closePopup();$('us-drop').setAttribute('aria-pressed',on);$('usmap').classList.toggle('dropping',on);$('us-maphint').textContent=on?'Tap the map where you want your pin.':'Tap a dot to add it to your trip, see Street View or show its boundary. Zoom in to county level to see official federal and state boundaries; the layers button switches maps (Satellite + Streets + Official Boundaries) or turns the boundaries off.'}
function links(s){const sv=`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${s.la},${s.lo}`;
 const page=s.p==='POTA'?KPC.links.pota(s.c):s.p==='SOTA'?(s.url||KPC.links.sota(s.c)):s.p==='WWFF'?KPC.links.kff(s.c):'';
 return{sv,dir:KPC.links.dir(s.la,s.lo),page}}
function popup(s){const l=links(s),d=center?KPC.miles(center[0],center[1],s.la,s.lo):null;
 const what=s.p==='POTA'?'POTA park':s.p==='SOTA'?`SOTA summit${s.m?' • '+s.m.toLocaleString()+' m ('+Math.round(s.m*3.28084).toLocaleString()+' ft)':''}${s.pts?' • '+s.pts+' pts':''}`:s.p==='WWFF'?'WWFF reference':'Your pin';
 const div=`<div class="us-pop"><b>${esc(s.n)}</b><div class="meta">${s.p==='PIN'?'':esc(s.c)+' • '}${what}${d!=null?' • '+d.toFixed(1)+' mi away':''} • grid ${KPC.grid(s.la,s.lo).slice(0,6)}</div>
${kmBadge(s)?'<div style="margin:4px 0">'+kmBadge(s)+'</div>':''}<div class="pinfo"></div><div class="live"></div>
<div class="acts"><button type="button" class="go" data-a="add">${inTrip(s.c)?'&#10003; IN TRIP (REMOVE)':'+ ADD TO TRIP'}</button><a href="${l.sv}" target="_blank" rel="noopener">&#128064; STREET VIEW</a><a href="${l.dir}" target="_blank" rel="noopener">DIRECTIONS</a>${s.p==='POTA'||s.p==='WWFF'?`<a href="kpc-in-park.html?ref=${encodeURIComponent(s.c)}">📍 AM I IN THE PARK?</a>`:''}${s.p!=='PIN'&&s.p!=='SOTA'?`<a href="${/iPhone|iPad|iPod/.test(navigator.userAgent)?'https://maps.apple.com/?q=parking&sll='+s.la+','+s.lo+'&z=14':'https://www.google.com/maps/search/parking/@'+s.la+','+s.lo+',14z'}" target="_blank" rel="noopener">🅿 LOOK FOR PARKING</a>`:''}${s.p!=='PIN'&&s.p!=='SOTA'?'<button type="button" data-a="bound">SHOW THIS PARK\u2019S OUTLINE</button>':''}${l.page?`<a href="${l.page}" target="_blank" rel="noopener">${s.p} PAGE &#8599;</a>`:''}</div></div>`;
 return div}
/* official website + park type + how you can activate, for the states around Kentucky (data/parkinfo/US-XX.json, weekly from
   POTA by kpc-state-links.yml; automatic, not checked by KPC). The state comes from where the dot is. */
const PINFO={};
function stateAt(la,lo){const inR=(r)=>{let c=false;for(let i=0,j=r.length-1;i<r.length;j=i++){const xi=r[i][0],yi=r[i][1],xj=r[j][0],yj=r[j][1];if((yi>la)!==(yj>la)&&lo<(xj-xi)*(la-yi)/(yj-yi)+xi)c=!c}return c};
 const b=BORD.find(b=>b.p.some(pl=>inR(pl[0])));return b?b.a:''}
const ACT={Automobile:'car',Campground:'campground',Pedestrian:'on foot',Boat:'boat',Bicycle:'bike',Backpacking:'backpacking',Hiking:'hiking'};
const CFED={},AGN={FS:'Forest Service',NPS:'National Park Service',USACE:'Army Corps',BLM:'BLM',FWS:'Fish & Wildlife',TVA:'TVA',BOR:'Reclamation'};
const SOTAI={};let KFFROWS=null;
const hd=t=>`<div class="meta" style="margin:8px 0 3px;font-weight:800;letter-spacing:.5px">${t}</div>`;
const ln=t=>`<div class="meta" style="margin:2px 0">${t}</div>`;
const GENW=/\b(state|national|park|parks|forest|wildlife|management|area|recreation|historic|historical|site|refuge|preserve|nature|the|of|and|lake|river|scenic|wild|memorial|monument|conservation|wma|nwr|sp|np|nf)\b/g;
const nwords=t=>String(t||'').toLowerCase().replace(/[^a-z0-9 ]/g,' ').replace(GENW,' ').split(/\s+/).filter(w=>w.length>2);
const nsim=(a,b)=>{const A=nwords(a),B=new Set(nwords(b));if(!A.length||!B.size)return 0;return A.filter(w=>B.has(w)).length/Math.max(A.length,B.size)};
const ymd=d=>{const t=new Date(d);return isNaN(t)?'':t.toLocaleDateString([],{month:'short',day:'numeric',year:'numeric'})};
/* SOTA summit facts from api2.sota.org.uk (CORS ok): height, points, winter bonus, how often activated */
async function sotaFacts(s){const [a,r]=s.c.split('/');if(!(s.c in SOTAI))SOTAI[s.c]=fetch('https://api2.sota.org.uk/api/summits/'+encodeURIComponent(a)+'/'+encodeURIComponent(r)).then(x=>x.ok?x.json():null).catch(()=>null);
 const j=await SOTAI[s.c];let h='';
 if(j){const n=+j.activationCount||0;
  h+=ln(`<b>${j.points||s.pts||0} point${(j.points||s.pts)==1?'':'s'}</b>${+j.bonusPoints?` + ${j.bonusPoints} winter bonus`:''}${j.regionName?' · '+esc(j.regionName):''}`);
  h+=ln(n?`Activated <b>${n.toLocaleString()}</b> time${n===1?'':'s'}${j.activationDate?' · last '+esc(ymd(j.activationDate)):''}${j.activationCall?' by '+esc(j.activationCall):''}${n<=5?' · <b style="color:#b45309">RARE</b>':''}`:'<b style="color:#c2410c">Never activated: a SOTA "ATNO"!</b>')}
 else if(s.m)h+=ln(`${Math.round(s.m*3.28084).toLocaleString()} ft (${s.m.toLocaleString()} m) · ${s.pts||0} points`);
 h+=ln('Activation zone: within 25 m (82 ft) of the top, on foot (no vehicles). 4 contacts to score the points.');
 h+=`<div class="acts"><a href="kpc-in-park.html?ref=${encodeURIComponent(s.c)}">AM I IN THE ZONE?</a><a href="https://sotl.as/summits/${encodeURIComponent(s.c)}" target="_blank" rel="noopener">SOTLAS (ROUTES, PHOTOS) ↗</a></div>`;
 return h}
/* WWFF (KFF) facts from our weekly copy of the WWFF directory (data/wwff/KFF.json) */
async function wwffFacts(s){if(!KFFROWS)KFFROWS=fetch('data/wwff/KFF.json').then(r=>r.ok?r.json():[]).catch(()=>[]);
 const x=(await KFFROWS).find(r=>r[0]===s.c);let h='';
 if(x&&x[5]){const a=String(x[5]).replace(/^K-/,''),c=String(x[6]||'').replace(/^K-/,'');h+=ln(`WWFF (KFF) reference · ${esc(a)}${c&&c!==a?' · '+esc(c):''}`)}
 h+=ln('WWFF counts every contact you make there, and you can add up visits: 44 contacts for the WWFF award (KFF may accept fewer for its own awards; check wwff.us).');
 if(x&&x[4])h+=`<div class="acts">${x&&x[4]?`<a href="${esc(x[4])}" target="_blank" rel="noopener">OFFICIAL WEBSITE ↗</a>`:''}</div>`;
 return h}
async function parkInfo(s,el){if(!el||el.dataset.done)return;el.dataset.done=1;
 const P=s.p,sts=[...new Set([stateAt(s.la,s.lo),...statesNear(s.la,s.lo,3)])].filter(Boolean);let h='';
 if(P==='POTA')for(const st of sts){if(!(st in PINFO))PINFO[st]=fetch('data/parkinfo/US-'+st+'.json').then(r=>r.ok?r.json():null).catch(()=>null);
  const d=await PINFO[st];const p=d&&d.parks&&d.parks[s.c];if(!p)continue;
  const [,web,typ,act]=p,how=(act||'').split(',').map(x=>ACT[x.trim()]||x.trim().toLowerCase()).filter(Boolean);
  h=`<div class="meta" style="margin:6px 0 2px">${typ?esc(typ):''}${how.length?(typ?' · ':'')+'activate by '+esc(how.join(', ')):''}</div>`+
   `<div class="acts">${web?`<a href="${esc(web)}" target="_blank" rel="noopener">OFFICIAL WEBSITE ↗</a>`:''}${d.stateSite&&/State Park|State Forest|State Recreation/i.test(typ)?`<a href="${esc(d.stateSite)}" target="_blank" rel="noopener">${esc(st)} STATE PARKS SITE (CAMPING, MAPS) ↗</a>`:''}</div>`;break}
 if(P==='SOTA')h+=await sotaFacts(s);
 if(P==='WWFF')h+=await wwffFacts(s);
 /* Park Notes tips (Kentucky page or the other-states page; parks, summits and KFF references) */
 if(!window.__kpcNotes)window.__kpcNotes=Promise.all(['kpc-park-notes.json','kpc-park-notes-us.json'].map(u=>fetch(u).then(r=>r.ok?r.json():null).catch(()=>null)));
 {const [kyN,usN]=await window.__kpcNotes,nk=((kyN&&kyN.notes)||[]).filter(t=>t.ref===s.c).length,nu=((usN&&usN.notes)||[]).filter(t=>t.ref===s.c).length;
  const ky=nk||(!nu&&stateAt(s.la,s.lo)==='KY'),n=nk+nu,href=ky?'kpc-park-notes.html#'+encodeURIComponent(s.c):'kpc-park-notes-us.html?ref='+encodeURIComponent(s.c)+'#find';
  h+=`<div class="meta" style="margin:8px 0 2px;font-weight:800"><a href="${href}">📝 ${n?'PARK NOTES: '+n+' TIP'+(n===1?'':'S'):'PARK NOTES: BE THE FIRST TO ADD A TIP'} ›</a></div>`}
 /* federal campgrounds + picnic shelters within 10 miles (Recreation.gov, data/campfed/US-XX.json, weekly by kpc-fed-camps.yml) */
 const near=[];for(const st of [...new Set([...sts,...statesNear(s.la,s.lo,10)])]){if(!(st in CFED))CFED[st]=fetch('data/campfed/US-'+st+'.json').then(r=>r.ok?r.json():null).catch(()=>null);
  const d=await CFED[st];((d&&d.camps)||[]).forEach(c=>{const mi=KPC.miles(s.la,s.lo,c[2],c[3]);if(mi<=10&&!near.some(x=>x.c[0]===c[0]))near.push({c,mi})})}
 near.sort((a,b)=>a.mi-b.mi);
 const row=({c,mi})=>ln(`<a href="${esc(c[6])}" target="_blank" rel="noopener">${esc(c[1])} ↗</a> · ${mi<.3?'right there':mi.toFixed(1)+' mi'}${c[4]?' · '+esc(AGN[c[4]]||c[4]):''}${c[5]?' · can reserve':' · first come'}`);
 const cg=near.filter(x=>x.c[7]!=='s'),sh=near.filter(x=>x.c[7]==='s');
 if(cg.length)h+=hd('⛺ FEDERAL CAMPGROUNDS NEARBY (RECREATION.GOV)')+cg.slice(0,4).map(row).join('');
 if(sh.length&&P!=='SOTA')h+=hd('🧺 PICNIC SHELTERS NEARBY (SHADE + TABLE, GOOD FOR ACTIVATING)')+sh.slice(0,3).map(row).join('');
 /* the other programs at the same place */
 const sotaRows=so=>so.slice(0,4).map(x=>ln(`<a href="https://sotl.as/summits/${encodeURIComponent(x.ref)}" target="_blank" rel="noopener">${esc(x.ref)} ↗</a> ${esc(x.name)} · ${Number(x.ft).toLocaleString()} ft · ${x.pts} pt${x.pts==1?'':'s'} · ${(x.d/1.609).toFixed(1)} mi`)).join('')+(so.length>4?`<div class="meta" style="font-size:11px;opacity:.8">${so.length-4} more on the map (turn on SOTA).</div>`:'');
 if(window.KPCB){try{
  if(P==='POTA'){const [ww,so]=await Promise.all([KPCB.wwffNear(s.la,s.lo,12),KPCB.sotaNear(s.la,s.lo,4.83)]);
   const same=ww.map(w=>Object.assign({sc:nsim(s.n,w.name)},w)).filter(w=>w.sc>=.6||(w.d<.4&&w.sc>0)).sort((a,b)=>b.sc-a.sc||a.d-b.d).slice(0,1);
   if(same.length)h+=hd('🌲 ALSO A WWFF REFERENCE')+same.map(w=>ln(`<a href="https://wwff.co/directory/?showRef=${encodeURIComponent(w.ref)}" target="_blank" rel="noopener">${esc(w.ref)} ↗</a> ${esc(w.name)} · one activation can count for both (check the WWFF rules)`)).join('');
   if(so.length)h+=hd(`⛰ SOTA SUMMITS WITHIN 3 MILES (${so.length})`)+sotaRows(so)}
  if(P==='WWFF'){const pota=ALL.filter(x=>x.p==='POTA'&&Math.abs(x.la-s.la)<.12&&Math.abs(x.lo-s.lo)<.15).map(x=>({x,sc:nsim(x.n,s.n),d:KPC.miles(s.la,s.lo,x.la,x.lo)})).filter(o=>o.sc>=.6||(o.d<.25&&o.sc>0)).sort((a,b)=>b.sc-a.sc||a.d-b.d).slice(0,1);
   if(pota.length)h+=hd('🏞 ALSO A POTA PARK')+pota.map(o=>ln(`<a href="https://pota.app/#/park/${encodeURIComponent(o.x.c)}" target="_blank" rel="noopener">${esc(o.x.c)} ↗</a> ${esc(o.x.n)} · one activation can count for both`)).join('');
   const so=await KPCB.sotaNear(s.la,s.lo,4.83);if(so.length)h+=hd(`⛰ SOTA SUMMITS WITHIN 3 MILES (${so.length})`)+sotaRows(so)}
  if(P==='SOTA'){const pk=ALL.filter(x=>x.p==='POTA'&&Math.abs(x.la-s.la)<.06&&Math.abs(x.lo-s.lo)<.08).map(x=>({x,d:KPC.miles(s.la,s.lo,x.la,x.lo)})).filter(o=>o.d<=3).sort((a,b)=>a.d-b.d).slice(0,3);
   if(pk.length)h+=hd('🏞 POTA PARKS NEAR THE SUMMIT')+pk.map(o=>ln(`<a href="https://pota.app/#/park/${encodeURIComponent(o.x.c)}" target="_blank" rel="noopener">${esc(o.x.c)} ↗</a> ${esc(o.x.n)} · ${o.d.toFixed(1)} mi`)).join('')+'<div class="meta" style="font-size:11px;opacity:.8">A summit can count for POTA too when it is inside the park’s boundary: check with AM I IN THE ZONE?, or tap the park’s dot and SHOW THIS PARK’S OUTLINE.</div>'}
 }catch(e){}}
 if(h)el.innerHTML=h}
async function livePota(s,el){if(!el||el.dataset.done)return;el.dataset.done=1;el.textContent='Checking POTA…';
 try{const r=await fetch(`https://api.pota.app/park/activations/${s.c}?count=all`);if(!r.ok)throw 0;const j=await r.json();const a=Array.isArray(j)?j:[];
  if(!a.length){el.textContent='No activations yet: a new one for POTA!';return}
  const last=a.map(x=>String(x.qso_date||'')).sort().pop();const good=a.filter(x=>+x.totalQSOs>=10).length;
  el.textContent=`${a.length} activation attempt${a.length===1?'':'s'} (${good} with 10+ QSOs) • last ${KPC.fmtDate(last)}`}catch(e){el.textContent=''}}
function drawDots(){if(!map)return;dots.clearLayers();
 const show=center?vis():[];
 show.forEach(s=>{const inT=inTrip(s.c),km=KM?KM.mark(s.c):{};const mk=L.circleMarker([s.la,s.lo],{radius:BIG?(inT?9:s.p==='SOTA'?6:7)+(TAP?2:0):(inT?6:s.p==='SOTA'?3.5:4.5)+(TAP?1:0),weight:inT||km.atno||km.rare?3:2,color:inT?'#f0c96b':km.atno?'#c2410c':km.rare?'#e08a2c':'#ffffff',fillColor:COL[s.p],fillOpacity:km.done&&!inT?.35:.95}); /* white ring shows on satellite */
  const pp=L.popup({maxWidth:300}).setContent(popup(s));pp._kpc=s;mk.bindPopup(pp);mk.addTo(dots)});
 trip.filter(s=>s.p==='PIN').forEach(s=>{const mk=L.marker([s.la,s.lo],{icon:L.divIcon({className:'',html:'<div class="pin-us"></div>',iconSize:[16,16],iconAnchor:[8,16]})});const pp=L.popup({maxWidth:300}).setContent(popup(s));pp._kpc=s;mk.bindPopup(pp);mk.addTo(dots)})}

/* ---------- search ---------- */
function normRef(q){q=q.trim().toUpperCase().replace(/\s+/g,'');if(/^K-\d{4,5}$/.test(q))q='US-'+q.slice(2);return q}
async function search(q){q=q.trim();if(!q)return;$('us-hits').style.display='none';
 const ll=parseLL(q);if(ll){go(ll.la,ll.lo,ll.label);return}
 const ref=normRef(q);if(BYREF[ref]){const s=BYREF[ref];await go(s.la,s.lo,s.n);openSpot(s);return}
 const lq=q.toLowerCase();const parks=ALL.filter(s=>progs.includes(s.p)&&s.n.toLowerCase().includes(lq)).slice(0,8);
 status('Searching places…');let places=[];
 try{places=(await kpcGeocode(q)).map(g=>({lat:g.la,lon:g.lo,display_name:g.label}))}catch(e){}
 const items=[...places.map(p=>({t:'place',la:+p.lat,lo:+p.lon,n:p.display_name})),...parks.map(s=>({t:'spot',s}))];
 if(!items.length){status(`Nothing found for “${esc(q)}”. Try a town and state (“Berea KY”), a ZIP, or a park number.`);return}
 if(items.length===1){const i=items[0];if(i.t==='place')go(i.la,i.lo,i.n);else{await go(i.s.la,i.s.lo,i.s.n);openSpot(i.s)}return}
 status('Pick one:');const h=$('us-hits');h.style.display='block';
 h.innerHTML=items.map((i,k)=>i.t==='place'?`<button type="button" data-k="${k}">&#128205; ${esc(i.n.split(',').slice(0,3).join(','))}<small>Place</small></button>`:`<button type="button" data-k="${k}"><span class="dot" style="background:${COL[i.s.p]}"></span>${esc(i.s.n)}<small>${i.s.p} ${esc(i.s.c)}</small></button>`).join('');
 h.onclick=async e=>{const b=e.target.closest('button');if(!b)return;const i=items[+b.dataset.k];h.style.display='none';if(i.t==='place')go(i.la,i.lo,i.n.split(',').slice(0,2).join(','));else{await go(i.s.la,i.s.lo,i.s.n);openSpot(i.s)}}}
function openSpot(s){if(!map)return;let hit=null;dots.eachLayer(l=>{if(l.getPopup&&l.getPopup()&&l.getPopup()._kpc===s)hit=l});if(hit)hit.openPopup()}
async function go(la,lo,label){clearRoute();center=[la,lo];radius=+$('usr').value;store.set('kpcUsLast',{la,lo,label,r:radius});
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
 const NEAR0=allNear(),NEAR=vis();   /* inside this function NEAR means the filtered list */
 if(KM)KM.ensure(NEAR0.filter(s=>s.p!=='WWFF').map(s=>({ref:s.c,la:s.la,lo:s.lo})));LIST=NEAR;const hid=NEAR0.length-NEAR.length,hidTxt=hid?`, ${hid.toLocaleString()} hidden by your filters`:'';
 if(RT){$('near-th2').textContent='MILE / OFF ROUTE';$('near-h').textContent=`Along your route (${NEAR.length.toLocaleString()}${NEAR.length>150?', first 150 shown':''}${hidTxt})`;
  $('near-body').innerHTML=NEAR.slice(0,150).map((s,i)=>{const r=RT.info[s.c]||{};return`<tr><td><span class="dot" style="background:${COL[s.p]}"></span><a href="#" data-o="${i}" class="ref">${esc(s.c)}</a><br>${esc(s.n)}${kmBadge(s)?'<br>'+kmBadge(s):''}</td><td>mile ${Math.round(r.at||0)}<br><small class="muted">${(r.off||0).toFixed(1)} mi off</small></td><td><button type="button" class="add${inTrip(s.c)?' in':''}" data-i="${i}">${inTrip(s.c)?'&#10003; ADDED':'+ ADD'}</button></td></tr>`}).join('')||`<tr><td colspan="3" class="muted">${hid?'Everything near the route is hidden by NEW TO ME / ATNO. Turn a filter off or widen the distance.':'Nothing that close to the route. Try a wider distance.'}</td></tr>`;return}
 $('near-th2').textContent='MILES';
 $('near-h').textContent=`Nearby (${NEAR.length.toLocaleString()}${NEAR.length>150?', closest 150 shown':''}${hidTxt})`;
 $('near-body').innerHTML=NEAR.slice(0,150).map((s,i)=>`<tr><td><span class="dot" style="background:${COL[s.p]}"></span><a href="#" data-o="${i}" class="ref">${esc(s.c)}</a><br>${esc(s.n)}${kmBadge(s)?'<br>'+kmBadge(s):''}</td><td>${KPC.miles(center[0],center[1],s.la,s.lo).toFixed(1)}</td><td><button type="button" class="add${inTrip(s.c)?' in':''}" data-i="${i}">${inTrip(s.c)?'&#10003; ADDED':'+ ADD'}</button></td></tr>`).join('')||`<tr><td colspan="3" class="muted">${hid?'Everything here is hidden by NEW TO ME / ATNO. Turn a filter off or try a bigger distance.':'Nothing that close. Try a bigger distance.'}</td></tr>`}

/* ---------- along a route ----------
   Start and finish can be a town, ZIP, park number or GPS coordinates. The driving route comes from the public OSRM
   server (straight line if it is busy); every spot within the chosen distance of the route is listed in the order
   you reach it, with how far off the route it is. */
let RT=null,routeL=null;
function parseLL(q){const m=String(q).trim().match(/^([NS])?\s*(-?\d{1,2}(?:\.\d+)?)\s*°?\s*([NS])?\s*[,;\s]\s*([EW])?\s*(-?\d{1,3}(?:\.\d+)?)\s*°?\s*([EW])?$/i);if(!m)return null;
 let la=+m[2],lo=+m[5];const ns=(m[1]||m[3]||'').toUpperCase(),ew=(m[4]||m[6]||'').toUpperCase();if(ns==='S')la=-Math.abs(la);if(ew==='W')lo=-Math.abs(lo);
 if(!ew&&lo>60&&la>15&&la<72)lo=-lo; /* "37.5, 85.3" in the US almost always means west longitude */
 if(Math.abs(la)>90||Math.abs(lo)>180)return null;return{la,lo,label:la.toFixed(4)+', '+lo.toFixed(4)}}
let lastNom=0;
async function resolvePoint(q){q=String(q||'').trim();if(!q)return null;if(PICKED[q])return PICKED[q];const ll=parseLL(q);if(ll)return ll;
 const ref=normRef(q);if(BYREF[ref]){const s=BYREF[ref];return{la:s.la,lo:s.lo,label:s.n+' ('+s.c+')'}}
 try{const g=await kpcGeocode(q);if(g.length)return{la:g[0].la,lo:g[0].lo,label:g[0].label}}catch(e){}
 const lq=q.toLowerCase(),s=ALL.find(x=>x.n.toLowerCase().includes(lq));return s?{la:s.la,lo:s.lo,label:s.n}:null}
async function roadRoute(a,b){try{const c=new AbortController(),t=setTimeout(()=>c.abort(),20000);
  const r=await fetch(`https://router.project-osrm.org/route/v1/driving/${a.lo},${a.la};${b.lo},${b.la}?overview=simplified&geometries=geojson`,{signal:c.signal});clearTimeout(t);
  if(!r.ok)throw 0;const j=await r.json();const rt=j.routes&&j.routes[0];if(!rt||!rt.geometry)throw 0;
  return{pts:rt.geometry.coordinates.map(c=>[c[1],c[0]]),mi:rt.distance/1609.34,hrs:rt.duration/3600,road:true}}
 catch(e){return{pts:[[a.la,a.lo],[b.la,b.lo]],mi:KPC.miles(a.la,a.lo,b.la,b.lo),road:false}}}
function corridor(pts,w){const cum=[0];for(let i=1;i<pts.length;i++)cum.push(cum[i-1]+KPC.miles(pts[i-1][0],pts[i-1][1],pts[i][0],pts[i][1]));
 let s0=90,n0=-90,w0=180,e0=-180;pts.forEach(([a,b])=>{s0=Math.min(s0,a);n0=Math.max(n0,a);w0=Math.min(w0,b);e0=Math.max(e0,b)});
 const dLa=w/69,dLo=w/(69*Math.cos(((s0+n0)/2)*Math.PI/180));const out=[],info={};
 ALL.forEach(s=>{if(!progs.includes(s.p)||s.la<s0-dLa||s.la>n0+dLa||s.lo<w0-dLo||s.lo>e0+dLo)return;
  const k=Math.cos(s.la*Math.PI/180)*69.17;let best=1e9,at=0;
  for(let i=1;i<pts.length;i++){const ax=(pts[i-1][1]-s.lo)*k,ay=(pts[i-1][0]-s.la)*69,bx=(pts[i][1]-s.lo)*k,by=(pts[i][0]-s.la)*69,dx=bx-ax,dy=by-ay,L2=dx*dx+dy*dy;
   const t=L2?Math.max(0,Math.min(1,-(ax*dx+ay*dy)/L2)):0,px=ax+t*dx,py=ay+t*dy,d=Math.hypot(px,py);if(d<best){best=d;at=cum[i-1]+t*(cum[i]-cum[i-1])}}
  if(best<=w){out.push(s);info[s.c]={off:best,at}}});
 out.sort((a,b)=>info[a.c].at-info[b.c].at);return{list:out,info,total:cum[cum.length-1]}}
function clearRoute(){RT=null;if(routeL){routeL.remove();routeL=null}}
async function runRoute(){const fq=$('urf').value,tq=$('urt').value,w=+$('urw').value;store.set('kpcUsRoute',{f:fq,t:tq,w});
 if(!fq.trim()||!tq.trim()){status('Type where you start and where you finish.');return}
 status('Finding your start…');const A=await resolvePoint(fq);if(!A){status(`Couldn’t find “${esc(fq)}”. Try a town and state, a ZIP, a park number or GPS like 37.57, -84.29.`);return}
 status('Finding your finish…');const B=await resolvePoint(tq);if(!B){status(`Couldn’t find “${esc(tq)}”. Try a town and state, a ZIP, a park number or GPS like 37.57, -84.29.`);return}
 status('Working out the drive…');const R=await roadRoute(A,B);
 for(let i=0;i<R.pts.length;i+=Math.max(1,Math.floor(R.pts.length/12)))await addLive(R.pts[i][0],R.pts[i][1],w); /* newer POTA parks for the states the route crosses */
 const C=corridor(R.pts,w);if(ctrMk){ctrMk.remove();ctrMk=null}if(ring){ring.remove();ring=null}
 RT={pts:R.pts,info:C.info,A,B,w};center=[A.la,A.lo];NEAR=C.list;
 const n={POTA:0,SOTA:0,WWFF:0};NEAR.forEach(s=>n[s.p]++);const h=R.hrs?`, about ${Math.floor(R.hrs)} h ${Math.round(R.hrs%1*60)} min`:'';
 status(`<b>${NEAR.length.toLocaleString()}</b> spots within ${w} miles of your ${Math.round(R.road?R.mi:C.total)}-mile ${R.road?'drive'+h:'route (straight line: the road-route server was busy)'} from <b>${esc(A.label)}</b> to <b>${esc(B.label)}</b>: ${progs.map(p=>n[p].toLocaleString()+' '+p).join(', ')}. Listed in the order you reach them.`);
 if(map){if(routeL)routeL.remove();const pin=(p,t)=>L.marker([p.la,p.lo],{interactive:false,icon:L.divIcon({className:'',html:`<div class="rt-end">${t}</div>`,iconSize:[26,26],iconAnchor:[13,13]})});
  routeL=L.featureGroup([L.polyline(R.pts,{color:'#171717',weight:8,opacity:.55,interactive:false}),L.polyline(R.pts,{color:'#f0c96b',weight:4,interactive:false,dashArray:R.road?null:'8 8'}),pin(A,'A'),pin(B,'B')]).addTo(map);
  map.fitBounds(routeL.getBounds(),{padding:[24,24]})}
 drawDots();drawNear()}
function setSearchMode(m){const route=m==='route';$('usf').style.display=route?'none':'';$('urf-form').style.display=route?'':'none';
 [...$('us-modes').children].forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.m===m)));store.set('kpcUsMode',m)}

/* ---------- boundary (OpenStreetMap, on request) ---------- */
/* The main overpass-api.de server says it is overloaded and refuses requests at busy times, so try the free public
   mirrors it lists first (private.coffee and VK Maps, no rate limits), then the main one. A form POST avoids long URLs
   and needs no CORS preflight. Answers are remembered per park for this visit. */
const OVP=['https://overpass.private.coffee/api/interpreter','https://maps.mail.ru/osm/tools/overpass/api/interpreter','https://overpass-api.de/api/interpreter'];
const ovpCache={};
/* every failure is kept so the message can say exactly what each server answered */
const OVPN=['private.coffee','VK Maps','overpass-api.de'];
async function overpass(q,key){if(ovpCache[key])return ovpCache[key];const why=[];
 /* ask all three at once and take the first good answer (one at a time took up to 75 s when two were slow) */
 const ctl=OVP.map(()=>new AbortController());
 const one=(u,i)=>new Promise((ok,no)=>{const t=setTimeout(()=>ctl[i].abort(),22000);
  fetch(u,{method:'POST',body:'data='+encodeURIComponent(q),headers:{'Content-Type':'application/x-www-form-urlencoded'},signal:ctl[i].signal})
   .then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json()}).then(j=>{if(j&&Array.isArray(j.elements))ok(j);else throw new Error('bad answer')})
   .catch(e=>{why.push(OVPN[i]+': '+(e.name==='AbortError'?'timed out after 22 s':/^HTTP \d+/.test(e.message)?'server answered '+e.message.replace('HTTP ','')+({'429':' (too many requests)','406':' (request refused)','504':' (server overloaded)','503':' (server unavailable)','400':' (query not accepted)'}[e.message.slice(5)]||''):e.message==='bad answer'?'sent something that was not boundary data':'blocked or unreachable from this browser ('+(e.message||e.name)+')'));no(e)})
   .finally(()=>clearTimeout(t))});
 try{const j=await Promise.any(OVP.map(one));ctl.forEach(c=>{try{c.abort()}catch(e){}});ovpCache[key]=j;return j}catch(e){}
 const err=new Error('all servers failed');err.why=why;throw err}
function sim(a,b){const w=t=>new Set(String(t).toLowerCase().replace(/[^a-z0-9 ]/g,' ').split(/\s+/).filter(x=>x.length>2&&!['state','park','national','area','the','and','wildlife','management'].includes(x)));const A=w(a),B=w(b);let n=0;A.forEach(x=>{if(B.has(x))n++});return n/Math.max(1,Math.min(A.size,B.size))}
async function showBoundary(s,btn){
 /* on/off switch (Brandon Oct 16): tap again to hide this park's outline */
 if(bound&&boundRef===s.c){bound.remove();bound=null;boundRef='';btn.textContent='SHOW THIS PARK\u2019S OUTLINE';status('Outline hidden.');return}
 if(bound){bound.remove();bound=null}boundRef=s.c;btn.textContent='LOOKING…';btn.disabled=true;
 /* Canada (Oct 17): the official CPCAD outline saved by kpc-canada-bounds.yml (data/canada-bounds/<REF>.json) */
 if(/^CA-/.test(s.c)){try{const r=await fetch('data/canada-bounds/'+encodeURIComponent(s.c)+'.json');if(r.ok){const f=await r.json();
   bound=L.geoJSON(f,{interactive:false,style:{color:'#f0c96b',weight:3,fillColor:'#f0c96b',fillOpacity:.15}}).addTo(map);
   const nm=(f.properties&&f.properties.cpcad)||s.n;btn.textContent='HIDE OUTLINE ('+String(nm).toUpperCase().slice(0,28)+')';btn.disabled=false;
   try{map.fitBounds(bound.getBounds(),{maxZoom:14,padding:[20,20]})}catch(e){}
   status(`Official boundary shown: <b>${esc(nm)}</b> (Canadian Protected and Conserved Areas Database, Government of Canada, Open Government Licence). POTA goes by the official boundary; check the park's own map too.`);return}}catch(e){}}
 /* official first: USGS PAD-US by the park's name near its pin (kpc-bounds.js), then OpenStreetMap */
 if(window.KPCB&&s.p!=='SOTA'){try{const fs=await KPCB.padusByName(s.n,s.la,s.lo);if(fs&&fs.length){
   bound=L.geoJSON({type:'FeatureCollection',features:fs},{interactive:false,style:{color:'#f0c96b',weight:3,fillColor:'#f0c96b',fillOpacity:.15}}).addTo(map);
   const nm=fs[0]._nm||s.n;btn.textContent='HIDE OUTLINE ('+String(nm).toUpperCase().slice(0,28)+')';btn.disabled=false;
   try{map.fitBounds(bound.getBounds(),{maxZoom:14,padding:[20,20]})}catch(e){}
   status(`Official boundary shown: <b>${esc(nm)}</b> (USGS PAD-US). POTA goes by the official boundary; check the park's own map too.`);return}}catch(e){}}
 const bb=`${(s.la-.3).toFixed(4)},${(s.lo-.4).toFixed(4)},${(s.la+.3).toFixed(4)},${(s.lo+.4).toFixed(4)}`; /* outline kept to ~20 miles around the park: much less data than a whole forest */
 const q=`[out:json][timeout:20];is_in(${s.la},${s.lo})->.a;(way(pivot.a)["boundary"~"protected_area|national_park"];rel(pivot.a)["boundary"~"protected_area|national_park"];way(pivot.a)["leisure"~"park|nature_reserve"];rel(pivot.a)["leisure"~"park|nature_reserve"];);out geom(${bb});`;
 try{const j=await overpass(q,s.c);const els=(j.elements||[]).filter(e=>e.tags);if(!els.length){btn.textContent='NO OUTLINE IN OPENSTREETMAP';return}
  const area=e=>{const g=e.type==='way'?e.geometry:(e.members||[]).flatMap(m=>m.geometry||[]);if(!g||!g.length)return 1e9;let a=1e9,c=-1e9,d=1e9,f=-1e9;g.forEach(p=>{if(!p)return;a=Math.min(a,p.lat);c=Math.max(c,p.lat);d=Math.min(d,p.lon);f=Math.max(f,p.lon)});return(c-a)*(f-d)};
  els.sort((x,y)=>(sim(s.n,y.tags.name||'')-sim(s.n,x.tags.name||''))||(area(x)-area(y)));const e=els[0];
  const lines=[];if(e.type==='way'&&e.geometry)lines.push(e.geometry.filter(Boolean).map(p=>[p.lat,p.lon]));
  else(e.members||[]).forEach(m=>{if(m.type==='way'&&m.geometry)lines.push(m.geometry.filter(Boolean).map(p=>[p.lat,p.lon]))});
  bound=L.featureGroup(lines.filter(l=>l.length>1).map(l=>{const closed=l.length>3&&l[0][0]===l[l.length-1][0]&&l[0][1]===l[l.length-1][1];return closed?L.polygon(l,{color:'#f0c96b',weight:3,fillColor:'#f0c96b',fillOpacity:.12,interactive:false}):L.polyline(l,{color:'#f0c96b',weight:3,interactive:false})})).addTo(map);
  btn.textContent='HIDE OUTLINE (NOT OFFICIAL)';btn.disabled=false;status(`No official boundary found, so this outline is from OpenStreetMap (a volunteer map, not official): <b>${esc(e.tags.name||'unnamed area')}</b>${sim(s.n,e.tags.name||'')<.5?' (closest match: it may not be the exact POTA park area)':''}.`)}
 catch(err){btn.textContent='BOUNDARY NOT AVAILABLE, TAP TO TRY AGAIN';{const pop=btn.closest('.us-pop');if(pop){let w=pop.querySelector('.bwhy');if(!w){w=document.createElement('div');w.className='bwhy';w.style.cssText='font-size:11px;color:#b5452b;margin-top:6px;line-height:1.4';pop.appendChild(w)}w.textContent='Why: '+(err.why||[err.message]).join(' \u2022 ')}}status('Boundary lookup failed. What each server said: <b>'+esc((err.why||[err.message]).join(' \u2022 '))+'</b>. Send a screenshot of this to the site admin. Meanwhile try the <b>Satellite + Park Lines (Beta)</b> map in the layers button.');btn.disabled=false;return}btn.disabled=false}

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
/* suggestions as you type (Brandon Oct 16: 'no predictive text on us planner'): parks / summits / WWFF from our list
   right away, then towns and ZIP codes anywhere in the US (kpc-place-suggest.js, Open-Meteo) */
if(window.KPCPlace){
 const KIND={POTA:'POTA park',SOTA:'SOTA summit',WWFF:'WWFF reference'};
 const local=q=>{const l=q.toLowerCase(),r=normRef(q);const hit=ALL.filter(s=>progs.includes(s.p)&&(s.c.toUpperCase()===r||s.c.toUpperCase().startsWith(r)&&r.length>3||s.n.toLowerCase().includes(l)));
  hit.sort((a,b)=>(b.n.toLowerCase().startsWith(l)-a.n.toLowerCase().startsWith(l))||a.n.localeCompare(b.n));
  return hit.slice(0,7).map(s=>({v:s.n,k:KIND[s.p]+' · '+s.c,la:s.la,lo:s.lo,s}))};
 KPCPlace.box($('usq'),{local,remote:true,onPick:async x=>{if(x.s){$('usq').value=x.s.n;await go(x.s.la,x.s.lo,x.s.n);openSpot(x.s)}else go(x.la,x.lo,x.v)}});
 ['urf','urt'].forEach(id=>KPCPlace.box($(id),{local,remote:true,onPick:x=>{PICKED[x.v]={la:x.la,lo:x.lo,label:x.s?x.s.n+' ('+x.s.c+')':x.v}}}));
}
$('usr').onchange=()=>{if(center)go(center[0],center[1],(store.get('kpcUsLast',{})||{}).label)};
{const bb=$('us-big');if(bb){bb.setAttribute('aria-pressed',String(BIG));bb.onclick=()=>{BIG=!BIG;store.set('kpcUsBig',BIG);bb.setAttribute('aria-pressed',String(BIG));drawDots()}}}   /* bigger dots chip (small = default, Brandon Oct 16) */
$('us-progs').onclick=e=>{const b=e.target.closest('button[data-p]');if(!b)return;const p=b.dataset.p;progs=progs.includes(p)?progs.filter(x=>x!==p):progs.concat(p);if(!progs.length)progs=[p];store.set('kpcUsProgs',progs);
 [...$('us-progs').querySelectorAll('[data-p]')].forEach(x=>x.setAttribute('aria-pressed',progs.includes(x.dataset.p)));if(RT){const C=corridor(RT.pts,RT.w);RT.info=C.info;NEAR=C.list;drawDots();drawNear();status(`<b>${NEAR.length.toLocaleString()}</b> spots within ${RT.w} miles of your route.`)}else if(center)go(center[0],center[1],(store.get('kpcUsLast',{})||{}).label)};
$('us-me').onclick=()=>{if(!navigator.geolocation){status('This browser can’t share your location.');return}status('Finding you…');
 navigator.geolocation.getCurrentPosition(p=>go(fix(p.coords.latitude),fix(p.coords.longitude),'you'),()=>status('Location was blocked or unavailable. Type a town or ZIP instead.'),{timeout:15000,maximumAge:300000})};
$('us-drop').onclick=()=>setDrop(!dropMode);
$('us-modes').onclick=e=>{const b=e.target.closest('button');if(b)setSearchMode(b.dataset.m)};
$('urf-form').onsubmit=e=>{e.preventDefault();runRoute()};
$('urw').onchange=()=>{if(RT){const C=corridor(RT.pts,+$('urw').value);RT.w=+$('urw').value;RT.info=C.info;NEAR=C.list;drawDots();drawNear();status(`<b>${NEAR.length.toLocaleString()}</b> spots within ${RT.w} miles of your route.`)}};
{const r=store.get('kpcUsRoute',null);if(r){$('urf').value=r.f||'';$('urt').value=r.t||'';if(r.w)$('urw').value=String(r.w)}setSearchMode(store.get('kpcUsMode','place'))}
$('near-body').onclick=e=>{const a=e.target.closest('[data-i]'),o=e.target.closest('[data-o]');
 if(a){const s=LIST[+a.dataset.i];inTrip(s.c)?removeStop(s.c):addStop(s)}
 if(o){e.preventDefault();const s=LIST[+o.dataset.o];map&&map.setView([s.la,s.lo],Math.max(map.getZoom(),11));setTimeout(()=>openSpot(s),300);$('usmap').scrollIntoView({behavior:'smooth',block:'center'})}};
$('trip-list').onclick=e=>{const b=e.target.closest('button');if(!b)return;const i=+(b.dataset.u??b.dataset.d??b.dataset.x);
 if(b.dataset.x!=null)return removeStop(trip[i].c);const j=b.dataset.u!=null?i-1:i+1;if(j<0||j>=trip.length)return;[trip[i],trip[j]]=[trip[j],trip[i]];saveTrip();drawTrip()};
$('t-order').onclick=bestOrder;
/* 📴 SAVE TRIP FOR NO SIGNAL (kpc-trip-offline.js): page, data for the stops' states and the street map around each stop */
if($('t-off'))$('t-off').onclick=()=>{if(!window.KPCTripOffline)return;const stops=trip.filter(s=>isFinite(s.la)&&isFinite(s.lo));
 if(!stops.length){$('t-offmsg').textContent='Add some stops first.';return}
 const st=[...new Set(stops.flatMap(s=>[stateAt(s.la,s.lo),...statesNear(s.la,s.lo,10)]).filter(Boolean))];
 const files=['locations.json','kpc-us-states.json','kpc-park-notes.json','kpc-park-notes-us.json','data/trails/index.json','KPC-logo.png'].concat(st.flatMap(x=>['data/parkinfo/US-'+x+'.json','data/campfed/US-'+x+'.json']));
 KPCTripOffline.save({stops,files,msg:$('t-offmsg'),btn:$('t-off'),key:'kpcUsTripSaved'})};
if(window.KPCTripOffline&&KPCTripOffline.offline())setTimeout(()=>status('📴 <b>No signal.</b> Showing your saved trip. The Street map works around the stops you saved; searching and live POTA info come back with signal.'),1500);
$('t-road').onclick=drawRoad;$('t-gpx').onclick=gpx;$('t-share').onclick=share;$('t-fromme').onchange=drawTrip;
$('t-clear').onclick=()=>{if(confirm('Clear all stops from this trip?')){trip=[];saveTrip();if(road){road.remove();road=null}drawTrip();drawDots();drawNear()}};
[...$('us-progs').querySelectorAll('[data-p]')].forEach(x=>x.setAttribute('aria-pressed',progs.includes(x.dataset.p)));
initMap();
/* new checker answers: the list redraws at once; map dots wait until an open popup is closed so it doesn't vanish */
if(KM){KM.bar($('km-bar'));let pend=false;
 window.addEventListener('kpcmine',()=>{if(!center)return;drawNear();if(map&&map._popup&&map.hasLayer(map._popup)){pend=true;return}drawDots()});
 if(map)map.on('popupclose',()=>{if(pend){pend=false;setTimeout(drawDots,0)}})}
loadAll().then(()=>{const shared=loadShared();drawTrip();
 /* ?q=… (sent by the KY Trip Planner for an out-of-state place): search it straight away */
 const qp=new URLSearchParams(location.search).get('q');if(qp&&!shared){$('usq').value=qp;search(qp);return}
 const last=store.get('kpcUsLast',null);if(last&&isFinite(last.la)){$('usr').value=String(last.r||25);go(last.la,last.lo,last.label)}
 else if(shared&&trip.length){go(trip[0].la,trip[0].lo,trip[0].n)}
 else status(`${ALL.length.toLocaleString()} POTA parks, SOTA summits and WWFF references ready. Search a town, ZIP or park to start.`);
 if(shared&&map&&trip.length)map.fitBounds(L.latLngBounds(trip.map(s=>[s.la,s.lo])),{padding:[30,30],maxZoom:11})})
 .catch(()=>status('Could not load the park list. Check your connection and refresh.'));
})();

/* ⛶ FULL / ✕ EXIT button (same as the Kit / Info Finder / In-Park maps; Esc exits) */
function kpcFullBtn(map,pos){if(!window.L||!map)return;if(!document.getElementById('kpc-full-css')){const c=document.createElement('style');c.id='kpc-full-css';
 c.textContent='.kfull-b{min-height:36px;padding:6px 10px;border:2px solid rgba(0,0,0,.25);border-radius:6px;background:#fff;color:#1378ff;font:900 12px Arial,sans-serif;letter-spacing:.6px;cursor:pointer}.kmap-full{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important;height:100dvh!important;max-height:none!important;min-height:0!important;margin:0!important;border-radius:0!important;z-index:5000!important}html.kmap-lock,html.kmap-lock body{overflow:hidden!important}';document.head.appendChild(c)}
 const box=map.getContainer();let on=false,ph=null;
 const C=L.Control.extend({options:{position:pos||'topleft'},onAdd(){const b=L.DomUtil.create('button','kfull-b');b.type='button';b.title='Full screen map';b.innerHTML='⛶ FULL';L.DomEvent.disableClickPropagation(b);
  const set=v=>{on=v;box.classList.toggle('kmap-full',on);document.documentElement.classList.toggle('kmap-lock',on);b.innerHTML=on?'✕ EXIT':'⛶ FULL';b.title=on?'Exit full screen':'Full screen map';if(on)ph=window.scrollY;else if(ph!=null)window.scrollTo(0,ph);setTimeout(()=>map.invalidateSize(),60)};
  b.onclick=()=>set(!on);document.addEventListener('keydown',e=>{if(on&&e.key==='Escape')set(false)});return b}});new C().addTo(map)}
