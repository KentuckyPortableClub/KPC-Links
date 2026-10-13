/* KPC CW Practice: live CW spots you can click to listen to.
   Spots come from POTA and SOTA (CW only). Clicking LISTEN opens your chosen WebSDR in its own tab,
   already tuned to that frequency in CW mode. Then use "Decode a tab" to decode it here.
   Receivers are other people's plain-http servers, so they can't be shown inside this page. */
(function(){
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const store={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};

const RX=[
 {id:'k3fef',name:'K3FEF (Pennsylvania)',short:'Pennsylvania',url:'http://k3fef.com:8901/',la:41.32,lo:-74.8},
 {id:'utah',name:'Northern Utah',short:'Utah',url:'http://websdr1.sdrutah.org:8901/index1a.html',above:[[7300,'http://websdr2.sdrutah.org:8902/index1a.html']],la:41.55,lo:-112.1},
 {id:'twente',name:'Twente (Netherlands)',short:'Netherlands',url:'http://websdr.ewi.utwente.nl:8901/',la:52.24,lo:6.85}
];
/* AUTO receiver: HF skips over nearby stations, so each band has a sweet-spot distance (low bands shorter,
   high bands longer). AUTO picks the receiver closest to that distance from the station. Rough guide only. */
const SWEET={'160m':500,'80m':500,'60m':700,'40m':800,'30m':1200,'20m':1500,'17m':1800,'15m':2000,'12m':2000,'10m':2000};
const STC={AL:[32.8,-86.8],AZ:[34.3,-111.7],AR:[34.9,-92.4],CA:[37.2,-119.5],CO:[39,-105.5],CT:[41.6,-72.7],DE:[39,-75.5],FL:[28.6,-82.4],GA:[32.7,-83.4],ID:[44.4,-114.6],IL:[40,-89.2],IN:[39.9,-86.3],IA:[42.1,-93.5],KS:[38.5,-98.4],KY:[37.5,-85.3],LA:[31,-92],ME:[45.4,-69.2],MD:[39,-76.8],MA:[42.3,-71.8],MI:[44.3,-85.4],MN:[46.3,-94.3],MS:[32.7,-89.7],MO:[38.4,-92.5],MT:[47,-109.6],NE:[41.5,-99.8],NV:[39.3,-116.6],NH:[43.7,-71.6],NJ:[40.2,-74.7],NM:[34.4,-106.1],NY:[42.9,-75.5],NC:[35.6,-79.4],ND:[47.5,-100.5],OH:[40.3,-82.8],OK:[35.6,-97.5],OR:[43.9,-120.6],PA:[40.9,-77.8],RI:[41.7,-71.5],SC:[33.9,-80.9],SD:[44.4,-100.2],TN:[35.9,-86.4],TX:[31.5,-99.3],UT:[39.3,-111.7],VT:[44.1,-72.7],VA:[37.5,-78.8],WA:[47.4,-120.5],WV:[38.6,-80.6],WI:[44.6,-89.9],WY:[43,-107.5]};
// SOTA associations (US by region code, Canada, Europe); anything else = no AUTO pick
const SASSOC={W0C:'CO',W0D:'SD',W0I:'IA',W0M:'MO',W0N:'NE',W1:'MA',W2:'NY',W3:'PA',W4A:'AL',W4C:'NC',W4G:'GA',W4K:'KY',W4T:'TN',W4V:'VA',W5A:'AR',W5M:'MS',W5N:'NM',W5O:'OK',W5T:'TX',W6:'CA',W7A:'AZ',W7I:'ID',W7M:'MT',W7N:'NV',W7O:'OR',W7U:'UT',W7W:'WA',W7Y:'WY',W8M:'MI',W8O:'OH',W8V:'WV',W9:'IL',W0:'CO'};
function gridXY(g){g=String(g||'').trim();if(!/^[A-R]{2}\d{2}/i.test(g))return null;g=g.toUpperCase();let lo=(g.charCodeAt(0)-65)*20-180+(+g[2])*2,la=(g.charCodeAt(1)-65)*10-90+(+g[3]);
 if(/^[A-X]{2}$/i.test(g.slice(4,6))){lo+=(g.charCodeAt(4)-65)*5/60+2.5/60;la+=(g.charCodeAt(5)-65)*2.5/60+1.25/60}else{lo+=1;la+=.5}return[la,lo]}
function assocXY(a){a=String(a||'').toUpperCase();const st=SASSOC[a]||SASSOC[a.slice(0,2)];if(st)return STC[st];if(/^VE|^VA/.test(a))return[45.5,-76];if(/^(G|M|2|F|D|E[AIS]|HB|OE|O[KMN]|S[MP]|I|P[AI]|L[AXY]|9A|S5|YO|LZ|SV|CT|OH|OZ|TF)/.test(a))return[50,8];return null}
const mi=(a,b)=>{const r=Math.PI/180,x=(b[0]-a[0])*r,y=(b[1]-a[1])*r,h=Math.sin(x/2)**2+Math.cos(a[0]*r)*Math.cos(b[0]*r)*Math.sin(y/2)**2;return 7917.6*Math.asin(Math.min(1,Math.sqrt(h)))};
function bestRx(s){const b=band(s.khz);if(!s.xy||!SWEET[b])return null;
 return RX.map(r=>{const d=mi(s.xy,[r.la,r.lo]);return{r,d,sc:Math.abs(Math.log(Math.max(d,50)/SWEET[b]))}}).sort((a,b)=>a.sc-b.sc)[0]}
function rxFor(s){if(st.rx!=='auto')return{r:RX.find(x=>x.id===st.rx)||RX[0],auto:false};const b=bestRx(s);return b?{r:b.r,d:b.d,auto:true}:{r:RX[0],auto:true,guess:true}}
function tuneUrl(r,khz){let u=r.url;(r.above||[]).forEach(([k,v])=>{if(+khz>k)u=v});return u.replace(/[?#].*$/,'')+'?tune='+(+(+khz).toFixed(2))+'cw'}
function band(k){const B=[[1800,2000,'160m'],[3500,4000,'80m'],[5330,5410,'60m'],[7000,7300,'40m'],[10100,10150,'30m'],[14000,14350,'20m'],[18068,18168,'17m'],[21000,21450,'15m'],[24890,24990,'12m'],[28000,29700,'10m'],[50000,54000,'6m']];const b=B.find(x=>k>=x[0]&&k<=x[1]);return b?b[2]:''}
// Spot times: POTA sends UTC without a zone; SOTA may add an offset. Unreadable times are dropped (they used to show as 'now').
function toMs(t){if(t==null||t==='')return null;if(typeof t==='number')return t<1e12?t*1000:t;const x=String(t).trim();const d=Date.parse(/[zZ]|[+-]\d\d:?\d\d$/.test(x)?x:x+'Z');return isFinite(d)?d:null}
const MAXAGE=30*60e3; // only spots from the last 30 minutes
function ago(t){if(!t)return'';const m=Math.max(0,Math.round((Date.now()-t)/6e4));return m<1?'now':m<60?m+' min':Math.round(m/60)+' h'}

let MEMBERS=['KZ4CP','N4BDW','KQ4HZK','K4ZSR']; // replaced by the club roster in kpc-tools.js when it loads
fetch('kpc-tools.js').then(r=>r.ok?r.text():'').then(t=>{const m=t.match(/MEMBERS\s*=\s*\[([^\]]*)\]/);if(m){const l=[...m[1].matchAll(/'([A-Za-z0-9/]+)'/g)].map(x=>x[1].toUpperCase());if(l.length)MEMBERS=l;draw()}}).catch(()=>{});
const base=c=>String(c||'').toUpperCase().split('/').sort((a,b)=>b.length-a.length)[0]||'';

let st=store.get('kpcCwSpots',{rx:'auto',f:'all'});if(!['auto','k3fef','utah','twente'].includes(st.rx))st.rx='auto';if(!['all','pota','sota','ky','kpc'].includes(st.f))st.f='all';
let spots=[],loaded=false,timer=null,err='',stamp=0;

async function load(){
 const out=[];let ok=0;
 try{const r=await fetch('https://api.pota.app/spot/activator',{cache:'no-store'});if(r.ok){ok++;const j=await r.json();
  (Array.isArray(j)?j:[]).forEach(s=>{if(String(s.mode||'').toUpperCase()!=='CW')return;const k=+s.frequency;if(!(k>0))return;
   out.push({call:String(s.activator||''),ref:String(s.reference||''),name:String(s.name||''),loc:String(s.locationDesc||''),khz:k,t:toMs(s.spotTime),prog:'POTA',xy:(isFinite(+s.latitude)&&+s.latitude&&isFinite(+s.longitude)?[+s.latitude,+s.longitude]:null)||gridXY(s.grid6)||gridXY(s.grid4)||STC[(String(s.locationDesc||'').match(/^US-([A-Z]{2})/)||[])[1]]||null})})}}catch(e){}
 try{const r=await fetch('https://api2.sota.org.uk/api/spots/50/all',{cache:'no-store'});if(r.ok){ok++;const j=await r.json();
  (Array.isArray(j)?j:[]).forEach(s=>{if(String(s.mode||'').toUpperCase()!=='CW')return;const k=parseFloat(s.frequency)*1000;if(!(k>0))return;
   out.push({call:String(s.activatorCallsign||''),ref:(s.associationCode||'')+'/'+(s.summitCode||''),name:String(s.summitDetails||''),loc:String(s.associationCode||''),khz:k,t:toMs(s.timeStamp),prog:'SOTA',xy:assocXY(s.associationCode)})})}}catch(e){}
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
 el.innerHTML=(err?`<p class="cws-empty">${esc(err)}</p>`:'')+(l.length?l.map((s,i)=>{const kpc=MEMBERS.includes(base(s.call)),rx=rxFor(s),utc=new Date(s.t).toISOString().slice(11,16);
  return `<div class="cws-row${kpc?' kpc':''}">
  <div class="cws-k"><b>${(s.khz/1000).toFixed(3)}</b><span>${band(s.khz)}</span></div>
  <div class="cws-who"><div class="cws-l1"><b>${esc(s.call)}</b> <span class="cws-p">${s.prog}</span>${kpc?' <span class="cws-p kpc">KPC</span>':''}${s.loc?` <span class="cws-st">${esc(s.loc)}</span>`:''}</div>
   <div class="cws-l2">${esc(s.ref)}${s.name?' · '+esc(s.name):''}</div>
   <div class="cws-l3"><span class="cws-age${Date.now()-s.t<6e5?' fresh':''}">⏱ ${ago(s.t)==='now'?'just now':ago(s.t)+' ago'}</span> <span class="cws-utc">${utc}Z</span> · 🎧 ${esc(rx.r.short)}${rx.auto?(rx.guess?' (auto: location unknown)':` (auto, ${Math.round(rx.d).toLocaleString()} mi)`):''}</div></div>
  <button type="button" class="cws-go" data-i="${i}">🎧 LISTEN</button></div>`}).join(''):(err?'':'<p class="cws-empty">No CW spots in the last 30 minutes for this choice. Tap ALL, or check back in a few minutes.</p>'));
 el._list=l;
 const u=$('cwsUpd');if(u)u.textContent=loaded?`${l.length} CW spot${l.length===1?'':'s'} · newest first · last 30 minutes · updated ${new Date(stamp).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})}`:'';
}
function listen(s){
 const rx=rxFor(s),r=rx.r;
 window.open(tuneUrl(r,s.khz),'kpc-websdr');
 const m=$('cwsMsg');if(m)m.innerHTML=`<b>Opened ${esc(r.name)} WebSDR on ${(s.khz/1000).toFixed(3)} MHz CW for ${esc(s.call)}.</b>${rx.auto&&!rx.guess?` AUTO picked it because it is about ${Math.round(rx.d).toLocaleString()} miles from the station, a good distance on ${band(s.khz)}.`:''}
 <ol class="rx-how"><li>Listen in that tab first. Can you hear the CW clearly? If it is weak or you hear nothing, pick another receiver under <b>LISTEN ON</b> and tap LISTEN again.</li>
 <li>Come back to this tab and tap <b>🖥 DECODE A TAB (WEBSDR)</b> at the top of the decoder.</li>
 <li>In the box that pops up, choose the <b>Chrome Tab</b> (or <b>Tab</b>) choice, click the WebSDR tab, turn on <b>Also share tab audio</b>, then click <b>Share</b>.</li>
 <li>Watch the waterfall: the CW shows as a bright line. Leave AUTO-FIND on, or turn it off and tap that line.</li></ol>
 Already decoding that tab? It keeps decoding when you retune; no need to restart.`;
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
