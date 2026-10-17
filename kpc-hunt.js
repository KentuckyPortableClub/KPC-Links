/* KPC Hunters Lounge (kpc-hunt.html) — Brandon Oct 16 2026: a dressed-up live spotting page for hunters.
   - Live spots: POTA (api.pota.app/spot/activator), SOTA (api2.sota.org.uk) and WWFF (Spothole), checked every minute.
   - Your log: upload any CSV / ADIF (POTA hunted parks export, WWFF Logsearch, SOTA chaser log, a logger's ADIF); the page
     pulls out every POTA / WWFF / SOTA number in it. Saved ONLY in this browser (localStorage kpcHuntLog), never sent anywhere.
     Old POTA numbers K-1234 count as US-1234 (and VE- as CA-). ✓ WORKED on a spot adds it by hand.
   - New-to-you parks roll across the big ticker (sticky) with an optional alert (chime, vibrate, notice). With "far-away
     mode" on, new parks outside your normal range only roll across the small ticker at the very top, with no alert.
   - Parks I still need (by state, POTA's live park list), Top 20 activators by state (data/leaders/US-XX.json, built weekly
     by kpc-state-leaders.yml), My numbers (api.pota.app/stats/user/<call>).
   Settings: kpcHuntF (filters), kpcHuntHome, kpcHuntRange, kpcHuntFar, kpcHuntBell, kpcHuntNote; call = kpcMyCall (shared). */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const PUB = !!(document.getElementById('hl') && document.getElementById('hl').dataset.public === '1');
  const PAGE = (document.getElementById('hl') && document.getElementById('hl').dataset.page) || 'lounge';   /* 'need' = kpc-hunt-need.html */
  /* pop-up boxes (log files, get my parks): any link to #lgModal / #suModal, or to something inside them, opens the box (Brandon Oct 17) */
  function openModal(id, inner) { const m = document.getElementById(id); if (!m) return; m.hidden = false; document.documentElement.classList.add('hl-noscroll');
    const t = inner && document.getElementById(inner); setTimeout(() => { if (t && t !== m) t.scrollIntoView({ block: 'start', behavior: 'smooth' }); else m.querySelector('.hl-mbox').scrollTop = 0; }, 30); }
  function closeModals() { document.querySelectorAll('.hl-modal').forEach(m => { m.hidden = true; }); document.documentElement.classList.remove('hl-noscroll'); }
  document.addEventListener('click', e => {
    if (e.target.closest('[data-mclose]') || e.target.classList.contains('hl-modal')) { closeModals(); return; }
    const a = e.target.closest('a[href^="#"]'); if (!a) return; const id = a.getAttribute('href').slice(1); const el = id && document.getElementById(id); if (!el) return;
    const m = el.classList.contains('hl-modal') ? el : el.closest('.hl-modal'); if (!m) return; e.preventDefault(); closeModals(); openModal(m.id, el === m ? null : id);
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModals(); });
  const DOCKON = () => !PUB && !!document.getElementById('hlDk');
  const DESKON = () => !PUB && !!document.getElementById('hlDk') && matchMedia('(min-width:1100px)').matches;   /* kpc-hunters.html = the public copy */
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const base = c => String(c || '').toUpperCase().trim().split('/').reduce((a, b) => b.length > a.length ? b : a, '');
  const ST = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };
  const BANDS = [['160m', 1800, 2000], ['80m', 3500, 4000], ['60m', 5330, 5410], ['40m', 7000, 7300], ['30m', 10100, 10150], ['20m', 14000, 14350], ['17m', 18068, 18168], ['15m', 21000, 21450], ['12m', 24890, 24990], ['10m', 28000, 29700], ['6m', 50000, 54000], ['2m', 144000, 148000], ['70cm', 420000, 450000]];
  const bandOf = k => (BANDS.find(b => k >= b[1] && k <= b[2]) || ['OTHER'])[0];
  const modeOf = m => { m = String(m || '').toUpperCase(); if (/SSB|LSB|USB|PHONE|^AM$|^FM$/.test(m)) return 'PHONE'; if (/^CW/.test(m)) return 'CW'; if (/FT8|FT4|RTTY|PSK|JS8|DATA|DIGI|OLIVIA|MFSK|JT|SSTV|VARA|Q65/.test(m)) return 'DIGITAL'; return 'OTHER'; };
  const WHERE = [['all', 'EVERYWHERE'], ['us', 'USA'], ['usca', 'USA + CANADA']];

  /* ---------------- references ---------------- */
  const nref = r => {
    r = String(r || '').toUpperCase().trim();
    let m = r.match(/^K-(\d{4,5})$/); if (m) return 'US-' + m[1];
    m = r.match(/^VE-(\d{4,5})$/); if (m) return 'CA-' + m[1];
    return r;
  };
  const progOf = r => /\//.test(r) ? 'SOTA' : /FF-\d{4}$/.test(r) ? 'WWFF' : 'POTA';
  function scan(text) {
    const out = new Set(), T = String(text || '').toUpperCase();
    (T.match(/\b[A-Z0-9]{1,4}\/[A-Z]{2}-\d{3}\b/g) || []).forEach(x => out.add(x));
    (T.match(/\b(?=[A-Z0-9]*[A-Z])[A-Z0-9]{1,4}-\d{4,5}\b/g) || []).forEach(x => { const r = nref(x); if (/FF-\d{4}$/.test(r) || /^[A-Z0-9]{1,3}-\d{4,5}$/.test(r)) out.add(r); });
    return out;
  }

  /* ---------------- saved state ---------------- */
  let LOG = get('kpcHuntLog', null); if (!LOG || !Array.isArray(LOG.r)) LOG = { t: 0, file: '', r: [], m: [] };
  let WK = new Set(LOG.r), MAN = new Set(LOG.m || []);
  const saveLog = () => { LOG.r = [...WK]; LOG.m = [...MAN]; put('kpcHuntLog', LOG); };
  const hasLog = () => WK.size > 0;
  let F = Object.assign({ v: 3, view: 'cards', p: ['POTA'], hide: true, qrt: true, nw: false, rg: false, bands: [], modes: ['PHONE'], where: 'all', st: '', q: '', sort: 'new' }, get('kpcHuntF', {}));
  /* Brandon Oct 16: everyone starts on POTA, phone (SSB), hiding hunted parks and QRT (once, then their own picks stick) */
  if (!F.v || F.v < 3) { Object.assign(F, { p: ['POTA'], hide: true, qrt: true, modes: ['PHONE'], v: 3 }); }
  F.rg = false; if (F.where === 'range') F.where = 'all'; if (F.sort === 'far') F.sort = 'new'; if (!Array.isArray(F.xc)) F.xc = [];
  const saveF = () => put('kpcHuntF', F);
  /* 'normal range' was removed Oct 16 (Brandon): no home, no far-away ticker */
  let HOME = null, RANGE = 1e9, FAR = false, BELL = get('kpcHuntBell', false), NOTE = get('kpcHuntNote', false);
  let CALL = base(get('kpcMyCall', ''));

  /* ---------------- geo ---------------- */
  function grid(g) {
    g = String(g || '').trim(); if (!/^[A-R]{2}\d{2}([A-X]{2})?/i.test(g)) return null;
    g = g.toUpperCase(); let lo = (g.charCodeAt(0) - 65) * 20 - 180 + (+g[2]) * 2, la = (g.charCodeAt(1) - 65) * 10 - 90 + (+g[3]);
    if (g.length >= 6) { lo += (g.charCodeAt(4) - 65) / 12 + 1 / 24; la += (g.charCodeAt(5) - 65) / 24 + 1 / 48; } else { lo += 1; la += .5; }
    return [la, lo];
  }
  const miles = (a, b, c, d) => { const r = Math.PI / 180; return 3958.8 * 2 * Math.asin(Math.sqrt(Math.sin((c - a) * r / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin((d - b) * r / 2) ** 2)); };
  const dist = s => HOME && isFinite(s.la) && isFinite(s.lo) ? miles(HOME.la, HOME.lo, s.la, s.lo) : null;
  const isFar = s => { const d = dist(s); return d != null && d > RANGE; };

  /* park facts: coords + activation counts (US parks from our weekly index; Canada from data/canada.json) */
  const PK = {};
  let pkLoad = null;
  function loadParks() {
    if (pkLoad) return pkLoad;
    pkLoad = Promise.all([
      fetch('data/parkinfo/index.json').then(r => r.ok ? r.json() : null).catch(() => null),
      fetch('kpc-ky-data.json').then(r => r.ok ? r.json() : null).catch(() => null),
      fetch('data/canada.json').then(r => r.ok ? r.json() : null).catch(() => null)
    ]).then(([ix, ky, ca]) => {
      ((ix && ix.rows) || []).forEach(r => { PK[r[0]] = { n: r[1], st: r[2], la: r[3], lo: r[4], a: r[6] }; });
      ((ky && ky.parks) || []).forEach(p => { const c = String(p.c).toUpperCase(); PK[c] = Object.assign(PK[c] || {}, { n: p.n, st: 'KY', la: p.la, lo: p.lo }); });
      ((ca && ca.rows) || []).forEach(r => { if (r[0] === 'POTA') PK[r[1]] = { n: r[2], st: '', la: r[3], lo: r[4] }; });
    });
    return pkLoad;
  }
  const SUM = get('kpcHuntSota', {});   // SOTA summit coords we've looked up
  async function sotaWhere(s) {
    if (SUM[s.ref]) return SUM[s.ref];
    const [a, r] = s.ref.split('/');
    try { const j = await fetch('https://api2.sota.org.uk/api/summits/' + encodeURIComponent(a) + '/' + encodeURIComponent(r)).then(x => x.ok ? x.json() : null); if (j && isFinite(+j.latitude)) { SUM[s.ref] = [+j.latitude, +j.longitude, +j.activationCount || 0]; put('kpcHuntSota', SUM); return SUM[s.ref]; } } catch (e) {}
    return null;
  }

  /* ---------------- spots ---------------- */
  let SP = [], src = '', first = true, SEEN = new Set(), next = 0;
  const toKhz = f => { f = Number(f); if (!isFinite(f) || f <= 0) return null; return f < 1000 ? f * 1000 : f < 1e6 ? f : f / 1000; };
  const toMs = t => { if (t == null) return null; if (typeof t === 'number') return t < 1e12 ? t * 1000 : t; const s = String(t); const d = Date.parse(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + 'Z'); return isFinite(d) ? d : null; };
  async function jget(u, ms) { const c = new AbortController(), tm = setTimeout(() => c.abort(), ms || 15000); try { const r = await fetch(u, { cache: 'no-store', signal: c.signal }); if (!r.ok) throw new Error(r.status); return await r.json(); } finally { clearTimeout(tm); } }
  function fromPota(x) {
    const khz = toKhz(x.frequency); if (!khz || !x.reference) return null;
    const loc = String(x.locationDesc || ''), g = grid(x.grid6 || x.grid4), ref = nref(x.reference);
    return { p: 'POTA', call: String(x.activator || '').toUpperCase(), khz, mode: String(x.mode || '').toUpperCase(), ref, name: x.name || '', loc, st: (loc.match(/US-([A-Z]{2})/) || [])[1] || '',
      la: g ? g[0] : +x.latitude, lo: g ? g[1] : +x.longitude, t: toMs(x.spotTime), by: x.spotter || '', com: x.comments || '', us: /^US-/.test(loc) || /^US-/.test(ref), ca: /^CA-/.test(ref) };
  }
  function fromSota(x) {
    const khz = toKhz(x.frequency); if (!khz) return null; const a = String(x.associationCode || ''), ref = (a + '/' + (x.summitCode || '')).toUpperCase();
    return { p: 'SOTA', call: String(x.activatorCallsign || '').toUpperCase(), khz, mode: String(x.mode || '').toUpperCase(), ref, name: x.summitDetails || '', loc: a, st: '', la: NaN, lo: NaN,
      t: toMs(x.timeStamp), by: x.callsign || '', com: x.comments || '', us: /^(W\d|K[HL]\d|W[0-9]?[A-Z])/.test(a), ca: /^(VE|VA|VY|VO)/.test(a) };
  }
  /* special event stations: calls on today's ARRL list (kpc-special-events.json), US 1x1 calls, W1AW/n, or the comment says so */
  let SES = new Set();
  fetch('kpc-special-events.json').then(r => r.ok ? r.json() : null).then(j => { ((j && j.stations) || []).forEach(x => [x.call].concat(x.calls || []).forEach(c => c && SES.add(base(c)))); }).catch(() => {});
  const isEvent = (call, com) => SES.has(base(call)) || /^[KNW]\d[A-Z]$/.test(base(call)) || /^W1AW\/\d$/.test(call) || /SPECIAL EVENT|\bSES\b/i.test(com || '');
  const DXPRE = /DXPEDITION|DX-?PED/i;
  /* Spothole: WWFF, other programs and the DX cluster (POTA and SOTA come straight from their own sites; skimmers left out) */
  function fromHole(x) {
    const sig = String(x.sig || ''), src0 = String(x.source || '');
    if (/^(POTA|SOTA)$/i.test(sig) || /RBN|SKIM/i.test(src0)) return null;
    const khz = toKhz(x.freq != null ? x.freq : x.frequency); if (!khz) return null;
    const call = String(x.dx_call || x.activator || '').toUpperCase(), com = x.comment || '';
    const country = x.dx_country || '', usa = /united states/i.test(country), can = /canada/i.test(country);
    const g = { qrt: !!x.qrt, call, khz, mode: String(x.mode || '').toUpperCase(), loc: country, st: usa ? String(x.dx_state || '').toUpperCase() : '', la: +(x.dx_latitude ?? NaN), lo: +(x.dx_longitude ?? NaN),
      t: toMs(x.time), by: x.de_call || '', com, us: usa, ca: can };
    if (/WWFF/i.test(sig)) {
      const rr = x.sig_refs || []; const refs = (Array.isArray(rr) ? rr : [rr]).map(v => typeof v === 'string' ? { id: v } : { id: v.id || v.ref || '', name: v.name || '' }).filter(v => v.id);
      if (!refs.length) return null; const ref = refs[0].id.toUpperCase();
      return Object.assign(g, { p: 'WWFF', ref, name: refs[0].name || '', us: /^KFF-/.test(ref), ca: /^VEFF-/.test(ref) });
    }
    const p = DXPRE.test(sig + ' ' + com) ? 'DXPED' : isEvent(call, com) ? 'EVENT' : 'DX';
    return Object.assign(g, { p, ref: '', label: sig && !/^dxpedition$/i.test(sig) ? sig : '', name: (x.dx_name ? x.dx_name + ' · ' : '') + country });
  }
  /* POTA + SOTA come first; Spothole (about 1 MB: WWFF, DX cluster, DXpeditions, special events) arrives on its own and
     is merged in when it lands, so a slow phone still sees POTA right away. The last Spothole list is reused meanwhile. */
  let LP = [], LS = [], LH = [], GOT = {}, holeBusy = false;
  async function load() {
    const a = jget('https://api.pota.app/spot/activator', 25000).then(x => { LP = (x || []).map(fromPota).filter(Boolean); GOT.POTA = 1; }).catch(() => { GOT.POTA = 0; });
    const b = jget('https://api2.sota.org.uk/api/spots/50/all', 25000).then(x => { LS = (x || []).map(fromSota).filter(Boolean); GOT.SOTA = 1; }).catch(() => { GOT.SOTA = 0; });
    if (!holeBusy) {
      holeBusy = true;
      jget('https://spothole.app/api/v1/spots?max_age=2700', 60000).then(j => { const L = Array.isArray(j) ? j : (j && j.spots) || []; LH = L.map(fromHole).filter(Boolean); GOT.HOLE = 1; })
        .catch(() => { GOT.HOLE = 0; }).finally(() => { holeBusy = false; build(!first); });
    }
    await Promise.all([a, b]);
    await build(!first); first = false;
    next = Date.now() + 60e3;
  }
  async function build(alert) {
    const now = Date.now(), seen = new Map();
    LP.concat(LS, LH).filter(s => s.call && (!s.t || now - s.t < 75 * 60e3)).sort((a, b) => (b.t || 0) - (a.t || 0)).forEach(s => { const k = keyOf(s); if (!seen.has(k)) seen.set(k, s); });
    SP = [...seen.values()]; SP.forEach(cty);
    await loadParks();
    SP.forEach(s => {
      const k = PK[s.ref];
      if (k) { if (!isFinite(s.la) && isFinite(k.la)) { s.la = k.la; s.lo = k.lo; } if (!s.st && k.st) s.st = k.st; if (k.a != null) s.acts = k.a; if (!s.name) s.name = k.n; }
      if (s.p === 'SOTA' && SUM[s.ref]) { s.la = SUM[s.ref][0]; s.lo = SUM[s.ref][1]; s.acts = SUM[s.ref][2]; }
    });
    const got = [GOT.POTA && 'POTA', GOT.SOTA && 'SOTA', GOT.HOLE && 'WWFF, DX cluster, DXpeditions and special events (Spothole)'].filter(Boolean);
    src = (got.length ? 'Spots from ' + got.join(', ') + '. Checked every minute while this page is open.' : 'The spot sites are not answering right now. Trying again in a minute.')
      + (GOT.HOLE === undefined ? ' Still loading the DX cluster, DXpedition, special event and WWFF spots…' : GOT.HOLE === 0 ? ' The DX cluster feed (Spothole) did not answer this time; trying again next minute.' : '');
    const need = SP.filter(s => s.p === 'SOTA' && !isFinite(s.la) && isNew(s)).slice(0, 12);
    if (need.length) Promise.all(need.map(async s => { const w = await sotaWhere(s); if (w) { s.la = w[0]; s.lo = w[1]; s.acts = w[2]; } })).then(() => { ticker(false); draw(); });
    ticker(alert); chips(); draw(); needDraw();
  }
  const isNew = s => !!s.ref && hasLog() && !WK.has(s.ref);
  const keyOf = s => s.p + '|' + s.call + '|' + (s.ref || Math.round(s.khz));
  /* country of each spot: POTA ref prefix → POTA's program list, SOTA association → SOTA's list, others from Spothole */
  const PROG = {}, ASSOC = {};
  fetch('https://api.pota.app/programs').then(r => r.ok ? r.json() : []).then(L => { (L || []).forEach(x => { if (x.programPrefix) PROG[x.programPrefix] = x.programName; }); SP.forEach(cty); chips(); draw(); }).catch(() => {});
  fetch('https://api2.sota.org.uk/api/associations').then(r => r.ok ? r.json() : []).then(L => { (L || []).forEach(x => { if (x.associationCode) ASSOC[x.associationCode] = String(x.associationName || ''); }); SP.forEach(cty); chips(); draw(); }).catch(() => {});
  const ctyName = n => { n = String(n || '').trim(); if (/^(USA|United States)/i.test(n)) return 'United States'; return n.split(/ - | \(|, /)[0].trim(); };
  function cty(s) {
    if (s.p === 'POTA') { const pre = String(s.ref).split('-')[0]; s.cty = PROG[pre] ? ctyName(PROG[pre]) : (pre === 'US' ? 'United States' : pre === 'CA' ? 'Canada' : pre); }
    else if (s.p === 'SOTA') { const a = String(s.ref).split('/')[0]; s.cty = ASSOC[a] ? ctyName(ASSOC[a]) : /^(W|K|N|A)\d|^K[HL]/.test(a) ? 'United States' : /^(VE|VA|VY|VO)/.test(a) ? 'Canada' : a; }
    else s.cty = ctyName(s.loc) || (s.us ? 'United States' : s.ca ? 'Canada' : 'Unknown');
    return s;
  }
  const isQrt = s => s.qrt || /QRT|\bhunting\b/i.test(s.com || '');
  const passPBM = s => F.p.includes(s.p) && !F.xc.includes(s.cty) && (!F.qrt || !isQrt(s)) && (!F.bands.length || F.bands.includes(bandOf(s.khz))) && (!F.modes.length || F.modes.includes(modeOf(s.mode)));

  /* ---------------- ticker + alerts ---------------- */
  let AC = null;
  function chime() {
    try {
      AC = AC || new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === 'suspended') AC.resume();
      [[880, 0], [1320, .16], [1760, .32]].forEach(([f, d]) => { const o = AC.createOscillator(), g = AC.createGain(); o.frequency.value = f; o.type = 'sine'; o.connect(g); g.connect(AC.destination); const t = AC.currentTime + d; g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(.25, t + .02); g.gain.exponentialRampToValueAtTime(.0001, t + .28); o.start(t); o.stop(t + .3); });
    } catch (e) {}
    try { navigator.vibrate && navigator.vibrate([180, 90, 180]); } catch (e) {}
  }
  const tItem = s => `<span class="it" data-k="${esc(keyOf(s))}">✨ <b>${esc(s.ref)}</b> ${esc(s.name || '')} <small>${esc(s.st || s.loc || '')}</small> · ${esc(s.call)} <i>${(s.khz / 1000).toFixed(3)}</i> <small>${esc(s.mode || '')}</small></span>`;
  function ticker(alert) {
    const T = $('hlTickT'), FT = $('hlFarT');
    if (!hasLog()) { T.innerHTML = PUB ? '<span class="hl-wait">Tap 📄 LOAD MY WORKED PARKS (top of the page) and new-to-you parks will roll across here.</span>' : '<span class="hl-wait">Tap ⭐ GET MY PARKS FROM POTA (top of the page) and new-to-you parks will roll across here.</span>'; T.style.setProperty('--dur', '22s'); $('hlFar').hidden = true; naDraw(); return; }
    const L = SP.filter(s => isNew(s) && passPBM(s));
    const far = FAR && HOME ? L.filter(isFar) : [], near = L.filter(s => !far.includes(s));
    const fresh = near.filter(s => !SEEN.has(keyOf(s)));
    L.forEach(s => SEEN.add(keyOf(s)));
    if (near.length) { const h = near.map(tItem).join(''); if (T.dataset.h !== h) { T.innerHTML = h; T.dataset.h = h; T.style.setProperty('--dur', Math.max(20, T.textContent.length * .2) + 's'); } }
    else { T.dataset.h = ''; T.innerHTML = `<span class="hl-wait">Nothing new to you on the air right now${far.length ? ` (${far.length} far away up top)` : ''}. Checking every minute…</span>`; T.style.setProperty('--dur', '24s'); }
    $('hlFar').hidden = !far.length;
    if (far.length) { FT.innerHTML = far.map(s => `<span>✨ <b>${esc(s.ref)}</b> ${esc(s.name)} ${esc(s.st || '')} · ${esc(s.call)} ${(s.khz / 1000).toFixed(3)} ${esc(s.mode)} · ${Math.round(dist(s))} mi</span>`).join(''); FT.style.setProperty('--dur', Math.max(25, FT.textContent.length * .16) + 's'); }
    if (alert && fresh.length) {
      const t = $('hlTick'); t.classList.remove('flash'); void t.offsetWidth; t.classList.add('flash');
      fire(`🔥 NEW PARK: ${fresh[0].ref} ${fresh[0].name || ''} · ${fresh[0].call} ${(fresh[0].khz / 1000).toFixed(3)}${fresh.length > 1 ? ` (+${fresh.length - 1} more)` : ''}`);
      if (BELL) chime();
      if (NOTE && 'Notification' in window && Notification.permission === 'granted') {
        try { const s = fresh[0]; new Notification('New park for you: ' + s.ref, { body: `${s.name || ''} ${s.st || ''}\n${s.call} on ${(s.khz / 1000).toFixed(3)} ${s.mode}${fresh.length > 1 ? `\n+${fresh.length - 1} more` : ''}`, icon: 'kpc-icon-180.png', tag: 'kpc-hunt' }); } catch (e) {}
      }
    }
    $('hsNew').textContent = hasLog() ? SP.filter(isNew).length : '–';
    naDraw(); try { lmDraw(); } catch (e) { console.error('map', e); }
    try { favAlert(); } catch (e) {}
  }
  function bell() { const b = $('hlBell'); b.setAttribute('aria-pressed', BELL); b.innerHTML = (BELL ? '🔔' : '🔕') + '<span class="t"> ALERT ' + (BELL ? 'ON' : 'OFF') + '</span>'; }
  $('hlBell').onclick = () => { BELL = !BELL; put('kpcHuntBell', BELL); bell(); if (BELL) chime(); };
  /* scrolling bars on/off, each on its own (Brandon Oct 17): the new-parks ticker and the conditions bar; the buttons stay */
  let BAN = get('kpcHuntBanner', true), CXB = get('kpcHuntCxBar', true);
  function ban() {
    const b = $('hlBan'), c = $('hlCxBan');
    $('hl').dataset.noban = BAN ? '' : '1'; $('hl').dataset.nocx = CXB ? '' : '1';
    if (b) { b.setAttribute('aria-pressed', BAN); b.innerHTML = '🎞<span class="t"> PARKS BAR ' + (BAN ? 'ON' : 'OFF') + '</span>'; }
    if (c) { c.setAttribute('aria-pressed', CXB); c.innerHTML = '📡<span class="t"> CONDITIONS ' + (CXB ? 'ON' : 'OFF') + '</span>'; }
  }
  if ($('hlBan')) $('hlBan').onclick = () => { BAN = !BAN; put('kpcHuntBanner', BAN); ban(); toast(BAN ? 'New-parks bar on.' : 'New-parks bar off. Tap 🎞 to bring it back.'); };
  if ($('hlCxBan')) $('hlCxBan').onclick = () => { CXB = !CXB; put('kpcHuntCxBar', CXB); ban(); toast(CXB ? 'Conditions bar on.' : 'Conditions bar off. Tap 📡 to bring it back.'); };
  ban();
  /* tap any award badge = the badge legend (Brandon Oct 17) */
  document.addEventListener('click', e => { const a = e.target.closest('.ac'); if (!a || a.closest('#awModal')) return; e.preventDefault(); e.stopPropagation(); openModal('awModal'); }, true);
  document.addEventListener('click', e => {
    const it = e.target.closest('.hl-tick-track .it'); if (!it) return;
    const c = document.querySelector(`.hs[data-k="${CSS.escape(it.dataset.k)}"]`);
    if (c) { c.scrollIntoView({ behavior: 'smooth', block: 'center' }); c.classList.remove('fresh'); void c.offsetWidth; c.classList.add('fresh'); }
  });

  /* ---------------- spot cards ---------------- */
  const ago = t => { if (!t) return ''; const m = Math.max(0, Math.round((Date.now() - t) / 60e3)); return m < 1 ? 'just now' : m + ' min ago'; };
  const PL = { POTA: 'POTA', WWFF: 'WWFF', SOTA: 'SOTA', DXPED: 'DXPEDITION', EVENT: 'SPECIAL EVENT', DX: 'DX CLUSTER' };
  const pageOf = s => s.p === 'SOTA' ? 'https://sotl.as/summits/' + s.ref : s.p === 'WWFF' ? 'https://wwff.co/directory/?showRef=' + s.ref : 'https://pota.app/#/park/' + s.ref;
  /* award progress right on the spot (Brandon Oct 16): times you've worked this park / this activator, N1CC new band */
  let CNT = get('kpcHuntCounts', null);
  function awardChips(s, short) {
    if (PUB) return '';
    if (!CNT || s.p !== 'POTA') return '';
    const out = [], pc = (CNT.pc || {})[s.ref] || 0, ac = (CNT.ac || {})[base(s.call)] || (CNT.ac || {})[s.call] || 0, n1 = (CNT.n1 || {})[s.ref];
    const lvl = (v, step) => (Math.floor(v / step) + 1) * step;
    if (pc) { const n = lvl(pc, 20), near = n - pc <= 5; out.push(`<span class="ac${near ? ' near' : ''}" title="Repeat Offender: every 20 QSOs with a park (tap for what the badges mean)">🔁 ${short ? '' : 'Park '}${pc}/${n}${near ? ' · ALMOST' : ''}</span>`); }
    if (ac) { const n = lvl(ac, 50), near = n - ac <= 10; out.push(`<span class="ac${near ? ' near' : ''}" title="Operator to Operator: every 50 QSOs with the same activator">🤝 ${short ? '' : base(s.call) + ' '}${ac}/${n}${near ? ' · ALMOST' : ''}</span>`); }
    if (n1 != null) { const L = n1.toUpperCase().split(',').filter(Boolean), b = bandOf(s.khz).toUpperCase(); if (L.length < 10 && !L.includes(b)) out.push(`<span class="ac near" title="N1CC: this park on 10 different bands">📶 NEW BAND ${L.length}/10</span>`); }
    return out.join('');
  }
  /* ⭐ favorite activators (Brandon Oct 16): pinned to the top while on the air, until you've worked them today */
  let FAV = new Set(get('kpcHuntFav', [])), FDONE = new Set(get('kpcHuntFavDone', [])), SEENFAV = new Set(), favFirst = true;
  const today = () => new Date().toISOString().slice(0, 10).replace(/-/g, '');
  /* calls hunted today (Brandon Oct 16: 'hide someone you've done hunted'): hidden by hand (🙈 on a card, or ✓ I WORKED IT)
     plus, on the members page, every call in today's hunting log. Starts fresh at 0000 UTC. */
  let HC = get('kpcHuntCallsDay', null);
  const hcFix = () => { if (!HC || HC.d !== today()) HC = { d: today(), c: [] }; };
  function callsToday() { hcFix(); const S = new Set(HC.c); try { if (!PUB && typeof Q !== 'undefined') Q.q.forEach(q => { if (q.d === today()) S.add(base(q.call)); }); } catch (e) {} return S; }
  function hideCall(c) { hcFix(); c = base(c); if (!HC.c.includes(c)) HC.c.push(c); put('kpcHuntCallsDay', HC); }
  const isFav = s => FAV.has(base(s.call));
  const favHunted = s => { const c = base(s.call), d = today(); return FDONE.has(c + '|' + d) || Q.q.some(q => base(q.call) === c && q.d === d); };
  const favPinned = s => isFav(s) && !favHunted(s);
  const saveFav = () => { put('kpcHuntFav', [...FAV]); const d = today(); FDONE = new Set([...FDONE].filter(x => x.endsWith('|' + d))); put('kpcHuntFavDone', [...FDONE]); };
  function favDraw() {
    const on = new Set(SP.map(s => base(s.call)));
    $('favN').textContent = FAV.size ? `(${FAV.size}${[...FAV].some(c => on.has(c)) ? ' · ' + [...FAV].filter(c => on.has(c)).length + ' ON THE AIR' : ''})` : '';
    $('favList').innerHTML = FAV.size ? [...FAV].sort().map(c => `<span class="hl-fav${on.has(c) ? ' on' : ''}"><a href="https://www.qrz.com/db/${encodeURIComponent(c)}" target="_blank" rel="noopener">${esc(c)}</a>${on.has(c) ? ' 📡' : ''}<button type="button" data-favx="${esc(c)}" title="Remove">✕</button></span>`).join('') : '<span class="hl-src">No favorites yet.</span>';
  }
  document.addEventListener('click', e => {
    const f = e.target.closest('[data-fav]'); if (f) { e.stopPropagation(); const c = f.dataset.fav; if (FAV.has(c)) FAV.delete(c); else { FAV.add(c); toast(`⭐ ${c} is a favorite: pinned to the top whenever they're on the air.`); } saveFav(); favDraw(); draw(); return; }
    const x = e.target.closest('[data-favx]'); if (x) { FAV.delete(x.dataset.favx); saveFav(); favDraw(); draw(); return; }
    const d = e.target.closest('[data-fdone]'); if (d) { FDONE.add(d.dataset.fdone + '|' + today()); saveFav(); draw(); toast('✓ Got them. Unpinned for today.'); }
  }, true);
  $('favForm').addEventListener('submit', e => { e.preventDefault(); const c = base($('favIn').value); if (!/^[A-Z0-9]{3,10}$/.test(c)) { toast('That doesn’t look like a call sign.'); return; } FAV.add(c); $('favIn').value = ''; saveFav(); favDraw(); draw(); });
  function favAlert() {
    const L = SP.filter(s => isFav(s) && !favHunted(s)), fresh = L.filter(s => !SEENFAV.has(base(s.call)));
    L.forEach(s => SEENFAV.add(base(s.call)));
    if (!favFirst && fresh.length) { const s = fresh[0]; fire(`⭐ FAVORITE ON THE AIR: ${s.call}${s.ref ? ' · ' + s.ref : ''} · ${(s.khz / 1000).toFixed(3)} ${s.mode}`); if (BELL) chime(); }
    favFirst = false;
  }
  function card(s) {
    const n = isNew(s), w = !!s.ref && hasLog() && WK.has(s.ref), d = dist(s), k = keyOf(s);
    const b = [`<span class="hb prog">${PL[s.p] || s.p}${s.label ? ' · ' + esc(s.label) : ''}</span>`];
    if (n) b.push('<span class="hb new">✨ NEW TO YOU</span>'); else if (w) b.push('<span class="hb wk">✓ WORKED</span>');
    if (s.acts === 0) b.push('<span class="hb atno">FIRST EVER ACTIVATION</span>'); else if (s.acts != null && s.acts <= 5) b.push(`<span class="hb rare">RARE · ${s.acts}</span>`);
    if (d != null && d > RANGE) b.push(`<span class="hb far">FAR · ${Math.round(d)} MI</span>`);
    if (isQrt(s)) b.push('<span class="hb qrt">QRT</span>');
    b.push(`<span class="hb">${bandOf(s.khz)}</span>`, `<span class="hb">${esc(s.mode || '?')}</span>`);
    return `<article class="hs p-${s.p}${n ? ' new' : ''}${w ? ' worked' : ''}${isQrt(s) ? ' qrt' : ''}" data-k="${esc(k)}">
 <div class="hs-top"><div class="hs-call"><button type="button" class="fv${isFav(s) ? ' on' : ''}" data-fav="${esc(base(s.call))}" title="${isFav(s) ? 'Remove from favorites' : 'Add to favorite activators'}">${isFav(s) ? '★' : '☆'}</button><a href="https://www.qrz.com/db/${encodeURIComponent(base(s.call))}" target="_blank" rel="noopener">${esc(s.call)}</a></div><div class="hs-f"><b>${(s.khz / 1000).toFixed(3)}</b><span>MHz · ${esc(s.mode || '')}</span></div></div>
 <div class="hs-park">${s.ref ? `<a href="${pageOf(s)}" target="_blank" rel="noopener">${esc(s.ref)}</a>` : ''}${esc(s.name || '')}</div>
 <div class="hs-meta">${esc(s.st ? (ST[s.st] || s.st) : s.loc)}${d != null ? ' · ' + Math.round(d) + ' mi' : ''} · ${ago(s.t)}${s.by ? ' · spotted by ' + esc(s.by) : ''}</div>
 ${s.com ? `<div class="hs-com">“${esc(String(s.com).slice(0, 140))}”</div>` : ''}
 ${awardChips(s) ? `<div class="hs-aw">${awardChips(s)}</div>` : ''}
 <div class="hs-b">${b.join('')}</div>
 <div class="hs-a"><button type="button" class="lg" data-log="1">📝 LOG IT</button><button type="button" class="hc" data-hc="${esc(s.call)}" title="Hide this call until 0000 UTC">🙈 HIDE ${esc(base(s.call))} TODAY</button>${s.ref ? `<button type="button" class="wk${w ? ' on' : ''}" data-wk="${esc(s.ref)}" data-wc="${esc(s.call)}">${w ? '✓ WORKED' : '＋ I WORKED IT'}</button><a href="${pageOf(s)}" target="_blank" rel="noopener">${s.p === 'SOTA' ? 'SOTLAS' : s.p} PAGE ↗</a>${s.p === 'POTA' && s.us ? `<a href="kpc-planner-us.html?q=${encodeURIComponent(s.ref)}">ON THE MAP</a>` : ''}<a href="kpc-park-info.html?ref=${encodeURIComponent(s.ref)}">PARK INFO</a>` : `<a href="https://www.qrz.com/db/${encodeURIComponent(base(s.call))}" target="_blank" rel="noopener">QRZ ↗</a><a href="https://www.dxsummit.fi/#/?dx_calls=${encodeURIComponent(base(s.call))}" target="_blank" rel="noopener">DX SUMMIT ↗</a>`}</div>
</article>`;
  }
  function row(s) {
    const n = isNew(s), w = !!s.ref && hasLog() && WK.has(s.ref), d = dist(s);
    const tag = n ? '<span class="hb new">NEW</span>' : w ? '<span class="hb wk">✓</span>' : '';
    const rare = s.acts === 0 ? '<span class="hb atno">1ST</span>' : s.acts != null && s.acts <= 5 ? `<span class="hb rare">RARE ${s.acts}</span>` : '';
    return `<tr class="hr${n ? ' new' : ''}${w ? ' worked' : ''}" data-k="${esc(keyOf(s))}"><td class="t hide-s">${esc(ago(s.t).replace(' min ago', 'm').replace('just now', 'now'))}</td><td class="c"><button type="button" class="fv${isFav(s) ? ' on' : ''}" data-fav="${esc(base(s.call))}">${isFav(s) ? '★' : '☆'}</button>${esc(s.call)}</td><td class="f">${(s.khz / 1000).toFixed(3)}<small>${esc(s.mode || '')}</small></td><td class="hide-s">${esc(s.mode || '')}</td>
<td><span class="pg">${PL[s.p] || s.p}</span> ${s.ref ? `<a href="${pageOf(s)}" target="_blank" rel="noopener" class="r">${esc(s.ref)}</a> ` : ''}${esc(s.name || '')} ${tag}${rare} ${awardChips(s, true)}</td><td class="hide-s">${esc(s.st || '')}</td><td class="hide-s">${d != null ? Math.round(d) : ''}</td>
<td class="a"><button type="button" class="lg" data-log="1" title="Log it">📝</button><button type="button" class="hc" data-hc="${esc(s.call)}" title="Hide this call today">🙈</button>${s.ref ? `<button type="button" class="wk${w ? ' on' : ''}" data-wk="${esc(s.ref)}" title="Mark worked">✓</button>` : ''}</td></tr>`;
  }
  function draw() {
    const q = F.q.trim().toUpperCase();
    const CT = F.hc ? callsToday() : null;
    let L = SP.filter(s => passPBM(s) && (!CT || !CT.has(base(s.call))) && (!F.hide || !WK.has(s.ref)) && (!F.nw || isNew(s)) && (!F.rg || !isFar(s))
      && (F.where === 'all' || (F.where === 'us' && s.us) || (F.where === 'usca' && (s.us || s.ca)) || (F.where === 'range' && dist(s) != null && !isFar(s)))
      && (!F.st || s.st === F.st)
      && (!q || [s.call, s.ref, s.name, s.st, ST[s.st] || '', s.loc, s.com].join(' ').toUpperCase().includes(q)));
    const srt = { new: (a, b) => (b.t || 0) - (a.t || 0), freq: (a, b) => a.khz - b.khz, mine: (a, b) => (isNew(b) - isNew(a)) || (b.t || 0) - (a.t || 0), far: (a, b) => (dist(a) ?? 1e9) - (dist(b) ?? 1e9) }[F.sort] || null;
    if (srt) L.sort(srt);
    const PIN = L.filter(favPinned); L = L.filter(s => !favPinned(s));
    $('hlFavs').innerHTML = PIN.length ? `<div class="hl-pinbar">⭐ FAVORITES ON THE AIR <small>pinned until you work them today</small></div><div class="hl-grid hl-pinned">${PIN.map(s => card(s).replace('<div class="hs-a">', `<div class="hs-a"><button type="button" class="got" data-fdone="${esc(base(s.call))}">✓ GOT THEM</button>`)).join('')}</div>` : '';
    favDraw();
    const old = new Set([...document.querySelectorAll('#hlSpots .hs')].map(x => x.dataset.k));
    $('hlSpots').className = F.view === 'table' ? 'hl-tablewrap' : 'hl-grid';
    $('hlSpots').innerHTML = !L.length ? `<div class="hl-empty">${SP.length ? 'No spots match your filters right now.' : 'No spots yet.'}</div>`
      : F.view === 'table' ? `<table class="hl-st"><thead><tr><th class="hide-s">WHEN</th><th>CALL</th><th>MHz</th><th class="hide-s">MODE</th><th>PARK / WHERE</th><th class="hide-s">STATE</th><th class="hide-s">MI</th><th></th></tr></thead><tbody>${L.slice(0, 400).map(row).join('')}</tbody></table>`
      : L.slice(0, 240).map(card).join('');
    if (old.size) document.querySelectorAll('#hlSpots .hs.new, #hlSpots tr.hr.new').forEach(x => { if (!old.has(x.dataset.k)) x.classList.add('fresh'); });
    const hid = SP.length - L.length;
    if ($('rtN')) $('rtN').textContent = L.length;
    $('hlCount').textContent = `${L.length} spot${L.length === 1 ? '' : 's'} shown${hid ? ` · ${hid} hidden by your filters` : ''}${hasLog() ? '' : ' · load your log to see which are new to you'}`;
    $('hsLive').textContent = SP.length; $('hlSrc').textContent = src; $('hlNoLog').hidden = hasLog(); if ($('hlNoLogP')) $('hlNoLogP').hidden = hasLog();
  }
  document.addEventListener('click', e => {
    const h = e.target.closest('[data-hc]'); if (!h) return;
    const c = base(h.dataset.hc); hideCall(c); const was = F.hc; F.hc = true; saveF(); chips(); draw();
    toast(`🙈 ${c} is hidden until 0000 UTC (HIDE CALLS I'VE WORKED TODAY is on).`, () => { HC.c = HC.c.filter(x => x !== c); put('kpcHuntCallsDay', HC); F.hc = was; saveF(); chips(); draw(); });
  });
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-wk]'); if (!b) return;
    const r = b.dataset.wk;
    if (WK.has(r) && MAN.has(r)) { WK.delete(r); MAN.delete(r); } else if (!WK.has(r)) { WK.add(r); MAN.add(r); if (!LOG.t) LOG.t = Date.now(); if (b.dataset.wc) hideCall(b.dataset.wc); }
    saveLog(); logInfo(); ticker(false); draw(); needDraw();
  });

  /* ---------------- filters ---------------- */
  function chips() {
    document.querySelectorAll('[data-g=p]').forEach(b => b.setAttribute('aria-pressed', F.p.includes(b.dataset.v)));
    $('fHide').setAttribute('aria-pressed', F.hide); $('fQrt').setAttribute('aria-pressed', !!F.qrt); $('fCalls').setAttribute('aria-pressed', !!F.hc); $('fNew').setAttribute('aria-pressed', F.nw); $('fRange').setAttribute('aria-pressed', F.rg);
    $('fBands').innerHTML = BANDS.map(b => b[0]).concat(['OTHER']).map(b => `<button type="button" class="hl-chip" data-band="${b}" aria-pressed="${F.bands.includes(b)}">${b.toUpperCase()}</button>`).join('');
    $('fModes').innerHTML = ['PHONE', 'CW', 'DIGITAL', 'OTHER'].map(m => `<button type="button" class="hl-chip" data-mode="${m}" aria-pressed="${F.modes.includes(m)}">${m === 'PHONE' ? 'PHONE (SSB/FM)' : m}</button>`).join('');
    $('fWhere').innerHTML = WHERE.map(w => `<button type="button" class="hl-chip" data-where="${w[0]}" aria-pressed="${F.where === w[0]}">${w[1]}</button>`).join('');
    $('sBand').textContent = F.bands.length ? F.bands.join(' ').toUpperCase() : 'ALL';
    $('sMode').textContent = F.modes.length ? F.modes.join(' ') : 'ALL';
    $('sWhere').textContent = (WHERE.find(w => w[0] === F.where) || WHERE[0])[1] + (F.st ? ' · ' + F.st : '');
    $('fSt').value = F.st; $('fSort').value = F.sort; $('fQ').value = F.q;
    const cc = {}; SP.forEach(x => { if (x.cty) cc[x.cty] = (cc[x.cty] || 0) + 1; }); F.xc.forEach(c => { if (!(c in cc)) cc[c] = 0; });
    $('fCty').innerHTML = Object.keys(cc).sort((a, b) => (cc[b] - cc[a]) || a.localeCompare(b)).map(c => `<button type="button" class="hl-chip${F.xc.includes(c) ? ' off' : ''}" data-cty="${esc(c)}" aria-pressed="${F.xc.includes(c)}">${F.xc.includes(c) ? '🚫 ' : ''}${esc(c)} <small>${cc[c]}</small></button>`).join('') || '<span class="hl-src">No spots yet.</span>';
    $('sCty').textContent = F.xc.length ? F.xc.length + ' HIDDEN' : 'NONE';
    activeBox();
  }
  document.addEventListener('click', e => {
    const t = e.target.closest('[data-g=p],[data-band],[data-mode],[data-where],#fHide,#fNew,#fRange,#fQrt'); if (!t) return;
    const tog = (a, v) => a.includes(v) ? a.filter(x => x !== v) : a.concat(v);
    if (t.dataset.g === 'p') { F.p = tog(F.p, t.dataset.v); if (!F.p.length) F.p = [t.dataset.v]; }
    else if (t.dataset.band) F.bands = tog(F.bands, t.dataset.band);
    else if (t.dataset.mode) F.modes = tog(F.modes, t.dataset.mode);
    else if (t.dataset.where) { F.where = t.dataset.where; if (F.where === 'range' && !HOME) { openModal('suModal', 'hHome'); $('hHome').textContent = 'Set where you are first.'; } }
    else if ((t.id === 'fHide' || t.id === 'fNew') && !hasLog()) { toast('Load your worked parks first (' + (PUB ? '📄 LOAD MY WORKED PARKS' : '⭐ GET MY PARKS FROM POTA') + '): until then the page can’t tell which parks you’ve worked.'); return; }
    else if (t.id === 'fQrt') F.qrt = !F.qrt;
    else if (t.id === 'fCalls') { F.hc = !F.hc; if (F.hc && !callsToday().size) toast(PUB ? 'Tap 🙈 HIDE … TODAY (or ✓ I WORKED IT) on a spot and that call drops out of the list until 0000 UTC.' : 'Calls you log today (and ones you tap 🙈 on) drop out of the list until 0000 UTC.'); }
    else if (t.id === 'fHide') F.hide = !F.hide; else if (t.id === 'fNew') F.nw = !F.nw; else if (t.id === 'fRange') { F.rg = !F.rg; if (F.rg && !HOME) { openModal('suModal', 'hHome'); $('hHome').textContent = 'Set where you are first.'; } }
    saveF(); chips(); ticker(false); draw();
  });
  /* the box that shows what you're filtering, each with an ✕, plus CLEAR ALL */
  const F0 = { p: ['POTA', 'WWFF', 'SOTA', 'DXPED', 'EVENT', 'DX'], qrt: false, hc: false, hide: false, nw: false, bands: [], modes: [], where: 'all', st: '', q: '', xc: [] };
  function activeBox() {
    const it = [];
    const PN = { POTA: 'POTA', WWFF: 'WWFF / KFF', SOTA: 'SOTA', DXPED: 'DXPEDITIONS', EVENT: 'SPECIAL EVENTS', DX: 'DX CLUSTER' };
    const pOff = F0.p.filter(x => !F.p.includes(x)), pOn = F.p.filter(x => !F0.p.includes(x));
    if (pOff.length || pOn.length) it.push(['p', 'Showing: ' + F.p.map(x => PN[x]).join(', ')]);
    if (F.hide) it.push(['hide', '🙈 Hiding parks I’ve hunted']);
    if (F.qrt) it.push(['qrt', '🚫 Hiding QRT']);
    if (F.hc) it.push(['hc', `🙋 Hiding calls I've worked today (${callsToday().size})`]);
    if (F.nw) it.push(['nw', '✨ New to me only']);
    F.bands.forEach(b => it.push(['band:' + b, 'Band ' + b]));
    F.modes.forEach(m => it.push(['mode:' + m, 'Mode ' + m]));
    if (F.where !== 'all') it.push(['where', (WHERE.find(w => w[0] === F.where) || [0, F.where])[1]]);
    if (F.st) it.push(['st', 'State ' + F.st]);
    if (F.q.trim()) it.push(['q', 'Search “' + F.q.trim() + '”']);
    F.xc.forEach(c => it.push(['xc:' + c, '🚫 ' + c]));
    const fb = $('hlFbN'); if (fb) fb.textContent = it.length ? it.length + ' ON' : '';
    const ft = $('hlFtogN'); if (ft) ft.textContent = ($('hlFilters').classList.contains('open') ? 'CLOSE ▴' : 'TAP TO OPEN ▾') + (it.length ? ` · ${it.length} ON` : '');
    const b = $('hlActive'); b.hidden = !it.length;
    b.innerHTML = it.length ? `<b>⚙</b>${it.map(([k, t]) => `<button type="button" class="hl-pill" data-unf="${esc(k)}" title="Remove this filter">${esc(t)} ✕</button>`).join('')}<button type="button" class="hl-btn line sm" data-unf="def" title="Back to the usual filters: POTA, phone, hide hunted parks and QRT">↺ DEFAULT</button><button type="button" class="hl-btn line sm" data-unf="*" title="Clear all filters">✕ ALL</button>` : '';
  }
  document.addEventListener('click', e => {
    const c = e.target.closest('[data-cty]');
    if (c) { const v = c.dataset.cty; F.xc = F.xc.includes(v) ? F.xc.filter(x => x !== v) : F.xc.concat(v); saveF(); chips(); ticker(false); draw(); return; }
    const u = e.target.closest('[data-unf]'); if (!u) return;
    const k = u.dataset.unf;
    if (k === '*') Object.assign(F, JSON.parse(JSON.stringify(F0)));
    else if (k === 'def') Object.assign(F, JSON.parse(JSON.stringify(F0)), { p: ['POTA'], hide: true, qrt: true, modes: ['PHONE'] });
    else if (k === 'p') F.p = F0.p.slice(); else if (k === 'hide') F.hide = false; else if (k === 'qrt') F.qrt = false; else if (k === 'hc') F.hc = false; else if (k === 'nw') F.nw = false; else if (k === 'where') F.where = 'all'; else if (k === 'st') F.st = ''; else if (k === 'q') F.q = '';
    else if (k.startsWith('band:')) F.bands = F.bands.filter(x => x !== k.slice(5)); else if (k.startsWith('mode:')) F.modes = F.modes.filter(x => x !== k.slice(5)); else if (k.startsWith('xc:')) F.xc = F.xc.filter(x => x !== k.slice(3));
    saveF(); chips(); ticker(false); draw();
  });
  $('hlFtog').onclick = () => { const f = $('hlFilters'); f.classList.toggle('open'); if ($('hlFbtn')) $('hlFbtn').setAttribute('aria-expanded', f.classList.contains('open')); $('hlFtog').setAttribute('aria-expanded', f.classList.contains('open')); activeBox(); };
  document.addEventListener('click', e => { const v = e.target.closest('[data-view]'); if (!v) return; F.view = v.dataset.view; saveF(); viewChips(); draw(); });
  function viewChips() { document.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', (F.view || 'cards') === b.dataset.view)); }
  $('fSt').onchange = () => { F.st = $('fSt').value; saveF(); chips(); draw(); };
  $('fSort').onchange = () => { F.sort = $('fSort').value; saveF(); draw(); };
  $('fQ').oninput = () => { F.q = $('fQ').value; saveF(); activeBox(); draw(); };
  document.addEventListener('click', e => { document.querySelectorAll('.hl-dd[open]').forEach(d => { if (!d.contains(e.target)) d.open = false; }); });
  document.querySelectorAll('.hl-dd').forEach(d => d.addEventListener('toggle', () => { if (d.open) document.querySelectorAll('.hl-dd[open]').forEach(o => { if (o !== d) o.open = false; }); }));

  /* ---------------- your log ---------------- */
  function logInfo() {
    const c = { POTA: 0, WWFF: 0, SOTA: 0 }; WK.forEach(r => c[progOf(r)]++);
    
    $('hProgs').innerHTML = WK.size ? Object.entries(c).map(([k, v]) => `<span>${k} <b>${v}</b></span>`).join('') : '';
    const when = LOG.t ? new Date(LOG.t).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) : '';
    const old = LOG.t && Date.now() - LOG.t > 14 * 864e5;
    const m = $('hMsg');
    if (!WK.size) { m.className = 'hl-msg'; m.textContent = 'No log loaded on this device yet.'; }
    else { m.className = 'hl-msg ' + (old ? 'bad' : 'ok'); m.innerHTML = `✓ ${WK.size} worked on this device${LOG.file ? ' from <b>' + esc(LOG.file) + '</b>' : ''}${when ? ', loaded ' + when : ''}${MAN.size ? ` (${MAN.size} added by hand)` : ''}.${old ? ' That was over 2 weeks ago: upload a fresh copy so new contacts count.' : ''}`; }
  }
  async function takeFiles(files) {
    let all = new Set(), names = [];
    for (const f of files) { try { const t = await f.text(); scan(t).forEach(r => all.add(r)); names.push(f.name); } catch (e) {} }
    const m = $('hMsg');
    if (!all.size) { m.className = 'hl-msg bad'; m.textContent = `No POTA, WWFF or SOTA numbers found in ${names.join(', ') || 'that file'}. Is it the hunted parks / chaser log file?`; return; }
    if (!$('hAdd').checked) { WK = new Set(MAN); }
    all.forEach(r => WK.add(r));
    LOG.t = Date.now(); LOG.file = names.join(', '); saveLog(); logInfo(); ticker(false); draw(); needDraw(); topDraw();
    m.innerHTML += ` <b>Found ${all.size}</b> in the file.`;
  }
  $('hFile').onchange = e => { if (e.target.files.length) takeFiles([...e.target.files]); e.target.value = ''; };
  const dz = $('hDrop');
  ['dragenter', 'dragover'].forEach(v => dz.addEventListener(v, e => { e.preventDefault(); dz.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(v => dz.addEventListener(v, e => { e.preventDefault(); dz.classList.remove('over'); }));
  dz.addEventListener('drop', e => { if (e.dataTransfer.files.length) takeFiles([...e.dataTransfer.files]); });
  $('hClear').onclick = () => { if (!confirm('Clear the worked list saved on this device?')) return; WK = new Set(); MAN = new Set(); LOG = { t: 0, file: '', r: [], m: [] }; saveLog(); logInfo(); ticker(false); draw(); needDraw(); };
  $('hCall').value = CALL;
  $('hCall').onchange = () => { CALL = base($('hCall').value); $('hCall').value = CALL; put('kpcMyCall', CALL); topDraw(); myStats(); };

  /* ---------------- home + range ---------------- */
  function homeInfo() {
    $('hHome').innerHTML = HOME ? `📍 Home: <b>${esc(HOME.label)}</b> · normal range ${RANGE} miles` : 'Not set yet: every new park goes on the big ticker.';
    $('hRange').innerHTML = [300, 600, 1000, 1500, 2500, 4000].map(r => `<button type="button" class="hl-chip" data-rg="${r}" aria-pressed="${RANGE === r}">${r} MI</button>`).join('');
    $('hFarMode').checked = !!FAR; $('hNotify').checked = !!NOTE;
  }
  const setHome = (la, lo, label) => { HOME = { la, lo, label }; put('kpcHuntHome', HOME); homeInfo(); ticker(false); draw(); };
  $('hGps').onclick = () => {
    if (!navigator.geolocation) { $('hHome').textContent = 'This browser can’t share your location. Pick your state instead.'; return; }
    $('hHome').textContent = 'Finding you…';
    navigator.geolocation.getCurrentPosition(p => setHome(+p.coords.latitude.toFixed(3), +p.coords.longitude.toFixed(3), 'your location (' + p.coords.latitude.toFixed(2) + ', ' + p.coords.longitude.toFixed(2) + ')'),
      () => { $('hHome').textContent = 'Location not allowed. Pick your state or type your grid instead.'; }, { timeout: 15000, maximumAge: 6e5 });
  };
  $('hSt').onchange = async () => {
    const a = $('hSt').value; if (!a) return;
    try {
      const B = await fetch('kpc-us-states.json').then(r => r.json()); const b = B.find(x => x.a === a); let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
      b.p.forEach(pl => pl[0].forEach(([x, y]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }));
      setHome(+((y0 + y1) / 2).toFixed(3), +((x0 + x1) / 2).toFixed(3), 'middle of ' + ST[a]);
    } catch (e) { $('hHome').textContent = 'Couldn’t load the state map. Try your grid square.'; }
    if (!$('nSt').dataset.set) { $('nSt').value = a; $('tSt').value = a; needLoad(); topDraw(); }
  };
  $('hGrid').onchange = () => { const g = grid($('hGrid').value); if (g) setHome(+g[0].toFixed(3), +g[1].toFixed(3), 'grid ' + $('hGrid').value.toUpperCase()); else $('hHome').textContent = 'That grid doesn’t look right (like EM77 or EM77ab).'; };
  document.addEventListener('click', e => { const b = e.target.closest('[data-rg]'); if (!b) return; RANGE = +b.dataset.rg; put('kpcHuntRange', RANGE); homeInfo(); ticker(false); draw(); });
  $('hFarMode').onchange = () => { FAR = $('hFarMode').checked; put('kpcHuntFar', FAR); ticker(false); };
  $('hNotify').onchange = async () => {
    NOTE = $('hNotify').checked;
    if (NOTE && 'Notification' in window && Notification.permission !== 'granted') { try { const p = await Notification.requestPermission(); if (p !== 'granted') { NOTE = false; $('hNotify').checked = false; alert('Notices are blocked for this site in your browser settings.'); } } catch (e) { NOTE = false; $('hNotify').checked = false; } }
    if (NOTE && !('Notification' in window)) { NOTE = false; $('hNotify').checked = false; alert('This browser can’t show notices. On iPhone, add this page to your Home Screen first.'); }
    put('kpcHuntNote', NOTE);
  };

  /* ---------------- parks I still need ---------------- */
  let NP = [], nShown = 120, nSrc = '';
  const stOpts = sel => Object.keys(ST).map(a => `<option value="${a}"${a === sel ? ' selected' : ''}>${ST[a]}</option>`).join('');
  let NV = get('kpcHuntNV', 'list'), BORDERS = null;
  async function needLoad() {
    const a = $('nSt').value; $('nList').innerHTML = '<div class="hl-empty">Loading ' + esc(ST[a]) + '’s parks…</div>'; $('nBar').innerHTML = ''; NP = []; nShown = 120;
    try { const L = await jget('https://api.pota.app/location/parks/US-' + a, 45000); NP = (L || []).filter(p => p && p.reference).map(p => ({ r: nref(p.reference), n: p.name || p.reference, a: +p.activations || 0, la: +p.latitude, lo: +p.longitude })); nSrc = 'POTA'; } catch (e) { NP = []; }
    if (!NP.length) { await loadParks(); NP = Object.entries(PK).filter(([r, k]) => k.st === a && /^US-/.test(r)).map(([r, k]) => ({ r, n: k.n || r, a: +k.a || 0, la: k.la, lo: k.lo })); nSrc = 'KPC copy'; }
    if (!NP.length) { $('nList').innerHTML = `<div class="hl-empty">Couldn’t load ${esc(ST[a])}’s parks just now. <button type="button" class="hl-btn line sm" id="nRetry">TRY AGAIN</button></div>`; $('nRetry').onclick = needLoad; return; }
    needDraw();
  }
  function nvChips() { document.querySelectorAll('[data-nv]').forEach(b => b.setAttribute('aria-pressed', NV === b.dataset.nv)); }
  document.addEventListener('click', e => { const b = e.target.closest('[data-nv]'); if (!b) return; NV = b.dataset.nv; put('kpcHuntNV', NV); nvChips(); needDraw(); });
  function needDraw() {
    try {
      nvChips();
      const a = $('nSt').value, q = $('nQ').value.trim().toUpperCase(), air = new Map(SP.filter(s => s.p === 'POTA').map(s => [s.ref, s]));
      $('nMap').hidden = NV !== 'map';
      if (NV === 'all') { allStates(); return; }
      if (!NP.length) return;
      const done = NP.filter(p => WK.has(p.r)).length, pct = Math.round(done / NP.length * 100);
      $('nBar').innerHTML = `<div class="bar"><i style="width:${pct}%"></i></div><p><b>${done.toLocaleString()}</b> of <b>${NP.length.toLocaleString()}</b> ${esc(ST[a])} parks worked (${pct}%) · <b>${(NP.length - done).toLocaleString()}</b> still to go${hasLog() ? '' : ' · tap ⭐ GET MY PARKS FROM POTA to see yours'}</p>`;
      let L = NP.filter(p => !WK.has(p.r) && (!q || (p.r + ' ' + p.n).toUpperCase().includes(q)) && (!$('nAir').checked || air.has(p.r)));
      const s = $('nSort').value;
      L.sort(s === 'name' ? (x, y) => String(x.n).localeCompare(String(y.n)) : s === 'ref' ? (x, y) => x.r.localeCompare(y.r, undefined, { numeric: true }) : s === 'busy' ? (x, y) => y.a - x.a : (x, y) => (x.a - y.a) || String(x.n).localeCompare(String(y.n)));
      L.sort((x, y) => air.has(y.r) - air.has(x.r));
      if (NV === 'map') stateMap(a, air);
      $('nList').innerHTML = L.length ? L.slice(0, nShown).map(p => { const o = air.get(p.r); return `<div class="hn${o ? ' air' : ''}"><a class="r" href="https://pota.app/#/park/${encodeURIComponent(p.r)}" target="_blank" rel="noopener">${esc(p.r)}</a>${esc(p.n)}<div class="m">${p.a ? p.a + ' activation' + (p.a === 1 ? '' : 's') : 'never activated'}${p.a > 0 && p.a <= 5 ? ' · RARE' : ''} · <a href="kpc-planner-us.html?q=${encodeURIComponent(p.r)}">map</a></div>${o ? `<div class="air">📡 ON THE AIR: ${esc(o.call)} ${(o.khz / 1000).toFixed(3)} ${esc(o.mode)}</div>` : ''}</div>`; }).join('')
        + (L.length > nShown ? `<div class="hl-row" style="grid-column:1/-1"><button type="button" class="hl-btn line sm" id="nMore">SHOW MORE (${(L.length - nShown).toLocaleString()} left)</button></div>` : '')
        : `<div class="hl-empty">${q || $('nAir').checked ? 'None match.' : hasLog() ? '🎉 You’ve worked every park in ' + esc(ST[a]) + '!' : 'Load your parks first.'}</div>`;
      const m = $('nMore'); if (m) m.onclick = () => { nShown += 200; needDraw(); };
    } catch (e) { $('nList').innerHTML = '<div class="hl-empty">Something went wrong drawing this list: ' + esc(e.message) + '</div>'; }
  }
  /* state view: the state's outline with every park as a dot (gold = still needed, green = worked, pulsing = on the air now) */
  let NM = null, NMG = null;
  async function stateMap(a, air) {
    const box = $('nMap');
    try { BORDERS = BORDERS || await fetch('kpc-us-states.json').then(r => r.json()); } catch (e) { box.innerHTML = '<div class="hl-empty">Couldn’t load the state map.</div>'; return; }
    const b = BORDERS.find(x => x.a === a); if (!b || !window.L) { box.innerHTML = '<div class="hl-empty">The map couldn’t load here.</div>'; return; }
    if (!NM) {
      box.innerHTML = '<div id="nLmap"></div><p class="hl-src">🟡 gold = still needed · 🟢 green = hunted · 🔴 pulsing red = on the air now. Tap a dot for the park.</p><p class="hl-msg" id="nPick"></p>';
      NM = L.map('nLmap', { zoomSnap: .25 });
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18, attribution: 'Imagery © Esri, Maxar, Earthstar Geographics' }).addTo(NM);
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18, opacity: .9 }).addTo(NM);
      NMG = L.layerGroup().addTo(NM);
    }
    setTimeout(() => NM.invalidateSize(), 30);
    NMG.clearLayers();
    const gj = { type: 'MultiPolygon', coordinates: b.p.map(pl => pl.map(r => r.map(([x, y]) => [x, y]))) };
    const out = L.geoJSON(gj);   /* not drawn (Brandon Oct 16: the satellite map already shows state lines); only used to fit the view */
    let bb = out.getBounds(); if (a === 'AK') bb = L.latLngBounds([51, -179], [71.5, -129]);
    NM.fitBounds(bb, { padding: [12, 12] });
    NP.filter(p => isFinite(p.la) && isFinite(p.lo)).forEach(p => {
      const w = WK.has(p.r), o = air.get(p.r);
      const m = o ? L.marker([p.la, p.lo], { icon: L.divIcon({ className: 'hl-pin red', html: '<span></span>', iconSize: [22, 22], iconAnchor: [11, 11] }), zIndexOffset: 1000 })
        : L.circleMarker([p.la, p.lo], { radius: w ? 4.5 : 6, color: '#1a1208', weight: 1.2, fillColor: w ? '#3ddc84' : '#ffcf7a', fillOpacity: w ? .75 : .95 });
      m.bindPopup(`<div class="hl-pop"><span class="r">${esc(p.r)}</span> ${esc(p.n)}<br>${p.a ? p.a + ' activations' : 'never activated'}${p.a > 0 && p.a <= 5 ? ' · RARE' : ''} · ${w ? '<span class="pw">✓ hunted</span>' : '<b>still needed</b>'}${o ? `<br><span class="pn">📡 ON THE AIR: ${esc(o.call)} ${(o.khz / 1000).toFixed(3)} ${esc(o.mode)}</span>` : ''}<div class="hl-popb"><a href="https://pota.app/#/park/${encodeURIComponent(p.r)}" target="_blank" rel="noopener">POTA PAGE</a><a href="kpc-planner-us.html?q=${encodeURIComponent(p.r)}">TRIP PLANNER</a></div></div>`, { maxWidth: 260 }).addTo(NMG);
    });
  }
  document.addEventListener('click', e => { const c = e.target.closest('[data-pr]'); if (!c) return; const p = NP.find(x => x.r === c.dataset.pr); if (p) $('nPick').innerHTML = `<a href="https://pota.app/#/park/${encodeURIComponent(p.r)}" target="_blank" rel="noopener"><b>${esc(p.r)}</b></a> ${esc(p.n)} · ${p.a ? p.a + ' activations' : 'never activated'} · ${WK.has(p.r) ? '✓ worked' : 'still needed'} · <a href="kpc-planner-us.html?q=${encodeURIComponent(p.r)}">trip planner</a>`; });
  /* all states at a glance: worked / total in every state (our weekly park list + Kentucky's own file) */
  async function allStates() {
    await loadParks();
    const tot = {}, wk = {};
    Object.entries(PK).forEach(([r, k]) => { if (!/^US-/.test(r) || !k.st) return; tot[k.st] = (tot[k.st] || 0) + 1; if (WK.has(r)) wk[k.st] = (wk[k.st] || 0) + 1; });
    const L = Object.keys(ST).filter(x => tot[x]).map(x => [x, wk[x] || 0, tot[x]]).sort((p, q) => (q[1] / q[2]) - (p[1] / p[2]) || p[0].localeCompare(q[0]));
    const all = L.reduce((n, r) => n + r[1], 0), T = L.reduce((n, r) => n + r[2], 0);
    $('nBar').innerHTML = `<p><b>${all.toLocaleString()}</b> of <b>${T.toLocaleString()}</b> US parks worked (${Math.round(all / T * 100)}%). Tap a state for its list.</p>`;
    $('nList').innerHTML = L.map(([x, w, t]) => `<button type="button" class="hn hs-st" data-sto="${x}"><b>${x}</b> ${esc(ST[x])}<div class="bar"><i style="width:${Math.round(w / t * 100)}%"></i></div><div class="m">${w.toLocaleString()} / ${t.toLocaleString()} · ${(t - w).toLocaleString()} to go</div></button>`).join('');
  }
  document.addEventListener('click', e => { const b = e.target.closest('[data-sto]'); if (!b) return; $('nSt').value = b.dataset.sto; $('nSt').dataset.set = 1; NV = 'list'; put('kpcHuntNV', NV); needLoad(); });
  $('nSt').onchange = () => { $('nSt').dataset.set = 1; needLoad(); };
  $('nQ').oninput = needDraw; $('nSort').onchange = needDraw; $('nAir').onchange = needDraw;

  /* ---------------- top activators + my numbers ---------------- */
  let TT = 'acts', TD = {};
  async function topDraw() {
    if (!$('tList')) return;   /* the Top section moved to its own Members Room page, kpc-top50.html (Oct 16) */
    const a = $('tSt').value;
    if (!TD[a]) { $('tList').innerHTML = '<div class="hl-empty">Loading…</div>'; TD[a] = await fetch('data/leaders/US-' + a + '.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null) || { none: 1 }; }
    const d = TD[a];
    if (d.none) { $('tList').innerHTML = `<div class="hl-empty">${esc(ST[a])}’s list is still being added up. It fills in within a week.</div>`; $('tSrc').textContent = ''; return; }
    const L = d[TT] || [], me = CALL ? L.findIndex(r => r[0] === CALL) : -1;
    const v = (n, l) => `<span class="v">${(+n || 0).toLocaleString()}<small>${l}</small></span>`;
    const COLS = { acts: r => v(r[1], 'ACTIVATIONS') + v(r[2], 'PARKS') + v(r[3], 'QSOS'), uniq: r => v(r[2], 'PARKS') + v(r[1], 'ACTIVATIONS') + v(r[3], 'QSOS'),
      hunt: r => v(r[1], 'QSOS') + v(r[2], 'PARKS (TOP 10)'), huntp: r => v(r[2], 'PARKS (TOP 10)') + v(r[1], 'QSOS') };
    const row = (r, i) => `<div class="ht${r[0] === CALL ? ' me' : ''}${/^hunt/.test(TT) ? ' two' : ''}"><span class="n">${i + 1}</span><span class="c"><a href="https://www.qrz.com/db/${encodeURIComponent(r[0])}" target="_blank" rel="noopener">${esc(r[0])}</a></span>${COLS[TT](r)}</div>`;
    $('tList').innerHTML = !L.length ? `<div class="hl-empty">${/^hunt/.test(TT) ? 'The hunter list is being added up this week.' : 'No activations yet.'}</div>` : L.slice(0, 20).map(row).join('') + (me >= 20 ? row(L[me], me) : '');
    $('tSrc').innerHTML = /^hunt/.test(TT)
      ? `Hunters in ${esc(ST[a])}: POTA only shares each park’s top 10 hunters, so KPC adds those lists up across the state’s ${d.parks.toLocaleString()} parks. QSOS = contacts counted where they’re in a park’s top 10; PARKS = how many ${esc(ST[a])} parks they’re top 10 at. Close, but not an official count. Updated ${esc(d.updated)}, weekly.`
      : `${esc(ST[a])}: ${d.activators.toLocaleString()} activators across ${d.activated.toLocaleString()} activated parks (${d.parks.toLocaleString()} parks in all). Added up by KPC from POTA’s public activation lists (10+ contacts counts, calls like K4TEST/P count as K4TEST). Updated ${esc(d.updated)}, weekly.${CALL && me < 0 ? ` ${esc(CALL)} isn’t in this state’s top 50 yet.` : ''}`;
  }
  document.addEventListener('click', e => { const b = e.target.closest('[data-t]'); if (!b) return; TT = b.dataset.t; document.querySelectorAll('[data-t]').forEach(x => x.setAttribute('aria-pressed', x === b)); topDraw(); });
  if ($('tSt')) $('tSt').onchange = topDraw;
  async function myStats() {
    if (!$('mStats')) return;
    const box = $('mStats'); const c = { POTA: 0, WWFF: 0, SOTA: 0 }; WK.forEach(r => c[progOf(r)]++);
    const logBits = hasLog() ? `<div class="g"><b>${c.POTA.toLocaleString()}</b><span>POTA IN YOUR LOG</span></div><div><b>${c.WWFF.toLocaleString()}</b><span>WWFF IN YOUR LOG</span></div><div><b>${c.SOTA.toLocaleString()}</b><span>SOTA IN YOUR LOG</span></div>` : '';
    if (!CALL) { box.innerHTML = logBits ? `<div class="hm">${logBits}</div>` : '<div class="hl-empty">Put your call sign in Step 1.</div>'; return; }
    box.innerHTML = '<div class="hl-empty">Asking POTA…</div>';
    try {
      const j = await jget('https://api.pota.app/stats/user/' + encodeURIComponent(CALL)), A = j.activator || {}, H = j.hunter || {};
      const n = v => (+v || 0).toLocaleString();
      box.innerHTML = `<div class="hm"><div class="g"><b>${n(H.parks)}</b><span>PARKS HUNTED</span></div><div><b>${n(H.qsos)}</b><span>HUNTER CONTACTS</span></div><div class="g"><b>${n(A.activations)}</b><span>ACTIVATIONS</span></div><div><b>${n(A.parks)}</b><span>PARKS ACTIVATED</span></div><div><b>${n(A.qsos)}</b><span>ACTIVATOR CONTACTS</span></div><div><b>${n(j.awards)}</b><span>AWARDS</span></div>${logBits}</div>
 <p class="hl-src">${esc(j.callsign || CALL)} from POTA’s public stats. <a href="https://pota.app/#/profile/${encodeURIComponent(CALL)}" target="_blank" rel="noopener">POTA PROFILE ↗</a></p>`;
    } catch (e) { box.innerHTML = (logBits ? `<div class="hm">${logBits}</div>` : '') + `<p class="hl-src">POTA didn’t answer for ${esc(CALL)}. Check the call, or try again later.</p>`; }
  }

  /* keep the big ticker just under the site's sticky top bar */
  let stq = 0;
  function stick() { stq = 0; const h = document.querySelector('header.site-nav, .site-nav'); let t = 0; if (h) { const cs = getComputedStyle(h); if (/sticky|fixed/.test(cs.position)) t = Math.max(0, Math.round(h.getBoundingClientRect().bottom)); } $('hlTick').style.top = t + 'px'; }
  addEventListener('resize', stick); addEventListener('scroll', () => { if (!stq) stq = requestAnimationFrame(stick); }, { passive: true }); setInterval(stick, 400);
  /* ---------------- my hunting log (Brandon Oct 16: tap a station, it fills in; must be bullet proof) ----------------
     Saved on every change in TWO places on the device: localStorage (kpcHuntQSO) and IndexedDB (kpc-hunt / kv / qso),
     the newer copy wins on load. The page asks the browser to keep it (navigator.storage.persist). On computers with
     Chrome/Edge, KEEP A BACKUP FILE picks a file on the computer that is rewritten (whole log, ADIF) after every save.
     DOWNLOAD FOR QRZ = ADIF 3.1.4 (POTA_REF / WWFF_REF / SOTA_REF + SIG/SIG_INFO). RESTORE reads an ADIF back in. */
  const QK = 'kpcHuntQSO';
  let Q = get(QK, null); if (!Q || !Array.isArray(Q.q)) Q = { v: 1, u: 0, grid: '', q: [], x: 0 };
  let IDB = null, FH = null, FHok = false, PERSIST = null, IDBok = false;
  const idb = () => IDB || (IDB = new Promise((res, rej) => { try { const r = indexedDB.open('kpc-hunt', 1); r.onupgradeneeded = () => r.result.createObjectStore('kv'); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); } catch (e) { rej(e); } }));
  const idbGet = k => idb().then(db => new Promise((res, rej) => { const t = db.transaction('kv').objectStore('kv').get(k); t.onsuccess = () => res(t.result); t.onerror = () => rej(t.error); }));
  const idbPut = (k, v) => idb().then(db => new Promise((res, rej) => { const t = db.transaction('kv', 'readwrite'); t.objectStore('kv').put(v, k); t.oncomplete = () => res(); t.onerror = () => rej(t.error); }));
  const utc = d => ({ d: d.toISOString().slice(0, 10).replace(/-/g, ''), t: d.toISOString().slice(11, 16).replace(':', '') });
  const fmtD = d => d ? d.slice(0, 4) + '-' + d.slice(4, 6) + '-' + d.slice(6, 8) : '';
  const fmtT = t => t ? t.slice(0, 2) + ':' + t.slice(2, 4) : '';
  async function qSave() {
    Q.u = Date.now();
    put(QK, Q);
    try { await idbPut('qso', JSON.parse(JSON.stringify(Q))); IDBok = true; } catch (e) { IDBok = false; }
    if (PERSIST === null && navigator.storage && navigator.storage.persist) { try { PERSIST = await navigator.storage.persist(); } catch (e) { PERSIST = false; } }
    if (FH && FHok) { try { const w = await FH.createWritable(); await w.write(adif(Q.q)); await w.close(); } catch (e) { FHok = false; } }
    safe();
  }
  async function qsoInit() {
    try { const o = await idbGet('qso'); IDBok = true; if (o && Array.isArray(o.q) && ((o.u || 0) > (Q.u || 0) || o.q.length > Q.q.length)) { Q = o; put(QK, Q); } } catch (e) {}
    try { FH = await idbGet('file'); if (FH && FH.queryPermission) FHok = (await FH.queryPermission({ mode: 'readwrite' })) === 'granted'; } catch (e) { FH = null; }
    if (navigator.storage && navigator.storage.persisted) { try { PERSIST = await navigator.storage.persisted(); } catch (e) {} }
    $('lgMy').value = CALL; $('lgGrid').value = Q.grid || '';
    if (!window.showSaveFilePicker) $('lgFile').hidden = true;
    safe(); qList();
  }
  function safe() {
    const n = Q.q.length, nx = Q.q.filter(q => !q.x).length, c = [];
    c.push(`<span>✓ ${n} contact${n === 1 ? '' : 's'} saved on this device</span>`);
    if (IDBok) c.push('<span>✓ second copy kept</span>');
    c.push(PERSIST ? '<span>✓ browser told to keep it</span>' : '<span class="warn">this browser may clear site data when space runs low: download a copy now and then</span>');
    if (FH) c.push(FHok ? `<span>✓ backup file kept up to date${FH.name ? ': ' + esc(FH.name) : ''}</span>` : '<button type="button" class="hl-btn line sm" id="lgRe">🔄 TAP TO RECONNECT THE BACKUP FILE</button>');
    if (nx) c.push(`<span class="warn">${nx} not downloaded yet</span>`);
    $('lgSafe').innerHTML = n || FH ? c.join('') : '';
    const re = $('lgRe'); if (re) re.onclick = async () => { try { FHok = (await FH.requestPermission({ mode: 'readwrite' })) === 'granted'; } catch (e) {} if (FHok) qSave(); else safe(); };
  }
  $('lgFile').onclick = async () => {
    try { FH = await window.showSaveFilePicker({ suggestedName: `KPC-hunting-log-${CALL || 'mine'}.adi`, types: [{ description: 'ADIF log', accept: { 'text/plain': ['.adi'] } }] }); FHok = true; await idbPut('file', FH); await qSave(); toast('✓ Backup file set. It updates after every save.'); } catch (e) {}
  };
  /* ---------- ADIF ---------- */
  const enc = new TextEncoder();
  const af = (k, v) => { v = String(v == null ? '' : v).replace(/[<>]/g, ''); return v === '' ? '' : `<${k}:${enc.encode(v).length}>${v} `; };
  function adMode(m) { m = String(m || '').toUpperCase(); if (m === 'FT4') return ['MFSK', 'FT4']; if (m === 'JS8') return ['MFSK', 'JS8']; if (m === 'PSK31') return ['PSK', 'PSK31']; if (/^(USB|LSB)$/.test(m)) return ['SSB', m]; if (m === 'OTHER' || !m) return ['SSB', '']; return [m, '']; }
  function adif(L) {
    let o = `KPC Hunters Lounge log\n${af('ADIF_VER', '3.1.4')}${af('PROGRAMID', 'KPC Hunters Lounge')}${af('CREATED_TIMESTAMP', new Date().toISOString().replace(/[-:]/g, '').replace('T', ' ').slice(0, 15))}<EOH>\n`;
    L.forEach(q => {
      const [md, sm] = adMode(q.mode), refs = String(q.ref || '').toUpperCase().split(/[ ,]+/).filter(Boolean);
      const pota = refs.filter(r => progOf(r) === 'POTA'), wwff = refs.filter(r => progOf(r) === 'WWFF'), sota = refs.filter(r => progOf(r) === 'SOTA');
      o += af('CALL', q.call) + af('QSO_DATE', q.d) + af('TIME_ON', q.tm) + af('FREQ', q.f) + af('BAND', q.band) + af('MODE', md) + af('SUBMODE', sm) + af('RST_SENT', q.rs) + af('RST_RCVD', q.rr)
        + af('STATION_CALLSIGN', q.my || CALL) + af('OPERATOR', q.my || CALL) + af('MY_GRIDSQUARE', q.grid || Q.grid)
        + af('POTA_REF', pota.join(',')) + af('WWFF_REF', wwff[0] || '') + af('SOTA_REF', sota[0] || '')
        + (pota.length ? af('SIG', 'POTA') + af('SIG_INFO', pota[0]) : wwff.length ? af('SIG', 'WWFF') + af('SIG_INFO', wwff[0]) : '')
        + af('NAME', q.on || '') + af('QTH', q.qth || '') + af('GRIDSQUARE', q.tg || '') + af('STATE', /^[A-Z]{2}$/.test(q.st || '') && ST[q.st] ? q.st : '') + af('COMMENT', [refs.join(' '), q.name].filter(Boolean).join(' ').slice(0, 120)) + af('NOTES', q.note) + '<EOR>\n';
    });
    return o;
  }
  function parseAdif(t) {
    const out = []; t = String(t || ''); const h = t.search(/<eoh>/i); if (h >= 0) t = t.slice(h + 5);
    t.split(/<eor>/i).forEach(rec => {
      const r = {}; const re = /<(\w+):(\d+)(?::\w)?>/g; let m;
      while ((m = re.exec(rec))) { r[m[1].toUpperCase()] = rec.substr(re.lastIndex, +m[2]); re.lastIndex += +m[2]; }
      if (!r.CALL || !r.QSO_DATE) return;
      const refs = [r.POTA_REF, r.WWFF_REF, r.SOTA_REF, r.SIG_INFO].filter(Boolean).join(',').toUpperCase().split(/[ ,]+/).filter(Boolean).map(nref);
      out.push({ id: 'i' + Math.random().toString(36).slice(2, 10), call: r.CALL.toUpperCase(), d: r.QSO_DATE, tm: String(r.TIME_ON || '').slice(0, 4), f: r.FREQ || '', band: (r.BAND || '').toLowerCase(), mode: r.SUBMODE || r.MODE || '',
        ref: [...new Set(refs)].join(', '), name: '', st: r.STATE || '', rs: r.RST_SENT || '', rr: r.RST_RCVD || '', note: r.NOTES || '', my: r.STATION_CALLSIGN || '', grid: r.MY_GRIDSQUARE || '', x: 1, t: Date.now() });
    });
    return out;
  }
  function download(name, text, type) {
    const blob = new Blob([text], { type: type || 'text/plain' });
    const touch = matchMedia('(pointer:coarse)').matches;
    if (touch && navigator.canShare) { try { const f = new File([blob], name, { type: 'text/plain' }); if (navigator.canShare({ files: [f] })) return navigator.share({ files: [f], title: name }).then(() => true).catch(() => false); } catch (e) {} }
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
    return Promise.resolve(true);
  }
  async function exp(onlyNew) {
    const L = onlyNew ? Q.q.filter(q => !q.x) : Q.q.slice();
    if (!L.length) { toast(onlyNew ? 'Nothing new since your last download.' : 'No contacts to download yet.'); return; }
    if (!CALL) { toast('Put your call sign in "My call" first: QRZ needs it on every contact.'); $('lgMy').focus(); return; }
    L.forEach(q => { if (!q.my) q.my = CALL; if (!q.grid && Q.grid) q.grid = Q.grid; });
    L.sort((a, b) => (a.d + a.tm).localeCompare(b.d + b.tm));
    const ok = await download(`KPC-hunting-log-${CALL || 'mine'}-${utc(new Date()).d}${onlyNew ? '-new' : ''}.adi`, adif(L));
    if (ok !== false) { L.forEach(q => q.x = 1); Q.x = Date.now(); qSave(); qList(); toast(`⬇ ${L.length} contact${L.length === 1 ? '' : 's'} ready for QRZ.`); }
  }
  $('lgAdif').onclick = () => exp(false); $('lgNew').onclick = () => exp(true);
  $('lgCsv').onclick = () => { const h = 'date_utc,time_utc,call,freq_mhz,band,mode,ref,name,state,rst_sent,rst_rcvd,note\n'; download(`KPC-hunting-log-${CALL || 'mine'}.csv`, h + Q.q.map(q => [fmtD(q.d), fmtT(q.tm), q.call, q.f, q.band, q.mode, q.ref, q.name, q.st, q.rs, q.rr, q.note].map(v => '"' + String(v || '').replace(/"/g, '""') + '"').join(',')).join('\n'), 'text/csv'); };
  $('lgLoad').onchange = async e => {
    const f = e.target.files[0]; e.target.value = ''; if (!f) return;
    const L = parseAdif(await f.text()); if (!L.length) { toast('No contacts found in that file.'); return; }
    const key = q => [base(q.call), q.d, q.tm, q.band, String(q.ref || '').replace(/\s/g, '')].join('|'), have = new Set(Q.q.map(key));
    const add = L.filter(q => !have.has(key(q))); Q.q = Q.q.concat(add);
    add.forEach(q => String(q.ref || '').split(/[ ,]+/).filter(Boolean).forEach(r => WK.add(r))); saveLog(); logInfo();
    await qSave(); qList(); toast(`↥ ${add.length} contact${add.length === 1 ? '' : 's'} added (${L.length - add.length} already in your log).`);
  };
  $('lgMy').onchange = () => { CALL = base($('lgMy').value); $('lgMy').value = CALL; $('hCall').value = CALL; put('kpcMyCall', CALL); myStats(); topDraw(); };
  $('lgGrid').onchange = () => { Q.grid = $('lgGrid').value.trim().toUpperCase().slice(0, 6); $('lgGrid').value = Q.grid; qSave(); };
  $('lgQ').oninput = () => qList();
  /* ---------- the list ---------- */
  let qShown = 100;
  function qList() {
    const q = $('lgQ').value.trim().toUpperCase();
    const L = Q.q.filter(x => !q || [x.call, x.ref, x.name, x.st, x.band, x.mode, x.note, fmtD(x.d)].join(' ').toUpperCase().includes(q)).sort((a, b) => (b.d + b.tm).localeCompare(a.d + a.tm));
    $('lgList').innerHTML = L.length ? `<table class="hl-logt"><thead><tr><th>UTC</th><th>CALL</th><th>FREQ</th><th>PARK / REF</th><th class="hide-s">RST</th><th></th></tr></thead><tbody>${L.slice(0, qShown).map(x => `<tr class="${x.x ? '' : 'nx'}"><td>${fmtD(x.d)}<br>${fmtT(x.tm)}</td><td class="c">${esc(x.call)}</td><td>${esc(x.f)}<br><small>${esc(x.band)} ${esc(x.mode)}</small></td><td class="r">${esc(x.ref)}<br><small style="color:var(--mu);font-family:Arial">${esc(x.name || '')}${x.st ? ' · ' + esc(x.st) : ''}</small></td><td class="hide-s">${esc(x.rs)} / ${esc(x.rr)}</td><td><button type="button" data-qe="${x.id}">EDIT</button><button type="button" data-qd="${x.id}">DELETE</button></td></tr>`).join('')}</tbody></table>${L.length > qShown ? '<div class="hl-row" style="padding:8px"><button type="button" class="hl-btn line sm" id="lgMore">SHOW MORE</button></div>' : ''}`
      : `<div class="hl-empty">${Q.q.length ? 'None match.' : 'No contacts logged on this device yet. Tap a spot card to log one.'}</div>`;
    const m = $('lgMore'); if (m) m.onclick = () => { qShown += 200; qList(); };
    dkList();
  }
  document.addEventListener('click', e => {
    const ed = e.target.closest('[data-qe]'); if (ed) { const x = Q.q.find(q => q.id === ed.dataset.qe); if (x) openSheet(null, x); return; }
    const dl = e.target.closest('[data-qd]'); if (dl) { const i = Q.q.findIndex(q => q.id === dl.dataset.qd); if (i < 0) return; const [x] = Q.q.splice(i, 1); qSave(); qList(); toast(`Deleted ${x.call}.`, () => { Q.q.splice(i, 0, x); qSave(); qList(); }); }
  });
  /* ---------- the log sheet ---------- */
  let EDIT = null;
  function rstFor(m) { m = String(m || '').toUpperCase(); return /^CW|RTTY/.test(m) ? '599' : /FT8|FT4|JS8|PSK/.test(m) ? '' : '59'; }
  function modePick(m) { m = String(m || '').toUpperCase(); if (/USB|LSB|SSB|PHONE/.test(m)) return 'SSB'; const o = [...$('fMode').options].map(x => x.value); return o.includes(m) ? m : (m ? 'OTHER' : 'SSB'); }
  function bandSet() { const f = parseFloat($('fFreq').value); $('fBand').value = f ? bandOf(f * 1000).replace('OTHER', '') : ''; dupe(); }
  function dupe() {
    const c = base($('fCall').value), r = $('fRef').value.toUpperCase().replace(/\s/g, ''), b = $('fBand').value, d = $('fDate').value.replace(/-/g, '');
    const hit = c && Q.q.find(q => q !== EDIT && base(q.call) === c && q.d === d && q.band === b && String(q.ref || '').replace(/\s/g, '') === r);
    $('fDupe').hidden = !hit; if (hit) $('fDupe').textContent = `⚠ You already logged ${c} at ${r || 'this spot'} on ${b} today (${fmtT(hit.tm)} UTC). Saving again makes a second copy.`;
  }
  function setNow() { const n = utc(new Date()); $('fDate').value = fmtD(n.d); $('fTime').value = fmtT(n.t); dupe(); }
  function openSheet(s, x) {
    if (PUB) return;
    if (!x && DOCKON()) { dkFill(s || {}); if (!DESKON()) dkGo(); return; }   /* members: the spot fills the log dock (left pane on computers, under the spots on phones) */
    EDIT = x || null;
    $('lgTitle').textContent = x ? '✏️ Edit this contact' : '📝 Log this contact';
    if (x) {
      $('fCall').value = x.call; $('fFreq').value = x.f; $('fMode').value = modePick(x.mode); $('fRef').value = x.ref; $('fName').value = x.name || ''; $('fDate').value = fmtD(x.d); $('fTime').value = fmtT(x.tm);
      $('fRs').value = x.rs || ''; $('fRr').value = x.rr || ''; $('fSt').value = x.st || ''; $('fNote').value = x.note || '';
    } else {
      s = s || {};
      $('fCall').value = s.call || ''; $('fFreq').value = s.khz ? (s.khz / 1000).toFixed(4).replace(/0+$/, '').replace(/\.$/, '') : ''; $('fMode').value = modePick(s.mode); $('fRef').value = s.ref || ''; $('fName').value = s.name || '';
      $('fRs').value = rstFor(s.mode); $('fRr').value = rstFor(s.mode); $('fSt').value = s.st || ''; $('fNote').value = ''; setNow();
    }
    bandSet(); $('lgSheet').classList.add('on');
    setTimeout(() => { (s && s.call ? $('fRs') : $('fCall')).focus({ preventScroll: true }); }, 250);
  }
  function closeSheet() { $('lgSheet').classList.remove('on'); EDIT = null; }
  $('lgX').onclick = closeSheet; $('fCancel').onclick = closeSheet; $('fNow').onclick = setNow;
  $('lgAdd').onclick = () => openSheet({});
  $('fFreq').oninput = bandSet; ['fCall', 'fRef', 'fDate'].forEach(id => $(id).addEventListener('input', dupe));
  $('fMode').onchange = () => { if (!EDIT) { $('fRs').value = rstFor($('fMode').value); $('fRr').value = rstFor($('fMode').value); } };
  $('lgForm').addEventListener('submit', async e => {
    e.preventDefault();
    const call = $('fCall').value.trim().toUpperCase(); if (!call) { $('fCall').focus(); return; }
    const ref = $('fRef').value.toUpperCase().split(/[ ,]+/).filter(Boolean).map(nref).join(', ');
    const rec = { id: EDIT ? EDIT.id : Date.now().toString(36) + Math.random().toString(36).slice(2, 6), call, d: $('fDate').value.replace(/-/g, ''), tm: $('fTime').value.replace(':', '').slice(0, 4),
      f: $('fFreq').value.trim(), band: $('fBand').value, mode: $('fMode').value, ref, name: $('fName').value.trim(), st: $('fSt').value.trim().toUpperCase(), rs: $('fRs').value.trim(), rr: $('fRr').value.trim(),
      note: $('fNote').value.trim(), my: CALL, grid: Q.grid, x: 0, t: Date.now() };
    if (!/^\d{8}$/.test(rec.d)) { const n = utc(new Date()); rec.d = n.d; rec.tm = n.t; }
    if (EDIT) { const i = Q.q.indexOf(EDIT); if (i >= 0) Q.q[i] = rec; else Q.q.push(rec); } else Q.q.push(rec);
    await qSave();
    ref.split(/[ ,]+/).filter(Boolean).forEach(r => { if (!WK.has(r)) { WK.add(r); MAN.add(r); } }); saveLog(); logInfo();
    const wasEdit = !!EDIT; closeSheet(); qList(); ticker(false); draw(); needDraw();
    toast(wasEdit ? '✓ Changes saved.' : `✓ ${call} saved on this device.`, wasEdit ? null : () => { Q.q = Q.q.filter(q => q.id !== rec.id); qSave(); qList(); });
  });
  let tT = 0;
  /* big box in the middle of the screen, so the POTA bookmark result can't be missed (a toast was too easy to miss on iPhone) */
  function bigNote(ok, html) {
    let d = document.getElementById('hlBig'); if (!d) { d = document.createElement('div'); d.id = 'hlBig'; d.setAttribute('role', 'alertdialog'); document.body.appendChild(d); }
    d.className = 'hl-big ' + (ok ? 'ok' : 'bad');
    d.innerHTML = `<div class="hl-bigbox"><div class="hl-bigic">${ok ? '✅' : '⚠️'}</div>${html}<button type="button">${ok ? 'SHOW ME THE SPOTS' : 'OK'}</button></div>`;
    d.hidden = false;
    d.querySelector('button').onclick = () => { d.hidden = true; if (ok) { const t = $('hlList') || $('hlTick'); if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' }); } };
  }
  function toast(msg, undo) {
    let t = document.querySelector('.hl-toast'); if (!t) { t = document.createElement('div'); t.className = 'hl-toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.innerHTML = esc(msg) + (undo ? '<button type="button">UNDO</button>' : ''); t.hidden = false;
    if (undo) t.querySelector('button').onclick = () => { undo(); t.hidden = true; };
    clearTimeout(tT); tT = setTimeout(() => { t.hidden = true; }, undo ? 7000 : 3500);
  }
  /* tapping a spot card (not its links/buttons) opens the log with everything filled in */
  document.addEventListener('click', e => {
    const lg = e.target.closest('[data-log]');
    const c = lg ? lg.closest('.hs, tr.hr') : (!e.target.closest('a,button,input,select,label') && e.target.closest('#hlSpots .hs, #hlSpots tr.hr'));
    if (!c || PUB) return; const s = SP.find(x => x.p + '|' + x.call + '|' + x.ref === c.dataset.k); if (s) openSheet(s);
  });


  /* ---------------- ⭐ bookmark: hunted parks straight from POTA (Brandon Oct 16) ----------------
     pota.app's own page loads them from api.pota.app/user/stats/hunted_activated_list?type=both with the signed-in
     Cognito idToken (localStorage CognitoIdentityServiceProvider.<client>.<user>.idToken) as the Authorization header
     (read from pota.app's web bundle Oct 16). The bookmark runs ON pota.app, makes that same call, and sends ONLY the
     park numbers back here in the address (#pota=US~1.2.17_CA~5), so the sign-in never leaves pota.app. */
  const HERE = location.origin + location.pathname;
  /* The bookmark is a tiny loader for kpc-pota-bm.js (that file holds the real code), so it is short enough for phones
     and never has to be copied again when the code changes. */
  const BMSRC = new URL('kpc-pota-bm.js', location.href).href.split('?')[0];
  const BM = `(function(){var s=document.createElement('script');s.src='${BMSRC}?t='+Date.now();s.onerror=function(){alert('KPC: could not load the bookmark code. Check your signal and try again.')};document.head.appendChild(s)})()`;
  const BMURL = 'javascript:' + encodeURI(BM);
  $('hBm').href = BMURL;
  $('hBm').onclick = e => { e.preventDefault(); toast('Drag this button to your bookmarks bar, then use it on pota.app.'); };
  /* which device steps to show: guessed from the device, can be switched */
  const DEV0 = /iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1) ? 'iphone' : /Android/.test(navigator.userAgent) ? 'android' : 'pc';
  function dev(d) { document.querySelectorAll('[data-devs]').forEach(o => o.hidden = o.dataset.devs !== d); document.querySelectorAll('[data-dev]').forEach(b => b.setAttribute('aria-pressed', b.dataset.dev === d)); }
  dev(DEV0);
  document.addEventListener('click', e => { const b = e.target.closest('[data-dev]'); if (b) dev(b.dataset.dev); });
  document.addEventListener('click', async e => { if (!e.target.closest('[data-bmcopy]')) return; try { await navigator.clipboard.writeText(BMURL); toast('✓ Copied. Now paste it as the bookmark’s web address.'); } catch (x) { prompt('Copy this, then paste it as the bookmark’s web address:', BMURL); } });
  async function fromPotaHash() {
    if (PUB) return;
    let m = location.hash.match(/[#&]pota=([^&]*)/), A = null;
    if (!m && /kpcpota/.test(location.hash)) {
      let P = null;
      const z = location.hash.match(/[#&]z=([A-Za-z0-9_-]+)/);
      if (z && window.DecompressionStream) {
        try {
          const b = atob(z[1].replace(/-/g, '+').replace(/_/g, '/')), u = new Uint8Array(b.length);
          for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i);
          P = JSON.parse(await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text());
        } catch (e) { P = null; }
      }
      if (!P && String(window.name).startsWith('KPCPOTA:')) { try { P = JSON.parse(window.name.slice(8)); } catch (e) {} }
      window.name = '';
      if (!P) { try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {} bigNote(false, '<h3>The park list from POTA didn’t come through</h3><p>Go back to pota.app, make sure you are signed in, wait until the page has fully loaded, then tap the ⭐ bookmark again. If it still fails, send Brandon a screenshot of this box.</p>'); return; }
      m = [0, P.refs]; A = P.aw;
    }
    if (!m) return;
    if (!A) { const a = location.hash.match(/[#&]aw=([^&]*)/); if (a) try { A = JSON.parse(decodeURIComponent(a[1])); } catch (e) {} }
    if (A) {
      try {
        if (A.pc || A.ac || A.n1) { put('kpcHuntCounts', { t: A.t || Date.now(), pc: A.pc || {}, ac: A.ac || {}, n1: A.n1 || {} }); CNT = get('kpcHuntCounts', null); delete A.pc; delete A.ac; delete A.n1; }
        put('kpcHuntAwards', A);
        if (A.call && !CALL) { CALL = base(A.call); put('kpcMyCall', CALL); $('hCall').value = CALL; $('lgMy').value = CALL; }
      } catch (e) {}
    }
    const got = new Set();
    decodeURIComponent(m[1]).split('_').forEach(grp => { const [pre, nums] = grp.split('~'); if (!pre || !nums) return; nums.split('.').forEach(n => { if (/^\d+$/.test(n)) got.add(nref(pre + '-' + n.padStart(4, '0'))); }); });
    try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {}
    if (!got.size) { $('hMsg').className = 'hl-msg bad'; $('hMsg').textContent = 'POTA sent back no hunted parks. Are you signed in with the right call?'; bigNote(false, '<h3>POTA sent back 0 hunted parks</h3><p>Are you signed in to pota.app with the right call sign? Sign in, let the page load, then tap the ⭐ bookmark again.</p>'); return; }
    const keep = [...WK].filter(r => progOf(r) !== 'POTA');      // WWFF / SOTA you loaded stay
    WK = new Set(keep.concat([...MAN]).concat([...got]));
    LOG.t = Date.now(); LOG.file = 'POTA (' + got.size + ' hunted parks)'; saveLog(); logInfo(); ticker(false); draw(); needDraw();
    try { window.scrollTo(0, 0); } catch (e) {}
    const st = new Set([...got].map(r => r.split('-')[0])).size;
    bigNote(true, `<h3>${got.size.toLocaleString()} hunted parks loaded from POTA</h3><p>${A && A.call ? 'For <b>' + esc(base(A.call)) + '</b>. ' : ''}From ${st} countr${st === 1 ? 'y' : 'ies'}. They are saved on this device, so parks you've already hunted drop out of the spots and only new ones light up.${CNT ? ' Your park and operator counts came over too (the 🔁 and 🤝 numbers on each spot).' : ''}</p><p class="s">Hunt more parks? Tap the ⭐ bookmark on pota.app again any time to refresh.</p>`);
  }

  /* ---------------- 🏅 my POTA awards (brought over by the ⭐ bookmark; kept in localStorage kpcHuntAwards) ---------------- */
  const FE = [0, 10, 20, 30, 40, 50, 75, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000, 10500, 11000, 11500, 12000, 12500, 13000, 13500, 14000, 14500, 15000];
  const numOf = (o, ...k) => { if (o == null) return null; if (typeof o === 'number') return o; for (const x of k) if (o[x] != null && isFinite(+o[x])) return +o[x]; const v = Object.values(o).find(v => typeof v === 'number'); return v ?? null; };
  const nextOf = (v, step) => Array.isArray(step) ? (step.find(x => x > v) ?? v) : (Math.floor(v / step) + 1) * step;
  const prevOf = (v, step) => Array.isArray(step) ? Math.max(0, ...step.filter(x => x <= v)) : Math.floor(v / step) * step;
  function tile(lbl, v, step, unit) {
    if (v == null) return '';
    const n = nextOf(v, step), p0 = prevOf(v, step), pct = n > p0 ? Math.round((v - p0) / (n - p0) * 100) : 100;
    return `<div class="aw-t"><b>${v.toLocaleString()}</b><span>${lbl}</span><div class="bar"><i style="width:${pct}%"></i></div><small>${n > v ? `${(n - v).toLocaleString()} more ${unit} to ${n.toLocaleString()}` : 'top level'}</small></div>`;
  }
  const AWL = {
    'hunter/op2op': ['🤝 Hunter Operator to Operator', 'Work the same activator 50 times; every 50 more is a new level', 'contacts', 50, 'activator'],
    'activator/op2op': ['🤝 Activator Operator to Operator', 'Work the same hunter 50 times from parks', 'contacts', 50, 'hunter'],
    'hunter/repeatoffender': ['🔁 Repeat Offender (hunter)', 'Hunt a park 20 times; every 20 more contacts is a new level', 'contacts', 20, 'park'],
    'activator/repeatoffender': ['🔁 Repeat Offender (activator)', 'Activate a park 20 times', 'activations', 20, 'park'],
    'hunter/n1ccmultiband': ['📶 N1CC (hunter)', '10 different parks on 10 different bands', 'bands', 10, 'park'],
    'activator/n1ccmultiband': ['📶 N1CC (activator)', '10 parks activated on 10 bands', 'bands', 10, 'park'],
    'hunter/sixpack': ['6️⃣ Six Pack (hunter)', 'Contacts with 6 different parks on 6 m', 'contacts', 0, 'park'],
    'activator/sixpack': ['6️⃣ Six Pack (activator)', '10 contacts at 6 different parks on 6 m', 'contacts', 10, 'park'],
    'activator/kilos': ['🏆 Kilo (activator)', '1,000 contacts from one park', 'contacts', 1000, 'park']
  };
  function awList(k, d) {
    const [title, desc, field, step, kind] = AWL[k]; const L = (d && d.top) || []; if (!L.length) return '';
    const rows = L.slice(0, 8).map(x => {
      const who = x.callsign || x.operatorCallsign || x.hunter || x.activator || x.reference || x.park || '?';
      const sub = x.name || x.parkName || x.locationDesc || '';
      const v = +(x[field] ?? x.contacts ?? x.activations ?? x.bands ?? 0);
      const nx = step ? nextOf(v, step) : null;
      const link = kind === 'park' ? `https://pota.app/#/park/${encodeURIComponent(who)}` : `https://www.qrz.com/db/${encodeURIComponent(base(who))}`;
      return `<div class="aw-r"><a href="${link}" target="_blank" rel="noopener">${esc(who)}</a><span class="s">${esc(sub)}${x.bandlist ? ' · ' + esc(String(x.bandlist).split(',').join(' ')) : ''}</span><span class="v">${v.toLocaleString()}${nx ? ` <small>/ ${nx.toLocaleString()}</small>` : ''}</span></div>`;
    }).join('');
    return `<div class="aw-c"><h4>${title}</h4><p>${desc}${d.total ? ` · ${(+d.total).toLocaleString()} in progress` : ''}. Closest to the next level:</p>${rows}</div>`;
  }
  function awDraw() { try { awDraw0(); } catch (e) { console.error('awards', e); const b = $('awBox'); if (b) b.innerHTML = '<div class="hl-empty">Your awards came over, but KPC couldn’t read part of them (' + esc(e.message) + '). Send Brandon a screenshot.</div>'; } }
  function awDraw0() {
    const box = $('awBox'); if (!box) return; const A = get('kpcHuntAwards', null); if (!A || !A.t) return;
    const n = (k, ...f) => numOf(A[k], ...f);
    const tiles = [tile('PARKS HUNTED', n('hunter/parks', 'numParks', 'parks'), FE, 'parks'), tile('PARKS ACTIVATED', n('activator/parks', 'numParks', 'parks'), FE, 'parks'),
      tile('DX ENTITIES HUNTED', n('hunter/dxentity', 'numEntities'), 5, 'entities'), tile('DX ENTITIES ACTIVATED', n('activator/dxentity', 'numEntities'), 5, 'entities'),
      tile('PARK TO PARK', n('activator/p2p', 'contacts'), 25, 'contacts'), tile('EARLY SHIFT HUNTER', n('hunter/earlyshift', 'contacts'), 100, 'contacts'), tile('LATE SHIFT HUNTER', n('hunter/lateshift', 'contacts'), 100, 'contacts'),
      tile('EARLY SHIFT ACTIVATOR', n('activator/earlyshift', 'contacts'), 100, 'contacts'), tile('LATE SHIFT ACTIVATOR', n('activator/lateshift', 'contacts'), 100, 'contacts')].join('');
    let was = '';
    if (A.loc) {
      const got = Object.keys(ST).filter(a => a !== 'DC' && A.loc['US-' + a]), miss = Object.keys(ST).filter(a => a !== 'DC' && !A.loc['US-' + a]);
      was = `<div class="aw-c"><h4>🗺 Worked All States (parks hunted)</h4><p><b>${got.length} of 50</b> states${miss.length ? '. Still needed: ' + miss.map(a => `<a href="#hlNeed" data-need="${a}">${a}</a>`).join(' ') : ': all 50! 🎉'}</p>
        <p>${Object.keys(A.loc).filter(l => !/^US-/.test(l)).length} other locations (provinces / countries) hunted.</p></div>`;
    }
    const E = A.earned || [], g = {};
    E.forEach(e => { g[e[0]] = (g[e[0]] || 0) + 1; });
    const rec = E.slice().sort((a, b) => String(b[1]).localeCompare(String(a[1]))).slice(0, 8);
    const earned = E.length ? `<div class="aw-c"><h4>🎖 Achievements earned: ${E.length.toLocaleString()}</h4><p>${Object.entries(g).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([k, v]) => `${esc(k)} <b>${v}</b>`).join(' · ')}</p><p><b>Newest:</b></p>${rec.map(e => `<div class="aw-r"><span>${esc(e[0])}${e[3] ? ' · ' + esc(e[3]) : ''}${e[4] ? ' · ' + esc(e[4]) : ''}</span><span class="v"><small>${esc(String(e[1] || '').slice(0, 10))}</small></span></div>`).join('')}</div>` : '';
    box.innerHTML = `<div class="aw-g">${tiles}</div><div class="aw-cols">${was}${earned}${Object.keys(AWL).map(k => awList(k, A[k])).join('')}</div>
      <p class="hl-src">From POTA for ${esc(A.call || CALL || 'you')}, brought over ${new Date(A.t).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}. POTA updates achievements once a day, and hunters get credit only after the activator's log is in. Tap the ⭐ bookmark on pota.app again to refresh. <a href="https://pota.app/#/user/achievements/progress" target="_blank" rel="noopener">POTA ACHIEVEMENTS ↗</a></p>`;
  }
  document.addEventListener('click', e => { const a = e.target.closest('[data-need]'); if (!a) return; e.preventDefault(); if (PAGE !== 'need' && !PUB) { location.href = 'kpc-hunt-need.html?st=' + encodeURIComponent(a.dataset.need); return; } $('nSt').value = a.dataset.need; $('nSt').dataset.set = 1; needLoad(); $('hlNeed').scrollIntoView({ behavior: 'smooth' }); });

  /* ---------------- the real map (Leaflet + Esri satellite + place names) ---------------- */
  let LM = null, LG = null, LMV = get('kpcHuntMz', 'na');
  const MZ = { na: [[15, -168], [70, -52]], us: [[24.5, -125], [49.5, -66.5]] };
  function lmZoom(z) { if (!LM) return; LMV = z; put('kpcHuntMz', z); if (z === 'world') LM.setView([25, -20], 2); else LM.fitBounds(MZ[z] || MZ.na); document.querySelectorAll('[data-mz]').forEach(b => b.setAttribute('aria-pressed', b.dataset.mz === z)); }
  function lmInit() {
    if (LM || !window.L || !$('hlLmap')) return;
    LM = L.map('hlLmap', { worldCopyJump: true, zoomSnap: .5, minZoom: 2 });
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 17, attribution: 'Imagery © Esri, Maxar, Earthstar Geographics' }).addTo(LM);
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 17, opacity: .9 }).addTo(LM);
    LG = L.layerGroup().addTo(LM); lmZoom(LMV);
  }
  const NEWICON = () => L.divIcon({ className: 'hl-pin', html: '<span></span>', iconSize: [22, 22], iconAnchor: [11, 11] });
  function lmDraw() {
    lmInit(); if (!LM) return; LG.clearLayers();
    SP.filter(s => isFinite(s.la) && isFinite(s.lo) && passPBM(s)).sort((a, b) => isNew(a) - isNew(b)).forEach(s => {
      const k = keyOf(s), n = isNew(s), w = !!s.ref && WK.has(s.ref);
      const pop = `<div class="hl-pop"><b>${esc(s.call)}</b> <span class="f">${(s.khz / 1000).toFixed(3)}</span> ${esc(s.mode || '')}<br>${s.ref ? `<span class="r">${esc(s.ref)}</span> ` : ''}${esc(s.name || '')}${n ? '<br><span class="pn">✨ NEW TO YOU</span>' : w ? '<br><span class="pw">✓ hunted</span>' : ''}${awardChips(s) ? '<br>' + awardChips(s) : ''}<div class="hl-popb"><button type="button" data-logk="${esc(k)}">📝 LOG IT</button><button type="button" data-dk="${esc(k)}">SHOW SPOT</button></div></div>`;
      const m = n ? L.marker([s.la, s.lo], { icon: NEWICON(), zIndexOffset: 1000 }) : L.circleMarker([s.la, s.lo], { radius: w ? 5 : 4.5, color: '#111', weight: 1, fillColor: w ? '#f0c96b' : '#cfd6d1', fillOpacity: .9 });
      m.bindPopup(pop, { maxWidth: 260 }).addTo(LG);
    });
  }
  document.addEventListener('click', e => {
    const z = e.target.closest('[data-mz]'); if (z) { lmZoom(z.dataset.mz); return; }
    const lk = e.target.closest('[data-logk]'); if (lk) { const s = SP.find(x => keyOf(x) === lk.dataset.logk); if (s) openSheet(s); return; }
    const c = e.target.closest('.hl-pop [data-dk], #hlBigSvg [data-dk]'); if (!c) return;
    let el = document.querySelector(`#hlSpots [data-k="${CSS.escape(c.dataset.dk)}"]`);
    if (!el) { F.hide = false; F.nw = false; F.q = ''; saveF(); chips(); draw(); el = document.querySelector(`#hlSpots [data-k="${CSS.escape(c.dataset.dk)}"]`); }
    if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.classList.remove('fresh'); void el.offsetWidth; el.classList.add('fresh'); }
  });

  /* ---------------- 🔥 flames up from the bottom when a new park shows up (Brandon Oct 16) ---------------- */
  let FX = get('kpcHuntFx', get('kpcHuntFlame', true) === false ? 'off' : 'flames'), fireT = 0; const FLAME = true;
  const FXL = { flames: ['🔥', 'FLAMES'], fireworks: ['🎆', 'FIREWORKS'], stars: ['🌠', 'SHOOTING STARS'], off: ['🚫', 'NO EFFECTS'] };
  function flameBtn() { const b = $('hlFlame'), f = FXL[FX] || FXL.flames; const dk = document.getElementById('hlDk'); if (dk) dk.dataset.fx = FX; b.setAttribute('aria-pressed', FX !== 'off'); b.dataset.fx = FX; b.innerHTML = f[0] + '<span class="t"> ' + f[1] + '</span>'; }
  $('hlFlame').onclick = () => { FX = FX === 'flames' ? 'fireworks' : FX === 'fireworks' ? 'stars' : FX === 'stars' ? 'off' : 'flames'; put('kpcHuntFx', FX); flameBtn(); if (FX !== 'off') fire(FX === 'flames' ? '🔥 Flames for new parks' : FX === 'fireworks' ? '🎆 Fireworks for new parks' : '🌠 Shooting stars for new parks'); else toast('No screen effects for new parks.'); };
  function fire(msg) {
    if (PAGE === 'need') return;
    if (FX === 'off' || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (FX === 'fireworks') return fireworks(msg);
    if (FX === 'stars') return shootingStars(msg);
    const cv = $('hlFire'), cx = cv.getContext('2d'), W = cv.width = innerWidth, H = cv.height = Math.round(innerHeight * .55); cv.style.height = '';
    const P = [], t0 = performance.now(), DUR = 3800;
    if (msg) { const m = $('hlFireMsg'); m.textContent = msg; m.classList.remove('on'); void m.offsetWidth; m.classList.add('on'); }
    cv.classList.add('on'); cancelAnimationFrame(fireT);
    const step = now => {
      const el = now - t0, live = el < DUR - 900;
      for (let i = 0; live && i < Math.max(14, W / 26); i++) P.push({ x: Math.random() * W, y: H + 10, vx: (Math.random() - .5) * .9, vy: -(2.2 + Math.random() * 4.2), r: 10 + Math.random() * 26, life: 0, max: 50 + Math.random() * 45 });
      cx.clearRect(0, 0, W, H); cx.globalCompositeOperation = 'lighter';
      for (let i = P.length - 1; i >= 0; i--) {
        const p = P[i]; p.life++; p.x += p.vx + Math.sin((p.life + i) / 6) * .6; p.y += p.vy; p.r *= .985;
        const k = p.life / p.max; if (k >= 1) { P.splice(i, 1); continue; }
        const g = cx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
        g.addColorStop(0, `rgba(255,${Math.round(230 - 150 * k)},${Math.round(120 - 110 * k)},${.75 * (1 - k)})`); g.addColorStop(.5, `rgba(255,${Math.round(110 - 80 * k)},0,${.45 * (1 - k)})`); g.addColorStop(1, 'rgba(120,10,0,0)');
        cx.fillStyle = g; cx.beginPath(); cx.arc(p.x, p.y, p.r, 0, 6.283); cx.fill();
      }
      if (el < DUR || P.length) fireT = requestAnimationFrame(step); else { cv.classList.remove('on'); cx.clearRect(0, 0, W, H); }
    };
    fireT = requestAnimationFrame(step);
  }
  /* 🌠 shooting stars: bright streaks with glowing tails race across the screen from the top */
  function shootingStars(msg) {
    const cv = $('hlFire'), cx = cv.getContext('2d'), W = cv.width = innerWidth, H = cv.height = innerHeight;
    cv.style.height = '100vh';
    if (msg) { const m = $('hlFireMsg'); m.textContent = msg.replace(/^🔥/, '🌠'); m.classList.remove('on'); void m.offsetWidth; m.classList.add('on'); }
    cv.classList.add('on'); cancelAnimationFrame(fireT);
    const S = [], SP2 = [], t0 = performance.now(), DUR = 4200; let made = 0;
    for (let i = 0; i < 70; i++) SP2.push({ x: Math.random() * W, y: Math.random() * H * .7, r: Math.random() * 1.3 + .3, p: Math.random() * 6.28 });
    const step = now => {
      const el = now - t0;
      if (el < DUR - 1200 && made < Math.round(el / 230) + 1) { made++; const a = (20 + Math.random() * 25) * Math.PI / 180, v = 14 + Math.random() * 12, left = Math.random() < .5;
        S.push({ x: left ? -40 + Math.random() * W * .5 : W * .5 + Math.random() * W * .5, y: -20 + Math.random() * H * .35, vx: (left ? 1 : -1) * Math.cos(a) * v, vy: Math.sin(a) * v, life: 0, max: 45 + Math.random() * 30, len: 14 + Math.random() * 10 }); }
      cx.clearRect(0, 0, W, H);
      const fade = Math.max(0, Math.min(1, el / 400, (DUR - el) / 600));
      SP2.forEach(st => { cx.globalAlpha = fade * (.35 + .35 * Math.sin(el / 300 + st.p)); cx.fillStyle = '#fff'; cx.beginPath(); cx.arc(st.x, st.y, st.r, 0, 6.283); cx.fill(); });
      cx.globalAlpha = 1;
      for (let i = S.length - 1; i >= 0; i--) {
        const s = S[i]; s.life++; s.x += s.vx; s.y += s.vy; const k = s.life / s.max;
        if (k >= 1) { S.splice(i, 1); continue; }
        const tx = s.x - s.vx * s.len, ty = s.y - s.vy * s.len, g = cx.createLinearGradient(s.x, s.y, tx, ty);
        g.addColorStop(0, `rgba(255,255,255,${1 - k})`); g.addColorStop(.25, `rgba(180,215,255,${.7 * (1 - k)})`); g.addColorStop(1, 'rgba(120,160,255,0)');
        cx.strokeStyle = g; cx.lineWidth = 3; cx.lineCap = 'round'; cx.beginPath(); cx.moveTo(s.x, s.y); cx.lineTo(tx, ty); cx.stroke();
        cx.fillStyle = `rgba(255,255,255,${1 - k})`; cx.shadowColor = '#bcd6ff'; cx.shadowBlur = 14; cx.beginPath(); cx.arc(s.x, s.y, 2.6, 0, 6.283); cx.fill(); cx.shadowBlur = 0;
      }
      if (el < DUR || S.length) fireT = requestAnimationFrame(step); else { cv.classList.remove('on'); cx.clearRect(0, 0, W, H); cv.style.height = ''; }
    };
    fireT = requestAnimationFrame(step);
  }
  /* 🎆 fireworks: rockets climb from the bottom and burst into colour */
  function fireworks(msg) {
    const cv = $('hlFire'), cx = cv.getContext('2d'), W = cv.width = innerWidth, H = cv.height = innerHeight;
    cv.style.height = '100vh';
    if (msg) { const m = $('hlFireMsg'); m.textContent = msg.replace(/^🔥/, '🎆'); m.classList.remove('on'); void m.offsetWidth; m.classList.add('on'); }
    cv.classList.add('on'); cancelAnimationFrame(fireT);
    const R = [], P = [], t0 = performance.now(), DUR = 4200, COL = ['#ffd76a', '#ff6b5a', '#3ddc84', '#8fb7ff', '#ff6fa8', '#ffffff', '#c08bff'];
    let launched = 0;
    const step = now => {
      const el = now - t0;
      if (el < DUR - 1400 && launched < Math.round(el / 260) + 1) { launched++; R.push({ x: W * (.12 + Math.random() * .76), y: H + 5, vy: -(H / 75 + Math.random() * H / 140), tY: H * (.18 + Math.random() * .3), c: COL[Math.floor(Math.random() * COL.length)] }); }
      cx.globalCompositeOperation = 'destination-out'; cx.fillStyle = 'rgba(0,0,0,.28)'; cx.fillRect(0, 0, W, H); cx.globalCompositeOperation = 'lighter';
      for (let i = R.length - 1; i >= 0; i--) {
        const r = R[i]; r.y += r.vy; r.vy *= .985;
        cx.fillStyle = r.c; cx.beginPath(); cx.arc(r.x, r.y, 2.4, 0, 6.283); cx.fill();
        if (r.y <= r.tY || r.vy > -1.5) { R.splice(i, 1); const k = 70 + Math.random() * 50; for (let j = 0; j < k; j++) { const a = Math.random() * 6.283, v = 1.5 + Math.random() * 5.5; P.push({ x: r.x, y: r.y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0, max: 50 + Math.random() * 35, c: Math.random() < .2 ? '#fff' : r.c }); } }
      }
      for (let i = P.length - 1; i >= 0; i--) {
        const p = P[i]; p.life++; p.x += p.vx; p.y += p.vy; p.vx *= .97; p.vy = p.vy * .97 + .06;
        const k = p.life / p.max; if (k >= 1) { P.splice(i, 1); continue; }
        cx.globalAlpha = 1 - k; cx.fillStyle = p.c; cx.beginPath(); cx.arc(p.x, p.y, 2.2 * (1 - k * .6), 0, 6.283); cx.fill(); cx.globalAlpha = 1;
      }
      if (el < DUR || P.length || R.length) fireT = requestAnimationFrame(step); else { cv.classList.remove('on'); cx.clearRect(0, 0, W, H); cv.style.height = ''; }
    };
    fireT = requestAnimationFrame(step);
  }
  /* ---------------- looks (Brandon Oct 16: switchable themes; Cabin Lodge = his pictures) ---------------- */
  let THEME = get('kpcHuntTheme', null) || 'lodge';
  function theme() { $('hl').dataset.theme = THEME; if (window.__hlAmb) { __hlAmb.hidden = THEME !== 'lodge'; if (THEME !== 'lodge' && __hlAmb.kOff) __hlAmb.kOff(); } document.querySelectorAll('[data-theme-pick]').forEach(b => b.setAttribute('aria-pressed', b.dataset.themePick === THEME)); }
  document.addEventListener('click', e => { const b = e.target.closest('[data-theme-pick]'); if (!b) return; THEME = b.dataset.themePick; put('kpcHuntTheme', THEME); theme(); });
  /* campfire crackle (+ crickets after dark) for the Cabin Lodge look (Brandon Oct 17); off until tapped */
  try { if (window.KPCAmbient && $('hlFlame')) { window.__hlAmb = KPCAmbient.button($('hlFlame').parentNode, 'fire', { cls: 'hl-bell hl-amb', when: () => THEME === 'lodge' }); $('hlFlame').parentNode.insertBefore(__hlAmb, $('hlFlame')); } } catch (e) {}
  theme();

  /* ---------------- mini North America map in the ticker ---------------- */
  const NA = {"124":"M171 122L178 123L181 128L185 129L187 133L179 131L181 129L178 130L174 128L173 125L170 125L168 123L170 122L167 122ZM160 96L160 94L153 92L139 76L130 80L123 75L124 73L116 73L116 27L123 27L139 32L136 30L138 30L137 28L144 27L143 29L162 24L148 29L146 31L150 31L150 29L165 26L169 24L167 23L169 22L176 28L179 28L182 24L184 27L182 28L195 26L207 30L222 31L224 34L219 34L219 36L244 36L250 43L249 40L251 41L251 39L248 36L257 32L251 34L245 34L247 32L256 30L262 35L266 34L274 37L286 35L291 37L291 35L286 35L285 33L289 32L294 33L293 35L296 34L295 39L297 38L298 40L294 40L297 42L296 40L299 40L297 36L306 32L305 30L302 31L303 28L306 28L296 26L294 19L302 15L314 24L310 24L312 25L308 27L318 27L315 29L318 30L319 34L321 30L327 30L329 33L327 33L327 36L330 39L334 38L338 31L341 31L338 29L338 26L355 29L352 30L355 32L350 33L355 38L354 40L347 43L340 40L345 44L333 42L336 45L332 48L314 45L332 49L328 54L320 54L319 57L305 54L306 56L315 57L317 60L310 61L312 62L310 62L310 64L307 63L308 65L306 65L301 72L300 80L303 81L303 84L304 81L307 81L310 88L309 90L319 89L337 97L339 100L344 98L350 99L353 114L358 117L357 119L359 118L363 121L361 118L365 118L366 112L361 102L369 99L374 94L373 87L366 82L366 80L371 77L370 71L367 71L370 67L367 64L370 62L377 64L387 63L389 66L394 67L394 69L402 70L402 74L397 75L401 75L401 78L403 78L400 82L405 80L407 82L407 84L404 85L407 85L407 83L409 83L409 85L414 81L416 83L421 73L421 75L426 78L424 80L429 82L426 83L430 83L427 85L432 85L430 88L435 90L435 92L430 91L433 92L434 95L439 96L438 100L441 98L441 101L444 99L450 102L438 107L439 109L447 104L450 104L451 108L453 106L457 108L457 112L455 112L457 112L457 114L454 117L446 118L440 124L414 124L402 134L396 133L401 135L394 142L383 147L384 148L375 153L373 157L364 157L364 161L349 167L347 164L351 159L350 148L347 147L346 144L344 145L344 142L342 143L340 140L326 133L324 135L314 135L301 131L301 128L299 128L299 130L188 130L187 127L184 128L184 126L186 127L184 126L185 124L184 126L180 124L181 121L176 123L174 122L176 121L174 122L174 120L169 119L173 117L171 116L169 118L169 114L173 114L171 113L172 111L168 116L167 115L168 110L166 111L166 109L163 108L165 106L164 107L168 109L165 105L162 109L159 107L160 104L162 104L158 103L162 98L161 97L160 100ZM218 -12L215 -11L217 -10L215 -10L216 -8L212 -8L211 -6L208 -7L209 -9L205 -8L205 -6L202 -7L200 -4L197 -6L188 -6L204 -12ZM247 -5L252 -3L253 -5L258 -5L256 0L230 3L223 1L236 -1L225 0L226 -2L224 -2L222 0L215 0L210 -2L220 -3L211 -3L220 -4L213 -5L221 -6L217 -6L221 -8L235 -3L244 -3L239 -7L246 -9ZM222 12L230 10L235 11L233 14L239 12L237 10L240 10L244 11L249 17L251 16L248 13L248 8L258 10L263 18L262 20L276 24L276 27L266 27L268 29L272 28L273 30L264 31L253 28L242 32L227 33L225 29L214 28L211 24L233 24L206 20L219 18L207 18L209 17L204 16L207 12L221 8L224 9ZM201 4L212 4L218 8L203 12L196 18L187 19L177 15L185 6L181 3L195 2ZM402 -40L414 -40L407 -38L420 -40L435 -36L405 -31L421 -32L402 -27L397 -28L399 -26L392 -26L397 -26L396 -24L381 -24L386 -24L386 -22L372 -23L382 -20L366 -20L382 -18L374 -18L379 -17L377 -15L368 -15L367 -12L360 -11L353 -13L355 -12L352 -11L363 -11L368 -8L356 -6L350 -9L351 -7L326 -7L326 -9L326 -7L322 -7L322 -9L326 -11L333 -11L328 -14L346 -12L350 -15L341 -12L338 -15L342 -16L340 -16L341 -18L335 -15L336 -17L330 -16L333 -19L353 -20L342 -20L346 -20L334 -24L335 -27L360 -23L348 -27L373 -29L365 -30L372 -32L356 -28L334 -28L347 -31L328 -28L323 -30L340 -31L321 -30L323 -31L321 -32L330 -33L318 -32L321 -33L314 -34L340 -35L334 -36L338 -37L362 -34L350 -37L357 -38L355 -39L365 -38L359 -40L374 -38L378 -38L371 -40ZM280 5L292 6L286 10L294 11L294 16L286 16L287 18L281 16L269 11L279 11L278 9L281 9L274 7L278 8L276 6ZM340 49L343 48L351 51L353 53L352 55L358 55L356 58L348 54L346 55L341 59L338 59L337 56L331 57L335 55L336 46L338 45ZM289 -7L290 -4L288 -4L291 -2L289 -3L288 0L279 0L277 -2L283 -3L269 -3L276 -4L272 -7L279 -5L282 -6L278 -6L280 -7L277 -8ZM266 -22L270 -19L276 -20L282 -18L283 -14L270 -16L260 -17L267 -19L260 -19L258 -22ZM312 -31L317 -28L323 -28L323 -26L329 -27L328 -25L332 -25L331 -23L338 -23L340 -21L330 -18L327 -20L328 -17L325 -18L325 -16L320 -18L322 -16L312 -16L309 -17L313 -18L306 -19L303 -20L315 -22L300 -21L297 -23L302 -24L297 -23L293 -26L302 -25L295 -26L298 -27L296 -27L296 -29L304 -28L298 -29L307 -30L303 -32ZM303 -10L307 -9L306 -7L323 -7L314 -6L321 -5L323 -4L321 -3L324 -2L343 -4L360 -3L359 -2L362 -1L358 0L362 1L359 0L359 2L352 3L346 0L346 2L337 3L326 3L327 1L313 2L312 -1L310 -1L312 -4L308 -7L299 -6L292 -9ZM307 4L319 6L312 11L303 11L306 13L299 15L297 7L301 7L299 5L302 4ZM412 149L409 147L409 140L403 138L397 149L381 150L386 148L391 142L398 140L406 132L414 129L423 130L423 133L413 135L417 135L417 137L421 136L420 138L419 140L421 140L422 144L435 147L436 149L427 151L426 153L423 152L419 157L415 156L417 152L415 153L422 148L423 150L427 148L420 148L423 146L421 145L419 148ZM458 117L453 127L455 124L458 125L455 127L459 127L459 130L462 127L466 128L463 131L465 131L464 133L468 132L465 137L469 134L467 136L467 138L469 136L468 142L466 142L466 140L463 141L464 136L458 141L456 140L461 137L443 137L447 132L443 132L448 130L447 128L449 128L450 122L453 118ZM334 20L341 20L341 17L336 15L343 15L337 12L338 10L343 11L338 9L349 6L358 9L359 11L355 13L358 13L356 15L363 13L366 16L365 13L370 14L366 12L372 11L380 13L376 16L380 14L383 15L379 16L381 17L380 19L384 16L383 18L386 17L387 19L387 17L393 17L395 19L389 21L397 19L396 22L392 23L395 22L394 24L398 21L404 21L407 23L400 25L407 25L408 23L411 25L403 27L413 29L403 31L413 33L412 35L415 34L414 36L418 35L418 37L421 35L425 37L421 38L428 39L425 41L433 40L435 42L430 43L432 45L429 47L426 46L426 50L418 46L422 43L416 45L411 42L408 43L411 45L405 44L411 47L413 51L415 50L420 53L418 54L422 56L422 59L419 56L421 61L419 60L419 62L409 56L409 58L404 56L414 62L416 66L395 60L392 58L394 57L387 54L387 52L384 53L380 51L381 53L371 54L367 52L370 48L377 49L378 51L377 48L386 48L382 44L391 38L387 33L384 33L385 31L382 32L378 30L374 32L377 28L371 27L373 26L364 22L362 23L365 24L363 26L325 23L322 20L331 20L320 17L323 9L329 6L340 6L333 11L335 16L340 18ZM362 7L375 9L376 11L369 11L360 11L357 6Z","304":"M480 63L480 60L478 61L474 57L474 55L479 54L473 54L475 52L480 53L480 51L476 49L477 51L472 54L470 48L476 46L470 48L466 45L475 41L465 44L470 40L464 39L469 36L478 37L465 37L467 34L474 35L475 33L466 34L470 31L476 32L475 30L479 29L476 29L479 25L463 23L462 21L477 23L473 20L476 20L468 19L469 17L473 17L466 17L467 15L465 13L466 16L464 18L458 18L457 16L461 13L457 14L458 12L460 13L461 10L457 10L459 8L457 8L455 4L451 4L455 2L447 -1L445 -4L428 -7L407 -5L402 -7L408 -8L395 -10L405 -12L415 -11L415 -13L403 -12L389 -16L390 -18L418 -21L423 -26L412 -25L412 -27L421 -30L428 -29L427 -31L435 -31L435 -34L438 -35L454 -32L443 -35L463 -37L466 -33L468 -37L476 -34L479 -35L476 -37L480 -37Z","484":"M211 212L221 211L234 218L254 216L266 230L268 230L270 226L274 226L282 237L283 242L291 245L289 253L289 264L291 268L289 265L289 267L297 282L299 281L303 284L312 281L314 283L319 269L332 267L333 271L329 277L329 284L327 281L323 286L316 286L316 289L314 289L318 295L313 295L311 302L304 294L301 294L294 297L276 289L273 285L269 285L260 278L257 273L259 272L257 262L250 252L242 246L243 243L244 244L243 242L233 233L229 226L228 219L225 217L220 215L221 224L229 233L232 241L234 241L237 253L242 257L240 261L239 257L231 250L232 246L227 240L225 241L220 236L224 237L224 233L217 226Z","840":"M160 96L158 101L156 100L156 95L151 97L154 94L146 89L145 87L148 87L144 85L144 82L143 84L141 83L139 78L140 84L136 83L136 80L132 80L136 82L133 84L122 78L122 75L123 77L122 75L115 76L115 74L103 75L101 72L94 72L93 70L95 69L89 71L88 69L86 70L87 72L85 73L88 72L86 75L82 74L82 76L72 79L76 76L73 76L75 71L84 71L80 69L83 68L82 67L73 70L68 74L69 76L63 79L67 80L66 82L46 93L46 95L37 98L33 97L27 101L31 96L39 96L39 93L45 91L48 87L50 88L50 82L53 79L48 82L46 81L48 80L45 80L45 83L41 80L31 82L33 79L30 74L32 72L30 75L23 76L19 72L26 72L24 71L26 70L18 70L17 67L15 67L18 66L18 63L22 62L22 59L28 60L31 57L35 58L37 55L34 52L37 51L19 53L12 49L15 48L8 46L21 42L25 42L25 45L33 45L36 43L32 43L30 40L34 43L39 42L25 39L13 33L15 31L25 30L32 23L40 22L41 24L41 21L48 21L53 18L58 19L55 20L56 21L67 20L72 23L107 24L116 27L116 73L124 73L123 75L130 80L139 76L153 92L160 94ZM381 150L397 149L400 141L403 138L407 138L412 151L406 152L406 154L405 152L404 155L399 156L397 159L398 162L396 163L398 166L400 165L400 167L397 166L395 168L394 166L394 168L385 171L384 169L382 179L380 180L378 176L380 175L378 176L380 183L377 189L377 183L375 183L375 178L377 177L374 178L373 183L375 185L371 182L375 185L375 187L372 185L375 187L374 189L373 187L375 190L371 189L376 190L378 196L376 192L377 194L373 194L376 195L376 197L377 195L376 198L372 197L374 198L372 200L375 200L370 201L360 212L357 212L358 214L357 213L354 218L354 224L360 240L359 248L355 249L352 240L349 238L349 230L344 224L338 227L338 224L332 222L330 224L328 224L328 222L319 223L319 225L323 225L321 227L324 230L319 227L320 229L315 229L315 227L311 226L305 225L302 228L300 226L297 232L295 233L296 232L293 231L294 233L291 234L289 238L290 246L283 242L282 237L274 226L270 226L269 229L266 230L254 216L234 218L221 211L211 212L208 206L198 203L197 198L190 189L190 186L192 188L190 185L194 185L188 185L183 174L184 167L182 160L184 144L187 144L184 144L185 140L183 140L181 133L189 134L187 138L190 135L190 139L188 139L191 138L189 130L299 130L299 128L301 128L301 131L314 135L324 135L326 133L340 140L342 143L344 142L344 145L346 144L346 146L350 148L351 159L347 164L349 167L364 161L364 157L373 157L375 153Z"};
  const PX = lo => ((lo + 170) * 4).toFixed(1), PY = la => ((75 - la) * 5).toFixed(1);
  function naDraw() {
    const sv = $('hlNaSvg'), bs = $('hlBigSvg'); if (!sv) return;
    const land = Object.entries(NA).map(([k, d]) => `<path class="land${k === '840' ? ' us' : ''}" d="${d}"/>`).join('');
    const on = s => isFinite(s.la) && isFinite(s.lo) && s.lo > -170 && s.lo < -50 && s.la > 14 && s.la < 75;
    const tt = s => `<title>${esc((s.ref ? s.ref + ' ' : '') + (s.name || '') + ' · ' + s.call + ' ' + (s.khz / 1000).toFixed(3) + ' ' + s.mode)}</title>`;
    const other = SP.filter(s => on(s) && !isNew(s) && passPBM(s)).map(s => `<circle class="sp" cx="${PX(s.lo)}" cy="${PY(s.la)}" r="3" data-dk="${esc(keyOf(s))}">${tt(s)}</circle>`).join('');
    const nw = SP.filter(s => on(s) && isNew(s) && passPBM(s)).map(s => `<circle class="${FAR && HOME && isFar(s) ? 'fr' : 'nw'}" cx="${PX(s.lo)}" cy="${PY(s.la)}" r="6" data-dk="${esc(keyOf(s))}">${tt(s)}</circle>`).join('');
    const hm = HOME ? `<circle class="home" cx="${PX(HOME.lo)}" cy="${PY(HOME.la)}" r="8"/>` : '';
    sv.innerHTML = land + other + nw + hm;
    if (bs) bs.innerHTML = land + other + nw + hm;
  }
  $('hlNa').onclick = () => { if (!MAPON) { MAPON = true; put('kpcHuntMap', true); mapOn(); } $('hlMapSec').scrollIntoView({ behavior: 'smooth', block: 'start' }); };
  let MAPON = get('kpcHuntMap', true);
  function mapOn() { $('hlBigMap').hidden = !MAPON && !DESKON(); $('hlMapTog').textContent = MAPON ? 'HIDE MAP' : 'SHOW MAP'; if (MAPON && LM) setTimeout(() => LM.invalidateSize(), 50); }
  $('hlMapTog').onclick = () => { MAPON = !MAPON; put('kpcHuntMap', MAPON); mapOn(); };

  /* ---------------- computers, members copy (Brandon Oct 16, 'like the new desktop logger'): ----------------
     log + entry dock on the left, SPOTS / MAP tabs on the right, every filter in one pop-up menu. Phones are unchanged. */
  function deskSet() {
    const m = $('hl'), on = DESKON();
    if (on) m.dataset.desk = '1'; else delete m.dataset.desk;
    /* computers: the live map moves INTO the log pane (map or log list, the entry box stays under either) */
    const bm = $('hlBigMap'), slot = $('dkMapSlot'), home = $('hlMapSec') && $('hlMapSec').querySelector('.hl-in');
    if (bm && slot && home) { const want = on ? slot : home; if (bm.parentNode !== want) { want.appendChild(bm); if (LM) setTimeout(() => LM.invalidateSize(), 60); } }
    if (on) { rtab(RT); dkList(); } else { const f = $('hlFilters'); if (f) f.classList.remove('desk-pop'); }
    mapOn();
  }
  let RT = get('kpcHuntRt', 'log'); if (RT !== 'map') RT = 'log';   /* left pane: my log OR the live map (Brandon Oct 17); spots always on the right */
  function rtab(v) {
    RT = v; put('kpcHuntRt', v); $('hl').dataset.rt = v;
    document.querySelectorAll('#hlLtabs [data-rt]').forEach(b => b.setAttribute('aria-pressed', b.dataset.rt === v));
    if (v === 'map') { lmInit(); setTimeout(() => { if (LM) { LM.invalidateSize(); lmZoom(LMV); } draw(); }, 60); }
  }
  if (!PUB && $('hlRtabs')) {
    $('hlLtabs').addEventListener('click', e => { const b = e.target.closest('[data-rt]'); if (!b) return; rtab(b.dataset.rt);
      const y = $('hlLtabs').getBoundingClientRect().top + scrollY - 150; if (scrollY > y + 5) scrollTo({ top: y, behavior: 'smooth' }); });
    $('hlFbtn').onclick = e => { e.stopPropagation(); $('hlFtog').click(); fPlace(); };
    function fPlace() { const f = $('hlFilters'), r = $('hlFbtn').getBoundingClientRect(), t = $('hlTick') ? $('hlTick').getBoundingClientRect().bottom : 0; const top = Math.max(r.bottom, t) + 8; f.style.top = top + 'px'; f.style.maxHeight = (innerHeight - top - 16) + 'px'; }
    addEventListener('scroll', () => { if (DESKON() && $('hlFilters').classList.contains('open')) fPlace(); }, { passive: true });
    document.addEventListener('click', e => {   /* tap outside the pop-up closes it */
      const f = $('hlFilters'); if (!DESKON() || !f.classList.contains('open')) return;
      if (e.target.closest('#hlFilters,#hlFbtn,#hlActive')) return; $('hlFtog').click();
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && DESKON() && $('hlFilters').classList.contains('open')) $('hlFtog').click(); });
    matchMedia('(min-width:1100px)').addEventListener('change', deskSet);
    /* the dock */
    const dkBand = () => { const f = parseFloat($('dFreq').value); $('dBand').value = f ? bandOf(f * 1000).replace('OTHER', '') : ''; dkDupe(); };
    function dkDupe() {
      const c = base($('dCall').value), r = $('dRef').value.toUpperCase().replace(/\s/g, ''), b = $('dBand').value, d = utc(new Date()).d;
      const hit = c && Q.q.find(q => base(q.call) === c && q.d === d && q.band === b && String(q.ref || '').replace(/\s/g, '') === r);
      $('dkDupe').hidden = !hit; if (hit) $('dkDupe').textContent = `⚠ DUPE: ${c} logged at ${fmtT(hit.tm)} UTC`;
    }
    $('dFreq').addEventListener('input', dkBand); ['dCall', 'dRef'].forEach(id => $(id).addEventListener('input', dkDupe)); $('dCall').addEventListener('input', dkWho);
    $('dMode').onchange = () => { $('dRs').value = rstFor($('dMode').value); $('dRr').value = rstFor($('dMode').value); };
    $('dCall').addEventListener('input', () => { const v = $('dCall').value.toUpperCase(); if (v !== $('dCall').value) $('dCall').value = v; });
    $('dSt').addEventListener('input', () => { $('dSt').value = $('dSt').value.toUpperCase(); });
    $('dkQ').oninput = () => dkList();
    $('dkClr').onclick = () => { dkClear(); $('dCall').focus(); };
    $('dkBack').onclick = () => { const sp = document.querySelector('.hl-spsec'), tk = $('hlTick'); if (!sp) return;   /* back up to the top of the spots, right under the banner (Brandon Oct 17) */
      const off = tk ? Math.max(0, tk.getBoundingClientRect().bottom) : 0; scrollTo({ top: sp.getBoundingClientRect().top + scrollY - off - 4, behavior: 'smooth' }); };
    $('dkRad').onclick = () => { const o = !$('hlDk').classList.contains('radio'); $('hlDk').classList.toggle('radio', o); $('dkRad').setAttribute('aria-expanded', o); if (o) $('dFreq').focus(); };
    ['dFreq', 'dRef'].forEach(id => $(id).addEventListener('input', dkRadT)); $('dMode').addEventListener('change', dkRadT); dkRadT();
    $('dkForm').addEventListener('submit', e => { e.preventDefault(); dkLog(); });
    const clk = () => { const n = new Date(); $('dkClk').textContent = n.toISOString().slice(11, 19) + ' UTC'; };
    clk(); setInterval(clk, 1000);
    if (!$('dRs').value) $('dMode').onchange();
    deskSet(); window.addEventListener('load', deskSet);
  }
  let BACKY = 0, BACKK = '';
  /* call sign look-up, same as the KPC Logger (callook.info for US calls, HamDB otherwise; shares its cache kpcLgCache) */
  const LKC = get('kpcLgCache', {});
  const tCase = v => { v = String(v || '').trim(); if (!v || /[a-z]/.test(v)) return v; return v.toLowerCase().replace(/\b([a-z])/g, m => m.toUpperCase()); };
  async function lookCall(call) {
    const b = base(call); if (!/^[A-Z0-9]{1,3}\d[A-Z0-9]{1,5}$/.test(b)) return null;
    const c = LKC[b]; if (c && Date.now() - c.t < 30 * 864e5) return c;
    const us = /^(A[A-L]|[KNW])[0-9A-Z]*\d/.test(b);
    const callook = async () => { const j = await fetch('https://callook.info/' + encodeURIComponent(b) + '/json').then(x => x.ok ? x.json() : null); if (!j || j.status !== 'VALID') return null;
      const l2 = String((j.address && j.address.line2) || ''), m = l2.match(/^(.*?),\s*([A-Z]{2})\s+\d/);
      return { name: j.name || '', qth: m ? tCase(m[1]) : tCase(l2), st: m ? m[2] : '', g: (j.location && j.location.gridsquare) || '', cl: (j.current && j.current.operClass) || (j.type === 'CLUB' ? 'CLUB' : ''), cty: 'United States' }; };
    const hamdb = async () => { const j = await fetch('https://api.hamdb.org/v1/' + encodeURIComponent(b) + '/json/kpclogger').then(x => x.ok ? x.json() : null); const h = j && j.hamdb, x = h && h.callsign;
      if (!x || !x.call || x.call === 'NOT_FOUND') return null;
      return { name: [x.fname, x.mi, x.name].filter(Boolean).join(' '), qth: tCase(x.addr2 || ''), st: x.state || '', g: x.grid || '', cl: x.class || '', cty: x.country || '' }; };
    let r = null; try { r = us ? (await callook().catch(() => null)) || (await hamdb().catch(() => null)) : await hamdb().catch(() => null); } catch (e) { r = null; }
    if (r) { r.t = Date.now(); r.name = tCase(r.name); LKC[b] = r; const k = Object.keys(LKC); if (k.length > 600) k.sort((x, y) => LKC[x].t - LKC[y].t).slice(0, 100).forEach(x => delete LKC[x]); put('kpcLgCache', LKC); }
    return r;
  }
  let dkWT = 0, dkWN = 0, DKWHO = null;
  function dkWho() {
    clearTimeout(dkWT); const call = $('dCall').value.trim().toUpperCase(), n = ++dkWN; DKWHO = null;
    if (base(call).length < 3) { $('dkWho').innerHTML = ''; return; }
    const prev = Q.q.filter(q => base(q.call) === base(call)).sort((a, b) => (b.d + b.tm).localeCompare(a.d + a.tm));
    const pv = prev.length ? `<span class="pv">🔁 worked ${prev.length}× before · last ${fmtD(prev[0].d)}${prev[0].ref ? ' at ' + esc(prev[0].ref) : ''} (${esc(prev[0].band)} ${esc(prev[0].mode)})</span>` : '<span class="pv nw">🆕 first time in your log</span>';
    $('dkWho').innerHTML = `<span class="lk">🔎 looking up ${esc(base(call))}…</span>${pv}`;
    dkWT = setTimeout(async () => {
      const r = await lookCall(call); if (n !== dkWN) return;
      DKWHO = r ? Object.assign({ call: base(call) }, r) : null;
      const who = r ? `<b>👤 ${esc(r.name || base(call))}</b> <span>${esc([r.qth, r.st].filter(Boolean).join(', ') || r.cty || '')}${r.g ? ' · ' + esc(r.g) : ''}${r.cl ? ' · ' + esc(r.cl) : ''}</span>` : `<span class="lk">No public listing for ${esc(base(call))}</span>`;
      $('dkWho').innerHTML = who + pv;
      if (r && r.st && !$('dSt').value && !$('dRef').value) $('dSt').value = r.st;
    }, 450);
  }
  function dkRadT() { const f = $('dFreq').value.trim(), r = $('dRef').value.trim(); $('dkRadT').textContent = (f || 'FREQ?') + ' ' + $('dMode').value + (r ? ' · ' + r : ''); $('dkRad').classList.toggle('bad', !f); }
  /* phones: jump down to the log; ↑ BACK TO SPOTS (only that button) goes back up */
  function dkGo() { BACKY = scrollY; setTimeout(() => $('hlDk').scrollIntoView({ behavior: 'smooth', block: 'end' }), 30); }
  /* phones: keyboard up while typing in the log = hide the extras so a few contacts show above the entry line (Brandon Oct 17) */
  let VVMAX = 0;
  function dkKb() {
    const vv = window.visualViewport, h = document.documentElement; if (!vv || PUB || DESKON() || !$('hlDk')) { h.classList.remove('hl-kb'); return; }
    VVMAX = Math.max(VVMAX, vv.height); const ae = document.activeElement, inDk = ae && ae.closest && ae.closest('#dkForm') && /^(INPUT|SELECT)$/.test(ae.tagName);
    const kb = !!inDk && vv.height < VVMAX - 120, was = h.classList.contains('hl-kb'); h.classList.toggle('hl-kb', kb);
    h.style.setProperty('--vvh', Math.round(vv.height) + 'px'); h.style.setProperty('--dkd', $('dkForm').offsetHeight + 'px');
    if (kb && !was) setTimeout(() => { const r = $('hlDk').getBoundingClientRect(); scrollBy(0, r.bottom - vv.height - vv.offsetTop + 6); }, 80);
  }
  if (window.visualViewport) { visualViewport.addEventListener('resize', dkKb); addEventListener('orientationchange', () => { VVMAX = 0; setTimeout(dkKb, 400); }); document.addEventListener('focusin', () => setTimeout(dkKb, 350)); document.addEventListener('focusout', () => setTimeout(dkKb, 350)); }
  function dkFill(s) {
    if (!$('dCall')) return;
    BACKK = s.call ? s.p + '|' + s.call + '|' + s.ref : '';
    $('dCall').value = s.call || ''; $('dFreq').value = s.khz ? (s.khz / 1000).toFixed(4).replace(/0+$/, '').replace(/\.$/, '') : $('dFreq').value;
    if (s.mode) $('dMode').value = modePick(s.mode);
    $('dRef').value = s.ref || ''; $('dName').value = s.name || ''; $('dSt').value = s.st || ''; $('dNote').value = '';
    $('dRs').value = rstFor($('dMode').value); $('dRr').value = rstFor($('dMode').value);
    $('dFreq').dispatchEvent(new Event('input')); dkRadT(); dkWho();
    if (!PUB && window.KPCCat && KPCCat.get().on && s.khz) KPCCat.tune(s.khz, $('dMode').value || s.mode).then(ok => { catChip(); if (!ok) toast('📻 Radio not set: open the CAT & QRZ tab to connect it.'); });
    const d = $('dkForm'); d.classList.remove('flash'); void d.offsetWidth; d.classList.add('flash');
    (s.call ? $('dRr') : $('dCall')).focus({ preventScroll: true }); if (s.call) $('dRr').select();
  }
  /* radio control (CAT, kpc-cat.js; set up on the CAT & QRZ tab): chip on the log + the log follows the radio's dial */
  function catChip() { const c = $('dkCat'); if (!c || !window.KPCCat) return; const S = KPCCat.get(); c.hidden = !S.on; const on = KPCCat.connected();
    c.className = 'dk-cat mem-only ' + (on ? 'on' : 'off'); c.textContent = on ? '📻 CAT ON' : '📻 CAT: CONNECT'; c.title = on ? 'Your radio follows the spots you click' : 'Radio not connected: tap to set it up'; }
  if (!PUB && window.KPCCat) {
    KPCCat.onStatus(() => catChip()); catChip();
    if (KPCCat.get().on) KPCCat.connect(false).then(catChip); // a radio this browser was allowed before reconnects by itself
    $('dkCat') && $('dkCat').addEventListener('click', async e => { if (!KPCCat.connected() && KPCCat.supported()) { e.preventDefault(); if (await KPCCat.connect(true)) toast('📻 Radio connected.'); else location.href = 'kpc-hunt-cat.html'; catChip(); } });
    KPCCat.follow(r => { if (!$('dFreq') || !r.khz) return; $('dFreq').value = (r.khz / 1000).toFixed(4).replace(/0+$/, '').replace(/\.$/, ''); if (r.mode) { const m = r.mode === 'DATA' ? 'FT8' : /SB$/.test(r.mode) ? 'SSB' : r.mode; if ([...$('dMode').options].some(o => o.value === m)) $('dMode').value = m; }
      $('dFreq').dispatchEvent(new Event('input')); dkRadT(); });
  }
  function dkClear() {
    ['dCall', 'dRef', 'dName', 'dSt', 'dNote'].forEach(id => { $(id).value = ''; }); dkWN++; DKWHO = null; $('dkWho').innerHTML = '';
    $('dRs').value = rstFor($('dMode').value); $('dRr').value = rstFor($('dMode').value); $('dkDupe').hidden = true;
  }
  async function dkLog() {
    const call = $('dCall').value.trim().toUpperCase(); if (!call) { $('dCall').focus(); return; }
    const n = utc(new Date());
    const ref = $('dRef').value.toUpperCase().split(/[ ,]+/).filter(Boolean).map(nref).join(', ');
    const f = $('dFreq').value.trim();
    const rec = { id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), call, d: n.d, tm: n.t, f, band: $('dBand').value, mode: $('dMode').value, ref,
      name: $('dName').value.trim(), st: $('dSt').value.trim().toUpperCase(), rs: $('dRs').value.trim(), rr: $('dRr').value.trim(), note: $('dNote').value.trim(), my: CALL, grid: Q.grid, x: 0, t: Date.now() };
    const w = DKWHO && DKWHO.call === base(call) ? DKWHO : (LKC[base(call)] || null); if (w) { rec.on = w.name || ''; rec.qth = [w.qth, w.st].filter(Boolean).join(', '); rec.tg = w.g || ''; }
    Q.q.push(rec); await qSave();
    ref.split(/[ ,]+/).filter(Boolean).forEach(r => { if (!WK.has(r)) { WK.add(r); MAN.add(r); } }); saveLog(); logInfo();
    qList(); ticker(false); draw(); needDraw();
    toast(`✓ ${call} logged${ref ? ' at ' + ref : ''}.`, () => { Q.q = Q.q.filter(q => q.id !== rec.id); qSave(); qList(); draw(); });
    dkClear(); $('dCall').focus({ preventScroll: true });
    if (!PUB && window.KPCQrz && KPCQrz.on()) { const a = adif([rec]); const one = a.slice(a.indexOf('<EOH>') + 5).trim();
      KPCQrz.send(one).then(r => { if (r.ok) { rec.qz = r.sure ? 2 : 1; qSave(); } toast((r.ok ? '☁ QRZ: ' : '⚠ QRZ: ') + r.msg); }); }
    /* the effect flares only every 50 contacts or for DX outside North America (Brandon Oct 17) */
    const NAPRE = /^(A[A-L]|[KNW]|V[A-GOY]|C[F-KYZ]|X[A-O]|4[A-C]|6[D-J]|C[LMO]|T[GI]|H[O-RI]|YN|YS|V[23P]|J[3678]|8P|6Y|ZF|C6|FG|FM|FS|PJ|P4|HH|OX|XP|TO|FP|ZB)/;
    const dx = base(call).length > 2 && !NAPRE.test(base(call)), tot = Q.q.length;
    if (tot % 50 === 0 || dx) { const fx = $('dkForm'); fx.classList.remove('pop'); void fx.offsetWidth; fx.classList.add('pop'); setTimeout(() => fx.classList.remove('pop'), 3200);
      fire(dx ? `🌍 DX! ${base(call)} is outside North America` : `🎉 ${tot} contacts in your log!`); }
  }
  function dkList() {
    const el = $('dkList'); if (!el || PUB) return;
    const q = ($('dkQ').value || '').trim().toUpperCase(), today = utc(new Date()).d;
    const L = Q.q.filter(x => !q || [x.call, x.ref, x.name, x.st, x.band, x.mode, x.note].join(' ').toUpperCase().includes(q)).sort((a, b) => (b.d + b.tm).localeCompare(a.d + a.tm));
    const nt = Q.q.filter(x => x.d === today).length;
    $('dkN').innerHTML = `<b>${nt}</b> today · <b>${Q.q.length}</b> total`;
    let last = '';
    el.innerHTML = L.length ? L.slice(0, 300).map(x => {
      const day = x.d !== last ? `<div class="dk-day">${x.d === today ? 'TODAY' : fmtD(x.d)}</div>` : ''; last = x.d;
      return `${day}<div class="dk-q${x.x ? '' : ' nx'}"><span class="t">${fmtT(x.tm)}</span><b class="c">${esc(x.call)}${x.on ? ` <small class="on">${esc(x.on.split(' ')[0])}</small>` : ''}</b><span class="m">${esc(x.band)} ${esc(x.mode)}</span><span class="r">${esc(x.ref || '')}${x.st ? ' <i>' + esc(x.st) + '</i>' : ''}</span><span class="s">${esc(x.rs || '')}/${esc(x.rr || '')}</span><span class="a"><button type="button" data-qe="${x.id}" title="Edit">✏</button><button type="button" data-qd="${x.id}" title="Delete">🗑</button></span></div>`;
    }).join('') : `<div class="hl-empty">${Q.q.length ? 'None match.' : 'No contacts yet. Click a spot on the right and it fills in down below.'}</div>`;
  }
  document.addEventListener('click', e => {
    const c = e.target.closest('#hlBigSvg [data-dk]'); if (!c) return;
    let el = document.querySelector(`#hlSpots [data-k="${CSS.escape(c.dataset.dk)}"]`);
    if (!el) { F.hide = false; F.nw = false; F.q = ''; saveF(); chips(); draw(); el = document.querySelector(`#hlSpots [data-k="${CSS.escape(c.dataset.dk)}"]`); }
    if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); el.classList.remove('fresh'); void el.offsetWidth; el.classList.add('fresh'); }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { $('hlNa').classList.remove('big'); closeSheet(); } });


  /* ---------------- computers only: a small scrolling CONDITIONS bar under the banner (Brandon Oct 17) ----------------
     the sun (NOAA SWPC: solar flux, Kp, X-ray), the weather where you are (Open-Meteo) and WSPR signal reports by band
     from the grid squares around you (db1.wspr.live, last 30 minutes). Where you are = GPS (only when tapped or already
     allowed), else your log's grid, else the middle of Kentucky. Nothing about you is sent anywhere but those services. */
  (function cxBar() {
    const bar = $('hlCx'); if (!bar) return;
    const wide = () => true;   /* computers AND phones since Oct 17 (Brandon) */
    const g2ll = g => { g = String(g || '').toUpperCase(); if (!/^[A-R]{2}\d{2}/.test(g)) return null; const lo = (g.charCodeAt(0) - 65) * 20 - 180 + (+g[2]) * 2 + 1, la = (g.charCodeAt(1) - 65) * 10 - 90 + (+g[3]) + .5; return [la, lo]; };
    const ll2g = (la, lo) => { lo += 180; la += 90; return String.fromCharCode(65 + Math.floor(lo / 20)) + String.fromCharCode(65 + Math.floor(la / 10)) + Math.floor((lo % 20) / 2) + Math.floor(la % 10); };
    const around = g => { const c = g2ll(g); if (!c) return [g]; const o = new Set(); for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) o.add(ll2g(c[0] + a, c[1] + b * 2)); return [...o]; };
    let LOC = get('kpcHuntCx', null), busy = false, last = 0;
    const WX = { 0: '☀️ Clear', 1: '🌤 Mostly clear', 2: '⛅ Partly cloudy', 3: '☁️ Cloudy', 45: '🌫 Fog', 48: '🌫 Fog', 51: '🌦 Drizzle', 53: '🌦 Drizzle', 55: '🌦 Drizzle', 61: '🌧 Rain', 63: '🌧 Rain', 65: '🌧 Heavy rain', 71: '🌨 Snow', 73: '🌨 Snow', 75: '🌨 Heavy snow', 80: '🌦 Showers', 81: '🌦 Showers', 82: '⛈ Heavy showers', 95: '⛈ Thunderstorms', 96: '⛈ Storms + hail', 99: '⛈ Storms + hail' };
    const BN = [[1, '160m'], [3, '80m'], [5, '60m'], [7, '40m'], [10, '30m'], [14, '20m'], [18, '17m'], [21, '15m'], [24, '12m'], [28, '10m'], [50, '6m']];
    async function where() {
      if (LOC && LOC.src === 'gps' && Date.now() - LOC.t < 6 * 36e5) return LOC;
      try { const p = navigator.permissions && await navigator.permissions.query({ name: 'geolocation' }); if (p && p.state === 'granted') return await gps(); } catch (e) {}
      const g = (Q.grid || '').slice(0, 4).toUpperCase(); if (/^[A-R]{2}\d{2}$/.test(g)) { const c = g2ll(g); return { la: c[0], lo: c[1], g, src: 'grid' }; }
      if (LOC) return LOC; return { la: 37.6, lo: -85.2, g: 'EM77', src: 'ky' };
    }
    function gps() { return new Promise((ok, no) => navigator.geolocation ? navigator.geolocation.getCurrentPosition(p => { const la = p.coords.latitude, lo = p.coords.longitude; LOC = { la, lo, g: ll2g(la, lo), src: 'gps', t: Date.now() }; put('kpcHuntCx', LOC); ok(LOC); }, no, { timeout: 12000, maximumAge: 6e5 }) : no()); }
    const one = (u, ms) => jget(u, ms || 20000).catch(() => null);
    async function load() {
      if (busy || !wide()) return; busy = true; last = Date.now();
      try {
        const L = await where(), sq = around(L.g), IN = "('" + sq.join("','") + "')";
        const sql = `SELECT band, count(*) AS c, max(distance) AS d FROM wspr.rx WHERE time > now() - INTERVAL 30 MINUTE AND band IN (${BN.map(b => b[0]).join(',')}) AND (substring(tx_loc,1,4) IN ${IN} OR substring(rx_loc,1,4) IN ${IN}) GROUP BY band ORDER BY band FORMAT JSON`;
        const [ws, kp, sf, xr, wx] = await Promise.all([one('https://db1.wspr.live/?query=' + encodeURIComponent(sql), 25000), one('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'),
          one('https://services.swpc.noaa.gov/products/summary/10cm-flux.json'), one('https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json'),
          one(`https://api.open-meteo.com/v1/forecast?latitude=${L.la.toFixed(3)}&longitude=${L.lo.toFixed(3)}&current=temperature_2m,weather_code,wind_speed_10m,wind_gusts_10m&daily=sunrise,sunset&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto&forecast_days=1`)]);
        const it = [];
        const sfi = sf ? Number((Array.isArray(sf) ? sf[0] : sf).flux) : NaN, k = kp && kp.length ? Number(kp[kp.length - 1].Kp) : NaN;
        if (isFinite(sfi)) it.push(`☀ Solar flux <b>${Math.round(sfi)}</b>`);
        if (isFinite(k)) it.push(`🧲 Kp <b>${k.toFixed(k % 1 ? 1 : 0)}</b> ${k >= 5 ? '<i class="bad">STORM</i>' : k >= 4 ? '<i class="meh">unsettled</i>' : '<i class="ok">calm</i>'}`);
        if (xr && xr.length) { const f = (xr.filter(x => x.energy === '0.1-0.8nm').pop() || {}).flux; if (f) { const c = f >= 1e-4 ? 'X' : f >= 1e-5 ? 'M' : f >= 1e-6 ? 'C' : f >= 1e-7 ? 'B' : 'A', m = (f / { X: 1e-4, M: 1e-5, C: 1e-6, B: 1e-7, A: 1e-8 }[c]).toFixed(1); it.push(`💥 X-ray <b>${c}${m}</b>${c === 'X' || c === 'M' ? ' <i class="bad">flare: low bands may fade</i>' : ''}`); } }
        if (isFinite(sfi) && isFinite(k)) { const sc = (sfi >= 150 ? 3 : sfi >= 110 ? 2 : sfi >= 80 ? 1 : 0) - (k >= 5 ? 3 : k >= 4 ? 2 : k >= 3 ? 1 : 0); it.push(`📻 HF <b>${sc >= 3 ? 'GREAT' : sc >= 2 ? 'GOOD' : sc >= 1 ? 'FAIR' : sc >= 0 ? 'SO-SO' : 'ROUGH'}</b>`); }
        const here = L.src === 'gps' ? 'at your spot' : L.src === 'grid' ? 'near ' + L.g : 'in Kentucky';
        if (wx && wx.current) { const c = wx.current; it.push(`${WX[c.weather_code] || '🌡'} <b>${Math.round(c.temperature_2m)}°F</b> ${esc(here)} · wind ${Math.round(c.wind_speed_10m)} mph${c.wind_gusts_10m > 25 ? ` <i class="meh">gusts ${Math.round(c.wind_gusts_10m)}</i>` : ''}`);
          const ft = v => { try { return new Date(v).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }); } catch (e) { return ''; } };
          if (wx.daily && wx.daily.sunrise) it.push(`🌅 Sunrise ${ft(wx.daily.sunrise[0])} · 🌇 sunset ${ft(wx.daily.sunset[0])}`); }
        const rows = (ws && ws.data) || [], m = {}; rows.forEach(r => { m[Number(r.band)] = [Number(r.c), Number(r.d)]; });
        const max = Math.max(0, ...rows.map(r => Number(r.c)));
        if (ws) it.push(`📡 WSPR near ${esc(L.g)} (last 30 min): ` + BN.map(([b, n]) => { const v = m[b]; return v ? `<span class="wb${v[0] >= max * .6 ? ' hot' : ''}">${n} <b>${v[0].toLocaleString()}</b>${v[1] ? ` <small>to ${Math.round(v[1] * .621).toLocaleString()} mi</small>` : ''}</span>` : `<span class="wb q">${n} quiet</span>`; }).join(' '));
        else it.push('📡 WSPR reports are not answering right now');
      it.push('⛈ <i class="meh">Forecasts can be wrong: watch the sky, and take the antenna down if you hear thunder</i>');
        const html = it.map(x => `<span class="ci">${x}</span>`).join('<span class="cs">•</span>');
        $('hlCxT').innerHTML = html + '<span class="cs">•</span>' + html;   /* twice, so the scroll loops with no gap */
        $('hlCxT').style.animationDuration = Math.max(40, Math.round($('hlCxT').scrollWidth / 2 / 45)) + 's';
        $('hlCxK').textContent = '📡 ' + (L.src === 'gps' ? 'YOUR SPOT' : L.g);
        $('hlCxLoc').hidden = L.src === 'gps';
      } catch (e) { console.error('cx', e); } finally { busy = false; }
    }
    $('hlCxLoc').onclick = () => gps().then(() => { last = 0; load(); }).catch(() => toast('Location is off for this site. Using your log\'s grid (MY LOG FILES › My grid) or Kentucky instead.'));
    load(); setInterval(() => { if (Date.now() - last > 10 * 6e4 && !document.hidden) load(); }, 60000);
    matchMedia('(min-width:1100px)').addEventListener('change', () => { if (wide() && !last) load(); });
  })();
  /* ---------------- Kentucky hunting season badge (Brandon Oct 17: 'a bow for archery and a gun for gun season, automatically') ----------------
     Dates follow KDFWR's usual pattern: deer archery = 1st Saturday of September to the 3rd Monday of January; early muzzleloader =
     3rd Saturday of October + Sunday; modern gun = 2nd Saturday of November for 16 days; late muzzleloader = 2nd Saturday of
     December for 9 days; spring turkey = 2nd Saturday of April for 23 days. Gun beats archery when both are open. */
  (function seasonBadge() {
    const hero = document.querySelector('.hl-hero .hl-acts'); if (!hero) return;
    const nth = (y, m, wd, n) => { const d = new Date(y, m, 1); d.setDate(1 + ((wd - d.getDay() + 7) % 7) + (n - 1) * 7); return d; };
    const add = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
    const now = new Date(), day = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const S = [];
    for (const y of [now.getFullYear() - 1, now.getFullYear()]) {
      S.push(['archery', nth(y, 8, 6, 1), nth(y + 1, 0, 1, 3)]);
      S.push(['muzzle', nth(y, 9, 6, 3), add(nth(y, 9, 6, 3), 1)]);
      S.push(['gun', nth(y, 10, 6, 2), add(nth(y, 10, 6, 2), 15)]);
      S.push(['muzzle', nth(y, 11, 6, 2), add(nth(y, 11, 6, 2), 8)]);
      S.push(['turkey', nth(y + 1, 3, 6, 2), add(nth(y + 1, 3, 6, 2), 22)]);
    }
    const open = S.filter(([, a, b]) => day >= a && day <= b), rank = { gun: 0, muzzle: 1, turkey: 2, archery: 3 };
    if (!open.length) return; open.sort((x, y) => rank[x[0]] - rank[y[0]]);
    const [k, , end] = open[0], fd = d => d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    const RIFLE = '<svg viewBox="0 0 64 20" width="46" height="15" aria-hidden="true"><path fill="currentColor" d="M1 9h30l3-3h9l1 2h14l5-1v4l-5 1H44l-2 2h-4l-1 5h-6l1-5h-3l-2 2H17l-3-2H1z"/></svg>';
    const T = { gun: [RIFLE, 'MODERN GUN DEER SEASON IN KENTUCKY'], muzzle: [RIFLE, 'MUZZLELOADER DEER SEASON IN KENTUCKY'],
      archery: ['<span class="em">🏹</span>', 'ARCHERY DEER SEASON IN KENTUCKY'], turkey: ['<span class="em">🦃</span>', 'SPRING TURKEY SEASON IN KENTUCKY'] }[k];
    const b = document.createElement('a'); b.className = 'hl-season s-' + k; b.href = 'https://fw.ky.gov'; b.target = '_blank'; b.rel = 'noopener';
    b.title = 'Hunters are in the woods. Dates follow KDFWR\'s usual pattern; check fw.ky.gov for the exact dates and rules.';
    b.innerHTML = `<i>${T[0]}</i><span><b>${T[1]}</b><small>until about ${fd(end)} · hunters are out: wear blaze orange in WMAs and forests, stay near roads and parking</small></span>`;
    hero.parentNode.insertBefore(b, hero);
  })();
  /* ---------------- start (Members Room page, no password since Oct 16 evening) ---------------- */
  function startApp() {
    const home0 = (HOME && HOME.label && (HOME.label.match(/middle of (.+)$/) || [])[1]) || '';
    const st0 = Object.keys(ST).find(k => ST[k] === home0) || 'KY';
    $('fSt').innerHTML = '<option value="">Any state</option>' + stOpts('');
    $('hSt').innerHTML = '<option value="">…or pick your state</option>' + stOpts('');
    $('nSt').innerHTML = stOpts(st0); if ($('tSt')) $('tSt').innerHTML = stOpts(st0);
    const qst = new URLSearchParams(location.search).get('st'); if (qst && ST[qst.toUpperCase()]) { $('nSt').value = qst.toUpperCase(); $('nSt').dataset.set = 1; }
    document.querySelectorAll('.hl-ptabs [data-pt]').forEach(t => { if (t.dataset.pt === PAGE) t.setAttribute('aria-current', 'page'); });
    /* each part on its own, so one problem never stops the rest of the page */
    [stick, chips, viewChips, bell, flameBtn, lmInit, logInfo, homeInfo, mapOn, qsoInit, awDraw, fromPotaHash, load, needLoad, topDraw, myStats].forEach(f => { try { const r = f(); if (r && r.catch) r.catch(e => console.error(f.name, e)); } catch (e) { console.error(f.name, e); } });
    setInterval(() => {
      const s = Math.max(0, Math.round((next - Date.now()) / 1000)); $('hsAge').textContent = next ? s + 's' : '–'; if (next && Date.now() >= next) { next = 0; load(); }
      const u = new Date(); $('hsUtc').textContent = u.toISOString().slice(11, 19);
      const n = Q.q.filter(q => q.d === today()).length; $('hsUtcL').textContent = PUB ? 'UTC' : `UTC · ${n} LOGGED TODAY`;
    }, 1000);
    setInterval(() => { document.querySelectorAll('.hs').length && draw(); }, 5 * 60e3);
  }
  startApp();
  window.KPCHunt = { scan, nref, adif, parseAdif };
})();
