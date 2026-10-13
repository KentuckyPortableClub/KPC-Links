/* KPC CW Practice: live CW spots you can click to listen to.
   Spots come from POTA and SOTA (CW only). Clicking LISTEN opens your chosen WebSDR in its own tab,
   already tuned to that frequency in CW mode. Then use "Decode a tab" to decode it here.
   Receivers are other people's plain-http servers, so they can't be shown inside this page. */
(function(){
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const store={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};

const RX=[
 {id:'k3fef',name:'K3FEF (Pennsylvania)',url:'http://k3fef.com:8901/'},
 {id:'utah',name:'Northern Utah',url:'http://websdr1.sdrutah.org:8901/index1a.html',above:[[7300,'http://websdr2.sdrutah.org:8902/index1a.html']]},
 {id:'twente',name:'Twente (Netherlands)',url:'http://websdr.ewi.utwente.nl:8901/'}
];
function tuneUrl(r,khz){let u=r.url;(r.above||[]).forEach(([k,v])=>{if(+khz>k)u=v});return u.replace(/[?#].*$/,'')+'?tune='+(+(+khz).toFixed(2))+'cw'}
function band(k){const B=[[1800,2000,'160m'],[3500,4000,'80m'],[5330,5410,'60m'],[7000,7300,'40m'],[10100,10150,'30m'],[14000,14350,'20m'],[18068,18168,'17m'],[21000,21450,'15m'],[24890,24990,'12m'],[28000,29700,'10m'],[50000,54000,'6m']];const b=B.find(x=>k>=x[0]&&k<=x[1]);return b?b[2]:''}
// Spot times: POTA sends UTC without a zone; SOTA may add an offset. Unreadable times are dropped (they used to show as 'now').
function toMs(t){if(t==null||t==='')return null;if(typeof t==='number')return t<1e12?t*1000:t;const x=String(t).trim();const d=Date.parse(/[zZ]|[+-]\d\d:?\d\d$/.test(x)?x:x+'Z');return isFinite(d)?d:null}
const MAXAGE=30*60e3; // only spots from the last 30 minutes
function ago(t){const m=Math.max(0,Math.round((Date.now()-t)/6e4));return m<1?'now':m<60?m+' min':Math.round(m/60)+' h'}

let MEMBERS=['KZ4CP','N4BDW','KQ4HZK','K4ZSR']; // replaced by the club roster in kpc-tools.js when it loads
fetch('kpc-tools.js').then(r=>r.ok?r.text():'').then(t=>{const m=t.match(/MEMBERS\s*=\s*\[([^\]]*)\]/);if(m){const l=[...m[1].matchAll(/'([A-Za-z0-9/]+)'/g)].map(x=>x[1].toUpperCase());if(l.length)MEMBERS=l;draw()}}).catch(()=>{});
const base=c=>String(c||'').toUpperCase().split('/').sort((a,b)=>b.length-a.length)[0]||'';

let st=store.get('kpcCwSpots',{rx:'k3fef',f:'all'});if(!['all','pota','sota','ky','kpc'].includes(st.f))st.f='all';
let spots=[],loaded=false,timer=null,err='',stamp=0;

async function load(){
 const out=[];let ok=0;
 try{const r=await fetch('https://api.pota.app/spot/activator',{cache:'no-store'});if(r.ok){ok++;const j=await r.json();
  (Array.isArray(j)?j:[]).forEach(s=>{if(String(s.mode||'').toUpperCase()!=='CW')return;const k=+s.frequency;if(!(k>0))return;
   out.push({call:String(s.activator||''),ref:String(s.reference||''),name:String(s.name||''),loc:String(s.locationDesc||''),khz:k,t:toMs(s.spotTime),prog:'POTA'})})}}catch(e){}
 try{const r=await fetch('https://api2.sota.org.uk/api/spots/50/all',{cache:'no-store'});if(r.ok){ok++;const j=await r.json();
  (Array.isArray(j)?j:[]).forEach(s=>{if(String(s.mode||'').toUpperCase()!=='CW')return;const k=parseFloat(s.frequency)*1000;if(!(k>0))return;
   out.push({call:String(s.activatorCallsign||''),ref:(s.associationCode||'')+'/'+(s.summitCode||''),name:String(s.summitDetails||''),loc:'',khz:k,t:toMs(s.timeStamp),prog:'SOTA'})})}}catch(e){}
 err=ok?'':'Couldn’t reach the POTA or SOTA spot feeds. Try again in a minute.';
 // newest spot per activator+reference, last 60 minutes
 const seen=new Map();out.filter(s=>s.t&&Date.now()-s.t<MAXAGE&&s.t-Date.now()<5*60e3).sort((a,b)=>b.t-a.t).forEach(s=>{const k=base(s.call)+'|'+s.ref;if(!seen.has(k))seen.set(k,s)});
 spots=[...seen.values()].sort((a,b)=>b.t-a.t);loaded=true;stamp=Date.now();draw();
}
function filtered(){
 return spots.filter(s=>st.f==='all'||(st.f==='pota'&&s.prog==='POTA')||(st.f==='ky'&&(/US-KY/.test(s.loc)||/^W4K\//.test(s.ref)))||(st.f==='kpc'&&MEMBERS.includes(base(s.call)))||(st.f==='sota'&&s.prog==='SOTA'));
}
function draw(){
 const el=$('cwsList');if(!el)return;
 document.querySelectorAll('.cws-f').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.f===st.f)));
 if($('cwsRx'))$('cwsRx').value=st.rx;
 if(!loaded){el.innerHTML='<p class="cws-empty">Loading CW spots…</p>';return}
 const l=filtered();
 el.innerHTML=(err?`<p class="cws-empty">${esc(err)}</p>`:'')+(l.length?l.map((s,i)=>`<div class="cws-row${MEMBERS.includes(base(s.call))?' kpc':''}">
  <div class="cws-k"><b>${(s.khz/1000).toFixed(3)}</b><span>${band(s.khz)}</span></div>
  <div class="cws-who"><b>${esc(s.call)}</b> <span class="cws-p">${s.prog}</span>${MEMBERS.includes(base(s.call))?' <span class="cws-p kpc">KPC</span>':''}<br><small>${esc(s.ref)}${s.name?' · '+esc(s.name.slice(0,44)):''}${s.loc?' · '+esc(s.loc):''} · ${ago(s.t)}</small></div>
  <button type="button" class="cws-go" data-i="${i}">🎧 LISTEN</button></div>`).join(''):(err?'':'<p class="cws-empty">No CW spots in the last 30 minutes for this choice. Tap ALL, or check back in a few minutes.</p>'));
 el._list=l;
 const u=$('cwsUpd');if(u)u.textContent=loaded?`${l.length} CW spot${l.length===1?'':'s'} · newest first · last 30 minutes · updated ${new Date(stamp).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})}`:'';
}
function listen(s){
 const r=RX.find(x=>x.id===st.rx)||RX[0];
 window.open(tuneUrl(r,s.khz),'kpc-websdr');
 const m=$('cwsMsg');if(m)m.innerHTML=`Opened <b>${esc(r.name)}</b> on <b>${(s.khz/1000).toFixed(3)} MHz CW</b> for ${esc(s.call)}. Now come back and tap <b>🖥 DECODE A TAB</b> above, pick the WebSDR tab, and turn on <b>Share tab audio</b>. Already decoding that tab? It keeps decoding; no need to restart.`;
}
function init(){
 if(!$('cwsList'))return;
 document.querySelectorAll('.cws-f').forEach(b=>b.addEventListener('click',()=>{st.f=b.dataset.f;store.set('kpcCwSpots',st);draw()}));
 $('cwsRx').addEventListener('change',e=>{st.rx=e.target.value;store.set('kpcCwSpots',st)});
 $('cwsRefresh').addEventListener('click',()=>{loaded=false;draw();load()});
 $('cwsList').addEventListener('click',e=>{const b=e.target.closest('.cws-go');if(!b)return;const s=($('cwsList')._list||[])[+b.dataset.i];if(s)listen(s)});
 const on=m=>{clearInterval(timer);timer=null;if(m==='listen'){load();timer=setInterval(load,6e4)}};
 document.addEventListener('kpccw:mode',e=>on(e.detail));
 const app=document.getElementById('cwApp');if(app&&app.dataset.mode==='listen')on('listen');
 draw();
}
window.KPCCWSpots={load,get spots(){return spots.slice()},tuneUrl};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
