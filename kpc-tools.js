/* KPC Tools — shared code. Edit MEMBERS to change the club roster. */
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
async function data(){if(!_data)_data=fetch('kpc-ky-data.json').then(r=>r.json());return _data}
async function counties(){if(!_counties)_counties=fetch('kpc-ky-counties.json').then(r=>r.json());return _counties}
async function countyOf(lat,lon){const C=await counties();for(const c of C)if(c.r.some(r=>pip(lon,lat,r)))return c.n;return null}
const fmtDate=d=>{d=String(d);return d.length===8?new Date(+d.slice(0,4),+d.slice(4,6)-1,+d.slice(6,8)).toLocaleDateString([],{month:'short',day:'numeric',year:'numeric'}):d};
const ok=q=>q>=10;
const cty=c=>{c=String(c||'');if(/^multiple/i.test(c)||/see official/i.test(c))return c.replace(/^see official site$/i,'County: see official site')||'';return c+(c.includes('/')?' Counties':' County')}; // a valid POTA activation is 10+ QSOs

/* Activation history for every Kentucky park in the guide.
   Returns {ref:[[callsign,yyyymmdd,qsos],...]} — cached in this browser for 12 hours. */
async function history(onProgress,force){
 const D=await data(),refs=D.parks.map(p=>p.c);
 if(!force){try{const c=JSON.parse(localStorage.getItem(CACHE_KEY)||'null');if(c&&Date.now()-c.t<CACHE_HOURS*36e5&&Object.keys(c.d).length>=refs.length*0.9){onProgress&&onProgress(refs.length,refs.length,c.t);return{hist:c.d,time:c.t,failed:c.f||[]}}}catch(e){}}
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
function navToggle(){const t=document.querySelector('.menu-toggle'),n=document.querySelector('.nav-links');if(!t)return;
 t.addEventListener('click',()=>{const o=n.classList.toggle('open');t.setAttribute('aria-expanded',String(o))})}
function leafletMap(id){const m=L.map(id,{scrollWheelZoom:false}).setView([37.75,-85.7],7);
 L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'© OpenStreetMap contributors'}).addTo(m);return m}
async function countyLayer(m){const C=await counties();const g=L.layerGroup();
 C.forEach(c=>c.r.forEach(r=>L.polygon(r.map(([x,y])=>[y,x]),{color:'#1d5a3a',weight:.7,opacity:.55,fill:false,interactive:false}).addTo(g)));g.addTo(m);return g}
const links={pota:r=>`https://pota.app/#/park/${r}`,sota:r=>`https://sotl.as/summits/${r}`,kff:r=>`https://logsearch.wwff.co/directory/${r}`,
 qrz:c=>`https://www.qrz.com/db/${encodeURIComponent(base(c))}`,gmap:(a,b)=>`https://www.google.com/maps/search/?api=1&query=${a},${b}`,
 dir:(a,b,o)=>`https://www.google.com/maps/dir/?api=1${o?`&origin=${o[0]},${o[1]}`:''}&destination=${a},${b}`,wx:(a,b)=>`https://weather.com/weather/today/l/${a},${b}`};
document.addEventListener('DOMContentLoaded',navToggle);
return{MEMBERS,esc,base,isMember,miles,grid,data,counties,countyOf,history,progressUI,leafletMap,countyLayer,links,fmtDate,ok,cty};
})();
