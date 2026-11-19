/* KPC POTA door for the browser (KPC owner, 2026-11-16, handoff item 7, spot relay): spots come from the club spot relay, whose address is in kpc-spots.json at the top of the site (the ONE setting; read once per page); the relay asks POTA at most every 2 minutes and its x-kpc-spot-age header gives the age shown (kpcSpotAge). A page reads POTA's spot list directly only when the relay does not answer or its copy is more than 30 minutes old, at most once per 5 minutes per browser and never while the tab is hidden; a state's park list is kept in the browser for 24 hours; polls pause while the tab is hidden. The same copy is in every page script that needs it (tests/test_pota_door_nov16.py). */
window.KPCPota=window.KPCPota||(function(){const STALE=18e5,GAP=3e5,DAY=864e5,DK='kpcPotaDirect';let sp=null,spAt=0,spSaved=0,tick=0,cfg=null;
function root(){const p=location.pathname,i=p.indexOf('/KPC-Links/');return location.origin+(i>=0?p.slice(0,i+11):'/')}
async function setting(){if(cfg)return cfg;try{const r=await fetch(root()+'kpc-spots.json');if(r.ok){const j=await r.json();if(j&&/^https:\/\//.test(j.relay||''))cfg={relay:j.relay,hdr:j.age_header||'x-kpc-spot-age',stale:1e3*(+j.stale_seconds||0)||STALE}}}catch(_){}return cfg||{relay:'',hdr:'',stale:STALE}}
function lsGet(k){try{return JSON.parse(localStorage.getItem(k)||'null')}catch(_){return null}}
function lsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(_){}}
async function direct(){const c=lsGet(DK);if(document.hidden||(c&&Date.now()-c.t<GAP))return c&&Array.isArray(c.spots)?c:null;lsSet(DK,{t:Date.now(),spots:c&&Array.isArray(c.spots)?c.spots:[]});
 const r=await fetch('https://api.pota.app/spot/activator');if(!r.ok)throw new Error('POTA '+r.status);const a=await r.json();const d={t:Date.now(),spots:Array.isArray(a)?a:[]};lsSet(DK,d);return d}
function age(){return spSaved?Math.max(0,Math.round((Date.now()-spSaved)/1e3)):null}
function badge(){if(typeof document==='undefined'||!document.body)return;let e=document.getElementById('kpcSpotAge');
 if(!e){e=document.createElement('div');e.id='kpcSpotAge';e.setAttribute('aria-live','polite');e.style.cssText='position:fixed;right:8px;bottom:8px;z-index:9999;font:12px sans-serif;background:rgba(0,0,0,.72);color:#fff;padding:2px 8px;border-radius:10px;pointer-events:none';document.body.appendChild(e)}
 if(!tick)tick=setInterval(badge,3e4);const s=age();e.textContent=s===null?'Spots: age unknown':'Spots '+(s<60?'under 1 min':Math.round(s/60)+' min')+' old'}
async function spots(){if(sp&&Date.now()-spAt<6e4){badge();return sp}const c=await setting();let a=null,saved=0,relay=null,rs=0;
 if(c.relay)try{const r=await fetch(c.relay);if(r.ok){const j=await r.json(),arr=Array.isArray(j)?j:(j&&Array.isArray(j.spots)?j.spots:null),h=r.headers.get(c.hdr),s=h===null||h===''?NaN:+h;if(arr){relay=arr;rs=isFinite(s)?Date.now()-1e3*s:0;if(!rs||Date.now()-rs<=c.stale){a=arr;saved=rs}}}}catch(_){}
 if(!a){let d=null;try{d=await direct()}catch(e){if(!relay&&!sp)throw e}
  if(d&&(!relay||d.t>rs)){a=d.spots;saved=d.t}else if(relay){a=relay;saved=rs}else if(sp){a=sp;saved=spSaved}else a=[]}
 sp=a;spAt=Date.now();spSaved=saved;badge();return sp}
function spotsResponse(){return spots().then(a=>({ok:true,status:200,json:async()=>a}),()=>({ok:false,status:0,json:async()=>[]}))}
async function parkList(loc,ms){const k='kpcPotaList:'+loc;let c=null;try{c=JSON.parse(localStorage.getItem(k)||'null')}catch(_){}if(c&&Array.isArray(c.rows)&&Date.now()-c.t<DAY)return c.rows;
 const ctl=typeof AbortController!=='undefined'?new AbortController():null,tm=ctl&&setTimeout(()=>ctl.abort(),ms||30000);
 try{const r=await fetch('https://api.pota.app/location/parks/'+encodeURIComponent(loc),ctl?{signal:ctl.signal}:{});if(!r.ok)throw new Error('POTA '+r.status);const rows=await r.json();try{localStorage.setItem(k,JSON.stringify({t:Date.now(),rows}))}catch(_){}return rows}
 catch(e){if(c&&Array.isArray(c.rows))return c.rows;throw e}finally{if(tm)clearTimeout(tm)}}
function poll(fn,ms){let last=Date.now();const id=setInterval(()=>{if(document.hidden)return;last=Date.now();fn()},ms);document.addEventListener('visibilitychange',()=>{if(!document.hidden&&Date.now()-last>ms){last=Date.now();fn()}});return id}
return{spots,spotsResponse,parkList,poll,age,setting}})();
const KPCPotaDoor = window.KPCPota;   /* kept: kpc-pota.js (POTA sign-in) takes the name window.KPCPota later */
/* KPC app: THE REAL SPOT SOURCES (Opus, Oct 22, step 4; Brandon: 'Spots they not pota,wwff,sota,dx cluster etc').
   Each one is a poll function on the spot frame (kpc-spots.js), the same way the website's Hunters Lounge reads them
   (kpc-links/kpc-hunt.js):
     POTA   the club spot relay (kpc-spots…workers.dev), POTA itself as the backup   every 60 s
     SOTA   api2.sota.org.uk/api/spots/50/all      every 60 s
     WWFF + DX cluster   spothole.app (one ~1 MB list for both, a small hobby service: every 3 min, and only while one of
            the two is switched on; RBN skimmer spots are left out, they swamp the list)
   They go through AP.net.raw (no CORS wall in the app) and only run while the device is online; the frame does the rest
   (no doubles, filters, watchlist, tap = tune + log line). */
(function (G) {
  'use strict';
  const AP = G.KPCApp, SPx = G.KPCSpots;
  if (!AP || !SPx) return;
  const toKhz = f => { f = Number(f); if (!isFinite(f) || f <= 0) return null; return f < 1000 ? f * 1000 : f < 1e6 ? f : f / 1000; };
  const toMs = t => { if (t == null) return Date.now(); if (typeof t === 'number') return t < 1e12 ? t * 1000 : t; const s = String(t); const d = Date.parse(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + 'Z'); return isFinite(d) ? d : Date.now(); };
  async function getJson(url, ms) {
    const r = AP.net.raw ? await AP.net.raw(url, { ms: ms || 25000 }) : null;
    if (r) { if (!r.ok) throw new Error('HTTP ' + (r.status || r.err || '?')); return JSON.parse(r.text || 'null'); }
    const x = await AP.net.fetch(url, {}, ms || 25000); if (!x.ok) throw new Error('HTTP ' + x.status); return x.json();
  }

  /* Oct 26 (Brandon: 'make sure the spots show state'): POTA's locationDesc 'US-KY' (or 'US-KY,US-TN' on a line) → 'KY' / 'KY/TN'; Canada 'CA-ON' → 'ON' */
  const stOf = d => [...new Set(String(d || '').split(/[,\s]+/).map(c => (/^(US|CA|MX|AU)-([A-Z]{2,3})$/i.exec(c) || [])[2]).filter(Boolean).map(x => x.toUpperCase()))].join('/');
  /* Nov 17 (Brandon: 'here is my relay leave pota as a back up for the spots'): the club's spot relay first, POTA as the
     backup, the same way the website does it (KPC-Links window.KPCPota, PR #239). The relay is the club's free Cloudflare
     Worker (KPC-Links tools/kpc-spot-relay.js): it asks POTA at most once every 2 minutes for everybody and hands out the
     same list, so the club's apps do not each knock on POTA's door. Read-only: SPOT ME posts still go straight to POTA.
     Fall back to POTA itself when the relay is down, slow (6 s), or its copy is over 10 minutes old; asking POTA
     directly then goes at most once every 2 minutes. */
  /* website copy (sync.sh): spots come through the site's browser door (kpc-spots.json relay first, POTA only as its backup) */
  const PS = { via: '', age: null, at: 0, direct: 0 };
  async function potaList() { const L = await KPCPotaDoor.spots(); PS.via = 'the club spot feed'; PS.age = KPCPotaDoor.age(); PS.at = Date.now(); return L; }
  SPx.potaVia = () => PS.via ? { via: PS.via, age: PS.age == null ? null : PS.age + Math.round((Date.now() - PS.at) / 1000) } : null;
  SPx._potaReset = () => { PS.via = ''; PS.age = null; PS.at = 0; PS.direct = 0; };   /* tests only: forget the last direct POTA ask */
  const so0 = () => (SPx.sources() || {}).pota;
  SPx.source({ id: 'pota', label: 'POTA', every: 60, poll: async () => {
    const L = await potaList();
    const so = so0(); if (so) { const v = SPx.potaVia(); so.title = 'via ' + v.via + (v.age != null ? ', ' + (v.age < 60 ? 'under 1 min' : Math.round(v.age / 60) + ' min') + ' old' : '') + ' ·'; }
    /* Nov 19 2026 (to-do 1, alerts that say what they are): remember each park's name from the spots, so an alert can name the park */
    const PN = G.KPCParkNames = G.KPCParkNames || {}; (L || []).forEach(x => { if (x.reference && x.name) PN[String(x.reference).toUpperCase()] = String(x.name).slice(0, 60); });
    return (L || []).map(x => ({ call: x.activator, khz: toKhz(x.frequency), mode: x.mode, refs: x.reference ? [x.reference] : [], t: toMs(x.spotTime),
      comment: [x.name, x.locationDesc, x.comments].filter(Boolean).join(' · '), grid: x.grid6 || x.grid4 || '', spotter: x.spotter || '', la: +x.latitude, lo: +x.longitude, st: stOf(x.locationDesc) })).filter(s => s.khz);
  } });

  /* Nov 18 (Opus review): SOTA always gives MHz. toKhz() guesses the unit from the size, so a 23 cm spot (1296.2 MHz) or a
     10 GHz one (10368.1) was read as kHz and landed on 160 m / 30 m */
  const sotaKhz = f => { f = Number(f); return isFinite(f) && f > 0 ? Math.round(f * 1000 * 10) / 10 : null; };
  SPx.source({ id: 'sota', label: 'SOTA', every: 60, poll: async () => {
    const L = await getJson('https://api2.sota.org.uk/api/spots/50/all');
    return (L || []).map(x => ({ call: x.activatorCallsign, khz: sotaKhz(x.frequency), mode: x.mode, refs: x.associationCode ? [(x.associationCode + '/' + (x.summitCode || '')).toUpperCase()] : [],
      t: toMs(x.timeStamp), comment: [x.summitDetails, x.comments].filter(Boolean).join(' · '), spotter: x.callsign || '' })).filter(s => s.khz);
  } });

  /* one Spothole fetch feeds two sources */
  let holeLast = 0, holeBusy = false;
  async function hole() {
    if (holeBusy || Date.now() - holeLast < 170000) return;
    const off = SPx.S.off || []; if (['wwff', 'dx', 'progs', 'rbn'].every(k => off.includes(k))) return;
    holeBusy = true; holeLast = Date.now();
    try {
      const j = await getJson('https://spothole.app/api/v1/spots?max_age=2700', 60000);
      const L = Array.isArray(j) ? j : (j && j.spots) || [], W = [], D = [], O = [], RB = [];
      L.forEach(x => {
        const sig = String(x.sig || ''), src0 = String(x.source || '');
        if (/^(POTA|SOTA)$/i.test(sig) || x.qrt) return;
        const rbn = /RBN|SKIM/i.test(src0);
        const khz = toKhz(x.freq != null ? x.freq : x.frequency); if (!khz) return;
        const s = { call: x.dx_call || x.activator, khz, mode: x.mode, t: toMs(x.time), cont: String(x.dx_continent || '').toUpperCase(), la: +(x.dx_latitude ?? NaN), lo: +(x.dx_longitude ?? NaN), cty: x.dx_country || '', st: String(x.dx_state || x.state || '').toUpperCase().slice(0, 6), sig: String(x.sig || ''), spotter: x.de_call || '', comment: [x.dx_name, x.dx_country, x.comment].filter(Boolean).join(' · ') };
        const rr = x.sig_refs || [], refs = (Array.isArray(rr) ? rr : [rr]).map(v => typeof v === 'string' ? v : (v.id || v.ref || '')).filter(Boolean);
        if (rbn) { s.refs = []; s.comment = [x.comment, 'skimmer ' + (x.de_call || '')].filter(Boolean).join(' · '); RB.push(s); }   /* Oct 24: RBN skimmers, its own source (off to start: hundreds a minute) */
        else if (/WWFF/i.test(sig)) { s.refs = refs; if (s.refs.length) W.push(s); }
        else if (sig && !/^dxped/i.test(sig)) { s.refs = refs; s.comment = [sig + (refs.length ? ' ' + refs.join('+') : ''), s.comment].filter(Boolean).join(' · '); O.push(s); }   /* GMA, IOTA, WWBOTA, LLOTA, castles, lighthouses… */
        else { s.refs = []; D.push(s); }
      });
      if (!off.includes('wwff')) SPx.feed('wwff', W);
      if (!off.includes('dx')) SPx.feed('dx', D);
      if (!off.includes('progs')) SPx.feed('progs', O);
      if (!off.includes('rbn')) SPx.feed('rbn', RB.slice(-300));
      const so = SPx.sources(); ['wwff', 'dx', 'progs', 'rbn'].forEach(k => { if (so[k]) so[k].err = ''; });
    } catch (e) { const so = SPx.sources(); ['wwff', 'dx', 'progs', 'rbn'].forEach(k => { if (so[k]) so[k].err = String(e.message || e); }); SPx.draw(); }
    finally { holeBusy = false; }
  }
  SPx.source({ id: 'wwff', label: 'WWFF', every: 180, poll: async () => { await hole(); return []; } });
  SPx.source({ id: 'dx', label: 'DX cluster', every: 180, poll: async () => { await hole(); return []; } });
  SPx.source({ id: 'progs', label: 'Other programs', every: 180, poll: async () => { await hole(); return []; } });
  if (!SPx.S.rbnSeen) { SPx.S.rbnSeen = 1; if (!SPx.S.off.includes('rbn')) SPx.S.off.push('rbn'); SPx.save(); }   /* starts OFF */
  SPx.source({ id: 'rbn', label: 'RBN skimmers', every: 180, poll: async () => { await hole(); return []; } });
})(window);
