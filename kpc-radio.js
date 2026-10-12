/* KPC Live: HF receiver (WebSDR / KiwiSDR / OpenWebRX) + worldwide spots with filters.
   Receivers are other people's servers. Most only run on plain http, and a secure (https) page like ours
   is not allowed to show an http page inside it, so those open tuned in their own tab instead.
   Spots come from Spothole (POTA, SOTA, WWFF, DX cluster, skimmers and more in one feed);
   if Spothole is down we read POTA and SOTA directly. */
(function(){
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const store={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};

/* ================= receiver ================= */
/* type: websdr (?tune=7200lsb)  kiwi (?f=7200lsbz10)  owrx (#freq=7200000,mod=lsb) */
const RX=[
 {id:'k3fef',name:'K3FEF WebSDR (Pennsylvania, USA)',type:'websdr',url:'http://k3fef.com:8901/'},
 /* Northern Utah runs separate receivers per band group: #1 (port 8901) only covers up through 40m,
    so anything above 40m goes to #2 (port 8902). A frequency a receiver doesn't cover just won't tune. */
 {id:'utah',name:'Northern Utah WebSDR (Utah, USA)',type:'websdr',url:'http://websdr1.sdrutah.org:8901/index1a.html',above:[[7300,'http://websdr2.sdrutah.org:8902/index1a.html']]},
 {id:'twente',name:'University of Twente WebSDR (Netherlands)',type:'websdr',url:'http://websdr.ewi.utwente.nl:8901/',note:'Hear North America from Europe'}
];
const BANDS=[['160m',1900,'lsb'],['80m',3850,'lsb'],['60m',5357,'usb'],['40m',7200,'lsb'],['30m',10136,'usb'],['20m',14250,'usb'],['17m',18130,'usb'],['15m',21300,'usb'],['12m',24950,'usb'],['10m',28400,'usb'],['WWV',10000,'am']];
const MODES=['lsb','usb','cw','am'];
let st=store.get('kpcRx',{rx:'k3fef',khz:7200,mode:'lsb',custom:''});
function rxList(){const l=RX.slice();if(st.custom)l.push({id:'custom',name:'My receiver: '+st.custom.replace(/^https?:\/\//,''),type:guessType(st.custom),url:st.custom});return l}
function curRx(){return rxList().find(r=>r.id===st.rx)||RX[0]}
function guessType(u){return /:8073\b|kiwi/i.test(u)?'kiwi':/openwebrx|#freq|:8073\b/i.test(u)?'owrx':/:8901\b|websdr/i.test(u)?'websdr':'kiwi'}
function rxBase(r,khz){let u=r.url;(r.above||[]).forEach(([k,v])=>{if(+khz>k)u=v});return u}
function tuneUrl(r,khz,mode){const base=rxBase(r,khz).replace(/[?#].*$/,'');const k=+(+khz).toFixed(2);
 if(r.type==='websdr')return base+'?tune='+k+mode;
 if(r.type==='owrx')return base+'#freq='+Math.round(k*1000)+',mod='+mode;
 return base.replace(/\/?$/,'/')+'?f='+k+mode+'z10'}
function bandOf(khz){const B=[[1800,2000,'160m'],[3500,4000,'80m'],[5330,5410,'60m'],[7000,7300,'40m'],[10100,10150,'30m'],[14000,14350,'20m'],[18068,18168,'17m'],[21000,21450,'15m'],[24890,24990,'12m'],[28000,29700,'10m'],[50000,54000,'6m'],[144000,148000,'2m'],[420000,450000,'70cm']];
 const b=B.find(x=>khz>=x[0]&&khz<=x[1]);return b?b[2]:(khz>=9995&&khz<=10005)||(khz>=4995&&khz<=5005)||(khz>=14995&&khz<=15005)?'WWV':''}
function sideband(khz){return khz<10000?'lsb':'usb'}
function fmtK(k){return (+k).toLocaleString(undefined,{maximumFractionDigits:2})}

function drawRx(){const box=$('rx-box');if(!box)return;const r=curRx(),url=tuneUrl(r,st.khz,st.mode),b=bandOf(st.khz);
 $('rx-sel').innerHTML=rxList().map(x=>`<option value="${esc(x.id)}"${x.id===r.id?' selected':''}>${esc(x.name)}</option>`).join('');
 $('rx-bands').innerHTML=BANDS.map(([l,k,m])=>`<button type="button" class="lv-chip" data-k="${k}" data-m="${m}" aria-pressed="${b===l||(l==='WWV'&&b==='WWV')}">${l}</button>`).join('');
 $('rx-modes').innerHTML=MODES.map(m=>`<button type="button" class="lv-chip" data-mode="${m}" aria-pressed="${m===st.mode}">${m.toUpperCase()}</button>`).join('');
 const f=$('rx-freq');if(document.activeElement!==f)f.value=st.khz;
 $('rx-now').innerHTML=`<b>${fmtK(st.khz)} kHz ${st.mode.toUpperCase()}</b>${b?' · '+b:''} · ${esc(r.name)}`;
 const open=$('rx-open');open.href=url;
 const frame=$('rx-frame'),blocked=$('rx-blocked'),secure=/^https:/i.test(r.url);
 if(secure){blocked.style.display='none';frame.style.display='block';if(frame.dataset.src!==url){frame.dataset.src=url;frame.src=url}}
 else{frame.style.display='none';if(frame.src&&frame.src!=='about:blank'){frame.src='about:blank';frame.dataset.src=''}blocked.style.display='flex';
  $('rx-btext').innerHTML=`<b>${esc(r.name)}</b> only runs on a plain (http) connection, so web browsers won't show it inside this page. Tap below to listen in its own tab, already tuned to <b>${fmtK(st.khz)} kHz ${st.mode.toUpperCase()}</b>. Keep that tab open: every band, mode or spot you pick here retunes it.`}
 store.set('kpcRx',st)}
let rxWin=null;
function retuneTab(){/* re-use one named tab so picking a spot doesn't open a pile of tabs */
 const r=curRx();if(/^https:/i.test(r.url))return;if(rxWin&&!rxWin.closed){try{rxWin.location.href=tuneUrl(r,st.khz,st.mode)}catch(e){}}}
function tune(khz,mode,go){st.khz=+khz;st.mode=mode||sideband(+khz);drawRx();retuneTab();if(go){const c=$('rx-card');if(c)c.scrollIntoView({behavior:'smooth',block:'start'})}}
function initRx(){if(!$('rx-box'))return;
 $('rx-bands').onclick=e=>{const b=e.target.closest('button');if(b)tune(b.dataset.k,b.dataset.m)};
 $('rx-modes').onclick=e=>{const b=e.target.closest('button');if(b){st.mode=b.dataset.mode;drawRx();retuneTab()}};
 $('rx-sel').onchange=e=>{st.rx=e.target.value;drawRx();retuneTab()};
 $('rx-form').onsubmit=e=>{e.preventDefault();let v=parseFloat($('rx-freq').value);if(!isFinite(v))return;if(v<100)v*=1000;/* typed MHz */
  if(v<100||v>30000){$('rx-freq').setCustomValidity('HF receivers cover 0.1 to 30 MHz');$('rx-freq').reportValidity();return}$('rx-freq').setCustomValidity('');tune(v,bandOf(v)==='WWV'?'am':(st.mode==='am'||st.mode==='cw'?st.mode:sideband(v)))};
 $('rx-open').onclick=e=>{e.preventDefault();rxWin=window.open($('rx-open').href,'kpc-websdr');if(!rxWin)location.href=$('rx-open').href};
 $('rx-btn').onclick=()=>$('rx-open').click();
 $('rx-add').onclick=()=>{const v=prompt('Paste the address of a KiwiSDR, WebSDR or OpenWebRX receiver (find one at rx.kiwisdr.com or websdr.org):',st.custom||'http://');
  if(v==null)return;const u=v.trim();if(!u){st.custom='';if(st.rx==='custom')st.rx=RX[0].id;drawRx();return}
  if(!/^https?:\/\/[^\s/]+/i.test(u)){alert('That doesn’t look like a web address. It should start with http:// or https://');return}
  st.custom=u;st.rx='custom';drawRx()};
 drawRx()}

/* ================= spots ================= */
const NEAR=['KY','IN','OH','WV','VA','TN','MO','IL'];
const USST=new Set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split(' '));
const CATS=['POTA','SOTA','WWFF','DX','RBN','OTHER'],CATL={POTA:'POTA',SOTA:'SOTA',WWFF:'WWFF',DX:'DX CLUSTER',RBN:'SKIMMER (RBN)',OTHER:'OTHER PROGRAMS'}; /* GMA, HEMA, WWBOTA and the like */
const SBANDS=['160m','80m','60m','40m','30m','20m','17m','15m','12m','10m','6m','2m'];
const SMODES=['SSB','CW','DIGITAL','OTHER'];
const AREAS=[['ky','Kentucky'],['near','Kentucky + neighbors'],['us','USA'],['NA','North America'],['EU','Europe'],['AS','Asia'],['SA','South America'],['AF','Africa'],['OC','Oceania'],['all','Worldwide']];
/* default view: POTA phone on 40m in the USA (new storage key so everyone starts there once) */
const F0=()=>({cats:['POTA'],bands:['40m'],modes:['SSB'],area:'us',q:''});
let F=store.get('kpcSpotF2',F0()),SHOWN=5;
let SP=[],srcNote='',lastLoad=0;
function modeGroup(m){m=String(m||'').toUpperCase();if(/SSB|LSB|USB|PHONE/.test(m))return'SSB';if(/^CW/.test(m))return'CW';if(/FT8|FT4|RTTY|PSK|JS8|DATA|DIGI|OLIVIA|MFSK|JT|SSTV|VARA|WSPR|Q65/.test(m))return'DIGITAL';return m?'OTHER':''}
function rxMode(m,khz){const g=modeGroup(m);return g==='CW'?'cw':/^AM$/i.test(m)?'am':sideband(khz)}
function cat(sig,source){const s=String(sig||'').toUpperCase(),o=String(source||'').toUpperCase();
 if(/POTA/.test(s)||(!s&&/POTA/.test(o)))return'POTA';if(/SOTA/.test(s)||(!s&&/SOTA/.test(o)))return'SOTA';if(/WWFF/.test(s)||(!s&&/WWFF/.test(o)))return'WWFF';
 if(s)return'OTHER';if(/RBN|SKIM/.test(o))return'RBN';if(/CLUSTER|DX/.test(o))return'DX';return o?'OTHER':'DX'}
function toKhz(f){f=Number(f);if(!isFinite(f)||f<=0)return null;return f<1000?f*1000:f<1e6?f:f/1000}
function toMs(t){if(t==null)return null;if(typeof t==='number')return t<1e12?t*1000:t;const s=String(t);const d=Date.parse(/[zZ]|[+-]\d\d:?\d\d$/.test(s)?s:s+'Z');return isFinite(d)?d:null}
function refsOf(x){const r=x.sig_refs||x.sig_ref||x.refs||[];const a=Array.isArray(r)?r:[r];
 return a.map(v=>typeof v==='string'?{id:v,name:''}:{id:v.id||v.ref||v.reference||'',name:v.name||''}).filter(v=>v.id)}
function normHole(x){const khz=toKhz(x.freq!=null?x.freq:x.frequency);if(!khz)return null;const refs=refsOf(x);
 return{call:String(x.dx_call||x.activator||x.call||'').toUpperCase(),khz,mode:String(x.mode||'').toUpperCase(),cat:cat(x.sig,x.source),label:x.sig||x.source||'',
  ref:refs.map(r=>r.id).join(', '),name:refs.map(r=>r.name).filter(Boolean).join(' / ')||x.sig_refs_names||x.dx_name||'',
  state:String(x.dx_state||'').toUpperCase(),country:x.dx_country||'',cont:String(x.dx_continent||'').toUpperCase(),grid:x.dx_grid||'',la:+(x.dx_latitude??x.dx_lat??NaN),lo:+(x.dx_longitude??x.dx_lon??NaN),
  t:toMs(x.time),comment:x.comment||'',by:x.de_call||''}}
function normPota(x){const khz=toKhz(x.frequency);if(!khz)return null;const loc=String(x.locationDesc||'');const st=(loc.match(/US-([A-Z]{2})/)||[])[1]||'';
 return{call:String(x.activator||'').toUpperCase(),khz,mode:String(x.mode||'').toUpperCase(),cat:'POTA',label:'POTA',ref:x.reference||'',name:x.name||'',state:st,country:/^US-/.test(loc)?'United States':'',cont:/^(US|CA|K|VE|XE)-/.test(loc)?'NA':'',grid:x.grid6||'',t:toMs(x.spotTime),comment:x.comments||'',by:x.spotter||''}}
function normSota(x){const khz=toKhz(x.frequency);if(!khz)return null;const ac=String(x.associationCode||'');const usa=/^W\d|^W[0-9]?[A-Z]/.test(ac);
 return{call:String(x.activatorCallsign||'').toUpperCase(),khz,mode:String(x.mode||'').toUpperCase(),cat:'SOTA',label:'SOTA',ref:(ac&&x.summitCode?ac+'/'+x.summitCode:x.summitCode||''),name:x.summitDetails||'',state:'',country:usa?'United States':'',cont:usa?'NA':'',grid:'',t:toMs(x.timeStamp),comment:x.comments||'',by:x.callsign||''}}
async function jget(u){const c=new AbortController(),tm=setTimeout(()=>c.abort(),15000);try{const r=await fetch(u,{cache:'no-store',signal:c.signal});if(!r.ok)throw new Error(r.status);return await r.json()}finally{clearTimeout(tm)}}
async function loadSpots(){const note=$('sp-note');if(note)note.textContent='Loading spots…';
 let out=null;
 for(const u of['https://spothole.app/api/v1/spots?limit=2000&max_age=3600','https://spothole.app/api/v1/spots?limit=1000']){try{const j=await jget(u);const a=Array.isArray(j)?j:(j&&Array.isArray(j.spots)?j.spots:null);if(a&&a.length){out=a.map(normHole).filter(Boolean);srcNote='Spothole (POTA, SOTA, WWFF, DX cluster, skimmers and more)';break}}catch(e){}}
 if(!out){out=[];const got=[];
  await Promise.all([jget('https://api.pota.app/spot/activator').then(a=>{(a||[]).forEach(x=>{const n=normPota(x);if(n)out.push(n)});got.push('POTA')}).catch(()=>{}),
   jget('https://api2.sota.org.uk/api/spots/50/all').then(a=>{(a||[]).forEach(x=>{const n=normSota(x);if(n)out.push(n)});got.push('SOTA')}).catch(()=>{})]);
  srcNote=got.length?got.join(' and ')+' directly (the all-in-one feed is not answering, so DX cluster and WWFF spots are missing right now)':''}
 /* newest spot per call + frequency */
 const seen=new Map();out.sort((a,b)=>(b.t||0)-(a.t||0)).forEach(s=>{const k=s.call+'|'+Math.round(s.khz);if(!seen.has(k))seen.set(k,s)});
 SP=[...seen.values()];lastLoad=Date.now();window.KPCSpots=SP;try{window.dispatchEvent(new CustomEvent('kpc-spots',{detail:SP}))}catch(e){}drawSpots()}
function inArea(s,a){if(a==='all')return true;
 const us=/United States|^USA?$/i.test(s.country)||/^(US|K)-/.test(s.ref)||USST.has(s.state);
 if(a==='ky')return s.state==='KY'||/US-KY/.test(s.ref);if(a==='near')return NEAR.includes(s.state);if(a==='us')return us;
 if(a==='NA')return s.cont==='NA'||us;return s.cont===a}
function filtered(){const q=F.q.trim().toUpperCase();return SP.filter(s=>(!F.cats.length||F.cats.includes(s.cat))&&(!F.bands.length||F.bands.includes(bandOf(s.khz)))&&(!F.modes.length||F.modes.includes(modeGroup(s.mode)))&&inArea(s,F.area)&&(!q||(s.call+' '+s.ref+' '+s.name+' '+s.comment).toUpperCase().includes(q)))}
function ago(t){if(!t)return'';const m=Math.max(0,Math.round((Date.now()-t)/60000));return m<1?'now':m<60?m+'m':Math.floor(m/60)+'h'}
function chips(id,list,sel,lab){$(id).innerHTML=`<button type="button" class="lv-chip" data-v="" aria-pressed="${!sel.length}">ALL</button>`+list.map(v=>`<button type="button" class="lv-chip" data-v="${v}" aria-pressed="${sel.includes(v)}">${lab?lab[v]:v}</button>`).join('')}
function drawFilters(){chips('sp-cats',CATS,F.cats,CATL);chips('sp-bands',SBANDS,F.bands);chips('sp-modes',SMODES,F.modes);
 $('sp-area').innerHTML=AREAS.map(([v,l])=>`<option value="${v}"${v===F.area?' selected':''}>${l}</option>`).join('');const q=$('sp-q');if(document.activeElement!==q)q.value=F.q}
/* KPC members: always pinned to the top in gold, whatever the filters (roster is MEMBERS in kpc-tools.js) */
const isKpc=c=>{try{if(typeof KPC!=='undefined'&&KPC.isMember)return KPC.isMember(c)}catch(e){}return['KZ4CP','N4BDW','KQ4HZK','K4ZSR'].includes(String(c||'').toUpperCase().split('/').reduce((a,b)=>b.length>a.length?b:a,''))};
function drawSpots(){const tb=$('sp-list');if(!tb)return;drawFilters();store.set('kpcSpotF2',F);
 const club=SP.filter(s=>isKpc(s.call)),L=filtered().filter(s=>!isKpc(s.call)),show=[...club,...L.slice(0,SHOWN)];
 $('sp-count').textContent=SP.length?`${(L.length+club.length).toLocaleString()} of ${SP.length.toLocaleString()} spots`+(club.length?` · ${club.length} KPC`:''):'';
 $('sp-note').textContent=SP.length?`From ${srcNote}. Last hour, newest first. Refreshes every minute.`:(lastLoad?'No spots could be loaded right now. Try again in a minute.':'Loading spots…');
 tb.innerHTML=(club.length?`<div class="sp-kpchead">&#9733; KPC MEMBERS ON THE AIR (${club.length}) <span>always shown first</span></div>`:'')+show.map((s,i)=>{const b=bandOf(s.khz),loc=[s.state,s.state?'':s.country].filter(Boolean).join(' ')||s.grid,k=i<club.length;
  return`${!k&&i===club.length&&club.length?'<div class="sp-kpchead sp-rest">ALL OTHER SPOTS (YOUR FILTERS)</div>':''}<div class="sp-row${k?' sp-kpc':''}"><div class="sp-a"><span class="sp-cat c-${s.cat}">${esc(s.cat==='OTHER'?(String(s.label||'OTHER')).toUpperCase():s.cat==='DX'?'DX':s.cat)}</span><b class="sp-call">${esc(s.call)}</b>${k?'<span class="sp-badge">KPC</span>':''}<span class="sp-t">${ago(s.t)}</span></div>
<div class="sp-b"><b>${fmtK(s.khz)}</b> kHz <span class="sp-m">${esc(s.mode||'?')}</span>${b?' · '+b:''}${loc?' · '+esc(loc):''}</div>
<div class="sp-c">${s.ref?`<span class="sp-ref">${esc(s.ref)}</span> `:''}${esc(s.name)}${s.comment?` <span class="sp-cm">“${esc(String(s.comment).slice(0,80))}”</span>`:''}</div>
<button type="button" class="sp-go" data-i="${i}" ${s.khz>30000?'disabled title="Above 30 MHz: HF receivers can’t tune this"':''}>&#9654; LISTEN</button></div>`}).join('')+(L.length?'':`<p class="sp-empty">${SP.length?'No '+(club.length?'other ':'')+'spots match these filters. Tap ALL on a row, pick another band, or SHOW EVERYTHING.':''}</p>`);
 if(L.length>SHOWN||SHOWN>5)tb.insertAdjacentHTML('beforeend',`<div class="sp-more">${L.length>SHOWN?`<button type="button" class="lv-chip" data-more="1">SHOW ${Math.min(20,L.length-SHOWN)} MORE (${(L.length-SHOWN).toLocaleString()} not shown)</button>`:''}${SHOWN>5?'<button type="button" class="lv-chip" data-less="1">SHOW FEWER</button>':''}</div>`);
 tb._show=show}
function initSpots(){if(!$('sp-list'))return;
 const tog=(key,id)=>$(id).onclick=e=>{const b=e.target.closest('button');if(!b)return;const v=b.dataset.v;if(!v)F[key]=[];else F[key]=F[key].includes(v)?F[key].filter(x=>x!==v):F[key].concat(v);SHOWN=5;drawSpots()};
 tog('cats','sp-cats');tog('bands','sp-bands');tog('modes','sp-modes');
 $('sp-area').onchange=e=>{F.area=e.target.value;SHOWN=5;drawSpots()};
 $('sp-q').oninput=e=>{F.q=e.target.value;SHOWN=5;clearTimeout(initSpots.t);initSpots.t=setTimeout(drawSpots,250)};
 $('sp-reset').onclick=()=>{F={cats:[],bands:[],modes:[],area:'all',q:''};SHOWN=5;drawSpots()};
 $('sp-list').onclick=e=>{if(e.target.closest('[data-more]')){SHOWN+=20;drawSpots();return}if(e.target.closest('[data-less]')){SHOWN=5;drawSpots();$('spots-card').scrollIntoView({behavior:'smooth',block:'start'});return}
  const b=e.target.closest('.sp-go');if(!b)return;const s=$('sp-list')._show[+b.dataset.i];if(!s)return;
  tune(s.khz,rxMode(s.mode,s.khz),true);
  const r=curRx();if(!/^https:/i.test(r.url)){rxWin=window.open(tuneUrl(r,st.khz,st.mode),'kpc-websdr')}};
 drawSpots();loadSpots();setInterval(()=>{if(!document.hidden)loadSpots()},60000);
 setInterval(()=>{if(!document.hidden&&SP.length)drawSpots()},30000)}

function start(){try{initRx()}catch(e){console.error(e)}try{initSpots()}catch(e){console.error(e)}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
window.KPCRadio={tune,tuneUrl,bandOf,modeGroup,cat,normHole,normPota,normSota};
})();
