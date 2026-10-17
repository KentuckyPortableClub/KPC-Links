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
    if (!hasLog()) { T.innerHTML = '<span class="hl-wait">Load your log (Step 1 below) and new-to-you parks will roll across here.</span>'; T.style.setProperty('--dur', '22s'); $('hlFar').hidden = true; naDraw(); return; }
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
    naDraw();
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
 <div class="hs-a"><button type="button" class="lg" data-log="1">📝 LOG IT</button><button type="button" class="wk${w ? ' on' : ''}" data-wk="${esc(s.ref)}">${w ? '✓ WORKED' : '＋ I WORKED IT'}</button><a href="${pageOf(s)}" target="_blank" rel="noopener">${s.p === 'SOTA' ? 'SOTLAS' : s.p} PAGE ↗</a>${s.p === 'POTA' && s.us ? `<a href="kpc-planner-us.html?q=${encodeURIComponent(s.ref)}">ON THE MAP</a>` : ''}<a href="kpc-park-info.html?ref=${encodeURIComponent(s.ref)}">PARK INFO</a></div>
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
        + af('STATE', /^[A-Z]{2}$/.test(q.st || '') && ST[q.st] ? q.st : '') + af('COMMENT', [refs.join(' '), q.name].filter(Boolean).join(' ').slice(0, 120)) + af('NOTES', q.note) + '<EOR>\n';
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
  function toast(msg, undo) {
    let t = document.querySelector('.hl-toast'); if (!t) { t = document.createElement('div'); t.className = 'hl-toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.innerHTML = esc(msg) + (undo ? '<button type="button">UNDO</button>' : ''); t.hidden = false;
    if (undo) t.querySelector('button').onclick = () => { undo(); t.hidden = true; };
    clearTimeout(tT); tT = setTimeout(() => { t.hidden = true; }, undo ? 7000 : 3500);
  }
  /* tapping a spot card (not its links/buttons) opens the log with everything filled in */
  document.addEventListener('click', e => {
    const lg = e.target.closest('[data-log]');
    const c = lg ? lg.closest('.hs') : (!e.target.closest('a,button,input,select,label') && e.target.closest('#hlSpots .hs'));
    if (!c) return; const s = SP.find(x => x.p + '|' + x.call + '|' + x.ref === c.dataset.k); if (s) openSheet(s);
  });

  /* ---------------- looks (Brandon Oct 16: switchable themes; Cabin Lodge = his pictures) ---------------- */
  let THEME = get('kpcHuntTheme', 'lodge');
  function theme() { $('hl').dataset.theme = THEME; document.querySelectorAll('[data-theme-pick]').forEach(b => b.setAttribute('aria-pressed', b.dataset.themePick === THEME)); }
  document.addEventListener('click', e => { const b = e.target.closest('[data-theme-pick]'); if (!b) return; THEME = b.dataset.themePick; put('kpcHuntTheme', THEME); theme(); });
  theme();

  /* ---------------- mini North America map in the ticker ---------------- */
  const NA = {"124":"M171 122L178 123L181 128L185 129L187 133L179 131L181 129L178 130L174 128L173 125L170 125L168 123L170 122L167 122ZM160 96L160 94L153 92L139 76L130 80L123 75L124 73L116 73L116 27L123 27L139 32L136 30L138 30L137 28L144 27L143 29L162 24L148 29L146 31L150 31L150 29L165 26L169 24L167 23L169 22L176 28L179 28L182 24L184 27L182 28L195 26L207 30L222 31L224 34L219 34L219 36L244 36L250 43L249 40L251 41L251 39L248 36L257 32L251 34L245 34L247 32L256 30L262 35L266 34L274 37L286 35L291 37L291 35L286 35L285 33L289 32L294 33L293 35L296 34L295 39L297 38L298 40L294 40L297 42L296 40L299 40L297 36L306 32L305 30L302 31L303 28L306 28L296 26L294 19L302 15L314 24L310 24L312 25L308 27L318 27L315 29L318 30L319 34L321 30L327 30L329 33L327 33L327 36L330 39L334 38L338 31L341 31L338 29L338 26L355 29L352 30L355 32L350 33L355 38L354 40L347 43L340 40L345 44L333 42L336 45L332 48L314 45L332 49L328 54L320 54L319 57L305 54L306 56L315 57L317 60L310 61L312 62L310 62L310 64L307 63L308 65L306 65L301 72L300 80L303 81L303 84L304 81L307 81L310 88L309 90L319 89L337 97L339 100L344 98L350 99L353 114L358 117L357 119L359 118L363 121L361 118L365 118L366 112L361 102L369 99L374 94L373 87L366 82L366 80L371 77L370 71L367 71L370 67L367 64L370 62L377 64L387 63L389 66L394 67L394 69L402 70L402 74L397 75L401 75L401 78L403 78L400 82L405 80L407 82L407 84L404 85L407 85L407 83L409 83L409 85L414 81L416 83L421 73L421 75L426 78L424 80L429 82L426 83L430 83L427 85L432 85L430 88L435 90L435 92L430 91L433 92L434 95L439 96L438 100L441 98L441 101L444 99L450 102L438 107L439 109L447 104L450 104L451 108L453 106L457 108L457 112L455 112L457 112L457 114L454 117L446 118L440 124L414 124L402 134L396 133L401 135L394 142L383 147L384 148L375 153L373 157L364 157L364 161L349 167L347 164L351 159L350 148L347 147L346 144L344 145L344 142L342 143L340 140L326 133L324 135L314 135L301 131L301 128L299 128L299 130L188 130L187 127L184 128L184 126L186 127L184 126L185 124L184 126L180 124L181 121L176 123L174 122L176 121L174 122L174 120L169 119L173 117L171 116L169 118L169 114L173 114L171 113L172 111L168 116L167 115L168 110L166 111L166 109L163 108L165 106L164 107L168 109L165 105L162 109L159 107L160 104L162 104L158 103L162 98L161 97L160 100ZM218 -12L215 -11L217 -10L215 -10L216 -8L212 -8L211 -6L208 -7L209 -9L205 -8L205 -6L202 -7L200 -4L197 -6L188 -6L204 -12ZM247 -5L252 -3L253 -5L258 -5L256 0L230 3L223 1L236 -1L225 0L226 -2L224 -2L222 0L215 0L210 -2L220 -3L211 -3L220 -4L213 -5L221 -6L217 -6L221 -8L235 -3L244 -3L239 -7L246 -9ZM222 12L230 10L235 11L233 14L239 12L237 10L240 10L244 11L249 17L251 16L248 13L248 8L258 10L263 18L262 20L276 24L276 27L266 27L268 29L272 28L273 30L264 31L253 28L242 32L227 33L225 29L214 28L211 24L233 24L206 20L219 18L207 18L209 17L204 16L207 12L221 8L224 9ZM201 4L212 4L218 8L203 12L196 18L187 19L177 15L185 6L181 3L195 2ZM402 -40L414 -40L407 -38L420 -40L435 -36L405 -31L421 -32L402 -27L397 -28L399 -26L392 -26L397 -26L396 -24L381 -24L386 -24L386 -22L372 -23L382 -20L366 -20L382 -18L374 -18L379 -17L377 -15L368 -15L367 -12L360 -11L353 -13L355 -12L352 -11L363 -11L368 -8L356 -6L350 -9L351 -7L326 -7L326 -9L326 -7L322 -7L322 -9L326 -11L333 -11L328 -14L346 -12L350 -15L341 -12L338 -15L342 -16L340 -16L341 -18L335 -15L336 -17L330 -16L333 -19L353 -20L342 -20L346 -20L334 -24L335 -27L360 -23L348 -27L373 -29L365 -30L372 -32L356 -28L334 -28L347 -31L328 -28L323 -30L340 -31L321 -30L323 -31L321 -32L330 -33L318 -32L321 -33L314 -34L340 -35L334 -36L338 -37L362 -34L350 -37L357 -38L355 -39L365 -38L359 -40L374 -38L378 -38L371 -40ZM280 5L292 6L286 10L294 11L294 16L286 16L287 18L281 16L269 11L279 11L278 9L281 9L274 7L278 8L276 6ZM340 49L343 48L351 51L353 53L352 55L358 55L356 58L348 54L346 55L341 59L338 59L337 56L331 57L335 55L336 46L338 45ZM289 -7L290 -4L288 -4L291 -2L289 -3L288 0L279 0L277 -2L283 -3L269 -3L276 -4L272 -7L279 -5L282 -6L278 -6L280 -7L277 -8ZM266 -22L270 -19L276 -20L282 -18L283 -14L270 -16L260 -17L267 -19L260 -19L258 -22ZM312 -31L317 -28L323 -28L323 -26L329 -27L328 -25L332 -25L331 -23L338 -23L340 -21L330 -18L327 -20L328 -17L325 -18L325 -16L320 -18L322 -16L312 -16L309 -17L313 -18L306 -19L303 -20L315 -22L300 -21L297 -23L302 -24L297 -23L293 -26L302 -25L295 -26L298 -27L296 -27L296 -29L304 -28L298 -29L307 -30L303 -32ZM303 -10L307 -9L306 -7L323 -7L314 -6L321 -5L323 -4L321 -3L324 -2L343 -4L360 -3L359 -2L362 -1L358 0L362 1L359 0L359 2L352 3L346 0L346 2L337 3L326 3L327 1L313 2L312 -1L310 -1L312 -4L308 -7L299 -6L292 -9ZM307 4L319 6L312 11L303 11L306 13L299 15L297 7L301 7L299 5L302 4ZM412 149L409 147L409 140L403 138L397 149L381 150L386 148L391 142L398 140L406 132L414 129L423 130L423 133L413 135L417 135L417 137L421 136L420 138L419 140L421 140L422 144L435 147L436 149L427 151L426 153L423 152L419 157L415 156L417 152L415 153L422 148L423 150L427 148L420 148L423 146L421 145L419 148ZM458 117L453 127L455 124L458 125L455 127L459 127L459 130L462 127L466 128L463 131L465 131L464 133L468 132L465 137L469 134L467 136L467 138L469 136L468 142L466 142L466 140L463 141L464 136L458 141L456 140L461 137L443 137L447 132L443 132L448 130L447 128L449 128L450 122L453 118ZM334 20L341 20L341 17L336 15L343 15L337 12L338 10L343 11L338 9L349 6L358 9L359 11L355 13L358 13L356 15L363 13L366 16L365 13L370 14L366 12L372 11L380 13L376 16L380 14L383 15L379 16L381 17L380 19L384 16L383 18L386 17L387 19L387 17L393 17L395 19L389 21L397 19L396 22L392 23L395 22L394 24L398 21L404 21L407 23L400 25L407 25L408 23L411 25L403 27L413 29L403 31L413 33L412 35L415 34L414 36L418 35L418 37L421 35L425 37L421 38L428 39L425 41L433 40L435 42L430 43L432 45L429 47L426 46L426 50L418 46L422 43L416 45L411 42L408 43L411 45L405 44L411 47L413 51L415 50L420 53L418 54L422 56L422 59L419 56L421 61L419 60L419 62L409 56L409 58L404 56L414 62L416 66L395 60L392 58L394 57L387 54L387 52L384 53L380 51L381 53L371 54L367 52L370 48L377 49L378 51L377 48L386 48L382 44L391 38L387 33L384 33L385 31L382 32L378 30L374 32L377 28L371 27L373 26L364 22L362 23L365 24L363 26L325 23L322 20L331 20L320 17L323 9L329 6L340 6L333 11L335 16L340 18ZM362 7L375 9L376 11L369 11L360 11L357 6Z","304":"M480 63L480 60L478 61L474 57L474 55L479 54L473 54L475 52L480 53L480 51L476 49L477 51L472 54L470 48L476 46L470 48L466 45L475 41L465 44L470 40L464 39L469 36L478 37L465 37L467 34L474 35L475 33L466 34L470 31L476 32L475 30L479 29L476 29L479 25L463 23L462 21L477 23L473 20L476 20L468 19L469 17L473 17L466 17L467 15L465 13L466 16L464 18L458 18L457 16L461 13L457 14L458 12L460 13L461 10L457 10L459 8L457 8L455 4L451 4L455 2L447 -1L445 -4L428 -7L407 -5L402 -7L408 -8L395 -10L405 -12L415 -11L415 -13L403 -12L389 -16L390 -18L418 -21L423 -26L412 -25L412 -27L421 -30L428 -29L427 -31L435 -31L435 -34L438 -35L454 -32L443 -35L463 -37L466 -33L468 -37L476 -34L479 -35L476 -37L480 -37Z","484":"M211 212L221 211L234 218L254 216L266 230L268 230L270 226L274 226L282 237L283 242L291 245L289 253L289 264L291 268L289 265L289 267L297 282L299 281L303 284L312 281L314 283L319 269L332 267L333 271L329 277L329 284L327 281L323 286L316 286L316 289L314 289L318 295L313 295L311 302L304 294L301 294L294 297L276 289L273 285L269 285L260 278L257 273L259 272L257 262L250 252L242 246L243 243L244 244L243 242L233 233L229 226L228 219L225 217L220 215L221 224L229 233L232 241L234 241L237 253L242 257L240 261L239 257L231 250L232 246L227 240L225 241L220 236L224 237L224 233L217 226Z","840":"M160 96L158 101L156 100L156 95L151 97L154 94L146 89L145 87L148 87L144 85L144 82L143 84L141 83L139 78L140 84L136 83L136 80L132 80L136 82L133 84L122 78L122 75L123 77L122 75L115 76L115 74L103 75L101 72L94 72L93 70L95 69L89 71L88 69L86 70L87 72L85 73L88 72L86 75L82 74L82 76L72 79L76 76L73 76L75 71L84 71L80 69L83 68L82 67L73 70L68 74L69 76L63 79L67 80L66 82L46 93L46 95L37 98L33 97L27 101L31 96L39 96L39 93L45 91L48 87L50 88L50 82L53 79L48 82L46 81L48 80L45 80L45 83L41 80L31 82L33 79L30 74L32 72L30 75L23 76L19 72L26 72L24 71L26 70L18 70L17 67L15 67L18 66L18 63L22 62L22 59L28 60L31 57L35 58L37 55L34 52L37 51L19 53L12 49L15 48L8 46L21 42L25 42L25 45L33 45L36 43L32 43L30 40L34 43L39 42L25 39L13 33L15 31L25 30L32 23L40 22L41 24L41 21L48 21L53 18L58 19L55 20L56 21L67 20L72 23L107 24L116 27L116 73L124 73L123 75L130 80L139 76L153 92L160 94ZM381 150L397 149L400 141L403 138L407 138L412 151L406 152L406 154L405 152L404 155L399 156L397 159L398 162L396 163L398 166L400 165L400 167L397 166L395 168L394 166L394 168L385 171L384 169L382 179L380 180L378 176L380 175L378 176L380 183L377 189L377 183L375 183L375 178L377 177L374 178L373 183L375 185L371 182L375 185L375 187L372 185L375 187L374 189L373 187L375 190L371 189L376 190L378 196L376 192L377 194L373 194L376 195L376 197L377 195L376 198L372 197L374 198L372 200L375 200L370 201L360 212L357 212L358 214L357 213L354 218L354 224L360 240L359 248L355 249L352 240L349 238L349 230L344 224L338 227L338 224L332 222L330 224L328 224L328 222L319 223L319 225L323 225L321 227L324 230L319 227L320 229L315 229L315 227L311 226L305 225L302 228L300 226L297 232L295 233L296 232L293 231L294 233L291 234L289 238L290 246L283 242L282 237L274 226L270 226L269 229L266 230L254 216L234 218L221 211L211 212L208 206L198 203L197 198L190 189L190 186L192 188L190 185L194 185L188 185L183 174L184 167L182 160L184 144L187 144L184 144L185 140L183 140L181 133L189 134L187 138L190 135L190 139L188 139L191 138L189 130L299 130L299 128L301 128L301 131L314 135L324 135L326 133L340 140L342 143L344 142L344 145L346 144L346 146L350 148L351 159L347 164L349 167L364 161L364 157L373 157L375 153Z"};
  const PX = lo => ((lo + 170) * 4).toFixed(1), PY = la => ((75 - la) * 5).toFixed(1);
  function naDraw() {
    const sv = $('hlNaSvg'); if (!sv) return;
    const land = Object.entries(NA).map(([k, d]) => `<path class="land${k === '840' ? ' us' : ''}" d="${d}"/>`).join('');
    const on = s => isFinite(s.la) && isFinite(s.lo) && s.lo > -170 && s.lo < -50 && s.la > 14 && s.la < 75;
    const other = SP.filter(s => on(s) && !isNew(s)).map(s => `<circle class="sp" cx="${PX(s.lo)}" cy="${PY(s.la)}" r="3"/>`).join('');
    const nw = SP.filter(s => on(s) && isNew(s) && passPBM(s)).map(s => `<circle class="${FAR && HOME && isFar(s) ? 'fr' : 'nw'}" cx="${PX(s.lo)}" cy="${PY(s.la)}" r="7"><title>${esc(s.ref + ' ' + (s.name || '') + ' · ' + s.call)}</title></circle>`).join('');
    const hm = HOME ? `<circle class="home" cx="${PX(HOME.lo)}" cy="${PY(HOME.la)}" r="8"/>` : '';
    sv.innerHTML = land + other + nw + hm;
  }
  $('hlNa').onclick = () => $('hlNa').classList.toggle('big');
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { $('hlNa').classList.remove('big'); closeSheet(); } });

  /* ---------------- start (after the password) ---------------- */
  function startApp() {
    $('hlLock').hidden = true; $('hlApp').hidden = false;
    const home0 = (HOME && HOME.label && (HOME.label.match(/middle of (.+)$/) || [])[1]) || '';
    const st0 = Object.keys(ST).find(k => ST[k] === home0) || 'KY';
    $('fSt').innerHTML = '<option value="">Any state</option>' + stOpts('');
    $('hSt').innerHTML = '<option value="">…or pick your state</option>' + stOpts('');
    $('nSt').innerHTML = stOpts(st0); $('tSt').innerHTML = stOpts(st0);
    stick();
    chips(); bell(); logInfo(); homeInfo(); qsoInit();
    load(); needLoad(); topDraw(); myStats();
    setInterval(() => { const s = Math.max(0, Math.round((next - Date.now()) / 1000)); $('hsAge').textContent = next ? s + 's' : '–'; if (next && Date.now() >= next) { next = 0; load(); } }, 1000);
    setInterval(() => { document.querySelectorAll('.hs').length && draw(); }, 5 * 60e3);
  }
  /* simple password lock, same password as the Map Rep Tool Box (keeps casual visitors out; not bank-grade security) */
  const HASH = 'b36efa5ab2718f715ea105ece66b600d914fb0be36ee52de48363e5727d92b73';
  const sha = async t => { const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join(''); };
  let unlocked = false; try { unlocked = localStorage.getItem('kpcHuntOK') === HASH; } catch (e) {}
  if (unlocked) startApp();
  else $('hlLockForm').addEventListener('submit', async e => {
    e.preventDefault();
    const h = await sha('kpc-maprep:' + $('hlPw').value.trim().toLowerCase());
    if (h === HASH) { try { localStorage.setItem('kpcHuntOK', HASH); } catch (x) {} startApp(); }
    else { $('hlPwMsg').textContent = 'That password is not right.'; $('hlPw').select(); }
  });
  window.KPCHunt = { scan, nref, adif, parseAdif };
})();
