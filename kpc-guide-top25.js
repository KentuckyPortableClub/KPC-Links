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
let D=null;

function rows(list,key){
 return list.map(p=>{
  const ok=isFinite(p.la)&&isFinite(p.lo)&&p.la;
  const map=ok?`<a href="${gps(p.la,p.lo)}" target="_blank" rel="noopener" title="Open the park's map point in Google Maps">GPS MAP</a>`:'';
  const pota=`<a href="${potaUrl(p.c)}" target="_blank" rel="noopener" title="Park page on pota.app">POTA PAGE</a>`;
  const badge=KM?KM.badge(p.c):'';
  const hide=KM&&KM.filtering()&&!KM.show(p.c);
  return `<tr class="g-keep${hide?' km-hide':''}"><td class="rk">${p.r}</td>`+
   `<td class="ref c-ref"><a href="${potaUrl(p.c)}" target="_blank" rel="noopener">${esc(p.c)}</a></td>`+
   `<td class="nm"><b>${esc(p.n)}${p.a===0?'<span class="never'+(KM?' g-print-only':'')+'" title="Nobody has a valid activation here yet">NEVER ACTIVATED</span>':''}</b>`+
   `<small>${esc(cty(p.co))}</small>${badge?`<div class="no-print">${badge}</div>`:''}`+
   `<span class="mo"><a href="${potaUrl(p.c)}" target="_blank" rel="noopener">${esc(p.c)} →</a>${ok?`<a href="${gps(p.la,p.lo)}" target="_blank" rel="noopener">GPS MAP →</a>`:''}</span></td>`+
   `<td class="n${key==='a'?' key':''}">${fmt(p.a)}</td><td class="n${key==='q'?' key':''}">${fmt(p.q)}</td>`+
   `<td class="go c-go">${pota}${map}</td></tr>`}).join('')}

function render(){
 if(!D)return;
 $('b1').innerHTML=rows(D.qsos||[],'q')||'<tr><td colspan="6">No parks listed.</td></tr>';
 $('b2').innerHTML=rows(D.acts||[],'a')||'<tr><td colspan="6">No parks listed.</td></tr>';
 const x=day(D.updated);
 if(x)$('snap').textContent=`${MONTHS[x.m]} ${x.y} reference snapshot.`;
 $('upd').textContent=(D.live?'LIVE FROM POTA • ':'UPDATED ')+longDate(D.updated).toUpperCase()+(D.parks?` • ${D.parks} KENTUCKY PARKS RANKED`:'');
 $('pfoot').textContent='Updated '+longDate(D.updated)+' • kentuckyportableclub.github.io/KPC-Links/kpc-guide-top25.html';
 if(KM){const seen=new Set(),sp=[];[...(D.qsos||[]),...(D.acts||[])].forEach(p=>{if(!seen.has(p.c)){seen.add(p.c);sp.push({ref:p.c,la:p.la,lo:p.lo})}});KM.ensure(sp)}
 document.documentElement.dataset.ready='1'}

function rank(stats,parks){
 const all=[];parks.forEach(p=>{const s=stats[p.c];if(s)all.push({c:p.c,n:p.n,co:p.co||'',la:p.la,lo:p.lo,a:s[0],q:s[1]})});
 const top=f=>all.slice().sort(f).slice(0,25).map((p,i)=>Object.assign({},p,{r:i+1}));
 return{parks:all.length,qsos:top((a,b)=>a.q-b.q||a.a-b.a||num(a.c)-num(b.c)),acts:top((a,b)=>a.a-b.a||a.q-b.q||num(a.c)-num(b.c))}}

async function jget(u,ms){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms||15000);
 try{const r=await fetch(u,{signal:c.signal,cache:'no-cache'});if(!r.ok)throw new Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}}

async function live(){
 const b=$('live'),m=$('msg');b.disabled=true;m.textContent='Asking POTA for every Kentucky park’s numbers…';
 try{const [j,ky]=await Promise.all([jget('https://api.pota.app/location/parks/US-KY',20000),jget('kpc-ky-data.json',20000)]);
  const st={};(Array.isArray(j)?j:[]).forEach(x=>{const r=String(x.reference||'').toUpperCase(),a=+x.activations,q=+(x.qsos??x.contacts);if(/^US-\d+$/.test(r)&&isFinite(a)&&isFinite(q))st[r]=[a,q]});
  const R=rank(st,(ky&&ky.parks)||[]);
  if(R.parks<50)throw new Error('too few parks');
  const t=new Date(),iso=`${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')}`;
  D=Object.assign(R,{updated:iso,live:true});render();
  m.textContent='Showing live numbers from POTA, ranked just now.';b.textContent='REFRESH LIVE NUMBERS'}
 catch(e){m.textContent='Could not reach POTA right now. Showing the weekly list. Try again in a minute.'}
 finally{b.disabled=false}}

if(KM){KM.bar($('km-bar'));window.addEventListener('kpcmine',render)}
$('live').addEventListener('click',live);
jget('kpc-top25.json').then(j=>{D=j;render()}).catch(()=>{
 $('upd').textContent='COULD NOT LOAD THE LIST';
 $('msg').textContent='The saved list did not load. Tap GET LIVE POTA NUMBERS, or download the PDF.';
 document.documentElement.dataset.ready='1'});
})();
