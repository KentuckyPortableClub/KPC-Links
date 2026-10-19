/* KPC "My Parks" checker — shared by the KPC Trip Planner, KY Trip Planner and KY Park Commander.
   Works for POTA parks and SOTA summits (WWFF is left out on purpose).
   - Your callsign is remembered on this device (key kpcMyCall) and shared by all three tools.
   - "Activated by you": POTA's public activation list for each park (10+ QSOs counts) and SOTA's public activation
     list for each summit (4+ QSOs counts). Looked up only for spots a tool is showing, saved for 12 hours per callsign.
   - ATNO (nobody has activated it yet): POTA's park list for each state and SOTA's summit list for each region,
     saved for a day.
   - Toggles NEW TO ME (hide what you've activated) and ATNO (only never-activated spots) are shared too (kpcMineOpt).
   A page calls KPCMine.bar(element) once, KPCMine.ensure(spots) after it draws, KPCMine.show(ref) to filter,
   KPCMine.badge(ref) for list/popup labels and KPCMine.mark(ref) for map dots, and listens for the window
   event 'kpcmine' to redraw when new answers arrive. No other site scripts are needed. */
(function(){
'use strict';
const POTA='https://api.pota.app',SOTA='https://api2.sota.org.uk/api';
const K_CALL='kpcMyCall',K_OPT='kpcMineOpt',K_MINE='kpcMine_v1',K_CNT='kpcAtno_v1';
const MINE_HRS=12,CNT_HRS=24,MAX_LOOKUPS=400;
const get=(k,d)=>{try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}};
const put=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}};
const esc=t=>String(t??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
/* KZ4CP/P, W4/KZ4CP, KZ4CP/M all mean KZ4CP: keep the longest part */
const base=c=>String(c||'').toUpperCase().trim().split('/').reduce((a,b)=>b.length>a.length?b:a,'');
const isPota=r=>/^[A-Z0-9]{1,3}-\d{4,5}$/.test(r);
const isSota=r=>/^[A-Z0-9]{1,4}\/[A-Z0-9]{2}-\d{3}$/.test(r);
const kind=r=>isPota(r)?'pota':isSota(r)?'sota':'';
const NEED={pota:10,sota:4};
async function jget(u,ms){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms||15000);
 try{const r=await fetch(u,{signal:c.signal});if(!r.ok)throw new Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}}

/* ---------- saved state ---------- */
let call=base(get(K_CALL,''));
/* A page can set window.KPC_MINE_NOSAVE=true before loading this file: its NEW TO ME / ATNO toggles then start OFF
   on every visit and are not saved or shared with the other tools (used by the Top 25 page). */
const NOSAVE=!!window.KPC_MINE_NOSAVE;
let opt=Object.assign({nw:0,atno:0,rare:0},NOSAVE?{}:get(K_OPT,{}));
let mine=get(K_MINE,null);if(!mine||mine.call!==call||!mine.d)mine={call,d:{}};   // d[ref]=[time, 2 activated | 1 tried | 0 never, last yyyymmdd]
let cnt=get(K_CNT,null);if(!cnt||!cnt.d||!cnt.g)cnt={g:{},d:{}};                     // d[ref]=activations by anyone, g[group]=time loaded
{const now=Date.now();for(const g in cnt.g)if(now-cnt.g[g]>CNT_HRS*36e5)delete cnt.g[g]}
const saveMine=()=>put(K_MINE,mine),saveCnt=()=>put(K_CNT,cnt);
const fresh=e=>e&&Date.now()-e[0]<MINE_HRS*36e5;

/* Pages that already loaded a full POTA history (Park Tracker, Park Checker) leave it in this browser:
   use it so those parks need no new lookups. */
function harvest(){if(!call)return;let n=0;
 const keys=['kpcHistory_v1'];try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(/^kpcHistLite_[A-Z]{2}$/.test(k))keys.push(k)}}catch(e){}
 keys.forEach(k=>{const c=get(k,null);if(!c||!c.d||Date.now()-c.t>MINE_HRS*36e5)return;
  for(const ref in c.d){const a=c.d[ref];if(!Array.isArray(a))continue;if(!fresh(mine.d[ref])){mine.d[ref]=judge(a.map(x=>({c:x[0],d:x[1],q:x[2]})),'pota',c.t);n++}
   if(cnt.d[ref]==null)cnt.d[ref]=a.filter(x=>x[2]>=10).length}});
 if(n)saveMine()}
function judge(list,k,t){let st=0,last='';list.forEach(x=>{if(base(x.c)!==call)return;const ok=!(x.q>=0)||x.q>=NEED[k];if(ok)st=2;else if(!st)st=1;const d=String(x.d||'').replace(/-/g,'').slice(0,8);if(d>last)last=d});return[t||Date.now(),st,last]}

/* ---------- ATNO counts ---------- */
let STATES=null;
function states(){if(!STATES)STATES=fetch('kpc-us-states.json').then(r=>r.json()).then(B=>B.map(b=>{let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;b.p.forEach(pl=>pl[0].forEach(([x,y])=>{x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}));return{a:b.a,p:b.p,bb:[x0,x1,y0,y1]}})).catch(()=>[]);return STATES}
function ringIn(x,y,r){let s=false;for(let i=0,j=r.length-1;i<r.length;j=i++){const[xi,yi]=r[i],[xj,yj]=r[j];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi+1e-15)+xi)s=!s}return s}
function stateOf(S,la,lo){let near=null;for(const s of S){const[x0,x1,y0,y1]=s.bb;if(lo<x0-.3||lo>x1+.3||la<y0-.3||la>y1+.3)continue;near=near||s.a;
 if(s.p.some(pl=>ringIn(lo,la,pl[0])&&!pl.slice(1).some(h=>ringIn(lo,la,h))))return s.a}return near}  /* near: parks on a shoreline just outside the border */
/* The KPC Trip Planner already downloads POTA's state lists: it hands them over here so they aren't fetched twice. */
function takePotaList(st,j){if(!Array.isArray(j))return;j.forEach(x=>{const r=String(x.reference||'').toUpperCase();if(r&&x.activations!=null)cnt.d[r]=+x.activations||0});cnt.g['P:'+st]=Date.now();saveCnt()}
async function loadCounts(spots){const want=new Set();
 const pota=spots.filter(s=>s.k==='pota'&&cnt.d[s.ref]==null&&isFinite(s.la)&&isFinite(s.lo));
 if(pota.length){const S=await states();pota.forEach(s=>{const a=stateOf(S,+s.la,+s.lo);if(a&&!cnt.g['P:'+a])want.add('P:'+a)})}
 spots.forEach(s=>{if(s.k==='sota'&&cnt.d[s.ref]==null){const m=s.ref.match(/^(.+)\/([A-Z0-9]{2})-\d{3}$/);if(m&&!cnt.g['S:'+m[1]+'/'+m[2]])want.add('S:'+m[1]+'/'+m[2])}});
 const list=[...want].filter(g=>!tried.has(g)).slice(0,12);if(!list.length)return false;
 await Promise.all(list.map(async g=>{if(tried.has(g))return;tried.add(g);
  try{if(g[0]==='P'){takePotaList(g.slice(2),await jget(POTA+'/location/parks/US-'+g.slice(2),15000));return}
   const j=await jget(SOTA+'/regions/'+g.slice(2),15000);const L=Array.isArray(j)?j:(j&&(j.summits||j.Summits))||[];
   L.forEach(s=>{const r=String(s.summitCode||s.SummitCode||'').toUpperCase(),n=s.activationCount??s.ActivationCount;if(r&&n!=null)cnt.d[r]=+n||0});cnt.g[g]=Date.now()}
  catch(e){/* that list can't be reached right now: those spots just show no ATNO answer */}}));
 saveCnt();return true}
const tried=new Set();

/* ---------- your activations ---------- */
async function lookup(ref,k){
 if(k==='pota'){const j=await jget(`${POTA}/park/activations/${ref}?count=all`);const a=Array.isArray(j)?j:[];
  if(cnt.d[ref]==null)cnt.d[ref]=a.filter(x=>+x.totalQSOs>=10).length;
  return judge(a.map(x=>({c:x.activeCallsign,d:x.qso_date,q:+x.totalQSOs})),'pota')}
 const j=await jget(`${SOTA}/activations/${ref}`);const a=Array.isArray(j)?j:[];
 if(cnt.d[ref]==null)cnt.d[ref]=a.length;
 return judge(a.map(x=>({c:x.ownCallsign||x.callsign||x.activatorCallsign||x.Callsign,d:x.activationDate||x.date,q:+(x.qsos??x.totalQSOs??x.qsoCount)})),'sota')}
let busy=false,again=null,last=[],prog=null,lastEmit=0,emitT=0;
function emit(now){clearTimeout(emitT);const go=()=>{lastEmit=Date.now();try{window.dispatchEvent(new CustomEvent('kpcmine'))}catch(e){}paint()};
 if(now||Date.now()-lastEmit>1500)go();else emitT=setTimeout(go,1500)}
/* spots: [{ref, la, lo}] or reference strings, nearest/most important first. Safe to call after every redraw. */
async function ensure(spots){
 spots=(spots||[]).map(s=>typeof s==='string'?{ref:s}:s).map(s=>({ref:String(s.ref||s.c||'').toUpperCase(),la:+s.la,lo:+s.lo})).map(s=>({...s,k:kind(s.ref)})).filter(s=>s.k);
 last=spots;paint();
 if(busy){again=spots;return}busy=true;
 try{
  /* emit only when something new arrived: pages redraw on 'kpcmine' and call ensure again */
  if(await loadCounts(spots))emit(true);
  if(call){harvest();
   const todo=spots.filter(s=>!fresh(mine.d[s.ref])&&!failed.has(s.ref));
   todo.forEach(s=>{if(cnt.d[s.ref]===0)mine.d[s.ref]=[Date.now(),0,'']});   /* nobody has activated it: you haven't either */
   const q=todo.filter(s=>!fresh(mine.d[s.ref])).slice(0,MAX_LOOKUPS);
   if(!todo.length){paint();return}
   if(q.length){let i=0,done=0,un=0;prog=[0,q.length];paint();
    const who=call;
    async function worker(){while(i<q.length){const s=q[i++];if(who!==call)return;
     try{mine.d[s.ref]=await lookup(s.ref,s.k)}catch(e){failed.add(s.ref)}
     done++;prog=[done,q.length];if(++un>=15){un=0;saveMine();saveCnt();emit()}else paint()}}
    await Promise.all(Array.from({length:6},worker));prog=null;saveMine();saveCnt()}
   emit(true)}
 }finally{busy=false;if(again){const a=again;again=null;setTimeout(()=>ensure(a),0)}}}
const failed=new Set();

/* ---------- answers for pages ---------- */
function status(ref){ref=String(ref||'').toUpperCase();const k=kind(ref);const e=mine.d[ref];
 return{k,mine:call&&k&&e?e[1]:null,last:e?e[2]:'',acts:k&&cnt.d[ref]!=null?cnt.d[ref]:null}}
function show(ref){if(!opt.nw&&!opt.atno&&!opt.rare)return true;const s=status(ref);
 if(!s.k)return false;                                /* WWFF and other programs aren't checked: hidden while a filter is on */
 if(opt.atno&&s.acts!==0)return false;
 if(opt.rare&&!(s.acts!=null&&s.acts<=5))return false;   /* RARE = never activated or 1-5 activations (same levels as kpc-rare.html) */
 if(opt.nw&&s.mine===2)return false;
 return true}
function mark(ref){const s=status(ref);return{done:s.mine===2,atno:s.acts===0,rare:s.acts!=null&&s.acts>=1&&s.acts<=5,acts:s.acts}}
const fmt=d=>d&&d.length===8?new Date(+d.slice(0,4),+d.slice(4,6)-1,+d.slice(6,8)).toLocaleDateString([],{month:'short',day:'numeric',year:'numeric'}):'';
function badge(ref){const s=status(ref);if(!s.k)return '';const out=[];
 if(s.acts===0)out.push('<span class="km-b km-atno" title="All Time New One: nobody has activated it yet">ATNO</span>');
 else if(s.acts!=null&&s.acts<=5)out.push(`<span class="km-b km-rare" title="Rarely activated">RARE · ${s.acts} ACTIVATION${s.acts===1?'':'S'}</span>`);
 else if(s.acts!=null&&s.acts<=20)out.push(`<span class="km-b km-unc" title="Not activated much">UNCOMMON · ${s.acts}</span>`);
 if(s.mine===2)out.push(`<span class="km-b km-done" title="You activated it${s.last?' (last '+fmt(s.last)+')':''}">&#10003; ACTIVATED${s.last?' '+esc(fmt(s.last)).toUpperCase():''}</span>`);
 else if(s.mine===1)out.push(`<span class="km-b km-tried" title="You tried but didn't reach ${NEED[s.k]} QSOs">TRIED, NOT COUNTED</span>`);
 else if(s.mine===0)out.push('<span class="km-b km-new">NEW TO YOU</span>');
 return out.length?`<span class="km-bs">${out.join('')}</span>`:''}

/* ---------- the control bar ---------- */
const bars=[];
function css(){if(document.getElementById('km-css'))return;const st=document.createElement('style');st.id='km-css';st.textContent=`
.km-bar{background:#fffaf0;color:#171717;border:1px solid #cbbf9f;border-left:5px solid #1d5a3a;border-radius:9px;padding:12px 14px;margin:0 0 14px;font-family:inherit;max-width:100%;box-sizing:border-box}
.km-bar *{box-sizing:border-box}
.km-row{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end}
.km-call{display:flex;flex-direction:column;gap:4px;font-size:11px;font-weight:900;letter-spacing:1.5px;color:#5a5446;flex:1 1 170px;min-width:0}
.km-call input{min-height:42px;padding:8px 11px;border:1px solid #cbbf9f;border-radius:7px;background:#fff;color:#171717;font-size:16px;font-weight:700;letter-spacing:1px;text-transform:uppercase;width:100%}
.km-bar button{min-height:42px;padding:8px 13px;border-radius:7px;font-size:12px;font-weight:900;letter-spacing:1px;cursor:pointer;font-family:inherit}
.km-go{background:#d5a63a;border:0;color:#0b0b0b}
.km-chip{background:#fff;border:1px solid #cbbf9f;color:#171717}
.km-chip[aria-pressed=true]{background:#171717;border-color:#171717;color:#f0c96b}
.km-chip[data-o=atno][aria-pressed=true]{background:#c2410c;border-color:#c2410c;color:#fff}
.km-chip[data-o=rare][aria-pressed=true]{background:#e08a2c;border-color:#e08a2c;color:#171717}
.km-st{font-size:13px;line-height:1.45;margin-top:8px;color:#2b2b2b}
.km-st i{display:block;height:5px;border-radius:3px;background:#1d5a3a;margin-top:5px;transition:width .3s}
.km-key{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12px;color:#5a5446;margin-top:6px}
.km-key span{display:inline-flex;align-items:center;gap:5px}
.km-dot{display:inline-block;width:12px;height:12px;border-radius:50%;background:#1d5a3a;border:2px solid #fff;box-shadow:0 0 0 1px #999}
.km-bs{display:inline-flex;flex-wrap:wrap;gap:4px;vertical-align:middle;margin:2px 0}
.km-b{display:inline-block;padding:2px 7px;border-radius:999px;font-size:10.5px;font-weight:900;letter-spacing:.8px;line-height:1.5;white-space:nowrap}
.km-done{background:#1d5a3a;color:#fff}.km-new{background:#e8f0fb;color:#1f4f8a;border:1px solid #9db7dd}
.km-tried{background:#f6e7c1;color:#6b4b00}.km-atno{background:#c2410c;color:#fff}.km-rare{background:#e08a2c;color:#171717}.km-unc{background:#f3e3b5;color:#5a4300}
@media(max-width:600px){.km-row>button{flex:1 1 auto}.km-call{flex-basis:100%}}`;document.head.appendChild(st)}
function bar(el,o){if(!el)return;css();o=o||{};
 el.classList.add('km-bar');
 el.innerHTML=`<div class="km-row"><label class="km-call">MY CALLSIGN (FOR NEW TO ME)<input type="text" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="e.g. KZ4CP" value="${esc(call)}"></label>
<button type="button" class="km-go">CHECK</button>
<button type="button" class="km-chip" data-o="nw" aria-pressed="${!!opt.nw}">NEW TO ME</button>
<button type="button" class="km-chip" data-o="atno" aria-pressed="${!!opt.atno}">ATNO</button>
<button type="button" class="km-chip" data-o="rare" aria-pressed="${!!opt.rare}" title="Never activated or 1-5 activations">RARE</button></div>
<div class="km-st" aria-live="polite"></div>
<div class="km-key"><span><span class="km-dot" style="opacity:.35"></span>Faded dot = you activated it</span><span><span class="km-dot" style="border-color:#c2410c;box-shadow:0 0 0 2px #c2410c"></span>Orange ring = ATNO (nobody has yet)</span><span><span class="km-dot" style="border-color:#e08a2c;box-shadow:0 0 0 2px #e08a2c"></span>Amber ring = rare (1-5 activations)</span><span>POTA parks and SOTA summits only</span></div>`;
 const inp=el.querySelector('input');
 const go=()=>{setCall(inp.value)};
 el.querySelector('.km-go').onclick=go;inp.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();go()}});
 el.querySelectorAll('.km-chip').forEach(b=>b.onclick=()=>{const k=b.dataset.o;
  if(k==='nw'&&!opt.nw&&!call){if(inp.value.trim()){setCall(inp.value)}else{inp.focus();say(el,'Type your callsign first, then tap NEW TO ME.');return}}
  opt[k]=opt[k]?0:1;if(!NOSAVE)put(K_OPT,opt);bars.forEach(x=>x.querySelectorAll('.km-chip').forEach(c=>c.setAttribute('aria-pressed',String(!!opt[c.dataset.o]))));emit(true)});
 bars.push(el);paint()}
function say(el,t){const s=el.querySelector('.km-st');if(s)s.innerHTML=t}
function setCall(c){c=base(c);if(c&&!/^[A-Z0-9]{3,10}$/.test(c)){bars.forEach(b=>say(b,'That doesn’t look like a callsign.'));return}
 if(c===call){if(last.length)ensure(last);return}
 call=c;put(K_CALL,c);mine={call:c,d:{}};saveMine();failed.clear();bars.forEach(b=>{const i=b.querySelector('input');if(i&&document.activeElement!==i)i.value=c});
 emit(true);if(last.length)ensure(last)}
function paint(){if(!bars.length)return;const L=last;let msg='';
 const n={done:0,new:0,atno:0,rare:0,unk:0};L.forEach(s=>{const x=status(s.ref);if(x.acts===0)n.atno++;else if(x.acts!=null&&x.acts<=5)n.rare++;if(x.mine===2)n.done++;else if(x.mine===0||x.mine===1)n.new++;else n.unk++});
 if(prog)msg=`Checking ${esc(call)}’s activations… ${prog[0]} of ${prog[1]} spots<i style="width:${Math.round(100*prog[0]/Math.max(1,prog[1]))}%"></i>`;
 else if(!L.length)msg=call?`Saved callsign: <b>${esc(call)}</b>. Search a place to see what you’ve activated there.`:'Type your callsign to mark the parks and summits you’ve already activated.';
 else if(!call)msg=`<b>${n.atno}</b> ATNO spot${n.atno===1?'':'s'} and <b>${n.rare}</b> rare in these results. Add your callsign to see which ones are new to you.`;
 else msg=`<b>${esc(call)}</b> in these results: <b>${n.done}</b> activated • <b>${n.new}</b> new to you • <b>${n.atno}</b> ATNO • <b>${n.rare}</b> rare${n.unk?` • ${n.unk} not checked${L.length>MAX_LOOKUPS?' (only the first '+MAX_LOOKUPS+' are checked; narrow the search for the rest)':' (POTA or SOTA did not answer)'}`:''}.`;
 if(opt.nw||opt.atno||opt.rare)msg+=` <b>Showing only ${[opt.atno&&'ATNO',!opt.atno&&opt.rare&&'rare',opt.nw&&'new-to-you'].filter(Boolean).join(' + ')} POTA/SOTA spots.</b>`;
 bars.forEach(b=>say(b,msg))}

window.KPCMine={bar,ensure,show,mark,badge,status,takePotaList,call:()=>call,opts:()=>({...opt}),filtering:()=>!!(opt.nw||opt.atno||opt.rare)};
})();
