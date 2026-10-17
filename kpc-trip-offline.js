/* KPC trip planners: SAVE MY TRIP FOR NO SIGNAL (Brandon Oct 16 2026).
   KPCTripOffline.save({stops:[{la,lo}], files:[urls], msg:el, btn:el, key:'kpcUsTripSaved'})
   Saves into the same caches the Activation Kit uses (kpc-finder-v1 = page + scripts + data, kpc-tiles-v1 = street
   map pieces), so kpc-finder-sw.js can open the planner with no signal. The trip itself is already kept on the phone.
   KPCTripOffline.offline() is true when the phone has no signal. */
(function () {
  'use strict';
  const APP = 'kpc-finder-v1', TILES = 'kpc-tiles-v1';       // never rename (house rule)
  const LEAF = /(unpkg\.com\/leaflet@1\.9\.4|cdnjs\.cloudflare\.com\/ajax\/libs\/leaflet\/1\.9\.4)/;
  function sw() { try { if ('serviceWorker' in navigator && window.isSecureContext) return navigator.serviceWorker.register('kpc-finder-sw.js'); } catch (e) {} return Promise.resolve(null); }
  sw();
  const tx = (lo, z) => Math.floor((lo + 180) / 360 * 2 ** z);
  const ty = (la, z) => { const r = la * Math.PI / 180; return Math.floor((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * 2 ** z); };
  /* street-map pieces around every stop: wide at zoom 10-12, close in at 13-15 (about 60-120 pieces a stop) */
  function tiles(stops) {
    const out = new Set();
    stops.forEach(s => {
      for (let z = 10; z <= 15; z++) {
        const pad = z <= 12 ? 0.07 : z === 13 ? 0.03 : 0.012;
        const x0 = tx(s.lo - pad, z), x1 = tx(s.lo + pad, z), y0 = ty(s.la + pad, z), y1 = ty(s.la - pad, z);
        for (let x = x0; x <= x1; x++) for (let y = y0; y <= y1; y++) out.add(`https://tile.openstreetmap.org/${z}/${x}/${y}.png`);
      }
    });
    return [...out].slice(0, 2200);
  }
  async function save(o) {
    const say = t => { if (o.msg) o.msg.innerHTML = t; };
    if (!('caches' in window)) { say('This browser can’t save pages for offline use.'); return; }
    if (o.btn) o.btn.disabled = true;
    try {
      await sw();
      say('Saving the planner…');
      const app = await caches.open(APP);
      const used = performance.getEntriesByType('resource').map(e => e.name)
        .filter(u => (u.startsWith(location.origin) && !/goatcounter|kpc-count/.test(u)) || LEAF.test(u));
      const urls = [...new Set([location.href.split('#')[0]].concat(used, (o.files || []).map(f => new URL(f, location.href).href)))];
      let ok = 0;
      for (const u of urls) {
        try { const r = await fetch(u, { cache: 'reload' }); if (r.ok) { const k = new URL(u); if (k.origin === location.origin) { k.search = ''; k.hash = ''; } await app.put(k.href, r); ok++; } } catch (e) {}
      }
      const T = tiles(o.stops || []), tc = await caches.open(TILES); let done = 0;
      for (let i = 0; i < T.length; i += 6) {
        await Promise.all(T.slice(i, i + 6).map(async u => { try { if (await tc.match(u)) { done++; return; } const r = await fetch(u, { mode: 'cors' }); if (r.ok) { await tc.put(u, r); done++; } } catch (e) {} }));
        say(`Saving the street map around your stops… ${Math.min(100, Math.round((i + 6) / Math.max(1, T.length) * 100))}%`);
      }
      const when = new Date().toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
      try { localStorage.setItem(o.key || 'kpcTripSaved', JSON.stringify({ t: Date.now(), n: (o.stops || []).length })); } catch (e) {}
      say(`✓ Saved ${when}: the planner, your ${(o.stops || []).length} stop${(o.stops || []).length === 1 ? '' : 's'} and ${done} street-map pieces around them. With no signal, open this page again: the <b>Street</b> map works around your stops. To test it, turn on airplane mode.`);
      if (o.btn) o.btn.textContent = '📴 UPDATE THE SAVED COPY';
    } catch (e) { say('Saving stopped: ' + esc(e.message || 'the phone may be out of space')); }
    if (o.btn) o.btn.disabled = false;
  }
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  function last(key) { try { return JSON.parse(localStorage.getItem(key) || 'null'); } catch (e) { return null; } }
  window.KPCTripOffline = { save, last, offline: () => navigator.onLine === false };
})();
