/* KPC ⬇ GPS wiring (HQ Oct 31 9:50 PM: the outside coder's kpc-gps.js builds GPX / KML / GeoJSON in the browser; chat 3 connects it
   to the real site). Members / beta first: nothing shows for guests until Brandon's GO.
   - data files: KPC-Data first, then the site's own copy (kpc-gps.js tries both);
   - park name + pin: KPCB.lookup (POTA's own record); the area (US-XX) comes from it so parking + key rows are found;
   - outline: the same official sources the cards use (Kentucky official maps, the checked US key, CPCAD, the world key).
     Never OpenStreetMap, never WDPA (ruling W-10: no downloads), never a guessed name search: those parks go out as pin only.
   Use: KPCGPSW.park(el, ref) · KPCGPSW.trip(el, () => [ref | {name, lat, lon}, ...]) · KPCGPSW.tripFile(stopsArray) */
(function () {
  'use strict';
  if (!window.KPCGPS || window.KPCGPSW) return;
  const KD = 'https://kentuckyportableclub.github.io/KPC-Data/';
  const member = () => !window.KPCGate || KPCGate.member();
  let BP = null;
  function needB() {   /* pages without kpc-bounds.js (the KY trip planner) load it the first time a file is made */
    if (window.KPCB) return Promise.resolve(window.KPCB);
    return BP || (BP = new Promise(res => { const s = document.createElement('script'); s.src = 'kpc-bounds.js?v=20261111rel2'; s.onload = () => res(window.KPCB || null); s.onerror = () => res(null); document.head.appendChild(s); }));
  }
  const LK = {};
  const look = ref => LK[ref] || (LK[ref] = needB().then(K => K && K.lookup ? K.lookup(ref) : null).catch(() => null));
  const areaOf = o => (o && o.us && /^[A-Z]{2}$/.test(o.st || '')) ? 'US-' + o.st : null;
  /* Nov 7 (tracts, hidden): a feature read while the tract switch was on carries properties.tract / tracts_total / parent; keep them
     (switch off: no such property, so the file is exactly as before) */
  const tprops = f => { const p = f.properties || {}; return p.tract ? Object.assign({ tract: p.tract, tracts_total: p.tracts_total }, p.parent ? { parent: p.parent } : {}) : {}; };
  const fc = fs => ({ type: 'FeatureCollection', features: fs.filter(f => f && f.geometry).map(f => ({ type: 'Feature', properties: Object.assign({ name: f._nm || '' }, tprops(f)), geometry: f.geometry })) });
  const agencies = fs => [...new Set(fs.map(f => (f._L && f._L.agency) || f._src).filter(Boolean))].join(' and ');
  const bad = s => /WDPA|Protected Planet|OpenStreetMap|OSM/i.test(String(s || ''));
  async function outline(ref, park) {
    const K = await needB(); if (!K) return { status: 'pin' };
    const o = (await look(ref)) || {}, la = park && park.lat != null ? park.lat : o.la, lo = park && park.lon != null ? park.lon : o.lo;
    try {
      if (/^US-/.test(ref)) {
        if (o.ky || (K.inKY && isFinite(la) && K.inKY(la, lo))) {
          const fs = await K.kyFor(ref).catch(() => null);
          if (fs && fs.length && !fs.some(f => bad(f._src))) return { status: 'official', agency: agencies(fs) || 'Kentucky official maps', geojson: fc(fs) };
        }
        const u = await K.usOutline(ref, o.short || o.name || (park && park.name), la, lo, [o.st].filter(Boolean)).catch(() => null);
        if (u && u.fs && u.fs.length && !bad(u.src) && !/name search/.test(u.why || '')) return { status: u.label === 'approx' ? 'approximate' : 'official', agency: u.src || '', why: u.why || '', geojson: fc(u.fs) };
        return { status: 'pin' };
      }
      if (/^CA-/.test(ref) && K.canada) { const fs = await K.canada(ref).catch(() => []); if (fs.length && !bad(fs[0]._src)) return { status: 'official', agency: fs[0]._src || '', geojson: fc(fs) }; return { status: 'pin' }; }
      if (K.worldKey) { const w = await K.worldKey(ref).catch(() => null); if (w && w.state === 'ok' && w.fs && w.fs.length && !w.fs.some(f => bad(f._src))) return { status: w.approx ? 'approximate' : 'official', agency: w.fs[0]._src || '', why: w.why || '', geojson: fc(w.fs) }; }
    } catch (e) {}
    return { status: 'pin' };
  }
  async function parkInfo(ref) { const o = await look(ref); return o ? { ref, name: o.name, lat: o.la, lon: o.lo, area: areaOf(o) } : null; }
  /* G6 (Nov 2): answer keys come ONLY from KPC-Data (released); the site's own held copy is never read */
  const kfetch = u => (/(^|\/)data\/(us|ca|world)-key\//.test(u) && u.indexOf(KD) !== 0) ? Promise.resolve(new Response('', { status: 404 })) : fetch(u);
  KPCGPS.config({ siteUrl: 'https://kentuckyportableclub.github.io/KPC-Links/', dataUrl: p => KD + p, fetch: kfetch, outline, parkInfo, trails: () => [] });
  /* a stop with its area filled in (parking + the checked key are read per state) */
  async function stopOf(s) {
    if (typeof s === 'string') { const o = await look(s); return { ref: s, area: areaOf(o) }; }
    if (s && s.ref) { if (s.area) return s; const o = await look(s.ref); return Object.assign({}, s, { area: areaOf(o) }); }
    return s;
  }
  function park(el, ref) {
    if (!el || !ref || !member()) return;
    el.innerHTML = '';
    look(ref).then(o => KPCGPS.button(el, { ref, area: areaOf(o), noFers: true }));   /* 2-fer spots only from the Overlap Finder, which hands over the spots it shows */
  }
  function trip(el, fn) {
    if (!el || !member()) return;
    el.innerHTML = '';
    KPCGPS.button(el, { noFers: true, stops: () => Promise.all((fn() || []).map(stopOf)) });
  }
  /* the planners' own ⬇ GPX buttons: one GPX of the whole trip, same notice + parking + outlines as the park files */
  async function tripFile(stops, name) {
    const ss = await Promise.all((stops || []).map(stopOf));
    const r = await KPCGPS.trip(ss, {});
    return KPCGPS.download(r.gpx, name || r.files.gpx);
  }
  /* any card can just carry <div data-gps-ref="US-1234"></div> or <div data-gps-refs="US-1,US-2"></div>: it fills by itself */
  function scan() {
    document.querySelectorAll('[data-gps-ref],[data-gps-refs]').forEach(el => {
      const k = el.dataset.gpsRef || el.dataset.gpsRefs; if (!k || el.dataset.gpsDone === k) return; el.dataset.gpsDone = k;
      if (el.dataset.gpsRef) park(el, k); else { const refs = k.split(',').map(x => x.trim()).filter(Boolean), fers = el._gpsFers || null; trip(el, () => fers ? refs.map((r, i) => i ? r : { ref: r, fers }) : refs); }
    });
  }
  if (member()) { new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true }); if (document.readyState !== 'loading') scan(); else document.addEventListener('DOMContentLoaded', scan); }
  window.KPCGPSW = { park, trip, tripFile, member, stopOf, outline };
})();
