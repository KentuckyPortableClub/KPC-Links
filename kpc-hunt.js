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
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const base = c => String(c || '').toUpperCase().trim().split('/').reduce((a, b) => b.length > a.length ? b : a, '');
  const ST = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };
  const BANDS = [['160m', 1800, 2000], ['80m', 3500, 4000], ['60m', 5330, 5410], ['40m', 7000, 7300], ['30m', 10100, 10150], ['20m', 14000, 14350], ['17m', 18068, 18168], ['15m', 21000, 21450], ['12m', 24890, 24990], ['10m', 28000, 29700], ['6m', 50000, 54000], ['2m', 144000, 148000], ['70cm', 420000, 450000]];
  const bandOf = k => (BANDS.find(b => k >= b[1] && k <= b[2]) || ['OTHER'])[0];
  const modeOf = m => { m = String(m || '').toUpperCase(); if (/SSB|LSB|USB|PHONE|^AM$|^FM$/.test(m)) return 'PHONE'; if (/^CW/.test(m)) return 'CW'; if (/FT8|FT4|RTTY|PSK|JS8|DATA|DIGI|OLIVIA|MFSK|JT|SSTV|VARA|Q65/.test(m)) return 'DIGITAL'; return 'OTHER'; };
  const WHERE = [['all', 'EVERYWHERE'], ['us', 'USA'], ['usca', 'USA + CANADA'], ['range', 'IN MY RANGE']];

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
  let F = Object.assign({ p: ['POTA', 'WWFF', 'SOTA'], hide: false, nw: false, rg: false, bands: [], modes: [], where: 'all', st: '', q: '', sort: 'new' }, get('kpcHuntF', {}));
  const saveF = () => put('kpcHuntF', F);
  let HOME = get('kpcHuntHome', null), RANGE = +get('kpcHuntRange', 1500) || 1500, FAR = get('kpcHuntFar', true), BELL = get('kpcHuntBell', false), NOTE = get('kpcHuntNote', false);
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
  async function jget(u) { const c = new AbortController(), tm = setTimeout(() => c.abort(), 15000); try { const r = await fetch(u, { cache: 'no-store', signal: c.signal }); if (!r.ok) throw new Error(r.status); return await r.json(); } finally { clearTimeout(tm); } }
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
  function fromHole(x) {
    if (!/WWFF/i.test(String(x.sig || ''))) return null; const khz = toKhz(x.freq != null ? x.freq : x.frequency); if (!khz) return null;
    const rr = x.sig_refs || x.sig_ref || []; const refs = (Array.isArray(rr) ? rr : [rr]).map(v => typeof v === 'string' ? { id: v } : { id: v.id || v.ref || '', name: v.name || '' }).filter(v => v.id);
    if (!refs.length) return null; const ref = refs[0].id.toUpperCase();
    return { p: 'WWFF', call: String(x.dx_call || x.activator || '').toUpperCase(), khz, mode: String(x.mode || '').toUpperCase(), ref, name: refs[0].name || x.sig_refs_names || '', loc: '', st: String(x.dx_state || '').toUpperCase(),
      la: +(x.dx_latitude ?? x.dx_lat ?? NaN), lo: +(x.dx_longitude ?? x.dx_lon ?? NaN), t: toMs(x.time), by: x.de_call || '', com: x.comment || '', us: /^KFF-/.test(ref), ca: /^VEFF-/.test(ref) };
  }
  async function load() {
    const out = [], got = [];
    await Promise.all([
      jget('https://api.pota.app/spot/activator').then(a => { (a || []).forEach(x => { const s = fromPota(x); if (s) out.push(s); }); got.push('POTA'); }).catch(() => {}),
      jget('https://api2.sota.org.uk/api/spots/50/all').then(a => { (a || []).forEach(x => { const s = fromSota(x); if (s) out.push(s); }); got.push('SOTA'); }).catch(() => {}),
      jget('https://spothole.app/api/v1/spots?limit=1000&max_age=3600').then(j => { const a = Array.isArray(j) ? j : (j && j.spots) || []; a.forEach(x => { const s = fromHole(x); if (s) out.push(s); }); got.push('WWFF (Spothole)'); }).catch(() => {})
    ]);
    const now = Date.now(), seen = new Map();
    out.filter(s => s.call && (!s.t || now - s.t < 75 * 60e3)).sort((a, b) => (b.t || 0) - (a.t || 0)).forEach(s => { const k = s.p + '|' + s.call + '|' + s.ref; if (!seen.has(k)) seen.set(k, s); });
    SP = [...seen.values()];
    await loadParks();
    SP.forEach(s => {
      const k = PK[s.ref];
      if (k) { if (!isFinite(s.la) && isFinite(k.la)) { s.la = k.la; s.lo = k.lo; } if (!s.st && k.st) s.st = k.st; if (k.a != null) s.acts = k.a; if (!s.name) s.name = k.n; }
      if (s.p === 'SOTA' && SUM[s.ref]) { s.la = SUM[s.ref][0]; s.lo = SUM[s.ref][1]; s.acts = SUM[s.ref][2]; }
    });
    src = got.length ? 'Spots from ' + got.join(', ') + '. Checked every minute while this page is open.' : 'The spot sites are not answering right now. Trying again in a minute.';
    /* look up where new-to-you SOTA summits are (only those), then redraw */
    const need = SP.filter(s => s.p === 'SOTA' && !isFinite(s.la) && isNew(s)).slice(0, 12);
    if (need.length) Promise.all(need.map(async s => { const w = await sotaWhere(s); if (w) { s.la = w[0]; s.lo = w[1]; s.acts = w[2]; } })).then(() => { ticker(false); draw(); });
    ticker(!first); first = false; draw(); needDraw();
    next = Date.now() + 60e3;
  }
  const isNew = s => hasLog() && !WK.has(s.ref);
  const passPBM = s => F.p.includes(s.p) && (!F.bands.length || F.bands.includes(bandOf(s.khz))) && (!F.modes.length || F.modes.includes(modeOf(s.mode)));

  /* ---------------- ticker + alerts ---------------- */
  let AC = null;
  function chime() {
    try {
      AC = AC || new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === 'suspended') AC.resume();
      [[880, 0], [1320, .16], [1760, .32]].forEach(([f, d]) => { const o = AC.createOscillator(), g = AC.createGain(); o.frequency.value = f; o.type = 'sine'; o.connect(g); g.connect(AC.destination); const t = AC.currentTime + d; g.gain.setValueAtTime(.0001, t); g.gain.exponentialRampToValueAtTime(.25, t + .02); g.gain.exponentialRampToValueAtTime(.0001, t + .28); o.start(t); o.stop(t + .3); });
    } catch (e) {}
    try { navigator.vibrate && navigator.vibrate([180, 90, 180]); } catch (e) {}
  }
  const tItem = s => `<span class="it" data-k="${esc(s.p + '|' + s.call + '|' + s.ref)}">✨ <b>${esc(s.ref)}</b> ${esc(s.name || '')} <small>${esc(s.st || s.loc || '')}</small> · ${esc(s.call)} <i>${(s.khz / 1000).toFixed(3)}</i> <small>${esc(s.mode || '')}</small></span>`;
  function ticker(alert) {
    const T = $('hlTickT'), FT = $('hlFarT');
    if (!hasLog()) { T.innerHTML = '<span class="hl-wait">Load your log (Step 1 below) and new-to-you parks will roll across here.</span>'; T.style.setProperty('--dur', '22s'); $('hlFar').hidden = true; return; }
    const L = SP.filter(s => isNew(s) && passPBM(s));
    const far = FAR && HOME ? L.filter(isFar) : [], near = L.filter(s => !far.includes(s));
    const fresh = near.filter(s => !SEEN.has(s.p + '|' + s.call + '|' + s.ref));
    L.forEach(s => SEEN.add(s.p + '|' + s.call + '|' + s.ref));
    if (near.length) { const h = near.map(tItem).join(''); if (T.dataset.h !== h) { T.innerHTML = h; T.dataset.h = h; T.style.setProperty('--dur', Math.max(20, T.textContent.length * .2) + 's'); } }
    else { T.dataset.h = ''; T.innerHTML = `<span class="hl-wait">Nothing new to you on the air right now${far.length ? ` (${far.length} far away up top)` : ''}. Checking every minute…</span>`; T.style.setProperty('--dur', '24s'); }
    $('hlFar').hidden = !far.length;
    if (far.length) { FT.innerHTML = far.map(s => `<span>✨ <b>${esc(s.ref)}</b> ${esc(s.name)} ${esc(s.st || '')} · ${esc(s.call)} ${(s.khz / 1000).toFixed(3)} ${esc(s.mode)} · ${Math.round(dist(s))} mi</span>`).join(''); FT.style.setProperty('--dur', Math.max(25, FT.textContent.length * .16) + 's'); }
    if (alert && fresh.length) {
      const t = $('hlTick'); t.classList.remove('flash'); void t.offsetWidth; t.classList.add('flash');
      if (BELL) chime();
      if (NOTE && 'Notification' in window && Notification.permission === 'granted') {
        try { const s = fresh[0]; new Notification('New park for you: ' + s.ref, { body: `${s.name || ''} ${s.st || ''}\n${s.call} on ${(s.khz / 1000).toFixed(3)} ${s.mode}${fresh.length > 1 ? `\n+${fresh.length - 1} more` : ''}`, icon: 'kpc-icon-180.png', tag: 'kpc-hunt' }); } catch (e) {}
      }
    }
    $('hsNew').textContent = hasLog() ? SP.filter(isNew).length : '–';
  }
  function bell() { const b = $('hlBell'); b.setAttribute('aria-pressed', BELL); b.textContent = BELL ? '🔔 ALERT ON' : '🔕 ALERT OFF'; }
  $('hlBell').onclick = () => { BELL = !BELL; put('kpcHuntBell', BELL); bell(); if (BELL) chime(); };
  document.addEventListener('click', e => {
    const it = e.target.closest('.hl-tick-track .it'); if (!it) return;
    const c = document.querySelector(`.hs[data-k="${CSS.escape(it.dataset.k)}"]`);
    if (c) { c.scrollIntoView({ behavior: 'smooth', block: 'center' }); c.classList.remove('fresh'); void c.offsetWidth; c.classList.add('fresh'); }
  });

  /* ---------------- spot cards ---------------- */
  const ago = t => { if (!t) return ''; const m = Math.max(0, Math.round((Date.now() - t) / 60e3)); return m < 1 ? 'just now' : m + ' min ago'; };
  const pageOf = s => s.p === 'SOTA' ? 'https://sotl.as/summits/' + s.ref : s.p === 'WWFF' ? 'https://wwff.co/directory/?showRef=' + s.ref : 'https://pota.app/#/park/' + s.ref;
  function card(s) {
    const n = isNew(s), w = hasLog() && WK.has(s.ref), d = dist(s), k = s.p + '|' + s.call + '|' + s.ref;
    const b = [`<span class="hb prog">${s.p}</span>`];
    if (n) b.push('<span class="hb new">✨ NEW TO YOU</span>'); else if (w) b.push('<span class="hb wk">✓ WORKED</span>');
    if (s.acts === 0) b.push('<span class="hb atno">FIRST EVER ACTIVATION</span>'); else if (s.acts != null && s.acts <= 5) b.push(`<span class="hb rare">RARE · ${s.acts}</span>`);
    if (d != null && d > RANGE) b.push(`<span class="hb far">FAR · ${Math.round(d)} MI</span>`);
    b.push(`<span class="hb">${bandOf(s.khz)}</span>`, `<span class="hb">${esc(s.mode || '?')}</span>`);
    return `<article class="hs${n ? ' new' : ''}${w ? ' worked' : ''}" data-k="${esc(k)}">
 <div class="hs-top"><div class="hs-call"><a href="https://www.qrz.com/db/${encodeURIComponent(base(s.call))}" target="_blank" rel="noopener">${esc(s.call)}</a></div><div class="hs-f"><b>${(s.khz / 1000).toFixed(3)}</b><span>MHz · ${esc(s.mode || '')}</span></div></div>
 <div class="hs-park"><a href="${pageOf(s)}" target="_blank" rel="noopener">${esc(s.ref)}</a>${esc(s.name || '')}</div>
 <div class="hs-meta">${esc(s.st ? (ST[s.st] || s.st) : s.loc)}${d != null ? ' · ' + Math.round(d) + ' mi' : ''} · ${ago(s.t)}${s.by ? ' · spotted by ' + esc(s.by) : ''}</div>
 ${s.com ? `<div class="hs-com">“${esc(String(s.com).slice(0, 140))}”</div>` : ''}
 <div class="hs-b">${b.join('')}</div>
 <div class="hs-a"><button type="button" class="wk${w ? ' on' : ''}" data-wk="${esc(s.ref)}">${w ? '✓ WORKED' : '＋ I WORKED IT'}</button><a href="${pageOf(s)}" target="_blank" rel="noopener">${s.p === 'SOTA' ? 'SOTLAS' : s.p} PAGE ↗</a>${s.p === 'POTA' && s.us ? `<a href="kpc-planner-us.html?q=${encodeURIComponent(s.ref)}">ON THE MAP</a>` : ''}<a href="kpc-park-info.html?ref=${encodeURIComponent(s.ref)}">PARK INFO</a></div>
</article>`;
  }
  function draw() {
    const q = F.q.trim().toUpperCase();
    let L = SP.filter(s => passPBM(s) && (!F.hide || !WK.has(s.ref)) && (!F.nw || isNew(s)) && (!F.rg || !isFar(s))
      && (F.where === 'all' || (F.where === 'us' && s.us) || (F.where === 'usca' && (s.us || s.ca)) || (F.where === 'range' && dist(s) != null && !isFar(s)))
      && (!F.st || s.st === F.st)
      && (!q || [s.call, s.ref, s.name, s.st, ST[s.st] || '', s.loc, s.com].join(' ').toUpperCase().includes(q)));
    const srt = { new: (a, b) => (b.t || 0) - (a.t || 0), freq: (a, b) => a.khz - b.khz, mine: (a, b) => (isNew(b) - isNew(a)) || (b.t || 0) - (a.t || 0), far: (a, b) => (dist(a) ?? 1e9) - (dist(b) ?? 1e9) }[F.sort] || null;
    if (srt) L.sort(srt);
    const old = new Set([...document.querySelectorAll('#hlSpots .hs')].map(x => x.dataset.k));
    $('hlSpots').innerHTML = L.length ? L.slice(0, 240).map(card).join('') : `<div class="hl-empty">${SP.length ? 'No spots match your filters right now.' : 'No spots yet.'}</div>`;
    if (old.size) document.querySelectorAll('#hlSpots .hs.new').forEach(x => { if (!old.has(x.dataset.k)) x.classList.add('fresh'); });
    const hid = SP.length - L.length;
    $('hlCount').textContent = `${L.length} spot${L.length === 1 ? '' : 's'} shown${hid ? ` · ${hid} hidden by your filters` : ''}${hasLog() ? '' : ' · load your log to see which are new to you'}`;
    $('hsLive').textContent = SP.length; $('hlSrc').textContent = src;
  }
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-wk]'); if (!b) return;
    const r = b.dataset.wk;
    if (WK.has(r) && MAN.has(r)) { WK.delete(r); MAN.delete(r); } else if (!WK.has(r)) { WK.add(r); MAN.add(r); if (!LOG.t) LOG.t = Date.now(); }
    saveLog(); logInfo(); ticker(false); draw(); needDraw();
  });

  /* ---------------- filters ---------------- */
  function chips() {
    document.querySelectorAll('[data-g=p]').forEach(b => b.setAttribute('aria-pressed', F.p.includes(b.dataset.v)));
    $('fHide').setAttribute('aria-pressed', F.hide); $('fNew').setAttribute('aria-pressed', F.nw); $('fRange').setAttribute('aria-pressed', F.rg);
    $('fBands').innerHTML = BANDS.map(b => b[0]).concat(['OTHER']).map(b => `<button type="button" class="hl-chip" data-band="${b}" aria-pressed="${F.bands.includes(b)}">${b.toUpperCase()}</button>`).join('');
    $('fModes').innerHTML = ['PHONE', 'CW', 'DIGITAL', 'OTHER'].map(m => `<button type="button" class="hl-chip" data-mode="${m}" aria-pressed="${F.modes.includes(m)}">${m === 'PHONE' ? 'PHONE (SSB/FM)' : m}</button>`).join('');
    $('fWhere').innerHTML = WHERE.map(w => `<button type="button" class="hl-chip" data-where="${w[0]}" aria-pressed="${F.where === w[0]}">${w[1]}</button>`).join('');
    $('sBand').textContent = F.bands.length ? F.bands.join(' ').toUpperCase() : 'ALL';
    $('sMode').textContent = F.modes.length ? F.modes.join(' ') : 'ALL';
    $('sWhere').textContent = (WHERE.find(w => w[0] === F.where) || WHERE[0])[1] + (F.st ? ' · ' + F.st : '');
    $('fSt').value = F.st; $('fSort').value = F.sort; $('fQ').value = F.q;
  }
  document.addEventListener('click', e => {
    const t = e.target.closest('[data-g=p],[data-band],[data-mode],[data-where],#fHide,#fNew,#fRange'); if (!t) return;
    const tog = (a, v) => a.includes(v) ? a.filter(x => x !== v) : a.concat(v);
    if (t.dataset.g === 'p') { F.p = tog(F.p, t.dataset.v); if (!F.p.length) F.p = [t.dataset.v]; }
    else if (t.dataset.band) F.bands = tog(F.bands, t.dataset.band);
    else if (t.dataset.mode) F.modes = tog(F.modes, t.dataset.mode);
    else if (t.dataset.where) { F.where = t.dataset.where; if (F.where === 'range' && !HOME) { $('hlSetup').scrollIntoView({ behavior: 'smooth' }); $('hHome').textContent = 'Set where you are first.'; } }
    else if (t.id === 'fHide') F.hide = !F.hide; else if (t.id === 'fNew') F.nw = !F.nw; else if (t.id === 'fRange') { F.rg = !F.rg; if (F.rg && !HOME) { $('hlSetup').scrollIntoView({ behavior: 'smooth' }); $('hHome').textContent = 'Set where you are first.'; } }
    saveF(); chips(); ticker(false); draw();
  });
  $('fSt').onchange = () => { F.st = $('fSt').value; saveF(); chips(); draw(); };
  $('fSort').onchange = () => { F.sort = $('fSort').value; saveF(); draw(); };
  $('fQ').oninput = () => { F.q = $('fQ').value; saveF(); draw(); };
  document.addEventListener('click', e => { document.querySelectorAll('.hl-dd[open]').forEach(d => { if (!d.contains(e.target)) d.open = false; }); });
  document.querySelectorAll('.hl-dd').forEach(d => d.addEventListener('toggle', () => { if (d.open) document.querySelectorAll('.hl-dd[open]').forEach(o => { if (o !== d) o.open = false; }); }));

  /* ---------------- your log ---------------- */
  function logInfo() {
    const c = { POTA: 0, WWFF: 0, SOTA: 0 }; WK.forEach(r => c[progOf(r)]++);
    $('hsLog').textContent = WK.size;
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
  async function needLoad() {
    const a = $('nSt').value; $('nList').innerHTML = '<div class="hl-empty">Loading ' + esc(ST[a]) + '’s parks…</div>'; NP = []; nShown = 120;
    try { const L = await jget('https://api.pota.app/location/parks/US-' + a); NP = (L || []).map(p => ({ r: nref(p.reference), n: p.name, a: +p.activations || 0, la: +p.latitude, lo: +p.longitude })); nSrc = 'POTA'; }
    catch (e) { await loadParks(); NP = Object.entries(PK).filter(([r, k]) => k.st === a && /^US-/.test(r)).map(([r, k]) => ({ r, n: k.n, a: k.a })); nSrc = 'KPC copy'; }
    needDraw();
  }
  function needDraw() {
    if (!NP.length) return;
    const a = $('nSt').value, q = $('nQ').value.trim().toUpperCase(), air = new Map(SP.filter(s => s.p === 'POTA').map(s => [s.ref, s]));
    const done = NP.filter(p => WK.has(p.r)).length, pct = Math.round(done / NP.length * 100);
    $('nBar').innerHTML = `<div class="bar"><i style="width:${pct}%"></i></div><p><b>${done}</b> of <b>${NP.length}</b> ${esc(ST[a])} parks worked (${pct}%) · <b>${NP.length - done}</b> still to go${hasLog() ? '' : ' · load your log in Step 1 to see yours'}</p>`;
    let L = NP.filter(p => !WK.has(p.r) && (!q || (p.r + ' ' + p.n).toUpperCase().includes(q)) && (!$('nAir').checked || air.has(p.r)));
    const s = $('nSort').value;
    L.sort(s === 'name' ? (x, y) => x.n.localeCompare(y.n) : s === 'ref' ? (x, y) => x.r.localeCompare(y.r, undefined, { numeric: true }) : s === 'busy' ? (x, y) => y.a - x.a : (x, y) => (x.a - y.a) || x.n.localeCompare(y.n));
    L.sort((x, y) => air.has(y.r) - air.has(x.r));
    $('nList').innerHTML = L.length ? L.slice(0, nShown).map(p => { const o = air.get(p.r); return `<div class="hn${o ? ' air' : ''}"><a class="r" href="https://pota.app/#/park/${encodeURIComponent(p.r)}" target="_blank" rel="noopener">${esc(p.r)}</a>${esc(p.n)}<div class="m">${p.a ? p.a + ' activation' + (p.a === 1 ? '' : 's') : 'never activated'}${p.a > 0 && p.a <= 5 ? ' · RARE' : ''} · <a href="kpc-planner-us.html?q=${encodeURIComponent(p.r)}">map</a></div>${o ? `<div class="air">📡 ON THE AIR: ${esc(o.call)} ${(o.khz / 1000).toFixed(3)} ${esc(o.mode)}</div>` : ''}</div>`; }).join('')
      + (L.length > nShown ? `<div class="hl-row" style="grid-column:1/-1"><button type="button" class="hl-btn line sm" id="nMore">SHOW MORE (${L.length - nShown} left)</button></div>` : '')
      : `<div class="hl-empty">${q || $('nAir').checked ? 'None match.' : '🎉 You’ve worked every park in ' + esc(ST[a]) + '!'}</div>`;
    const m = $('nMore'); if (m) m.onclick = () => { nShown += 200; needDraw(); };
  }
  $('nSt').onchange = () => { $('nSt').dataset.set = 1; needLoad(); };
  $('nQ').oninput = needDraw; $('nSort').onchange = needDraw; $('nAir').onchange = needDraw;

  /* ---------------- top activators + my numbers ---------------- */
  let TT = 'acts', TD = {};
  async function topDraw() {
    const a = $('tSt').value;
    if (!TD[a]) { $('tList').innerHTML = '<div class="hl-empty">Loading…</div>'; TD[a] = await fetch('data/leaders/US-' + a + '.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null) || { none: 1 }; }
    const d = TD[a];
    if (d.none) { $('tList').innerHTML = `<div class="hl-empty">${esc(ST[a])}’s list is still being added up. It fills in within a week.</div>`; $('tSrc').textContent = ''; return; }
    const L = d[TT] || [], me = CALL ? L.findIndex(r => r[0] === CALL) : -1;
    const row = (r, i) => `<div class="ht${r[0] === CALL ? ' me' : ''}"><span class="n">${i + 1}</span><span class="c"><a href="https://www.qrz.com/db/${encodeURIComponent(r[0])}" target="_blank" rel="noopener">${esc(r[0])}</a></span><span class="v">${(TT === 'acts' ? r[1] : r[2]).toLocaleString()}<small>${TT === 'acts' ? 'ACTIVATIONS' : 'PARKS'}</small></span><span class="v">${(TT === 'acts' ? r[2] : r[1]).toLocaleString()}<small>${TT === 'acts' ? 'PARKS' : 'ACTIVATIONS'}</small></span></div>`;
    $('tList').innerHTML = L.slice(0, 20).map(row).join('') + (me >= 20 ? row(L[me], me) : '') || '<div class="hl-empty">No activations yet.</div>';
    $('tSrc').innerHTML = `${esc(ST[a])}: ${d.activators.toLocaleString()} activators across ${d.activated.toLocaleString()} activated parks (${d.parks.toLocaleString()} parks in all). Added up by KPC from POTA’s public activation lists (10+ contacts counts, calls like K4TEST/P count as K4TEST). Updated ${esc(d.updated)}, weekly.${CALL && me < 0 ? ` ${esc(CALL)} isn’t in this state’s top 50 yet.` : ''}`;
  }
  document.addEventListener('click', e => { const b = e.target.closest('[data-t]'); if (!b) return; TT = b.dataset.t; document.querySelectorAll('[data-t]').forEach(x => x.setAttribute('aria-pressed', x === b)); topDraw(); });
  $('tSt').onchange = topDraw;
  async function myStats() {
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
  stick(); addEventListener('resize', stick); addEventListener('scroll', () => { if (!stq) stq = requestAnimationFrame(stick); }, { passive: true }); setInterval(stick, 400);
  /* ---------------- start ---------------- */
  const home0 = (HOME && HOME.label && (HOME.label.match(/middle of (.+)$/) || [])[1]) || '';
  const st0 = Object.keys(ST).find(k => ST[k] === home0) || 'KY';
  $('fSt').innerHTML = '<option value="">Any state</option>' + stOpts('');
  $('hSt').innerHTML = '<option value="">…or pick your state</option>' + stOpts('');
  $('nSt').innerHTML = stOpts(st0); $('tSt').innerHTML = stOpts(st0);
  chips(); bell(); logInfo(); homeInfo();
  load(); needLoad(); topDraw(); myStats();
  setInterval(() => { const s = Math.max(0, Math.round((next - Date.now()) / 1000)); $('hsAge').textContent = next ? s + 's' : '–'; if (next && Date.now() >= next) { next = 0; load(); } }, 1000);
  setInterval(() => { document.querySelectorAll('.hs').length && draw(); }, 5 * 60e3);
  window.KPCHunt = { scan, nref };
})();
