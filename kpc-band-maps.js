/* KPC Band Activity & Gray Line  (loads only when the section is opened)
   Sources (all read straight from the browser, no keys):
   - WSPR.live  (db1.wspr.live)      actual received weak-signal reports, Kentucky area
   - Spothole   (spothole.app)        DX cluster, skimmer (RBN), POTA, SOTA and WWFF spots
   - NOAA SWPC                        solar flux and K-index
   The gray line is calculated here from the sun's position. */
(function(){
const root=document.getElementById('kpc-bands');if(!root)return;
const KYSQ=['EM56','EM57','EM66','EM67','EM68','EM76','EM77','EM78','EM79','EM86','EM87','EM88','EM89'];
const KYIN="('"+KYSQ.join("','")+"')";
const BANDS=[[1,'160m'],[3,'80m'],[5,'60m'],[7,'40m'],[10,'30m'],[14,'20m'],[18,'17m'],[21,'15m'],[24,'12m'],[28,'10m'],[50,'6m']];
const BCODES=BANDS.map(b=>b[0]).join(',');
const BCOL={1:'#8e6bd6',3:'#5b8def',5:'#2fb5c9',7:'#2dae6e',10:'#7bc043',14:'#f2c230',18:'#f08a1c',21:'#e5533d',24:'#d63b8a',28:'#b04ae8',50:'#e0e0e0'};
const KY={lat:37.8,lon:-85.7};
const CK='kpcBandsCache_v1',MAXAGE=10*60*1000;
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const $=(s,r)=>(r||root).querySelector(s);
let state={heat:null,heard:null,hearing:null,spots:null,noaa:null,t:0},map=null,layers=null,night=null,sunMk=null,scale='band',sel=new Set(),dir='both',started=false,timer=null;

/* ---------- skeleton ---------- */
root.innerHTML=`<details class="kb" id="kb-det"><summary><span><b>KPC BAND ACTIVITY &amp; GRAY LINE</b><small>Which bands are active around Kentucky, and where in the world • tap to open</small></span><i aria-hidden="true">▾</i></summary>
<div class="kb-body" hidden>
<div class="kb-top"><div class="kb-tile"><span>KENTUCKY RIGHT NOW</span><b id="kb-sun">…</b><small id="kb-sunsub"></small></div><div class="kb-tile"><span>SOLAR CONDITIONS</span><b id="kb-sol">…</b><small id="kb-solsub"></small></div><div class="kb-tile"><span>DATA AGE</span><b id="kb-age">…</b><small><button type="button" class="kb-btn" id="kb-refresh">REFRESH</button></small></div></div>
<h3>Band activity near Kentucky</h3>
<p class="kb-sub">Weak-signal (WSPR) reports where a Kentucky-area station was heard or was hearing, last 6 hours, in 30-minute blocks. Brighter means more reports. These are <b>real receptions</b>, not predictions.</p>
<div class="kb-chips" id="kb-scale"><button type="button" class="kb-chip" data-s="band" aria-pressed="true">EACH BAND ON ITS OWN SCALE</button><button type="button" class="kb-chip" data-s="all" aria-pressed="false">ALL BANDS TOGETHER</button></div>
<div id="kb-heat" class="kb-heat" aria-label="Band activity heat map"></div>
<div class="kb-legend"><span>few</span><i></i><span>many reports</span></div>
<h3>Gray line &amp; who hears Kentucky</h3>
<p class="kb-sub">The shaded area is night. The soft band along its edge is the gray line, where signals often travel farthest. Lines show WSPR paths from the last 2 hours.</p>
<div class="kb-chips" id="kb-dir"><button type="button" class="kb-chip" data-d="both" aria-pressed="true">BOTH WAYS</button><button type="button" class="kb-chip" data-d="heard" aria-pressed="false">KENTUCKY HEARD ABROAD</button><button type="button" class="kb-chip" data-d="hearing" aria-pressed="false">KENTUCKY HEARING</button></div>
<div class="kb-chips" id="kb-bands"></div>
<div id="kb-map" class="kb-map" role="img" aria-label="World map with day and night and WSPR paths to Kentucky"></div>
<p class="kb-sub" id="kb-mapnote"></p>
<h3>DX, skimmer and park spots</h3>
<p class="kb-sub">Spots reported in the last hour by DX clusters, skimmers (RBN), POTA, SOTA and WWFF through Spothole. A spot means someone reported activity. It does not prove the band was open for you. Green is spots involving Kentucky grids.</p>
<div id="kb-spots" class="kb-spots"></div>
<p class="kb-note" id="kb-status"></p>
<p class="kb-note">Sources: WSPR.live, Spothole, NOAA SWPC. Kentucky area means grid squares ${KYSQ.join(', ')} (includes a little of the neighboring states). Times shown in your local time.</p>
</div></details>`;
const det=$('#kb-det');
det.addEventListener('toggle',()=>{if(det.open&&!started){started=true;$('.kb-body').hidden=false;start()}else if(det.open){$('.kb-body').hidden=false;if(map)setTimeout(()=>map.invalidateSize(),150)}});
if(location.hash==='#band-activity'){det.open=true}

/* ---------- helpers ---------- */
const g4c=loc=>{const m=/^([A-R])([A-R])(\d)(\d)/i.exec(loc||'');if(!m)return null;const A='ABCDEFGHIJKLMNOPQR';return{lat:(A.indexOf(m[2].toUpperCase())*10-90)+(+m[4])+.5,lon:(A.indexOf(m[1].toUpperCase())*20-180)+(+m[3])*2+1}};
const bandOfHz=hz=>{const k=hz>1e6?hz/1e3:hz;const T=[[1800,2000,'160m'],[3500,4000,'80m'],[5300,5410,'60m'],[7000,7300,'40m'],[10100,10150,'30m'],[14000,14350,'20m'],[18068,18168,'17m'],[21000,21450,'15m'],[24890,24990,'12m'],[28000,29700,'10m'],[50000,54000,'6m']];for(const t of T)if(k>=t[0]&&k<=t[1])return t[2];return null};
async function jget(url,ms){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms||20000);try{const r=await fetch(url,{signal:c.signal});if(!r.ok)throw new Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}}
const wq=sql=>jget('https://db1.wspr.live/?query='+encodeURIComponent(sql+' FORMAT JSON')).then(j=>j.data||[]);
const utc=s=>new Date(String(s).replace(' ','T')+'Z');
const ago=t=>{const m=Math.round((Date.now()-t)/60000);return m<1?'just now':m<60?m+' min':Math.round(m/60)+' h'};

/* ---------- sun, gray line ---------- */
const R=Math.PI/180;
function sunPos(d){const jd=d.getTime()/864e5+2440587.5,n=jd-2451545.0;const L=(280.460+0.9856474*n)%360,g=((357.528+0.9856003*n)%360)*R;const lam=(L+1.915*Math.sin(g)+0.020*Math.sin(2*g))*R,eps=(23.439-0.0000004*n)*R;const dec=Math.asin(Math.sin(eps)*Math.sin(lam)),ra=Math.atan2(Math.cos(eps)*Math.sin(lam),Math.cos(lam));const gmst=((280.46061837+360.98564736629*n)%360+360)%360;let sl=((ra/R-gmst)%360+540)%360-180;return{dec,lon:sl,lat:dec/R,ra,gmst}}
function sunAlt(lat,lon,s){const H=((s.gmst+lon)*R)-s.ra;return Math.asin(Math.sin(lat*R)*Math.sin(s.dec)+Math.cos(lat*R)*Math.cos(s.dec)*Math.cos(H))/R}
function nightPoly(s,h){const pts=[];let darkN=s.lat<h;/* alt at north pole = declination */const darkS=-s.lat<h;
 for(let lon=-180;lon<=180;lon+=2){let prev=sunAlt(-90,lon,s)-h,cross=null;for(let lat=-89;lat<=90;lat+=1){const f=sunAlt(lat,lon,s)-h;if((prev<0)!==(f<0)){cross=lat-1+(-prev)/(f-prev);break}prev=f}
  pts.push([cross===null?(darkN?90:-90):cross,lon])}
 const out=pts.slice();if(darkN&&!darkS){out.push([90,180],[90,-180])}else if(darkS&&!darkN){out.push([-90,180],[-90,-180])}else if(darkN&&darkS){return[[ -90,-180],[-90,180],[90,180],[90,-180]]}
 return out}
function sunStatus(){const s=sunPos(new Date()),a=sunAlt(KY.lat,KY.lon,s);let t,sub;if(a>6){t='DAYLIGHT';sub='Sun '+a.toFixed(0)+'° above the horizon. Higher bands (20m to 10m) usually do best.'}else if(a>=-6){t='GRAY LINE';sub='Sunrise or sunset around Kentucky. Often good for long-distance contacts.'}else{t='NIGHT';sub='Sun '+Math.abs(a).toFixed(0)+'° below the horizon. Lower bands (80m to 30m) usually do best.'}return{t,sub}}

/* ---------- data ---------- */
async function load(force){
 let c=null;try{c=JSON.parse(localStorage.getItem(CK)||'null')}catch(e){}
 if(!force&&c&&Date.now()-c.t<MAXAGE){state=c;return}
 if(force&&c&&Date.now()-c.t<60000){state=c;return}
 const st=$('#kb-status');st.textContent='Loading live data…';
 const next={t:Date.now(),heat:null,heard:null,hearing:null,spots:null,noaa:null};const errs=[];
 const jobs=[
  wq(`SELECT band, toStartOfInterval(time, INTERVAL 30 MINUTE) AS t, count(*) AS c FROM wspr.rx WHERE time > now() - INTERVAL 6 HOUR AND band IN (${BCODES}) AND (substring(tx_loc,1,4) IN ${KYIN} OR substring(rx_loc,1,4) IN ${KYIN}) GROUP BY band,t ORDER BY t`).then(d=>next.heat=d).catch(e=>errs.push('WSPR heat map')),
  wq(`SELECT band, substring(rx_loc,1,4) AS loc, count(*) AS c, max(distance) AS d FROM wspr.rx WHERE time > now() - INTERVAL 2 HOUR AND band IN (${BCODES}) AND substring(tx_loc,1,4) IN ${KYIN} AND substring(rx_loc,1,4) NOT IN ${KYIN} GROUP BY band,loc ORDER BY c DESC LIMIT 500`).then(d=>next.heard=d).catch(e=>errs.push('WSPR paths')),
  wq(`SELECT band, substring(tx_loc,1,4) AS loc, count(*) AS c, max(distance) AS d FROM wspr.rx WHERE time > now() - INTERVAL 2 HOUR AND band IN (${BCODES}) AND substring(rx_loc,1,4) IN ${KYIN} AND substring(tx_loc,1,4) NOT IN ${KYIN} GROUP BY band,loc ORDER BY c DESC LIMIT 500`).then(d=>next.hearing=d).catch(e=>errs.push('WSPR paths')),
  (async()=>{let j=null;for(const u of['https://spothole.app/api/v1/spots?limit=2000&max_age=3600','https://spothole.app/api/v1/spots?limit=1000','https://spothole.app/api/v3/spots?limit=1000']){try{j=await jget(u);if(Array.isArray(j))break}catch(e){j=null}}if(!Array.isArray(j))throw 0;next.spots=j.map(s=>({hz:Number(s.freq),g1:String(s.dx_grid||''),g2:String(s.de_grid||''),st:[s.dx_state,s.de_state],src:s.source||s.sig||'Spot',t:s.time})).filter(s=>Number.isFinite(s.hz))})().catch(e=>errs.push('Spothole')),
  (async()=>{const[k,f]=await Promise.all([jget('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'),jget('https://services.swpc.noaa.gov/products/summary/10cm-flux.json')]);next.noaa={kp:Number(k[k.length-1].Kp),flux:Number((Array.isArray(f)?f[0]:f).flux)}})().catch(e=>errs.push('NOAA'))];
 await Promise.all(jobs);
 next.errs=[...new Set(errs)];
 if(!next.heat&&!next.heard&&c){state=c;state.errs=next.errs;return}
 state=next;try{localStorage.setItem(CK,JSON.stringify(next))}catch(e){}
}

/* ---------- render ---------- */
function paintTop(){const s=sunStatus();$('#kb-sun').textContent=s.t;$('#kb-sunsub').textContent=s.sub;
 const n=state.noaa;if(n){const k=n.kp;$('#kb-sol').textContent='SFI '+n.flux+' • Kp '+k.toFixed(1);$('#kb-solsub').textContent=k>=5?'Geomagnetic storm: HF may be disturbed.':k>=4?'Unsettled: some HF disturbance possible.':'Quiet geomagnetic field. '+(n.flux>=120?'Good flux for the higher bands.':n.flux>=90?'Moderate flux.':'Low flux; stay on the lower bands.')}else{$('#kb-sol').textContent='unavailable';$('#kb-solsub').textContent=''}
 $('#kb-age').textContent=state.t?ago(state.t):'…'}
function paintHeat(){const box=$('#kb-heat');if(!state.heat){box.innerHTML='<p class="kb-empty">WSPR data is unavailable right now. Try REFRESH in a minute.</p>';return}
 const now=Date.now(),step=30*60000,end=Math.floor(now/step)*step,N=12,cols=[];for(let i=N-1;i>=0;i--)cols.push(end-i*step);
 const M={};BANDS.forEach(b=>M[b[0]]=cols.map(()=>0));let gmax=1;
 state.heat.forEach(r=>{const i=cols.indexOf(Math.floor(utc(r.t).getTime()/step)*step);if(i>=0&&M[r.band]){M[r.band][i]+=Number(r.c)}});
 BANDS.forEach(b=>M[b[0]].forEach(v=>{if(v>gmax)gmax=v}));
 const fmt=t=>{const d=new Date(t);let h=d.getHours();return(h%12||12)+(h<12?'a':'p')};
 let h='<div class="kb-hrow kb-hhead"><span></span>'+cols.map((t,i)=>`<span>${i%2===0?fmt(t):''}</span>`).join('')+'<span class="kb-tot">6h</span></div>';
 BANDS.forEach(([code,name])=>{const row=M[code],mx=scale==='all'?gmax:Math.max(1,...row),tot=row.reduce((a,b)=>a+b,0);
  h+=`<div class="kb-hrow"><span class="kb-bl">${name}</span>`+row.map((v,i)=>{const t=v?Math.sqrt(v/mx):0;const bg=v?`rgba(213,166,58,${(0.18+0.82*t).toFixed(2)})`:'rgba(255,255,255,.05)';return`<span class="kb-c" style="background:${bg}" title="${name}: ${v} report${v===1?'':'s'} around ${fmt(cols[i])}"></span>`}).join('')+`<span class="kb-tot">${tot.toLocaleString()}</span></div>`});
 box.innerHTML=h}
function paintSpots(){const box=$('#kb-spots');if(!state.spots){box.innerHTML='<p class="kb-empty">Spot data is unavailable right now.</p>';return}
 const kys=new Set(KYSQ),by={};BANDS.forEach(b=>by[b[1]]={n:0,ky:0,src:{}});
 state.spots.forEach(s=>{const b=bandOfHz(s.hz);if(!b)return;const o=by[b];o.n++;o.src[s.src]=(o.src[s.src]||0)+1;const inKY=kys.has(s.g1.slice(0,4).toUpperCase())||kys.has(s.g2.slice(0,4).toUpperCase())||s.st.some(x=>x==='KY');if(inKY)o.ky++});
 const mx=Math.max(1,...Object.values(by).map(o=>o.n));
 box.innerHTML=BANDS.map(([c,b])=>{const o=by[b],top=Object.entries(o.src).sort((x,y)=>y[1]-x[1]).slice(0,3).map(x=>x[0]+' '+x[1]).join(' • ');return`<div class="kb-srow"><span class="kb-bl">${b}</span><div class="kb-bar"><i style="width:${(100*o.n/mx).toFixed(1)}%"><u style="width:${o.n?(100*o.ky/o.n).toFixed(1):0}%"></u></i></div><span class="kb-num">${o.n}<small>${o.ky?o.ky+' KY':''}</small></span><span class="kb-src">${esc(top)}</span></div>`}).join('')}
function ensureLeaflet(){return new Promise((res,rej)=>{if(window.L)return res();const l=document.createElement('link');l.rel='stylesheet';l.href='https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css';document.head.appendChild(l);const s=document.createElement('script');s.src='https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js';s.onload=res;s.onerror=rej;document.head.appendChild(s)})}
function paintMap(){if(!window.L)return;const el=$('#kb-map');
 if(!map){map=L.map(el,{worldCopyJump:true,minZoom:1,maxZoom:6,zoomControl:true,attributionControl:true}).setView([30,-60],2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:6,attribution:'© OpenStreetMap contributors'}).addTo(map);
  layers=L.layerGroup().addTo(map);night=L.layerGroup().addTo(map);
  L.circleMarker([KY.lat,KY.lon],{radius:8,color:'#000',weight:2,fillColor:'#d5a63a',fillOpacity:1}).addTo(map).bindTooltip('Kentucky',{permanent:false});}
 paintNight();paintPaths()}
function paintNight(){if(!map)return;night.clearLayers();const s=sunPos(new Date());
 [[0,.22],[-6,.16],[-12,.16]].forEach(([h,o])=>{try{L.polygon(nightPoly(s,h),{stroke:false,fillColor:'#0a0a2a',fillOpacity:o,interactive:false}).addTo(night)}catch(e){}});
 L.marker([s.lat,s.lon],{icon:L.divIcon({className:'kb-sun',html:'☀',iconSize:[26,26],iconAnchor:[13,13]}),interactive:false,keyboard:false}).addTo(night)}
function paintPaths(){if(!map)return;layers.clearLayers();let n=0,tot=0;
 const add=(rows,kind)=>{(rows||[]).forEach(r=>{const code=Number(r.band);if(sel.size&&!sel.has(code))return;const p=g4c(r.loc);if(!p)return;const c=Number(r.c);tot+=c;n++;
  const col=BCOL[code]||'#fff',nm=(BANDS.find(b=>b[0]===code)||[0,'?'])[1];
  L.polyline([[KY.lat,KY.lon],[p.lat,p.lon]],{color:col,weight:Math.min(4,1+Math.log10(c+1)),opacity:.55,interactive:false}).addTo(layers);
  L.circleMarker([p.lat,p.lon],{radius:Math.min(9,3+Math.log2(c+1)),color:'#111',weight:1,fillColor:col,fillOpacity:.9}).addTo(layers).bindTooltip(`${nm} • ${r.loc.toUpperCase()} • ${c} report${c===1?'':'s'} • ${kind==='heard'?'heard Kentucky':'Kentucky heard them'}${r.d?' • up to '+Math.round(r.d*0.621371).toLocaleString()+' mi':''}`)})};
 if(dir!=='hearing')add(state.heard,'heard');if(dir!=='heard')add(state.hearing,'hearing');
 $('#kb-mapnote').textContent=(state.heard||state.hearing)?`${n} paths shown • ${tot.toLocaleString()} reports in the last 2 hours. Tap a dot for details. Colors match the band buttons.`:'WSPR path data is unavailable right now.'}
function paintChips(){const box=$('#kb-bands');box.innerHTML='<button type="button" class="kb-chip" data-b="all" aria-pressed="'+(sel.size===0)+'">ALL BANDS</button>'+BANDS.map(([c,n])=>`<button type="button" class="kb-chip" data-b="${c}" aria-pressed="${sel.has(c)}" style="--bc:${BCOL[c]}"><i></i>${n}</button>`).join('');
 box.querySelectorAll('button').forEach(b=>b.onclick=()=>{const v=b.dataset.b;if(v==='all')sel.clear();else{const c=Number(v);sel.has(c)?sel.delete(c):sel.add(c)}paintChips();paintPaths()})}
function paintAll(){paintTop();paintHeat();paintSpots();paintMap();const e=state.errs&&state.errs.length?'Could not load: '+state.errs.join(', ')+'. Showing what is available.':'';$('#kb-status').textContent=e}
async function start(){
 paintChips();
 root.querySelectorAll('#kb-scale .kb-chip').forEach(b=>b.onclick=()=>{scale=b.dataset.s;root.querySelectorAll('#kb-scale .kb-chip').forEach(x=>x.setAttribute('aria-pressed',x===b));paintHeat()});
 root.querySelectorAll('#kb-dir .kb-chip').forEach(b=>b.onclick=()=>{dir=b.dataset.d;root.querySelectorAll('#kb-dir .kb-chip').forEach(x=>x.setAttribute('aria-pressed',x===b));paintPaths()});
 $('#kb-refresh').onclick=async()=>{const b=$('#kb-refresh');b.disabled=true;await load(true);paintAll();setTimeout(()=>b.disabled=false,3000)};
 paintTop();
 try{await ensureLeaflet()}catch(e){$('#kb-map').innerHTML='<p class="kb-empty">The map library could not load.</p>'}
 await load(false);paintAll();setTimeout(()=>map&&map.invalidateSize(),200);
 timer=setInterval(()=>{if(!det.open||document.hidden)return;paintTop();paintNight()},60000);
 setInterval(async()=>{if(!det.open||document.hidden)return;if(Date.now()-state.t>MAXAGE){await load(false);paintAll()}},120000)}
})();
