/* KPC Live radar extras: SOTA ON AIR, WWFF ON AIR, SEVERE OUTLOOK and RAIN AT A PARK.
   - Spots come from kpc-radio.js (event 'kpc-spots'); summit/WWFF positions from locations-ky.json, else the spot's grid.
   - Severe outlook: NWS map service copy of the SPC Day 1 categorical outlook (fields dn,label,label2,fill,stroke),
     falling back to SPC's own GeoJSON file.
   - Rain timeline: Open-Meteo 15-minute precipitation (NOAA HRRR in North America) + hourly chance of rain.
   Needs the Live radar map from kpc-live.js (window.KPCLive.map or event 'kpc-livemap'). */
(function(){
const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const store={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
let map=null,sotaL,wwffL,outL,rainMk=null,SPOTS=[],LOC=null,PARKS=null,rainMode=false;
const ON=store.get('lvPlus',{sota:true,wwff:true,out:false});
const BOX={s:35.0,n:40.6,w:-91.5,e:-80.0}; /* Kentucky plus roughly 100 miles */
function chip(id,on){const b=$(id);if(b)b.setAttribute('aria-pressed',String(!!on))}
async function jget(u,ms){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms||15000);try{const r=await fetch(u,{cache:'no-store',signal:c.signal});if(!r.ok)throw new Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}}
function gridXY(g){g=String(g||'').trim();if(!/^[A-R]{2}\d{2}([A-X]{2})?/i.test(g))return null;g=g.toUpperCase();let lo=(g.charCodeAt(0)-65)*20-180+(+g[2])*2,la=(g.charCodeAt(1)-65)*10-90+(+g[3]);
 if(g.length>=6&&/[A-X]{2}/.test(g.slice(4,6))){lo+=(g.charCodeAt(4)-65)/12+1/24;la+=(g.charCodeAt(5)-65)/24+1/48}else{lo+=1;la+=.5}return[la,lo]}
function loadLoc(){if(!LOC)LOC=fetch('locations-ky.json').then(r=>r.json()).then(j=>{const m={};(j.rows||j).forEach(r=>{if(r[0]!=='POTA')m[String(r[1]).toUpperCase()]=[+r[3],+r[4],r[2]]});return m}).catch(()=>({}));return LOC}
const allUS=()=>{const b=$('lv-c-all');return b&&b.getAttribute('aria-pressed')==='true'};

/* ---------- SOTA / WWFF on the air ---------- */
async function drawXota(){if(!map)return;const loc=await loadLoc();sotaL.clearLayers();wwffL.clearLayers();const n={SOTA:0,WWFF:0};
 SPOTS.forEach(s=>{if(s.cat!=='SOTA'&&s.cat!=='WWFF')return;const ref=String(s.ref||'').split(/[ ,]+/)[0].toUpperCase();
  let xy=(isFinite(s.la)&&isFinite(s.lo)&&s.la)?[s.la,s.lo]:null;if(!xy&&loc[ref])xy=loc[ref];if(!xy)xy=gridXY(s.grid);if(!xy)return;
  const near=xy[0]>=BOX.s&&xy[0]<=BOX.n&&xy[1]>=BOX.w&&xy[1]<=BOX.e;
  if(!near&&!(allUS()&&(s.cont==='NA'||/United States/i.test(s.country)||/^W|^K|^N|^A[A-L]/.test(s.call))))return;
  const sota=s.cat==='SOTA';n[s.cat]++;
  const name=s.name||(loc[ref]&&loc[ref][2])||'';
  const page=sota?`https://sotl.as/summits/${encodeURIComponent(ref)}`:`https://logsearch.wwff.co/directory/${encodeURIComponent(ref)}`;
  L.circleMarker(xy,{pane:'spotp',radius:7,color:'#fff',weight:2.5,fillColor:sota?'#8a4b14':'#2b6cb0',fillOpacity:1})
   .bindPopup(`<b>${esc(name||ref)}</b> (${esc(ref)})<br><b>${esc(s.call)}</b> &middot; ${(s.khz/1000).toFixed(3)} MHz ${esc(s.mode||'')}<br><small>${sota?'SOTA summit':'WWFF reference'}${s.t?' &middot; spotted '+Math.max(0,Math.round((Date.now()-s.t)/60000))+' min ago':''}</small><br><a href="${page}" target="_blank" rel="noopener">${sota?'Summit page':'WWFF page'}</a> &middot; <a href="#rx-card" data-tune="${s.khz}|${esc(s.mode||'')}">Listen</a>`)
   .addTo(sota?sotaL:wwffL)});
 const parts=[];if(ON.sota)parts.push(n.SOTA+' SOTA');if(ON.wwff)parts.push(n.WWFF+' WWFF');
 $('lv-xnote').textContent=parts.length&&SPOTS.length?parts.join(' and ')+' on the air'+(allUS()?' (all US)':' near Kentucky')+' (brown = summit, blue = WWFF)':''}

/* ---------- severe weather outlook (SPC Day 1) ---------- */
const RISK={2:['General thunderstorms','#c1e9c1','TSTM'],3:['Marginal (1 of 5)','#66a366','MRGL'],4:['Slight (2 of 5)','#f6f67f','SLGT'],5:['Enhanced (3 of 5)','#e6c27f','ENH'],6:['Moderate (4 of 5)','#e67f7f','MDT'],8:['High (5 of 5)','#ff7fff','HIGH']};
const KYPTS=[[38.25,-85.76],[38.04,-84.5],[36.99,-86.44],[37.08,-88.6],[37.48,-82.52],[37.09,-84.6],[37.77,-87.11],[38.48,-82.64]];
function inRing(x,y,r){let c=false;for(let i=0,j=r.length-1;i<r.length;j=i++){const[xi,yi]=r[i],[xj,yj]=r[j];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi+1e-15)+xi)c=!c}return c}
function inGeom(g,la,lo){if(!g)return false;const P=g.type==='Polygon'?[g.coordinates]:g.type==='MultiPolygon'?g.coordinates:[];return P.some(p=>inRing(lo,la,p[0])&&!p.slice(1).some(h=>inRing(lo,la,h)))}
let outData=null,outT=0;
async function loadOutlook(){if(outData&&Date.now()-outT<20*60000)return outData;
 const tries=['https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/MapServer/1/query?where=1%3D1&outFields=dn,label,label2,fill,stroke,valid,expire&returnGeometry=true&f=geojson',
  'https://www.spc.noaa.gov/products/outlook/day1otlk_cat.nolyr.geojson'];
 for(const u of tries){try{const j=await jget(u,20000);if(j&&Array.isArray(j.features)){outData=j;outT=Date.now();return j}}catch(e){}}throw new Error('outlook unavailable')}
async function drawOutlook(){if(!map)return;outL.clearLayers();const note=$('lv-onote');note.textContent='Loading the severe weather outlook…';
 try{const j=await loadOutlook();let ky=0;
  const feats=j.features.map(f=>{const p=f.properties||{},dn=+(p.dn??p.DN);return{f,p,dn}}).filter(x=>RISK[x.dn]).sort((a,b)=>a.dn-b.dn);
  feats.forEach(({f,p,dn})=>{const[name,col]=RISK[dn];
   L.geoJSON(f.geometry,{pane:'warnp',style:{color:p.stroke||col,weight:1.5,fillColor:p.fill||col,fillOpacity:.35}}).bindPopup(`<b>Severe weather outlook: ${esc(name)}</b><br><small>Storm Prediction Center, today</small><br><a href="https://www.spc.noaa.gov/products/outlook/day1otlk.html" target="_blank" rel="noopener">SPC outlook details</a>`).addTo(outL);
   if(KYPTS.some(([la,lo])=>inGeom(f.geometry,la,lo)))ky=Math.max(ky,dn)});
  note.innerHTML=feats.length?`Severe outlook today for Kentucky: <b>${ky?RISK[ky][0]:'no severe risk'}</b>. Colors: green = thunderstorms or marginal, yellow = slight, orange = enhanced, red = moderate, pink = high.`:'Severe outlook: no thunderstorm areas outlined for today.'}
 catch(e){note.textContent='The severe weather outlook did not load. Try again in a few minutes.'}}

/* ---------- rain at a park ---------- */
function loadParks(){if(!PARKS)PARKS=fetch('kpc-ky-data.json').then(r=>r.json()).then(j=>j.parks||[]).catch(()=>[]);return PARKS}
async function rainAt(la,lo,label){const box=$('lv-rain-out');box.innerHTML='<p class="lv-src" style="margin:8px 0">Checking the rain forecast…</p>';
 if(map){if(rainMk)rainMk.remove();rainMk=L.marker([la,lo],{pane:'spotp',title:label,icon:L.divIcon({className:'',html:'<div style="width:18px;height:18px;border-radius:50%;background:#1f6fd1;border:3px solid #fff;box-shadow:0 0 0 2px #0b2e5a"></div>',iconSize:[18,18],iconAnchor:[9,9]})}).addTo(map)}
 try{const j=await jget(`https://api.open-meteo.com/v1/forecast?latitude=${la.toFixed(4)}&longitude=${lo.toFixed(4)}&minutely_15=precipitation&hourly=precipitation_probability,precipitation&forecast_days=2&timezone=auto&precipitation_unit=inch`);
  const m=j.minutely_15||{},h=j.hourly||{},off=(j.utc_offset_seconds||0)*1000;
  const toMs=t=>Date.parse(t+'Z')-off,now=Date.now();
  const q=(m.time||[]).map((t,i)=>({t:toMs(t),p:+(m.precipitation||[])[i]||0})).filter(x=>x.t>=now-15*60000).slice(0,9);
  const hr=(h.time||[]).map((t,i)=>({t:toMs(t),c:(h.precipitation_probability||[])[i],p:+(h.precipitation||[])[i]||0})).filter(x=>x.t>=now-60*60000).slice(0,12);
  const tm=t=>new Date(t).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'}),th=t=>new Date(t).toLocaleTimeString([],{hour:'numeric'});
  const wet=q.find(x=>x.p>=0.005),wetNow=q[0]&&q[0].p>=0.005,dry=wetNow?q.find(x=>x.p<0.005):null;
  const firstHr=hr.find(x=>(x.c??0)>=50);
  let sum;if(wetNow)sum=`<b>Raining or about to rain</b> at ${esc(label)}${dry?`, easing around ${tm(dry.t)}`:' for the next two hours'}.`;
  else if(wet)sum=`<b>Rain likely starting around ${tm(wet.t)}</b> at ${esc(label)} (in about ${Math.max(5,Math.round((wet.t-now)/60000/5)*5)} minutes).`;
  else sum=`<b>No rain expected in the next two hours</b> at ${esc(label)}.${firstHr?` Chance of rain reaches ${firstHr.c}% around ${th(firstHr.t)}.`:' Chance of rain stays under 50% for the next 12 hours.'}`;
  const bar=(p)=>p<0.005?'#e9e3d2':p<0.02?'#9cc9f0':p<0.1?'#3d8fe0':'#123f8c';
  box.innerHTML=`<p style="margin:10px 0 8px;font-size:15px">${sum}</p>
<div class="rn-lab">NEXT 2 HOURS (15-MINUTE STEPS)</div><div class="rn-row">${q.map(x=>`<div class="rn-c" title="${tm(x.t)}: ${x.p.toFixed(2)} in"><i style="background:${bar(x.p)}"></i><span>${tm(x.t).replace(/ ?[AP]M/,'')}</span></div>`).join('')}</div>
<div class="rn-lab">CHANCE OF RAIN, NEXT 12 HOURS</div><div class="rn-row">${hr.map(x=>`<div class="rn-c" title="${th(x.t)}: ${x.c??'?'}%"><i style="height:${Math.max(3,(x.c||0)*0.42)}px;background:${(x.c||0)>=50?'#1f6fd1':'#9cc9f0'};margin-top:auto"></i><b>${x.c??'?'}%</b><span>${th(x.t).replace(/ ?[AP]M/,'')}</span></div>`).join('')}</div>
<p class="lv-src" style="margin:8px 0 0">Light blue = light rain, blue = moderate, dark blue = heavy. Forecast by Open-Meteo (NOAA HRRR model). Times are your local time. Tap the map or pick another park to check somewhere else.</p>`;
  store.set('lvRainLast',{la,lo,label})}
 catch(e){box.innerHTML='<p class="lv-src" style="margin:8px 0;color:#b5452b">The rain forecast did not load. Try again in a minute.</p>'}}
function setRain(on){rainMode=on;chip('lv-c-rain',on);$('lv-rain').style.display=on?'':'none';$('lv-map').classList.toggle('rain-pick',on);
 if(!on&&rainMk){rainMk.remove();rainMk=null}
 if(on){loadParks();
  const last=store.get('lvRainLast',null);if(last&&isFinite(last.la))rainAt(last.la,last.lo,last.label)}}

/* ---------- wire up ---------- */
function start(m){if(map||!m)return;map=m;
 sotaL=L.layerGroup();wwffL=L.layerGroup();outL=L.layerGroup();
 if(ON.sota)sotaL.addTo(map);if(ON.wwff)wwffL.addTo(map);chip('lv-c-sota',ON.sota);chip('lv-c-wwff',ON.wwff);chip('lv-c-out',ON.out);
 if(ON.out){outL.addTo(map);drawOutlook()}
 $('lv-c-sota').onclick=()=>{ON.sota=!ON.sota;store.set('lvPlus',ON);chip('lv-c-sota',ON.sota);ON.sota?sotaL.addTo(map):map.removeLayer(sotaL);drawXota()};
 $('lv-c-wwff').onclick=()=>{ON.wwff=!ON.wwff;store.set('lvPlus',ON);chip('lv-c-wwff',ON.wwff);ON.wwff?wwffL.addTo(map):map.removeLayer(wwffL);drawXota()};
 $('lv-c-out').onclick=()=>{ON.out=!ON.out;store.set('lvPlus',ON);chip('lv-c-out',ON.out);if(ON.out){outL.addTo(map);drawOutlook()}else{map.removeLayer(outL);$('lv-onote').textContent=''}};
 $('lv-c-rain').onclick=()=>setRain(!rainMode);
 const all=$('lv-c-all');if(all)all.addEventListener('click',()=>setTimeout(drawXota,0));
 /* listen on the map box itself so taps on warning or outlook areas still count in rain mode */
 map.getContainer().addEventListener('click',e=>{if(!rainMode)return;if(e.target.closest('.leaflet-control,.leaflet-popup,.leaflet-marker-icon'))return;
  const ll=map.mouseEventToLatLng(e);setTimeout(()=>map.closePopup(),0);rainAt(ll.lat,ll.lng,'the spot you tapped')});
 map.on('popupopen',e=>{const a=e.popup.getElement()&&e.popup.getElement().querySelector('[data-tune]');if(!a)return;a.onclick=ev=>{const[k,md]=a.dataset.tune.split('|');if(window.KPCRadio){ev.preventDefault();const kh=+k;window.KPCRadio.tune(kh,/CW/i.test(md)?'cw':/AM/i.test(md)?'am':kh<10000?'lsb':'usb',true);const bl=$('rx-blocked'),op=$('rx-open');if(op&&bl&&getComputedStyle(bl).display!=='none')op.click()}}});
 /* our own suggestion list (the phone's built-in one shows see-through on some phones) */
 const sug=$('lv-rain-sug'),pick=p=>{sug.hidden=true;$('lv-rain-q').value=p.n+' ('+p.c+')';rainAt(+p.la,+p.lo,p.n);if(map)map.setView([p.la,p.lo],Math.max(map.getZoom(),8))};
 $('lv-rain-q').addEventListener('input',async()=>{const v=$('lv-rain-q').value.trim().toLowerCase();if(v.length<2){sug.hidden=true;return}const P=await loadParks();
  const hits=P.filter(p=>p.n.toLowerCase().includes(v)||p.c.toLowerCase().includes(v)).slice(0,8);
  if(!hits.length){sug.hidden=true;return}sug._hits=hits;sug.innerHTML=hits.map((p,i)=>`<button type="button" data-i="${i}"><b>${esc(p.n)}</b><small>${esc(p.c)}${p.co?' \u00b7 '+esc(p.co)+' County':''}</small></button>`).join('');sug.hidden=false});
 sug.addEventListener('click',e=>{const b=e.target.closest('button');if(b)pick(sug._hits[+b.dataset.i])});
 document.addEventListener('click',e=>{if(!e.target.closest('#lv-rain-form,#lv-rain-sug'))sug.hidden=true});
 $('lv-rain-q').addEventListener('keydown',e=>{if(e.key==='Escape')sug.hidden=true});
 $('lv-rain-form').onsubmit=async ev=>{ev.preventDefault();sug.hidden=true;const v=$('lv-rain-q').value.trim();if(!v)return;const P=await loadParks();
  const ref=(v.match(/US-\d+/i)||[])[0];const p=ref?P.find(x=>x.c.toUpperCase()===ref.toUpperCase()):P.find(x=>x.n.toLowerCase()===v.toLowerCase())||P.find(x=>x.n.toLowerCase().includes(v.toLowerCase()));
  if(p){rainAt(+p.la,+p.lo,p.n);if(map)map.setView([p.la,p.lo],Math.max(map.getZoom(),8))}else $('lv-rain-out').innerHTML='<p class="lv-src" style="margin:8px 0">No Kentucky park matches that. Try part of the name, a park number like US-0724, or tap the map.</p>'};
 $('lv-rain-me').onclick=()=>{if(!navigator.geolocation)return;$('lv-rain-out').innerHTML='<p class="lv-src" style="margin:8px 0">Finding you…</p>';navigator.geolocation.getCurrentPosition(p=>rainAt(p.coords.latitude,p.coords.longitude,'your location'),()=>{$('lv-rain-out').innerHTML='<p class="lv-src" style="margin:8px 0">Location was blocked. Pick a park or tap the map instead.</p>'},{timeout:15000,maximumAge:300000})};
 window.addEventListener('kpc-spots',e=>{SPOTS=e.detail||[];drawXota()});if(window.KPCSpots){SPOTS=window.KPCSpots;drawXota()}
 setInterval(()=>{if(ON.out&&!document.hidden)drawOutlook()},30*60000)}
if(window.KPCLive&&window.KPCLive.map)start(window.KPCLive.map);else window.addEventListener('kpc-livemap',e=>start(e.detail));
})();
