/* KPC Top 25 low-activity Kentucky POTA parks (kpc-guide-top25.html).
   Reads kpc-top25.json, which the "KPC Top 25" GitHub Action refreshes every Monday from POTA's public park
   numbers (.github/scripts/kpc_top25.py). "Get live POTA numbers" ranks the parks again in this browser,
   straight from api.pota.app, using the same rules:
     List 1: lowest total QSOs first; activation count breaks ties.
     List 2: lowest total activations first; total QSOs breaks ties.
     Any tie left goes to the lower reference number. */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const esc=t=>String(t??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const KM=window.KPCMine||null;
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
const day=s=>{const m=String(s||'').match(/^(\d{4})-(\d{2})-(\d{2})/);return m?{y:+m[1],m:+m[2]-1,d:+m[3]}:null};
const longDate=s=>{const x=day(s);return x?`${MONTHS[x.m]} ${x.d}, ${x.y}`:''};
const cty=c=>{c=String(c||'');if(!c||/^multiple/i.test(c)||/see official/i.test(c))return c.replace(/^see official site$/i,'County: see official site');return c+(c.includes('/')?' Counties':' County')};
const num=r=>{const n=parseInt(String(r).split('-')[1],10);return isFinite(n)?n:1e9};
const fmt=n=>Number.isFinite(+n)?(+n).toLocaleString('en-US'):'—';
const potaUrl=r=>`https://pota.app/#/park/${r}`;
const gps=(a,b)=>`https://www.google.com/maps/search/?api=1&query=${a},${b}`;
let D=null,KY={};

function rows(list,key){
 return list.map(p=>{
  const ok=isFinite(p.la)&&isFinite(p.lo)&&p.la;
  const map=ok?`<a href="${gps(p.la,p.lo)}" target="_blank" rel="noopener" title="Open the park's map point in Google Maps">GPS MAP</a>`:'';
  const pota=`<a href="${potaUrl(p.c)}" target="_blank" rel="noopener" title="Park page on pota.app">POTA PAGE</a>`;
  const badge=KM?KM.badge(p.c):'';
  const k=KY[p.c];if(k){p.n=k.n;p.co=k.co||p.co;if(isFinite(k.la)){p.la=k.la;p.lo=k.lo}}
  return `<tr class="g-keep"><td class="rk">${p.r}</td>`+
   `<td class="ref c-ref"><a href="${potaUrl(p.c)}" target="_blank" rel="noopener">${esc(p.c)}</a></td>`+
   `<td class="nm"><b>${esc(p.n)}${p.a===0?'<span class="never'+(KM?' g-print-only':'')+'" title="Nobody has a valid activation here yet">NEVER ACTIVATED</span>':''}</b>`+
   `<small>${esc(cty(p.co))}</small>${badge?`<div class="no-print">${badge}</div>`:''}`+
   `<span class="mo"><a href="${potaUrl(p.c)}" target="_blank" rel="noopener">${esc(p.c)} →</a>${ok?`<a href="${gps(p.la,p.lo)}" target="_blank" rel="noopener">GPS MAP →</a>`:''}</span></td>`+
   `<td class="n${key==='a'?' key':''}">${fmt(p.a)}</td><td class="n${key==='q'?' key':''}">${fmt(p.q)}</td>`+
   `<td class="go c-go">${pota}${map}</td></tr>`}).join('')}

/* My Parks filter on (NEW TO ME / ATNO): build a full 25 from every ranked park, skipping the ones the filter hides,
   numbered 1-25. The printed PDF always uses the plain club list. */
function pool(){
 if(D.all&&D.all.length)return D.all.map(x=>{const k=KY[x[0]]||{};return{c:x[0],a:+x[1],q:+x[2],n:k.n||x[0],co:k.co||'',la:k.la,lo:k.lo}});
 const seen=new Set(),out=[];[...(D.qsos||[]),...(D.acts||[])].forEach(p=>{if(!seen.has(p.c)){seen.add(p.c);out.push(p)}});return out}
const BYQ=(a,b)=>a.q-b.q||a.a-b.a||num(a.c)-num(b.c),BYA=(a,b)=>a.a-b.a||a.q-b.q||num(a.c)-num(b.c);
function mineTop(sorter){const s=pool().sort(sorter);return{cand:s.slice(0,80),top:s.filter(p=>KM.show(p.c)).slice(0,25).map((p,i)=>Object.assign({},p,{r:i+1}))}}
function render(){
 if(!D)return;
 const f=KM&&KM.filtering()&&!window.matchMedia('print').matches;
 let L1=D.qsos||[],L2=D.acts||[],cand=[];
 if(f){const x=mineTop(BYQ),y=mineTop(BYA);L1=x.top;L2=y.top;cand=[...x.cand,...y.cand]}
 const note=f?'<tr class="no-print"><td colspan="6" class="t25-note">Your list: parks hidden by your My Parks filter are skipped, so these are the next lowest. Turn the filter off to see the club list.</td></tr>':'';
 $('b1').innerHTML=(rows(L1,'q')||'<tr><td colspan="6">No parks listed.</td></tr>')+note;
 $('b2').innerHTML=(rows(L2,'a')||'<tr><td colspan="6">No parks listed.</td></tr>')+note;
 const x=day(D.updated);
 if(x)$('snap').textContent=`${MONTHS[x.m]} ${x.y} reference snapshot.`;
 $('upd').textContent=(D.live?'LIVE FROM POTA • ':'UPDATED ')+longDate(D.updated).toUpperCase()+(D.parks?` • ${(+D.parks).toLocaleString()} ${pName(WHERE).toUpperCase()} PARKS RANKED`:'');
 $('pfoot').textContent='Updated '+longDate(D.updated)+' • kentuckyportableclub.github.io/KPC-Links/kpc-guide-top25.html';
 if(KM){const seen=new Set(),sp=[];[...(D.qsos||[]),...(D.acts||[]),...cand].forEach(p=>{if(!seen.has(p.c)){seen.add(p.c);sp.push({ref:p.c,la:p.la,lo:p.lo})}});KM.ensure(sp)}
 document.documentElement.dataset.ready='1'}

function rank(stats,parks){
 const all=[];parks.forEach(p=>{const s=stats[p.c];if(s)all.push({c:p.c,n:p.n,co:p.co||'',la:p.la,lo:p.lo,a:s[0],q:s[1]})});
 const top=f=>all.slice().sort(f).slice(0,25).map((p,i)=>Object.assign({},p,{r:i+1}));
 return{parks:all.length,qsos:top((a,b)=>a.q-b.q||a.a-b.a||num(a.c)-num(b.c)),acts:top((a,b)=>a.a-b.a||a.q-b.q||num(a.c)-num(b.c))}}

async function jget(u,ms){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms||15000);
 try{const f=(/^data\/parkinfo\//.test(u)&&window.KPC&&KPC.dataUrl)?KPC.dataUrl(u,{signal:c.signal,cache:'no-cache'}):fetch(u,{signal:c.signal,cache:'no-cache'});const r=await f;if(!r.ok)throw new Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}}


/* Oct 24 (Brandon: 'top 25 only does ky....can it expand'): a WHERE picker. Kentucky keeps the weekly list (and the PDF);
   every other US state, Canadian province and 64 countries rank from the nightly park files (data/parkinfo: activations
   field 7, QSOs field 9). GET LIVE POTA NUMBERS works for US states and provinces (api.pota.app/location/parks/<loc>). */
const STN={AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',DC:'District of Columbia',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming'};
const PRV={AB:'Alberta',BC:'British Columbia',MB:'Manitoba',NB:'New Brunswick',NL:'Newfoundland and Labrador',NS:'Nova Scotia',NT:'Northwest Territories',NU:'Nunavut',ON:'Ontario',PE:'Prince Edward Island',QC:'Quebec',SK:'Saskatchewan',YT:'Yukon'};
const CTRY='AG AI AT AU AW BB BE BL BM BQ BS BZ CH CR CU CW CZ DE DK DM DO EE ES FI FR GB GD GL GP GT HN HR HT HU IE IT JM JP KN KY LC LT LU LV MF MQ MS MX NI NL NO PA PL PM PT RO SE SI SK SV SX TC TT VC VG'.split(' ');
let DNm=null;try{DNm=new Intl.DisplayNames(['en'],{type:'region'})}catch(e){}
const cName=p=>{try{const n=DNm&&DNm.of(p);if(n&&n!==p)return n}catch(e){}return p};
const pName=k=>/^US-/.test(k)?STN[k.slice(3)]||k:/^CA-/.test(k)?PRV[k.slice(3)]||k:cName(k);
let WHERE=(()=>{try{return new URLSearchParams(location.search).get('where')||localStorage.getItem('kpcT25Place')||'US-KY'}catch(e){return 'US-KY'}})();
async function placeData(){
 if(WHERE==='US-KY')return null;
 const f=/^US-/.test(WHERE)?'data/parkinfo/'+WHERE+'.json':/^CA-/.test(WHERE)?'data/parkinfo/CA.json':'data/parkinfo/'+WHERE+'.json';
 const J=await jget(f,30000);const st={},parks=[];
 Object.entries(J.parks||{}).forEach(([r,v])=>{if(/^CA-/.test(WHERE)&&v[10]!==WHERE.slice(3))return;const a=+v[7],q=+v[9];if(!isFinite(a)||!isFinite(q))return;st[r]=[a,q];parks.push({c:r,n:v[0],co:'',la:v[5],lo:v[6]})});
 const R=rank(st,parks);R.all=parks.map(p=>[p.c,st[p.c][0],st[p.c][1]]);parks.forEach(p=>{KY[p.c]=p});
 return Object.assign(R,{updated:J.updated||''})}
function labels(){const n=pName(WHERE);document.querySelectorAll('.t25P').forEach(e=>{e.textContent=e.closest('.t25-print-head')?n.toUpperCase():n});
 const b=$('live');if(b)b.hidden=!/^(US|CA)-/.test(WHERE);const m=$('msg');if(m)m.textContent=WHERE==='US-KY'?'Updated every Monday from POTA. Tap for the latest numbers right now.':'From POTA\'s numbers, refreshed every night.'+(/^(US|CA)-/.test(WHERE)?' Tap for the latest right now.':'')}
function fillWhere(){const o=L=>L.map(([k,n])=>`<option value="${k}"${k===WHERE?' selected':''}>${esc(n)}</option>`).join('');
 $('t25W').innerHTML=`<optgroup label="United States">${o(Object.keys(STN).map(s=>['US-'+s,STN[s]]).sort((a,b)=>a[1].localeCompare(b[1])))}</optgroup><optgroup label="Canada">${o(Object.keys(PRV).map(s=>['CA-'+s,PRV[s]]).sort((a,b)=>a[1].localeCompare(b[1])))}</optgroup><optgroup label="Other countries">${o(CTRY.map(p=>[p,cName(p)]).sort((a,b)=>a[1].localeCompare(b[1])))}</optgroup>`;
 $('t25W').onchange=async()=>{WHERE=$('t25W').value;try{localStorage.setItem('kpcT25Place',WHERE);const u=new URL(location.href);u.searchParams.set('where',WHERE);history.replaceState(null,'',u)}catch(e){}labels();await loadPlace()}}
async function loadPlace(){
 $('upd').textContent='LOADING…';
 if(WHERE==='US-KY'){const [j,ky]=await Promise.all([jget('kpc-top25.json'),jget('kpc-ky-data.json').catch(()=>null)]);((ky&&ky.parks)||[]).forEach(p=>{KY[p.c]=p});D=j;render();return}
 try{D=await placeData();render()}catch(e){$('upd').textContent='COULD NOT LOAD '+pName(WHERE).toUpperCase();$('b1').innerHTML=$('b2').innerHTML='<tr><td colspan="6">The park list did not load. Try again in a minute.</td></tr>'}}
async function live(){
 const b=$('live'),m=$('msg');b.disabled=true;m.textContent='Asking POTA for every park’s numbers…';
 try{if(WHERE!=='US-KY'){const j=await jget('https://api.pota.app/location/parks/'+WHERE,25000);const st={},parks=[];(Array.isArray(j)?j:[]).forEach(x=>{const r=String(x.reference||'').toUpperCase(),a=+x.activations,q=+(x.qsos??x.contacts);if(r&&isFinite(a)&&isFinite(q)){st[r]=[a,q];parks.push({c:r,n:x.name||r,co:'',la:+x.latitude,lo:+x.longitude})}});
   if(parks.length<3)throw new Error('none');const R=rank(st,parks);R.all=parks.map(p=>[p.c,st[p.c][0],st[p.c][1]]);parks.forEach(p=>{KY[p.c]=p});const t=new Date();D=Object.assign(R,{updated:t.toISOString().slice(0,10),live:true});render();m.textContent='Showing live numbers from POTA, ranked just now.';b.textContent='REFRESH LIVE NUMBERS';return}
  const [j,ky]=await Promise.all([jget('https://api.pota.app/location/parks/US-KY',20000),jget('kpc-ky-data.json',20000)]);
  const st={};(Array.isArray(j)?j:[]).forEach(x=>{const r=String(x.reference||'').toUpperCase(),a=+x.activations,q=+(x.qsos??x.contacts);if(/^US-\d+$/.test(r)&&isFinite(a)&&isFinite(q))st[r]=[a,q]});
  const R=rank(st,(ky&&ky.parks)||[]);
  if(R.parks<50)throw new Error('too few parks');
  const t=new Date(),iso=`${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')}`;
  ((ky&&ky.parks)||[]).forEach(p=>{KY[p.c]=p});
  R.all=Object.keys(st).filter(r=>KY[r]).map(r=>[r,st[r][0],st[r][1]]);
  D=Object.assign(R,{updated:iso,live:true});render();
  m.textContent='Showing live numbers from POTA, ranked just now.';b.textContent='REFRESH LIVE NUMBERS'}
 catch(e){m.textContent='Could not reach POTA right now. Showing the weekly list. Try again in a minute.'}
 finally{b.disabled=false}}

if(KM){KM.bar($('km-bar'));window.addEventListener('kpcmine',render)}
$('live').addEventListener('click',live);
fillWhere();labels();
loadPlace().catch(()=>{
 $('upd').textContent='COULD NOT LOAD THE LIST';
 $('msg').textContent='The saved list did not load. Tap GET LIVE POTA NUMBERS.';
 document.documentElement.dataset.ready='1'});
})();
