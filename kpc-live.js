/* KPC Live ("Happening Now") page. Sources (all verified to load in a real browser Oct 9, 2026):
   POTA spots (api.pota.app), WSPR via kpc-band-strip.js, NOAA SWPC, Open-Meteo, NWS alerts,
   Iowa Environmental Mesonet NEXRAD tiles, NOAA nowCOAST lightning strike density. */
(function(){
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const MEMBERS=['KZ4CP','N4BDW','KQ4HZK','K4ZSR'];
const CITIES=[{n:'Louisville',la:38.25,lo:-85.76,c:'#e6194b'},{n:'Bowling Green',la:36.99,lo:-86.44,c:'#3b6fe0'},{n:'Hazard',la:37.25,lo:-83.19,c:'#f58231'},{n:'Paducah',la:37.08,lo:-88.60,c:'#8e3fc4'},{n:'Ashland',la:38.48,lo:-82.64,c:'#0f9d8a'}];
const BL={1:'160m',3:'80m',7:'40m',10:'30m',14:'20m',18:'17m',21:'15m',24:'12m',28:'10m',50:'6m'};
const base=c=>String(c||'').toUpperCase().split('/').reduce((a,b)=>b.length>a.length?b:a,'');
async function jget(u,ms){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms||15000);try{const r=await fetch(u,{signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}}
const stamp=()=>{const e=$('lv-stamp');if(e)e.textContent=new Date().toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})};

/* ---------- sun ---------- */
const R=Math.PI/180;
function sunPos(d){const jd=d.getTime()/864e5+2440587.5,n=jd-2451545.0;const L=(280.460+0.9856474*n)%360,g=((357.528+0.9856003*n)%360)*R;const lam=(L+1.915*Math.sin(g)+0.020*Math.sin(2*g))*R,eps=(23.439-0.0000004*n)*R;const dec=Math.asin(Math.sin(eps)*Math.sin(lam)),ra=Math.atan2(Math.cos(eps)*Math.sin(lam),Math.cos(lam));const gmst=((280.46061837+360.98564736629*n)%360+360)%360;return{dec,ra,gmst}}
function sunAlt(lat,lon,s){const H=((s.gmst+lon)*R)-s.ra;return Math.asin(Math.sin(lat*R)*Math.sin(s.dec)+Math.cos(lat*R)*Math.cos(s.dec)*Math.cos(H))/R}
let sunMode='day';
function sunStatus(){const now=new Date(),a=sunAlt(37.8,-85.7,sunPos(now)),b=sunAlt(37.8,-85.7,sunPos(new Date(now.getTime()+15*60000)));
 if(a>6){sunMode='day';return['DAYLIGHT','Sun is up in Kentucky']}
 if(a>=-6){sunMode='gray';return['GRAY LINE',b>a?'Sunrise in Kentucky':'Sunset in Kentucky']}
 sunMode='night';return['NIGHT','Dark in Kentucky']}
let sfi=null,kp=null,lastRows=null,parksN=0,membersN=0;
function renderStatus(){const [t,s]=sunStatus();$('lv-sun').innerHTML='<b>'+t+'</b><span>'+s+'</span>';
 $('lv-sfi').innerHTML='<b>'+(Number.isFinite(sfi)?'SFI '+Math.round(sfi):'SFI --')+'</b><span>Solar flux</span>';
 const kl=!Number.isFinite(kp)?'':kp<3?'Geomagnetic: quiet':kp<5?'Geomagnetic: unsettled':'Geomagnetic: storm';
 $('lv-kp').innerHTML='<b>'+(Number.isFinite(kp)?'Kp '+(kp%1?kp.toFixed(1):kp):'Kp --')+'</b><span>'+kl+'</span>';
 $('lv-parks').innerHTML='<b>'+parksN+' park'+(parksN===1?'':'s')+'</b><span>on the air in KY now'+(membersN?' · '+membersN+' KPC':'')+'</span>';
 bestBets()}
function bestBets(){const el=$('lv-best');if(!el)return;let t='';
 if(lastRows){const m={};lastRows.forEach(r=>m[Number(r.band)]=Number(r.c));const top=Object.entries(m).filter(e=>BL[e[0]]).sort((a,b)=>b[1]-a[1]).filter(e=>e[1]>0).slice(0,2).map(e=>BL[e[0]]);
  if(top.length===2)t='<b>Best bets right now:</b> '+top[0]+' and '+top[1]+' are the busiest bands. ';else if(top.length===1)t='<b>Best bet right now:</b> '+top[0]+' is the busiest band. '}
 const hint=sunMode==='night'?'After dark the lower bands (80m to 30m) usually do best.':sunMode==='day'?'In daylight the higher bands (20m to 10m) usually do best.':'The gray line is often good for long-distance contacts.';
 t+=hint;if(Number.isFinite(kp)&&kp>=5)t+=' <b>Geomagnetic storm in progress: HF may be poor.</b>';
 el.innerHTML=t}
window.addEventListener('kpc-bands',e=>{const d=e.detail||{};lastRows=d.rows||null;if(Number.isFinite(d.sfi))sfi=d.sfi;if(Number.isFinite(d.kp))kp=d.kp;renderStatus();spaceExtra()});

/* ---------- space weather (NOAA SWPC) ---------- */
async function spaceExtra(){try{const j=await jget('https://services.swpc.noaa.gov/products/noaa-scales.json');const c=j['0']||j[0]||{};const g=c.G&&c.G.Scale,r=c.R&&c.R.Scale,s=c.S&&c.S.Scale;
  $('sw-g').textContent=g!=null?'G'+g:'--';$('sw-r').textContent=r!=null?'R'+r:'--';$('sw-s').textContent=s!=null?'S'+s:'--'}catch(e){}
 if(Number.isFinite(sfi))$('sw-sfi').textContent=Math.round(sfi);if(Number.isFinite(kp))$('sw-kp').textContent=kp%1?kp.toFixed(1):kp}
async function noaaBasic(){try{const [k,f]=await Promise.all([jget('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'),jget('https://services.swpc.noaa.gov/products/summary/10cm-flux.json')]);kp=Number(k[k.length-1].Kp);sfi=Number((Array.isArray(f)?f[0]:f).flux);renderStatus();spaceExtra()}catch(e){}}

/* ---------- POTA spots bar ---------- */
const mhz=f=>{const n=parseFloat(f);return isNaN(n)?esc(f):(n/1000).toFixed(3)};
const tm=s=>new Date(String(s.spotTime).endsWith('Z')?s.spotTime:s.spotTime+'Z');
async function spots(){try{const all=await jget('https://api.pota.app/spot/activator');
  const club=all.filter(s=>MEMBERS.includes(base(s.activator)));const ky=all.filter(s=>String(s.locationDesc||'').split(',').some(x=>x.trim()==='US-KY'));
  const show=[...club,...ky.filter(s=>!club.includes(s))].sort((a,b)=>(MEMBERS.includes(base(b.activator))-MEMBERS.includes(base(a.activator)))||(tm(b)-tm(a)));
  parksN=new Set(ky.map(s=>s.reference)).size;membersN=new Set(club.map(s=>base(s.activator))).size;
  $('lv-spotlist').innerHTML=show.slice(0,14).map(s=>`<span class="ch${MEMBERS.includes(base(s.activator))?' k':''}"><b>${esc(s.activator)}</b> ${esc(s.reference)} &middot; ${mhz(s.frequency)} ${esc(s.mode)}</span>`).join('')||'<span class="ch">No Kentucky parks spotted right now</span>';
  $('lv-spotcount').innerHTML=parksN||membersN?`<b>${parksN}</b> KY park${parksN===1?'':'s'}${membersN?` &middot; <b>${membersN}</b> KPC member${membersN===1?'':'s'}`:''}`:'Quiet right now';
  $('lv-dot').classList.toggle('off',!show.length);renderStatus()}catch(e){$('lv-spotlist').innerHTML='<span class="ch">Live spots are on the <a href="kpc-spots.html" style="color:inherit;text-decoration:underline">spots page</a></span>'}}

/* ---------- weather ---------- */
const WX={0:'Clear',1:'Mostly clear',2:'Partly cloudy',3:'Overcast',45:'Fog',48:'Fog',51:'Light drizzle',53:'Drizzle',55:'Heavy drizzle',56:'Freezing drizzle',57:'Freezing drizzle',61:'Light rain',63:'Rain',65:'Heavy rain',66:'Freezing rain',67:'Freezing rain',71:'Light snow',73:'Snow',75:'Heavy snow',77:'Snow grains',80:'Rain showers',81:'Rain showers',82:'Heavy showers',85:'Snow showers',86:'Snow showers',95:'Thunderstorm',96:'Thunderstorm, hail',99:'Thunderstorm, hail'};
const wxCard=(n,c,col)=>`<div class="w"><b>${col?`<i class="cdot" style="background:${col}"></i>`:''}${esc(n)}</b><div class="t">${Math.round(c.temperature_2m)}&deg;</div><small>${esc(WX[c.weather_code]||'')} &middot; wind ${Math.round(c.wind_speed_10m)} mph</small></div>`;
const cityTemps={};let youCard='';
const Q='&current=temperature_2m,weather_code,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph';
async function weather(){try{const j=await jget('https://api.open-meteo.com/v1/forecast?latitude='+CITIES.map(c=>c.la).join(',')+'&longitude='+CITIES.map(c=>c.lo).join(',')+Q);
  const a=Array.isArray(j)?j:[j];$('lv-wx').innerHTML=youCard+a.map((x,i)=>{cityTemps[CITIES[i].n]=Math.round(x.current.temperature_2m);return wxCard(CITIES[i].n,x.current,CITIES[i].c)}).join('');radarCities()}catch(e){$('lv-wx').innerHTML='<div class="w" style="grid-column:1/-1"><small>Weather could not load right now. Try the <a href="kpc-weather.html">KPC Field Weather</a> page.</small></div>'}}
function alertsUI(list,where){const box=$('lv-alerts');
 if(!list){box.className='ok';box.innerHTML='Alerts could not load. <a href="https://alerts.weather.gov/search?area=KY" target="_blank" rel="noopener">Check NWS alerts</a>';return}
 if(!list.length){box.className='ok';box.innerHTML='&#10003; No active NWS watches or warnings'+(where?' for '+esc(where):' in Kentucky')+'.';return}
 const g={};list.forEach(f=>{const p=f.properties||{};g[p.event]=(g[p.event]||0)+1});const ev=Object.entries(g).sort((a,b)=>(/Warning/.test(b[0])-/Warning/.test(a[0]))||b[1]-a[1]);
 const sev=ev.some(e=>/Warning/.test(e[0]));box.className='alert'+(sev?' sev':'');
 box.innerHTML='<b>&#9888; Active NWS alerts'+(where?' for '+esc(where):'')+':</b> '+ev.slice(0,6).map(e=>esc(e[0])+(e[1]>1&&!where?' ('+e[1]+')':'')).join(', ')+'. <a href="https://alerts.weather.gov/search?area=KY" target="_blank" rel="noopener">See details &rarr;</a>'}
async function alerts(){try{const j=await jget('https://api.weather.gov/alerts/active?area=KY');alertsUI(j.features||[])}catch(e){alertsUI(null)}}
function useLocation(){const b=$('lv-loc');if(!navigator.geolocation){b.textContent='LOCATION NOT AVAILABLE';return}b.textContent='LOCATING...';
 navigator.geolocation.getCurrentPosition(async p=>{const la=p.coords.latitude,lo=p.coords.longitude;b.textContent='\u{1F4CD} UPDATE MY LOCATION';
  try{const j=await jget('https://api.open-meteo.com/v1/forecast?latitude='+la+'&longitude='+lo+Q);youCard=wxCard('YOUR LOCATION',j.current).replace('class="w"','class="w you"');weather();
   try{const a=await jget('https://api.weather.gov/alerts/active?point='+la.toFixed(4)+','+lo.toFixed(4));alertsUI(a.features||[],'your location')}catch(e){}}catch(e){b.textContent='COULD NOT GET WEATHER'}},()=>{b.textContent='LOCATION BLOCKED'},{timeout:12000,maximumAge:300000})}

/* ---------- radar + lightning map ---------- */
let map,cityLayer,radarFrames=[],cur,lightning,counties,loopTimer=null,playing=false,idx=0,framesBuilt=false;
const RTILE=m=>'https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/nexrad-n0q-900913'+(m?'-m'+String(m).padStart(2,'0')+'m':'')+'/{z}/{x}/{y}.png';
const OFFS=[50,45,40,35,30,25,20,15,10,5,0];
function frameLabel(off){const d=new Date(Math.floor(Date.now()/300000)*300000-off*60000);return d.toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})}
function radarCities(){if(!cityLayer)return;cityLayer.clearLayers();CITIES.forEach(c=>{const t=cityTemps[c.n];L.circleMarker([c.la,c.lo],{radius:8,color:'#fff',weight:3,fillColor:c.c,fillOpacity:1,pane:'dotp'}).bindTooltip(c.n+(t!=null?' '+t+'\u00B0':''),{direction:'top'}).addTo(cityLayer)})}
function initMap(){if(typeof L==='undefined'||typeof KPC==='undefined'||!$('lv-map'))return;
 let svb=null;try{svb=localStorage.getItem('kpcBaseMap');localStorage.setItem('kpcBaseMap',localStorage.getItem('lvBase')||'Street')}catch(e){}
 map=KPC.leafletMap('lv-map');try{if(svb===null)localStorage.removeItem('kpcBaseMap');else localStorage.setItem('kpcBaseMap',svb)}catch(e){}
 map.on('baselayerchange',e=>{try{localStorage.setItem('lvBase',e.name)}catch(_){}});map.setView([37.75,-85.7],6);
 map.createPane('radarp');map.getPane('radarp').style.zIndex=350;map.createPane('lightp');map.getPane('lightp').style.zIndex=355;map.createPane('dotp');map.getPane('dotp').style.zIndex=650;
 let re=0,rok=0;const rnote=()=>{$('lv-rnote').textContent=re>3&&!rok?'Radar tiles did not load. Check your connection or try again.':rok?'Radar: NOAA NEXRAD, latest scan about '+frameLabel(0):''};
 cur=L.tileLayer(RTILE(0)+'?t='+Math.floor(Date.now()/300000),{pane:'radarp',opacity:.8,maxZoom:12,attribution:'Radar: NOAA/NWS via Iowa Environmental Mesonet'}).addTo(map);
 cur.on('tileerror',()=>{re++;rnote()});cur.on('tileload',()=>{rok++;if(rok%10===1)rnote()});
 let le=0;lightning=L.tileLayer.wms('https://nowcoast.noaa.gov/geoserver/ows',{pane:'lightp',layers:'lightning_detection:ldn_lightning_strike_density',format:'image/png',transparent:true,version:'1.3.0',opacity:.85,attribution:'Lightning: NOAA nowCOAST'}).addTo(map);
 lightning.on('tileerror',()=>{if(++le===3)$('lv-lnote').textContent='The lightning layer did not load. It may be down for a moment.'});
 lightning.on('load',()=>{le=0;$('lv-lnote').textContent=''});
 cityLayer=L.layerGroup().addTo(map);radarCities();
 KPC.countyLayer(map).then(g=>{counties=g;map.removeLayer(g);setChip('lv-c-counties',false)}).catch(()=>{});
 $('lv-slider').addEventListener('input',()=>{buildFrames();stop();show(Number($('lv-slider').value))});
 $('lv-play').onclick=()=>playing?stop():play();
 $('lv-c-radar').onclick=()=>{const on=toggle('lv-c-radar');frames().forEach(l=>on?l.addTo(map):map.removeLayer(l));if(on){show(idx)}};
 $('lv-c-light').onclick=()=>{toggle('lv-c-light')?lightning.addTo(map):map.removeLayer(lightning)};
 $('lv-c-counties').onclick=()=>{const on=toggle('lv-c-counties');if(counties)on?counties.addTo(map):map.removeLayer(counties)};
 setTimeout(()=>map.invalidateSize(),300)}
const frames=()=>framesBuilt?radarFrames:[cur];
function toggle(id){const b=$(id),on=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',on);return on}
function setChip(id,on){$(id).setAttribute('aria-pressed',on)}
function buildFrames(){if(framesBuilt)return;framesBuilt=true;radarFrames=OFFS.map(o=>o===0?cur:L.tileLayer(RTILE(o),{pane:'radarp',opacity:0,maxZoom:12}).addTo(map));$('lv-slider').max=OFFS.length-1}
function show(i){idx=i;radarFrames.forEach((l,j)=>l.setOpacity(j===i?.8:0));$('lv-flabel').textContent=(i===OFFS.length-1?'Now ':'')+frameLabel(OFFS[i]);$('lv-slider').value=i}
function play(){if($('lv-c-radar').getAttribute('aria-pressed')!=='true'){toggle('lv-c-radar');}buildFrames();playing=true;$('lv-play').innerHTML='&#10074;&#10074; PAUSE';idx=0;show(0);loopTimer=setInterval(()=>{idx=(idx+1)%OFFS.length;show(idx);if(idx===OFFS.length-1){clearInterval(loopTimer);setTimeout(()=>{if(playing){idx=-1;loopTimer=setInterval(()=>{idx=(idx+1)%OFFS.length;show(idx)},650)}},1400)}},650)}
function stop(){playing=false;clearInterval(loopTimer);$('lv-play').innerHTML='&#9654; PLAY LAST HOUR'}

/* ---------- start ---------- */
function openSignalMap(){const t=setInterval(()=>{const d=document.getElementById('kb-det');if(d){clearInterval(t);if(!d.open)d.open=true}},300);setTimeout(()=>clearInterval(t),15000)}
function init(){renderStatus();noaaBasic();spots();weather();alerts();initMap();openSignalMap();
 $('lv-loc').onclick=useLocation;
 setInterval(spots,60000);setInterval(()=>{noaaBasic();weather();alerts();renderStatus()},300000);
 setInterval(()=>{renderStatus();stamp()},60000);stamp();
 setInterval(()=>{if(cur&&!playing){cur.setUrl(RTILE(0)+'?t='+Math.floor(Date.now()/300000))}},300000)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
