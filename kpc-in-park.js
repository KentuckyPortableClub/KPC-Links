/* KPC "Am I in the Park?" (kpc-in-park.html). Uses kpc-bounds.js (window.KPCB).
   GPS (or a tap on the map) -> which official boundaries the spot is inside, how far to the edge, which POTA / WWFF references, and (SOTA) how high you are below a nearby summit.
   ?ref=US-1234 checks against one park; ?lat=&lon= checks a spot. */
(function () {
  'use strict';
  const B = window.KPCB, $ = id => document.getElementById(id), esc = B.esc;
  const st = { here: null, area: null, target: null, watch: null, busy: false, osm: null, osmAt: null, last: 0 };
  let map = null, lay = null, me = null, accC = null, line = null;

  function initMap(la, lo, z) {
    if (map) return;
    map = L.map('ipMap', { zoomControl: true }).setView([la, lo], z || 7);
    const street = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' });
    const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19, attribution: 'Imagery © Esri' });
    street.addTo(map); L.control.layers({ Street: street, Satellite: sat }).addTo(map);
    map.on('click', e => { stopWatch(); check(e.latlng.lat, e.latlng.lng, 0, 'map'); });
  }
  const say = (cls, h) => { $('ipV').className = 'ip-v ' + cls; $('ipV').innerHTML = h; };

  /* ---------- gather boundaries around a spot (network), then judge locally ---------- */
  async function gather(la, lo) {
    const feats = [], A = { la, lo, feats, pota: [], padusOk: false, kyOk: false };
    const jobs = [];
    if (B.inKY(la, lo)) jobs.push(B.ky().then(F => { A.kyOk = true; F.forEach(f => { const b = f._bb; if (lo > b[0] - .1 && lo < b[2] + .1 && la > b[1] - .1 && la < b[3] + .1) feats.push({ src: f._L.kpc ? 'kpc' : 'ky', f }); }); }).catch(() => {}));
    jobs.push(B.padusArea(la, lo, 0.03).then(F => { A.padusOk = true; F.forEach(f => feats.push({ src: 'padus', f })); }).catch(() => {}));
    jobs.push(B.potaNear(la, lo, 0.3).then(P => { A.pota = P; }).catch(() => {}));
    A.wwff = []; A.sota = [];
    jobs.push(B.wwffNear(la, lo, 25).then(W => { A.wwff = W; }).catch(() => {}));
    jobs.push(B.sotaNear(la, lo, 6).then(S => { A.sota = S; }).catch(() => {}));
    await Promise.all(jobs);
    if (B.inKY(la, lo) && B.kyData()) { const K = B.kyData().parks.map(p => ({ ref: p.c, name: p.n, la: p.la, lo: p.lo })); A.pota = A.pota.concat(K.filter(k => !A.pota.some(p => p.ref === k.ref))); }
    return A;
  }
  /* every program reference a boundary belongs to: POTA parks and WWFF areas, [{ref, name, prog}] */
  function refsOf(x) {
    if (x.src === 'osm') return [];
    const P = (x.src !== 'padus' ? B.kyRefs(x.f) : B.refsFor(x.f, st.area.pota)).map(r => Object.assign({ prog: 'POTA' }, r));
    const W = new Map(), KD = B.kyData();
    if (KD && x.src !== 'padus') { P.forEach(r => { const pk = KD.parks.find(q => q.c === r.ref); (pk && pk.kff || []).forEach(k => { const kk = KD.kff.find(q => q.c === k); W.set(k, { ref: k, name: kk ? kk.n : '', prog: 'WWFF' }); }); }); }
    const small = !(x.f.properties && +x.f.properties.GIS_Acres > 60000) && !(x.f._L && (x.f._L.proc || x.f._L.k === 'bwilder'));
    (st.area.wwff || []).forEach(w => { if (W.has(w.ref)) return; if (B.sameName(w.name, x.f._nm) || P.some(r => B.sameName(w.name, r.name)) || (small && x.f.properties.Category !== 'Easement' && B.inside(w.la, w.lo, x.f.geometry))) W.set(w.ref, { ref: w.ref, name: w.name, prog: 'WWFF' }); });
    return P.concat([...W.values()]);
  }
  const spotQ = r => (r.prog === 'WWFF' ? 'wwff=' : r.prog === 'SOTA' ? 'sota=' : 'pota=') + encodeURIComponent(r.ref);
  const acres = p => p && p.GIS_Acres ? ' · ' + Math.round(+p.GIS_Acres).toLocaleString() + ' acres' : '';
  function label(x) {
    const p = x.f.properties || {};
    if (x.src === 'padus') return { name: x.f._nm, what: (p.Loc_Mang || p.Mang_Name || 'public land') + (p.Des_Tp ? ' · ' + p.Des_Tp : '') + acres(p), src: 'Official (USGS PAD-US)', access: p.Pub_Access, ease: p.Category === 'Easement' };
    if (x.src === 'osm') return { name: x.f._nm, what: x.f._op || 'OpenStreetMap outline', src: 'OpenStreetMap (NOT official)' };
    return { name: x.f._nm, what: x.f._L.name + ' · ' + x.f._L.agency, src: x.src === 'kpc' ? 'KPC-drawn outline (approximate, not official)' : 'Official (' + x.f._L.agency + ')', note: x.f._L.note, proc: x.f._L.proc };
  }

  /* ---------- judge ---------- */
  async function check(la, lo, acc, how, alt) {
    st.here = { la, lo, acc: acc || 0, how, alt: isFinite(alt) && alt !== null ? alt : null };
    initMap(la, lo, 14);
    const far = !st.area || B.km(la, lo, st.area.la, st.area.lo) > 1.2;
    if (far && !st.busy) {
      st.busy = true; say('wait', 'Checking the official boundaries around you…');
      try { st.area = await gather(la, lo); } finally { st.busy = false; }
    }
    if (!st.area) return;
    judge();
  }
  function judge() {
    const { la, lo, acc, how } = st.here, A = st.area, accKm = (acc || 0) / 1000, margin = Math.max(accKm, 0.012);
    let rows = A.feats.map(x => Object.assign({}, x, { in: B.inside(la, lo, x.f.geometry), e: B.edge(la, lo, x.f.geometry) }));
    const T = st.target;
    if (T && T.feats) rows = rows.concat(T.feats.filter(f => !A.feats.some(x => x.f === f)).map(f => ({ src: f._L ? (f._L.kpc ? 'kpc' : 'ky') : 'padus', f, tgt: true, in: B.inside(la, lo, f.geometry), e: B.edge(la, lo, f.geometry) })));
    rows.forEach(r => { r.L = label(r); r.refs = refsOf(r); });
    const hits = rows.filter(r => r.in).sort((a, b) => (b.refs.length > 0) - (a.refs.length > 0) || ((a.f._bb[2] - a.f._bb[0]) * (a.f._bb[3] - a.f._bb[1])) - ((b.f._bb[2] - b.f._bb[0]) * (b.f._bb[3] - b.f._bb[1])));
    const near = rows.filter(r => !r.in && r.e.km < 8).sort((a, b) => a.e.km - b.e.km);
    const good = r => !r.L.proc && !r.L.ease && r.L.access !== 'XA';
    const progHits = hits.filter(r => r.refs.length && good(r));
    const fsLand = hits.some(r => r.src === 'padus' && /Forest Service|USFS/i.test((r.f.properties.Loc_Mang || '') + (r.f.properties.Mang_Name || '')) && !r.L.ease);
    const accTxt = how === 'map' ? 'Spot you tapped on the map.' : acc ? `Your GPS is good to about ±${B.dist(accKm)}.` : '';
    const btns = refs => refs.map(r => `<div class="ip-ref"><b>${esc(r.ref)}</b> ${esc(r.name)}<span><a href="kpc-spot-me.html?pota=${encodeURIComponent(r.ref)}">SPOT ME ›</a><a href="kpc-park-info.html?q=${encodeURIComponent(r.ref)}">PARK INFO ›</a></span></div>`).join('');
    const uniq = list => { const m = new Map(); list.forEach(r => r.refs.forEach(x => m.set(x.ref, x))); return [...m.values()]; };
    let v;
    if (T && T.prog === 'SOTA') {
      v = ['wait', `<div class="ip-t">Checking: <b>${esc(T.ref)} ${esc(T.name)}</b></div><h2>CHECKING YOUR HEIGHT…</h2>`];
    } else if (T) {
      const th = rows.filter(r => r.in && (r.tgt || r.refs.some(x => x.ref === T.ref))), tn = rows.filter(r => !r.in && (r.tgt || r.refs.some(x => x.ref === T.ref))).sort((a, b) => a.e.km - b.e.km);
      const head = `<div class="ip-t">Checking: <b>${esc(T.ref)} ${esc(T.name)}</b></div>`;
      if (!th.length && !tn.length) v = ['maybe', head + `<h2>NO OFFICIAL BOUNDARY FOUND</h2><p>We could not find a boundary file for ${esc(T.ref)}. Use the park's own map. ${T.la ? `Its ${esc(T.prog)} pin is about <b>${B.dist(B.km(la, lo, T.la, T.lo))}</b> ${B.dir(la, lo, T.la, T.lo)} of you.` : ''}</p>`];
      else if (th.length) { const best = th.sort((a, b) => b.e.km - a.e.km)[0]; v = best.e.km > margin && good(best) ? ['yes', head + `<h2>✓ YOU'RE INSIDE</h2><p>About <b>${B.dist(best.e.km)}</b> from the nearest boundary line (${esc(best.L.src)}).</p>`] : ['edge', head + `<h2>ON THE EDGE</h2><p>You're inside, but only about <b>${B.dist(best.e.km)}</b> from the line${best.e.km <= accKm ? ', closer than your GPS can tell' : ''}. Move farther in to be sure.</p>`]; }
      else { const n = tn[0]; v = ['no', head + `<h2>✕ NOT INSIDE</h2><p>The boundary is about <b>${B.dist(n.e.km)}</b> to the <b>${B.dir(la, lo, n.e.lat, n.e.lon)}</b>.${n.e.km <= accKm ? ' That is within your GPS error, so move a bit and check again.' : ''}</p>`]; }
    } else if (progHits.length) {
      const per = new Map(); progHits.forEach(r => r.refs.forEach(x => { const o = per.get(x.ref); if (!o || r.e.km > o.km) per.set(x.ref, { x, km: r.e.km, kpc: r.src === 'kpc' }); }));
      const P = [...per.values()], edgy = P.filter(o => o.km <= margin);
      const rows2 = P.map(o => `<div class="ip-ref"><b>${esc(o.x.ref)}</b> ${esc(o.x.name)} <i class="ip-p">${esc(o.x.prog)}</i> <em>${o.km <= margin ? '⚠ only ' + B.dist(o.km) + ' from its edge' : B.dist(o.km) + ' from its edge'}${o.kpc ? ' (KPC-drawn outline, approximate)' : ''}</em><span><a href="kpc-spot-me.html?${spotQ(o.x)}">SPOT ME ›</a><a href="kpc-park-info.html?q=${encodeURIComponent(o.x.ref)}">INFO ›</a></span></div>`).join('');
      v = edgy.length === P.length ? ['edge', `<h2>ON THE EDGE</h2><p>You look inside, but you're very close to the line${accKm && edgy.some(o => o.km <= accKm) ? ', closer than your GPS can tell' : ''}. Move farther in to be sure.</p>${rows2}`]
        : ['yes', `<h2>✓ YOU'RE INSIDE</h2><p>${P.length > 1 ? 'These references all count from this spot:' : 'This reference counts from this spot:'}</p>${edgy.length ? '<p>⚠ You are right on the edge of ' + edgy.map(o => esc(o.x.ref)).join(', ') + ', so that one may not count from here.</p>' : ''}${rows2}`];
    } else if (hits.some(r => r.L.proc) && !fsLand) {
      v = ['maybe', `<h2>CHECK THE LAND OWNER</h2><p>You're inside Daniel Boone National Forest's outer line, but the national land database does not show this exact spot as Forest Service land. It may be private land inside the forest. Check the Forest Service map.${A.padusOk ? '' : ' (We could not reach the national land database just now, so try again with signal.)'}</p>`];
    } else if (hits.length) {
      const h = hits[0];
      v = ['maybe', `<h2>PUBLIC LAND, BUT NO PARK REFERENCE MATCHED</h2><p>You're inside <b>${esc(h.L.name)}</b> (${esc(h.L.what)}), but we could not match it to a POTA or WWFF reference. Look it up on pota.app or wwff.co before you count it.${h.L.access === 'XA' ? ' <b>The database lists this land as closed to the public.</b>' : ''}</p>`];
    } else {
      const n = near.find(r => r.refs.length) || near[0];
      v = ['no', `<h2>✕ NOT INSIDE A PARK OR WWFF AREA</h2>${n ? `<p>Nearest: <b>${esc(n.L.name)}</b>${n.refs.length ? ' (' + n.refs.map(r => esc(r.ref)).join(', ') + ')' : ''}, about <b>${B.dist(n.e.km)}</b> to the <b>${B.dir(la, lo, n.e.lat, n.e.lon)}</b>.</p>` : '<p>No park boundary within about 5 miles.</p>'}`];
    }
    if (!A.padusOk && !A.kyOk) v = ['maybe', '<h2>NO SIGNAL FOR THE BOUNDARY SERVICE</h2><p>We could not load the official boundaries. ' + (B.inKY(la, lo) ? 'Open this page once with signal (or save Park Commander for offline) so the Kentucky boundaries are stored on your phone.' : 'Try again when you have signal.') + '</p>'];
    st.v = v; st.progHit = progHits.length > 0; st.accLine = `<p class="ip-acc">${accTxt}</p>`;
    say(v[0], v[1] + `<p class="ip-acc">${accTxt} ${how === 'watch' ? 'Updated ' + new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', second: '2-digit' }) + '.' : ''}</p>`);
    sotaPanel();
    if (how !== 'watch' && !st.scrolled) { st.scrolled = true; $('ipV').scrollIntoView({ behavior: 'smooth', block: 'center' }); }
    // OpenStreetMap only when nothing official says yes (and only now and then)
    const osmBox = $('ipOsm');
    if (!T && !progHits.length && navigator.onLine !== false && (!st.osmAt || B.km(la, lo, st.osmAt.la, st.osmAt.lo) > 0.15)) {
      st.osmAt = { la, lo }; osmBox.innerHTML = '<p class="ip-small">Also asking OpenStreetMap…</p>';
      B.osmAt(la, lo).then(o => { st.osm = o.length ? o : null; drawOsm(); }).catch(() => { osmBox.innerHTML = ''; });
    } else if (progHits.length) { st.osm = null; osmBox.innerHTML = ''; }
    else drawOsm();
    // list
    $('ipList').innerHTML = (hits.length ? '<h3>BOUNDARIES YOU ARE INSIDE</h3>' + hits.map(r => item(r, true)).join('') : '') + (near.length ? '<h3>NEARBY BOUNDARIES</h3>' + near.slice(0, 6).map(r => item(r, false)).join('') : '') +
      `<p class="ip-small">Checked: ${[A.kyOk ? 'Kentucky official boundary files' : '', A.padusOk ? 'USGS PAD-US (national public land database)' : 'PAD-US did not answer', A.pota.length ? 'POTA park list' : '', (A.wwff || []).length ? 'WWFF directory' : '', (A.sota || []).length ? 'SOTA summits list' : ''].filter(Boolean).join(' · ')}.</p>`;
    draw(rows, hits, near);
  }
  function item(r, isIn) {
    const L = r.L, { la, lo } = st.here;
    return `<div class="ip-it${isIn ? ' in' : ''}${r.src === 'kpc' ? ' kpc' : ''}"><b>${esc(L.name)}</b><span>${esc(L.what)}</span><span>${isIn ? 'Edge about ' + B.dist(r.e.km) + ' away' : 'About ' + B.dist(r.e.km) + ' to the ' + B.dir(la, lo, r.e.lat, r.e.lon)} · ${esc(L.src)}</span>` +
      (r.refs.length ? `<span class="ip-r">${r.refs.map(x => esc(x.ref + ' ' + x.name) + ' (' + esc(x.prog) + ')').join('; ')}</span>` : '') +
      (L.access && L.access !== 'OA' ? `<span class="ip-w">⚠ ${esc(B.ACCESS[L.access] || L.access)}</span>` : '') + (L.ease ? '<span class="ip-w">⚠ Conservation easement: often private land, not open to the public.</span>' : '') +
      (L.note ? `<span class="ip-w">⚠ ${esc(L.note)}</span>` : '') + '</div>';
  }
  /* SOTA: the activation zone is everything within 25 m (82 ft) of height below the summit, so we compare ground height */
  async function sotaPanel() {
    const box = $('ipSota'), { la, lo, alt } = st.here, T = st.target;
    const list = (T && T.prog === 'SOTA') ? [{ ref: T.ref, name: T.name, la: T.la, lo: T.lo, m: T.ft ? T.ft / 3.28084 : null, ft: T.ft, d: B.km(la, lo, T.la, T.lo) }] : (st.area.sota || []).map(x => Object.assign({}, x, { d: B.km(la, lo, x.la, x.lo) })).filter(x => x.d < 3).sort((a, b) => a.d - b.d).slice(0, 2);
    if (!list.length) { box.innerHTML = ''; return; }
    if (!st.elev || B.km(la, lo, st.elev.la, st.elev.lo) > 0.02) { box.innerHTML = '<p class="ip-small">SOTA: checking your height above sea level…</p>'; const e = await B.elevation(la, lo); st.elev = e ? Object.assign({ la, lo }, e) : { la, lo, m: null }; if (st.here.la !== la) return; }
    const g = st.elev.m, ft = m => Math.round(m * 3.28084).toLocaleString() + ' ft';
    const rowsH = list.map(s => {
      const below = g != null && s.m ? s.m - g : null, inAZ = below != null && below <= 25 && s.d < 1.5;
      const where = s.d < 0.03 ? 'right at the summit' : B.dist(s.d) + ' to the ' + B.dir(la, lo, s.la, s.lo);
      return { s, inAZ, html: `<div class="ip-ref"><b>${esc(s.ref)}</b> ${esc(s.name)} <i class="ip-p">SOTA</i> <em>${where}${below != null ? ' · the top is about <b>' + ft(Math.max(0, below)) + '</b> above you' : ''}${s.m ? ' (summit ' + ft(s.m) + ')' : ''}</em><span><a href="kpc-spot-me.html?sota=${encodeURIComponent(s.ref)}">SPOT ME ›</a><a href="https://sotl.as/summits/${encodeURIComponent(s.ref)}" target="_blank" rel="noopener">SOTLAS ↗</a></span></div>` };
    });
    const az = rowsH.find(r => r.inAZ), close = rowsH.find(r => !r.inAZ && g != null && r.s.m && r.s.m - g <= 40 && r.s.d < 1.5);
    const head = az ? `<h3>✓ LOOKS LIKE YOU'RE IN THE ACTIVATION ZONE</h3><p>You're within 82 ft (25 m) of the top of ${esc(az.s.ref)}.</p>` : close ? `<h3>ALMOST IN THE ACTIVATION ZONE</h3><p>Climb a little higher toward ${esc(close.s.ref)}: the zone is the last 82 ft (25 m) below the top.</p>` : `<h3>SOTA SUMMIT${list.length > 1 ? 'S' : ''} NEARBY</h3><p>The activation zone is the last 82 ft (25 m) below the top.</p>`;
    box.innerHTML = `<div class="ip-sota${az ? ' ok' : ''}">${head}${rowsH.map(r => r.html).join('')}<p class="ip-small">Your ground height: ${g != null ? ft(g) + ' from the ' + esc(st.elev.src) + ' elevation map' : 'not available (no signal?)'}${alt != null ? ' · your phone\'s GPS says ' + ft(alt) : ''}. Map heights are close but not exact (and GPS height is worse), so when it's close, walk higher.</p></div>`;
    if (az && !T) {
      const line = `<div class="ip-ref"><b>${esc(az.s.ref)}</b> ${esc(az.s.name)} <i class="ip-p">SOTA</i> <em>in the activation zone</em><span><a href="kpc-spot-me.html?sota=${encodeURIComponent(az.s.ref)}">SPOT ME ›</a></span></div>`;
      if (st.progHit) $('ipV').insertAdjacentHTML('beforeend', '<p><b>Plus a summit:</b> you look to be in the SOTA activation zone too (summit-to-park).</p>' + line);
      else say('yes', `<h2>✓ YOU'RE IN A SOTA ACTIVATION ZONE</h2><p>You're within 82 ft of the top. (This spot is not inside a POTA park or WWFF area.)</p>${line}${st.accLine || ''}`);
    }
    if (T && T.prog === 'SOTA') {
      const r = rowsH[0], b = g != null && r.s.m ? r.s.m - g : null, hd = `<div class="ip-t">Checking: <b>${esc(T.ref)} ${esc(T.name)}</b></div>`;
      say(r.inAZ ? 'yes' : b != null && b <= 40 && r.s.d < 1.5 ? 'edge' : b == null ? 'maybe' : 'no', hd + (r.inAZ ? `<h2>✓ IN THE ACTIVATION ZONE</h2><p>The top is about ${ft(Math.max(0, b))} above you (the zone is 82 ft).</p>` : b == null ? '<h2>COULD NOT CHECK YOUR HEIGHT</h2><p>No elevation answer right now. The summit is ' + (r.s.d < 0.03 ? 'right here' : B.dist(r.s.d) + ' to the ' + B.dir(la, lo, r.s.la, r.s.lo)) + '.</p>' : `<h2>${b <= 40 && r.s.d < 1.5 ? 'ALMOST THERE' : '✕ NOT IN THE ACTIVATION ZONE'}</h2><p>The top is about <b>${ft(b)}</b> above you and ${r.s.d < 0.03 ? 'right here' : B.dist(r.s.d) + ' to the <b>' + B.dir(la, lo, r.s.la, r.s.lo) + '</b>'}. The zone is the last 82 ft below the top.</p>`));
    }
  }
  function drawOsm() {
    const box = $('ipOsm');
    if (!st.osm) { box.innerHTML = ''; return; }
    const o = st.osm[0], e = B.edge(st.here.la, st.here.lo, o.geometry);
    box.innerHTML = `<div class="ip-osm"><b>OpenStreetMap says you're inside: ${esc(o._nm)}</b>${o.others && o.others.length ? ' (also ' + o.others.map(esc).join(', ') + ')' : ''}.${isFinite(e.km) ? ' Its outline is about ' + B.dist(e.km) + ' away.' : ''}<br><span>${esc(B.OSM_NOTE)}</span></div>`;
    if (map) { if (st.osmLay) st.osmLay.remove(); st.osmLay = L.geoJSON(o.geometry, { style: { color: '#ff4fd8', weight: 3, dashArray: '8 6', fill: false } }).addTo(map); }
  }
  function draw(rows, hits, near) {
    if (!map) return;
    const { la, lo, acc } = st.here;
    if (lay) lay.remove(); lay = L.layerGroup().addTo(map);
    const show = new Set(hits.concat(near.slice(0, 6)));
    rows.filter(r => show.has(r)).forEach(r => {
      const kpc = r.src === 'kpc';
      L.geoJSON(r.f.geometry, { style: kpc ? { color: '#ffd400', weight: 3, dashArray: '12 5 2 5', fillOpacity: 0 } : r.in ? { color: '#ffb000', weight: 3, fillColor: '#ffb000', fillOpacity: r.L.proc ? .04 : .14 } : { color: '#c98a00', weight: 2, dashArray: '6 6', fillOpacity: .03 }, interactive: false }).addTo(lay);
    });
    if (me) me.remove(); if (accC) accC.remove(); if (line) line.remove();
    if (acc) accC = L.circle([la, lo], { radius: acc, color: '#1378ff', weight: 1, fillOpacity: .08, interactive: false }).addTo(map);
    me = L.circleMarker([la, lo], { radius: 9, color: '#fff', weight: 3, fillColor: '#1378ff', fillOpacity: 1 }).addTo(map);
    const n = (hits[0] || near[0]); if (n && n.e.km < 8) line = L.polyline([[la, lo], [n.e.lat, n.e.lon]], { color: '#1378ff', weight: 2, dashArray: '4 6', interactive: false }).addTo(map);
    if (st.here.how !== 'watch' || !st.fitted) { st.fitted = true; map.setView([la, lo], Math.max(map.getZoom(), n && n.e.km < 1 ? 16 : 14)); }
  }

  /* ---------- GPS ---------- */
  function gps() {
    if (!navigator.geolocation) return say('no', '<h2>NO GPS IN THIS BROWSER</h2><p>Tap the map instead to check a spot.</p>');
    say('wait', 'Getting your location… (allow location if your phone asks)');
    navigator.geolocation.getCurrentPosition(p => check(p.coords.latitude, p.coords.longitude, p.coords.accuracy, 'gps', p.coords.altitude), e => say('no', `<h2>COULD NOT GET YOUR LOCATION</h2><p>${e.code === 1 ? 'Location is turned off for this site. Allow it in your browser settings, then try again.' : 'Your phone could not get a GPS fix. Step outside or wait a moment and try again.'} You can also tap the map to check a spot.</p>`), { enableHighAccuracy: true, timeout: 20000, maximumAge: 5000 });
  }
  function startWatch() {
    if (!navigator.geolocation) return;
    st.fitted = false;
    st.watch = navigator.geolocation.watchPosition(p => { const now = Date.now(); if (now - st.last < 4000) return; st.last = now; check(p.coords.latitude, p.coords.longitude, p.coords.accuracy, 'watch', p.coords.altitude); }, () => {}, { enableHighAccuracy: true, maximumAge: 3000, timeout: 30000 });
    $('ipWatch').textContent = '■ STOP CHECKING'; $('ipWatch').classList.add('on');
    say('wait', 'Watching your GPS. Walk around and the answer updates every few seconds.');
  }
  function stopWatch() { if (st.watch != null) navigator.geolocation.clearWatch(st.watch); st.watch = null; $('ipWatch').textContent = '🚶 KEEP CHECKING AS I WALK'; $('ipWatch').classList.remove('on'); }

  /* ---------- one park (?ref= or the box) ---------- */
  async function setTarget(q) {
    q = String(q || '').trim().toUpperCase(); if (!q) { st.target = null; $('ipTgt').innerHTML = ''; if (st.here) judge(); return; }
    if (!/^[A-Z0-9]{1,4}(\/[A-Z0-9]{2})?-\d{1,5}$/.test(q.replace(/\s+/g, ''))) { $('ipTgt').innerHTML = '<p class="ip-small">Type a reference like US-1271 (POTA), KFF-1271 (WWFF) or W4K/EC-001 (SOTA).</p>'; return; }
    $('ipTgt').innerHTML = '<p class="ip-small">Loading ' + esc(q) + '…</p>';
    let T = null;
    try {
      await B.ky(); const KD = B.kyData();
      const kp = KD.parks.find(p => p.c === q), kk = KD.kff.find(p => p.c === q), ks = KD.summits.find(p => p.c === q);
      if (kp) T = { prog: 'POTA', ref: q, name: kp.n, la: kp.la, lo: kp.lo, feats: await B.kyFor(q) };
      else if (kk) T = { prog: 'WWFF', ref: q, name: kk.n, la: kk.la, lo: kk.lo, feats: kk.p ? await B.kyFor(kk.p) : [] };
      else if (ks) T = { prog: 'SOTA', ref: q, name: ks.n, la: ks.la, lo: ks.lo, ft: ks.ft, feats: [] };
      if (!T || (!T.feats.length && T.prog !== 'SOTA')) {
        const o = await B.lookup(q);
        if (o) { T = { prog: o.prog, ref: o.ref, name: o.name, la: o.la, lo: o.lo, ft: o.ft, feats: [] }; if (o.prog !== 'SOTA' && o.us) T.feats = await B.padusByName(o.short || o.name, o.la, o.lo).catch(() => []); }
      }
      if (T && T.prog === 'SOTA' && !T.ft) { const o = await B.lookup(q).catch(() => null); if (o) T.ft = o.ft; }
    } catch (e) {}
    if (!T) { $('ipTgt').innerHTML = '<p class="ip-small">Could not find ' + esc(ref) + '. Check the number (and your signal).</p>'; return; }
    st.target = T; $('ipTgt').innerHTML = `<p class="ip-small">Checking against <b>${esc(T.ref)} ${esc(T.name)}</b> (${esc(T.prog)})${T.prog === 'SOTA' ? ' · summit ' + (T.ft ? T.ft.toLocaleString() + ' ft' : '') : T.feats.length ? '' : ' (no boundary file found)'} · <a href="#" id="ipClr">check any reference instead</a></p>`;
    $('ipClr').onclick = e => { e.preventDefault(); $('ipRef').value = ''; setTarget(''); };
    initMap(T.la, T.lo, 13);
    if (T.feats.length) { const g = L.geoJSON({ type: 'FeatureCollection', features: T.feats.map(f => ({ type: 'Feature', properties: {}, geometry: f.geometry })) }); if (!st.here) { map.fitBounds(g.getBounds(), { padding: [20, 20], maxZoom: 15 }); g.setStyle({ color: '#ffb000', weight: 3, fillOpacity: .1 }).addTo(map); st.tgLay = g; } }
    if (st.here) judge();
  }

  /* ---------- start ---------- */
  $('ipGo').addEventListener('click', () => { stopWatch(); st.scrolled = false; gps(); });
  $('ipWatch').addEventListener('click', () => st.watch != null ? stopWatch() : startWatch());
  $('ipRefForm').addEventListener('submit', e => { e.preventDefault(); setTarget($('ipRef').value); });
  const Q = new URLSearchParams(location.search);
  initMap(37.8, -85.7, 7);
  if (Q.get('ref')) { $('ipRef').value = Q.get('ref'); setTarget(Q.get('ref')); }
  if (Q.get('lat') && Q.get('lon')) check(+Q.get('lat'), +Q.get('lon'), 0, 'map');
})();
