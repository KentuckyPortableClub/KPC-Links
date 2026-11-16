/* KPC POTA door for the browser (KPC owner, 2026-11-16, handoff item 7, v5): spots come from the club spot file on the data-only live-spots branch (one club reader asks POTA every 5 minutes); a page reads POTA's spot list directly only when that file is more than 30 minutes old or cannot be read, at most once per 5 minutes per browser and never while the tab is hidden; the page shows how old the spots are (kpcSpotAge); a state's park list is kept in the browser for 24 hours; polls pause while the tab is hidden. The same copy is in every page script that needs it (tests/test_pota_door_nov16.py). */
window.KPCPota=window.KPCPota||(function(){const SPOTS='https://raw.githubusercontent.com/KentuckyPortableClub/KPC-Links/live-spots/spots.json',STALE=18e5,GAP=3e5,DAY=864e5,DK='kpcPotaDirect';let sp=null,spAt=0,spSaved=0,tick=0;
function lsGet(k){try{return JSON.parse(localStorage.getItem(k)||'null')}catch(_){return null}}
function lsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(_){}}
async function direct(){const c=lsGet(DK);if(document.hidden||(c&&Date.now()-c.t<GAP))return c&&Array.isArray(c.spots)?c:null;lsSet(DK,{t:Date.now(),spots:c&&Array.isArray(c.spots)?c.spots:[]});
 const r=await fetch('https://api.pota.app/spot/activator');if(!r.ok)throw new Error('POTA '+r.status);const a=await r.json();const d={t:Date.now(),spots:Array.isArray(a)?a:[]};lsSet(DK,d);return d}
function age(){return spSaved?Math.max(0,Math.round((Date.now()-spSaved)/1e3)):null}
function badge(){if(typeof document==='undefined'||!document.body)return;let e=document.getElementById('kpcSpotAge');
 if(!e){e=document.createElement('div');e.id='kpcSpotAge';e.setAttribute('aria-live','polite');e.style.cssText='position:fixed;right:8px;bottom:8px;z-index:9999;font:12px sans-serif;background:rgba(0,0,0,.72);color:#fff;padding:2px 8px;border-radius:10px;pointer-events:none';document.body.appendChild(e)}
 if(!tick)tick=setInterval(badge,3e4);const s=age();e.textContent=s===null?'Spots: age unknown':'Spots '+(s<60?'under 1 min':Math.round(s/60)+' min')+' old'}
async function spots(){if(sp&&Date.now()-spAt<6e4){badge();return sp}let a=null,saved=0,file=null;
 try{const r=await fetch(SPOTS+'?t='+Math.floor(Date.now()/6e4),{cache:'no-store'});if(r.ok){const j=await r.json();if(j&&Array.isArray(j.spots)){file=j;saved=1e3*(+j.saved||0);if(Date.now()-saved<=STALE)a=j.spots}}}catch(_){}
 if(!a){let d=null;try{d=await direct()}catch(e){if(!file&&!sp)throw e}
  if(d&&(!file||d.t>saved)){a=d.spots;saved=d.t}else if(file)a=file.spots;else if(sp){a=sp;saved=spSaved}else a=[]}
 sp=a;spAt=Date.now();spSaved=saved;badge();return sp}
function spotsResponse(){return spots().then(a=>({ok:true,status:200,json:async()=>a}),()=>({ok:false,status:0,json:async()=>[]}))}
async function parkList(loc,ms){const k='kpcPotaList:'+loc;let c=null;try{c=JSON.parse(localStorage.getItem(k)||'null')}catch(_){}if(c&&Array.isArray(c.rows)&&Date.now()-c.t<DAY)return c.rows;
 const ctl=typeof AbortController!=='undefined'?new AbortController():null,tm=ctl&&setTimeout(()=>ctl.abort(),ms||30000);
 try{const r=await fetch('https://api.pota.app/location/parks/'+encodeURIComponent(loc),ctl?{signal:ctl.signal}:{});if(!r.ok)throw new Error('POTA '+r.status);const rows=await r.json();try{localStorage.setItem(k,JSON.stringify({t:Date.now(),rows}))}catch(_){}return rows}
 catch(e){if(c&&Array.isArray(c.rows))return c.rows;throw e}finally{if(tm)clearTimeout(tm)}}
function poll(fn,ms){let last=Date.now();const id=setInterval(()=>{if(document.hidden)return;last=Date.now();fn()},ms);document.addEventListener('visibilitychange',()=>{if(!document.hidden&&Date.now()-last>ms){last=Date.now();fn()}});return id}
return{spots,spotsResponse,parkList,poll,age,SPOTS}})();
/* KPC QRM check (Opus, Oct 23 2026; Brandon: 'if someone was going to spot at 14.284 but someone was spotted 5 minutes
   ago at 14.286 give a warning … you may cause QRM, are you sure you want to spot here? Same for cw … ft8 and 4 is
   perfectly fine'). One rule for every place a station spots ITSELF (Spot Me page; the Logger has the same rule inline).
     KPCQrm.check(kHz, mode, myCall) -> Promise of '' (clear) or the warning text to put in a confirm()
   Room each side: SSB 3 kHz, AM 6, FM 10, CW / RTTY 1, PSK 0.5; FT8 / FT4 / FT2 / JS8 never warn (one shared sub-band by
   design). Spots up to 20 minutes old count. Reads POTA's spot list; if it can't, it says nothing. */
(function (G) {
  const ROOM = { SSB: 3, AM: 6, FM: 10, CW: 1, RTTY: 1, PSK31: 0.5, PSK: 0.5 };
  const base = c => { c = String(c || '').toUpperCase().trim(); const p = c.split('/').filter(Boolean); return p.length ? p.reduce((a, b) => (b.length > a.length ? b : a)) : ''; };
  const kh = f => { f = +f; return !isFinite(f) || f <= 0 ? null : f < 1000 ? f * 1000 : f; };
  const mhz = k => (k / 1000).toFixed(k % 1 ? 4 : 3).replace(/0+$/, '').replace(/\.$/, '');
  const ms = t => { const s = String(t || ''); const d = Date.parse(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + 'Z'); return isFinite(d) ? d : 0; };
  async function check(k, mode, me) {
    const m = String(mode || '').toUpperCase(), g = ROOM[/^(USB|LSB|PHONE)$/.test(m) ? 'SSB' : m];
    k = kh(k); if (!g || !k) return '';
    let L = [];
    try { const r = await KPCPota.spotsResponse(); L = r.ok ? await r.json() : []; } catch (e) { return ''; }
    const now = Date.now(), mine = base(me);
    const near = (Array.isArray(L) ? L : []).map(x => Object.assign({}, x, { _k: kh(x.frequency), _t: ms(x.spotTime) }))
      .filter(x => x._k && base(x.activator) !== mine && Math.abs(x._k - k) <= g && now - x._t < 20 * 60000)
      .sort((a, b) => Math.abs(a._k - k) - Math.abs(b._k - k)).slice(0, 3);
    if (!near.length) return '';
    const ago = x => { const n = Math.max(0, Math.round((now - x._t) / 60000)); return n < 1 ? 'just now' : n === 1 ? '1 minute ago' : n + ' minutes ago'; };
    return '⚠ Possible QRM\n\n' + near.map(x => `${x.activator} was spotted on ${mhz(x._k)} ${ago(x)}` + (x.reference ? ` (${x.reference})` : '')).join('\n') +
      `.\n\nSpotting on ${mhz(k)} may put you on top of ${near.length > 1 ? 'them' : 'that station'}. Are you sure you want to spot here?`;
  }
  G.KPCQrm = { check, ROOM };
})(window);
