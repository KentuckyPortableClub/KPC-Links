/* KPC Tools — shared code.
   CLUB ROSTER: the MEMBERS line below is the ONLY place to add or remove a member.
   Every page (Live, On The Air, Tool Box, Members, Campout, Discord page) and the Discord spot bot read it.
   Use plain callsigns in single quotes, e.g. ['KZ4CP','N4BDW','NEW1CALL'] */
const KPC=(()=>{
const MEMBERS=['KZ4CP','N4BDW','KQ4HZK','K4ZSR'];
const API='https://api.pota.app';
const CACHE_KEY='kpcHistory_v1', CACHE_HOURS=12;
let _data,_counties;
const esc=t=>String(t??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const base=c=>String(c||'').toUpperCase().trim().split('/').reduce((a,b)=>b.length>a.length?b:a,'');
const isMember=c=>MEMBERS.includes(base(c));
function miles(a,b,c,d){const R=3958.8,r=Math.PI/180,x=(c-a)*r,y=(d-b)*r,h=Math.sin(x/2)**2+Math.cos(a*r)*Math.cos(c*r)*Math.sin(y/2)**2;return 2*R*Math.asin(Math.sqrt(h))}
function grid(lat,lon){lon+=180;lat+=90;const A='ABCDEFGHIJKLMNOPQR',a='abcdefghijklmnopqrstuvwx';
 const f1=Math.floor(lon/20),f2=Math.floor(lat/10),s1=Math.floor((lon%20)/2),s2=Math.floor(lat%10),
 t1=Math.floor(((lon%2)*60)/5),t2=Math.floor(((lat%1)*60)/2.5);return A[f1]+A[f2]+s1+s2+a[t1]+a[t2]}
function pip(x,y,ring){let ins=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const[xi,yi]=ring[i],[xj,yj]=ring[j];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi+1e-15)+xi)ins=!ins}return ins}
/* POTA's current list of Kentucky parks (cached for a day). Parks POTA adds after kpc-ky-data.json was last
   updated are added automatically with basic info (name, location, county, a type guessed from the name).
   Hand-added details (parking, websites, 2-fers, trails) still come from kpc-ky-data.json. */
const LIVE_KEY='kpcLiveKY';let _live;
function liveKY(wait){if(_live)return _live;
 _live=(async()=>{let c=null;try{c=JSON.parse(localStorage.getItem(LIVE_KEY)||'null')}catch(e){}
  if(c&&Array.isArray(c.rows)&&Date.now()-c.t<864e5)return c.rows;
  const ctl=typeof AbortController!=='undefined'?new AbortController():null;
  const net=fetch(API+'/location/parks/US-KY',ctl?{signal:ctl.signal}:{}).then(r=>{if(!r.ok)throw 0;return r.json()}).then(j=>{
   const rows=(Array.isArray(j)?j:[]).map(x=>[String(x.reference||'').toUpperCase(),String(x.name||'').trim(),+x.latitude,+x.longitude]).filter(r=>/^US-\d+$/.test(r[0])&&r[1]&&isFinite(r[2])&&isFinite(r[3])&&r[2]!==0);
   if(rows.length>50){try{localStorage.setItem(LIVE_KEY,JSON.stringify({t:Date.now(),rows}))}catch(e){}return rows}return null}).catch(()=>null);
  const r=await Promise.race([net,new Promise(res=>setTimeout(()=>res(undefined),wait||3000))]);
  if(r===undefined)net.then(()=>{});/* keep going in the background so the next visit has it */
  return r||(c&&Array.isArray(c.rows)?c.rows:[])})();
 return _live}
const guessType=n=>/WMA|Wildlife Management/i.test(n)?'WMA':/State (Resort |Historic )?Park|State Historic Site/i.test(n)?'State Park':/Nature Preserve|Natural Area/i.test(n)?'Nature Preserve':/State Forest/i.test(n)?'State Forest':/National Forest/i.test(n)?'National Forest':/National Recreation Area/i.test(n)?'National Recreation Area':/National|NPS/i.test(n)?'National / NPS':/Trail/i.test(n)?'Trail':'Other';
async function data(){if(!_data)_data=Promise.all([fetch('kpc-ky-data.json').then(r=>r.json()),liveKY().catch(()=>[])]).then(async([d,rows])=>{
  const have=new Set(d.parks.map(p=>p.c));d.newParks=[];
  for(const[c,n,la,lo]of rows){if(have.has(c))continue;have.add(c);let co='';try{co=await countyOf(la,lo)||''}catch(e){}
   d.parks.push({c,n,co,t:guessType(n),la,lo,web:'',off:'',camp:null,tf:[],kff:[],sota:[],acc:0,ap:[],nw:1});d.newParks.push(c)}
  return d});return _data}
async function counties(){if(!_counties)_counties=fetch('kpc-ky-counties.json').then(r=>r.json());return _counties}
async function countyOf(lat,lon){const C=await counties();for(const c of C)if(c.r.some(r=>pip(lon,lat,r)))return c.n;return null}
const fmtDate=d=>{d=String(d);return d.length===8?new Date(+d.slice(0,4),+d.slice(4,6)-1,+d.slice(6,8)).toLocaleDateString([],{month:'short',day:'numeric',year:'numeric'}):d};
const ok=q=>q>=10;
const cty=c=>{c=String(c||'');if(/^multiple/i.test(c)||/see official/i.test(c))return c.replace(/^see official site$/i,'County: see official site')||'';return c+(c.includes('/')?' Counties':' County')}; // a valid POTA activation is 10+ QSOs

/* Activation history for every Kentucky park in the guide.
   Returns {ref:[[callsign,yyyymmdd,qsos],...]} — cached in this browser for 12 hours. */
async function history(onProgress,force){
 const D=await data(),refs=D.parks.map(p=>p.c);
 if(!force){try{const c=JSON.parse(localStorage.getItem(CACHE_KEY)||'null');if(c&&Date.now()-c.t<CACHE_HOURS*36e5&&Object.keys(c.d).length>=refs.length*0.9){const miss=refs.filter(r=>!c.d[r]);
   if(miss.length&&miss.length<=20){await Promise.all(miss.map(async ref=>{try{const r=await fetch(`${API}/park/activations/${ref}?count=all`);if(!r.ok)throw 0;const j=await r.json();c.d[ref]=(Array.isArray(j)?j:[]).map(a=>[String(a.activeCallsign||'').toUpperCase(),String(a.qso_date||''),+a.totalQSOs||0])}catch(e){c.d[ref]=[]}}));try{localStorage.setItem(CACHE_KEY,JSON.stringify(c))}catch(e){}}
   onProgress&&onProgress(refs.length,refs.length,c.t);return{hist:c.d,time:c.t,failed:c.f||[]}}}catch(e){}}
 const out={},failed=[];let done=0,i=0;
 async function worker(){while(i<refs.length){const ref=refs[i++];
  try{const r=await fetch(`${API}/park/activations/${ref}?count=all`);if(!r.ok)throw 0;const j=await r.json();
   out[ref]=(Array.isArray(j)?j:[]).map(a=>[String(a.activeCallsign||'').toUpperCase(),String(a.qso_date||''),+a.totalQSOs||0])}
  catch(e){failed.push(ref);out[ref]=[]}
  done++;onProgress&&onProgress(done,refs.length)}}
 await Promise.all(Array.from({length:6},worker));
 if(failed.length>=refs.length)throw new Error('POTA could not be reached');
 const t=Date.now();try{localStorage.setItem(CACHE_KEY,JSON.stringify({t,d:out,f:failed}))}catch(e){}
 return{hist:out,time:t,failed};
}
function progressUI(el){return(d,n,cached)=>{el.classList.add('on');el.querySelector('i').style.width=(100*d/n)+'%';
 el.querySelector('small').textContent=cached?`Loaded saved POTA data from ${new Date(cached).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'})} • refreshes every ${CACHE_HOURS} hours`:`Loading POTA activation history… ${d} of ${n} Kentucky parks`;
 if(d>=n&&cached)setTimeout(()=>{},0)}}
function navToggle(){const t=document.querySelector('.menu-toggle'),n=document.querySelector('.nav-links');if(!t||document.getElementById('kpcNavMore'))return;
 t.addEventListener('click',()=>{const o=n.classList.toggle('open');t.setAttribute('aria-expanded',String(o))})}
function leafletMap(id){const m=L.map(id,{scrollWheelZoom:false}).setView([37.75,-85.7],7);
 const st=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'© OpenStreetMap contributors'});
 const base={'Street':st};
 try{base['Terrain']=L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'© OpenTopoMap (CC-BY-SA), © OpenStreetMap contributors'});
  base['Satellite']=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery © Esri, Maxar, Earthstar Geographics'});
  const over={},pad=window.KPCPadMenu?KPCPadMenu(m,base,over):null;   /* official PAD-US boundaries (kpc-padus-layer.js) */
  let want='Street';try{want=localStorage.getItem('kpcBaseMap')||'Street'}catch(e){}
  (base[want]||st).addTo(m);if(pad&&want===pad.NAME)pad.layer.addTo(m);L.control.layers(base,pad?over:null,{position:'topright',collapsed:true}).addTo(m);
  m.on('baselayerchange',e=>{try{localStorage.setItem('kpcBaseMap',e.name)}catch(x){}})}catch(e){st.addTo(m)}
 return m}
async function countyLayer(m){const C=await counties();const g=L.layerGroup();
 C.forEach(c=>c.r.forEach(r=>L.polygon(r.map(([x,y])=>[y,x]),{color:'#1d5a3a',weight:.7,opacity:.55,fill:false,interactive:false}).addTo(g)));g.addTo(m);return g}
const links={pota:r=>`https://pota.app/#/park/${r}`,sota:r=>`https://sotl.as/summits/${r}`,kff:r=>`https://logsearch.wwff.co/directory/${r}`,
 qrz:c=>`https://www.qrz.com/db/${encodeURIComponent(base(c))}`,gmap:(a,b)=>`https://www.google.com/maps/search/?api=1&query=${a},${b}`,
 dir:(a,b,o)=>`https://www.google.com/maps/dir/?api=1${o?`&origin=${o[0]},${o[1]}`:''}&destination=${a},${b}`,wx:(a,b)=>`https://weather.com/weather/today/l/${a},${b}`};
document.addEventListener('DOMContentLoaded',navToggle);
return{MEMBERS,liveKY,esc,base,isMember,miles,grid,data,counties,countyOf,history,progressUI,leafletMap,countyLayer,links,fmtDate,ok,cty};
})();
/* KPC popup fit (shared; identical copy in kpc-tools.js and kpc-map-extras.js, runs once).
   Keeps map popups fully visible: clear of the map edges AND the sticky site menu bar, re-checked when popup
   content grows after it opens (live data, boundary text), and taller popups scroll instead of running off. */
(function(){if(!window.L||!L.Map||window.__kpcPopFit)return;window.__kpcPopFit=true;
 /* Keep every map inside its own layer so the site menu always opens on top of it, and while a card is open
    let the card sit above the map buttons (zoom, map type, Street View) so it is never hidden behind them. */
 try{const st=document.createElement('style');st.textContent='.leaflet-container{isolation:isolate}.kx-popopen .leaflet-control-container .leaflet-top,.kx-popopen .leaflet-control-container .leaflet-bottom{z-index:350!important}';document.head.appendChild(st)}catch(e){}
 function navBottom(){const n=document.querySelector('.site-nav');if(!n)return 0;const cs=getComputedStyle(n);if(!/sticky|fixed/.test(cs.position))return 0;return n.getBoundingClientRect().bottom}
 function fit(p){const m=p&&p._map,c=p&&p._container;if(!m||!c||!c.isConnected)return;
  const mr=m.getContainer().getBoundingClientRect(),cr=c.getBoundingClientRect();
  const top=Math.max(mr.top,navBottom())+12,left=mr.left+10,right=mr.right-10,bottom=mr.bottom-10;
  let dx=0,dy=0;if(cr.top<top)dy=cr.top-top;else if(cr.bottom>bottom&&cr.top-(cr.bottom-bottom)>=top)dy=cr.bottom-bottom;
  if(cr.left<left)dx=cr.left-left;else if(cr.right>right)dx=cr.right-right;
  if(Math.abs(dx)>2||Math.abs(dy)>2)m.panBy([Math.round(dx),Math.round(dy)],{animate:true,duration:.25})}
 function cap(p){const m=p._map,c=p._container;if(!m||!c)return;const w=c.querySelector('.leaflet-popup-content-wrapper'),body=c.querySelector('.leaflet-popup-content');if(!w||!body)return;
  const mr=m.getContainer().getBoundingClientRect(),room=Math.max(140,mr.bottom-Math.max(mr.top,navBottom())-70);
  body.style.maxHeight=room+'px';body.style.overflowY='auto'}
 L.Map.addInitHook(function(){const map=this;
  /* Hover cards (Park Commander, KY planner) set autoPan:false on purpose so the map holds still under the mouse;
     once a card is tapped or clicked it is pinned (autoPan:true) and is then moved fully into view. */
  map.on('popupopen',e=>{const p=e.popup;map.getContainer().classList.add('kx-popopen');cap(p);const go=()=>{if(p.options.autoPan!==false)fit(p)};setTimeout(go,40);setTimeout(go,400);
   clearInterval(p._kpcW);if(p.options.autoPan===false)p._kpcW=setInterval(()=>{if(!p._map){clearInterval(p._kpcW);return}if(p.options.autoPan!==false){clearInterval(p._kpcW);fit(p)}},250);
   if(window.ResizeObserver&&p._container){if(p._kpcRO)p._kpcRO.disconnect();let t=0;p._kpcRO=new ResizeObserver(()=>{clearTimeout(t);t=setTimeout(()=>{cap(p);go()},60)});p._kpcRO.observe(p._container)}});
  map.on('popupclose',e=>{const p=e.popup;setTimeout(()=>{if(!map.getContainer().querySelector('.leaflet-popup'))map.getContainer().classList.remove('kx-popopen')},50);if(!p)return;clearInterval(p._kpcW);if(p._kpcRO){p._kpcRO.disconnect();p._kpcRO=null}})})})();
/* KPC place + address lookup (shared by both trip planners).
   Street addresses ("123 Main St, Berea KY") go to the US Census geocoder first (JSONP: it allows that, not plain
   fetch), then OpenStreetMap Nominatim, then Photon. Towns and landmarks go to Nominatim first.
   opts.ky: look inside Kentucky first. Returns [{la,lo,label}] (best first) or []. */
window.kpcGeocode=window.kpcGeocode||(function(){let lastNom=0,seq=0;
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 function census(q){return new Promise(res=>{const cb='__kpcCensus'+(++seq),s=document.createElement('script');let done=false;
  const end=v=>{if(done)return;done=true;try{delete window[cb]}catch(e){window[cb]=undefined}s.remove();res(v)};
  window[cb]=j=>{const m=((j&&j.result&&j.result.addressMatches)||[]).map(a=>({la:+a.coordinates.y,lo:+a.coordinates.x,label:String(a.matchedAddress||q)})).filter(a=>isFinite(a.la)&&isFinite(a.lo));end(m)};
  s.onerror=()=>end([]);setTimeout(()=>end([]),12000);
  s.src='https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?benchmark=Public_AR_Current&format=jsonp&callback='+cb+'&address='+encodeURIComponent(q);document.head.appendChild(s)})}
 async function nominatim(q,ky){const out=[];const base='https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=us&limit=5&q='+encodeURIComponent(q);
  for(const u of ky?[base+'&viewbox=-89.6,39.2,-81.9,36.4&bounded=1',base]:[base]){const w=1100-(Date.now()-lastNom);if(w>0)await wait(w);lastNom=Date.now();
   try{const r=await fetch(u,{headers:{'Accept-Language':'en'}});if(r.ok){const j=await r.json();(j||[]).forEach(p=>out.push({la:+p.lat,lo:+p.lon,label:String(p.display_name||q).split(',').slice(0,3).join(',')}))}}catch(e){}
   if(out.length)break}return out}
 async function photon(q){try{const r=await fetch('https://photon.komoot.io/api/?limit=5&lang=en&q='+encodeURIComponent(q));if(!r.ok)return[];const j=await r.json();
  return(j.features||[]).filter(f=>f.properties&&/^us$/i.test(f.properties.countrycode||'')).map(f=>{const p=f.properties;return{la:+f.geometry.coordinates[1],lo:+f.geometry.coordinates[0],label:[[p.housenumber,p.street].filter(Boolean).join(' ')||p.name,p.city||p.county,p.state].filter(Boolean).join(', ')}})}catch(e){return[]}}
 const strip=q=>q.replace(/\b(apt|apartment|unit|suite|ste|lot|#)\s*[\w-]+/gi,'').replace(/(\d{5})-\d{4}/,'$1').replace(/\s+,/g,',').replace(/\s{2,}/g,' ').trim();
 return async function(q,opts){q=String(q||'').trim();if(!q)return[];opts=opts||{};const addr=/^\d+[A-Za-z]?\s+\S+/.test(q),c=strip(q);
  const steps=addr?[()=>census(c),()=>nominatim(c,opts.ky),()=>photon(c)]:[()=>nominatim(q,opts.ky),()=>photon(q)];
  for(const st of steps){const r=await st();if(r&&r.length)return r}return[]}})();
/* "Show where I am" map button (shared by both trip planners): live blue dot + accuracy ring. First tap finds you and
   centers the map; tap again to re-center when you have panned away, or to turn it off when you are in view. */
window.kpcLocate=window.kpcLocate||function(map,opts){opts=opts||{};if(!window.L||!map||!map.getContainer)return null;
 if(!document.getElementById('kpc-locate-css')){const st=document.createElement('style');st.id='kpc-locate-css';
  st.textContent='.kpc-locate a{display:flex;align-items:center;justify-content:center;width:34px;height:34px;font-size:20px;line-height:1;color:#1f6fd1;background:#fff;text-decoration:none}.kpc-locate a.on{background:#1f6fd1;color:#fff}.kpc-locate a.busy{opacity:.6}@keyframes kpcpulse{0%{box-shadow:0 0 0 0 rgba(31,111,209,.55)}100%{box-shadow:0 0 0 14px rgba(31,111,209,0)}}.kpc-me{width:18px;height:18px;border-radius:50%;background:#1f6fd1;border:3px solid #fff;animation:kpcpulse 1.6s infinite}';document.head.appendChild(st)}
 let wid=null,dot=null,ring=null,first=true,btn;
 function stop(){if(wid!==null&&navigator.geolocation)navigator.geolocation.clearWatch(wid);wid=null;btn.classList.remove('on','busy');btn.title='Show where I am';if(dot){dot.remove();ring.remove();dot=ring=null}}
 function start(){if(!navigator.geolocation){alert('This browser can’t share your location.');return}first=true;btn.classList.add('on','busy');btn.title='Finding you…';
  wid=navigator.geolocation.watchPosition(p=>{const ll=[p.coords.latitude,p.coords.longitude],a=Math.min(p.coords.accuracy||0,5000);btn.classList.remove('busy');btn.title='Showing where you are (tap to re-center or turn off)';
   if(!dot){ring=L.circle(ll,{radius:a,color:'#1f6fd1',weight:1,fillColor:'#1f6fd1',fillOpacity:.12,interactive:false}).addTo(map);
    dot=L.marker(ll,{zIndexOffset:3000,keyboard:false,icon:L.divIcon({className:'',html:'<div class="kpc-me"></div>',iconSize:[24,24],iconAnchor:[12,12]})}).bindTooltip('You are here').addTo(map)}
   else{dot.setLatLng(ll);ring.setLatLng(ll).setRadius(a)}
   if(first){map.setView(ll,Math.max(map.getZoom(),13));first=false}},
  err=>{stop();alert(err&&err.code===1?'Location is turned off for this site. Allow location in your browser settings to see where you are.':'Your location isn’t available right now. Try again in the open, away from buildings.')},
  {enableHighAccuracy:true,maximumAge:10000,timeout:30000})}
 const C=L.control({position:opts.position||'topleft'});
 C.onAdd=()=>{const d=L.DomUtil.create('div','leaflet-bar kpc-locate');btn=L.DomUtil.create('a','',d);btn.href='#';btn.setAttribute('role','button');btn.title='Show where I am';btn.setAttribute('aria-label','Show where I am');btn.innerHTML='&#9678;';
  L.DomEvent.disableClickPropagation(d);L.DomEvent.on(btn,'click',e=>{L.DomEvent.preventDefault(e);
   if(wid===null)start();else if(dot&&!map.getBounds().pad(-0.1).contains(dot.getLatLng()))map.setView(dot.getLatLng(),Math.max(map.getZoom(),13));else stop()});return d};
 C.addTo(map);return C};
